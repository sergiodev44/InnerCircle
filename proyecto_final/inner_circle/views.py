from .models import Profile, Product, Venta, Resena, User, FriendRequest, Mensaje, Conversation, Notification, BlockedUser, Report, Dispute
from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView, UpdateView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import ProfileForm, ProductForm, ResenaForm, UserForm, FriendRequestForm, MensajeForm, ProductSearchForm, ReportForm, DisputeForm, DisputeResponseForm
from django.views import View
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.shortcuts import render
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import uuid
import stripe
import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def cleanup_abandoned_carts():
    """Release products from abandoned carts (unpaid for >15 minutes)"""
    cutoff_time = timezone.now() - timedelta(minutes=1)
    abandoned = Venta.objects.filter(
        estado_pago='no_pagado',
        created_at__lt=cutoff_time
    )
    for venta in abandoned:
        if venta.product.estado == 'RESV':
            venta.product.estado = 'DISP'
            venta.product.save()
            venta.estado_pago = 'cancelada'
            venta.save()

def can_report_user(user):
    """Check if user can report (max 3 per hour)"""
    one_hour_ago = timezone.now() - timedelta(hours=1)
    recent_reports = Report.objects.filter(
        reporter=user,
        created_at__gte=one_hour_ago
    ).count()
    return recent_reports < 3


def can_send_message(user):
    """Check if user can send message (max 3 per 1 minute for testing)"""
    one_min_ago = timezone.now() - timedelta(minutes=1)
    recent_messages = Mensaje.objects.filter(
        sender=user,
        created_at__gte=one_min_ago
    ).count()
    print(f"DEBUG: User {user.username} has {recent_messages} messages in last min. Can send: {recent_messages < 3}")
    return recent_messages < 15


def get_rate_limit_timeout(user):
    """Get minutes until user can send next message (0 if ok to send)"""
    one_min_ago = timezone.now() - timedelta(minutes=1)
    oldest_msg = Mensaje.objects.filter(
        sender=user,
        created_at__gte=one_min_ago
    ).order_by('created_at').first()
    
    if not oldest_msg or oldest_msg.created_at < one_min_ago:
        return 0
    
    # Seconds until oldest message leaves the 1-minute window
    time_left = oldest_msg.created_at + timedelta(minutes=1) - timezone.now()
    seconds = int(time_left.total_seconds()) + 1
    return max(1, seconds)


def check_and_ban_spammer(user, action_type):
    """Auto-ban user if they violate rate limit TWICE in same 1 minute"""
    # Refresh user from DB to get latest last_rate_limit_warning
    user.refresh_from_db()
    
    one_min_ago = timezone.now() - timedelta(minutes=1)
    
    print(f"DEBUG: Checking ban status for {user.username}. last_rate_limit_warning={user.last_rate_limit_warning}")
    
    # Check if user already has a recent violation (stored in last_rate_limit_warning)
    if user.last_rate_limit_warning:
        time_since_warning = timezone.now() - user.last_rate_limit_warning
        print(f"DEBUG: Time since warning: {time_since_warning}. Is < 1 min? {time_since_warning < timedelta(minutes=1)}")
        if time_since_warning < timedelta(minutes=1):
            # Second violation within a minute = permanent ban
            user.is_banned = True
            user.save()
            from django.db import connection
            connection.commit()
            print(f"DEBUG: PERMANENTLY BANNED {user.username} for second rate limit violation")
            return True
    
    # First violation: mark the timestamp
    print(f"DEBUG: Setting first violation warning for {user.username}")
    user.last_rate_limit_warning = timezone.now()
    user.save()
    from django.db import connection
    connection.commit()
    print(f"DEBUG: First violation for {user.username}. Warning issued. last_rate_limit_warning={user.last_rate_limit_warning}")
    return False

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"

# USER
class userCreateView(CreateView,):
    model = User
    form_class = UserForm
    template_name = "UserForm.html"
    success_url = reverse_lazy("login")


class VerifyEmailView(View):
    """Simple email verification view"""
    def get(self, request):
        uid = request.GET.get('uid')
        token = request.GET.get('token')
        
        if not uid or not token:
            return render(request, 'inner_circle/email_verification_failed.html')
        
        try:
            user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            return render(request, 'inner_circle/email_verification_failed.html')
        
        # Check if token matches
        if user.email_verification_token == token:
            user.email_verified = True
            user.email_verification_token = None  # Clear token after use
            user.save()
            return render(request, 'inner_circle/email_verified.html', {'user': user})
        
        return render(request, 'inner_circle/email_verification_failed.html')

class ResendVerificationEmailView(LoginRequiredMixin, View):
    """Resend verification email to user"""
    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return redirect('inner_circle:profile_detail', pk=request.user.profile.pk)
        
        # Generate new token
        token = str(uuid.uuid4())
        user.email_verification_token = token
        user.save()
        
        # Send email
        verification_link = f"http://localhost:8000/inner/verify-email/?uid={user.pk}&token={token}"
        subject = 'Verify your email - InnerCircle'
        message = f"Hi {user.username},\n\nVerify your email:\n{verification_link}\n\nExpires in 24 hours."
        
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        except Exception as e:
            print(f"Failed to send email: {e}")
        
        return redirect('inner_circle:profile_detail', pk=pk)

# PROFILE
class profileDetailView(DetailView):
    model = Profile
    template_name = "profileDetail.html"
    context_object_name = "profile"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.get_object().user
        context["frequest"] = profile_user.recibe_solicitud.all()
        context["amigos"] = profile_user.friends.all()
        context["mis_resenas"] = Resena.objects.filter(recibidor=profile_user)
        context["bloqueados"] = BlockedUser.objects.filter(blocker=profile_user)
        context["user_products"] = Product.objects.filter(user=profile_user, deleted_at__isnull=True).order_by('-created_at')
        context["user_ventas"] = Venta.objects.filter(vendedor=profile_user).select_related('product', 'comprador__profile').order_by('-created_at')
        # Pass list of blocked user IDs for template checks
        if self.request.user.is_authenticated:
            context["blocked_user_ids"] = list(self.request.user.bloqueados.values_list('blocked__id', flat=True))
            context["my_friends_ids"] = set(self.request.user.friends.values_list('id', flat=True))
            user = self.request.user
            context['is_friend'] = user.friends.filter(pk=profile_user.pk).exists()
            # Stats visible only if owner or friends
            context['can_view_stats'] = user.pk == profile_user.pk or context['is_friend']
            from .models import FriendRequest
            
            # Check for sent request
            sent_request = FriendRequest.objects.filter(sender=user, recibidor2=profile_user, status='pendiente').first()
            context['friend_request_sent'] = sent_request is not None
            context['friend_request_sent_id'] = sent_request.pk if sent_request else None
            
            # Check for received request
            received_request = FriendRequest.objects.filter(sender=profile_user, recibidor2=user, status='pendiente').first()
            context['friend_request_received'] = received_request is not None
            context['friend_request_received_id'] = received_request.pk if received_request else None
        else:
            context['can_view_stats'] = False
        return context
    
class profileUpdateView(LoginRequiredMixin,UserPassesTestMixin,UpdateView):
    model = Profile
    template_name = "profileForm.html"
    form_class = ProfileForm
    def test_func(self):
        return self.request.user.pk == self.get_object().user.pk
    
    def get_success_url(self):
        return reverse_lazy("inner_circle:profile_detail", 
        kwargs={"pk": self.get_object().user.profile.pk}
        )
    
class profileDeleteView(LoginRequiredMixin,UserPassesTestMixin,DeleteView):
    model = Profile
    template_name = "profileDelete.html"
    def test_func(self):
        return self.request.user.pk == self.get_object().user.pk
    success_url = reverse_lazy("inner_circle:producto_list")
    # success_url = reverse_lazy("logout")
    

# PRODUCTS
class productListView(ListView):
    model = Product
    template_name = "productList.html"
    context_object_name = "productos"
    paginate_by = 12
    
    def get_queryset(self):
        cleanup_abandoned_carts()
        queryset = Product.objects.exclude(user=self.request.user).exclude(estado__in=['RESV', 'VEND'])
        
        # Exclude blocked users from showing their products
        if self.request.user.is_authenticated:
            blocked_users = self.request.user.bloqueados.values_list('blocked', flat=True)
            queryset = queryset.exclude(user__in=blocked_users)
            
            # Also exclude users who have blocked the current user
            blocking_users = BlockedUser.objects.filter(blocked=self.request.user).values_list('blocker', flat=True)
            queryset = queryset.exclude(user__in=blocking_users)
        
        return self._apply_filters(queryset)
    
    def _apply_filters(self, queryset):
        nombre = self.request.GET.get('nombre', '').strip()
        precio_min = self.request.GET.get('precio_min', '')
        precio_max = self.request.GET.get('precio_max', '')
        talla = self.request.GET.get('talla', '')
        category = self.request.GET.get('category', '')
        sort = self.request.GET.get('sort', '')
        
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
        if precio_min:
            queryset = queryset.filter(precio__gte=precio_min)
        if precio_max:
            queryset = queryset.filter(precio__lte=precio_max)
        if talla:
            queryset = queryset.filter(talla=talla)
        if category:
            queryset = queryset.filter(category__nombre=category)
        
        # Apply sorting
        if sort == 'precio_asc':
            queryset = queryset.order_by('precio')
        elif sort == 'precio_desc':
            queryset = queryset.order_by('-precio')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProductSearchForm(self.request.GET)
        context['current_tab'] = 'general'
        return context
    
class amigosProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "productList.html"
    context_object_name = "productos"
    paginate_by = 12
    
    def get_queryset(self):
        cleanup_abandoned_carts()
        queryset = Product.objects.filter(user__in=self.request.user.friends.all()).exclude(estado='VEND')
        
        # Exclude blocked users
        blocked_users = self.request.user.bloqueados.values_list('blocked', flat=True)
        queryset = queryset.exclude(user__in=blocked_users)
        
        # Also exclude users who have blocked the current user
        blocking_users = BlockedUser.objects.filter(blocked=self.request.user).values_list('blocker', flat=True)
        queryset = queryset.exclude(user__in=blocking_users)
        
        return self._apply_filters(queryset)
    
    def _apply_filters(self, queryset):
        nombre = self.request.GET.get('nombre', '').strip()
        precio_min = self.request.GET.get('precio_min', '')
        precio_max = self.request.GET.get('precio_max', '')
        talla = self.request.GET.get('talla', '')
        category = self.request.GET.get('category', '')
        sort = self.request.GET.get('sort', '')
        
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
        if precio_min:
            queryset = queryset.filter(precio__gte=precio_min)
        if precio_max:
            queryset = queryset.filter(precio__lte=precio_max)
        if talla:
            queryset = queryset.filter(talla=talla)
        if category:
            queryset = queryset.filter(category__nombre=category)
        
        # Apply sorting
        if sort == 'precio_asc':
            queryset = queryset.order_by('precio')
        elif sort == 'precio_desc':
            queryset = queryset.order_by('-precio')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProductSearchForm(self.request.GET)
        context['current_tab'] = 'amigos'
        return context
    
    
class productDetailView(DetailView):
    model = Product
    template_name = "productDetail.html"
    context_object_name = "producto"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["blocked_user_ids"] = list(self.request.user.bloqueados.values_list('blocked__id', flat=True))
            # Friendship / friend request state for seller (used in productDetail template)
            try:
                seller = self.get_object().user
                user = self.request.user
                context['is_friend'] = user.friends.filter(pk=seller.pk).exists()
                from .models import FriendRequest
                
                # Check for sent request
                sent_request = FriendRequest.objects.filter(sender=user, recibidor2=seller, status='pendiente').first()
                context['friend_request_sent'] = sent_request is not None
                context['friend_request_sent_id'] = sent_request.pk if sent_request else None
                
                # Check for received request
                received_request = FriendRequest.objects.filter(sender=seller, recibidor2=user, status='pendiente').first()
                context['friend_request_received'] = received_request is not None
                context['friend_request_received_id'] = received_request.pk if received_request else None
            except Exception:
                context['is_friend'] = False
                context['friend_request_sent'] = False
                context['friend_request_sent_id'] = None
                context['friend_request_received'] = False
                context['friend_request_received_id'] = None
        return context

class productCreateView(LoginRequiredMixin,CreateView):
    model = Product
    form_class = ProductForm
    template_name = "productForm.html"
    success_url = reverse_lazy("inner_circle:producto_list")
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form) 
       
    
class productUpdateView(LoginRequiredMixin,UserPassesTestMixin,UpdateView,):
    model = Product
    form_class = ProductForm
    template_name = "productForm.html"
    success_url = reverse_lazy("inner_circle:producto_list")
    def test_func(self):
        return self.request.user.pk == self.get_object().user.pk
    
# class productDeleteView(LoginRequiredMixin,DeleteView):
#     model = Product
#     template_name = "productDelete.html"
#     success_url = reverse_lazy("inner_circle:producto_list")
    
    
class productDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "productDelete.html"
    
    def test_func(self):
        return self.request.user == self.get_object().user
    
    def get_object(self):
        return Product.objects.all_including_deleted().get(pk=self.kwargs['pk'])
    
    def get(self, request, *args, **kwargs):
        product = self.get_object()
        if not self.test_func():
            return redirect('inner_circle:producto_list')
        context = {'product': product}
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        product = self.get_object()
        if not self.test_func():
            return redirect('inner_circle:producto_list')
        # Soft delete: mark with deleted_at timestamp
        product.deleted_at = timezone.now()
        product.save()
        return redirect('inner_circle:mis_productos', pk=request.user.pk)
    

class misProductosListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "misProducts.html"
    context_object_name = "productos"
    paginate_by = 12
    
    def get_queryset(self):
        # Show only active (not deleted) products for the current user
        queryset = Product.objects.filter(user=self.request.user)
        return self._apply_filters(queryset)
    
    def _apply_filters(self, queryset):
        nombre = self.request.GET.get('nombre', '').strip()
        precio_min = self.request.GET.get('precio_min', '')
        precio_max = self.request.GET.get('precio_max', '')
        talla = self.request.GET.get('talla', '')
        category = self.request.GET.get('category', '')
        sort = self.request.GET.get('sort', '')
        
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
        if precio_min:
            queryset = queryset.filter(precio__gte=precio_min)
        if precio_max:
            queryset = queryset.filter(precio__lte=precio_max)
        if talla:
            queryset = queryset.filter(talla=talla)
        if category:
            queryset = queryset.filter(category__nombre=category)
        
        # Apply sorting
        if sort == 'precio_asc':
            queryset = queryset.order_by('precio')
        elif sort == 'precio_desc':
            queryset = queryset.order_by('-precio')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProductSearchForm(self.request.GET)
        return context
    

# VENTAS

# REMEMBER #
### Esta bien necesita revisión ###

# v2
class ventaCreateView(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """Create venta with row-level locking to prevent double-selling"""
        # Lock product row to prevent race conditions
        product = Product.objects.select_for_update().get(pk=self.kwargs['pk'])
        
        # Double-check product status after acquiring lock
        if product.estado != 'DISP':
            return redirect('inner_circle:producto_list')
        
        venta = Venta(
            comprador=request.user,
            vendedor=product.user,
            product=product,
            precio_base=product.precio,
        )
        # Calculate tax, fee, and total
        venta.calculate_totals()
        venta.save()

        # Mark product as reserved (NOT sold yet - that happens after payment succeeds)
        product.estado = 'RESV'
        product.save()
        # Redirect to Stripe checkout instead of detail
        return redirect('inner_circle:checkout', pk=venta.pk)
    
    def get(self, request, *args, **kwargs):
        product = Product.objects.get(pk=self.kwargs['pk'])
        # Create a temporary venta to show the breakdown
        venta = Venta(
            precio_base=product.precio,
        )
        venta.calculate_totals()
        context = {'product': product, 'venta': venta}
        return render(request, 'inner_circle/venta_form.html', context)

    

class ventaDetailView(LoginRequiredMixin,UserPassesTestMixin,DetailView):
    model = Venta
    template_name = "ventaDetail.html"

    def test_func(self):
        venta = self.get_object()
        return self.request.user in [venta.comprador, venta.vendedor]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.get_object().product
        return context
    

class stripeCheckoutView(LoginRequiredMixin, DetailView):
    """Stripe checkout page - creates PaymentIntent and displays payment form"""
    model = Venta
    template_name = "inner_circle/checkout.html"
    context_object_name = "venta"
    
    def get_object(self):
        return Venta.objects.get(pk=self.kwargs['pk'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venta = self.get_object()
        
        # Only the buyer can access checkout
        if self.request.user != venta.comprador:
            raise PermissionError("Only the buyer can access checkout")
        
        # Create Stripe Payment Intent
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(venta.importe_total * 100),  # Convert to cents
                currency='eur',
                metadata={
                    'venta_id': venta.pk,
                    'buyer_id': venta.comprador.id,
                    'product_id': venta.product.id,
                }
            )
            venta.stripe_payment_intent = intent.id
            venta.save()
            
            context['client_secret'] = intent.client_secret
            context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
            context['product'] = venta.product
        except stripe.error.StripeError as e:
            context['error'] = str(e)
        
        return context
    

class ventasList(LoginRequiredMixin, TemplateView):
    template_name = "inner_circle/ventas_list.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Paginate ventas (sales as seller)
        ventas = Venta.objects.filter(vendedor=self.request.user)
        page = self.request.GET.get('page', 1)
        paginator = Paginator(ventas, self.paginate_by)
        try:
            ventas = paginator.page(page)
        except PageNotAnInteger:
            ventas = paginator.page(1)
        except EmptyPage:
            ventas = paginator.page(paginator.num_pages)
        
        # Paginate compras (purchases as buyer) - use different page param
        compras = Venta.objects.filter(comprador=self.request.user)
        page_compras = self.request.GET.get('page_compras', 1)
        paginator_compras = Paginator(compras, self.paginate_by)
        try:
            compras = paginator_compras.page(page_compras)
        except PageNotAnInteger:
            compras = paginator_compras.page(1)
        except EmptyPage:
            compras = paginator_compras.page(paginator_compras.num_pages)
        
        context['ventas'] = ventas
        context['compras'] = compras
        return context


@method_decorator(csrf_exempt, name='dispatch')
class stripeWebhookView(View):
    """Handle Stripe webhooks for payment confirmation"""
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return JsonResponse({'error': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError:
            return JsonResponse({'error': 'Invalid signature'}, status=400)
        
        # Handle payment_intent.payment_failed event - release product back to DISP
        if event['type'] == 'payment_intent.payment_failed':
            try:
                payment_intent = event['data']['object']
                venta_id = None
                if 'metadata' in payment_intent and 'venta_id' in payment_intent['metadata']:
                    venta_id = payment_intent['metadata']['venta_id']
                
                print(f"❌ Webhook received payment_intent.payment_failed")
                print(f"   Payment Intent ID: {payment_intent['id']}")
                print(f"   Venta ID from metadata: {venta_id}")
                
                if venta_id:
                    try:
                        venta_id_int = int(venta_id)
                        with transaction.atomic():
                            product = Product.objects.select_for_update().get(prods=venta_id_int)
                            # Release product back to available if payment fails
                            if product.estado == 'RESV':
                                product.estado = 'DISP'
                                product.save()
                                print(f"   ✅ Released product {product.pk} back to DISP")
                    except Product.DoesNotExist:
                        print(f"   ⚠️  Product not found for venta: {venta_id_int}")
                    except ValueError:
                        print(f"   ❌ Invalid venta_id format: {venta_id}")
            except Exception as e:
                print(f"❌ Error processing payment_intent.payment_failed: {str(e)}")
        
        # Handle payment_intent.succeeded event
        elif event['type'] == 'payment_intent.succeeded':
            try:
                payment_intent = event['data']['object']
                
                # Access Stripe object using bracket notation
                venta_id = None
                if 'metadata' in payment_intent and 'venta_id' in payment_intent['metadata']:
                    venta_id = payment_intent['metadata']['venta_id']
                
                print(f"🔔 Webhook received payment_intent.succeeded")
                print(f"   Payment Intent ID: {payment_intent['id']}")
                print(f"   Venta ID from metadata: {venta_id}")
                
                if venta_id:
                    try:
                        venta_id_int = int(venta_id)
                        # Use atomic transaction to ensure product status updates consistently with payment
                        with transaction.atomic():
                            venta = Venta.objects.select_for_update().get(pk=venta_id_int)
                            print(f"   ✅ Found venta: {venta.pk}")
                            print(f"   Current estado_pago: {venta.estado_pago}")
                            venta.estado_pago = 'pagado'
                            venta.save()
                            
                            # Mark product as SOLD (finalize the sale) - soft delete
                            product = venta.product
                            product.estado = 'VEND'
                            product.deleted_at = timezone.now()
                            product.save()
                            print(f"   ✅ Updated venta.estado_pago to 'pagado'")
                            print(f"   ✅ Soft-deleted product {product.pk} (marked as VEND)")
                            
                            # Send email to seller only when payment succeeds
                            subject = f'¡Tu producto {product.nombre} fue vendido!'
                            message = f"""Hola {venta.vendedor.username},

{venta.comprador.username} compró tu producto "{product.nombre}" por ${venta.precio_base}.

Total: €{venta.importe_total}

Ve a tu panel de ventas para más detalles.

—InnerCircle"""
                            try:
                                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [venta.vendedor.email])
                            except Exception as e:
                                print(f"Failed to send payment confirmation email: {e}")
                    except Venta.DoesNotExist:
                        print(f"   ❌ Venta not found with id: {venta_id_int}")
                    except ValueError:
                        print(f"   ❌ Invalid venta_id format: {venta_id}")
                else:
                    print(f"   ⚠️  No venta_id in metadata")
                    
            except Exception as e:
                print(f"❌ Error processing payment_intent.succeeded: {str(e)}")
                import traceback
                traceback.print_exc()
        
        return JsonResponse({'success': True})


class stripePaymentStatusView(LoginRequiredMixin, View):
    """Check payment status and update venta"""
    def post(self, request, pk):
        try:
            venta = Venta.objects.get(pk=pk)
            
            # Only buyer can check status
            if request.user != venta.comprador:
                return JsonResponse({'error': 'Unauthorized'}, status=403)
            
            # Check payment intent status
            if venta.stripe_payment_intent:
                intent = stripe.PaymentIntent.retrieve(venta.stripe_payment_intent)
                
                if intent.status == 'succeeded':
                    venta.estado_pago = 'pagado'
                    venta.save()
                    return JsonResponse({
                        'success': True,
                        'status': 'pagado',
                        'redirect_url': f'/inner/venta/{venta.pk}/'
                    })
                elif intent.status == 'processing':
                    return JsonResponse({'success': True, 'status': 'processing'})
                else:
                    return JsonResponse({'success': False, 'status': intent.status})
            
            return JsonResponse({'error': 'No payment intent found'}, status=400)
        
        except Venta.DoesNotExist:
            return JsonResponse({'error': 'Venta not found'}, status=404)


# RESEÑAS

class resenaDetailView(LoginRequiredMixin,UserPassesTestMixin,DetailView):
    model = Resena
    template_name = "resenaDetail.html"
    def test_func(self):
        return self.request.user.pk == self.get_object().user.pk
    
class resenaCreateView(LoginRequiredMixin,UserPassesTestMixin,CreateView):
    model = Resena
    form_class = ResenaForm
    template_name = "resenaForm.html"
    
    def get_success_url(self):
        return reverse_lazy("inner_circle:venta_detail", kwargs={"pk": self.object.venta.pk})
    
    def test_func(self):
        venta = Venta.objects.get(pk=self.kwargs['pk'])
        return self.request.user == venta.comprador
    
    def form_valid(self, form):
        venta = Venta.objects.get(pk=self.kwargs['pk'])
        form.instance.escritor = self.request.user
        form.instance.recibidor = venta.vendedor
        form.instance.venta = venta
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['venta'] = Venta.objects.get(pk=self.kwargs['pk'])
        return context
    

# class resenaDetailView:
#     pass

class resenaDeleteView(LoginRequiredMixin, UserPassesTestMixin,DeleteView):
    model = Resena
    template_name = "resenaDelete.html"
    success_url = reverse_lazy("inner_circle:producto_list")
    def test_func(self):
        return self.request.user.pk == self.get_object().user.pk
    

# FriendRequest
class frequestCreateView(LoginRequiredMixin, View):
    """Create a friend request - just POST without form page"""
    def post(self, request, *args, **kwargs):
        profile = Profile.objects.get(pk=self.kwargs['pk'])
        recipient = profile.user
        
        # Don't allow sending request to yourself
        if recipient == request.user:
            return redirect('inner_circle:profile_detail', pk=profile.pk)
        
        # Check if request already exists
        if FriendRequest.objects.filter(sender=request.user, recibidor2=recipient).exists():
            return redirect('inner_circle:profile_detail', pk=profile.pk)
        
        # Create the friend request
        FriendRequest.objects.create(sender=request.user, recibidor2=recipient)
        
        return redirect('inner_circle:profile_detail', pk=profile.pk)
  
# REMEMBER #
### Esta bien necesita revisión ###
class frRequestResponseView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Accept or reject a friend request"""
    def test_func(self):
        fr = FriendRequest.objects.get(pk=self.kwargs['pk'])
        return self.request.user == fr.recibidor2
    
    def post(self, request, *args, **kwargs):
        fr = FriendRequest.objects.get(pk=self.kwargs['pk'])
        action = request.POST.get('action')

        if action == 'aceptar':
            request.user.friends.add(fr.sender)
            fr.status = 'aceptada'
        elif action == 'rechazar':
            fr.status = 'rechazada'
        
        fr.save()
        return redirect('inner_circle:profile_detail', pk=request.user.profile.pk)


class frRequestCancelView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Cancel a pending friend request sent by current user"""
    def test_func(self):
        fr = FriendRequest.objects.get(pk=self.kwargs['pk'])
        return self.request.user == fr.sender
    
    def post(self, request, *args, **kwargs):
        fr = FriendRequest.objects.get(pk=self.kwargs['pk'])
        # Just delete the pending request
        if fr.status == 'pendiente':
            fr.delete()
        
        # Determine where to redirect back to
        recipient_profile = fr.recibidor2.profile
        return redirect('inner_circle:profile_detail', pk=recipient_profile.pk)
    

# REMEMBER #
### Esta bien necesita revisión ###
class friendDeleteView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        amigo = User.objects.get(pk=self.kwargs['pk'])
        action = request.POST.get('action')

        if action == 'remove':
            request.user.friends.remove(amigo)
        
        return redirect('inner_circle:profile_detail', pk=request.user.profile.pk )
    

    
# Notifications
class profileNotis(LoginRequiredMixin, TemplateView):
    template_name = "inner_circle/profile_notis.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['frequest'] = FriendRequest.objects.filter(
            recibidor2=self.request.user,
            status='pendiente'
        )
        context['ventas']= Venta.objects.filter(vendedor=self.request.user)
        context['compras']= Venta.objects.filter(comprador=self.request.user)
        context['notificaciones'] = Notification.objects.filter(user=self.request.user)
        
        # Marcar notificaciones como leídas cuando el usuario las ve
        Notification.objects.filter(user=self.request.user, leido=False).update(leido=True)

        return context
    
    
# Mensajes
# REMEMBER #
### Esta bien necesita revisión ###

class conversacionDetailView(LoginRequiredMixin, UserPassesTestMixin, View):
    
    def test_func(self):
        conversation = Conversation.objects.get(pk=self.kwargs['conversation_id'])
        user_in_conversation = self.request.user in [conversation.usuario1, conversation.usuario2]
        
        # Check if either user is blocked
        otro_user = conversation.usuario2 if self.request.user == conversation.usuario1 else conversation.usuario1
        is_blocked = BlockedUser.objects.filter(
            Q(blocker=self.request.user, blocked=otro_user) |
            Q(blocker=otro_user, blocked=self.request.user)
        ).exists()
        
        return user_in_conversation and not is_blocked
    
    def get(self, request, *args, **kwargs):
        conversation = Conversation.objects.get(pk=self.kwargs['conversation_id'])
        usuario_actual = request.user
        otro_user = conversation.usuario2 if usuario_actual == conversation.usuario1 else conversation.usuario1
        
        mensajes = conversation.mensajes.all()
        
        # Check rate limit status
        rate_limited = not can_send_message(request.user)
        timeout_minutes = get_rate_limit_timeout(request.user) if rate_limited else 0
        
        if rate_limited:
            request.user.refresh_from_db()
            if request.user.last_rate_limit_warning:
                time_since = timezone.now() - request.user.last_rate_limit_warning
                print(f"DEBUG: GET rate limited - warning was {int(time_since.total_seconds())}s ago")
                if time_since < timedelta(hours=1):
                    # Second timeout within 1 hour = permanent ban
                    print(f"DEBUG: BANNING {request.user.username}")
                    request.user.is_banned = True
                    request.user.save()
                    # Middleware will catch next request, but redirect now
                    from django.contrib.auth import logout
                    logout(request)
                    return redirect('inner_circle:banned')
            else:
                # First timeout: record warning
                print(f"DEBUG: First timeout for {request.user.username} - saving warning")
                request.user.last_rate_limit_warning = timezone.now()
                request.user.save()
        
        context = {
            'mensajes': mensajes,
            'conversation': conversation,
            'producto': conversation.producto,
            'otro_usuario': otro_user,
            'form': MensajeForm(),
            'rate_limited': rate_limited,
            'timeout_minutes': timeout_minutes,
        }
        return render(request, 'inner_circle/conversacion.html', context)
    
    def post(self, request, *args, **kwargs):
        request.user.refresh_from_db()
        
        if not can_send_message(request.user):
            # Rate limit exceeded - check if this is a second violation
            if request.user.last_rate_limit_warning:
                time_since = timezone.now() - request.user.last_rate_limit_warning
                print(f"DEBUG: Second violation? Warning was {int(time_since.total_seconds())}s ago")
                if time_since < timedelta(hours=1):
                    # Second rate limit hit within 1 hour = permanent ban
                    print(f"DEBUG: BANNING {request.user.username}")
                    request.user.is_banned = True
                    request.user.save()
                    return HttpResponse("Tu cuenta ha sido suspendida permanentemente por abuso.", status=429)
            
            # First violation: save warning and show timeout
            print(f"DEBUG: First violation for {request.user.username}")
            request.user.last_rate_limit_warning = timezone.now()
            request.user.save()
            
            conversation = Conversation.objects.get(pk=self.kwargs['conversation_id'])
            context = {
                'timeout_minutes': get_rate_limit_timeout(request.user),
                'conversation': conversation,
                'otro_usuario': conversation.usuario2 if request.user == conversation.usuario1 else conversation.usuario1,
            }
            return render(request, 'inner_circle/mensaje_rate_limit.html', context, status=429)
        
        conversation = Conversation.objects.get(pk=self.kwargs['conversation_id'])
        form = MensajeForm(request.POST)
        
        if form.is_valid():
            mensaje = form.save(commit=False)
            mensaje.sender = request.user
            mensaje.conversation = conversation
            mensaje.save()
        
        return redirect('inner_circle:conversacion_detail', conversation_id=conversation.pk)


class iniciarConversacionView(LoginRequiredMixin, View):
    
    def get(self, request, *args, **kwargs):
        producto = Product.objects.get(pk=self.kwargs['product_pk'])
        otro_user = User.objects.get(pk=self.kwargs['user_pk'])
        
        # Validar que no sea el mismo usuario
        if request.user == otro_user:
            return redirect('inner_circle:producto_detail', pk=producto.pk)
        
        # Check if blocked
        is_blocked = BlockedUser.objects.filter(
            Q(blocker=request.user, blocked=otro_user) |
            Q(blocker=otro_user, blocked=request.user)
        ).exists()
        
        if is_blocked:
            return redirect('inner_circle:producto_detail', pk=producto.pk)
        
        # get_or_create conversation
        conversation, created = Conversation.objects.get_or_create(
            producto=producto,
            usuario1=request.user,
            usuario2=otro_user
        )
        
        return redirect('inner_circle:conversacion_detail', conversation_id=conversation.pk)


class mensajeCreateView(LoginRequiredMixin, CreateView):
    model = Mensaje
    form_class = MensajeForm
    template_name = "inner_circle/mensajeForm.html"
    
    def dispatch(self, request, *args, **kwargs):
        # Rate limit check at dispatch level (catches all attempts)
        if request.method == 'POST':
            print(f"DEBUG DISPATCH: User {request.user.username} attempting to send message")
            if not can_send_message(request.user):
                print(f"DEBUG DISPATCH: Rate limit exceeded for {request.user.username}, banning...")
                # Ban them immediately for trying to bypass
                check_and_ban_spammer(request.user, 'message')
                # Refresh to verify ban
                request.user.refresh_from_db()
                print(f"DEBUG DISPATCH: User {request.user.username} is_banned after ban check: {request.user.is_banned}")
                return HttpResponse("Has excedido el límite de mensajes. Tu cuenta ha sido suspendida temporalmente.", status=429)
        
        print(f"DEBUG DISPATCH: User {request.user.username} passed rate limit check")
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy("inner_circle:conversacion_detail", 
                          kwargs={"conversation_id": self.object.conversation.pk})
    
    def form_valid(self, form):
        producto = Product.objects.get(pk=self.request.POST.get('producto'))
        otro_user = User.objects.get(pk=self.request.POST.get('receptor'))
        
        # Crear o obtener la conversation
        conversation, created = Conversation.objects.get_or_create(
            producto=producto,
            usuario1=self.request.user,
            usuario2=otro_user
        )
        
        form.instance.sender = self.request.user
        form.instance.conversation = conversation
        
        result = super().form_valid(form)
        
        # Final check for spam and auto-ban
        check_and_ban_spammer(self.request.user, 'message')
        
        return result
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        producto_id = self.request.GET.get('producto') or self.request.POST.get('producto')
        receptor_id = self.request.GET.get('receptor') or self.request.POST.get('receptor')
        
        if producto_id and receptor_id:
            context['producto'] = Product.objects.get(pk=producto_id)
            context['receptor'] = User.objects.get(pk=receptor_id)
        return context



# REMEMBER #
### Esta bien necesita revisión ###
class mensajesListView(LoginRequiredMixin, TemplateView):
    template_name = "inner_circle/mensajesList.html"
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user
        
        conversaciones = Conversation.objects.filter(
            Q(usuario1=usuario) | Q(usuario2=usuario)
        ).prefetch_related('mensajes')
        
        # Pagination
        page = self.request.GET.get('page', 1)
        paginator = Paginator(conversaciones, self.paginate_by)
        try:
            conversaciones = paginator.page(page)
        except PageNotAnInteger:
            conversaciones = paginator.page(1)
        except EmptyPage:
            conversaciones = paginator.page(paginator.num_pages)
        
        context['conversaciones'] = conversaciones
        
        # Add disputes (como comprador y vendedor)
        context['buyer_disputes'] = Dispute.objects.filter(comprador=usuario).order_by('-created_at')
        context['seller_disputes'] = Dispute.objects.filter(vendedor=usuario).order_by('-created_at')
        
        return context


# REPORT & BLOCK

class BlockUserView(LoginRequiredMixin, View):
    """Block a user - local block, doesn't go to admin"""
    def post(self, request, *args, **kwargs):
        user_to_block = User.objects.get(pk=self.kwargs['pk'])
        
        # Check if already blocked
        if BlockedUser.objects.filter(blocker=request.user, blocked=user_to_block).exists():
            return redirect('inner_circle:profile_detail', pk=user_to_block.profile.pk)
        
        # Create the block
        BlockedUser.objects.create(blocker=request.user, blocked=user_to_block)
        
        return redirect('inner_circle:profile_detail', pk=user_to_block.profile.pk)


class UnblockUserView(LoginRequiredMixin, View):
    """Unblock a user"""
    def post(self, request, *args, **kwargs):
        user_to_unblock = User.objects.get(pk=self.kwargs['pk'])
        
        BlockedUser.objects.filter(blocker=request.user, blocked=user_to_unblock).delete()
        
        return redirect('inner_circle:profile_detail', pk=user_to_unblock.profile.pk)


class ReportUserView(LoginRequiredMixin, CreateView):
    """Report a user - goes to admin for review"""
    model = Report
    form_class = ReportForm
    template_name = "inner_circle/reportUserForm.html"
    
    def dispatch(self, request, *args, **kwargs):
        # Rate limit check at dispatch level
        if request.method == 'POST':
            if not can_report_user(request.user):
                # Ban them immediately and explicitly
                print(f"DEBUG REPORT: Rate limit exceeded for {request.user.username}, banning NOW")
                request.user.is_banned = True
                request.user.save()
                from django.db import connection
                connection.commit()  # Force DB commit
                print(f"DEBUG REPORT: User {request.user.username} is_banned set to True and saved to DB")
                return HttpResponse("Has excedido el límite de reportes. Tu cuenta ha sido suspendida permanentemente.", status=429)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        reported_user = User.objects.get(pk=self.kwargs['pk'])
        
        # Check if already reported by this user
        if Report.objects.filter(reporter=self.request.user, reported_user=reported_user).exists():
            form.add_error(None, "Ya has reportado a este usuario")
            return self.form_invalid(form)
        
        form.instance.reporter = self.request.user
        form.instance.reported_user = reported_user
        
        result = super().form_valid(form)
        
        # Final check for spam and auto-ban
        check_and_ban_spammer(self.request.user, 'report')
        
        return result
    
    def get_success_url(self):
        return reverse_lazy("inner_circle:profile_detail", 
                          kwargs={"pk": User.objects.get(pk=self.kwargs['pk']).profile.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reported_user'] = User.objects.get(pk=self.kwargs['pk'])
        return context


class BannedView(TemplateView):
    """View shown to banned users"""
    template_name = "inner_circle/banned.html"


# ==================== DISPUTE SYSTEM ====================

class DisputeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Buyer files a dispute with optional evidence"""
    model = Dispute
    form_class = DisputeForm
    template_name = "inner_circle/dispute_form.html"
    
    def test_func(self):
        """Only buyer can file dispute"""
        venta = Venta.objects.get(pk=self.kwargs['venta_pk'])
        return self.request.user == venta.comprador
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['venta'] = Venta.objects.get(pk=self.kwargs['venta_pk'])
        return context
    
    def form_valid(self, form):
        venta = Venta.objects.get(pk=self.kwargs['venta_pk'])
        
        # Prevent duplicate disputes
        if Dispute.objects.filter(venta=venta).exists():
            form.add_error(None, "Ya existe una reclamación para esta compra")
            return self.form_invalid(form)
        
        form.instance.venta = venta
        form.instance.comprador = venta.comprador
        form.instance.vendedor = venta.vendedor
        result = super().form_valid(form)
        
        # Notify seller that buyer filed dispute
        Notification.objects.create(
            user=venta.vendedor,
            tipo='dispute',
            contenido=f'{venta.comprador.username} abrió una reclamación: {form.cleaned_data["razon"]}',
            object_id=self.object.id
        )
        
        return result
    
    def get_success_url(self):
        venta = Venta.objects.get(pk=self.kwargs['venta_pk'])
        return reverse_lazy("inner_circle:dispute_detail", kwargs={"pk": venta.dispute.pk})


class DisputeDetailView(LoginRequiredMixin, UserPassesTestMixin, View):
    """View & manage dispute - buyer sees complaint, seller can respond"""
    template_name = "inner_circle/dispute_detail.html"
    
    def test_func(self):
        """Only involved parties"""
        dispute = Dispute.objects.get(pk=self.kwargs['pk'])
        return self.request.user in [dispute.comprador, dispute.vendedor]
    
    def get(self, request, *args, **kwargs):
        dispute = Dispute.objects.get(pk=self.kwargs['pk'])
        
        # Auto-resolve if timeout & notify both parties
        if dispute.auto_resolve_if_timeout():
            Notification.objects.create(
                user=dispute.comprador,
                tipo='dispute',
                contenido=f'Reclamación resuelta: Reembolso automático procesado (14 días sin respuesta)',
                object_id=dispute.id
            )
            Notification.objects.create(
                user=dispute.vendedor,
                tipo='dispute',
                contenido=f'Reclamación resuelta en tu contra: Reembolso procesado por falta de respuesta',
                object_id=dispute.id
            )
        
        is_seller = request.user == dispute.vendedor
        form = DisputeResponseForm() if is_seller and dispute.estado == 'ABIERTO' else None
        
        context = {
            'dispute': dispute,
            'is_buyer': request.user == dispute.comprador,
            'is_seller': is_seller,
            'form': form,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        """Seller responds to dispute"""
        dispute = Dispute.objects.get(pk=self.kwargs['pk'])
        
        # Only seller can respond
        if request.user != dispute.vendedor:
            return redirect('inner_circle:dispute_detail', pk=dispute.pk)
        
        form = DisputeResponseForm(request.POST, request.FILES, instance=dispute)
        if form.is_valid():
            dispute = form.save(commit=False)
            dispute.estado = 'RESPONDIDO'
            dispute.save()
            
            # Notify buyer that seller responded
            Notification.objects.create(
                user=dispute.comprador,
                tipo='dispute',
                contenido=f'{dispute.vendedor.username} respondió tu reclamación',
                object_id=dispute.id
            )
        
        return redirect('inner_circle:dispute_detail', pk=dispute.pk)


class DisputeListView(LoginRequiredMixin, ListView):
    """List all disputes for buyer & seller"""
    model = Dispute
    template_name = "inner_circle/dispute_list.html"
    context_object_name = "disputes"
    paginate_by = 10
    
    def get_queryset(self):
        return Dispute.objects.filter(
            Q(comprador=self.request.user) | Q(vendedor=self.request.user)
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Count by role
        context['buyer_disputes'] = Dispute.objects.filter(
            comprador=self.request.user
        ).count()
        context['seller_disputes'] = Dispute.objects.filter(
            vendedor=self.request.user
        ).count()
        return context

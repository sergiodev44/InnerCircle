from .models import Profile, Product, Venta, Resena, User, FriendRequest, Mensaje, Conversation, Notification, BlockedUser, Report
from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView, UpdateView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import ProfileForm, ProductForm, ResenaForm, UserForm, FriendRequestForm, MensajeForm, ProductSearchForm, ReportForm
from django.views import View
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.shortcuts import render
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
import uuid
import stripe
import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

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
        context["frequest"] = self.get_object().user.recibe_solicitud.all()
        context["amigos"] = self.get_object().user.friends.all()
        context["mis_resenas"] = Resena.objects.filter(recibidor=self.get_object().user)
        context["bloqueados"] = BlockedUser.objects.filter(blocker=self.get_object().user)
        # Pass list of blocked user IDs for template checks
        if self.request.user.is_authenticated:
            context["blocked_user_ids"] = list(self.request.user.bloqueados.values_list('blocked__id', flat=True))
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
    
    def get_queryset(self):
        queryset = Product.objects.exclude(user=self.request.user)
        
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
        return context
    
class amigosProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "amigosProductList.html"
    context_object_name = "amigos_productos"
    
    def get_queryset(self):
        queryset = Product.objects.filter(user__in=self.request.user.friends.all())
        
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
        return context
    
    
class productDetailView(DetailView):
    model = Product
    template_name = "productDetail.html"
    context_object_name = "producto"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["blocked_user_ids"] = list(self.request.user.bloqueados.values_list('blocked__id', flat=True))
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
    
    
class productDeleteView(LoginRequiredMixin,UserPassesTestMixin,DeleteView):
    model = Product
    template_name = "productDelete.html"
    success_url = reverse_lazy("inner_circle:producto_list")
    def test_func(self):
        return self.request.user == self.get_object().user
    

class misProductosListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "misProducts.html"
    context_object_name = "productos"
    
    def get_queryset(self):
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
            return redirect('inner_circle:product_list')
        
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ventas']= Venta.objects.filter(vendedor=self.request.user)
        context['compras']= Venta.objects.filter(comprador=self.request.user)
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
                            
                            # Mark product as SOLD (finalize the sale)
                            product = venta.product
                            product.estado = 'VEND'
                            product.save()
                            print(f"   ✅ Updated venta.estado_pago to 'pagado'")
                            print(f"   ✅ Updated product {product.pk} estado to 'VEND'")
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
class frequestCreateView(LoginRequiredMixin,CreateView):
    model = FriendRequest
    template_name = "fRequestForm.html"
    form_class = FriendRequestForm

    def form_valid(self, form):
        if form.instance.recibidor2 == self.request.user:
            form.add_error("No puedes enviar solicitud a tí mismo")
            return self.form_invalid(form)
        form.instance.sender = self.request.user 
        return super().form_valid(form)
    
    def get_success_url(self):
        return  reverse_lazy("inner_circle:profile_detail",
        kwargs={"pk" : self.request.user.profile.pk}
        )
  
# REMEMBER #
### Esta bien necesita revisión ###
class frRequestResponseView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        fr = FriendRequest.objects.get(pk=self.kwargs['pk'])
        return self.request.user == fr.recibidor2
    
    def post(self, request, *args, **kwargs):
        fr = FriendRequest.objects.get(pk=self.kwargs['pk'])
        action = request.POST.get('action')

        if action == 'aceptar':
            request.user.friends.add(fr.sender)
            fr.delete()
        elif action == 'rechazar':
            fr.delete()

        return redirect('inner_circle:profile_detail', pk=request.user.profile.pk)
    

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
        # context["resenas_recibidos"] = Resena.objects.filter(escritor=self.get_object().user)

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
        
        context = {
            'mensajes': mensajes,
            'conversation': conversation,
            'producto': conversation.producto,
            'otro_usuario': otro_user,
            'form': MensajeForm()
        }
        return render(request, 'inner_circle/conversacion.html', context)
    
    def post(self, request, *args, **kwargs):
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
        
        return super().form_valid(form)
    
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user
        
        conversaciones = Conversation.objects.filter(
            Q(usuario1=usuario) | Q(usuario2=usuario)
        ).prefetch_related('mensajes')
        
        context['conversaciones'] = conversaciones
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
    
    def form_valid(self, form):
        reported_user = User.objects.get(pk=self.kwargs['pk'])
        
        # Check if already reported by this user
        if Report.objects.filter(reporter=self.request.user, reported_user=reported_user).exists():
            form.add_error(None, "Ya has reportado a este usuario")
            return self.form_invalid(form)
        
        form.instance.reporter = self.request.user
        form.instance.reported_user = reported_user
        
        return super().form_valid(form)
    
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

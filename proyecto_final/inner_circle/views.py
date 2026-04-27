from .models import Profile, Product, Venta, Resena, User, FriendRequest, Mensaje, Conversation, Notification
from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView, UpdateView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import ProfileForm, ProductForm, ResenaForm, UserForm, FriendRequestForm, MensajeForm, ProductSearchForm
from django.views import View
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.shortcuts import render
from django.db.models import Q

# USER
class userCreateView(CreateView,):
    model = User
    form_class = UserForm
    template_name = "UserForm.html"
    success_url = reverse_lazy("login")

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
        return self._apply_filters(queryset)
    
    def _apply_filters(self, queryset):
        nombre = self.request.GET.get('nombre', '').strip()
        precio_min = self.request.GET.get('precio_min', '')
        precio_max = self.request.GET.get('precio_max', '')
        talla = self.request.GET.get('talla', '')
        
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
        if precio_min:
            queryset = queryset.filter(precio__gte=precio_min)
        if precio_max:
            queryset = queryset.filter(precio__lte=precio_max)
        if talla:
            queryset = queryset.filter(talla=talla)
        
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
        return self._apply_filters(queryset)
    
    def _apply_filters(self, queryset):
        nombre = self.request.GET.get('nombre', '').strip()
        precio_min = self.request.GET.get('precio_min', '')
        precio_max = self.request.GET.get('precio_max', '')
        talla = self.request.GET.get('talla', '')
        
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
        if precio_min:
            queryset = queryset.filter(precio__gte=precio_min)
        if precio_max:
            queryset = queryset.filter(precio__lte=precio_max)
        if talla:
            queryset = queryset.filter(talla=talla)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProductSearchForm(self.request.GET)
        return context
    
    
class productDetailView(DetailView):
    model = Product
    template_name = "productDetail.html"
    context_object_name = "producto"
    

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
        
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
        if precio_min:
            queryset = queryset.filter(precio__gte=precio_min)
        if precio_max:
            queryset = queryset.filter(precio__lte=precio_max)
        if talla:
            queryset = queryset.filter(talla=talla)
        
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
    def post(self, request, *args, **kwargs):
        product = Product.objects.get(pk = self.kwargs['pk'])
        if product.estado == 'VEND':
            return redirect('inner_circle:product_list')
        
        venta = Venta.objects.create(
            comprador=request.user,
            vendedor=product.user,
            product=product,
            importe=product.precio,
        )

        product.estado = 'VEND'
        product.save()
        return redirect('inner_circle:venta_detail', pk=venta.pk)
    
    def get(self, request, *args, **kwargs):
        product = Product.objects.get(pk=self.kwargs['pk'])
        context = {'product': product}
        return render(request, 'inner_circle/venta_form.html', context)

    

class ventaDetailView(LoginRequiredMixin,UserPassesTestMixin,DetailView):
    model = Venta
    template_name = "ventaDetail.html"

    def test_func(self):
        venta = self.get_object()
        return self.request.user in [venta.comprador, venta.vendedor]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = Product.objects.get(pk=self.kwargs['pk'])
        return context
    

class ventasList(LoginRequiredMixin, TemplateView):
    template_name = "inner_circle/ventas_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ventas']= Venta.objects.filter(vendedor=self.request.user)
        context['compras']= Venta.objects.filter(comprador=self.request.user)
        return context


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
        return self.request.user in [conversation.usuario1, conversation.usuario2]
    
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



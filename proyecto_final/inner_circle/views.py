from .models import Profile, Product, Venta, Resena, User, FriendRequest
from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView, UpdateView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import ProfileForm, ProductForm, ResenaForm, UserForm, FriendRequestForm
from django.views import View
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.shortcuts import render

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
    context_object_name = "perfil"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["frequest"] = self.get_object().user.recibe_solicitud.all()
        context["amigos"] = self.get_object().user.friends.all()
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
    
class amigosProductListView(ListView, LoginRequiredMixin):
    model = Product
    template_name = "amigosProductList.html"
    context_object_name = "amigos_productos"
    def get_queryset(self):
        return Product.objects.filter(user__in=self.request.user.friends.all())
    
    
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
    success_url = reverse_lazy("inner:producto_list")
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
        return Product.objects.filter(user=self.request.user)
    

# VENTAS

# REMEMBER #
### Esta bien necesita revisión ###
#V1
# class ventaCreateView(LoginRequiredMixin, CreateView):
#     model = Venta
#     fields = []

#     def form_valid(self, form):
#         product = Product.objects.get(pk=self.kwargs['pk'])
#         if product.estado == 'VEND':
#             return self.form_invalid(form)
#         form.instance.comprador = self.request.user
#         form.instance.vendedor = product.user
#         form.instance.product = product
#         form.instance.importe = product.precio
#         response = super().form_valid(form)
#         product.estado = 'VEND'
#         product.save()
#         return response
       
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['product'] = Product.objects.get(pk=self.kwargs['pk'])
#         return context

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


# RESEÑAS
class resenaDetailView(LoginRequiredMixin,UserPassesTestMixin,DetailView):
    model = Resena
    template_name = "resenaDetail.html"
    def test_func(self):
        return self.request.user.pk == self.get_object().user.pk
    
class resenaCreateView(LoginRequiredMixin,CreateView):
    model = Resena
    form_class = ResenaForm
    template_name = "resenaForm.html"
    success_url = reverse_lazy("inner:producto_list")

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

        return context
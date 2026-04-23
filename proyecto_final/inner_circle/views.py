from .models import Profile, Product, Venta, Resena, User
from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView, UpdateView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import ProfileForm, ProductForm, ResenaForm, UserForm

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
    
class amigosProductListView(ListView):
    model = Product
    template_name = "amigosProductList.html"
    
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



# VENTAS
class ventaDetailView(LoginRequiredMixin,UserPassesTestMixin,DetailView):
    model = Venta
    template_name = "ventaDetail.html"
    def test_func(self):
        return self.request.user.pk == self.get_object().user.pk


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
    success_url = reverse_lazy("inner:producto_list")
    def test_func(self):
        return self.request.user.pk == self.get_object().user.pk
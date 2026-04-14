# from django.shortcuts import render
from .models import Profile, Product, Venta, Resena
from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView, UpdateView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import ProfileForm

# PROFILE
class profileUpdateView(UpdateView,LoginRequiredMixin,UserPassesTestMixin):
    model = Profile
    template_name = "profileForm.html"
    form_class = ProfileForm
    success_url = reverse_lazy("inner:profile_detail")

    def test_func(self):
        if self.user.pk == request.user.pk:
            return False

class profileDeleteView(DeleteView,LoginRequiredMixin,UserPassesTestMixin):
    model = Profile
    template_name = "profileDelete.html"

    def test_func(self):
        if self.user.pk == request.user.pk:
            return False

    # montar el logout
    #success_url = reverse_lazy("....")
    

# PRODUCTS
class productListView(DetailView):
    model = Product
    template_name = "productList.html"
    pass
class amigosProductListView(DetailView):
    model = Product
    template_name = "amigosProductList.html"
    pass
class productDetailView(DetailView):
    model = Product
    template_name = "ProductDetail.html"
    pass

class productCreateView(CreateView,LoginRequiredMixin):
    model = Product
    # form_class = productForm
    template_name = "productForm.html"
    success_url = reverse_lazy("inner:producto_list")
    pass
class productUpdateView(UpdateView,LoginRequiredMixin,UserPassesTestMixin):
    model = Product
    # form_class = productForm
    template_name = "productForm.html"
    success_url = reverse_lazy("inner:producto_list")
    def test_func(self):
        if self.user.pk == request.user.pk:
            return False
    pass
class productDeleteView(DeleteView,LoginRequiredMixin,UserPassesTestMixin):
    model = Product
    template_name = "productDelete.html"
    success_url = reverse_lazy("inner:producto_list")

    def test_func(self):
        if self.user.pk == request.user.pk:
            return False
    pass


# VENTAS
class ventaDetailView(DetailView,LoginRequiredMixin,UserPassesTestMixin):
    model = Venta
    template_name = "ventaDetail.html"

    def test_func(self):
        if self.user.pk == request.user.pk:
            return False
    pass


class resenaCreateView(CreateView,LoginRequiredMixin):
    model = Resena
    # form_class = resenaForm
    template_name = "resenaForm.html"
    success_url = reverse_lazy("inner:resena_list")
    pass

# class resenaDetailView:
#     pass

class resenaDeleteView(DeleteView, LoginRequiredMixin, UserPassesTestMixin):
    model = Resena
    template_name = "resenaDelete.html"
    success_url = reverse_lazy("inner:resena_list")
     # only the review writer can delete its own review
     # ill fix this later
    def test_func(self):
        if self.user.pk == request.user.pk:
            return False
    pass
from django.shortcuts import render
from .models import Profile, Product, Venta, Resena
from django.urls import reverse_lazy
from django.views.generic import DeleteView, UpdateView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin


class profileUpdateView(UpdateView):
    model = Profile
    template_name = "profileForm.html"
    # form_class = profileForm
    success_url = reverse_lazy("inner:profile_detail")

class profileDeleteView(DeleteView):
    model = Profile
    template_name = "profileDelete.html"

    # montar el logout
    #success_url = reverse_lazy("....")
    

class productCreateView(CreateView):
    model = Product
    template_name = "product_create.html"
    success_url = reverse_lazy("inner:profile_detail")
    pass
class productDetailView(DetailView):
    model = Product
    pass
class productUpdateView(UpdateView):
    model = Product
    pass
class productDeleteView(DeleteView):
    model = Product
    pass

class ventaDetailView(DetailView):
    model = Venta
    pass


class resenaCreateView(CreateView):
    model = Resena
    pass
# class resenaDetailView:
#     pass
class resenaDeleteView(DeleteView):
    model = Resena
    pass
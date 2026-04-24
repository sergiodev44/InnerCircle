from django import forms
from django.forms import ModelForm
from .models import Profile, Product, Venta, Resena, User, FriendRequest, Mensaje
from django.contrib.auth.forms import UserCreationForm

class UserForm(UserCreationForm):
     class Meta:
        model = User
        fields = ["username", "mobile"]
        widgets = {
             "username" : forms.TextInput(attrs={}),
             "mobile" : forms.NumberInput(attrs={}),
        }



class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["nombre_tag", "bio", "img_perfil"]
        widgets = {
            "nombre_tag": forms.TextInput(attrs={}),
            "bio": forms.Textarea(attrs={'cols':30,'rows':2}),
            "img_perfil": forms.ClearableFileInput(attrs={}),
            
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["nombre","descripcion","estado","precio","talla","img_prod"]
        widgets = {
            "nombre": forms.TextInput(attrs={}),
            "descripcion": forms.Textarea(attrs={'cols':30, 'rows':3}),
            "estado": forms.Select(attrs={}),
            "talla": forms.Select(attrs={}),
            "img_prod": forms.ClearableFileInput(attrs={}),

        }


class ResenaForm(forms.ModelForm):
    class Meta:
        model = Resena
        fields = ["contenido","puntuacion"]
        widgets = {
             "contenido": forms.Textarea(attrs={'cols':50, 'rows':5}),
             "puntuacion" : forms.Select(),
        }


class FriendRequestForm(forms.ModelForm):
    class Meta:
        model = FriendRequest
        fields = ["recibidor2"]
        widgets = {
             "recibidor2" : forms.Select(attrs={}),
        }


class MensajeForm(forms.ModelForm):
    class Meta:
        model = Mensaje
        fields = ["contenido"]
        widgets = {
            "contenido": forms.Textarea(attrs={'cols':50, 'rows':3}),
        }


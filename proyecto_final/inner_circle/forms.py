from django import forms
from django.forms import ModelForm
from .models import Profile, Product, Venta, Resena, User, FriendRequest, Mensaje, Category, Report, Dispute
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

class UserForm(UserCreationForm):
     class Meta:
        model = User
        fields = ["username", "email", "mobile"]
        widgets = {
             "username" : forms.TextInput(attrs={}),
             "email" : forms.EmailInput(attrs={}),
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
        fields = ["nombre","descripcion","estado","precio","talla","category","img_prod"]
        widgets = {
            "nombre": forms.TextInput(attrs={}),
            "descripcion": forms.Textarea(attrs={'cols':30, 'rows':3}),
            "estado": forms.Select(attrs={}),
            "talla": forms.Select(attrs={}),
            "category": forms.Select(attrs={}),
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


class ProductSearchForm(forms.Form):
    SORT_CHOICES = [
        ('', '-- Más recientes primero --'),
        ('precio_asc', 'Precio: menor a mayor'),
        ('precio_desc', 'Precio: mayor a menor'),
    ]
    
    nombre = forms.CharField(max_length=200, required=False, label="Nombre del producto")
    precio_min = forms.DecimalField(min_value=0, required=False, label="Precio mínimo")
    precio_max = forms.DecimalField(min_value=0, required=False, label="Precio máximo")
    talla = forms.ChoiceField(choices=[('', '-- Todas las tallas --')] + list(Product.TALLAS), required=False, label="Talla")
    category = forms.ChoiceField(choices=[('', '-- Todas las categorías --')] + list(Category.CATEGORIAS), required=False, label="Categoría")
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False, label="Ordenar por")


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason", "description"]
        widgets = {
            "reason": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={
                "cols": 50, 
                "rows": 5,
                "class": "form-control",
                "placeholder": "Describa por favor por qué está reporting a este usuario"
            }),
        }
        labels = {
            "reason": "Razón del reporte",
            "description": "Descripción detallada"
        }


class DisputeForm(forms.ModelForm):
    """Form for buyer to file dispute"""
    class Meta:
        model = Dispute
        fields = ["razon", "descripcion", "comprador_evidence"]
        widgets = {
            "razon": forms.Select(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={
                "cols": 50, "rows": 5, "class": "form-control",
                "placeholder": "Explique detalladamente el problema"
            }),
            "comprador_evidence": forms.FileInput(attrs={"class": "form-control"}),
        }
        labels = {
            "razon": "Razón de la reclamación",
            "descripcion": "Descripción del problema",
            "comprador_evidence": "Prueba (JPG, PNG, PDF) - Opcional"
        }


class DisputeResponseForm(forms.ModelForm):
    """Form for seller to respond to dispute"""
    class Meta:
        model = Dispute
        fields = ["vendedor_response", "vendedor_evidence"]
        widgets = {
            "vendedor_response": forms.Textarea(attrs={
                "cols": 50, "rows": 5, "class": "form-control",
                "placeholder": "Responda a la reclamación"
            }),
            "vendedor_evidence": forms.FileInput(attrs={"class": "form-control"}),
        }
        labels = {
            "vendedor_response": "Tu respuesta",
            "vendedor_evidence": "Prueba (JPG, PNG, PDF) - Opcional"
        }


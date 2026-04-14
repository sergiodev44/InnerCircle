from django.forms import ModelForm, forms
from .models import Profile, Product, Venta, Resena

class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ["user", "nombre_tag", "bio", "img_perfil"]
        widgets = {
            "user": forms.TextInput(attrs={}),
            "nombre_tag": forms.TextInput(attrs={}),
            "bio": forms.Textarea(attrs={'cols':30,'rows':2}),
            "img_perfil": forms.ClearableFileInput(attrs={}),
            
        }
         
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    mobile = models.IntegerField()

class Profile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    nombre_tag = models.CharField(max_length=200)
    # max length?
    bio = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    img_perfil = models.ImageField()

class Product(models.Model):
    ESTADO_PRODUCTO = [("DISP","disponible"), ("RESV","reservado"), ("VEND","vendido")]
    TALLAS = [("S", "pequeña"), ("M", "mediana"), ("L", "grande"), ("XL", "muy grande")]

    user = models.ForeignKey(User,on_delete=models.SET_NULL, null=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    estado = models.CharField(choices=ESTADO_PRODUCTO)
    precio = models.DecimalField(max_digits=6, decimal_places=2)
    talla = models.CharField(choices=TALLAS)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateField(auto_now=True)
    img_prod = models.ImageField()
    # los productos también tienen imagenes, 3. Cómo lo añado?

class Venta(models.Model):
    comprador = models.ForeignKey(User,on_delete=models.SET_NULL, null=True, related_name="comprador")
    vendedor = models.ForeignKey(User,on_delete=models.SET_NULL, null=True, related_name="vendedor")
    importe = models.DecimalField(max_digits=6, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.comprador == self.vendedor:
            raise ValueError("error")
        super().save(*args,**kwargs)

class Resena(models.Model):
    # NOTA = [("1", "1"),("2","2"),("3","3"),("4","4"),("5","5")]
    escritor = models.ForeignKey(User,on_delete=models.SET_NULL, null=True, related_name="escritor")
    recibidor = models.ForeignKey(User,on_delete=models.SET_NULL, null=True, related_name="recibidor")
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="venta")
    contenido = models.TextField()
    puntuacion = models.IntegerField(choices=[(i,str(i)) for i in range(1,6)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["escritor", "venta"]

# Idea opcional es meter como mensajes para negociar precios,
#  interacción vendedor / comprador ??? TBD
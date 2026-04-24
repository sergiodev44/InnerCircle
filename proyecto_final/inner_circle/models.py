from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class User(AbstractUser):
    mobile = models.IntegerField()
    #Atributo para el tema de la amistad
    friends = models.ManyToManyField('self', symmetrical=True, blank=True)

class Profile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    nombre_tag = models.CharField(max_length=200)
    # max length?
    bio = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    img_perfil = models.ImageField(upload_to="profiles/")

class Product(models.Model):
    """
    no incluir zapatos porque no van por tallas
    productos con medidas específicas por ejemplo correas, 
    deberían tener un campo opcional de extra info en el form no?
    """
    ESTADO_PRODUCTO = [("DISP","disponible"), ("RESV","reservado"), ("VEND","vendido")]
    TALLAS = [("S", "pequeña"), ("M", "mediana"), ("L", "grande"), ("XL", "muy grande")]

    user = models.ForeignKey(User,on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    estado = models.CharField(choices=ESTADO_PRODUCTO)
    precio = models.DecimalField(max_digits=6, decimal_places=2)
    talla = models.CharField(choices=TALLAS)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateField(auto_now=True)
    img_prod = models.ImageField(upload_to="products/")
    # los productos también tienen imagenes, 3. Cómo lo añado?

class Venta(models.Model):
    ESTADO_VENTA = [("pendiente","pendiente"),("cancelada","cancelada"),("completada","completada")]
    comprador = models.ForeignKey(User,on_delete=models.CASCADE, related_name="comprador")
    vendedor = models.ForeignKey(User,on_delete=models.CASCADE, related_name="vendedor")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="prods" )
    importe = models.DecimalField(max_digits=6, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    

    def clean(self):
        if self.comprador == self.vendedor:
            raise ValidationError("error")
     

class Resena(models.Model):
    escritor = models.ForeignKey(User,on_delete=models.CASCADE, null=True, related_name="escritor")
    recibidor = models.ForeignKey(User,on_delete=models.CASCADE, null=True, related_name="recibidor")
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="venta")
    contenido = models.TextField()
    puntuacion = models.IntegerField(choices=[(i,str(i)) for i in range(1,6)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["escritor", "venta"]

# Idea opcional es meter como mensajes para negociar precios,
#  interacción vendedor / comprador ??? TBD


class FriendRequest(models.Model):
    estado_peticion = [("pendiente", "pendiente"), ("aceptada", "aceptada"), ("rechazada", "rechazada")]
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="envia_solicitud")
    recibidor2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recibe_solicitud")
    status = models.CharField(choices=estado_peticion, default="pendiente")
    sent_at = models.DateTimeField(auto_now_add=True)
    # añadir un mensaje opcional?

    class Meta:
        unique_together = ["sender", "recibidor2"]

class Mensaje(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="m_enviados")
    receptor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="m_recibidos")
    producto = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="mensajes")
    contenido = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
    


from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class User(AbstractUser):
    mobile = models.IntegerField()
    #Atributo para el tema de la amistad
    friends = models.ManyToManyField('self', symmetrical=True, blank=True)
    
    @property
    def promedio_rating(self):
        """Calcula el promedio de calificaciones recibidas"""
        ratings = self.recibidor.all()
        if ratings.exists():
            return round(ratings.aggregate(prom=models.Avg('puntuacion'))['prom'], 1)
        return None

class Profile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    nombre_tag = models.CharField(max_length=200)
    # max length?
    bio = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    img_perfil = models.ImageField(upload_to="profiles/")

class Category(models.Model):
    CATEGORIAS = [
        ('Camisas','Camisas'),
        ('Camisetas', 'Camisetas'),
        ('Polos','Polos'),
        ('Pantalones','Pantalones'),
        ('Jeans','Jeans'),
        ('Sudaderas','Sudaderas'),
        ('Jerseis','Jerseis'),
        ('Chaquetones','Chaquetones'),
    ]
    nombre = models.CharField(choices=CATEGORIAS, default='Camisetas')
    descripcion = models.TextField(blank=True)
    icono = models.CharField(max_length=50, blank=True)

class Product(models.Model):
    """
    no incluir zapatos porque no van por tallas
    productos con medidas específicas por ejemplo correas, 
    deberían tener un campo opcional de extra info en el form no?
    """
    ESTADO_PRODUCTO = [("DISP","disponible"), ("RESV","reservado"), ("VEND","vendido")]
    TALLAS = [("S", "pequeña"), ("M", "mediana"), ("L", "grande"), ("XL", "muy grande")]

    user = models.ForeignKey(User,on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="productos")
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    estado = models.CharField(choices=ESTADO_PRODUCTO)
    precio = models.DecimalField(max_digits=6, decimal_places=2)
    talla = models.CharField(choices=TALLAS)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateField(auto_now=True)
    img_prod = models.ImageField(upload_to="products/")
    # los productos también tienen imagenes, 3. Cómo lo añado?

    class Meta:
        ordering = ['-created_at']

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


class Conversation(models.Model):
    producto = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="conversaciones")
    usuario1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conv_usuario1")
    usuario2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conv_usuario2")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [("producto", "usuario1", "usuario2")]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.usuario1.username} & {self.usuario2.username}"


class Mensaje(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True, blank=True, related_name="mensajes")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="m_enviados")
    contenido = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username} - {self.created_at}"



class Notification(models.Model):
    TIPO_CHOICES = [
        ('mensaje', 'Nuevo mensaje'),
        ('venta', 'Nueva venta'),
        ('resena', 'Nueva reseña'),
        ('amistad', 'Solicitud de amistad')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    contenido = models.TextField()
    leido = models.BooleanField(default=False)
    object_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']







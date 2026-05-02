from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.core.validators import FileExtensionValidator
from django.utils import timezone


# Image Validation Constants
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'avif']


# Soft Delete QuerySet & Manager
class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet that filters out soft-deleted products"""
    def active(self):
        return self.filter(deleted_at__isnull=True)
    
    def deleted(self):
        return self.exclude(deleted_at__isnull=True)


class SoftDeleteManager(models.Manager):
    """Manager that returns only active (not soft-deleted) products by default"""
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).active()
    
    def all_including_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


def validate_image_size(file):
    """Validate image file size (prevent large uploads)"""
    if file.size > MAX_IMAGE_SIZE:
        raise ValidationError(
            f'Imagen muy grande. Máximo {MAX_IMAGE_SIZE // (1024*1024)}MB. '
            f'Tu archivo: {file.size / (1024*1024):.1f}MB'
        )


class User(AbstractUser):
    mobile = models.IntegerField()
    #Atributo para el tema de la amistad
    friends = models.ManyToManyField('self', symmetrical=True, blank=True)
    is_banned = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=32, blank=True, null=True)
    last_rate_limit_warning = models.DateTimeField(blank=True, null=True)  # Track rate limit violations
    
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
    img_perfil = models.ImageField(
        upload_to="profiles/",
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS),
            validate_image_size,
        ]
    )

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
    
    def __str__(self):
        return self.nombre

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
    img_prod = models.ImageField(
        upload_to="products/",
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS),
            validate_image_size,
        ]
    )
    deleted_at = models.DateTimeField(null=True, blank=True, default=None)
    
    objects = SoftDeleteManager()

    class Meta:
        ordering = ['-created_at']

class Venta(models.Model):
    ESTADO_VENTA = [("pendiente","pendiente"),("cancelada","cancelada"),("completada","completada")]
    ESTADO_PAGO = [("no_pagado","no pagado"), ("pagado","pagado"), ("fallido","fallido")]
    
    comprador = models.ForeignKey(User,on_delete=models.CASCADE, related_name="comprador")
    vendedor = models.ForeignKey(User,on_delete=models.CASCADE, related_name="vendedor")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="prods" )
    precio_base = models.DecimalField(max_digits=6, decimal_places=2)  # Product price
    impuesto = models.DecimalField(max_digits=6, decimal_places=2, default=0)  # Tax (10% by default)
    tarifa_servicio = models.DecimalField(max_digits=6, decimal_places=2, default=0)  # Service fee (5% by default)
    importe_total = models.DecimalField(max_digits=6, decimal_places=2)  # Total charged
    estado_pago = models.CharField(choices=ESTADO_PAGO, default="no_pagado")
    stripe_payment_intent = models.CharField(max_length=255, blank=True, null=True)  # Stripe payment ID
    created_at = models.DateTimeField(auto_now_add=True)

    

    def clean(self):
        if self.comprador == self.vendedor:
            raise ValidationError("error")
    
    @property
    def TAX_RATE(self):
        """Tax rate: 10%"""
        return Decimal('0.10')
    
    @property
    def SERVICE_FEE_RATE(self):
        """Service fee rate: 5%"""
        return Decimal('0.05')
    
    def calculate_totals(self):
        """Calculate tax, service fee, and total"""
        self.impuesto = (self.precio_base * self.TAX_RATE).quantize(Decimal('0.01'))
        self.tarifa_servicio = (self.precio_base * self.SERVICE_FEE_RATE).quantize(Decimal('0.01'))
        self.importe_total = self.precio_base + self.impuesto + self.tarifa_servicio
        return self.importe_total
     

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


class BlockedUser(models.Model):
    """User A blocks User B - local/personal blocking"""
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bloqueados")
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bloqueado_por")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["blocker", "blocked"]
    
    def __str__(self):
        return f"{self.blocker.username} bloqueó a {self.blocked.username}"


class Report(models.Model):
    REASON_CHOICES = [
        ('scam', 'Estafa/Fraude'),
        ('harassment', 'Acoso/Insultos'),
        ('inappropriate_content', 'Contenido inapropiado'),
        ('fake_product', 'Producto falso'),
        ('other', 'Otro')
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('reviewing', 'En revisión'),
        ('resolved', 'Resuelto'),
        ('dismissed', 'Desestimado')
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reportes_hechos")
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reportes_recibidos")
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["reporter", "reported_user"]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reporte: {self.reporter.username} → {self.reported_user.username} ({self.reason})"







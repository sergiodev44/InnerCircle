from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from datetime import timedelta
import stripe
from django.conf import settings

"""Aquí están todos los models de InnerCircle"""

"""Variables creadas para el control del tamaño y formato de las imagenes"""
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'avif']



class SoftDeleteQuerySet(models.QuerySet):
    """Filtro de productos que ya están vendidos, no borrados de la db"""
    def active(self):
        return self.filter(deleted_at__isnull=True)
    
    def deleted(self):
        return self.exclude(deleted_at__isnull=True)


class SoftDeleteManager(models.Manager):
    """Manager que devuelve los productos que pasan el filtro de softdeleted"""
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).active()
    
    def all_including_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


def validate_image_size(file):
    """Validador del tamaño de la imagen"""
    if file.size > MAX_IMAGE_SIZE:
        raise ValidationError(
            f'Imagen muy grande. Máximo {MAX_IMAGE_SIZE // (1024*1024)}MB. '
            f'Tu archivo: {file.size / (1024*1024):.1f}MB'
        )


class User(AbstractUser):
    "Clase custom del Usuario base de Django"
    mobile = models.IntegerField()
    friends = models.ManyToManyField('self', symmetrical=True, blank=True)
    is_banned = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    last_rate_limit_warning = models.DateTimeField(blank=True, null=True)
    
    @property
    def promedio_rating(self):
        """Calcula el promedio de calificaciones recibidas"""
        ratings = self.recibidor.all()
        if ratings.exists():
            return round(ratings.aggregate(prom=models.Avg('puntuacion'))['prom'], 1)
        return None

class Profile(models.Model):
    """Clase de Perfil de Usuario"""
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    nombre_tag = models.CharField(max_length=200)
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
    """Clase Categoría para adminstrar de forma más óptima este atributo de los producots"""
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
    Clase central de InnerCircle que gestiona los Productos y sus atributos
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
        ],
        null=True,
        blank=True
    )
    deleted_at = models.DateTimeField(null=True, blank=True, default=None)
    
    objects = SoftDeleteManager()

    class Meta:
        ordering = ['-created_at']


class ProductImage(models.Model):
    """
    Clase que permite gestionar la subida de imágenes para productos
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(
        upload_to="products/",
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS),
            validate_image_size,
        ]
    )
    order = models.PositiveIntegerField(default=0) 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.product.nombre} - Image {self.order}"

class Venta(models.Model):
    ESTADO_VENTA = [("pendiente","pendiente"),("cancelada","cancelada"),("completada","completada")]
    ESTADO_PAGO = [("no_pagado","no pagado"), ("pagado","pagado"), ("fallido","fallido")]
    
    comprador = models.ForeignKey(User,on_delete=models.CASCADE, related_name="comprador")
    vendedor = models.ForeignKey(User,on_delete=models.CASCADE, related_name="vendedor")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="prods" )
    precio_base = models.DecimalField(max_digits=6, decimal_places=2)  
    impuesto = models.DecimalField(max_digits=6, decimal_places=2, default=0) 
    tarifa_servicio = models.DecimalField(max_digits=6, decimal_places=2, default=0)  
    importe_total = models.DecimalField(max_digits=6, decimal_places=2)  
    estado_pago = models.CharField(choices=ESTADO_PAGO, default="no_pagado")
    stripe_payment_intent = models.CharField(max_length=255, blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    

    def clean(self):
        if self.comprador == self.vendedor:
            raise ValidationError("error")
    
    @property
    def TAX_RATE(self):
        """Tasa de Impuestos"""
        return Decimal('0.10')
    
    @property
    def SERVICE_FEE_RATE(self):
        """% que InnerCircle gana por venta"""
        return Decimal('0.05')
    
    def calculate_totals(self):
        """Calcula el precio total a pagar"""
        self.impuesto = (self.precio_base * self.TAX_RATE).quantize(Decimal('0.01'))
        self.tarifa_servicio = (self.precio_base * self.SERVICE_FEE_RATE).quantize(Decimal('0.01'))
        self.importe_total = self.precio_base + self.impuesto + self.tarifa_servicio
        return self.importe_total
     

class Resena(models.Model):
    """Clase para que el comprador pueda escribir una reseña al vendedor"""
    escritor = models.ForeignKey(User,on_delete=models.CASCADE, null=True, related_name="escritor")
    recibidor = models.ForeignKey(User,on_delete=models.CASCADE, null=True, related_name="recibidor")
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="venta")
    contenido = models.TextField()
    puntuacion = models.IntegerField(choices=[(i,str(i)) for i in range(1,6)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["escritor", "venta"]



class FriendRequest(models.Model):
    """Clase para las peticiones de amistad"""
    estado_peticion = [("pendiente", "pendiente"), ("aceptada", "aceptada"), ("rechazada", "rechazada")]
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="envia_solicitud")
    recibidor2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recibe_solicitud")
    status = models.CharField(choices=estado_peticion, default="pendiente")
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["sender", "recibidor2"]


class Conversation(models.Model):
    """Clase para las conversación sobre un productos entre vendedor y comprador"""
    producto = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="conversaciones")
    usuario1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conv_usuario1")
    usuario2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conv_usuario2")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [("producto", "usuario1", "usuario2")]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.usuario1.username} & {self.usuario2.username}"


class Dispute(models.Model):
    """Sistema de disputas/reclamaciones simple"""
    RAZONES = [
        ('fake_product', 'Producto falso/no auténtico'),
        ('never_received', 'Nunca llegó'),
        ('damage', 'Llegó dañado'),
        ('not_as_described', 'No corresponde a descripción'),
    ]
    ESTADO = [
        ('ABIERTO', 'Abierto - Esperando respuesta del vendedor'),
        ('RESPONDIDO', 'Respondido - Esperando decisión del admin'),
        ('REEMBOLSADO', 'Reembolsado - Comprador gana (refund)'),
        ('RECHAZADO', 'Rechazado - Vendedor gana (sin refund)'),
    ]
    
    venta = models.OneToOneField(Venta, on_delete=models.CASCADE, related_name="dispute")
    comprador = models.ForeignKey(User, on_delete=models.CASCADE, related_name="disputes_buyer")
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="disputes_seller")
    razon = models.CharField(max_length=50, choices=RAZONES)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO, default='ABIERTO')
    
    comprador_evidence = models.FileField(
        upload_to="disputes/",
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'webp'])]
    )
    vendedor_response = models.TextField(blank=True, null=True)
    vendedor_evidence = models.FileField(
        upload_to="disputes/",
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'webp'])]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    refund_processed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Dispute #{self.id} - {self.venta.product.nombre}"
    
    def auto_resolve_if_timeout(self):
        """Auto-resolver de disputas después de 14 días
        si el vendedor no responde o el admin no la resuelve"""
        if self.estado == 'ABIERTO' and timezone.now() - self.created_at > timedelta(days=14):
            self.estado = 'REEMBOLSADO'
            self.resolved_at = timezone.now()
            self.save()
            self.process_refund()
            return True
        return False
    
    def process_refund(self):
        """Reembolso de Stripe"""
        if self.refund_processed or not self.venta.stripe_payment_intent:
            return False
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe.Refund.create(
                payment_intent=self.venta.stripe_payment_intent,
                reason='requested_by_customer'
            )
            self.refund_processed = True
            self.save()
            return True
        except stripe.error.StripeError as e:
            print(f"Refund error for dispute {self.id}: {str(e)}")
            return False


class Mensaje(models.Model):
    """Clase que gestiona los mensajes de las conversaciones"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True, blank=True, related_name="mensajes")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="m_enviados")
    contenido = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username} - {self.created_at}"



class Notification(models.Model):
    """Sistema de notificaciones a usuarios sobre su activad, disputas, ventas y mensajes"""
    TIPO_CHOICES = [
        ('mensaje', 'Nuevo mensaje'),
        ('venta', 'Nueva venta'),
        ('resena', 'Nueva reseña'),
        ('amistad', 'Solicitud de amistad'),
        ('dispute', 'Reclamación')
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
    """Clase para que usuarios bloqueen a usuarios"""
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bloqueados")
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bloqueado_por")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["blocker", "blocked"]
    
    def __str__(self):
        return f"{self.blocker.username} bloqueó a {self.blocked.username}"


class Report(models.Model):
    """Clase de reportes, donde usuarios pueden denunciar a los vendedores
     por malas prñacticas"""
    
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







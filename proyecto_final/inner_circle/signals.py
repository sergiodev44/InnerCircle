from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from .models import User, Profile, Mensaje, Venta, FriendRequest, Resena, Notification
from django.core.mail import send_mail
from django.conf import settings
import uuid

# Parte del user

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def send_verification_email(sender, instance, created, **kwargs):
    """Send email verification link when user signs up"""
    if created and instance.email:
        # Generate UUID token (dashes are URL-safe, won't be MIME-mangled)
        token = str(uuid.uuid4())
        instance.email_verification_token = token
        instance.save()
        
        # Build verification link
        verification_link = f"http://localhost:8000/inner/verify-email/?uid={instance.pk}&token={token}"
        
        # Email content
        subject = 'Verify your email - InnerCircle'
        message = f"Hi {instance.username},\n\nVerify your email:\n{verification_link}\n\nExpires in 24 hours."
        
        # Send email
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.email])
        except Exception as e:
            print(f"Failed to send email: {e}")


@receiver(user_logged_in)
def create_profile_extra(sender, user, request, **kwargs):
    Profile.objects.get_or_create(user=user)


# Parte de las notis

@receiver(post_save, sender=Mensaje)
def notificar_mensaje(sender, instance, created, **kwargs):
    if created:
        otro = instance.conversation.usuario2 if instance.sender == instance.conversation.usuario1 else instance.conversation.usuario1
        Notification.objects.create(
            user=otro,
            tipo='mensaje',
            contenido=f"Nuevo mensaje de {instance.sender.profile.nombre_tag} sobre {instance.conversation.producto.nombre}",
            object_id=instance.conversation.pk
        )

@receiver(post_save, sender=Venta)
def notificar_venta(sender, instance, created,**kwargs):
    if created:
        Notification.objects.create(
            user=instance.vendedor,
            tipo="venta",
            contenido=f"Interés de {instance.comprador.username} en {instance.product.nombre}",
            object_id=instance.pk
        )
        
        # Send email notification to seller
        subject = f'¡Tu producto {instance.product.nombre} fue vendido!'
        message = f"""Hola {instance.vendedor.username},

{instance.comprador.username} compró tu producto "{instance.product.nombre}" por ${instance.precio_base}.

Total: €    {instance.importe_total}

Ve a tu panel de ventas para más detalles.

—InnerCircle"""
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.vendedor.email])
        except Exception as e:
            print(f"Failed to send venta email: {e}")

@receiver(post_save, sender=Resena)
def notificar_resena(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.recibidor,
            tipo="resena",
            contenido=f"Nueva reseña de {instance.escritor.username}",
            object_id=instance.pk
        )

@receiver(post_save, sender=FriendRequest)
def notificar_amistad(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.recibidor2,
            tipo="amistad",
            contenido=f"Solicitud de amistad de {instance.sender.profile.nombre_tag}",
            object_id=instance.pk
        )

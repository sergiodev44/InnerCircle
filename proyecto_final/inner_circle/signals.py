from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from .models import User, Profile, Mensaje, Venta, FriendRequest, Resena, Notification

# Parte del user

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

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

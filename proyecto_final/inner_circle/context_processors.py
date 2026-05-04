from .models import Notification


def notifications_context(request):
    """Agregar count de notificaciones no leídas a cada template"""
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            user=request.user, 
            leido=False
        ).count()
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}

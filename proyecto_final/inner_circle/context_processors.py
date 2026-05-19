from .models import Notification


def notifications_context(request):
    """Agrega la suma de las notificaciones no leidas a los template"""
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            user=request.user, 
            leido=False
        ).count()
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}

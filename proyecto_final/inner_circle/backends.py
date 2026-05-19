from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class BannedUserBackend(ModelBackend):
    """
    Backend de autorización perosnalizado que evita que usuarios baneados hagan log in.
    Los usurios baneados deben de ser perdonados por el admin
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username, password, **kwargs)
        
        if user is None:
            return None
        
        # Check if user is banned (is_active=False means banned)
        """si el is_active=True significa que está baneado"""
        if not user.is_active:
            return None
        
        return user

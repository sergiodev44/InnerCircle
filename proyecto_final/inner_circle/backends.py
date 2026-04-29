from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class BannedUserBackend(ModelBackend):
    """
    Custom authentication backend that prevents banned users from logging in.
    Banned users have is_active=False set by admin.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username, password, **kwargs)
        
        if user is None:
            return None
        
        # Check if user is banned (is_active=False means banned)
        if not user.is_active:
            # Don't authenticate banned users
            return None
        
        return user

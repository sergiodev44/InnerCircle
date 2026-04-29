from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout


class BannedUserMiddleware(MiddlewareMixin):
    """
    Middleware that checks if the logged-in user is banned (is_active=False).
    If they are, they get logged out immediately.
    """
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # Refresh user from database to get the latest is_active status
            request.user.refresh_from_db()
            
            if not request.user.is_active:
                # User is banned, log them out
                logout(request)
        
        return None

from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse


class BannedUserMiddleware(MiddlewareMixin):
    """
    Middleware that checks if the logged-in user is banned.
    If they are, they get logged out and redirected to banned page.
    """
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # Refresh user from database to get the latest is_banned status
            request.user.refresh_from_db()
            
            if request.user.is_banned:
                # User is banned, log them out and redirect
                logout(request)
                if not request.path.endswith('/banned/'):
                    return redirect(reverse('inner_circle:banned'))
        
        return None

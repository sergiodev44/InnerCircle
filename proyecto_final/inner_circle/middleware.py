from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse


class BannedUserMiddleware(MiddlewareMixin):
    """
    Middleware para comprobar que si el usuario logeado está baneado.
    Estos usuarios son deslogeados y redirigidos a la página de baneados
    """
    
    def process_request(self, request):
        if request.user.is_authenticated:
            """refresca la db para sacar el status del user"""
            request.user.refresh_from_db()
            
            if request.user.is_banned:
                logout(request)
                if not request.path.endswith('/banned/'):
                    return redirect(reverse('inner_circle:banned'))
        
        return None

from django.urls import path
from .views import profileDetailView,profileUpdateView, profileDeleteView, userCreateView
from .views import productListView,misProductosListView, amigosProductListView, productDetailView, productCreateView, productUpdateView, productDeleteView
from .views import ventaDetailView, ventaCreateView, ventasList, resenaDetailView, resenaCreateView, resenaDeleteView
from .views import frequestCreateView, frRequestResponseView, friendDeleteView
from .views import profileNotis, conversacionDetailView, iniciarConversacionView, mensajesListView
from .views import BlockUserView, UnblockUserView, ReportUserView, BannedView

app_name = "inner_circle"

urlpatterns = [
    # User
    path('user/create', userCreateView.as_view(), name="user_create"),
    # Profile
    path('perfil/<int:pk>/', profileDetailView.as_view(), name="profile_detail"),
    path('perfil/<int:pk>/actualizar/', profileUpdateView.as_view(), name="profile_update"),
    path('perfil/<int:pk>/eliminar/', profileDeleteView.as_view(), name="profile_delete"),


    # Products
    path('', productListView.as_view(), name="producto_list"),
    path('mis-productos/<int:pk>/', misProductosListView.as_view(), name=("mis_productos") ),
    path('productos/amigos/', amigosProductListView.as_view(), name="amigos_product_list"),
    path('productos/<int:pk>/', productDetailView.as_view(), name="producto_detail"),
    path('productos/crear/', productCreateView.as_view(), name="product_create"),
    path('productos/<int:pk>/actualizar/', productUpdateView.as_view(), name="product_update"),
    path('productos/<int:pk>/eliminar/', productDeleteView.as_view(), name="product_delete"),
    

    # Ventas
    path('products/<int:pk>/comprar', ventaCreateView.as_view(), name="venta_crear"),
    path('venta/<int:pk>/', ventaDetailView.as_view(), name="venta_detail"),
    path('ventas-list/<int:pk>/', ventasList.as_view(), name="ventas_list"),

    # Reseñas
    path('resena/<int:pk>', resenaCreateView.as_view(), name="resena_create"),
    path('resena/<int:pk>/', resenaDetailView.as_view(), name="resena_detail"),
    path('resena/<int:pk>/eliminar/', resenaDeleteView.as_view(), name="resena_delete"),

    # Notificaciones
    path('perfil/<int:pk>/enviar-peticion', frequestCreateView.as_view(), name="frequest_create"),
    path('frequest/<int:pk>/respuesta/', frRequestResponseView.as_view(), name="frequest_respuesta"),
    path('perfil/<int:pk>/amigos-eliminar/', friendDeleteView.as_view(), name="friend_remove"),
    path('notificaciones/<int:pk>/', profileNotis.as_view(), name="profile_notis" ),

    # Mensajes
    path('conversacion/<int:conversation_id>/', conversacionDetailView.as_view(), name="conversacion_detail"),
    path('conversacion/iniciar/<int:product_pk>/<int:user_pk>/', iniciarConversacionView.as_view(), name="iniciar_conversacion"),
    path('mensajes/', mensajesListView.as_view(), name="mensajes_list"),
    
    # Block & Report
    path('perfil/<int:pk>/bloquear/', BlockUserView.as_view(), name="block_user"),
    path('perfil/<int:pk>/desbloquear/', UnblockUserView.as_view(), name="unblock_user"),
    path('perfil/<int:pk>/reportar/', ReportUserView.as_view(), name="report_user"),
    path('banned/', BannedView.as_view(), name="banned"),
]
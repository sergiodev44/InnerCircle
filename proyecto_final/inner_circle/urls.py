
from django.urls import path
from .views import profileDetailView,profileUpdateView, profileDeleteView
from .views import productListView, amigosProductListView, productCreateView, productUpdateView, productDeleteView
from .views import ventaDetailView, resenaDetailView, resenaCreateView, resenaDeleteView

app_name = "inner_circle"

urlpatterns = [
    # Profile
    path('perfil/<int:pk>/', profileDetailView.as_view(), name="profile_detail"),
    path('perfil/<int:pk>/actualizar/', profileUpdateView.as_view(), name="profile_update"),
    path('perfil/<int:pk>/eliminar/', profileDeleteView.as_view(), name="profile_delete"),

    # Products
    path('', productListView.as_view(), name="producto_list"),
    path('productos/amigos/', amigosProductListView.as_view(), name="amigos_product_list"),
    path('productos/crear/', productCreateView.as_view(), name="product_create"),
    path('productos/<int:pk>/actualizar/', productUpdateView.as_view(), name="product_update"),
    path('productos/<int:pk>/eliminar/', productDeleteView.as_view(), name="product_delete"),
    

    # Ventas
    path('venta/<int:pk>/', ventaDetailView.as_view(), name="venta_detail"),

    # Reseñas
    path('resena/', resenaCreateView.as_view(), name="resena_create"),
    path('resena/<int:pk>/', resenaDetailView.as_view(), name="resena_detail"),
    path('resena/<int:pk>/eliminar/', resenaDeleteView.as_view(), name="resena_delete"),
]
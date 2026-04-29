from django.contrib import admin
from .models import User, Profile, Product, Category, Venta, Resena, FriendRequest, Conversation, Mensaje, Notification, BlockedUser, Report

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'mobile', 'is_banned')
    search_fields = ('username', 'email')
    list_filter = ('is_banned',)
    actions = ['ban_user', 'unban_user']
    
    def ban_user(self, request, queryset):
        updated = queryset.update(is_banned=True)
        self.message_user(request, f"{updated} usuario(s) baneado(s)")
    ban_user.short_description = "Banear usuario seleccionado"
    
    def unban_user(self, request, queryset):
        updated = queryset.update(is_banned=False)
        self.message_user(request, f"{updated} usuario(s) desbaneado(s)")
    unban_user.short_description = "Desbanear usuario seleccionado"

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('nombre_tag', 'user', 'created_at')
    search_fields = ('nombre_tag', 'user__username')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'user', 'precio', 'estado', 'created_at')
    search_fields = ('nombre', 'user__username')
    list_filter = ('estado', 'category', 'created_at')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'comprador', 'vendedor', 'product', 'importe_total', 'estado_pago', 'created_at')
    search_fields = ('comprador__username', 'vendedor__username', 'product__nombre')
    list_filter = ('estado_pago', 'created_at')

@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ('id', 'escritor', 'recibidor', 'puntuacion', 'created_at')
    search_fields = ('escritor__username', 'recibidor__username')

@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recibidor2', 'status', 'sent_at')
    search_fields = ('sender__username', 'recibidor2__username')
    list_filter = ('status',)

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'usuario1', 'usuario2', 'created_at')
    search_fields = ('producto__nombre', 'usuario1__username', 'usuario2__username')

@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'conversation', 'created_at')
    search_fields = ('sender__username', 'conversation__id')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'tipo', 'leido', 'created_at')
    search_fields = ('user__username', 'tipo')
    list_filter = ('tipo', 'leido', 'created_at')

@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ('blocker', 'blocked', 'created_at')
    search_fields = ('blocker__username', 'blocked__username')
    readonly_fields = ('created_at',)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporter', 'reported_user', 'reason', 'status', 'created_at')
    search_fields = ('reporter__username', 'reported_user__username')
    list_filter = ('status', 'reason', 'created_at')
    actions = ['mark_as_reviewing', 'mark_as_dismissed']
    
    def mark_as_reviewing(self, request, queryset):
        queryset.update(status='reviewing')
    mark_as_reviewing.short_description = "Marcar como en revisión"
    
    def mark_as_dismissed(self, request, queryset):
        queryset.update(status='dismissed')
    mark_as_dismissed.short_description = "Desestimar reportes"

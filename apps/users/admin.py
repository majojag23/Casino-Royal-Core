from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, LoginHistory, PasswordReset


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """Admin para CustomUser"""

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información personal', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'date_of_birth')
        }),
        ('Documento', {
            'fields': ('document_type', 'document_number')
        }),
        ('Dirección', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Billetera', {
            'fields': ('balance', 'bonus_balance')
        }),
        ('Seguridad', {
            'fields': ('status', 'two_factor_enabled', 'login_attempts', 'locked_until')
        }),
        ('Verificación', {
            'fields': ('email_verified', 'document_verified', 'kyc_verified')
        }),
        ('Auditoría', {
            'fields': ('last_login_ip', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
    )

    list_display = ('username', 'email', 'balance', 'status', 'created_at')
    list_filter = ('status', 'email_verified', 'document_verified', 'kyc_verified', 'created_at')
    search_fields = ('username', 'email', 'document_number')
    ordering = ('-created_at',)


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    """Admin para historial de logins"""

    list_display = ('user', 'ip_address', 'success', 'created_at')
    list_filter = ('success', 'created_at')
    search_fields = ('user__username', 'ip_address')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'ip_address', 'user_agent', 'success', 'reason', 'created_at')


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    """Admin para recuperación de contraseña"""

    list_display = ('user', 'used', 'created_at', 'expires_at')
    list_filter = ('used', 'created_at')
    search_fields = ('user__username', 'token')
    readonly_fields = ('user', 'token', 'created_at', 'expires_at')

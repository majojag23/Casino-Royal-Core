from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'action', 'ip_address', 'created_at')
    list_filter = ('action', 'created_at')
    ordering = ('-created_at',)

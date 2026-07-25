from django.contrib import admin
from .models import AdminPanel, AdminLog


@admin.register(AdminPanel)
class AdminPanelModelAdmin(admin.ModelAdmin):
    list_display = ('min_bet', 'max_bet', 'maintenance_mode', 'updated_at')


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action', 'target_user', 'created_at')
    list_filter = ('action', 'created_at')
    ordering = ('-created_at',)

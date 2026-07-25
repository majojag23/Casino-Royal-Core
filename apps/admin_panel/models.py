from django.db import models
from apps.users.models import CustomUser


class AdminPanel(models.Model):
    """Configuración del panel admin"""

    min_bet = models.DecimalField(max_digits=10, decimal_places=2, default=0.50)
    max_bet = models.DecimalField(max_digits=10, decimal_places=2, default=10000.00)
    welcome_bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    welcome_bonus_multiplier = models.IntegerField(default=30)
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'admin_panel'


class AdminLog(models.Model):
    """Auditoría de acciones del admin"""

    ACTION_TYPES = [
        ('user_suspend', 'Suspender usuario'),
        ('user_ban', 'Banear usuario'),
        ('modify_settings', 'Modificar configuración'),
        ('process_withdrawal', 'Procesar retiro'),
        ('refund', 'Reembolso'),
        ('bonus_grant', 'Otorgar bono'),
    ]

    admin = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    target_user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='admin_actions')
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin_logs'
        ordering = ['-created_at']

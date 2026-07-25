from django.db import models


class AuditLog(models.Model):
    """Log de auditoría"""

    ACTION_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('deposit', 'Depósito'),
        ('withdrawal', 'Retiro'),
        ('game_play', 'Juego'),
    ]

    user_id = models.IntegerField()
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    ip_address = models.GenericIPAddressField()
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']

from django.db import models
from apps.users.models import CustomUser


class Transaction(models.Model):
    """Modelo para transacciones"""

    TRANSACTION_TYPES = [
        ('deposit', 'Depósito'),
        ('withdrawal', 'Retiro'),
        ('bet', 'Apuesta'),
        ('win', 'Ganancia'),
        ('bonus', 'Bono'),
        ('refund', 'Reembolso'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    ]

    PAYMENT_METHODS = [
        ('pse', 'PSE'),
        ('credit_card', 'Tarjeta Crédito'),
        ('debit_card', 'Tarjeta Débito'),
        ('paypal', 'PayPal'),
        ('wallet', 'Billetera Interna'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.CharField(max_length=100, unique=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='COP')

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, null=True, blank=True)
    payment_provider_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_transaction_type_display()} - {self.amount}"


class PaymentMethod(models.Model):
    """Métodos de pago guardados (integración Stripe)"""

    METHOD_TYPES = [
        ('card', 'Tarjeta'),
        ('bank_account', 'Cuenta Bancaria'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payment_methods')
    stripe_payment_method_id = models.CharField(max_length=255, unique=True, default='')
    type = models.CharField(max_length=20, choices=METHOD_TYPES, default='card')
    nickname = models.CharField(max_length=100, default='Mi Tarjeta')
    last_four = models.CharField(max_length=4, blank=True)
    brand = models.CharField(max_length=50, blank=True)
    active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_methods'
        ordering = ['-created_at']

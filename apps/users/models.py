from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta

class CustomUser(AbstractUser):
    """Modelo de usuario extendido para casino"""

    DOCUMENT_TYPES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('PA', 'Pasaporte'),
    ]

    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('suspended', 'Suspendido'),
        ('banned', 'Prohibido'),
        ('pending_verification', 'Pendiente Verificación'),
    ]

    # Información personal
    document_type = models.CharField(max_length=2, choices=DOCUMENT_TYPES, null=True, blank=True)
    document_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    # Dirección
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, default='Colombia')

    # Billetera del casino
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    bonus_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])

    # Bono de bienvenida / requisito de apuesta (rollover)
    welcome_bonus_claimed = models.BooleanField(default=False)
    bonus_wagering_required = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bonus_wagering_progress = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Seguridad y estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_verification')
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=255, blank=True)

    # Verificación
    email_verified = models.BooleanField(default=False)
    document_verified = models.BooleanField(default=False)
    kyc_verified = models.BooleanField(default=False)

    # Stripe
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True, unique=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"

    def is_account_locked(self):
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False

    def add_balance(self, amount):
        self.balance += amount
        self.save()

    def subtract_balance(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False

    def has_active_bonus(self):
        return self.bonus_balance > 0 and self.bonus_wagering_progress < self.bonus_wagering_required

    def grant_welcome_bonus(self, deposit_amount, match_rate=1.0, max_bonus=200, rollover=20):
        """Bono de bienvenida (por defecto 100% hasta $200) sobre el primer depósito.
        El bono no es retirable: solo se libera hacia el saldo real una vez cumplido
        el requisito de apuesta (rollover)."""
        if self.welcome_bonus_claimed:
            return None
        from decimal import Decimal
        bonus_amount = min(deposit_amount * Decimal(str(match_rate)), Decimal(str(max_bonus)))
        self.bonus_balance += bonus_amount
        self.bonus_wagering_required += bonus_amount * Decimal(str(rollover))
        self.welcome_bonus_claimed = True
        self.save()
        return bonus_amount

    def place_bet(self, amount):
        """Descuenta primero del saldo real; si no alcanza, usa el bono (nunca retirable
        directamente) como respaldo para poder seguir jugando."""
        if self.balance + self.bonus_balance < amount:
            return False
        if self.balance >= amount:
            self.balance -= amount
        else:
            remainder = amount - self.balance
            self.balance = 0
            self.bonus_balance -= remainder
        self.save()
        return True

    def record_wager(self, amount):
        """Registra progreso hacia el requisito de apuesta del bono; si se cumple,
        libera el bono restante como saldo real retirable."""
        if self.bonus_wagering_required > 0 and self.bonus_wagering_progress < self.bonus_wagering_required:
            self.bonus_wagering_progress += amount
            if self.bonus_wagering_progress >= self.bonus_wagering_required and self.bonus_balance > 0:
                self.balance += self.bonus_balance
                self.bonus_balance = 0
            self.save()

    def credit_win(self, amount):
        """Las ganancias mientras haya bono activo se acreditan como bono (no retirable)
        hasta cumplir el requisito de apuesta; si no hay bono activo, van al saldo real."""
        if self.has_active_bonus():
            self.bonus_balance += amount
        else:
            self.balance += amount
        self.save()


class LoginHistory(models.Model):
    """Historial de intentos de login"""

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    success = models.BooleanField(default=False)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'login_history'
        ordering = ['-created_at']


class PasswordReset(models.Model):
    """Tokens para recuperación de contraseña"""

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        db_table = 'password_resets'

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at

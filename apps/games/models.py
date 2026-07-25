from decimal import Decimal
from django.db import models
from apps.users.models import CustomUser


class GameResult(models.Model):
    """Modelo para resultados de juegos"""

    GAME_TYPES = [
        ('slots', 'Slots'),
        ('farm_fest', 'Farm Fest Slots'),
        ('duck_rush', 'Duck Rush'),
        ('panda_mines', 'Panda Mines'),
        ('roulette', 'Ruleta'),
        ('golden_jet', 'Golden Jet'),
        ('cyber_rolett', 'Cyber Rolett'),
        ('personajes', 'Personajes'),
        ('dragon_fruit', 'Dragon Fruit Bonanza'),
        ('totem_falls', 'Totem Falls Bonanza'),
        ('golden_sling_rush', 'Golden Sling Rush'),
        ('frozen_age', 'Frozen Age'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='game_results')
    game_type = models.CharField(max_length=50, choices=GAME_TYPES)
    bet_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payout = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profit_loss = models.DecimalField(max_digits=10, decimal_places=2)
    result = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'game_results'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_game_type_display()} - {self.bet_amount}"


class GameSettings(models.Model):
    """Configuración global de juegos"""

    game_type = models.CharField(max_length=50, unique=True)
    min_bet = models.DecimalField(max_digits=10, decimal_places=2, default=0.50)
    max_bet = models.DecimalField(max_digits=10, decimal_places=2, default=10000.00)
    rtp = models.FloatField(default=0.96)  # Return to Player
    enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'game_settings'

    def __str__(self):
        return f"{self.game_type} - RTP: {self.rtp*100}%"


class SlotsJackpot(models.Model):
    """Pool progresivo del jackpot de Neon Slots (fila 7-7-7)"""

    BASE_AMOUNT = Decimal('400.00')

    amount = models.DecimalField(max_digits=12, decimal_places=2, default=BASE_AMOUNT)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'slots_jackpot'

    def __str__(self):
        return f"Jackpot: ${self.amount}"

    @classmethod
    def get_locked(cls):
        """Obtiene (creando si hace falta) la fila única del jackpot con lock para actualizarla de forma segura"""
        obj, _ = cls.objects.get_or_create(pk=1, defaults={'amount': cls.BASE_AMOUNT})
        return cls.objects.select_for_update().get(pk=obj.pk)

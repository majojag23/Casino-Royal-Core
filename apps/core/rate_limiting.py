"""
Rate limiting y throttling para API
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.core.cache import cache
from django.utils.decorators import method_decorator
from functools import wraps
import time


class UserGameThrottle(UserRateThrottle):
    """Rate limit para jugar (máx 30 juegos/minuto)"""
    scope = 'game_play'
    rate = '30/minute'


class UserDepositThrottle(UserRateThrottle):
    """Rate limit para depósitos (máx 10/hora)"""
    scope = 'deposit'
    rate = '10/hour'


class UserLoginThrottle(UserRateThrottle):
    """Rate limit para login (máx 20/hora)"""
    scope = 'login'
    rate = '20/hour'


class UserWithdrawalThrottle(UserRateThrottle):
    """Rate limit para retiros (máx 5/día)"""
    scope = 'withdrawal'
    rate = '5/day'


class UserAPIThrottle(UserRateThrottle):
    """Rate limit general para API (máx 100/minuto)"""
    scope = 'api'
    rate = '100/minute'


class RateLimitDecorator:
    """Decorador para rate limiting personalizado"""

    @staticmethod
    def rate_limit(max_calls: int, time_window: int, key_func=None):
        """
        Decorador para rate limiting

        Args:
            max_calls: Número máximo de llamadas
            time_window: Ventana de tiempo en segundos
            key_func: Función para generar clave (default: user_id)
        """
        def decorator(func):
            @wraps(func)
            def wrapper(self, request, *args, **kwargs):
                # Generar clave
                if key_func:
                    key = key_func(request, *args, **kwargs)
                else:
                    key = f"rate_limit_{func.__name__}_{request.user.id if request.user.is_authenticated else 'anon'}"

                # Obtener contador actual
                current = cache.get(key, 0)

                if current >= max_calls:
                    from rest_framework.response import Response
                    from rest_framework import status
                    return Response(
                        {'error': f'Demasiadas solicitudes. Máximo {max_calls} por {time_window} segundos'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS
                    )

                # Incrementar contador
                cache.set(key, current + 1, time_window)

                return func(self, request, *args, **kwargs)
            return wrapper
        return decorator


class LoginAttemptTracker:
    """Rastrear intentos de login fallidos"""

    @staticmethod
    def record_failed_attempt(email: str):
        """Registrar intento fallido"""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            user = User.objects.get(email=email)
            user.login_attempts += 1

            # Bloquear después de 5 intentos fallidos
            if user.login_attempts >= 5:
                from django.utils import timezone
                from datetime import timedelta
                user.locked_until = timezone.now() + timedelta(minutes=15)
                user.save()
                return {'locked': True, 'message': 'Cuenta bloqueada por 15 minutos'}

            user.save()
            return {'locked': False, 'attempts': user.login_attempts}
        except User.DoesNotExist:
            return {'locked': False, 'attempts': 0}

    @staticmethod
    def reset_attempts(email: str):
        """Resetear intentos fallidos"""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            user = User.objects.get(email=email)
            user.login_attempts = 0
            user.locked_until = None
            user.save()
        except User.DoesNotExist:
            pass


class BetLimitValidator:
    """Validar límites de apuestas para prevenir problemas de juego"""

    @staticmethod
    def validate_bet(user, bet_amount: float, game_type: str) -> dict:
        """
        Valida que la apuesta cumpla los límites

        Retorna: {valid: bool, message: str}
        """
        from decimal import Decimal
        bet = Decimal(str(bet_amount))

        # Mínimo y máximo global
        MIN_BET = Decimal('1.00')
        MAX_BET = Decimal('1000.00')

        if bet < MIN_BET:
            return {'valid': False, 'message': f'Apuesta mínima: ${MIN_BET}'}

        if bet > MAX_BET:
            return {'valid': False, 'message': f'Apuesta máxima: ${MAX_BET}'}

        # Validar contra balance
        if user.balance < bet:
            return {'valid': False, 'message': 'Saldo insuficiente'}

        # Límites por juego
        game_limits = {
            'slots': {'max': Decimal('500.00'), 'min': Decimal('1.00')},
            'panda_mines': {'max': Decimal('750.00'), 'min': Decimal('1.00')},
            'roulette': {'max': Decimal('1000.00'), 'min': Decimal('1.00')},
            'golden_jet': {'max': Decimal('500.00'), 'min': Decimal('1.00')},
            'cyber_rolett': {'max': Decimal('750.00'), 'min': Decimal('1.00')},
            'personajes': {'max': Decimal('600.00'), 'min': Decimal('1.00')},
        }

        if game_type in game_limits:
            limits = game_limits[game_type]
            if bet > limits['max']:
                return {'valid': False, 'message': f'Apuesta máxima para este juego: ${limits["max"]}'}

        # Validar velocidad de apuestas (máx 1 apuesta cada 2 segundos)
        from apps.games.models import GameResult
        from django.utils import timezone
        from datetime import timedelta

        last_game = GameResult.objects.filter(user=user).order_by('-created_at').first()
        if last_game:
            seconds_since_last = (timezone.now() - last_game.created_at).total_seconds()
            if seconds_since_last < 2:
                return {'valid': False, 'message': 'Espera antes de apostar nuevamente'}

        return {'valid': True, 'message': 'Apuesta válida'}

    @staticmethod
    def get_daily_stats(user) -> dict:
        """Obtener estadísticas diarias de apuestas"""
        from apps.games.models import GameResult
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        games_today = GameResult.objects.filter(
            user=user,
            created_at__gte=today_start
        )

        total_bet = sum(g.bet_amount for g in games_today)
        total_payout = sum(g.payout for g in games_today)
        total_loss = sum(max(0, -g.profit_loss) for g in games_today)
        total_win = sum(max(0, g.profit_loss) for g in games_today)

        return {
            'games_played': games_today.count(),
            'total_bet': float(total_bet),
            'total_payout': float(total_payout),
            'total_win': float(total_win),
            'total_loss': float(total_loss),
            'net_result': float(total_payout - total_bet)
        }

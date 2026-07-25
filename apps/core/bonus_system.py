"""
Sistema de bonificaciones para el casino
"""

from django.db import models, transaction
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta


class BonusManager:
    """Administrar bonificaciones de usuarios"""

    BONUS_TYPES = {
        'welcome': {
            'name': 'Bono de Bienvenida',
            'amount': Decimal('50.00'),
            'description': 'Bono al crear cuenta'
        },
        'first_deposit': {
            'name': 'Bono Primer Depósito',
            'amount_percent': Decimal('100'),  # 100% del depósito
            'max_amount': Decimal('200.00'),
            'description': 'Duplica tu primer depósito'
        },
        'daily_bonus': {
            'name': 'Bono Diario',
            'amount': Decimal('10.00'),
            'description': 'Bono por jugar hoy'
        },
        'weekend_bonus': {
            'name': 'Bono de Fin de Semana',
            'amount_percent': Decimal('50'),
            'max_amount': Decimal('100.00'),
            'description': '50% extra en depósitos fin de semana'
        },
        'loyalty_bonus': {
            'name': 'Bono por Lealtad',
            'amount_percent': Decimal('10'),
            'description': '10% bonus por cada $100 jugados'
        },
        'referral': {
            'name': 'Bono por Referrer',
            'amount': Decimal('25.00'),
            'description': 'Bono cuando refierres un amigo'
        }
    }

    @staticmethod
    def add_welcome_bonus(user):
        """Dar bono de bienvenida al crear cuenta"""
        bonus_type = BonusManager.BONUS_TYPES['welcome']
        bonus_amount = bonus_type['amount']

        with transaction.atomic():
            user.bonus_balance += bonus_amount
            user.save()

            # Registrar en historial
            BonusHistory.objects.create(
                user=user,
                bonus_type='welcome',
                amount=bonus_amount,
                description=bonus_type['description'],
                status='active'
            )

        return {
            'success': True,
            'bonus_type': 'welcome',
            'amount': float(bonus_amount),
            'new_bonus_balance': float(user.bonus_balance)
        }

    @staticmethod
    def add_first_deposit_bonus(user, deposit_amount: Decimal):
        """Dar bono por primer depósito (100% hasta $200)"""
        from apps.payments.models import Transaction

        # Verificar que es el primer depósito
        previous_deposits = Transaction.objects.filter(
            user=user,
            transaction_type='deposit',
            status='completed'
        ).count()

        if previous_deposits > 0:
            return {'success': False, 'message': 'Este usuario ya recibió bonificación de primer depósito'}

        bonus_type = BonusManager.BONUS_TYPES['first_deposit']
        bonus_amount = min(
            deposit_amount * (bonus_type['amount_percent'] / Decimal('100')),
            bonus_type['max_amount']
        )

        with transaction.atomic():
            user.bonus_balance += bonus_amount
            user.save()

            BonusHistory.objects.create(
                user=user,
                bonus_type='first_deposit',
                amount=bonus_amount,
                description=f"Bono 100% en depósito de ${float(deposit_amount):.2f}",
                status='active',
                metadata={
                    'deposit_amount': float(deposit_amount),
                    'bonus_percent': 100
                }
            )

        return {
            'success': True,
            'bonus_type': 'first_deposit',
            'amount': float(bonus_amount),
            'new_bonus_balance': float(user.bonus_balance)
        }

    @staticmethod
    def add_daily_bonus(user):
        """Dar bono diario si no lo recibió hoy"""
        # Verificar que no lo recibió hoy
        today = timezone.now().date()
        today_bonus = BonusHistory.objects.filter(
            user=user,
            bonus_type='daily_bonus',
            created_at__date=today
        ).exists()

        if today_bonus:
            return {'success': False, 'message': 'Ya recibiste tu bono diario hoy'}

        bonus_type = BonusManager.BONUS_TYPES['daily_bonus']
        bonus_amount = bonus_type['amount']

        with transaction.atomic():
            user.bonus_balance += bonus_amount
            user.save()

            BonusHistory.objects.create(
                user=user,
                bonus_type='daily_bonus',
                amount=bonus_amount,
                description=bonus_type['description'],
                status='active'
            )

        return {
            'success': True,
            'bonus_type': 'daily_bonus',
            'amount': float(bonus_amount),
            'new_bonus_balance': float(user.bonus_balance)
        }

    @staticmethod
    def add_loyalty_bonus(user):
        """Dar bono por lealtad basado en dinero jugado"""
        from apps.games.models import GameResult

        # Calcular total jugado este mes
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        games_this_month = GameResult.objects.filter(
            user=user,
            created_at__gte=month_start
        )

        total_bets = sum(g.bet_amount for g in games_this_month)

        # Bono por cada $100 jugados (máx 1 vez por mes)
        loyalty_bonuses_this_month = BonusHistory.objects.filter(
            user=user,
            bonus_type='loyalty_bonus',
            created_at__gte=month_start
        ).count()

        if loyalty_bonuses_this_month >= 1:
            return {'success': False, 'message': 'Ya recibiste tu bono de lealtad este mes'}

        bonus_amount = (total_bets / Decimal('100')) * Decimal('10')  # 10% de cada $100

        if bonus_amount < Decimal('1'):
            return {'success': False, 'message': 'No has jugado lo suficiente para bono de lealtad'}

        with transaction.atomic():
            user.bonus_balance += bonus_amount
            user.save()

            BonusHistory.objects.create(
                user=user,
                bonus_type='loyalty_bonus',
                amount=bonus_amount,
                description=f"Bono por lealtad - ${float(total_bets):.2f} jugados",
                status='active',
                metadata={'total_bets': float(total_bets)}
            )

        return {
            'success': True,
            'bonus_type': 'loyalty_bonus',
            'amount': float(bonus_amount),
            'new_bonus_balance': float(user.bonus_balance)
        }

    @staticmethod
    def use_bonus(user, amount: Decimal):
        """Usar balance de bonus para apuestas"""
        if user.bonus_balance < amount:
            return {'success': False, 'message': 'Saldo de bonus insuficiente'}

        with transaction.atomic():
            user.bonus_balance -= amount
            user.save()

        return {'success': True, 'remaining_bonus': float(user.bonus_balance)}

    @staticmethod
    def convert_bonus_to_cash(user, amount: Decimal = None):
        """Convertir bonus a dinero (requiere 10x rollover)"""
        if amount is None:
            amount = user.bonus_balance

        if amount <= 0:
            return {'success': False, 'message': 'Monto de bonus inválido'}

        if user.bonus_balance < amount:
            return {'success': False, 'message': 'Saldo de bonus insuficiente'}

        # Verificar rollover (10x del monto)
        from apps.games.models import GameResult
        bonus_history = BonusHistory.objects.filter(
            user=user,
            status='active'
        )

        total_bonus_given = sum(b.amount for b in bonus_history)
        required_rollover = total_bonus_given * Decimal('10')

        games = GameResult.objects.filter(user=user)
        total_bet = sum(g.bet_amount for g in games)

        if total_bet < required_rollover:
            return {
                'success': False,
                'message': f'Debes apostar ${float(required_rollover):.2f} para convertir bonus',
                'current_bet': float(total_bet),
                'required_rollover': float(required_rollover)
            }

        with transaction.atomic():
            user.bonus_balance -= amount
            user.balance += amount
            user.save()

            BonusHistory.objects.filter(status='active').update(status='converted')

        return {
            'success': True,
            'converted_amount': float(amount),
            'new_balance': float(user.balance),
            'new_bonus_balance': float(user.bonus_balance)
        }

    @staticmethod
    def get_bonus_info(user) -> dict:
        """Obtener información sobre bonificaciones del usuario"""
        active_bonuses = BonusHistory.objects.filter(user=user, status='active')

        return {
            'total_bonus_balance': float(user.bonus_balance),
            'active_bonuses': [
                {
                    'type': b.bonus_type,
                    'amount': float(b.amount),
                    'description': b.description,
                    'created_at': b.created_at.isoformat()
                }
                for b in active_bonuses
            ],
            'bonus_types_available': list(BonusManager.BONUS_TYPES.keys())
        }


# Modelo BonusHistory creado con migraciones
# from apps.core.models import BonusHistory
# (Ver PASO_6_AVANZADO.md para crear migraciones)

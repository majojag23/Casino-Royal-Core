"""
Sistema de analítica y estadísticas
"""

from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from collections import defaultdict


class UserAnalytics:
    """Análisis de actividad del usuario"""

    @staticmethod
    def get_user_stats(user) -> dict:
        """Obtener estadísticas completas del usuario"""
        from apps.games.models import GameResult
        from apps.payments.models import Transaction

        games = GameResult.objects.filter(user=user)
        transactions = Transaction.objects.filter(user=user)

        total_bet = sum(g.bet_amount for g in games) if games else Decimal('0')
        total_payout = sum(g.payout for g in games) if games else Decimal('0')
        total_profit = sum(g.profit_loss for g in games) if games else Decimal('0')
        games_won = games.filter(profit_loss__gt=0).count() if games else 0
        games_lost = games.filter(profit_loss__lte=0).count() if games else 0

        total_deposited = sum(
            t.amount for t in transactions.filter(transaction_type='deposit', status='completed')
        ) if transactions else Decimal('0')

        total_withdrawn = sum(
            t.amount for t in transactions.filter(transaction_type='withdrawal', status='completed')
        ) if transactions else Decimal('0')

        return {
            'total_games': games.count(),
            'total_bet': float(total_bet),
            'total_payout': float(total_payout),
            'total_profit_loss': float(total_profit),
            'games_won': games_won,
            'games_lost': games_lost,
            'win_rate': (games_won / games.count() * 100) if games.count() > 0 else 0,
            'average_bet': float(total_bet / games.count()) if games.count() > 0 else 0,
            'total_deposited': float(total_deposited),
            'total_withdrawn': float(total_withdrawn),
            'current_balance': float(user.balance),
            'account_age_days': (timezone.now() - user.created_at).days,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }

    @staticmethod
    def get_daily_stats(user, days: int = 30) -> list:
        """Obtener estadísticas diarias"""
        from apps.games.models import GameResult

        stats = defaultdict(lambda: {
            'games': 0,
            'total_bet': Decimal('0'),
            'total_payout': Decimal('0'),
            'total_profit': Decimal('0')
        })

        start_date = timezone.now() - timedelta(days=days)
        games = GameResult.objects.filter(
            user=user,
            created_at__gte=start_date
        )

        for game in games:
            date = game.created_at.date()
            stats[date]['games'] += 1
            stats[date]['total_bet'] += game.bet_amount
            stats[date]['total_payout'] += game.payout
            stats[date]['total_profit'] += game.profit_loss

        result = []
        for date in sorted(stats.keys()):
            s = stats[date]
            result.append({
                'date': str(date),
                'games': s['games'],
                'total_bet': float(s['total_bet']),
                'total_payout': float(s['total_payout']),
                'total_profit': float(s['total_profit']),
                'average_bet': float(s['total_bet'] / s['games']) if s['games'] > 0 else 0
            })

        return result

    @staticmethod
    def get_game_stats(user) -> dict:
        """Estadísticas por juego"""
        from apps.games.models import GameResult

        games = GameResult.objects.filter(user=user)
        stats_by_game = defaultdict(lambda: {
            'count': 0,
            'total_bet': Decimal('0'),
            'total_payout': Decimal('0'),
            'total_profit': Decimal('0'),
            'games_won': 0
        })

        for game in games:
            game_type = game.game_type
            stats_by_game[game_type]['count'] += 1
            stats_by_game[game_type]['total_bet'] += game.bet_amount
            stats_by_game[game_type]['total_payout'] += game.payout
            stats_by_game[game_type]['total_profit'] += game.profit_loss
            if game.profit_loss > 0:
                stats_by_game[game_type]['games_won'] += 1

        result = {}
        for game_type, stats in stats_by_game.items():
            result[game_type] = {
                'games_played': stats['count'],
                'total_bet': float(stats['total_bet']),
                'total_payout': float(stats['total_payout']),
                'total_profit': float(stats['total_profit']),
                'games_won': stats['games_won'],
                'win_rate': (stats['games_won'] / stats['count'] * 100) if stats['count'] > 0 else 0,
                'average_bet': float(stats['total_bet'] / stats['count']) if stats['count'] > 0 else 0
            }

        return result


class CasinoAnalytics:
    """Análisis a nivel de casino"""

    @staticmethod
    def get_casino_stats() -> dict:
        """Estadísticas generales del casino"""
        from django.contrib.auth import get_user_model
        from apps.games.models import GameResult
        from apps.payments.models import Transaction

        User = get_user_model()

        total_users = User.objects.count()
        active_users_today = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(hours=24)
        ).count()

        games = GameResult.objects.all()
        total_games = games.count()
        total_bets = sum(g.bet_amount for g in games) if games else Decimal('0')
        total_payouts = sum(g.payout for g in games) if games else Decimal('0')
        total_casino_profit = total_bets - total_payouts

        transactions = Transaction.objects.filter(status='completed')
        total_deposits = sum(
            t.amount for t in transactions.filter(transaction_type='deposit')
        ) if transactions else Decimal('0')

        total_withdrawals = sum(
            t.amount for t in transactions.filter(transaction_type='withdrawal')
        ) if transactions else Decimal('0')

        return {
            'total_users': total_users,
            'active_users_today': active_users_today,
            'total_games_played': total_games,
            'total_bets': float(total_bets),
            'total_payouts': float(total_payouts),
            'casino_profit': float(total_casino_profit),
            'total_deposits': float(total_deposits),
            'total_withdrawals': float(total_withdrawals),
            'net_revenue': float(total_deposits - total_withdrawals),
            'rtp': float((total_payouts / total_bets * 100)) if total_bets > 0 else 0
        }

    @staticmethod
    def get_game_popularity() -> dict:
        """Juegos más jugados"""
        from apps.games.models import GameResult
        from django.db.models import Count

        games_count = GameResult.objects.values('game_type').annotate(
            count=Count('id')
        ).order_by('-count')

        return {
            game['game_type']: game['count']
            for game in games_count
        }

    @staticmethod
    def get_hourly_activity() -> dict:
        """Actividad por hora del día"""
        from apps.games.models import GameResult
        from django.db.models import Count

        games_by_hour = {}
        for hour in range(24):
            games_by_hour[f"{hour:02d}:00"] = 0

        games = GameResult.objects.all()
        for game in games:
            hour = game.created_at.hour
            games_by_hour[f"{hour:02d}:00"] += 1

        return games_by_hour

    @staticmethod
    def get_revenue_by_period(period: str = 'daily') -> dict:
        """Ingresos por período"""
        from apps.games.models import GameResult
        from apps.payments.models import Transaction

        result = {}

        if period == 'daily':
            days = 30
            format_str = '%Y-%m-%d'
        elif period == 'weekly':
            days = 90
            format_str = '%Y-W%V'
        elif period == 'monthly':
            days = 365
            format_str = '%Y-%m'
        else:
            return {}

        start_date = timezone.now() - timedelta(days=days)

        games = GameResult.objects.filter(created_at__gte=start_date)
        for game in games:
            date_key = game.created_at.strftime(format_str)
            if date_key not in result:
                result[date_key] = {'bets': Decimal('0'), 'payouts': Decimal('0')}
            result[date_key]['bets'] += game.bet_amount
            result[date_key]['payouts'] += game.payout

        # Convertir a float
        for date_key in result:
            result[date_key]['bets'] = float(result[date_key]['bets'])
            result[date_key]['payouts'] = float(result[date_key]['payouts'])
            result[date_key]['profit'] = result[date_key]['bets'] - result[date_key]['payouts']

        return result


class RiskManagement:
    """Gestión de riesgo y detección de anomalías"""

    @staticmethod
    def check_betting_anomaly(user) -> dict:
        """Verificar comportamiento anómalo de apuestas"""
        from apps.games.models import GameResult

        last_24_hours = timezone.now() - timedelta(hours=24)
        games_24h = GameResult.objects.filter(
            user=user,
            created_at__gte=last_24_hours
        )

        total_loss_24h = sum(
            max(0, -g.profit_loss) for g in games_24h
        )

        alerts = []

        # Alerta si perdió más de $500 en 24h
        if total_loss_24h > Decimal('500'):
            alerts.append({
                'type': 'high_loss',
                'severity': 'warning',
                'message': f'Pérdida de ${float(total_loss_24h):.2f} en 24 horas',
                'amount': float(total_loss_24h)
            })

        # Alerta si jugó más de 100 juegos en 24h
        if games_24h.count() > 100:
            alerts.append({
                'type': 'excessive_gaming',
                'severity': 'warning',
                'message': f'{games_24h.count()} juegos en 24 horas',
                'count': games_24h.count()
            })

        # Alerta si la tasa de pérdida es > 80%
        games_lost = games_24h.filter(profit_loss__lte=0).count()
        if games_24h.count() > 0 and games_lost / games_24h.count() > 0.8:
            alerts.append({
                'type': 'high_loss_rate',
                'severity': 'warning',
                'message': f'Tasa de pérdida: {(games_lost/games_24h.count()*100):.1f}%',
                'loss_rate': games_lost / games_24h.count()
            })

        return {
            'has_anomalies': len(alerts) > 0,
            'alerts': alerts,
            'total_games_24h': games_24h.count(),
            'total_loss_24h': float(total_loss_24h)
        }

    @staticmethod
    def send_anomaly_alert(user, anomaly_info: dict):
        """Enviar alerta si se detecta comportamiento anómalo"""
        if anomaly_info['has_anomalies']:
            from apps.core.email_notifications import EmailNotifier

            alert_details = {
                'alerts': anomaly_info['alerts'],
                'recommendations': [
                    'Considera tomar un descanso',
                    'Establece límites de apuesta',
                    'Contáctanos si necesitas ayuda con el juego responsable'
                ]
            }

            EmailNotifier.send_account_security_alert(
                user=user,
                alert_type='unusual_betting_pattern',
                details=alert_details
            )

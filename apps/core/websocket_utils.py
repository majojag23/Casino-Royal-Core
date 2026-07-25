"""
Utilidades para integración de WebSockets en API endpoints
"""

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import datetime
import json


class WebSocketBroadcaster:
    """
    Clase para enviar eventos a través de WebSockets
    """

    @staticmethod
    def broadcast_balance_update(user_id, balance, timestamp=None):
        """Envía actualización de balance a un usuario"""
        channel_layer = get_channel_layer()
        room_group_name = f'balance_{user_id}'

        if timestamp is None:
            timestamp = datetime.now().isoformat()

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'balance_update',
                'balance': str(balance),
                'timestamp': timestamp
            }
        )

    @staticmethod
    def broadcast_game_result(user_id, game_type, bet, payout, profit_loss, new_balance):
        """Envía resultado de juego a un usuario"""
        channel_layer = get_channel_layer()
        balance_room = f'balance_{user_id}'
        game_stream = f'game_stream_{game_type}'

        timestamp = datetime.now().isoformat()

        async_to_sync(channel_layer.group_send)(
            balance_room,
            {
                'type': 'game_result',
                'game': game_type,
                'bet': str(bet),
                'payout': str(payout),
                'profit_loss': str(profit_loss),
                'new_balance': str(new_balance),
                'timestamp': timestamp
            }
        )

        async_to_sync(channel_layer.group_send)(
            game_stream,
            {
                'type': 'game_event',
                'game': game_type,
                'player': f'usuario_{user_id}',
                'bet': str(bet),
                'result': 'win' if profit_loss > 0 else 'loss',
                'payout': str(payout),
                'timestamp': timestamp
            }
        )

    @staticmethod
    def send_notification(user_id, title, message, level='info'):
        """Envía una notificación a un usuario"""
        channel_layer = get_channel_layer()
        room_group_name = f'notifications_{user_id}'
        timestamp = datetime.now().isoformat()

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'send_notification',
                'title': title,
                'message': message,
                'level': level,
                'timestamp': timestamp
            }
        )

    @staticmethod
    def update_leaderboard(leaderboard_data):
        """Actualiza el leaderboard para todos los usuarios"""
        channel_layer = get_channel_layer()
        room_group_name = 'leaderboard'
        timestamp = datetime.now().isoformat()

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'leaderboard_update',
                'leaderboard': leaderboard_data,
                'timestamp': timestamp
            }
        )

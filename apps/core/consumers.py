"""
WebSocket Consumers para comunicación en tiempo real
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class BalanceConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer para actualizaciones de balance en tiempo real
    Conecta: ws://localhost:8000/ws/balance/{user_id}/
    """

    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'balance_{self.user_id}'

        # Verificar que el usuario está autenticado
        user = await self.get_user(self.user_id)
        if not user:
            await self.close()
            return

        # Unirse al grupo
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Enviar balance inicial
        balance = await self.get_user_balance(self.user_id)
        await self.send(text_data=json.dumps({
            'type': 'balance_update',
            'balance': str(balance),
            'status': 'connected'
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def balance_update(self, event):
        """Enviar actualización de balance"""
        await self.send(text_data=json.dumps({
            'type': 'balance_update',
            'balance': event['balance'],
            'timestamp': event['timestamp']
        }))

    async def game_result(self, event):
        """Enviar resultado de juego"""
        await self.send(text_data=json.dumps({
            'type': 'game_result',
            'game': event['game'],
            'bet': event['bet'],
            'payout': event['payout'],
            'profit_loss': event['profit_loss'],
            'new_balance': event['new_balance'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_user_balance(self, user_id):
        try:
            user = User.objects.get(id=user_id)
            return str(user.balance)
        except User.DoesNotExist:
            return "0.00"


class LeaderboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer para tablero de líderes en tiempo real
    Conecta: ws://localhost:8000/ws/leaderboard/
    """

    async def connect(self):
        self.room_group_name = 'leaderboard'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Enviar leaderboard inicial
        leaderboard = await self.get_leaderboard()
        await self.send(text_data=json.dumps({
            'type': 'leaderboard_update',
            'leaderboard': leaderboard,
            'status': 'connected'
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def leaderboard_update(self, event):
        """Enviar actualización del leaderboard"""
        await self.send(text_data=json.dumps({
            'type': 'leaderboard_update',
            'leaderboard': event['leaderboard'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def get_leaderboard(self):
        from apps.users.models import CustomUser

        users = CustomUser.objects.all().order_by('-balance')[:10]
        leaderboard = []

        for idx, user in enumerate(users, 1):
            leaderboard.append({
                'rank': idx,
                'username': user.email.split('@')[0],
                'balance': str(user.balance),
                'verified': user.kyc_verified
            })

        return leaderboard


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer para notificaciones en tiempo real
    Conecta: ws://localhost:8000/ws/notifications/{user_id}/
    """

    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'notifications_{self.user_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def send_notification(self, event):
        """Enviar notificación"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'title': event['title'],
            'message': event['message'],
            'level': event.get('level', 'info'),  # info, success, warning, error
            'timestamp': event['timestamp']
        }))


class GameStreamConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer para stream de juegos en vivo
    Conecta: ws://localhost:8000/ws/game_stream/{game_type}/
    """

    async def connect(self):
        self.game_type = self.scope['url_route']['kwargs']['game_type']
        self.room_group_name = f'game_stream_{self.game_type}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        await self.send(text_data=json.dumps({
            'type': 'stream_status',
            'game': self.game_type,
            'status': 'watching',
            'viewers': 1
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def game_event(self, event):
        """Enviar evento de juego"""
        await self.send(text_data=json.dumps({
            'type': 'game_event',
            'game': event['game'],
            'player': event['player'],
            'bet': event['bet'],
            'result': event['result'],
            'payout': event['payout'],
            'timestamp': event['timestamp']
        }))

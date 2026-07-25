import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino_project.settings')

django_asgi_app = get_asgi_application()

from apps.core.consumers import (
    BalanceConsumer,
    LeaderboardConsumer,
    NotificationConsumer,
    GameStreamConsumer
)

websocket_urlpatterns = [
    path('ws/balance/<int:user_id>/', BalanceConsumer.as_asgi()),
    path('ws/leaderboard/', LeaderboardConsumer.as_asgi()),
    path('ws/notifications/<int:user_id>/', NotificationConsumer.as_asgi()),
    path('ws/game_stream/<str:game_type>/', GameStreamConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})

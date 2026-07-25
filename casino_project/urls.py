from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.shortcuts import render


def reset_password_view(request, token):
    return render(request, 'auth/reset_password.html', {'token': token})

def deposit_view(request):
    return render(request, 'payments/deposit.html', {'stripe_key': settings.STRIPE_PUBLISHABLE_KEY})

def casino_home(request):
    return HttpResponse("""
    <html>
    <head>
        <title>Casino Online - Bienvenido</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; background: #080254; color: #fff; }
            h1 { color: #F44CFC; }
            .button { background: #741AC0; color: white; padding: 10px 20px; margin: 10px; text-decoration: none; border-radius: 5px; }
            .button:hover { background: #F44CFC; }
        </style>
    </head>
    <body>
        <h1>🎰 Casino Online</h1>
        <p>¡Bienvenido al Casino Online construido con Django!</p>
        <br>
        <a href="/admin/" class="button">Panel Admin</a>
        <a href="/lobby/" class="button">Lobby de Juegos</a>
        <a href="/login/" class="button">Login</a>
        <br><br>
        <h3>Credenciales de Prueba:</h3>
        <p>Admin (usar username, no email): admin / admin123<br>
        Usuario: usuario1@casino.com / TestPass123!</p>
    </body>
    </html>
    """)

urlpatterns = [
    path('', casino_home, name='home'),
    path('admin/', admin.site.urls),
    path('api/users/', include('apps.users.urls')),
    path('api/games/', include('apps.games.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/admin/', include('apps.admin_panel.urls')),

    # Frontend URLs
    path('lobby/', TemplateView.as_view(template_name='games/lobby.html'), name='games-lobby'),
    path('login/', TemplateView.as_view(template_name='auth/login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='auth/register.html'), name='register'),
    path('forgot-password/', TemplateView.as_view(template_name='auth/forgot_password.html'), name='forgot-password'),
    path('reset-password/<str:token>/', reset_password_view, name='reset-password'),
    path('profile/', TemplateView.as_view(template_name='profile/dashboard.html'), name='profile-dashboard'),
    path('promos/', TemplateView.as_view(template_name='promos.html'), name='promos'),
    path('vip/', TemplateView.as_view(template_name='vip.html'), name='vip'),
    path('games/neon_slots/', TemplateView.as_view(template_name='games/neon_slots.html'), name='game-neon-slots'),
    path('games/farm_fest/', TemplateView.as_view(template_name='games/farm_fest_slots.html'), name='game-farm-fest'),
    path('games/duck_rush/', TemplateView.as_view(template_name='games/duck_rush.html'), name='game-duck-rush'),
    path('games/panda_mines/', TemplateView.as_view(template_name='games/panda_mines.html'), name='game-panda-mines'),
    path('games/cyber_rolett/', TemplateView.as_view(template_name='games/cyber_rolett.html'), name='game-cyber-rolett'),
    path('games/golden_jet/', TemplateView.as_view(template_name='games/golden_jet.html'), name='game-golden-jet'),
    path('games/dragon_fruit/', TemplateView.as_view(template_name='games/dragon_fruit.html'), name='game-dragon-fruit'),
    path('games/totem_falls/', TemplateView.as_view(template_name='games/totem_falls.html'), name='game-totem-falls'),
    path('games/golden_sling_rush/', TemplateView.as_view(template_name='games/golden_sling_rush.html'), name='game-golden-sling-rush'),
    path('games/bird_blast/', TemplateView.as_view(template_name='games/golden_sling_rush.html'), name='game-bird-blast'),
    path('games/frozen_age/', TemplateView.as_view(template_name='games/frozen_age.html'), name='game-frozen-age'),
    path('deposit/', deposit_view, name='deposit'),
    path('withdraw/', TemplateView.as_view(template_name='payments/withdraw.html'), name='withdraw'),
    path('panel/', TemplateView.as_view(template_name='admin/dashboard.html'), name='admin-dashboard'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

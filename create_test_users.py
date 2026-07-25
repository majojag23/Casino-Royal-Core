#!/usr/bin/env python
"""
Script para crear usuarios de prueba en el casino online
Uso: python manage.py shell < create_test_users.py
O: python create_test_users.py
"""

import os
import django
from django.utils import timezone
from datetime import timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino_project.settings')
django.setup()

from apps.users.models import CustomUser, LoginHistory
from apps.games.models import GameResult
from apps.payments.models import Transaction
from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_users():
    """Crear usuarios de prueba"""

    test_users = [
        {
            'email': 'usuario1@casino.com',
            'password': 'TestPass123!',
            'first_name': 'Juan',
            'last_name': 'García',
            'phone': '+573001234567',
            'document_type': 'CC',
            'document_number': '12345678',
            'date_of_birth': '1990-05-15',
            'country': 'Colombia',
            'balance': 1500.00,
            'kyc_verified': True,
            'email_verified': True,
            'document_verified': True,
        },
        {
            'email': 'usuario2@casino.com',
            'password': 'TestPass123!',
            'first_name': 'María',
            'last_name': 'López',
            'phone': '+573109876543',
            'document_type': 'CC',
            'document_number': '87654321',
            'date_of_birth': '1992-08-20',
            'country': 'Colombia',
            'balance': 2500.50,
            'kyc_verified': True,
            'email_verified': True,
            'document_verified': True,
        },
        {
            'email': 'usuario3@casino.com',
            'password': 'TestPass123!',
            'first_name': 'Carlos',
            'last_name': 'Rodríguez',
            'phone': '+573105555555',
            'document_type': 'CE',
            'document_number': '11111111',
            'date_of_birth': '1988-12-10',
            'country': 'Colombia',
            'balance': 750.25,
            'kyc_verified': False,
            'email_verified': True,
            'document_verified': False,
        },
        {
            'email': 'admin@casino.com',
            'password': 'AdminPass123!',
            'first_name': 'Admin',
            'last_name': 'Casino',
            'phone': '+573217777777',
            'document_type': 'CC',
            'document_number': '99999999',
            'date_of_birth': '1985-01-01',
            'country': 'Colombia',
            'balance': 10000.00,
            'kyc_verified': True,
            'email_verified': True,
            'document_verified': True,
            'is_staff': True,
            'is_superuser': True,
        },
        {
            'email': 'demo@casino.com',
            'password': 'DemoPass123!',
            'first_name': 'Demo',
            'last_name': 'User',
            'phone': '+573218888888',
            'document_type': 'PP',
            'document_number': '22222222',
            'date_of_birth': '1995-06-15',
            'country': 'Colombia',
            'balance': 500.00,
            'bonus_balance': 100.00,
            'kyc_verified': True,
            'email_verified': True,
            'document_verified': True,
        },
    ]

    created_users = []
    for user_data in test_users:
        email = user_data.pop('email')
        password = user_data.pop('password')

        # Verificar si el usuario ya existe
        if User.objects.filter(email=email).exists():
            print(f"⚠️  Usuario {email} ya existe, saltando...")
            continue

        # Crear usuario
        user = User.objects.create_user(
            email=email,
            password=password,
            username=email.split('@')[0],
            **user_data
        )

        created_users.append(user)
        print(f"✅ Usuario creado: {email} (Balance: ${user.balance})")

    return created_users

def create_game_history(users):
    """Crear historial de juegos para los usuarios"""

    games = ['slots', 'panda_mines', 'roulette', 'golden_jet', 'cyber_rolett', 'personajes']

    for user in users:
        if user.email == 'admin@casino.com':
            continue  # Skip admin

        # Crear 5 resultados de juegos por usuario
        for i in range(5):
            game_type = games[i % len(games)]
            bet_amount = 10 + (i * 5)

            # Generar resultado aleatorio
            import random
            if random.random() > 0.6:  # 40% de ganancias
                payout = bet_amount * random.choice([2, 3, 5, 10])
                profit_loss = payout - bet_amount
            else:
                payout = 0
                profit_loss = -bet_amount

            GameResult.objects.create(
                user=user,
                game_type=game_type,
                bet_amount=bet_amount,
                payout=payout,
                profit_loss=profit_loss,
                result={
                    'spin': random.randint(1, 10),
                    'multiplier': payout / bet_amount if payout > 0 else 0
                }
            )

        print(f"  📊 Historial de juegos creado para {user.email}")

def create_transaction_history(users):
    """Crear historial de transacciones"""

    for user in users:
        if user.email == 'admin@casino.com':
            continue  # Skip admin

        # Depósito inicial
        Transaction.objects.create(
            user=user,
            type='deposit',
            amount=user.balance,
            status='completed',
            payment_method='stripe'
        )

        # Algunos retiros
        import random
        if random.random() > 0.5:
            Transaction.objects.create(
                user=user,
                type='withdrawal',
                amount=random.randint(50, 300),
                status='completed',
                payment_method='bank_transfer'
            )

        print(f"  💰 Transacciones creadas para {user.email}")

def create_login_history(users):
    """Crear historial de logins"""

    for user in users:
        if user.email == 'admin@casino.com':
            continue

        # 3 logins recientes
        for i in range(3):
            LoginHistory.objects.create(
                user=user,
                ip_address=f'192.168.1.{100 + i}',
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
                login_time=timezone.now() - timedelta(days=i)
            )

        print(f"  🔐 Historial de login creado para {user.email}")

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("🎰 CREANDO USUARIOS DE PRUEBA PARA CASINO ONLINE")
    print("="*60 + "\n")

    print("📝 Creando usuarios...")
    users = create_test_users()

    if not users:
        print("❌ No se crearon usuarios nuevos")
        return

    print("\n📊 Creando historial de juegos...")
    create_game_history(users)

    print("\n💰 Creando historial de transacciones...")
    create_transaction_history(users)

    print("\n🔐 Creando historial de login...")
    create_login_history(users)

    print("\n" + "="*60)
    print("✅ ¡USUARIOS DE PRUEBA CREADOS EXITOSAMENTE!")
    print("="*60)
    print("\n📧 CREDENCIALES DE ACCESO:\n")

    test_accounts = [
        ('usuario1@casino.com', 'TestPass123!', 'Usuario Regular 1'),
        ('usuario2@casino.com', 'TestPass123!', 'Usuario Regular 2'),
        ('usuario3@casino.com', 'TestPass123!', 'Usuario Regular 3 (Sin KYC)'),
        ('demo@casino.com', 'DemoPass123!', 'Cuenta Demo'),
        ('admin@casino.com', 'AdminPass123!', 'Admin/Superuser'),
    ]

    for email, password, description in test_accounts:
        print(f"  📌 {description}")
        print(f"     Email: {email}")
        print(f"     Pass:  {password}")
        print()

    print("="*60)
    print("🌐 Acceso:")
    print("  Login: http://localhost:8000/login/")
    print("  Admin: http://localhost:8000/admin/")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()

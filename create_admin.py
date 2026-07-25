#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Crear admin
try:
    admin = User.objects.create_superuser(
        email='admin@casino.com',
        username='admin',
        password='AdminPass123!',
        first_name='Admin',
        last_name='Casino'
    )
    print(f"[OK] Admin creado: {admin.email}")
except Exception as e:
    print(f"[ERROR] {str(e)}")

# Crear usuarios de prueba
test_users = [
    {'email': 'usuario1@casino.com', 'password': 'TestPass123!', 'first_name': 'Juan', 'last_name': 'Garcia', 'balance': 1500.00},
    {'email': 'usuario2@casino.com', 'password': 'TestPass123!', 'first_name': 'Maria', 'last_name': 'Lopez', 'balance': 2500.50},
]

for user_data in test_users:
    try:
        user = User.objects.create_user(
            email=user_data['email'],
            username=user_data['email'].split('@')[0],
            password=user_data['password'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            balance=user_data['balance'],
            kyc_verified=True
        )
        print(f"[OK] Usuario creado: {user.email} (${user.balance})")
    except Exception as e:
        print(f"[ERROR] {str(e)}")

print("[LISTO] Usuarios creados exitosamente!")

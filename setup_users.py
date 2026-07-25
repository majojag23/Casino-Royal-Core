#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino_project.settings')
sys.path.insert(0, '/Users/Asus/Desktop/casino-online')

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Datos de usuarios
usuarios = [
    ('usuario1@casino.com', 'TestPass123!', 'Juan', 'García', 1500.00),
    ('usuario2@casino.com', 'TestPass123!', 'María', 'López', 2500.50),
    ('usuario3@casino.com', 'TestPass123!', 'Carlos', 'Rodríguez', 750.25),
    ('demo@casino.com', 'DemoPass123!', 'Demo', 'User', 500.00),
]

print("Creando usuarios...")

for email, password, first, last, balance in usuarios:
    try:
        if not User.objects.filter(email=email).exists():
            user = User.objects.create_user(
                email=email,
                password=password,
                username=email.split('@')[0],
                first_name=first,
                last_name=last,
                balance=balance
            )
            print(f"  OK: {email} (${balance})")
        else:
            print(f"  SKIP: {email} existe")
    except Exception as e:
        print(f"  ERROR: {email} - {str(e)}")

# Admin
try:
    if not User.objects.filter(email='admin@casino.com').exists():
        User.objects.create_superuser(
            email='admin@casino.com',
            password='AdminPass123!',
            username='admin',
            first_name='Admin',
            last_name='Casino'
        )
        print(f"  OK: admin@casino.com")
    else:
        print(f"  SKIP: admin@casino.com existe")
except Exception as e:
    print(f"  ERROR: admin - {str(e)}")

print("\nUsuarios creados!")
print("\nCredenciales:")
print("  usuario1@casino.com / TestPass123!")
print("  usuario2@casino.com / TestPass123!")
print("  usuario3@casino.com / TestPass123!")
print("  demo@casino.com / DemoPass123!")
print("  admin@casino.com / AdminPass123!")

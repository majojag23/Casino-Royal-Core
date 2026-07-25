# 🚀 Guía de Deployment a Producción

## Resumen de Opciones

```
┌─────────────────────────────────────────────────────┐
│ OPCIONES DE DEPLOYMENT                              │
├─────────────────────────────────────────────────────┤
│ 1. Heroku     → PaaS, fácil, $7-50/mes            │
│ 2. DigitalOcean → VPS, flexible, $5-40/mes        │
│ 3. AWS        → Enterprise, escalable, variable   │
│ 4. Servidor Propio → Control total, complejidad   │
└─────────────────────────────────────────────────────┘
```

---

## 📋 Pre-requisitos Universales

### 1. Base de Datos PostgreSQL

```bash
# En tu servidor/contenedor
apt-get update
apt-get install postgresql postgresql-contrib

# Crear BD y usuario
sudo -u postgres psql

CREATE DATABASE casino_db;
CREATE USER casino_user WITH PASSWORD 'secure_password_here';
ALTER ROLE casino_user SET client_encoding TO 'utf8';
ALTER ROLE casino_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE casino_user SET default_transaction_deferrable TO on;
ALTER ROLE casino_user SET default_transaction_level TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE casino_db TO casino_user;
\q
```

### 2. Redis (para Celery y Cache)

```bash
apt-get install redis-server

# Iniciar
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 3. Dependencias del Sistema

```bash
apt-get install python3.11 python3.11-dev python3-pip
apt-get install build-essential libpq-dev
apt-get install curl git nginx supervisor
```

---

## 🐳 Opción 1: Docker (Recomendado)

### Crear Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements-dev.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copiar código
COPY . .

# Recolectar static files
RUN python manage.py collectstatic --noinput

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "casino_project.asgi:application"]
```

### Crear docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: casino_db
      POSTGRES_USER: casino_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: daphne -b 0.0.0.0 -p 8000 casino_project.asgi:application
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
    ports:
      - "8000:8000"
    environment:
      DEBUG: ${DEBUG}
      SECRET_KEY: ${SECRET_KEY}
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis

  celery:
    build: .
    command: celery -A casino_project worker -l info
    volumes:
      - .:/app
    environment:
      DEBUG: ${DEBUG}
      SECRET_KEY: ${SECRET_KEY}
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  static_volume:
```

### Iniciar con Docker

```bash
# Crear .env
cat > .env << EOF
DEBUG=False
SECRET_KEY=tu-clave-secreta-super-segura
DB_NAME=casino_db
DB_USER=casino_user
DB_PASSWORD=contraseña-segura
EOF

# Build y run
docker-compose build
docker-compose up -d

# Migraciones
docker-compose exec web python manage.py migrate

# Crear superuser
docker-compose exec web python manage.py createsuperuser
```

---

## ☁️ Opción 2: Heroku (Fácil)

### 1. Preparar Aplicación

```bash
# Crear Procfile
cat > Procfile << EOF
web: daphne -b 0.0.0.0 -p $PORT casino_project.asgi:application
worker: celery -A casino_project worker -l info
EOF

# Crear runtime.txt
echo "python-3.11.8" > runtime.txt

# Crear .gitignore
cat > .gitignore << EOF
*.pyc
__pycache__/
.env
*.egg-info/
db.sqlite3
EOF
```

### 2. Configurar para Heroku

```python
# settings.py - agregar al final
import dj_database_url
import os

# Database
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600
    )
}

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Whitelist de hosts
ALLOWED_HOSTS = ['*.herokuapp.com', 'tu-dominio.com']

# SSL
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Stripe
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@casino.com')

# Celery
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
```

### 3. Deploy en Heroku

```bash
# Login
heroku login

# Crear app
heroku create tu-casino-app

# Agregar PostgreSQL
heroku addons:create heroku-postgresql:standard-0 -a tu-casino-app

# Agregar Redis
heroku addons:create heroku-redis:premium-0 -a tu-casino-app

# Configurar variables
heroku config:set SECRET_KEY='tu-clave-secreta' -a tu-casino-app
heroku config:set DEBUG=False -a tu-casino-app
heroku config:set STRIPE_SECRET_KEY='sk_live_...' -a tu-casino-app
heroku config:set STRIPE_PUBLISHABLE_KEY='pk_live_...' -a tu-casino-app
heroku config:set EMAIL_HOST_USER='tu-email@gmail.com' -a tu-casino-app
heroku config:set EMAIL_HOST_PASSWORD='app-password' -a tu-casino-app

# Deploy
git push heroku main

# Migraciones
heroku run python manage.py migrate -a tu-casino-app

# Crear superuser
heroku run python manage.py createsuperuser -a tu-casino-app

# Ver logs
heroku logs --tail -a tu-casino-app
```

---

## 🔧 Opción 3: DigitalOcean (Recomendado para Control)

### 1. Crear Droplet

```bash
# Crear en DigitalOcean:
# - Ubuntu 22.04
# - $5-40/mes según recursos
# - SSH key configurada
```

### 2. Configuración Inicial

```bash
# SSH al servidor
ssh root@tu-ip

# Actualizar
apt-get update && apt-get upgrade -y

# Crear usuario no-root
adduser deploy
usermod -aG sudo deploy

# Cambiar a deploy
su deploy

# Clonar repo
cd ~
git clone https://github.com/tu-usuario/casino-online.git
cd casino-online
```

### 3. Instalar Dependencias

```bash
# Python y dev tools
sudo apt-get install python3.11 python3.11-dev python3-pip
sudo apt-get install build-essential libpq-dev

# PostgreSQL
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Redis
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Nginx
sudo apt-get install nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Supervisor (para procesos)
sudo apt-get install supervisor

# Certbot (SSL)
sudo apt-get install certbot python3-certbot-nginx
```

### 4. Configurar Base de Datos

```bash
sudo -u postgres psql

CREATE DATABASE casino_db;
CREATE USER casino_user WITH PASSWORD 'secure_password';
ALTER ROLE casino_user SET client_encoding TO 'utf8';
ALTER ROLE casino_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE casino_user SET default_transaction_deferrable TO on;
GRANT ALL PRIVILEGES ON DATABASE casino_db TO casino_user;
\q
```

### 5. Crear Virtual Environment

```bash
cd ~/casino-online

# Python env
python3.11 -m venv venv
source venv/bin/activate

# Instalar requirements
pip install -r requirements-dev.txt

# Instalar gunicorn
pip install gunicorn
```

### 6. Configurar Django

```bash
# Crear .env
cat > .env << 'EOF'
DEBUG=False
SECRET_KEY=tu-clave-super-secreta-aqui
DATABASE_URL=postgresql://casino_user:secure_password@localhost:5432/casino_db
REDIS_URL=redis://localhost:6379/0
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=app-password
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
EOF

# Migraciones
python manage.py migrate

# Recolectar static
python manage.py collectstatic --noinput

# Crear superuser
python manage.py createsuperuser
```

### 7. Configurar Gunicorn

```bash
# Crear archivo systemd
sudo tee /etc/systemd/system/gunicorn.service > /dev/null << 'EOF'
[Unit]
Description=Gunicorn Casino App
After=network.target

[Service]
User=deploy
Group=www-data
WorkingDirectory=/home/deploy/casino-online
Environment="PATH=/home/deploy/casino-online/venv/bin"
ExecStart=/home/deploy/casino-online/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/home/deploy/casino-online/gunicorn.sock \
    casino_project.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

### 8. Configurar Nginx

```bash
# Crear config
sudo tee /etc/nginx/sites-available/casino > /dev/null << 'EOF'
upstream gunicorn {
    server unix:/home/deploy/casino-online/gunicorn.sock;
}

server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    client_max_body_size 100M;

    location /static/ {
        alias /home/deploy/casino-online/staticfiles/;
    }

    location /media/ {
        alias /home/deploy/casino-online/media/;
    }

    location / {
        proxy_pass http://gunicorn;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket
    location /ws {
        proxy_pass http://gunicorn;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Habilitar
sudo ln -s /etc/nginx/sites-available/casino /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. SSL con Certbot

```bash
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
```

### 10. Configurar Celery

```bash
sudo tee /etc/systemd/system/celery.service > /dev/null << 'EOF'
[Unit]
Description=Celery Service
After=network.target redis.service

[Service]
Type=forking
User=deploy
Group=deploy
WorkingDirectory=/home/deploy/casino-online
Environment="PATH=/home/deploy/casino-online/venv/bin"
ExecStart=/home/deploy/casino-online/venv/bin/celery -A casino_project worker -l info

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl start celery
sudo systemctl enable celery
```

---

## 📊 Configuración settings.py para Producción

```python
import os
from pathlib import Path
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# SEGURIDAD
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

# HTTPS
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# DATABASE (PostgreSQL)
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Redis & Celery
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Static & Media
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@casino.com')

# Stripe
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'error.log'),
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'ERROR',
    },
}
```

---

## 📋 Checklist Pre-Deployment

```
SEGURIDAD
□ DEBUG = False
□ SECRET_KEY = valor nuevo y seguro
□ ALLOWED_HOSTS = dominios correctos
□ SSL/HTTPS configurado
□ CORS configuration correcta

BASE DE DATOS
□ PostgreSQL instalado y corriendo
□ Base de datos creada
□ Usuario con permisos correctos
□ Migraciones ejecutadas
□ Backup configured

PAGOS
□ Stripe keys actualizadas (live, no test)
□ Webhook configurado en Stripe
□ Webhook secret en settings

EMAIL
□ SMTP configurado (Gmail, SendGrid, etc)
□ Credenciales correctas
□ Test email enviado

CACHE & CELERY
□ Redis instalado y corriendo
□ Celery worker configurado
□ Celery beat (scheduler) si es necesario

STATIC FILES
□ collectstatic ejecutado
□ Nginx sirviendo static files

LOGS & MONITORING
□ Logging configurado
□ Directorio de logs creado
□ Supervisor/systemd configurado

DOMINIO
□ DNS apuntando a servidor
□ SSL certificate valido
□ Email MX records configurados
```

---

## 🔍 Monitoreo en Producción

### Logs

```bash
# Ver logs
sudo journalctl -u gunicorn -f
sudo journalctl -u celery -f
sudo tail -f ~/casino-online/logs/error.log
```

### Health Check

```bash
# Endpoint para monitoreo
@app.route('/health/')
def health():
    return {'status': 'ok', 'timestamp': datetime.now()}

# Monitorear con
watch -n 5 'curl -s http://localhost:8000/health/ | jq'
```

### Performance

```bash
# Ver procesos
ps aux | grep python

# Ver conexiones Redis
redis-cli
> INFO

# Ver conexiones PostgreSQL
sudo -u postgres psql
> SELECT * FROM pg_stat_activity;
```

---

## 🔄 Actualizar en Producción

```bash
# SSH al servidor
ssh deploy@tu-ip

cd ~/casino-online

# Pull cambios
git pull origin main

# Activar virtualenv
source venv/bin/activate

# Instalar nuevos requirements
pip install -r requirements-dev.txt

# Migraciones
python manage.py migrate

# Recolectar static
python manage.py collectstatic --noinput

# Reiniciar servicios
sudo systemctl restart gunicorn
sudo systemctl restart celery
sudo systemctl restart nginx
```

---

## 📦 Backup & Recuperación

### Backup Automático

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/home/deploy/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# BD PostgreSQL
pg_dump -U casino_user casino_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Static files
tar -czf $BACKUP_DIR/static_$DATE.tar.gz ~/casino-online/staticfiles

# Media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz ~/casino-online/media

# Guardar últimos 7 días
find $BACKUP_DIR -type f -mtime +7 -delete
```

### Restaurar

```bash
# Restaurar BD
gunzip < db_backup.sql.gz | psql -U casino_user casino_db

# Restaurar archivos
tar -xzf static_backup.tar.gz -C ~/casino-online
tar -xzf media_backup.tar.gz -C ~/casino-online
```

---

## 🎯 Resumen Quick-Start

### Docker (5 minutos)
```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### Heroku (10 minutos)
```bash
heroku create casino-app
heroku addons:create heroku-postgresql
git push heroku main
heroku run python manage.py migrate
```

### DigitalOcean (30 minutos)
```bash
# Seguir pasos 1-10 arriba
# El más manual pero más control
```

---

## 📞 Troubleshooting

### Error: `relation "users_customuser" does not exist`
```bash
python manage.py migrate --run-syncdb
```

### Error: `CORS error`
```python
# Agregar en settings.py
CORS_ALLOWED_ORIGINS = ["https://tu-dominio.com"]
```

### Error: `SSL certificate problem`
```bash
# Renovar con Certbot
sudo certbot renew --dry-run
sudo certbot renew
```

### Error: `Email no se envía`
```python
# Test email
python manage.py shell
from django.core.mail import send_mail
send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

---

## ✅ Deployment Checklist

- [ ] Base de datos PostgreSQL configurada
- [ ] Redis instalado
- [ ] Código actualizado a `main` branch
- [ ] Migraciones ejecutadas
- [ ] Static files recolectados
- [ ] SSL certificate instalado
- [ ] Email configurado y testeado
- [ ] Stripe keys actualizadas (live)
- [ ] Logging configurado
- [ ] Backups programados
- [ ] Monitoreo activado
- [ ] Admin panel accesible
- [ ] Prueba end-to-end completada

---

¡Listo para Producción! 🚀

**Escribe `status` para resumen final del proyecto**

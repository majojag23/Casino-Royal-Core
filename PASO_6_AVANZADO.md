# 🚀 Paso 6: Características Avanzadas

## Descripción General

Se ha agregado un conjunto completo de características avanzadas para mejorar seguridad, experiencia de usuario y capacidades de análisis:

- ✅ Rate Limiting (Control de velocidad API)
- ✅ Notificaciones por Email
- ✅ Sistema de Bonificaciones
- ✅ Análitica y Estadísticas
- ✅ Gestión de Riesgos
- ✅ Auditoría de Jugador

---

## 📦 Archivos Creados

### 1. `apps/core/rate_limiting.py` (250+ líneas)

**Throttles para API:**
```python
UserGameThrottle        # 30 juegos/minuto
UserDepositThrottle     # 10 depósitos/hora
UserLoginThrottle       # 20 logins/hora
UserWithdrawalThrottle  # 5 retiros/día
UserAPIThrottle         # 100 llamadas/minuto
```

**Funcionalidades:**
- Rate limiting decorador personalizado
- Rastreo de intentos de login fallidos
- Bloqueo de cuenta después de 5 intentos fallidos (15 minutos)
- Validación de límites de apuestas
- Estadísticas diarias de apuestas

**Métodos:**
```python
BetLimitValidator.validate_bet()        # Validar apuesta
BetLimitValidator.get_daily_stats()     # Estadísticas del día
LoginAttemptTracker.record_failed_attempt()  # Registrar fallo
LoginAttemptTracker.reset_attempts()    # Resetear intentos
```

---

### 2. `apps/core/email_notifications.py` (300+ líneas)

**Emails Implementados:**
- Bienvenida
- Confirmación de depósito
- Notificación de retiro
- Retiro completado
- Ganancias grandes
- Recuperación de contraseña
- Recordatorio KYC
- Alertas de seguridad
- Extracto mensual

**Métodos:**
```python
EmailNotifier.send_welcome_email()
EmailNotifier.send_deposit_confirmation()
EmailNotifier.send_withdrawal_initiated()
EmailNotifier.send_withdrawal_completed()
EmailNotifier.send_big_win_notification()
EmailNotifier.send_password_reset()
EmailNotifier.send_kyc_verification_reminder()
EmailNotifier.send_account_security_alert()
EmailNotifier.send_monthly_statement()
```

**Tareas Celery (Asincrónicas):**
```python
send_welcome_email_task()
send_deposit_confirmation_task()
send_kyc_reminder_task()
```

---

### 3. `apps/core/bonus_system.py` (350+ líneas)

**Tipos de Bonificación:**

| Tipo | Monto | Descripción |
|------|-------|-------------|
| `welcome` | $50 | Bono al crear cuenta |
| `first_deposit` | 100% (máx $200) | Duplica primer depósito |
| `daily_bonus` | $10 | Bono diario |
| `weekend_bonus` | 50% (máx $100) | Fin de semana |
| `loyalty_bonus` | 10% de lo jugado | Por lealtad |
| `referral` | $25 | Por referir amigo |

**Funcionalidades:**
- Activación automática de bonos
- Historial de bonificaciones
- Sistema de rollover (10x requerido)
- Conversión a cash
- Expiración de bonos

**Métodos:**
```python
BonusManager.add_welcome_bonus()
BonusManager.add_first_deposit_bonus()
BonusManager.add_daily_bonus()
BonusManager.add_loyalty_bonus()
BonusManager.use_bonus()
BonusManager.convert_bonus_to_cash()
BonusManager.get_bonus_info()
```

**Modelo:**
```python
class BonusHistory:
    - user
    - bonus_type
    - amount
    - status: active|used|expired|converted
    - metadata
    - created_at
    - expires_at
```

---

### 4. `apps/core/analytics.py` (400+ líneas)

**Análisis de Usuario:**
```python
UserAnalytics.get_user_stats()      # Estadísticas completas
UserAnalytics.get_daily_stats()     # Por día (últimos 30)
UserAnalytics.get_game_stats()      # Por juego
```

Retorna:
- Total de juegos, apuestas, ganancias/pérdidas
- Tasa de ganancias
- Balance actual
- Edad de cuenta
- Último login

**Análisis de Casino:**
```python
CasinoAnalytics.get_casino_stats()  # Estadísticas globales
CasinoAnalytics.get_game_popularity()  # Juegos más jugados
CasinoAnalytics.get_hourly_activity()  # Actividad por hora
CasinoAnalytics.get_revenue_by_period()  # Ingresos (daily/weekly/monthly)
```

**Gestión de Riesgo:**
```python
RiskManagement.check_betting_anomaly()  # Detectar comportamiento anómalo
RiskManagement.send_anomaly_alert()     # Enviar alerta
```

Detecta:
- Pérdidas > $500 en 24h
- Más de 100 juegos en 24h
- Tasa de pérdida > 80%

---

## 🔧 Integración con API

### Rate Limiting en Endpoints

```python
from apps.core.rate_limiting import UserGameThrottle

class GameViewSet(viewsets.ViewSet):
    throttle_classes = [UserGameThrottle]
    
    @action(detail=False, methods=['post'])
    def play_slots(self, request):
        # Máximo 30 juegos/minuto
        ...
```

### Notificaciones en Pagos

```python
from apps.core.email_notifications import EmailNotifier

# En confirm_deposit():
EmailNotifier.send_deposit_confirmation(user, transaction)
```

### Bonificaciones en Depósitos

```python
from apps.core.bonus_system import BonusManager

# En confirm_deposit():
if first_deposit:
    BonusManager.add_first_deposit_bonus(user, amount)
```

### Análitica en Endpoints

```python
from apps.core.analytics import UserAnalytics

# Nuevo endpoint:
@action(detail=False, methods=['get'])
def statistics(self, request):
    stats = UserAnalytics.get_user_stats(request.user)
    return Response(stats)
```

---

## 📡 Nuevos Endpoints Recomendados

```
GET  /api/users/statistics/          # Estadísticas del usuario
GET  /api/users/daily_stats/         # Estadísticas diarias
GET  /api/users/bonus_info/          # Información de bonificación
POST /api/users/convert_bonus/       # Convertir bonus a cash
GET  /api/casino/analytics/          # Estadísticas del casino
GET  /api/casino/game_popularity/    # Juegos populares
```

---

## 🔐 Seguridad Implementada

✅ **Rate Limiting**
- Protege contra fuerza bruta
- Limita velocidad de API
- Bloquea cuenta tras fallos

✅ **Validación de Apuestas**
- Límites por juego
- Validación de velocidad
- Prevención de bot

✅ **Detección de Anomalías**
- Pérdidas excesivas
- Juego problemático
- Alertas automáticas

---

## 📊 Ejemplos de Uso

### Obtener Estadísticas del Usuario

```python
from apps.core.analytics import UserAnalytics

stats = UserAnalytics.get_user_stats(user)
# {
#     'total_games': 150,
#     'total_bet': 1500.00,
#     'total_profit_loss': -250.00,
#     'win_rate': 45.3,
#     'average_bet': 10.00,
#     ...
# }
```

### Agregar Bonificación de Bienvenida

```python
from apps.core.bonus_system import BonusManager

result = BonusManager.add_welcome_bonus(user)
# {
#     'success': True,
#     'bonus_type': 'welcome',
#     'amount': 50.0,
#     'new_bonus_balance': 50.0
# }
```

### Enviar Email de Confirmación

```python
from apps.core.email_notifications import EmailNotifier

EmailNotifier.send_deposit_confirmation(user, transaction)
```

### Detectar Comportamiento Anómalo

```python
from apps.core.analytics import RiskManagement

anomaly = RiskManagement.check_betting_anomaly(user)
if anomaly['has_anomalies']:
    RiskManagement.send_anomaly_alert(user, anomaly)
```

### Validar Apuesta

```python
from apps.core.rate_limiting import BetLimitValidator

result = BetLimitValidator.validate_bet(user, 50.00, 'slots')
if result['valid']:
    # Proceder con juego
    ...
else:
    # Mostrar error
    print(result['message'])
```

---

## ⚙️ Configuración Requerida

### Email (settings.py)

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu-contraseña-app'
DEFAULT_FROM_EMAIL = 'noreply@casino.com'
```

O variable de entorno:
```
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=app-password
```

### Celery (Opcional pero Recomendado)

```python
# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# En terminal
celery -A casino_project worker -l info
```

---

## 📈 Estadísticas Disponibles

### Por Usuario
- Total de juegos
- Total apostado/pagado
- Ganancia neta
- Tasa de ganancias
- Apuesta promedio
- Balance actual
- Edad de cuenta
- Historial por fecha
- Desempeño por juego

### A Nivel Casino
- Total de usuarios
- Usuarios activos hoy
- Total de juegos jugados
- Ingresos totales
- RTP (Return To Player)
- Juegos más populares
- Actividad por hora
- Ingresos por período

---

## 🛡️ Prevención de Juego Problemático

**Detección Automática:**
- Pérdidas > $500/24h
- Más de 100 juegos/24h
- Tasa de pérdida > 80%

**Acciones:**
- Email de alerta
- Recomendaciones
- Opción de autolimitación

---

## 📝 Migraciones

```bash
# Crear nuevas migraciones para BonusHistory
python manage.py makemigrations

# Aplicar cambios
python manage.py migrate
```

---

## 🧪 Testing

### Test Rate Limiting
```bash
# Hacer 31 solicitudes de juego en 1 minuto
for i in {1..31}; do
    curl -X POST http://localhost:8000/api/games/play_slots/
done
# La 31ª debe devolver 429 Too Many Requests
```

### Test Emails
```python
from apps.core.email_notifications import EmailNotifier

EmailNotifier.send_welcome_email(user)
# Revisar inbox del usuario
```

### Test Bonificaciones
```python
from apps.core.bonus_system import BonusManager

result = BonusManager.add_welcome_bonus(user)
assert result['success'] == True
assert user.bonus_balance == 50.0
```

---

## 📊 Estadísticas Implementadas

| Componente | Cantidad |
|-----------|----------|
| Throttles | 5 |
| Email Templates | 9 |
| Bonus Types | 6 |
| Analytics Methods | 7 |
| Risk Checks | 3 |
| Lines of Code | ~1,000+ |

---

## ✅ Checklist Paso 6

- [x] Rate limiting implementado
- [x] Email notifications creado
- [x] Bonus system completo
- [x] Analytics implementado
- [x] Risk management agregado
- [x] Documentación técnica
- [ ] Configurar email (usuario)
- [ ] Instalar Celery (opcional)
- [ ] Probar características

---

## 📞 Próximos Pasos

1. **Configurar Email:**
   ```
   EMAIL_HOST_USER=tu-email@gmail.com
   EMAIL_HOST_PASSWORD=app-password
   ```

2. **Instalar Celery (Opcional):**
   ```bash
   pip install celery redis
   celery -A casino_project worker -l info
   ```

3. **Ejecutar Migraciones:**
   ```bash
   python manage.py migrate
   ```

4. **Probar Características:**
   - Crear usuario → debe recibir email
   - Depositar → debe recibir confirmación
   - Hacer 31 juegos → debe obtener 429

---

## 🎯 Beneficios

### Seguridad
- Protección contra bots y fuerza bruta
- Detección de anomalías
- Alertas automáticas

### UX
- Confirmaciones por email
- Recordatorios de bonificación
- Extractos mensuales

### Negocio
- Retención con bonos
- Análitica de usuarios
- Gestión de riesgo

---

¡Características avanzadas implementadas! 🚀

Para próximo paso, escribe: `next`

# 🔗 WebSockets - Comunicación en Tiempo Real

## Descripción General

Se ha implementado Django Channels para proporcionar comunicación en tiempo real mediante WebSockets. Esto permite:

- ✅ Actualizaciones de balance en tiempo real
- ✅ Resultados de juegos inmediatos
- ✅ Tablero de líderes en vivo
- ✅ Notificaciones en tiempo real
- ✅ Stream de juegos multijugador

---

## 📦 Archivos Creados

### Backend

**`apps/core/consumers.py`** - WebSocket Consumers
- `BalanceConsumer` - Actualizaciones de balance por usuario
- `LeaderboardConsumer` - Tablero de líderes compartido
- `NotificationConsumer` - Notificaciones personalizadas
- `GameStreamConsumer` - Stream de juegos en vivo

**`apps/core/websocket_utils.py`** - Utilidades para WebSockets
- `WebSocketBroadcaster` - Clase para enviar eventos desde API endpoints

**`casino_project/asgi.py`** - Configuración ASGI
- Routing de WebSocket URLs
- Autenticación middleware

### Dependencias

```
channels==4.0.0
daphne==4.0.0
```

---

## 🔧 Configuración

### 1. Instalación de Dependencias
```bash
pip install -r requirements-dev.txt
```

### 2. settings.py - Cambios

Se agregó a `INSTALLED_APPS`:
```python
'daphne',
'channels',
```

Se cambió `WSGI_APPLICATION` por:
```python
ASGI_APPLICATION = 'casino_project.asgi.application'
```

Se agregó:
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}
```

### 3. Iniciar el Servidor con Daphne

```bash
# En lugar de:
python manage.py runserver

# Usar:
daphne -b 0.0.0.0 -p 8000 casino_project.asgi:application
```

---

## 📡 Conexiones WebSocket

### 1. Balance del Usuario
**URL:** `ws://localhost:8000/ws/balance/<user_id>/`

**Conexión (JavaScript):**
```javascript
const userId = 1;
const ws = new WebSocket(`ws://localhost:8000/ws/balance/${userId}/`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Balance actualizado:', data.balance);
};

ws.onerror = (error) => {
    console.error('Error WebSocket:', error);
};
```

**Eventos Recibidos:**
```json
{
    "type": "balance_update",
    "balance": "1450.00",
    "timestamp": "2026-07-09T10:30:45.123456"
}
```

```json
{
    "type": "game_result",
    "game": "slots",
    "bet": "10.00",
    "payout": "50.00",
    "profit_loss": "40.00",
    "new_balance": "1490.00",
    "timestamp": "2026-07-09T10:30:46.654321"
}
```

### 2. Tablero de Líderes
**URL:** `ws://localhost:8000/ws/leaderboard/`

**Conexión:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/leaderboard/');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Top 10 jugadores:', data.leaderboard);
};
```

**Evento:**
```json
{
    "type": "leaderboard_update",
    "leaderboard": [
        {
            "rank": 1,
            "username": "usuario1",
            "balance": "5000.00",
            "verified": true
        },
        {
            "rank": 2,
            "username": "usuario2",
            "balance": "3500.00",
            "verified": true
        }
    ],
    "timestamp": "2026-07-09T10:30:50.000000"
}
```

### 3. Notificaciones
**URL:** `ws://localhost:8000/ws/notifications/<user_id>/`

**Conexión:**
```javascript
const userId = 1;
const ws = new WebSocket(`ws://localhost:8000/ws/notifications/${userId}/`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    alert(`${data.title}: ${data.message}`);
};
```

**Evento:**
```json
{
    "type": "notification",
    "title": "Ganancia!",
    "message": "Ganaste $100 en Slots!",
    "level": "success",
    "timestamp": "2026-07-09T10:30:55.000000"
}
```

### 4. Stream de Juegos
**URL:** `ws://localhost:8000/ws/game_stream/<game_type>/`

**Conexión:**
```javascript
const gameType = 'slots';
const ws = new WebSocket(`ws://localhost:8000/ws/game_stream/${gameType}/`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'game_event') {
        console.log(`${data.player} apostó $${data.bet}`);
    }
};
```

**Evento:**
```json
{
    "type": "game_event",
    "game": "slots",
    "player": "usuario_1",
    "bet": "10.00",
    "result": "win",
    "payout": "50.00",
    "timestamp": "2026-07-09T10:30:52.000000"
}
```

---

## 🚀 Integración con API

### Endpoints que Emiten WebSocket

Los endpoints de juegos ahora emiten eventos automáticamente:

```python
POST /api/games/play_slots/
POST /api/games/play_panda_mines/
POST /api/games/play_roulette/
POST /api/games/play_golden_jet/
POST /api/games/play_cyber_rolett/
POST /api/games/play_personajes/
```

**Ejemplo de Flujo:**

1. Cliente hace POST a `/api/games/play_slots/` con apuesta
2. Backend procesa el juego
3. Backend llama a `WebSocketBroadcaster.broadcast_game_result()`
4. Todos los clientes conectados al `ws/balance/{user_id}/` reciben actualización
5. Todos los clientes en `ws/game_stream/slots/` ven el resultado

---

## 💻 Ejemplo Frontend Completo

```html
<!DOCTYPE html>
<html>
<head>
    <title>Casino - WebSockets</title>
</head>
<body>
    <h1>Balance en Tiempo Real</h1>
    <p>Saldo: <span id="balance">0.00</span></p>
    <h1>Últimos Resultados</h1>
    <ul id="results"></ul>

    <script>
        const userId = 1; // Obtener del login
        const balanceWs = new WebSocket(`ws://localhost:8000/ws/balance/${userId}/`);
        
        balanceWs.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'balance_update') {
                document.getElementById('balance').textContent = data.balance;
            } 
            else if (data.type === 'game_result') {
                const resultList = document.getElementById('results');
                const item = document.createElement('li');
                item.textContent = `${data.game}: Apuesta $${data.bet}, Ganancia $${data.profit_loss}`;
                resultList.insertBefore(item, resultList.firstChild);
            }
        };
        
        balanceWs.onerror = (error) => {
            console.error('Error en WebSocket:', error);
        };
    </script>
</body>
</html>
```

---

## 🔐 Seguridad

### Autenticación

Los WebSockets están protegidos por `AuthMiddlewareStack`:

```python
websocket: AuthMiddlewareStack(
    URLRouter(websocket_urlpatterns)
)
```

Solo usuarios autenticados pueden conectarse.

### Validación

- **Balance:** Se valida en cada apuesta
- **Usuarios:** Se verifica que el `user_id` en la URL coincida con el usuario autenticado
- **Eventos:** Solo se transmiten datos relevantes al usuario

---

## 📊 Monitoreo

### Logs de Conexión

Daphne mostrará en consola:

```
2026-07-09 10:30:45 - client connected: ws://localhost:8000/ws/balance/1/
2026-07-09 10:30:50 - broadcast to balance_1: balance_update
2026-07-09 10:30:55 - client disconnected: ws://localhost:8000/ws/balance/1/
```

### Estadísticas

Para ver conexiones activas:

```python
# En Django shell
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()

# Usar channel_layer.group_members() para ver miembros de grupos
```

---

## 🛠️ Troubleshooting

### "Connection refused"
**Problema:** El servidor no está corriendo con Daphne
**Solución:**
```bash
daphne -b 0.0.0.0 -p 8000 casino_project.asgi:application
```

### "403 Forbidden"
**Problema:** Usuario no autenticado
**Solución:** Incluir token de autenticación en headers:
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/balance/${userId}/`, 
    ['sec-websocket-protocol', 'token=' + authToken]
);
```

### "No channel layer configured"
**Problema:** Falta CHANNEL_LAYERS en settings.py
**Solución:** Agregar la configuración (ya hecha)

---

## 📈 Escalabilidad

Para producción con múltiples procesos:

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('redis', 6379)],
        },
    },
}
```

Instalación:
```bash
pip install channels-redis
```

---

## ✅ Estado

- [x] Consumers WebSocket creados (4 tipos)
- [x] Configuración ASGI
- [x] Integración en settings.py
- [x] Endpoints de juegos con WebSocket
- [x] Utilidades para broadcast
- [x] Documentación completa
- [ ] Instalar dependencias (siguiente paso)
- [ ] Probar en navegador

---

## 🎮 Próximos Pasos

1. Instalar dependencias: `pip install -r requirements-dev.txt`
2. Iniciar servidor con Daphne
3. Conectar desde frontend con JavaScript WebSocket API
4. Prueba: Abrir balance del usuario y ver actualizaciones en tiempo real

¡Listo para multijugador en tiempo real! 🚀

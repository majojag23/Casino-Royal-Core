# 💳 Integración Stripe - Paso 5

## Descripción General

Se ha implementado **Stripe** para procesamiento de pagos reales en el casino online. Esto permite:

- ✅ Depósitos con tarjeta de crédito/débito
- ✅ Confirmación automática de pagos
- ✅ Webhooks para sincronización
- ✅ Reembolsos automáticos
- ✅ Gestión de múltiples payment methods

---

## 🔑 Claves de Stripe

### Obtener Claves

1. Crear cuenta en [stripe.com](https://stripe.com)
2. Dashboard → Developers → API keys
3. Copiar **Publishable Key** y **Secret Key**

### Configurar en Proyecto

**Opción 1: Variables de entorno (.env)**
```
STRIPE_PUBLISHABLE_KEY=pk_test_XXXXXXX
STRIPE_SECRET_KEY=sk_test_XXXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXXX
```

**Opción 2: Directamente en settings.py (solo desarrollo)**
```python
STRIPE_PUBLISHABLE_KEY = 'pk_test_...'
STRIPE_SECRET_KEY = 'sk_test_...'
```

---

## 📦 Archivos Creados/Modificados

### Nuevos Archivos

**`apps/payments/stripe_config.py`** (280+ líneas)
Clase `StripePaymentProcessor` con métodos:
- `create_payment_intent()` - Crea Payment Intent
- `confirm_payment()` - Confirma estado del pago
- `create_customer()` - Crea cliente en Stripe
- `attach_payment_method()` - Adjunta tarjeta
- `create_charge()` - Cobra a cliente
- `refund_charge()` - Reembolsa cargo
- `list_payment_methods()` - Lista tarjetas guardadas
- `delete_payment_method()` - Elimina tarjeta

**`apps/payments/webhooks.py`** (150+ líneas)
Webhook handler para eventos de Stripe:
- `payment_intent.succeeded` → Actualiza balance
- `payment_intent.payment_failed` → Notifica error
- `charge.refunded` → Revierte transacción

### Archivos Modificados

**`apps/payments/views.py`** (Completamente actualizado)
Nuevos endpoints:
- `POST /api/payments/create_deposit_intent/` - Crear pago
- `POST /api/payments/confirm_deposit/` - Confirmar pago
- `POST /api/payments/withdraw/` - Retirar dinero
- `POST /api/payments/add_payment_method/` - Agregar tarjeta
- `GET /api/payments/payment_methods/` - Listar tarjetas
- `POST /api/payments/remove_payment_method/` - Eliminar tarjeta
- `GET /api/payments/balance/` - Obtener saldo
- `GET /api/payments/transactions/` - Historial

**`apps/payments/models.py`** (Actualizado)
- Agregó campo `stripe_payment_method_id` a PaymentMethod
- Agregó campos de metadata

**`apps/users/models.py`** (Actualizado)
- Agregó `stripe_customer_id` a CustomUser

**`apps/payments/urls.py`** (Actualizado)
- Agregó ruta para webhook de Stripe

**`requirements-dev.txt`** (Actualizado)
- Agregó `stripe==7.4.0`

**`casino_project/settings.py`** (Actualizado)
- Agregó configuración de Stripe

---

## 🔄 Flujos de Pago

### Flujo 1: Depósito con Tarjeta

```
1. Usuario POST /api/payments/create_deposit_intent/
   ├─ Monto: $50
   ├─ Backend: Crea Payment Intent en Stripe
   └─ Retorna: client_secret + publishable_key

2. Frontend: Integra Stripe Elements
   ├─ Muestra formulario de tarjeta
   ├─ Usuario ingresa datos
   └─ Stripe tokeniza

3. Frontend: Confirma con PaymentIntent
   └─ POST /api/payments/confirm_deposit/
      ├─ Payment Intent: confirmado
      ├─ Backend: Actualiza balance
      └─ Emite evento WebSocket

4. Usuario: Ve balance actualizado en tiempo real
```

### Flujo 2: Confirmación de Pago (Webhook)

```
Stripe emite: payment_intent.succeeded
    ↓
POST /api/payments/stripe_webhook/
    ├─ Verifica firma de Stripe
    ├─ Busca transacción
    ├─ Actualiza balance
    └─ Emite WebSocket

Usuario recibe notificación en tiempo real
```

### Flujo 3: Retiro de Dinero

```
Usuario POST /api/payments/withdraw/
    ├─ Verifica KYC
    ├─ Deduce balance
    ├─ Crea transacción pendiente
    └─ Notifica al usuario

Admin revisa y procesa retiro manualmente
    └─ Transfiere a cuenta bancaria
```

---

## 📡 Endpoints API

### Crear Depósito

```
POST /api/payments/create_deposit_intent/
Content-Type: application/json

{
    "amount": 50.00,
    "payment_method_type": "card"
}

Response:
{
    "transaction_id": 123,
    "client_secret": "pi_XXXXX_secret_XXXXX",
    "payment_intent_id": "pi_XXXXX",
    "amount": 50.0,
    "publishable_key": "pk_test_XXXXX"
}
```

### Confirmar Depósito

```
POST /api/payments/confirm_deposit/
Content-Type: application/json

{
    "payment_intent_id": "pi_XXXXX"
}

Response:
{
    "transaction_id": 123,
    "status": "completed",
    "amount": 50.0,
    "new_balance": 1050.00,
    "message": "Depósito completado exitosamente"
}
```

### Agregar Payment Method

```
POST /api/payments/add_payment_method/
Content-Type: application/json

{
    "payment_method_id": "pm_XXXXX",
    "nickname": "Mi Tarjeta Visa"
}

Response:
{
    "success": true,
    "payment_method_id": "pm_XXXXX",
    "type": "card",
    "last_four": "4242"
}
```

### Listar Payment Methods

```
GET /api/payments/payment_methods/

Response:
[
    {
        "id": 1,
        "stripe_id": "pm_XXXXX",
        "type": "card",
        "nickname": "Mi Tarjeta",
        "last_four": "4242"
    }
]
```

### Obtener Balance

```
GET /api/payments/balance/

Response:
{
    "balance": 1050.00,
    "bonus_balance": 50.00,
    "total": 1100.00
}
```

### Crear Retiro

```
POST /api/payments/withdraw/
Content-Type: application/json

{
    "amount": 100.00,
    "withdraw_method": "bank_transfer",
    "bank_details": {
        "account_number": "1234567890",
        "bank_name": "Banco XYZ"
    }
}

Response:
{
    "transaction_id": "txn_123",
    "status": "pending",
    "amount": 100.0,
    "message": "Retiro pendiente. Se procesará en 1-3 días hábiles"
}
```

---

## 💻 Ejemplo Frontend: Stripe Elements

```html
<!DOCTYPE html>
<html>
<head>
    <title>Depósito - Casino</title>
    <script src="https://js.stripe.com/v3/"></script>
</head>
<body>
    <h1>Depositar Dinero</h1>
    <form id="deposit-form">
        <input type="number" id="amount" placeholder="Monto ($)" min="1" max="10000">
        <div id="card-element"></div>
        <button type="submit">Depositar</button>
    </form>

    <script>
        const stripe = Stripe('PK_TEST_KEY'); // Tu publishable key
        const elements = stripe.elements();
        const cardElement = elements.create('card');
        cardElement.mount('#card-element');

        document.getElementById('deposit-form').addEventListener('submit', async (e) => {
            e.preventDefault();

            const amount = document.getElementById('amount').value;

            // 1. Crear Payment Intent
            const intentResponse = await fetch('/api/payments/create_deposit_intent/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({amount: parseFloat(amount)})
            });

            const intentData = await intentResponse.json();
            const clientSecret = intentData.client_secret;

            // 2. Confirmar pago con Stripe
            const {error, paymentIntent} = await stripe.confirmCardPayment(clientSecret, {
                payment_method: {
                    card: cardElement,
                    billing_details: {name: 'Usuario'}
                }
            });

            if (error) {
                alert('Error: ' + error.message);
                return;
            }

            // 3. Confirmar en backend
            const confirmResponse = await fetch('/api/payments/confirm_deposit/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    payment_intent_id: paymentIntent.id
                })
            });

            const confirmData = await confirmResponse.json();
            if (confirmResponse.ok) {
                alert('Depósito exitoso: $' + confirmData.amount);
            } else {
                alert('Error: ' + confirmData.error);
            }
        });
    </script>
</body>
</html>
```

---

## 🔐 Seguridad

✅ **PCI Compliance**
- Stripe maneja datos de tarjeta
- Backend nunca ve datos de tarjeta
- Frontend usa Stripe Elements

✅ **Firma de Webhook**
- Todo webhook verifica firma de Stripe
- Imposible falsificar eventos

✅ **Validación de Transacciones**
- Cada transacción verificada en Stripe
- Balance solo actualiza tras confirmación

✅ **KYC Requerido**
- Solo usuarios verificados pueden retirar
- Límites de retiro configurables

---

## 🧪 Testing

### Tarjetas de Prueba Stripe

```
Exitosa:  4242 4242 4242 4242
Rechazada: 4000 0000 0000 0002
3D Secure: 4000 0025 0000 3155
```

**Otros campos (prueba):**
- Mes: Cualquiera > hoy
- Año: Futuro
- CVC: Cualquier 3 dígitos

### Flujo de Prueba

1. Ir a `/deposit/`
2. Ingresar $50
3. Usar tarjeta 4242 4242 4242 4242
4. Click "Depositar"
5. Confirmar pago
6. Ver balance actualizado
7. Revisar webhooks en Stripe Dashboard

---

## ⚙️ Configuración Webhooks

### Registrar Webhook en Stripe

1. Dashboard → Developers → Webhooks
2. New endpoint
3. URL: `https://tudominio.com/api/payments/stripe_webhook/`
4. Events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `charge.refunded`

### Testing Webhook Localmente

```bash
# Instalar Stripe CLI
# Luego:
stripe listen --forward-to localhost:8000/api/payments/stripe_webhook/

# En otra terminal:
stripe trigger payment_intent.succeeded
```

---

## 📊 Transacciones

Todas las transacciones se guardan en BD:

```python
Transaction.objects.filter(
    transaction_type='deposit',
    status='completed'
).values('user__email', 'amount')
```

**Estados:**
- `pending` - Esperando confirmación
- `completed` - Exitosa
- `failed` - Rechazada
- `cancelled` - Cancelada

---

## 📝 Migraciones

```bash
# Crear nuevas migraciones
python manage.py makemigrations

# Aplicar cambios
python manage.py migrate
```

Los cambios incluyen:
- Nuevo campo `stripe_customer_id` en CustomUser
- Actualización de PaymentMethod con campos Stripe
- Índices para búsquedas rápidas

---

## 🛠️ Troubleshooting

### "Invalid API Key"
**Solución:** Verificar que `STRIPE_SECRET_KEY` está correcto en settings.py

### "Webhook signature verification failed"
**Solución:** Verificar que `STRIPE_WEBHOOK_SECRET` coincide con Stripe Dashboard

### "Payment method not found"
**Solución:** El cliente debe adjuntar tarjeta primero

### "Insufficient balance"
**Solución:** Usuario no tiene fondos para retirar

---

## 📈 Escalabilidad

**Actual:**
- Un servidor
- Payment Intent por transacción
- Webhooks síncronos

**Producción:**
- Múltiples servidores
- Redis para queue de pagos
- Webhooks asíncronos con Celery
- Rate limiting por usuario

---

## ✅ Checklist Paso 5

- [x] Stripe config creado
- [x] Payment Intent integration
- [x] Webhook handlers
- [x] Endpoints de pago
- [x] Models actualizados
- [x] Settings configurados
- [x] Documentación técnica
- [ ] Instalar dependencias (usuario)
- [ ] Obtener claves Stripe (usuario)
- [ ] Configurar webhooks (usuario)

---

## 📞 Próximos Pasos

1. Instalar: `pip install stripe`
2. Crear cuenta Stripe
3. Copiar claves a .env
4. Ejecutar migraciones
5. Registrar webhook
6. Probar con tarjetas de prueba

---

¡Pagos reales implementados! 💳

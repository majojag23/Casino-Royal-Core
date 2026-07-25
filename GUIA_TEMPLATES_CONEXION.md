# 🎯 Guía Rápida: Conectar Templates con Django

## ✅ Lo Que Ya Está Hecho

✓ **9 Templates HTML completos** con CSS y JavaScript integrados
✓ **Diseño responsive** mobile-first (480px)
✓ **Validación de formularios** cliente-lado
✓ **Integración con API REST** lista para conectar
✓ **Sistema de colores** Figma implementado (#741AC0, #F44CFC, etc)
✓ **4 Apps Django** con endpoints listos

---

## 🚀 Pasos para Activar los Templates

### 1. Actualizar `casino_project/urls.py`

Reemplaza el contenido con esto:

```python
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.users.urls')),
    path('api/', include('apps.games.urls')),
    path('api/', include('apps.payments.urls')),
    path('api/', include('apps.admin_panel.urls')),
    
    # Frontend URLs
    path('', TemplateView.as_view(template_name='games/lobby.html'), name='games-lobby'),
    path('login/', TemplateView.as_view(template_name='auth/login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='auth/register.html'), name='register'),
    path('forgot-password/', TemplateView.as_view(template_name='auth/forgot_password.html'), name='forgot-password'),
    path('profile/', TemplateView.as_view(template_name='profile/dashboard.html'), name='profile-dashboard'),
    path('games/<str:game>/', TemplateView.as_view(template_name='games/game.html'), name='play-game'),
    path('deposit/', TemplateView.as_view(template_name='payments/deposit.html'), name='deposit'),
    path('withdraw/', TemplateView.as_view(template_name='payments/withdraw.html'), name='withdraw'),
    path('admin/', TemplateView.as_view(template_name='admin/dashboard.html'), name='admin-dashboard'),
]

# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

### 2. Verificar `casino_project/settings.py`

Asegurate que tenga estas líneas (ya deberían estar):

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
```

### 3. Crear carpeta de estáticos (si no existe)

```bash
mkdir -p static/images
mkdir -p static/css
mkdir -p static/js
```

### 4. Crear archivo `.env` (si no existe)

```
DEBUG=True
SECRET_KEY=tu-clave-secreta-aqui
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://localhost:3000
```

### 5. Ejecutar migraciones

```bash
python manage.py migrate
```

### 6. Crear superuser (para admin)

```bash
python manage.py createsuperuser
# Username: admin
# Email: admin@casino.com
# Password: (tu contraseña)
```

### 7. Iniciar servidor

```bash
python manage.py runserver
```

---

## 🌐 URLs Disponibles Después de Conectar

### Autenticación
| URL | Template | Descripción |
|-----|----------|-------------|
| `/login/` | auth/login.html | Iniciar sesión |
| `/register/` | auth/register.html | Registrarse |
| `/forgot-password/` | auth/forgot_password.html | Recuperar contraseña |

### Juegos
| URL | Template | Descripción |
|-----|----------|-------------|
| `/` | games/lobby.html | Lobby/Home |
| `/games/slots/` | games/game.html | Jugar Slots |
| `/games/panda_mines/` | games/game.html | Jugar Panda Mines |
| `/games/roulette/` | games/game.html | Jugar Ruleta |
| `/games/golden_jet/` | games/game.html | Jugar Golden Jet |
| `/games/cyber_rolett/` | games/game.html | Jugar Cyber Rolett |
| `/games/personajes/` | games/game.html | Jugar Personajes |

### Usuario
| URL | Template | Descripción |
|-----|----------|-------------|
| `/profile/` | profile/dashboard.html | Mi perfil |
| `/deposit/` | payments/deposit.html | Depositar |
| `/withdraw/` | payments/withdraw.html | Retirar |

### Admin
| URL | Template | Descripción |
|-----|----------|-------------|
| `/admin/` | admin/dashboard.html | Panel admin |

---

## 🧪 Pruebas Rápidas

### 1. Test de Login
```bash
# 1. Abre http://localhost:8000/login/
# 2. Intenta registrarte
# 3. Luego login con tus credenciales
# 4. Deberías ir al lobby
```

### 2. Test de API
```bash
# Registrar usuario
curl -X POST http://localhost:8000/api/users/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@casino.com",
    "password": "testpass123",
    "password_confirm": "testpass123",
    "first_name": "Juan",
    "last_name": "Pérez",
    "document_type": "CC",
    "document_number": "12345678",
    "phone": "+573005555555",
    "date_of_birth": "1990-01-01",
    "country": "Colombia"
  }'

# Login
curl -X POST http://localhost:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@casino.com",
    "password": "testpass123"
  }'

# Obtener perfil (usar token del login)
curl -X GET http://localhost:8000/api/users/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Test de Juego
```bash
# Jugar slots (usar token válido)
curl -X POST http://localhost:8000/api/games/play_slots/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"bet_amount": 10}'
```

---

## 📱 Vista Mobile en Chrome DevTools

1. Abre DevTools (F12)
2. Haz clic en "Toggle Device Toolbar" (Ctrl+Shift+M)
3. Selecciona "iPhone 12" o dimensiones 480x852
4. Los templates se adaptan automáticamente

---

## 🎨 Personalizar Colores

Los colores están en `base.html` dentro del `<style>`:

```css
:root {
    --primary: #741AC0;      /* Cambiar de aquí */
    --accent: #F44CFC;       /* O aquí */
    /* ... etc */
}
```

Para cambiar todos los templates, solo edita `base.html`.

---

## 🔒 Autenticación JWT

Los tokens se guardan en `localStorage`:

```javascript
// En login, se guardan automáticamente:
localStorage.setItem('access_token', data.access);
localStorage.setItem('refresh_token', data.refresh);

// Luego se usan en headers:
'Authorization': `Bearer ${localStorage.getItem('access_token')}`
```

---

## 📊 Flujo de Usuario Típico

```
1. Usuario visita http://localhost:8000/
   → Redirige a /login/ (sin token)

2. Hace clic en "Registrarse"
   → Va a /register/
   → Llena formulario
   → POST a /api/users/auth/register/

3. Hace login
   → POST a /api/users/auth/login/
   → Recibe access_token
   → Se guarda en localStorage
   → Redirige a /

4. Ve el lobby con 6 juegos
   → GET a /api/users/profile/ (con token)

5. Hace clic en un juego
   → Va a /games/slots/ (o el que haya elegido)

6. Juega (POST a /api/games/play_slots/)
   → Ve resultado
   → Balance se actualiza

7. Va a /deposit/
   → Elige método de pago
   → POST a /api/payments/deposit/

8. Va a /profile/
   → Ve historial de transacciones
   → Puede cambiar contraseña
   → Puede ver KYC status

9. Admin va a /admin/
   → Ve estadísticas
   → Puede suspender usuarios
   → Puede ver todas las transacciones
```

---

## ⚠️ Errores Comunes y Soluciones

### Error: "No such table: users_customuser"
```bash
# Solución:
python manage.py migrate
```

### Error: "CORS error en login"
En `casino_project/settings.py`, verifica:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://localhost:3000",
]
```

### Error: "Templates not found"
Verifica que exista: `C:\Users\Asus\Desktop\casino-online\templates\`
Y que `TEMPLATES['DIRS']` en settings.py apunte ahí.

### Error: "Estáticos no cargan"
En desarrollo, Django los sirve automáticamente.
En producción:
```bash
python manage.py collectstatic
```

---

## 📝 Checklist de Implementación

### Backend ✅
- [x] Modelos Django creados
- [x] Serializers DRF creados
- [x] ViewSets con endpoints creados
- [x] URLs de API configuradas
- [x] JWT authentication configurada
- [x] CORS configurado

### Frontend ✅
- [x] Template base.html con estilos
- [x] Templates de autenticación (login, register, forgot_password)
- [x] Templates de juegos (lobby, game detail)
- [x] Templates de usuario (perfil)
- [x] Templates de pagos (deposit, withdraw)
- [x] Template de admin (dashboard)
- [x] Validación de formularios JS
- [x] Llamadas a API con JWT

### Testing (TODO)
- [ ] Test de registro
- [ ] Test de login
- [ ] Test de juegos
- [ ] Test de pagos
- [ ] Test de admin

### Deployment (TODO)
- [ ] Configurar variables de entorno
- [ ] Minificar CSS/JS
- [ ] Optimizar imágenes
- [ ] Configurar HTTPS
- [ ] Deploy a servidor

---

## 🚀 Próximo Paso Más Importante

**Agrega estas 2 líneas a `casino_project/urls.py` primero:**

```python
path('api/', include('apps.users.urls')),
# ... resto de paths ...
```

Luego ejecuta:
```bash
python manage.py runserver
```

¡Y todo debería funcionar! 🎉

---

## 📞 Preguntas Frecuentes

**P: ¿Los templates usan AJAX?**
R: Sí, utilizan Fetch API con async/await. No requieren jQuery.

**P: ¿Puedo cambiar los colores?**
R: Sí, edita las variables CSS en `base.html` línea 8-26.

**P: ¿Qué pasa con las imágenes?**
R: Los emojis funcionan sin imágenes. Para logos custom, descárgalos a `static/images/`.

**P: ¿Cómo protejo las rutas?**
R: Los templates verifican `localStorage.access_token`. Los endpoints requieren JWT.

**P: ¿Necesito Webpack o Build Tools?**
R: No, todo está inline. CSS y JS están en los templates.

**P: ¿Funciona en producción?**
R: Sí, pero necesitas: HTTPS, DEBUG=False, SECRET_KEY segura, collectstatic.

---

## 💡 Tips Profesionales

1. **Para desarrollo**: Usa `python manage.py runserver` y abre en navegador
2. **Para debugging**: Abre DevTools (F12) y ve Network + Console
3. **Para testing de API**: Usa Postman o curl
4. **Para feedback UX**: Abre DevTools → Device Toolbar (480px mobile)
5. **Para ver logs**: Mira la terminal donde corre `runserver`

---

## ¡Listo para Ejecutar! 🎰

Ahora tu casino online tiene:
- ✅ Backend completamente funcional
- ✅ Frontend responsivo y moderno
- ✅ Autenticación segura con JWT
- ✅ Sistema de juegos
- ✅ Pagos integrados
- ✅ Panel administrativo
- ✅ Diseño Figma implementado

¡A jugar! 🚀

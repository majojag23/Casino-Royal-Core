# 🎰 Templates HTML e Imágenes Requeridas

## ✅ Templates Creados

Todos los templates han sido creados en la carpeta `templates/`:

### 📁 Estructura de Directorios
```
templates/
├── base.html                 ✅ Template base con estilos globales
├── auth/
│   ├── login.html           ✅ Página de login
│   └── register.html        ✅ Página de registro
├── games/
│   ├── lobby.html           ✅ Lobby/Home de juegos
│   └── game.html            ✅ Pantalla individual de juego
├── profile/
│   └── dashboard.html       ✅ Perfil de usuario
├── payments/
│   ├── deposit.html         ✅ Depositar fondos
│   └── withdraw.html        ✅ Retirar fondos
└── admin/
    └── dashboard.html       ✅ Panel administrativo
```

### 📋 Características de los Templates

**base.html**
- Sistema de colores: Púrpura (#741AC0) + Magenta (#F44CFC)
- Diseño mobile-first (480px)
- Navegación responsive
- Sistema de alertas
- Variables CSS reutilizables

**auth/login.html**
- Formulario de login con validación
- Integración con API `/api/users/auth/login/`
- Almacenamiento de tokens JWT
- Opciones de login social (placeholders)

**auth/register.html**
- Registro completo con campos KYC
- Validación de contraseñas
- Integración con API `/api/users/auth/register/`
- Aceptación de términos y privacidad

**games/lobby.html**
- Grid de 6 juegos disponibles
- Estadísticas rápidas (balance, ganancias, rachas)
- Botones de depositar/retirar
- Sistema de filtros (todos, trending, nuevos, favoritos)
- Conexión con `/api/users/profile/`

**games/game.html**
- Área de juego interactiva
- Controles de apuesta con botones rápidos
- Historial de últimos resultados
- Integración con `/api/games/play_slots/` y `/api/games/play_panda_mines/`
- Mostrador de balance en tiempo real

**profile/dashboard.html**
- 4 Tabs: Resumen, Transacciones, Configuración, Seguridad
- Información de verificación KYC
- Estadísticas: balance, bonus, juegos jugados, ganancia total
- Formulario de edición de perfil
- Cambio de contraseña
- Integración con `/api/users/profile/` y `/api/payments/transactions/`

**payments/deposit.html**
- 3 métodos de pago: Tarjeta, PSE, Billetera
- Montos rápidos ($50-$5,000)
- Cálculo automático de comisiones (3%)
- Formularios específicos por método
- Integración con `/api/payments/deposit/`

**payments/withdraw.html**
- 2 métodos: Transferencia Bancaria, PSE
- Montos mínimos ($50)
- Cálculo de comisiones (2%)
- Datos bancarios completos
- Integración con `/api/payments/withdraw/`

**admin/dashboard.html**
- Estadísticas: usuarios totales, activos, balance, ingresos
- Gráficos visuales (últimos 7 días)
- Tabla de usuarios con filtros
- Tabla de transacciones
- Configuración de juegos (min/max bet)
- Panel de bonificaciones
- Integración con `/api/admin/dashboard/`, `/api/admin/users/`, `/api/admin/transactions/`

---

## 🖼️ Imágenes Requeridas

### 📥 Para Descargar/Crear

#### Logo y Branding
- **logo_casino.png** - Logo principal (200x200px recomendado)
  - Ubicación: `static/images/logo.png`
  - Propuesta: Usar emoji 🎰 o crear logo custom

- **favicon.ico** - Ícono de pestaña (32x32px)
  - Ubicación: `static/favicon.ico`
  - Propuesta: 🎰

#### Iconos de Juegos (puedes usar emojis o crear custom)
- **slot-icon.png** - Para Neon Slots (128x128px)
  - Emoji actual: 🎰
  
- **panda-mines-icon.png** - Para Panda Mines (128x128px)
  - Emoji actual: 🐼

- **roulette-icon.png** - Para Ruleta (128x128px)
  - Emoji actual: 🎡

- **golden-jet-icon.png** - Para Golden Jet (128x128px)
  - Emoji actual: ✈️

- **cyber-rolett-icon.png** - Para Cyber Rolett (128x128px)
  - Emoji actual: 🤖

- **personajes-icon.png** - Para Personajes (128x128px)
  - Emoji actual: 🧙

#### Logos de Métodos de Pago
- **stripe-logo.png** - Logo Stripe (200x100px)
  - Para depósitos con tarjeta

- **pse-logo.png** - Logo PSE (200x100px)
  - Para transferencias PSE

- **visa-logo.png** - Logo Visa (150x50px)
  - Para depósitos/retiros

- **mastercard-logo.png** - Logo Mastercard (150x50px)
  - Para depósitos/retiros

#### Fondos y Elementos
- **background-gradient.png** - Fondo personalizado (1920x1080px)
  - Gradiente púrpura/azul/magenta

- **card-bg-pattern.png** - Patrón para tarjetas (800x600px)
  - Patrón sutil para fondos de tarjetas

#### Avatares de Usuario
- **default-avatar.png** - Avatar por defecto (100x100px)
  - Propuesta: Iniciales del usuario o avatar genérico

---

## 🔗 URLs de Rutas Django Requeridas

Para que los templates funcionen, necesitas agregar estas rutas en `casino_project/urls.py`:

```python
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    # ... tus URLs de API existentes ...
    
    # Frontend URLs
    path('', TemplateView.as_view(template_name='games/lobby.html'), name='games-lobby'),
    path('login/', TemplateView.as_view(template_name='auth/login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='auth/register.html'), name='register'),
    path('profile/', TemplateView.as_view(template_name='profile/dashboard.html'), name='profile-dashboard'),
    path('games/<str:game>/', TemplateView.as_view(template_name='games/game.html'), name='play-game'),
    path('deposit/', TemplateView.as_view(template_name='payments/deposit.html'), name='deposit'),
    path('withdraw/', TemplateView.as_view(template_name='payments/withdraw.html'), name='withdraw'),
    path('admin/', TemplateView.as_view(template_name='admin/dashboard.html'), name='admin-dashboard'),
    path('forgot-password/', TemplateView.as_view(template_name='auth/forgot_password.html'), name='forgot-password'),
]
```

---

## 📦 Configuración Estática

### 1. Crear carpeta de imágenes
```bash
mkdir -p static/images
mkdir -p static/css
mkdir -p static/js
```

### 2. Copiar logos de pago (ejemplo)
Descarga desde:
- **Stripe**: https://stripe.com/media/branding/stripe-mark.png
- **PSE**: Solicitar a PSE directamente
- **Visa**: https://usa.visa.com/content/dam/VCOM/regional/na/us/Global/ApplyNow/visa-logo.png
- **Mastercard**: https://www.mastercard.us/content/dam/public/mastercardcom/en-us/images/page-assets/homepage/Mastercard_logo.svg

### 3. Configurar Django para servir estáticos
En `casino_project/settings.py`:

```python
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# En desarrollo, Django sirve los estáticos automáticamente
# En producción, ejecuta: python manage.py collectstatic
```

---

## 🎨 Personalización de Estilos

### Colores Disponibles
```css
--primary: #741AC0;          /* Púrpura */
--primary-light: #A77BC3;    /* Púrpura claro */
--accent: #F44CFC;           /* Magenta */
--accent-dark: #2B028C;      /* Azul oscuro */
--bg-base: #080254;          /* Fondo base */
--text-primary: #FFFFFF;     /* Texto principal */
--text-secondary: #46407C;   /* Texto secundario */
--success: #4CAF50;          /* Verde */
--danger: #f44336;           /* Rojo */
```

### Espaciado
```css
--spacing-xs: 8px;
--spacing-sm: 12px;
--spacing-md: 16px;
--spacing-lg: 24px;
--spacing-xl: 42px;
--spacing-xxl: 63px;
```

---

## ✨ Próximos Pasos Recomendados

1. **Descargar/Crear Imágenes**
   - [ ] Logo casino
   - [ ] Iconos de juegos
   - [ ] Logos de pago

2. **Configurar Rutas Django**
   - [ ] Agregar URLs frontend
   - [ ] Configurar STATIC_URL
   - [ ] Crear carpetas de estáticos

3. **Integración con API**
   - [ ] Verificar endpoints de autenticación
   - [ ] Probar endpoints de juegos
   - [ ] Probar endpoints de pagos

4. **Testing**
   - [ ] Test login/registro
   - [ ] Test juegos
   - [ ] Test depositar/retirar
   - [ ] Test panel admin

5. **Deployment**
   - [ ] Configurar CORS correctamente
   - [ ] Activar HTTPS
   - [ ] Optimizar imágenes
   - [ ] Minificar CSS/JS

---

## 📱 Responsive Behavior

Todos los templates son responsive y se adaptan automáticamente a:
- 📱 Mobile: 375px - 480px
- 📱 Tablet: 768px - 1024px
- 🖥️ Desktop: 1280px+

Los breakpoints principales usan `@media (max-width: 480px)`

---

## 🔐 Seguridad Implementada

✅ Validación de formularios cliente-lado
✅ Uso de JWT para autenticación
✅ Headers CSRF en formularios
✅ Encriptación SSL (requerida en producción)
✅ Validación de montos mínimos
✅ Verificación de balance
✅ Manejo de errores seguro

---

## 📞 Soporte

¿Necesitas ayuda con:
- **Descarga de imágenes**: Verifica los links en "Descargar/Crear"
- **Rutas Django**: Copia el código de "URLs de Rutas Django Requeridas"
- **Estilos**: Modifica las variables CSS en `base.html`
- **Funcionalidad**: Los endpoints API ya están listos en el backend

¡Todos los templates están listos para usar! 🚀

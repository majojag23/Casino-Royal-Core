# 👥 Usuarios de Prueba - Casino Online

## ⚠️ Nota Importante

Para crear usuarios de prueba, primero necesitas:

1. **Detener el servidor Django**
   ```bash
   # Presiona Ctrl+C en la terminal donde corre el servidor
   ```

2. **Eliminar la BD vieja y ejecutar migraciones**
   ```bash
   # En Windows
   del db.sqlite3
   
   # En Mac/Linux
   rm db.sqlite3
   
   # Luego migrar
   python manage.py migrate --no-input
   ```

3. **Crear los usuarios**
   ```bash
   python setup_users.py
   ```

4. **Iniciar el servidor de nuevo**
   ```bash
   python manage.py runserver
   ```

---

## 📧 Credenciales de Prueba

Una vez que ejecutes `python setup_users.py`, tendrás estos usuarios:

### Usuarios Regulares

| Email | Contraseña | Balance | Verificado | Uso |
|-------|-----------|---------|-----------|-----|
| usuario1@casino.com | TestPass123! | $1,500.00 | ✅ Sí | Pruebas generales |
| usuario2@casino.com | TestPass123! | $2,500.50 | ✅ Sí | Pruebas de juegos |
| usuario3@casino.com | TestPass123! | $750.25 | ❌ No | Pruebas sin KYC |
| demo@casino.com | DemoPass123! | $500.00 | ✅ Sí | Demo pública |

### Admin

| Email | Contraseña | Balance | Tipo |
|-------|-----------|---------|------|
| admin@casino.com | AdminPass123! | $10,000.00 | Superuser |

---

## 🔐 Acceso

### Para Jugadores
```
URL: http://localhost:8000/login/
```

### Para Administradores
```
URL: http://localhost:8000/admin/
Email: admin@casino.com
Password: AdminPass123!
```

---

## 📋 Script de Setup

El archivo `setup_users.py` crea todos los usuarios automáticamente.

**Ubicación:** `/C:\Users\Asus\Desktop\casino-online\setup_users.py`

**Qué hace:**
- ✅ Crea 4 usuarios regulares con balances
- ✅ Crea 1 usuario admin/superuser
- ✅ Evita duplicados (solo crea si no existe)
- ✅ Imprime confirmación de cada usuario

---

## 🧪 Pruebas Recomendadas

### 1. Login básico
```
Email: usuario1@casino.com
Pass: TestPass123!
→ Debería ir al lobby de juegos
```

### 2. Jugar
```
Dentro del lobby, haz click en cualquier juego
→ Debería abrir la pantalla del juego
→ Apuesta dinero y juega
→ Balance debería actualizar
```

### 3. Perfil
```
URL: http://localhost:8000/profile/
→ Ver balance, historial de transacciones
→ Cambiar contraseña
```

### 4. Pagos
```
Depositar: http://localhost:8000/deposit/
Retirar: http://localhost:8000/withdraw/
→ Probar flujos de pago
```

### 5. Admin
```
URL: http://localhost:8000/admin/
Email: admin@casino.com
Pass: AdminPass123!
→ Ver estadísticas
→ Gestionar usuarios
→ Ver transacciones
```

---

## 🛠️ Troubleshooting

### "No such table: users"
**Problema:** Las migraciones no se aplicaron
**Solución:**
```bash
python manage.py migrate --no-input
```

### "Database is locked"
**Problema:** Otro proceso usa la BD
**Solución:**
```bash
# Detén el servidor Django primero
# Presiona Ctrl+C en la terminal
```

### "User already exists"
**Problema:** Intentaste crear usuarios que ya existen
**Solución:** Solo ejecuta una vez, o edita el archivo para cambiar emails

---

## 📊 Datos Generados

El archivo `setup_users.py` genera:

1. **CustomUser** objects con:
   - Email y contraseña hasheada
   - Nombre y apellido
   - Balance inicial
   - Estado de verificación (KYC)

2. **Superuser** (admin) con:
   - Acceso al panel /admin/
   - Balance $10,000
   - Permisos totales

---

## ✅ Estado Actual

- [x] Script creado: `setup_users.py`
- [x] Credenciales documentadas
- [x] Instrucciones de setup
- [x] Guía de troubleshooting
- [ ] Usuarios creados (espera a ejecutar script)

---

## 📝 Próximo Paso

**Para crear los usuarios de prueba:**

1. Abre terminal
2. Navega a: `C:\Users\Asus\Desktop\casino-online`
3. Ejecuta: `python setup_users.py`
4. Inicia servidor: `python manage.py runserver`
5. Accede a: `http://localhost:8000/login/`

¡Listo para probar! 🎮

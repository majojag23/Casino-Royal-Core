# Script de instalación de WebSockets para Windows
# Uso: .\install_websockets.ps1

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Instalando WebSockets (Paso 4)" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Python
Write-Host "1. Verificando Python..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python no está instalado" -ForegroundColor Red
    exit 1
}

# 2. Actualizar pip
Write-Host "2. Actualizando pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# 3. Instalar requirements
Write-Host "3. Instalando paquetes desde requirements-dev.txt..." -ForegroundColor Yellow
pip install -r requirements-dev.txt

# 4. Instalar WebSockets
Write-Host "4. Instalando Channels y Daphne..." -ForegroundColor Yellow
pip install channels==4.0.0 daphne==4.0.0 asgiref==3.7.1

# 5. Verificar instalación
Write-Host "5. Verificando instalación..." -ForegroundColor Yellow
python -c "import channels; import daphne; print('OK: Channels y Daphne instalados')"
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: Instalación exitosa" -ForegroundColor Green
}

# 6. Aplicar migraciones
Write-Host "6. Aplicando migraciones..." -ForegroundColor Yellow
python manage.py migrate

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Instalación completada!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Cyan
Write-Host "1. Inicia el servidor con Daphne:" -ForegroundColor White
Write-Host "   daphne -b 0.0.0.0 -p 8000 casino_project.asgi:application" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Abre en navegador:" -ForegroundColor White
Write-Host "   http://localhost:8000/test/websockets.html" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Prueba WebSockets desde consola:" -ForegroundColor White
Write-Host "   const ws = new WebSocket('ws://localhost:8000/ws/balance/1/');" -ForegroundColor Yellow

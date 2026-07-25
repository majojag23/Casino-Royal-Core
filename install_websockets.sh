#!/bin/bash

echo "Instalando dependencias para WebSockets..."
echo ""

# Actualizar pip
echo "1. Actualizando pip..."
pip install --upgrade pip

# Instalar requirements
echo "2. Instalando paquetes desde requirements-dev.txt..."
pip install -r requirements-dev.txt

# Instalar dependencias adicionales de WebSockets
echo "3. Instalando dependencias de WebSockets..."
pip install channels==4.0.0 daphne==4.0.0 asgiref==3.7.1

# Verificar instalación
echo ""
echo "Verificando instalación..."
python -c "import channels; import daphne; print('OK: Channels y Daphne instalados')"

echo ""
echo "Instalación completada!"
echo ""
echo "Próximos pasos:"
echo "1. Asegúrate de que las migraciones están aplicadas:"
echo "   python manage.py migrate"
echo ""
echo "2. Inicia el servidor con Daphne:"
echo "   daphne -b 0.0.0.0 -p 8000 casino_project.asgi:application"
echo ""
echo "3. Prueba WebSockets desde el navegador (F12 > Console):"
echo "   const ws = new WebSocket('ws://localhost:8000/ws/balance/1/');"
echo "   ws.onmessage = (e) => console.log(JSON.parse(e.data));"

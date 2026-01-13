#!/bin/bash
# Script de inicio con logs DEBUG para diagnosticar problemas
# Muestra todos los mensajes de auto-responder y detalles de paquetes

cd "$(dirname "$0")"

echo "🔍 Iniciando proxy en modo DEBUG..."
echo "   Verás TODOS los mensajes incluyendo auto-responder"
echo ""
echo "Presiona Ctrl+C para detener"
echo ""

DEBUG=1 python3 main.py

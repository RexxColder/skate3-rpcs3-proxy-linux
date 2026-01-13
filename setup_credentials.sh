#!/bin/bash
# Script para configurar credenciales de EA
# Ejecuta este script para crear el archivo de configuración de login

set -e

echo "============================================================"
echo "Configuración de Credenciales de EA"
echo "============================================================"
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Directorio de configuración
CONFIG_DIR="$HOME/.config/skate3-proxy"
CONFIG_FILE="$CONFIG_DIR/login.json"

echo "Este script creará el archivo de credenciales en:"
echo "  $CONFIG_FILE"
echo ""
echo -e "${YELLOW}IMPORTANTE:${NC} Necesitas una cuenta de EA válida."
echo "Si no tienes una, créala en: https://www.ea.com/"
echo ""

read -p "¿Continuar? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelado."
    exit 0
fi

echo ""
echo "Ingresa tus credenciales de EA:"
echo ""

# Leer email
read -p "Email de EA: " EA_EMAIL
if [ -z "$EA_EMAIL" ]; then
    echo -e "${RED}Error: Email no puede estar vacío${NC}"
    exit 1
fi

# Leer password (oculto)
read -s -p "Password de EA: " EA_PASSWORD
echo ""
if [ -z "$EA_PASSWORD" ]; then
    echo -e "${RED}Error: Password no puede estar vacío${NC}"
    exit 1
fi

# Leer nombre PSN
read -p "Nombre PSN (para Skate 3): " PSN_NAME
if [ -z "$PSN_NAME" ]; then
    echo -e "${RED}Error: Nombre PSN no puede estar vacío${NC}"
    exit 1
fi

# Crear directorio si no existe
mkdir -p "$CONFIG_DIR"

# Crear archivo JSON
cat > "$CONFIG_FILE" <<EOF
{
  "email": "$EA_EMAIL",
  "password": "$EA_PASSWORD",
  "psnName": "$PSN_NAME"
}
EOF

# Asegurar permisos restrictivos (solo lectura para el usuario)
chmod 600 "$CONFIG_FILE"

echo ""
echo -e "${GREEN}✓ Credenciales guardadas exitosamente!${NC}"
echo ""
echo "Ubicación: $CONFIG_FILE"
echo "Permisos: 600 (solo lectura para tu usuario)"
echo ""
echo "Para editar las credenciales más tarde:"
echo "  nano $CONFIG_FILE"
echo ""
echo -e "${GREEN}¡Listo para usar el proxy!${NC}"
echo ""

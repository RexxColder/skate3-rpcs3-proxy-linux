#!/bin/bash
# Script para configurar redirección de red
# Redirige gosredirector.ea.com a localhost

set -e

echo "============================================================"
echo "Configuración de Redirección de Red"
echo "============================================================"
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: Este script debe ejecutarse como root${NC}"
    echo "Usa: sudo ./setup_network.sh"
    exit 1
fi

HOSTS_FILE="/etc/hosts"
EA_DOMAIN="gosredirector.ea.com"
BACKUP_FILE="/etc/hosts.backup.skate3proxy.$(date +%s)"

echo "Este script modificará $HOSTS_FILE para redirigir:"
echo "  $EA_DOMAIN → 127.0.0.1"
echo ""
echo -e "${YELLOW}Se creará un backup en:${NC}"
echo "  $BACKUP_FILE"
echo ""

# Verificar si ya existe la entrada
if grep -q "$EA_DOMAIN" "$HOSTS_FILE"; then
    echo -e "${YELLOW}⚠ La entrada ya existe en $HOSTS_FILE${NC}"
    echo ""
    echo "Líneas actuales:"
    grep "$EA_DOMAIN" "$HOSTS_FILE"
    echo ""
    read -p "¿Quieres reemplazarla? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelado."
        exit 0
    fi
    
    # Hacer backup
    cp "$HOSTS_FILE" "$BACKUP_FILE"
    echo -e "${GREEN}✓ Backup creado${NC}"
    
    # Remover líneas existentes
    sed -i "/$EA_DOMAIN/d" "$HOSTS_FILE"
    echo -e "${GREEN}✓ Líneas antiguas removidas${NC}"
else
    # Hacer backup
    cp "$HOSTS_FILE" "$BACKUP_FILE"
    echo -e "${GREEN}✓ Backup creado${NC}"
fi

# Agregar nueva entrada
echo "" >> "$HOSTS_FILE"
echo "# Skate 3 Proxy - Redirige EA servers a localhost" >> "$HOSTS_FILE"
echo "127.0.0.1  $EA_DOMAIN" >> "$HOSTS_FILE"

echo -e "${GREEN}✓ Entrada agregada a $HOSTS_FILE${NC}"
echo ""
echo "Configuración actual:"
echo "─────────────────────────────────────────────"
grep "$EA_DOMAIN" "$HOSTS_FILE"
echo "─────────────────────────────────────────────"
echo ""

# Verificar con ping (timeout rápido)
echo "Verificando redirección..."
if ping -c 1 -W 1 "$EA_DOMAIN" > /dev/null 2>&1; then
    IP=$(ping -c 1 "$EA_DOMAIN" | grep -oP '(?<=\().*?(?=\))' | head -1)
    if [ "$IP" = "127.0.0.1" ]; then
        echo -e "${GREEN}✓ Redirección funcionando correctamente!${NC}"
        echo "  $EA_DOMAIN → $IP"
    else
        echo -e "${YELLOW}⚠ La IP no es localhost: $IP${NC}"
        echo "  Puede ser que el DNS cache necesite limpiarse."
    fi
else
    echo -e "${YELLOW}⚠ No se pudo verificar (ping falló)${NC}"
    echo "  Esto es normal si no hay conectividad."
fi

echo ""
echo -e "${GREEN}Configuración completada!${NC}"
echo ""
echo "Para revertir los cambios:"
echo "  sudo cp $BACKUP_FILE $HOSTS_FILE"
echo ""
echo "Para limpiar DNS cache (opcional):"
echo "  sudo systemd-resolve --flush-caches  # SystemD"
echo "  sudo /etc/init.d/dns-clean restart    # SysV"
echo ""

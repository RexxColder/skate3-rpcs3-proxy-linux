#!/bin/bash
# Script de inicio rápido para el proxy
# Verifica configuración y ejecuta el proxy

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo ""
echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}    Skate 3 RPCS3 Proxy - Verificación y Ejecución${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}"
echo ""

# Variables
CONFIG_FILE="$HOME/.config/skate3-proxy/login.json"
HOSTS_FILE="/etc/hosts"
EA_DOMAIN="gosredirector.ea.com"

errors=0
warnings=0

# Función para imprimir checks
check_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    warnings=$((warnings + 1))
}

check_error() {
    echo -e "${RED}✗${NC} $1"
    errors=$((errors + 1))
}

# ============================================================
# Check 1: Credenciales
# ============================================================
echo -e "${BOLD}[1/5] Verificando credenciales...${NC}"

if [ -f "$CONFIG_FILE" ]; then
    # Verificar que sea JSON válido
    if python3 -c "import json; json.load(open('$CONFIG_FILE'))" 2>/dev/null; then
        EMAIL=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['email'])" 2>/dev/null)
        if [ ! -z "$EMAIL" ]; then
            check_ok "Credenciales encontradas para: $EMAIL"
        else
            check_error "Archivo de credenciales existe pero está vacío"
        fi
    else
        check_error "Archivo de credenciales no es JSON válido"
        echo "      Ejecuta: ./setup_credentials.sh"
    fi
else
    check_error "No se encontraron credenciales"
    echo "      Ejecuta: ./setup_credentials.sh"
fi

# ============================================================
# Check 2: Redirección de red
# ============================================================
echo -e "${BOLD}[2/5] Verificando redirección de red...${NC}"

if grep -q "$EA_DOMAIN" "$HOSTS_FILE" 2>/dev/null; then
    HOSTS_LINE=$(grep "$EA_DOMAIN" "$HOSTS_FILE" | head -1)
    if echo "$HOSTS_LINE" | grep -q "127.0.0.1"; then
        check_ok "Redirección configurada: $EA_DOMAIN → 127.0.0.1"
    else
        check_warn "Redirección existe pero no apunta a 127.0.0.1"
        echo "      Línea actual: $HOSTS_LINE"
    fi
else
    check_error "Redirección NO configurada en $HOSTS_FILE"
    echo "      Ejecuta: sudo ./setup_network.sh"
fi

# ============================================================
# Check 3: Puertos disponibles
# ============================================================
echo -e "${BOLD}[3/5] Verificando puertos...${NC}"

if command -v netstat &> /dev/null; then
    if netstat -tuln 2>/dev/null | grep -q ":42100 "; then
        check_warn "Puerto 42100 ya está en uso"
    else
        check_ok "Puerto 42100 disponible"
    fi
    
    if netstat -tuln 2>/dev/null | grep -q ":9999 "; then
        check_warn "Puerto 9999 ya está en uso"
    else
        check_ok "Puerto 9999 disponible"
    fi
else
    check_warn "netstat no disponible, no se pueden verificar puertos"
fi

# ============================================================
# Check 4: RPCS3
# ============================================================
echo -e "${BOLD}[4/5] Verificando RPCS3...${NC}"

if pgrep -i -f rpcs > /dev/null 2>&1; then
    PID=$(pgrep -i -f rpcs | head -1)
    check_ok "RPCS3 está corriendo (PID: $PID)"
else
    check_warn "RPCS3 NO está corriendo"
    echo "      El proxy funcionará, pero necesitarás iniciar RPCS3 después"
fi

# ============================================================
# Check 5: Dependencias Python
# ============================================================
echo -e "${BOLD}[5/5] Verificando dependencias...${NC}"

if python3 -c "import asyncio" 2>/dev/null; then
    check_ok "Python asyncio disponible"
else
    check_error "Python asyncio no disponible"
fi

if [ -f "requirements.txt" ]; then
    if python3 -c "import pkg_resources; pkg_resources.require(open('requirements.txt').read().splitlines())" 2>/dev/null; then
        check_ok "Todas las dependencias instaladas"
    else
        check_warn "Algunas dependencias pueden faltar"
        echo "      Ejecuta: pip3 install -r requirements.txt"
    fi
fi

# ============================================================
# Resumen
# ============================================================
echo ""
echo -e "${BOLD}Resumen de verificación:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $errors -eq 0 ] && [ $warnings -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✓ Todo está listo!${NC}"
elif [ $errors -eq 0 ]; then
    echo -e "${YELLOW}${BOLD}⚠ $warnings advertencia(s) - Puede funcionar${NC}"
else
    echo -e "${RED}${BOLD}✗ $errors error(es) encontrado(s)${NC}"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================
# Decisión de ejecución
# ============================================================

if [ $errors -gt 0 ]; then
    echo -e "${RED}No se puede ejecutar el proxy debido a errores.${NC}"
    echo ""
    echo "Resuelve los errores arriba y vuelve a ejecutar:"
    echo "  ./start_proxy.sh"
    echo ""
    exit 1
fi

if [ $warnings -gt 0 ]; then
    echo -e "${YELLOW}Hay advertencias. ¿Continuar de todos modos?${NC}"
    read -p "Presiona Enter para continuar, Ctrl+C para cancelar..."
    echo ""
fi

# ============================================================
# Ejecutar proxy
# ============================================================

echo -e "${BOLD}${GREEN}Iniciando proxy...${NC}"
echo ""
echo "Presiona Ctrl+C para detener"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ejecutar con manejo de señales
trap 'echo ""; echo "Deteniendo proxy..."; exit 0' INT TERM

python3 main.py

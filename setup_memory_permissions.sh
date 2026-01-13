#!/bin/bash
# Script de configuración de permisos para manipulación de memoria RPCS3
# Este script configura los permisos necesarios para que el proxy pueda
# leer y escribir la memoria del proceso RPCS3

set -e

echo "============================================================"
echo "Configuración de Permisos - Skate 3 RPCS3 Proxy"
echo "============================================================"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: Este script debe ejecutarse como root${NC}"
    echo "Usa: sudo ./setup_memory_permissions.sh"
    exit 1
fi

echo "Selecciona el método de configuración:"
echo ""
echo "1) ${GREEN}Temporary${NC} - Funciona hasta reiniciar (Recomendado para pruebas)"
echo "   Ejecuta: echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope"
echo ""
echo "2) ${YELLOW}Permanent${NC} - Persiste después de reinicio (Menos seguro)"
echo "   Modifica /etc/sysctl.d/10-ptrace.conf"
echo ""
echo "3) ${GREEN}Capabilities${NC} - Dar permisos solo a Python (Más seguro)"
echo "   Usa: setcap cap_sys_ptrace=eip /usr/bin/python3"
echo ""
echo "4) Cancelar"
echo ""

read -p "Selecciona opción [1-4]: " choice

case $choice in
    1)
        echo ""
        echo -e "${YELLOW}Configurando ptrace_scope temporalmente...${NC}"
        
        # Guardar valor actual
        CURRENT=$(cat /proc/sys/kernel/yama/ptrace_scope)
        echo "Valor actual: $CURRENT"
        
        # Configurar a 0 (permite ptrace a cualquier proceso del mismo usuario)
        echo 0 > /proc/sys/kernel/yama/ptrace_scope
        
        NEW=$(cat /proc/sys/kernel/yama/ptrace_scope)
        echo -e "${GREEN}✓ Configurado a: $NEW${NC}"
        echo ""
        echo -e "${YELLOW}IMPORTANTE:${NC} Este cambio se perderá al reiniciar."
        echo "Para hacerlo permanente, ejecuta este script nuevamente con opción 2."
        ;;
        
    2)
        echo ""
        echo -e "${YELLOW}Configurando ptrace_scope permanentemente...${NC}"
        
        # Crear archivo de configuración
        CONFIG_FILE="/etc/sysctl.d/10-ptrace.conf"
        
        # Backup si existe
        if [ -f "$CONFIG_FILE" ]; then
            cp "$CONFIG_FILE" "${CONFIG_FILE}.backup.$(date +%s)"
            echo "Backup creado: ${CONFIG_FILE}.backup.*"
        fi
        
        # Escribir configuración
        echo "kernel.yama.ptrace_scope = 0" > "$CONFIG_FILE"
        
        # Aplicar inmediatamente
        sysctl -p "$CONFIG_FILE"
        
        echo -e "${GREEN}✓ Configuración permanente aplicada${NC}"
        echo ""
        echo -e "${YELLOW}ADVERTENCIA DE SEGURIDAD:${NC}"
        echo "  ptrace_scope = 0 permite que cualquier proceso de tu usuario"
        echo "  pueda adjuntarse a otros procesos. Esto reduce la seguridad."
        echo ""
        echo "Para revertir:"
        echo "  sudo rm $CONFIG_FILE"
        echo "  echo 1 | sudo tee /proc/sys/kernel/yama/ptrace_scope"
        ;;
        
    3)
        echo ""
        echo -e "${YELLOW}Configurando capabilities para Python...${NC}"
        
        # Encontrar ruta de Python
        PYTHON_PATH=$(which python3)
        echo "Python encontrado en: $PYTHON_PATH"
        
        # Dar capability
        setcap cap_sys_ptrace=eip "$PYTHON_PATH"
        
        # Verificar
        echo ""
        echo "Capabilities actuales:"
        getcap "$PYTHON_PATH"
        
        echo ""
        echo -e "${GREEN}✓ Capability CAP_SYS_PTRACE otorgada a Python${NC}"
        echo ""
        echo "Este método es más seguro porque solo Python tiene acceso,"
        echo "no todos los procesos del usuario."
        echo ""
        echo "Para revertir:"
        echo "  sudo setcap -r $PYTHON_PATH"
        ;;
        
    4)
        echo "Cancelado."
        exit 0
        ;;
        
    *)
        echo -e "${RED}Opción inválida${NC}"
        exit 1
        ;;
esac

echo ""
echo "============================================================"
echo "Verificación de Configuración"
echo "============================================================"
echo ""

# Mostrar estado actual
echo "Estado de ptrace_scope:"
SCOPE=$(cat /proc/sys/kernel/yama/ptrace_scope)
echo "  Valor: $SCOPE"

case $SCOPE in
    0)
        echo -e "  ${GREEN}✓ Modo: Deshabilitado (permite ptrace)${NC}"
        ;;
    1)
        echo -e "  ${YELLOW}⚠ Modo: Restricted (solo procesos hijo)${NC}"
        echo "    El scanner NO funcionará así."
        ;;
    2)
        echo -e "  ${RED}✗ Modo: Admin-only${NC}"
        echo "    El scanner NO funcionará así."
        ;;
    3)
        echo -e "  ${RED}✗ Modo: No attach (completamente deshabilitado)${NC}"
        echo "    El scanner NO funcionará así."
        ;;
esac

echo ""

# Verificar capabilities de Python si se usó opción 3
PYTHON_PATH=$(which python3)
if getcap "$PYTHON_PATH" 2>/dev/null | grep -q cap_sys_ptrace; then
    echo -e "${GREEN}✓ Python tiene CAP_SYS_PTRACE${NC}"
else
    echo "  Python NO tiene CAP_SYS_PTRACE"
fi

echo ""
echo "============================================================"
echo "Prueba del Scanner"
echo "============================================================"
echo ""
echo "Para probar el scanner de memoria:"
echo ""
echo "1. Inicia RPCS3 con Skate 3"
echo "2. Ejecuta como tu usuario normal (NO sudo):"
echo "   cd /home/rexx/.gemini/antigravity/scratch/skate3-proxy-linux"
echo "   python3 src/memory/scanner.py"
echo ""
echo "Si ves las regiones de memoria, ¡funciona! 🎉"
echo ""

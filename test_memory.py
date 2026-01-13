#!/usr/bin/env python3
"""
Test interactivo del scanner de memoria RPCS3
Verifica que todos los componentes funcionen correctamente
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Colores ANSI
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def check_ptrace_permissions():
    """Verifica configuración de ptrace_scope"""
    print_header("Verificación de Permisos")
    
    try:
        with open('/proc/sys/kernel/yama/ptrace_scope', 'r') as f:
            scope = int(f.read().strip())
        
        print(f"ptrace_scope actual: {scope}")
        
        if scope == 0:
            print_success("ptrace_scope = 0 (permite acceso a memoria)")
            return True
        elif scope == 1:
            print_warning("ptrace_scope = 1 (solo procesos hijo)")
            print_info("El scanner NO funcionará con este valor")
            print_info("Ejecuta: sudo ./setup_memory_permissions.sh")
            return False
        else:
            print_error(f"ptrace_scope = {scope} (muy restrictivo)")
            print_info("Ejecuta: sudo ./setup_memory_permissions.sh")
            return False
            
    except Exception as e:
        print_error(f"Error leyendo ptrace_scope: {e}")
        return False

def check_python_capabilities():
    """Verifica si Python tiene CAP_SYS_PTRACE"""
    import subprocess
    
    try:
        python_path = sys.executable
        result = subprocess.run(
            ['getcap', python_path],
            capture_output=True,
            text=True
        )
        
        if 'cap_sys_ptrace' in result.stdout:
            print_success(f"Python tiene CAP_SYS_PTRACE: {python_path}")
            return True
        else:
            print_info(f"Python NO tiene CAP_SYS_PTRACE")
            return False
            
    except Exception as e:
        print_info("No se pudo verificar capabilities (normal si no está instalado)")
        return False

def check_rpcs3_running():
    """Verifica si RPCS3 está corriendo"""
    print_header("Verificación de RPCS3")
    
    try:
        from src.memory.scanner import RPCS3MemoryScanner
        
        # Usar el método del scanner para detectar RPCS3
        pid = RPCS3MemoryScanner._find_rpcs3_pid()
        
        if pid:
            print_success(f"RPCS3 encontrado:")
            print(f"  PID: {pid}")
            
            # Mostrar nombre del proceso
            try:
                with open(f'/proc/{pid}/comm', 'r') as f:
                    comm = f.read().strip()
                    print(f"  Proceso: {comm}")
            except:
                pass
                
            return True
        else:
            print_warning("RPCS3 NO está corriendo")
            print_info("Inicia RPCS3 (nativo o AppImage) antes de continuar")
            return False
            
    except Exception as e:
        print_error(f"Error buscando RPCS3: {e}")
        return False

def test_memory_scanner():
    """Prueba el scanner de memoria"""
    print_header("Prueba del Scanner de Memoria")
    
    try:
        from src.memory.scanner import RPCS3MemoryScanner
        
        print_info("Conectando al scanner...")
        scanner = RPCS3MemoryScanner()
        
        print_success(f"Scanner conectado a RPCS3 PID {scanner.pid}")
        
        # Test 1: Leer regiones de memoria
        print("\nTest 1: Lectura de regiones de memoria")
        regions = scanner.get_memory_regions(writable_only=False)
        print_success(f"Encontradas {len(regions)} regiones de memoria")
        
        # Mostrar algunas regiones
        print("\nPrimeras 5 regiones:")
        for region in regions[:5]:
            size_mb = (region.end - region.start) / 1024 / 1024
            print(f"  {region.start:016X}-{region.end:016X} "
                  f"{region.permissions} {size_mb:8.2f} MB")
        
        # Test 2: Lectura de memoria
        print("\nTest 2: Lectura de memoria")
        if regions:
            test_addr = regions[0].start
            test_data = scanner.read_memory(test_addr, 16)
            
            if test_data:
                hex_str = ' '.join(f'{b:02X}' for b in test_data)
                print_success(f"Lectura exitosa en {test_addr:016X}:")
                print(f"  {hex_str}")
            else:
                print_warning("No se pudo leer memoria (puede ser normal para algunas regiones)")
        
        # Test 3: Buscar patrón simple
        print("\nTest 3: Búsqueda de patrón")
        print_info("Buscando patrón de bytes en memoria...")
        print_warning("Esto puede tardar unos segundos...")
        
        # Buscar ELF header (común en ejecutables)
        elf_pattern = b'\x7fELF'
        addresses = scanner.find_pattern(elf_pattern, max_results=3)
        
        if addresses:
            print_success(f"Patrón ELF encontrado en {len(addresses)} ubicaciones:")
            for addr in addresses:
                print(f"  {addr:016X}")
        else:
            print_info("Patrón no encontrado (normal)")
        
        print_success("\n¡Todas las pruebas del scanner completadas!")
        return True
        
    except RuntimeError as e:
        print_error(f"Error inicializando scanner: {e}")
        return False
    except Exception as e:
        print_error(f"Error en pruebas del scanner: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_recommendations():
    """Muestra recomendaciones según resultados"""
    print_header("Recomendaciones")
    
    print("Para usar el scanner de memoria:")
    print("\n1. Asegúrate de tener permisos:")
    print("   sudo ./setup_memory_permissions.sh")
    print("\n2. Inicia RPCS3 con Skate 3")
    print("\n3. Ejecuta este test nuevamente:")
    print("   python3 test_memory.py")
    print("\n4. Si todo funciona, integra el scanner en el proxy:")
    print("   # En main.py, descomentar sección de memory scanner")
    print()

def main():
    """Función principal"""
    print_header("Test del Sistema de Manipulación de Memoria")
    print("Este script verifica que puedas acceder a la memoria de RPCS3\n")
    
    results = {
        'permissions': False,
        'rpcs3': False,
        'scanner': False
    }
    
    # Check 1: Permisos
    results['permissions'] = check_ptrace_permissions()
    has_caps = check_python_capabilities()
    
    if not results['permissions'] and not has_caps:
        print_error("\n¡Se necesita configurar permisos!")
        print_info("Ejecuta: sudo ./setup_memory_permissions.sh")
        show_recommendations()
        return 1
    
    # Check 2: RPCS3
    results['rpcs3'] = check_rpcs3_running()
    
    if not results['rpcs3']:
        print_warning("\nRPCS3 no está corriendo")
        print_info("Inicia RPCS3 y ejecuta este test nuevamente")
        return 1
    
    # Check 3: Scanner
    results['scanner'] = test_memory_scanner()
    
    # Resumen final
    print_header("Resumen")
    
    all_ok = all(results.values())
    
    if all_ok:
        print_success("¡TODO FUNCIONA CORRECTAMENTE!")
        print()
        print("El scanner de memoria está listo para usar.")
        print("Puedes integrarlo en el proxy para parches avanzados.")
        print()
        print_info("Ver: MEMORY_MANIPULATION_GUIDE.md para más detalles")
        return 0
    else:
        print_warning("Algunos tests fallaron:")
        for key, value in results.items():
            status = "✓" if value else "✗"
            print(f"  {status} {key}")
        print()
        show_recommendations()
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nError inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

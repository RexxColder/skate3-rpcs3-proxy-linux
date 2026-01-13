# 🧠 Guía de Manipulación de Memoria - RPCS3

Esta guía explica cómo configurar y usar el sistema de manipulación de memoria para RPCS3 en Linux.

---

## 📋 Requisitos Previos

### 1. Sistema Operativo
- ✅ **Linux** (Kernel 2.6.26+)
- ✅ Soporte para `/proc/[pid]/mem` y `/proc/[pid]/maps`
- ✅ Python 3.8+

### 2. Permisos Necesarios

Para leer/escribir la memoria de RPCS3, necesitas **uno** de estos métodos:

| Método | Seguridad | Persistencia | Dificultad |
|--------|-----------|--------------|------------|
| **ptrace_scope = 0** (Temporal) | ⚠️ Media | ❌ Hasta reinicio | ⭐ Fácil |
| **ptrace_scope = 0** (Permanente) | ⚠️ Baja | ✅ Permanente | ⭐⭐ Media |
| **CAP_SYS_PTRACE** | ✅ Alta | ✅ Permanente | ⭐⭐⭐ Avanzada |

---

## 🚀 Configuración Rápida

### Método 1: Temporal (Recomendado para Pruebas)

```bash
# Ejecutar como root
sudo ./setup_memory_permissions.sh
# Seleccionar opción 1
```

O manualmente:

```bash
# Ver estado actual
cat /proc/sys/kernel/yama/ptrace_scope

# Configurar (requiere sudo)
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope

# Verificar
cat /proc/sys/kernel/yama/ptrace_scope  # Debe mostrar: 0
```

> **⚠️ IMPORTANTE:** Este cambio se pierde al reiniciar.

### Método 2: Permanente

```bash
sudo ./setup_memory_permissions.sh
# Seleccionar opción 2
```

O manualmente:

```bash
# Crear archivo de configuración
sudo bash -c 'echo "kernel.yama.ptrace_scope = 0" > /etc/sysctl.d/10-ptrace.conf'

# Aplicar
sudo sysctl -p /etc/sysctl.d/10-ptrace.conf
```

### Método 3: Capabilities (Más Seguro)

```bash
sudo ./setup_memory_permissions.sh
# Seleccionar opción 3
```

O manualmente:

```bash
# Dar capability solo a Python
sudo setcap cap_sys_ptrace=eip $(which python3)

# Verificar
getcap $(which python3)
# Salida esperada: /usr/bin/python3 = cap_sys_ptrace+eip
```

---

## 🧪 Probar el Scanner

### 1. Iniciar RPCS3

```bash
# Abre RPCS3 y carga Skate 3
rpcs3
```

### 2. Probar el Scanner

```bash
cd /home/rexx/.gemini/antigravity/scratch/skate3-proxy-linux
python3 src/memory/scanner.py
```

**Salida esperada:**

```
Intentando conectar a RPCS3...
RPCS3 encontrado con PID 12345

Conectado a RPCS3 PID 12345
Regiones de memoria: 2847

Primeras 10 regiones:
  00005555FC000000-00005555FC001000 r--p     0.00 MB /usr/bin/rpcs3
  00005555FC001000-00005555FE123000 r-xp    33.13 MB /usr/bin/rpcs3
  ...
  
Test de lectura en 00005555FC000000:
  7F 45 4C 46 02 01 01 00 00 00 00 00 00 00 00 00
```

### 3. Si Hay Errores

#### Error: "No se encontró proceso RPCS3"

```bash
# Verificar que RPCS3 está corriendo
pgrep -x rpcs3

# Si no retorna nada, RPCS3 no está corriendo
```

#### Error: "Permission denied" en /proc/[pid]/mem

```bash
# Verificar ptrace_scope
cat /proc/sys/kernel/yama/ptrace_scope

# Si es > 0, necesitas configurarlo:
sudo ./setup_memory_permissions.sh
```

#### Error: "Operation not permitted"

Posibles causas:
1. **SELinux** o **AppArmor** bloqueando
2. **ptrace_scope** no configurado correctamente
3. No tienes permisos sobre el proceso RPCS3

```bash
# Verificar SELinux
getenforce

# Si está en "Enforcing", temporalmente:
sudo setenforce 0

# Verificar AppArmor
sudo aa-status
```

---

## 🔧 Uso del Scanner en el Proxy

### Ejemplo Básico

```python
from src.memory.scanner import RPCS3MemoryScanner

# Conectar a RPCS3
scanner = RPCS3MemoryScanner()

# Leer una dirección
data = scanner.read_memory(0x12345678, 16)
print(f"Data: {data.hex()}")

# Escribir en una dirección
scanner.write_memory(0x12345678, b'\x90\x90\x90\x90')

# Buscar un patrón
addresses = scanner.find_pattern_from_hex("90 90 90 90 ?? 90")
print(f"Patrón encontrado en: {[hex(a) for a in addresses]}")
```

### Integración con Proxy

El proxy puede usar el scanner para:

1. **Parches anti-desync avanzados**
2. **Detectar estados del juego**
3. **Modificar variables en memoria**

```python
# En main.py
from src.memory.scanner import RPCS3MemoryScanner

try:
    scanner = RPCS3MemoryScanner()
    logger.info(f"Scanner de memoria conectado a PID {scanner.pid}")
    
    # Buscar patrón de desync y parchearlo
    desync_pattern = "01 02 03 04 ?? 05 06"
    addresses = scanner.find_pattern_from_hex(desync_pattern)
    
    for addr in addresses:
        scanner.write_memory(addr + 4, b'\x00')  # Parchear byte wildcard
        logger.info(f"Parcheado desync en {addr:016X}")
        
except RuntimeError:
    logger.warning("No se pudo inicializar scanner de memoria (RPCS3 no está corriendo)")
```

---

## 🔍 Funcionalidades del Scanner

### Buscar Patrones

```python
# Patrón exacto
pattern = b'\x90\x90\x90\x90'
addresses = scanner.find_pattern(pattern)

# Patrón con wildcards (usando -1)
pattern = bytes([0x90, 0x90, -1, 0x90])  # 90 90 ?? 90
addresses = scanner.find_pattern(pattern, wildcard=-1)

# Desde string hex
addresses = scanner.find_pattern_from_hex("90 90 ?? 90")
```

### Leer/Escribir Memoria

```python
# Leer
data = scanner.read_memory(address, 16)  # Lee 16 bytes

# Escribir
success = scanner.write_memory(address, b'\x00\x01\x02\x03')
```

### Obtener Regiones de Memoria

```python
# Todas las regiones escribibles
regions = scanner.get_memory_regions(writable_only=True)

for region in regions:
    print(f"{region.start:016X}-{region.end:016X} {region.permissions}")
```

---

## 🛡️ Consideraciones de Seguridad

### ⚠️ Advertencias

1. **ptrace_scope = 0 reduce la seguridad**
   - Permite que cualquier proceso de tu usuario se adjunte a otros procesos
   - Úsalo solo en sistemas de desarrollo/juego
   - No recomendado para servidores

2. **Manipular memoria puede crashear RPCS3**
   - Siempre haz backup de tus saves
   - Prueba en un ambiente seguro primero

3. **Privilegios elevados**
   - Nunca ejecutes el proxy como root
   - Usa capabilities cuando sea posible

### ✅ Mejores Prácticas

1. **Usar capabilities en lugar de ptrace_scope = 0**
   ```bash
   sudo setcap cap_sys_ptrace=eip $(which python3)
   ```

2. **Testear primero en read-only**
   ```python
   # Solo leer, no escribir
   regions = scanner.get_memory_regions(writable_only=False)
   ```

3. **Validar antes de escribir**
   ```python
   # Leer primero
   original = scanner.read_memory(address, 4)
   
   # Escribir
   scanner.write_memory(address, new_data)
   
   # Verificar
   verify = scanner.read_memory(address, 4)
   assert verify == new_data
   ```

---

## 📊 Información Técnica

### /proc/[pid]/mem

- **Archivo especial** que representa la memoria del proceso
- Necesita permisos de lectura/escritura
- Acceso controlado por `ptrace_scope`

### /proc/[pid]/maps

- **Solo lectura** (no necesita permisos especiales)
- Muestra el layout de memoria del proceso
- Formato:
  ```
  address           perms offset   dev   inode      pathname
  00400000-00452000 r-xp  00000000 08:02 173521     /usr/bin/foo
  ```

### ptrace_scope Valores

| Valor | Descripción |
|-------|-------------|
| **0** | Cualquier proceso puede ptrace a procesos del mismo usuario |
| **1** | Solo procesos padre pueden hacer ptrace a hijos (default en Ubuntu) |
| **2** | Solo root puede hacer ptrace |
| **3** | ptrace completamente deshabilitado |

---

## 🐛 Troubleshooting

### Problema: Scanner no encuentra RPCS3

**Solución:**
```bash
# Verificar proceso
ps aux | grep rpcs3

# El proceso puede llamarse diferente
pgrep -i rpcs  # Case insensitive
```

### Problema: Permission denied constantemente

**Solución:**
```bash
# Método 1: Verificar ptrace_scope
cat /proc/sys/kernel/yama/ptrace_scope

# Método 2: Verificar ownership del proceso
ps -u $(whoami) | grep rpcs3

# Método 3: Verificar capabilities
getcap $(which python3)
```

### Problema: Región de memoria no legible

Algunas regiones pueden no ser legibles incluso con permisos correctos. Es normal.

**Solución:**
```python
# El scanner ya maneja esto con try/except
data = scanner.read_memory(address, length)
if data is None:
    logger.warning("Región no accesible")
```

---

## 📚 Recursos Adicionales

- [Linux ptrace man page](https://man7.org/linux/man-pages/man2/ptrace.2.html)
- [/proc filesystem documentation](https://man7.org/linux/man-pages/man5/proc.5.html)
- [Linux capabilities](https://man7.org/linux/man-pages/man7/capabilities.7.html)
- [Yama LSM documentation](https://www.kernel.org/doc/html/latest/admin-guide/LSM/Yama.html)

---

## ✅ Checklist de Configuración

Antes de usar el scanner, verifica:

- [ ] RPCS3 está instalado y funciona
- [ ] `ptrace_scope` configurado o capabilities otorgadas
- [ ] Python 3.8+ instalado
- [ ] Scanner de prueba ejecutado exitosamente
- [ ] Sin errores de permisos

---

**¡Listo para manipular memoria!** 🚀

Si tienes problemas, consulta la sección de troubleshooting o ejecuta:
```bash
python3 src/memory/scanner.py
```

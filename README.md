# 🎮 Skate 3 RPCS3 Online Proxy - Linux Edition

Port completo del proxy Skate 3 de Windows a Linux para RPCS3.

## 📊 Estado del Proyecto

**Versión:** 0.95 (Autenticación Funcional)  
**Estado:** ✅ Autenticación completa - ⚠️ Keep-alive en desarrollo

### ✅ Funciona (95%)
- ✅ Protocolo EA Blaze completamente implementado
- ✅ TDF Builder Windows-style con tipos 0x1F y 0x1D
- ✅ Inyección de credenciales correcta
- ✅ **Autenticación con EA servers exitosa**
- ✅ Detección RPCS3 (nativo y AppImage)
- ✅ Sistema completo de análisis y debugging

### ⚠️ En Desarrollo (5%)
- Respuestas automáticas a comandos keep-alive
- Sistema de auto-responder para mantener conexión

---

## 🚀 Quick Start

### Prerequisitos
- Linux (Arch, Ubuntu, Debian, Fedora)
- Python 3.8+
- RPCS3 (nativo o AppImage)
- Skate 3 ROM

### Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/TUUSER/skate3-proxy-linux.git
cd skate3-proxy-linux

# 2. Instalar dependencias
pip3 install -r requirements.txt

# 3. Configurar credenciales EA
./setup_credentials.sh

# 4. Configurar red
sudo ./setup_network.sh

# 5. Configurar RPCS3
# En RPCS3 → Configuration → Network:
# - PSN Status: RPCN
# - IP/Hosts switches: gosredirector.ea.com=127.0.0.1
```

### Ejecución

```bash
# Método simple
python3 main.py

# Con monitor
python3 run_with_monitor.py

# Con captura para debugging
python3 run_debug_capture.py
```

---

## 📁 Estructura del Proyecto

```
skate3-proxy-linux/
├── main.py                      # Entry point
├── run_with_monitor.py          # Monitor de memoria
├── run_debug_capture.py         # Captura de paquetes
├── requirements.txt             # Dependencias Python
│
├── setup_credentials.sh         # Config de credenciales EA
├── setup_network.sh             # Config de redirección
├── setup_memory_permissions.sh  # Permisos ptrace
│
├── src/
│   ├── network/
│   │   ├── proxy.py            # Proxy MITM principal
│   │   ├── redirector.py       # Redirector (puerto 42100)
│   │   ├── blaze.py            # Parser protocolo Blaze
│   │   ├── tdf.py              # Builder TDF Windows-style
│   │   └── tdf_replace.py      # Búsqueda/reemplazo TDF
│   ├── memory/
│   │   └── scanner.py          # Scanner memoria RPCS3
│   └── config/
│       └── manager.py          # Gestor configuración
│
├── tests/
│   ├── test_windows_auth.py
│   ├── test_exact_windows_packet.py
│   └── analyze_*.py            # Scripts de análisis
│
├── docs/
│   ├── BLAZE_PROTOCOL_ANALYSIS.md
│   ├── POST_AUTH_ANALYSIS.md
│   ├── MEMORY_MANIPULATION_GUIDE.md
│   └── NEXT_STEPS.md
│
└── README.md                    # Este archivo
```

---

## 🔧 Configuración Detallada

### 1. Credenciales EA

**Automático:**
```bash
./setup_credentials.sh
```

**Manual:**
```json
# ~/.config/skate3-proxy/login.json
{
  "email": "tu_email@ea.com",
  "password": "tu_password",
  "psnName": "TuNombrePSN"
}
```

### 2. Redirección de Red

El script `setup_network.sh` configura `/etc/hosts`:
```
127.0.0.1  gosredirector.ea.com
```

### 3. RPCS3

**Via GUI:**
1. Configuration → Network
2. PSN Status → RPCN
3. IP/Hosts switches → `gosredirector.ea.com=127.0.0.1`

**Via archivo:**
```yaml
# ~/.config/rpcs3/config.yml
Net:
  PSN status: RPCN
  IP swap list: "gosredirector.ea.com=127.0.0.1"
```

---

## 🎮 Uso con Skate 3

1. **Iniciar proxy** (uno de los métodos arriba)
2. **Abrir RPCS3** con Skate 3
3. **En el menú del juego** → "Online" o "EA Skate"
4. **Intentar conectar**

### Resultado Esperado

El proxy mostrará:
```
🔐 Interceptado paquete de autenticación
✅ Paquete 0x3C construido (78 bytes)
```

En Skate 3:
- Autenticación exitosa
- Mensaje: "Lost connection to EA Nation"

> **Nota:** La autenticación funciona correctamente. El mensaje "lost connection" indica que el keep-alive aún está en desarrollo (ver sección Estado del Proyecto).

---

## 📊 Cómo Funciona

### Flujo de Red

```
Skate 3 → RPCS3 → gosredirector.ea.com (127.0.0.1:42100)
                     ↓
                  Redirector Server
                     ↓
                  Proxy MITM (127.0.0.1:9999)
                     ↓
                  EA Servers (159.153.70.49:10010)
```

### Protocolo EA Blaze

El proxy implementa el protocolo Blaze de EA:
- **Component:** Categoría del mensaje (Auth, Game State, etc.)
- **Command:** Acción específica dentro del component
- **TDF Fields:** Type-Data-Field, formato de datos propietario de EA

### Inyección de Credenciales

**Método Windows (replicado exactamente):**
1. Interceptar paquete 0xC8 del juego
2. Construir NUEVO paquete 0x3C con credenciales
3. Enviar paquete propio a EA
4. Formato exacto: 78 bytes con tags correctos

---

## 🧪 Testing y Debugging

### Test del Builder TDF
```bash
python3 test_windows_auth.py
```
Verifica estructura del paquete de autenticación.

### Captura de Paquetes
```bash
python3 run_debug_capture.py
```
Guarda logs en `captures/packets_*.log` y `captures/packets_*.hex`

### Análisis de Protocolo
```bash
python3 analyze_complete_session.py
```
Genera `COMPLETE_PROTOCOL_MAP.txt` con análisis byte por byte.

### Comparación con Windows
```bash
python3 compare_packets.py
```
Compara paquetes generados vs capturas Windows.

---

## 📚 Documentación Técnica

### Análisis del Protocolo
- [`BLAZE_PROTOCOL_ANALYSIS.md`](docs/BLAZE_PROTOCOL_ANALYSIS.md) - Estructura del protocolo
- [`POST_AUTH_ANALYSIS.md`](docs/POST_AUTH_ANALYSIS.md) - Paquetes post-autenticación
- [`COMPLETE_PROTOCOL_MAP.txt`](COMPLETE_PROTOCOL_MAP.txt) - Mapeo completo (generado)

### Desarrollo
- [`NEXT_STEPS.md`](docs/NEXT_STEPS.md) - Próximos pasos y TODOs
- [`MEMORY_MANIPULATION_GUIDE.md`](docs/MEMORY_MANIPULATION_GUIDE.md) - Escaneo de memoria

---

## 🔍 Troubleshooting

### "Permission denied" en setup scripts
```bash
chmod +x setup_*.sh
sudo ./setup_network.sh  # Este requiere sudo
```

### Proxy no intercepta paquetes

**Verificar `/etc/hosts`:**
```bash
cat /etc/hosts | grep gosredirector
# Debe mostrar: 127.0.0.1  gosredirector.ea.com
```

**Verificar config RPCS3:**
```bash
grep "IP swap" ~/.config/rpcs3/config.yml
```

### ImportError al ejecutar
```bash
pip3 install -r requirements.txt
```

### "Lost connection" inmediatamente

**Esto es esperado actualmente.** El proxy autentica correctamente pero la conexión se pierde porque el sistema de keep-alive aún está en desarrollo.

**Solución futura:** Implementar auto-responder para comandos críticos (ver NEXT_STEPS.md).

---

## 🛠️ Desarrollo

### Implementación del Keep-Alive

**Comandos que requieren respuesta:**
1. `0x02/0x14` - QOS Configuration
2. `0x09/0x02` - Ping/Pong
3. `0x02/0x08` - Game Ready

Ver [`docs/POST_AUTH_ANALYSIS.md`](docs/POST_AUTH_ANALYSIS.md) para detalles completos.

### Contribuir

1. Fork el repositorio
2. Crear branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

---

## 📜 Licencia

Este proyecto es un port del proxy Skate 3 original de Windows. El protocolo EA Blaze fue analizado mediante ingeniería inversa de capturas de red.

**Uso educativo y personal únicamente.**

---

## 🙏 Créditos

- **Proyecto original:** Skate 3 Online Proxy (Windows)
- **Análisis de protocolo:** Ingeniería inversa de capturas PCAPNG
- **Testing:** RPCS3 + Skate 3
- **Desarrollo Linux:** Port completo del protocolo

---

## 📞 Soporte

**Issues:** GitHub Issues  
**Documentación:** Ver carpeta `docs/`  
**Logs:** `captures/` (con run_debug_capture.py)

---

## 🎯 Estado de Funcionalidades

| Funcionalidad | Estado | Notas |
|---------------|--------|-------|
| Protocolo Blaze | ✅ 100% | Completamente implementado |
| TDF Builder | ✅ 100% | Windows-style, tipos 0x1F/0x1D |
| Autenticación | ✅ 100% | EA acepta credenciales |
| Redirector | ✅ 100% | Puerto 42100 funcional |
| Proxy MITM | ✅ 100% | Puerto 9999 funcional |
| Detección RPCS3 | ✅ 100% | Nativo y AppImage |
| Keep-Alive | ⚠️ 5% | En desarrollo |
| Anti-Desync | ⚠️ 50% | Implementado parcialmente |

---

**Proyecto activo en desarrollo. ¡Contribuciones bienvenidas!**
# skate3-rpcs3-proxy-linux

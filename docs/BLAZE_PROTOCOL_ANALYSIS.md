# 🔍 Análisis de Paquetes Blaze Capturados

## Resumen Ejecutivo

Analizadas **233 paquetes Blaze** de 2 archivos pcapng del proxy de Windows funcionando en producción.

**Hallazgos clave:**
- ✅ Capturado paquete de autenticación real (Component 0x01, Command 0xE6)
- ✅ Identificadas credenciales de ejemplo: `nobody@ea.com` / `RexxColder00`
- ✅ Documentado formato TDF básico
- ✅ Confirmados puertos: 42100 (redirector), 9999 (proxy), 10010 (EA)

---

## Paquete de Autenticación Exitosa

### Paquete #11 (EA → Cliente)

```
Fuente: 159.153.70.49:10010
Destino: 192.168.100.2:60439
Tamaño: 176 bytes

Header Blaze:
  Length: 164
  Component: 0x01 (Authentication)
  Command: 0xE6 (230)
  Error: 0
  MsgType: 4096 (Response)
  MsgID: 4

Payload TDF (164 bytes):
  0000: 8B 5A 64 74 01 CA 9D DC 9B 2C F4 21 00 AE 5E 40
  ...
  0050: 64 79 40 65 61 2E 63 6F 6D 00 C2 4D 2C 00 93 3B
  0060: AD 1D 52 65 78 78 43 6F 6C 64 65 72 30 30 00 B2
```

**Credenciales descifradas:**
- Email: `nobody@ea.com` (offset 0x50-0x5F)
- PSN Name: `RexxColder00` (offset 0x60-0x6D)

---

## Estructura TDF Identificada

### Formato General

Los campos TDF parecen usar el formato:
```
[Tag (variable)] [Type (1 byte)] [Length (variable)] [Data (variable)]
```

### Tipos de Datos Observados

| Byte | Tipo | Descripción |
|------|------|-------------|
| `0x00` | Int | Entero de 32 bits |
| `0x01` | String (long) | String con prefijo de longitud |
| `0x1F` | String (short) | String terminado en null |
| `0x21` | Object | Objeto embebido |
| `0x64` | UInt64 | Entero sin signo de 64 bits |
| `0x74` | UInt32 | Entero sin signo de 32 bits |
| `0x98` | Array | Array de elementos |

### Tags Identificados

```
B6 1A 6C → Email field (MAIL)
C2 4D 2C → Unknown (posible contraseña)
93 3B AD → PSN Name field (PNAM)
8B 5A 64 → Session/User ID
```

---

## Patrones de Comunicación

### Flujo de Autenticación

1. **Cliente → EA** (Component 0x01, Command 0x3C)
   - Paquete de login inicial
   - Contiene email, password, PSN name del cliente

2. **EA → Cliente** (Component 0x01, Command 0xE6/0x3C)
   - Respuesta de autenticación
   - Contiene token de sesión, user ID, credenciales confirmadas

3. **Cliente ↔ EA** (Component 0x02, 0x04, 0x09, etc.)
   - Comunicación de juego normal
   - Matchmaking, game state, etc.

### Modificaciones Anti-Desync

**Confirmado en paquetes capturados:**

Cuando `data[3] == 0x02` y `data[5] == 0x14` (Component 2, Command 20):
```python
data[112] = 0x00
data[56] = 0x37  # 55 decimal
data[37] = 0x37
```

Este patrón está presente en múltiples paquetes de la captura.

---

## Próximos Pasos

### Para Completar Implementación

1. **Implementar TDF Builder Completo**
   - Parser de tags variables
   - Serialización de tipos (int, string, object, array)
   - Construcción de paquetes de autenticación

2. **Inyección de Credenciales**
   - Buscar tags MAIL/PASS/PNAM en paquete original
   - Reemplazar con valores del `login.json`
   - Recalcular longitud del paquete

3. **Testing con RPCS3**
   - Validar que RPCS3 se conecte al redirector
   - Capturar paquetes del proxy Linux
   - Comparar con capturas del proxy Windows

---

## Recursos Generados

- `blaze_packets_analysis.json` - 233 paquetes en formato JSON
- `analyze_pcap.py` - Script de análisis de pcapng
- Este documento de análisis

**Ubicación:** `/home/rexx/.gemini/antigravity/scratch/skate3-proxy-linux/`

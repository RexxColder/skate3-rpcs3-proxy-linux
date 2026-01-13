#!/usr/bin/env python3
"""
Modificación del proxy con logging detallado de paquetes
Para debugging y comparación con capturas de Windows
"""

import asyncio
import logging
import time
import os
from datetime import datetime
from pathlib import Path
import sys

# Importar componentes del proxy
from src.memory.scanner import RPCS3MemoryScanner
from src.network.redirector import RedirectorServer
from src.network.proxy import ProxyServer, EACredentials

# Setup logging con hex dumps
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directorio para guardar capturas
CAPTURE_DIR = Path("/home/rexx/.gemini/antigravity/scratch/skate3-proxy-linux/captures")
CAPTURE_DIR.mkdir(exist_ok=True)

class PacketLogger:
    """Logger de paquetes con hex dumps"""
    
    def __init__(self):
        self.packet_count = 0
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = CAPTURE_DIR / f"packets_{timestamp}.log"
        self.hex_file = CAPTURE_DIR / f"packets_{timestamp}.hex"
        
    def log_packet(self, direction: str, data: bytes, description: str = ""):
        """
        Registra un paquete con hex dump completo
        
        Args:
            direction: "SEND" o "RECV"
            data: Bytes del paquete
            description: Descripción adicional
        """
        self.packet_count += 1
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Log textual
        with open(self.log_file, 'a') as f:
            f.write(f"\n{'='*70}\n")
            f.write(f"[{timestamp}] Packet #{self.packet_count} - {direction}\n")
            if description:
                f.write(f"Description: {description}\n")
            f.write(f"Length: {len(data)} bytes\n")
            f.write(f"{'='*70}\n")
            
            # Hex dump estilo hexdump
            f.write("\nHex Dump:\n")
            for i in range(0, len(data), 16):
                # Offset
                f.write(f"{i:08X}  ")
                
                # Hex bytes
                hex_part = data[i:i+16]
                for j in range(16):
                    if j < len(hex_part):
                        f.write(f"{hex_part[j]:02X} ")
                    else:
                        f.write("   ")
                    if j == 7:
                        f.write(" ")
                
                # ASCII representation
                f.write(" |")
                for byte in hex_part:
                    if 32 <= byte <= 126:
                        f.write(chr(byte))
                    else:
                        f.write(".")
                f.write("|\n")
            
            # Parse Blaze header si es suficientemente grande
            if len(data) >= 12:
                f.write(f"\nBlaze Header Analysis:\n")
                length = int.from_bytes(data[0:2], 'big')
                component = data[3]
                command = data[5]
                error = int.from_bytes(data[6:8], 'big')
                msg_type = int.from_bytes(data[8:10], 'big')
                msg_id = int.from_bytes(data[10:12], 'big')
                
                f.write(f"  Length:    {length}\n")
                f.write(f"  Component: 0x{component:02X} ({component})\n")
                f.write(f"  Command:   0x{command:02X} ({command})\n")
                f.write(f"  Error:     {error}\n")
                f.write(f"  Msg Type:  {msg_type}\n")
                f.write(f"  Msg ID:    {msg_id}\n")
        
        # Hex raw para fácil comparación
        with open(self.hex_file, 'a') as f:
            f.write(f"\n# Packet #{self.packet_count} - {direction} - {description}\n")
            f.write(' '.join(f'{b:02X}' for b in data))
            f.write('\n')
        
        # Log en consola
        logger.info(f"{direction} packet #{self.packet_count}: {len(data)} bytes - {description}")

class DebugProxyServer(ProxyServer):
    """Proxy con logging detallado de todos los paquetes"""
    
    def __init__(self, *args, packet_logger=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.packet_logger = packet_logger or PacketLogger()
    
    async def tunnel_to_ea(self, reader, writer):
        """RPCS3 → EA con logging"""
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                
                # Log packet FROM client
                desc = "From RPCS3"
                
                # Verificar si es autenticación
                if (len(data) > 5 and 
                    data[3] == 0x01 and  # Authentication
                    data[5] == 0xC8):     # Login
                    
                    desc = "AUTH REQUEST (Original from RPCS3)"
                    self.packet_logger.log_packet("RECV", data, desc)
                    
                    logger.info("🔐 Interceptado paquete de autenticación")
                    
                    if self.credentials:
                        data = self.inject_credentials(data)
                        desc = "AUTH REQUEST (Modified with credentials)"
                        self.packet_logger.log_packet("SEND", data, desc)
                        logger.info("✅ Credenciales inyectadas y logged")
                        self.authenticated = True
                else:
                    self.packet_logger.log_packet("SEND", data, desc)
                
                writer.write(data)
                await writer.drain()
                
        except Exception as e:
            logger.error(f"Error en tunnel_to_ea: {e}")
    
    async def tunnel_from_ea(self, reader, writer):
        """EA → RPCS3 con logging"""
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                
                # Log packet FROM EA
                desc = "From EA Server"
                
                # Identificar respuesta de autenticación
                if len(data) >= 12:
                    component = data[3]
                    command = data[5]
                    error = int.from_bytes(data[6:8], 'big')
                    
                    if component == 0x01:  # Authentication
                        if error == 0:
                            desc = f"AUTH RESPONSE (SUCCESS) - Cmd: 0x{command:02X}"
                        else:
                            desc = f"AUTH RESPONSE (ERROR {error}) - Cmd: 0x{command:02X}"
                
                self.packet_logger.log_packet("RECV", data, desc)
                
                # Aplicar parches anti-desync
                data = self.apply_desync_patches(data)
                
                writer.write(data)
                await writer.drain()
                
        except Exception as e:
            logger.error(f"Error en tunnel_from_ea: {e}")

def load_credentials_simple():
    """Carga credenciales sin ConfigManager"""
    import json
    config_file = Path.home() / '.config' / 'skate3-proxy' / 'login.json'
    
    if not config_file.exists():
        return None
    
    try:
        with open(config_file, 'r') as f:
            data = json.load(f)
            return EACredentials(
                email=data['email'],
                password=data['password'],
                psn_name=data['psnName']
            )
    except Exception as e:
        logger.error(f"Error cargando credenciales: {e}")
        return None

async def main():
    """Función principal con logging de paquetes"""
    
    print("\n" + "="*70)
    print(f"{'🔍 SKATE 3 PROXY - MODO DEBUG CON CAPTURA DE PAQUETES 🔍':^70}")
    print("="*70)
    print()
    
    # Inicializar packet logger
    packet_logger = PacketLogger()
    logger.info(f"📝 Logs de paquetes en: {CAPTURE_DIR}")
    logger.info(f"   - Textual: {packet_logger.log_file.name}")
    logger.info(f"   - Hex:     {packet_logger.hex_file.name}")
    
    # Scanner de memoria (opcional)
    try:
        scanner = RPCS3MemoryScanner()
        logger.info(f"🔍 Scanner conectado a RPCS3 PID {scanner.pid}")
    except RuntimeError:
        logger.warning("⚠️  Scanner no disponible (RPCS3 no corriendo)")
    
    # Cargar credenciales
    credentials = load_credentials_simple()
    
    if not credentials:
        logger.error("❌ No se encontraron credenciales!")
        logger.info("Ejecuta: ./setup_credentials.sh")
        return
    
    logger.info(f"✅ Credenciales cargadas para: {credentials.email}")
    
    # Inicializar servidores
    redirector = RedirectorServer(port=42100, proxy_port=9999)
    proxy = DebugProxyServer(
        port=9999,
        credentials=credentials,
        packet_logger=packet_logger
    )
    
    logger.info("\n🚀 Iniciando servidores...")
    logger.info("📡 Redirector: puerto 42100")
    logger.info("🔧 Proxy MITM: puerto 9999")
    logger.info("🔍 DEBUG MODE: Capturando todos los paquetes")
    logger.info("\n⏳ Esperando conexiones de RPCS3...\n")
    
    # Iniciar servidores
    try:
        await asyncio.gather(
            redirector.start(),
            proxy.start()
        )
    except KeyboardInterrupt:
        logger.info("\n\n🛑 Deteniendo proxy...")
        logger.info(f"📊 Total de paquetes capturados: {packet_logger.packet_count}")
        logger.info(f"📝 Logs guardados en: {CAPTURE_DIR}")
        await redirector.stop()
        await proxy.stop()
        logger.info("✅ Proxy detenido")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Saliendo...")
        sys.exit(0)

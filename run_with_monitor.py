#!/usr/bin/env python3
"""
Monitor de memoria en tiempo real - VERSIÓN SIMPLE
Sin dependencias externas (no requiere requests, PyQt6, etc.)
"""

import asyncio
import logging
import time
import os
from datetime import datetime
from pathlib import Path
import sys

# Importar solo lo esencial
from src.memory.scanner import RPCS3MemoryScanner
from src.network.redirector import RedirectorServer
from src.network.proxy import ProxyServer, EACredentials

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleMemoryMonitor:
    """Monitor simple de memoria sin psutil"""
    
    def __init__(self):
        self.rpcs3_scanner = None
        self.proxy_pid = os.getpid()
        self.stats = {
            'rpcs3': {
                'pid': None,
                'regions': 0,
            },
            'proxy': {
                'pid': self.proxy_pid,
                'packets_intercepted': 0,
                'credentials_injected': 0
            }
        }
        
    async def init_rpcs3_scanner(self):
        """Intenta conectar al scanner de RPCS3"""
        try:
            self.rpcs3_scanner = RPCS3MemoryScanner()
            self.stats['rpcs3']['pid'] = self.rpcs3_scanner.pid
            logger.info(f"🔍 Scanner conectado a RPCS3 PID {self.rpcs3_scanner.pid}")
            return True
        except RuntimeError as e:
            logger.warning(f"⚠️  RPCS3 no detectado: {e}")
            return False
    
    async def update_stats(self):
        """Actualiza estadísticas de memoria"""
        # Stats de RPCS3
        if self.rpcs3_scanner:
            try:
                regions = self.rpcs3_scanner.get_memory_regions(writable_only=False)
                self.stats['rpcs3']['regions'] = len(regions)
            except:
                pass
    
    def print_stats(self):
        """Imprime estadísticas"""
        print("\n" + "="*70)
        print(f"{'MONITOR DE MEMORIA TIEMPO REAL':^70}")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^70}")
        print("="*70)
        
        # RPCS3 Stats
        print("\n📊 RPCS3:")
        if self.stats['rpcs3']['pid']:
            print(f"  PID:            {self.stats['rpcs3']['pid']}")
            print(f"  Regiones Mem:   {self.stats['rpcs3']['regions']}")
        else:
            print("  ❌ No detectado")
        
        # Proxy Stats
        print("\n🔧 Proxy:")
        print(f"  PID:            {self.stats['proxy']['pid']}")
        print(f"  Paquetes:       {self.stats['proxy']['packets_intercepted']}")
        print(f"  Inyecciones:    {self.stats['proxy']['credentials_injected']}")
        
        print("\n" + "="*70)
        print("Presiona Ctrl+C para detener")
        print()
    
    async def monitor_loop(self):
        """Loop de monitoreo que actualiza cada 3 segundos"""
        while True:
            await self.update_stats()
            self.print_stats()
            await asyncio.sleep(3)

class MonitoredProxyServer(ProxyServer):
    """Proxy con contador de paquetes"""
    
    def __init__(self, *args, monitor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.monitor = monitor
    
    async def tunnel_to_ea(self, reader, writer):
        """Override para contar paquetes interceptados"""
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                
                # Contar paquetes
                if self.monitor:
                    self.monitor.stats['proxy']['packets_intercepted'] += 1
                
                # Verificar si es paquete de autenticación
                if (len(data) > 5 and 
                    data[3] == 0x01 and  # BlazeComponent.Authentication
                    data[5] == 0xC8):     # AuthenticationCommand.Login
                    
                    logger.info("🔐 Interceptado paquete de autenticación")
                    
                    if self.credentials:
                        data = self.inject_credentials(data)
                        logger.info("✅ Credenciales inyectadas")
                        if self.monitor:
                            self.monitor.stats['proxy']['credentials_injected'] += 1
                        self.authenticated = True
                    else:
                        logger.warning("⚠️  Sin credenciales configuradas!")
                
                writer.write(data)
                await writer.drain()
                
        except Exception as e:
            logger.error(f"Error en tunnel_to_ea: {e}")
    
    async def tunnel_from_ea(self, reader, writer):
        """Override para contar paquetes"""
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                
                if self.monitor:
                    self.monitor.stats['proxy']['packets_intercepted'] += 1
                
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
    """Función principal con monitoreo"""
    
    print("\n" + "="*70)
    print(f"{'🎮 SKATE 3 RPCS3 PROXY - MODO MONITOREO 🎮':^70}")
    print("="*70)
    print()
    
    # Inicializar monitor
    monitor = SimpleMemoryMonitor()
    
    # Intentar conectar a RPCS3
    await monitor.init_rpcs3_scanner()
    
    # Cargar credenciales
    credentials = load_credentials_simple()
    
    if not credentials:
        logger.error("❌ No se encontraron credenciales!")
        logger.info("Ejecuta: ./setup_credentials.sh")
        return
    
    logger.info(f"✅ Credenciales cargadas para: {credentials.email}")
    
    # Inicializar servidores
    redirector = RedirectorServer(port=42100, proxy_port=9999)
    proxy = MonitoredProxyServer(
        port=9999,
        credentials=credentials,
        monitor=monitor
    )
    
    # Iniciar monitoreo en background
    monitor_task = asyncio.create_task(monitor.monitor_loop())
    
    logger.info("\n🚀 Iniciando servidores...")
    logger.info("📡 Redirector: puerto 42100")
    logger.info("🔧 Proxy MITM: puerto 9999")
    logger.info("\n⏳ Esperando conexiones de RPCS3...\n")
    
    # Iniciar servidores
    try:
        await asyncio.gather(
            redirector.start(),
            proxy.start(),
            monitor_task
        )
    except KeyboardInterrupt:
        logger.info("\n\n🛑 Deteniendo proxy...")
        monitor_task.cancel()
        await redirector.stop()
        await proxy.stop()
        logger.info("✅ Proxy detenido")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Saliendo...")
        sys.exit(0)

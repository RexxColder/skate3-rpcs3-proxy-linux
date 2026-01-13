#!/usr/bin/env python3
"""
Skate 3 RPCS3 Proxy - Main Entry Point
Linux port of Windows proxy for playing Skate 3 online
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.network import RedirectorServer, ProxyServer
from src.config import ConfigManager, UpdateManager

# Memory manipulation (optional - requires permissions)
try:
    from src.memory import RPCS3MemoryScanner, RPCS3MemoryPatcher
    MEMORY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Memory module not available: {e}")
    MEMORY_AVAILABLE = False

logger = logging.getLogger(__name__)


class Skate3Proxy:
    """Main proxy application"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.updater = UpdateManager(self.config)
        
        self.redirector = None
        self.proxy = None
        
    async def start(self):
        """Inicia todos los servidores"""
        logger.info("=" * 60)
        logger.info("Skate 3 RPCS3 Proxy - Linux Edition v1.0.3")
        logger.info("=" * 60)
        
        # Cargar configuración
        settings = self.config.load_settings()
        credentials = self.config.load_credentials()
        
        if not credentials:
            logger.warning("No se encontraron credenciales configuradas")
            logger.warning("Crea ~/.config/skate3-proxy/login.json con tu info de EA")
            logger.warning('Formato: {"email": "...", "password": "...", "psnName": "..."}')
        
        # Verificar actualizaciones
        update_info = self.updater.check_update()
        if update_info:
            logger.info(f"Nueva versión disponible: {update_info.get('version')}")
            if 'changelog' in update_info:
                logger.info(f"Changelog: {update_info['changelog']}")
        
        # Descargar usernames
        usernames = self.updater.download_usernames()
        logger.info(f"Usernames cargados: {len(usernames)}")
        
        # Memory patching (opcional)
        if MEMORY_AVAILABLE:
            try:
                logger.info("\nIntentando conectar a RPCS3...")
                scanner = RPCS3MemoryScanner()
                patcher = RPCS3MemoryPatcher(scanner)
                
                # Verificar EBOOT
                if patcher.verify_eboot():
                    logger.info("Aplicando parches de memoria...")
                    applied = patcher.apply_all_game_speed_patches()
                    logger.info(f"✅ {applied}/4 parches aplicados")
                else:
                    logger.warning("⚠️  EBOOT modificado, saltando parches")
                    
            except RuntimeError as e:
                logger.info(f"Memory patching no disponible: {e}")
                logger.info("(El proxy funcionará sin parches de memoria)")
        else:
            logger.info("Memory patching deshabilitado (módulo no disponible)")
        
        # Crear servidores
        self.redirector = RedirectorServer()
        self.proxy = ProxyServer(credentials=credentials)
        
        # Iniciar ambos servidores
        logger.info("\nIniciando servidores...")
        
        try:
            await asyncio.gather(
                self.redirector.start(),
                self.proxy.start()
            )
        except KeyboardInterrupt:
            logger.info("\n\nDeteniendo servidores...")
            await self.stop()
    
    async def stop(self):
        """Detiene todos los servidores"""
        if self.redirector:
            await self.redirector.stop()
        if self.proxy:
            await self.proxy.stop()


def main():
    """Entry point"""
    import os
    
    # Configurar logging - soportar DEBUG via env var
    log_level = logging.DEBUG if os.getenv('DEBUG') == '1' else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(Path.home() / '.config' / 'skate3-proxy' / 'proxy.log')
        ]
    )
    
    # Crear directorio de logs
    log_dir = Path.home() / '.config' / 'skate3-proxy'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Iniciar aplicación
    app = Skate3Proxy()
    
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        logger.info("Proxy detenido por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

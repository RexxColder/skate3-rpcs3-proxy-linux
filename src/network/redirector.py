#!/usr/bin/env python3
"""
Redirector Server - Port 42100
Intercepts initial RPCS3 connection and redirects to local proxy
Based on Form1.cs lines 252-322
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RedirectorServer:
    """
    Servidor que escucha en puerto 42100 y redirige RPCS3 al proxy local.
    Replica la funcionalidad del método _00A0() del código original.
    """
    
    def __init__(self, port: int = 42100, proxy_host: str = '127.0.0.1', proxy_port: int = 9999):
        self.port = port
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.server: Optional[asyncio.Server] = None
        
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Maneja conexión de RPCS3.
        Basado en Form1.cs líneas 254-321
        """
        addr = writer.get_extra_info('peername')
        logger.info(f"Redirector: Nueva conexión desde {addr}")
        
        try:
            # Leer petición inicial de RPCS3
            data = await reader.read(2048)
            if not data:
                logger.warning("Redirector: No se recibieron datos")
                return
            
            logger.debug(f"Redirector: Recibidos {len(data)} bytes")
            
            # Construir respuesta de redirección
            # Replica el array de bytes de Form1.cs líneas 292-302
            response = bytearray([
                0x00, 0x46, 0x00, 0x05, 0x00, 0x01, 0x00, 0x00, 0x10, 0x00,
                0x00, 0x00, 0x86, 0x49, 0x32, 0xD0, 0x00, 0xDA, 0x1B, 0x35,
                0x00, 0xA2, 0xFC, 0xF4, 0x1F, 0x1C, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0xA7, 0x00, 0x00, 0x74, 0x9F, 0x99,
                0x46, 0x31, 0xC2, 0xFC, 0xB4, 0x52, 0x27, 0x1B, 0x00, 0xCE,
                0x58, 0xF5, 0x21, 0x00, 0xE2, 0x4B, 0xB3, 0x74, 0x00, 0x00,
                0x00, 0x00
            ])
            
            # Insertar hostname del proxy (Form1.cs líneas 304-308)
            hostname_bytes = self.proxy_host.encode('ascii')
            for i, byte in enumerate(hostname_bytes):
                if 26 + i < len(response):
                    response[26 + i] = byte
            
            # Insertar puerto en big-endian (Form1.cs líneas 309-314)
            port_bytes = self.proxy_port.to_bytes(2, 'big')
            response[66] = port_bytes[0]
            response[67] = port_bytes[1]
            
            # Copiar sequence number de la petición (Form1.cs líneas 315-316)
            if len(data) >= 12:
                response[10] = data[10]
                response[11] = data[11]
            
            # Enviar respuesta
            writer.write(bytes(response))
            await writer.drain()
            
            logger.info(f"Redirector: Enviada redirección a {self.proxy_host}:{self.proxy_port}")
            
        except Exception as e:
            logger.error(f"Redirector: Error manejando cliente: {e}", exc_info=True)
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
    
    async def start(self):
        """Inicia el servidor de redirección"""
        try:
            self.server = await asyncio.start_server(
                self.handle_client,
                '0.0.0.0',
                self.port
            )
            
            addrs = ', '.join(str(sock.getsockname()) for sock in self.server.sockets)
            logger.info(f"Redirector Server listening on {addrs}")
            
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            logger.error(f"Redirector: Error iniciando servidor: {e}", exc_info=True)
            raise
    
    async def stop(self):
        """Detiene el servidor"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("Redirector Server stopped")


if __name__ == '__main__':
    # Test standalone
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        server = RedirectorServer()
        try:
            await server.start()
        except KeyboardInterrupt:
            await server.stop()
    
    asyncio.run(main())

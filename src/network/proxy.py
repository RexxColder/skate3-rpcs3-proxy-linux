#!/usr/bin/env python3
"""
Main Proxy Server - Port 9999
MITM proxy between RPCS3 and EA Blaze servers
Based on Form1.cs lines 324-396
"""

import asyncio
import logging
from typing import Optional
from dataclasses import dataclass

from .blaze import BlazePacket, BlazeComponent, AuthenticationCommand
from .tdf import inject_credentials_into_packet

logger = logging.getLogger(__name__)


@dataclass
class EACredentials:
    """Credenciales de EA para autenticación"""
    email: str
    password: str
    psn_name: str


class ProxyServer:
    """
    Servidor proxy principal que intercepta y modifica tráfico
    entre RPCS3 y servidor EA Blaze.
    """
    
    def __init__(
        self,
        port: int = 9999,
        ea_server: str = '159.153.70.49',
        ea_port: int = 10010,
        credentials: Optional[EACredentials] = None
    ):
        self.port = port
        self.ea_server = ea_server
        self.ea_port = ea_port
        self.credentials = credentials
        self.server: Optional[asyncio.Server] = None
        self.authenticated = False
        
        # Field names from decrypted strings (MAIL, PASS, PNAM)
        self.field_names = ['MAIL', 'PASS', 'PNAM']
    
    def set_credentials(self, credentials: EACredentials):
        """Actualiza credenciales de EA"""
        self.credentials = credentials
    
    async def handle_client(
        self,
        client_reader: asyncio.StreamReader,
        client_writer: asyncio.StreamWriter
    ):
        """
        Maneja conexión de RPCS3 y crea túnel con EA.
        Basado en Form1.cs líneas 324-349
        """
        addr = client_writer.get_extra_info('peername')
        logger.info(f"Proxy: Nueva conexión desde {addr}")
        
        ea_reader: Optional[asyncio.StreamReader] = None
        ea_writer: Optional[asyncio.StreamWriter] = None
        
        try:
            # Conectar al servidor EA
            logger.info(f"Proxy: Conectando a EA {self.ea_server}:{self.ea_port}")
            ea_reader, ea_writer = await asyncio.open_connection(
                self.ea_server,
                self.ea_port
            )
            logger.info("Proxy: Conectado a servidor EA")
            
            # Crear tareas bidireccionales
            await asyncio.gather(
                self.tunnel_to_ea(client_reader, ea_writer),
                self.tunnel_from_ea(ea_reader, client_writer),
                return_exceptions=True
            )
            
        except Exception as e:
            logger.error(f"Proxy: Error en túnel: {e}", exc_info=True)
        finally:
            self.authenticated = False
            
            # Cerrar conexiones
            try:
                client_writer.close()
                await client_writer.wait_closed()
            except:
                pass
            
            if ea_writer:
                try:
                    ea_writer.close()
                    await ea_writer.wait_closed()
                except:
                    pass
            
            logger.info(f"Proxy: Conexión cerrada con {addr}")
    
    async def tunnel_to_ea(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ):
        """
        RPCS3 → EA (con intercepción de autenticación)
        Basado en Form1.cs líneas 362-396
        """
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                
                # Verificar si es paquete de autenticación
                # Component 1 (0x01), Command 200 (0xC8)
                if (len(data) > 5 and 
                    data[3] == BlazeComponent.Authentication and 
                    data[5] == AuthenticationCommand.Login):
                    
                    logger.info("Proxy: Interceptado paquete de autenticación")
                    
                    if self.credentials:
                        # Inyectar credenciales reales
                        data = self.inject_credentials(data)
                        logger.info("Proxy: Credenciales inyectadas")
                        self.authenticated = True
                    else:
                        logger.warning("Proxy: Sin credenciales configuradas!")
                
                writer.write(data)
                await writer.drain()
                
        except Exception as e:
            logger.error(f"Proxy: Error en tunnel_to_ea: {e}")
    
    async def tunnel_from_ea(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ):
        """
        EA → RPCS3 (con modificaciones anti-desync)
        Basado en Form1.cs líneas 362-396
        """
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                
                # Aplicar parches anti-desync
                # Basado en Form1.cs líneas 368-373
                data = self.apply_desync_patches(data)
                
                writer.write(data)
                await writer.drain()
                
        except Exception as e:
            logger.error(f"Proxy: Error en tunnel_from_ea: {e}")
    
    def inject_credentials(self, data: bytes) -> bytes:
        """
        Inyecta credenciales ESTILO WINDOWS: Reemplaza paquete 0xC8 con nuestro 0x3C.
        No modifica el paquete del juego, sino que construye uno nuevo.
        """
        if not self.credentials:
            logger.warning("Proxy: Sin credenciales para inyectar")
            return data
        
        try:
            # Importar builder TDF
            from .tdf import BlazeAuthPacket
            import struct
            
            # Extraer msg_id del paquete original para mantener sincronización
            msg_id = struct.unpack('>H', data[10:12])[0] if len(data) >= 12 else 2
            
            # Construir NUESTRO paquete 0x3C estilo Windows
            our_packet = BlazeAuthPacket(msg_id=msg_id)
            our_packet.add_email(self.credentials.email)
            our_packet.add_password(self.credentials.password)
            our_packet.add_psn_name(self.credentials.psn_name)
            
            new_data = our_packet.build()
            
            logger.info(f"✅ Paquete 0x3C construido ({len(new_data)} bytes)")
            logger.debug(f"  Original 0xC8: {len(data)} bytes")
            logger.debug(f"  Nuevo 0x3C: {len(new_data)} bytes")
            
            return new_data
            
        except Exception as e:
            logger.error(f"Error construyendo paquete 0x3C: {e}", exc_info=True)
            return data
    
    def apply_desync_patches(self, data: bytes) -> bytes:
        """
        Aplica parches para prevenir desincronización.
        Basado en Form1.cs líneas 368-373
        """
        data = bytearray(data)
        
        # Patch específico para Component 2, Command 20
        if len(data) > 112 and data[3] == 0x02 and data[5] == 0x14:
            data[112] = 0x00
            data[56] = 0x37   # 55 decimal
            data[37] = 0x37
            logger.debug("Proxy: Aplicado patch anti-desync")
        
        return bytes(data)
    
    async def start(self):
        """Inicia el servidor proxy"""
        try:
            self.server = await asyncio.start_server(
                self.handle_client,
                '0.0.0.0',
                self.port
            )
            
            addrs = ', '.join(str(sock.getsockname()) for sock in self.server.sockets)
            logger.info(f"Proxy Server listening on {addrs}")
            
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            logger.error(f"Proxy: Error iniciando servidor: {e}", exc_info=True)
            raise
    
    async def stop(self):
        """Detiene el servidor"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("Proxy Server stopped")


if __name__ == '__main__':
    # Test standalone
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        # Credenciales de prueba
        creds = EACredentials(
            email='test@example.com',
            password='testpass',
            psn_name='TestPlayer'
        )
        
        server = ProxyServer(credentials=creds)
        try:
            await server.start()
        except KeyboardInterrupt:
            await server.stop()
    
    asyncio.run(main())

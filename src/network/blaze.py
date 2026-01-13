#!/usr/bin/env python3
"""
EA Blaze Protocol Parser/Builder
Based on decompiled Blaze component classes
"""

from enum import IntEnum
from typing import Dict, Any, Optional
import struct
import logging

logger = logging.getLogger(__name__)


class BlazeComponent(IntEnum):
    """EA Blaze Protocol Components"""
    Authentication = 0x01
    GameManager = 0x04
    Redirector = 0x05
    Util = 0x09
    UserSessions = 0x0F
    Messaging = 0x19


class AuthenticationCommand(IntEnum):
    """Authentication component commands"""
    Login = 0xC8  # 200 decimal
    SilentLogin = 0x4C
    Logout = 0x1E


class BlazePacket:
    """
    EA Blaze Protocol Packet Structure
    Header: 12 bytes + TDF payload
    """
    
    def __init__(self):
        self.length: int = 0
        self.component: int = 0
        self.command: int = 0
        self.error_code: int = 0
        self.msg_type: int = 0
        self.msg_id: int = 0
        self.params: Dict[str, Any] = {}
    
    @classmethod
    def from_bytes(cls, data: bytes) -> Optional['BlazePacket']:
        """
        Parse Blaze packet from bytes
        Format basado en análisis del código original
        """
        if len(data) < 12:
            return None
        
        packet = cls()
        
        # Header structure (12 bytes)
        packet.length = struct.unpack('>H', data[0:2])[0]
        packet.component = data[3]
        packet.command = data[5]
        packet.error_code = struct.unpack('>H', data[6:8])[0]
        packet.msg_type = struct.unpack('>H', data[8:10])[0]
        packet.msg_id = struct.unpack('>H', data[10:12])[0]
        
        # TODO: Parse TDF (Type-Data-Field) payload
        # Los parámetros están en formato TDF después del header
        
        return packet
    
    def to_bytes(self) -> bytes:
        """
        Build Blaze packet bytes
        Basado en clase _2003 del código original
        """
        # Construir header
        header = bytearray(12)
        
        # Length (placeholder, se actualiza después)
        struct.pack_into('>H', header, 0, 0)
        
        # Component y Command
        header[3] = self.component
        header[5] = self.command
        
        # Error code, msg type, msg id
        struct.pack_into('>H', header, 6, self.error_code)
        struct.pack_into('>H', header, 8, self.msg_type)
        struct.pack_into('>H', header, 10, self.msg_id)
        
        # TODO: Serializar parámetros en formato TDF
        payload = bytearray()
        
        # Actualizar length
        total_length = len(header) + len(payload)
        struct.pack_into('>H', header, 0, total_length)
        
        return bytes(header) + bytes(payload)
    
    def is_authentication(self) -> bool:
        """Verifica si es paquete de autenticación"""
        return (self.component == BlazeComponent.Authentication and 
                self.command == AuthenticationCommand.Login)
    
    def __repr__(self):
        return (f"BlazePacket(component={self.component:02X}, "
                f"command={self.command:02X}, "
                f"msg_type={self.msg_type}, "
                f"msg_id={self.msg_id})")


class TDFBuilder:
    """
    Type-Data-Field builder for Blaze protocol
    TDF es el formato de serialización de EA
    """
    
    @staticmethod
    def build_string(tag: str, value: str) -> bytes:
        """Construye TDF de tipo string"""
        # TODO: Implementar formato TDF completo
        # Por ahora, formato simplificado
        result = bytearray()
        result.extend(tag.encode('ascii')[:4].ljust(4, b'\x00'))
        result.append(0x03)  # String type
        result.extend(len(value).to_bytes(2, 'big'))
        result.extend(value.encode('utf-8'))
        return bytes(result)
    
    @staticmethod
    def build_int(tag: str, value: int) -> bytes:
        """Construye TDF de tipo integer"""
        result = bytearray()
        result.extend(tag.encode('ascii')[:4].ljust(4, b'\x00'))
        result.append(0x00)  # Int type
        result.extend(value.to_bytes(4, 'big'))
        return bytes(result)


if __name__ == '__main__':
    # Test parsing
    test_data = bytes([
        0x00, 0x46, 0x00, 0x01, 0x00, 0xC8, 0x00, 0x00,
        0x00, 0x00, 0x12, 0x34
    ])
    
    packet = BlazePacket.from_bytes(test_data)
    if packet:
        print(f"Parsed: {packet}")
        print(f"Is auth: {packet.is_authentication()}")

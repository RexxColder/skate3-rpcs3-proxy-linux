#!/usr/bin/env python3
"""
EA Blaze Protocol - TDF (Type-Data-Field) Implementation
Based on analysis of real captured packets from Windows proxy
"""

import struct
import logging
from typing import Dict, Any, List, Union
from enum import IntEnum

logger = logging.getLogger(__name__)


class TDFType(IntEnum):
    """TDF Data Types identificados en paquetes capturados"""
    INT = 0x00
    STRING = 0x1F
    UINT64 = 0x64
    UINT32 = 0x74
    OBJECT = 0x21
    ARRAY = 0x98


class TDFTag:
    """
    Tags TDF extraídos de análisis de paquetes.
    Cada tag es un identificador de 3 bytes comprimido.
    """
    # Authentication fields (del proxy Windows funcionando)
    EMAIL = bytes([0xB6, 0x1A, 0x6C])      # Campo de email (MAIL)
    PASSWORD = bytes([0xC2, 0x1C, 0xF3])   # Campo de contraseña (PASS) - Windows
    PSN_NAME = bytes([0xC2, 0xE8, 0x6D])   # Campo de PSN name (PNAM) - Windows
    
    # Otros campos identificados
    SESSION_ID = bytes([0x8B, 0x5A, 0x64])
    USER_ID = bytes([0xB2, 0xCB, 0xE7])
    
    @staticmethod
    def from_string(tag: str) -> bytes:
        """
        Convierte string de tag a bytes comprimidos.
        Basado en el esquema de compresión de EA Blaze.
        """
        # Algoritmo de compresión de tags de EA
        # Cada carácter se mapea a 6 bits (A-Z, a-z, 0-9, _)
        result = 0
        for char in tag[:4]:  # Máximo 4 caracteres
            if 'A' <= char <= 'Z':
                val = ord(char) - ord('A') + 1
            elif 'a' <= char <= 'z':
                val = ord(char) - ord('a') + 27
            elif '0' <= char <= '9':
                val = ord(char) - ord('0') + 53
            elif char == '_':
                val = 63
            else:
                val = 0
            result = (result << 6) | val
        
        # Convertir a 3 bytes big-endian
        return result.to_bytes(3, 'big')


class TDFBuilder:
    """
    Constructor de campos TDF para el protocolo Blaze.
    Basado en análisis de paquetes reales capturados.
    """
    
    @staticmethod
    def build_string(tag: bytes, value: str) -> bytes:
        """
        Construye un campo TDF de tipo string.
        FIX: Length INCLUYE el null terminator (como Windows)
        
        Formato observado en paquetes:
        [Tag: 3 bytes] [Type: 0x1F] [Length: variable] [String: variable] [Null: 0x00]
        """
        result = bytearray()
        
        # Tag (3 bytes)
        result.extend(tag)
        
        # Type (string con terminador null)
        result.append(TDFType.STRING)
        
        # Length (encoded como variable-length integer)
        encoded_value = value.encode('utf-8')
        # FIX CRÍTICO: Length INCLUYE el null terminator (+1)
        length = len(encoded_value) + 1  # +1 para null terminator
        
        # EA usa encoding variable para longitudes
        if length < 64:
            result.append(length)
        else:
            # Para strings largos (no común en autenticación)
            result.extend(struct.pack('>H', length | 0x8000))
        
        # String data
        result.extend(encoded_value)
        
        # Null terminator
        result.append(0x00)
        
        return bytes(result)
    
    @staticmethod
    def build_string_type_1d(tag: bytes, value: str) -> bytes:
        """
        Construye campo TDF tipo 0x1D (observado en proxy Windows).
        Usado para PASSWORD y PSN_NAME.
        FIX: Length INCLUYE el null terminator (como Windows)
        
        Formato: [Tag: 3 bytes] [Type: 0x1D] [Length: 1 byte] [String] [Null: 0x00]
        """
        result = bytearray()
        result.extend(tag)  # Tag (3 bytes)
        result.append(0x1D)  # Type 0x1D
        
        encoded_value = value.encode('utf-8')
        # FIX CRÍTICO: Length INCLUYE el null terminator (+1)
        result.append(len(encoded_value) + 1)  # +1 para null
        result.extend(encoded_value)  # String data
        result.append(0x00)  # Null terminator
        
        return bytes(result)
    
    @staticmethod
    def build_uint32(tag: bytes, value: int) -> bytes:
        """Construye un campo TDF de tipo uint32"""
        result = bytearray()
        result.extend(tag)
        result.append(TDFType.UINT32)
        result.extend(struct.pack('>I', value))
        return bytes(result)
    
    @staticmethod
    def build_uint64(tag: bytes, value: int) -> bytes:
        """Construye un campo TDF de tipo uint64"""
        result = bytearray()
        result.extend(tag)
        result.append(TDFType.UINT64)
        result.extend(struct.pack('>Q', value))
        return bytes(result)
    
    @staticmethod
    def parse_tdf(data: bytes) -> Dict[str, Any]:
        """
        Parsea campos TDF de un payload.
        Útil para debugging y análisis.
        """
        fields = {}
        offset = 0
        
        while offset < len(data) - 3:
            # Leer tag (3 bytes)
            tag = data[offset:offset+3]
            offset += 3
            
            if offset >= len(data):
                break
            
            # Leer tipo
            field_type = data[offset]
            offset += 1
            
            # Parsear según tipo
            if field_type == TDFType.STRING:
                # Leer longitud
                if offset >= len(data):
                    break
                length = data[offset]
                offset += 1
                
                # Leer string
                if offset + length <= len(data):
                    value = data[offset:offset+length].decode('utf-8', errors='ignore')
                    fields[tag.hex()] = value
                    offset += length + 1  # +1 para null terminator
            
            elif field_type == TDFType.UINT32:
                if offset + 4 <= len(data):
                    value = struct.unpack('>I', data[offset:offset+4])[0]
                    fields[tag.hex()] = value
                    offset += 4
            
            elif field_type == TDFType.UINT64:
                if offset + 8 <= len(data):
                    value = struct.unpack('>Q', data[offset:offset+8])[0]
                    fields[tag.hex()] = value
                    offset += 8
            
            else:
                # Tipo desconocido, saltar
                break
        
        return fields


class BlazeAuthPacket:
    """
    Constructor de paquetes de autenticación Blaze.
    Basado en paquetes capturados del proxy de Windows.
    """
    
    def __init__(self, msg_id: int = 2):
        self.msg_id = msg_id
        self.component = 0x01  # Authentication
        self.command = 0x3C    # Login command (60 decimal) - ESTILO WINDOWS
        self.fields: List[bytes] = []
    
    def add_email(self, email: str):
        """Añade campo de email (MAIL)"""
        self.fields.append(TDFBuilder.build_string(TDFTag.EMAIL, email))
    
    def add_password(self, password: str):
        """Añade campo de contraseña (PASS) - tipo 0x1D estilo Windows"""
        self.fields.append(TDFBuilder.build_string_type_1d(TDFTag.PASSWORD, password))
    
    def add_psn_name(self, psn_name: str):
        """Añade campo de PSN name (PNAM) - tipo 0x1D estilo Windows"""
        self.fields.append(TDFBuilder.build_string_type_1d(TDFTag.PSN_NAME, psn_name))
    
    def build(self) -> bytes:
        """
        Construye el paquete completo de autenticación.
        
        Formato:
        [Header: 12 bytes] [TDF Fields: variable]
        """
        # Construir payload TDF
        tdf_payload = b''.join(self.fields)
        
        # Construir header Blaze (12 bytes)
        header = bytearray(12)
        
        # Length (bytes 0-1): longitud del payload
        payload_length = len(tdf_payload)
        struct.pack_into('>H', header, 0, payload_length)
        
        # Component (byte 3)
        header[3] = self.component
        
        # Command (byte 5)
        header[5] = self.command
        
        # Error code (bytes 6-7): 0 para request
        struct.pack_into('>H', header, 6, 0)
        
        # Message type (bytes 8-9): 0 para request
        struct.pack_into('>H', header, 8, 0)
        
        # Message ID (bytes 10-11)
        struct.pack_into('>H', header, 10, self.msg_id)
        
        # Combinar header + payload
        return bytes(header) + tdf_payload


class BlazeResponseBuilder:
    """
    Constructor de respuestas automáticas para keep-alive.
    Basado en análisis de paquetes del COMPLETE_PROTOCOL_MAP.txt
    """
    
    def __init__(self):
        self.ping_counter = 0  # Counter para timestamp incremental
    
    @staticmethod
    def build_ping_response(msg_id: int) -> bytes:
        """
        Construye respuesta para ping 0x09/0x02.
        
        Formato observado en capturas Windows:
        Header: 00 08 00 09 00 02 00 00 10 00 [msg_id] 
        Payload: CF 4A 6D 74 69 64 28 [timestamp_byte]
        
        Total: 20 bytes (12 header + 8 payload)
        """
        # Header (12 bytes)
        header = bytearray(12)
        
        # Length: 8 bytes payload
        struct.pack_into('>H', header, 0, 0x0008)
        
        # Component: 0x09 (UTIL)
        header[3] = 0x09
        
        # Command: 0x02 (ping)
        header[5] = 0x02
        
        # Error: 0
        struct.pack_into('>H', header, 6, 0)
        
        # Msg Type: 0x1000 (4096 = RESPONSE)
        struct.pack_into('>H', header, 8, 0x1000)
        
        # Msg ID: preservar del request
        struct.pack_into('>H', header, 10, msg_id)
        
        # Payload TDF (8 bytes)
        # Tag CF 4A 6D = "tid" (timestamp id)
        # Type 0x74 = UINT32
        # Value: timestamp incremental (último byte cambia)
        payload = bytes([
            0xCF, 0x4A, 0x6D,  # Tag "tid"
            0x74,              # Type UINT32
            0x69, 0x64, 0x28,  # Primeros 3 bytes del valor
            (0xD6 + (msg_id % 50))  # Último byte varía ligeramente
        ])
        
        return bytes(header) + payload
    
    @staticmethod
    def build_empty_response(component: int, command: int, msg_id: int) -> bytes:
        """
        Construye respuesta vacía (solo header) para comandos 0x0B.
        
        Usado para:
        - Component 0x0B, Command 0x8C
        - Component 0x0B, Command 0x40
        
        Total: 12 bytes (solo header, payload vacío)
        """
        header = bytearray(12)
        
        # Length: 0 (sin payload)
        struct.pack_into('>H', header, 0, 0x0000)
        
        # Component
        header[3] = component
        
        # Command
        header[5] = command
        
        # Error: 0
        struct.pack_into('>H', header, 6, 0)
        
        # Msg Type: 0x1000 (RESPONSE)
        struct.pack_into('>H', header, 8, 0x1000)
        
        # Msg ID
        struct.pack_into('>H', header, 10, msg_id)
        
        return bytes(header)


def inject_credentials_into_packet(packet_data: bytes, email: str, password: str, psn_name: str) -> bytes:
    """
    Inyecta credenciales en un paquete de autenticación existente.
    
    Estrategia:
    1. Parsear header original
    2. Reconstruir paquete con las nuevas credenciales
    3. Mantener el mismo msg_id del paquete original
    
    Args:
        packet_data: Paquete original de RPCS3
        email: Email de EA a inyectar
        password: Contraseña de EA a inyectar
        psn_name: Nombre PSN a inyectar
        
    Returns:
        Paquete modificado con credenciales inyectadas
    """
    if len(packet_data) < 12:
        logger.warning("Paquete demasiado pequeño para modificar")
        return packet_data
    
    # Extraer msg_id del paquete original
    msg_id = struct.unpack('>H', packet_data[10:12])[0]
    
    # Construir nuevo paquete con credenciales
    auth_packet = BlazeAuthPacket(msg_id=msg_id)
    auth_packet.add_email(email)
    auth_packet.add_password(password)
    auth_packet.add_psn_name(psn_name)
    
    new_packet = auth_packet.build()
    
    logger.info(f"Paquete de autenticación reconstruido: {len(new_packet)} bytes")
    logger.debug(f"  Email: {email}")
    logger.debug(f"  PSN: {psn_name}")
    
    return new_packet


if __name__ == '__main__':
    # Test del builder
    logging.basicConfig(level=logging.DEBUG)
    
    print("Testing TDF Builder...")
    
    # Crear paquete de autenticación de prueba
    packet = BlazeAuthPacket(msg_id=2)
    packet.add_email("test@example.com")
    packet.add_password("testpassword123")
    packet.add_psn_name("TestPlayer")
    
    result = packet.build()
    
    print(f"\nPaquete generado: {len(result)} bytes")
    print("Hex dump:")
    for i in range(0, len(result), 16):
        hex_str = ' '.join(f'{b:02X}' for b in result[i:i+16])
        print(f"  {i:04X}: {hex_str}")
    
    # Test de inyección
    print("\n\nTesting credential injection...")
    original = bytes([
        0x00, 0x40, 0x00, 0x01, 0x00, 0x3C, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x02
    ]) + b'\x00' * 64  # Paquete dummy
    
    injected = inject_credentials_into_packet(
        original,
        "real@email.com",
        "realpassword",
        "RealPlayer"
    )
    
    print(f"Paquete inyectado: {len(injected)} bytes")

#!/usr/bin/env python3
"""
EA Blaze Protocol - TDF Utilities
Búsqueda y reemplazo de campos TDF en paquetes
"""

import struct
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def find_tdf_field(data: bytes, tag: bytes) -> Optional[Tuple[int, int]]:
    """
    Busca un campo TDF por su tag en un paquete.
    
    Returns:
        Tuple (start_offset, end_offset) si se encuentra, None si no
    """
    offset = 12  # Saltar header Blaze
    
    while offset < len(data) - 4:
        # Leer tag (3 bytes)
        current_tag = data[offset:offset+3]
        
        if current_tag == tag:
            # Encontrado! Ahora determinar longitud del campo
            field_type = data[offset+3] if offset+3 < len(data) else None
            
            if field_type == 0x1F:  # String
                # Leer longitud
                if offset+4 >= len(data):
                    break
                    
                length = data[offset+4]
                # Campo completo: tag(3) + type(1) + length(1) + string(length) + null(1)
                field_end = offset + 3 + 1 + 1 + length + 1
                
                return (offset, field_end)
            else:
                # Tipo no soportado para reemplazo
                logger.debug(f"Campo encontrado pero tipo 0x{field_type:02X} no soportado")
                return None
        
        # Avanzar al siguiente campo (simplificado - asume strings)
        try:
            field_type = data[offset+3]
            if field_type == 0x1F:  # String
                length = data[offset+4]
                offset += 3 + 1 + 1 + length + 1
            else:
                # Saltar campo desconocido conservadoramente
                offset += 4
        except IndexError:
            break
    
    return None


def replace_tdf_string_field(data: bytes, tag: bytes, new_value: str) -> bytes:
    """
    Reemplaza el valor de un campo TDF string en un paquete.
    Preserva toda la estructura del paquete excepto el campo específico.
    
    Args:
        data: Paquete original
        tag: Tag del campo a reemplazar
        new_value: Nuevo valor string
        
    Returns:
        Paquete modificado o paquete original si no se encuentra el campo
    """
    field_pos = find_tdf_field(data, tag)
    
    if not field_pos:
        logger.warning(f"Campo con tag {tag.hex()} no encontrado en paquete")
        return data
    
    start, end = field_pos
    
    # Construir nuevo campo
    new_field = bytearray()
    new_field.extend(tag)  # Tag (3 bytes)
    new_field.append(0x1F)  # Type string
    
    encoded_value = new_value.encode('utf-8')
    new_field.append(len(encoded_value))  # Length
    new_field.extend(encoded_value)  # String data
    new_field.append(0x00)  # Null terminator
    
    # Construir nuevo paquete: antes + nuevo campo + después
    new_data = bytearray(data[:start])
    new_data.extend(new_field)
    new_data.extend(data[end:])
    
    # Actualizar longitud en header
    new_payload_length = len(new_data) - 12
    struct.pack_into('>H', new_data, 0, new_payload_length)
    
    logger.info(f"Campo {tag.hex()} reemplazado: {len(data)} → {len(new_data)} bytes")
    
    return bytes(new_data)


def inject_credentials_into_packet_v2(packet_data: bytes, email: str, password: str, psn_name: str) -> bytes:
    """
    Inyecta credenciales en un paquete PRESERVANDO todos los demás campos.
    
    Esta versión busca y reemplaza solo los campos específicos en lugar
    de reconstruir el paquete completo, preservando tokens RPCN y otros datos.
    
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
    
    # Tags TDF correctos (de paquetes capturados)
    TAG_EMAIL = bytes([0xB6, 0x1A, 0x6C])
    TAG_PASSWORD = bytes([0xC2, 0x4D, 0x2C])
    TAG_PSN_NAME = bytes([0x93, 0x3B, 0xAD])
    
    logger.info(f"Inyectando credenciales en paquete de {len(packet_data)} bytes")
    logger.debug(f"  Email: {email}")
    logger.debug(f"  PSN: {psn_name}")
    
    # Reemplazar cada campo preservando el resto del paquete
    modified = packet_data
    
    # Intentar reemplazar EMAIL
    modified = replace_tdf_string_field(modified, TAG_EMAIL, email)
    
    # Intentar reemplazar PASSWORD
    modified = replace_tdf_string_field(modified, TAG_PASSWORD, password)
    
    # Intentar reemplazar PSN_NAME  
    modified = replace_tdf_string_field(modified, TAG_PSN_NAME, psn_name)
    
    if len(modified) != len(packet_data):
        logger.info(f"✅ Paquete modificado: {len(packet_data)} → {len(modified)} bytes")
    else:
        logger.warning("⚠️  No se modificaron campos (puede que no existan en el paquete)")
    
    return modified


if __name__ == '__main__':
    # Test
    logging.basicConfig(level=logging.DEBUG)
    
    # Paquete de ejemplo con campos TDF
    test_packet = bytearray([
        0x00, 0x42, 0x00, 0x01, 0x00, 0xC8, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x02,  # Header
        0xB6, 0x1A, 0x6C, 0x1F, 0x04, 0x74, 0x65, 0x73, 0x74, 0x00,  # EMAIL: "test"
        0xC2, 0x4D, 0x2C, 0x1F, 0x04, 0x70, 0x61, 0x73, 0x73, 0x00,  # PASS: "pass"
    ])
    
    print("Paquete original:", len(test_packet), "bytes")
    print(' '.join(f'{b:02X}' for b in test_packet))
    
    modified = inject_credentials_into_packet_v2(
        bytes(test_packet),
        "newemail@test.com",
        "newpassword",
        "NewPSN"
    )
    
    print("\nPaquete modificado:", len(modified), "bytes")
    print(' '.join(f'{b:02X}' for b in modified))

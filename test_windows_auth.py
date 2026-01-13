#!/usr/bin/env python3
"""Test rápido del paquete 0x3C estilo Windows"""

from src.network.tdf import BlazeAuthPacket, TDFTag

def test_windows_style_packet():
    """Verifica estructura del paquete Windows-style"""
    
    print("\n" + "="*70)
    print("TEST: Paquete de Autenticación Estilo Windows")
    print("="*70)
    
    # Construir paquete con credenciales de ejemplo
    packet = BlazeAuthPacket(msg_id=2)
    packet.add_email("palettafacundo@proton.me")
    packet.add_password("Soyelmejor1.")
    packet.add_psn_name("RexxColder00")
    
    result = packet.build()
    
    print(f"\n📊 Paquete generado: {len(result)} bytes")
    print(f"   Esperado: ~64 bytes (Windows)")
    
    # Verificar header
    print(f"\n🔍 Header Analysis:")
    print(f"   Component: 0x{result[3]:02X} (esperado: 0x01) {'✓' if result[3] == 0x01 else '✗'}")
    print(f"   Command:   0x{result[5]:02X} (esperado: 0x3C) {'✓' if result[5] == 0x3C else '✗'}")
    
    # Hex dump
    print(f"\n📝 Hex Dump:")
    for i in range(0, len(result), 16):
        hex_part = ' '.join(f'{b:02X}' for b in result[i:i+16])
        ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in result[i:i+16])
        print(f"   {i:04X}: {hex_part:<48} {ascii_part}")
    
    # Verificar tags
    result_hex = result.hex()
    tags_found = {
        'EMAIL (B61A6C)': 'b61a6c' in result_hex,
        'PASS (C21CF3)': 'c21cf3' in result_hex,
        'PSN (C2E86D)': 'c2e86d' in result_hex
    }
    
    print(f"\n🏷️  Tags TDF:")
    for tag, found in tags_found.items():
        print(f"   {tag}: {'✓ Encontrado' if found else '✗ No encontrado'}")
    
    # Resultado
    all_ok = (
        result[3] == 0x01 and 
        result[5] == 0x3C and 
        all(tags_found.values()) and
        60 <= len(result) <= 80
    )
    
    print(f"\n{'='*70}")
    if all_ok:
        print("✅ TEST PASADO - Paquete compatible con Windows")
    else:
        print("❌ TEST FALLIDO - Revisar estructura")
    print("="*70)
    
    return all_ok

if __name__ == '__main__':
    test_windows_style_packet()

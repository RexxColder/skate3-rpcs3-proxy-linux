#!/usr/bin/env python3
"""
Test Auto-Responder para Keep-Alive
Valida que los response builders generen paquetes correctos
"""

import sys
sys.path.insert(0, '/home/rexx/.gemini/antigravity/scratch/skate3-proxy-linux')

from src.network.tdf import BlazeResponseBuilder
from src.network.proxy import ProxyServer
import struct


def test_ping_response():
    """Test del response builder para ping 0x09/0x02"""
    print("\n" + "="*70)
    print("TEST 1: Ping Response Builder (0x09/0x02)")
    print("="*70)
    
    builder = BlazeResponseBuilder()
    msg_id = 13  # Ejemplo del COMPLETE_PROTOCOL_MAP
    
    response = builder.build_ping_response(msg_id)
    
    print(f"\n✅ Response generado: {len(response)} bytes")
    print(f"   Esperado: 20 bytes (12 header + 8 payload)")
    
    # Hex dump
    print("\n📝 Hex Dump:")
    for i in range(0, len(response), 16):
        hex_part = ' '.join(f'{b:02X}' for b in response[i:i+16])
        ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in response[i:i+16])
        print(f"   {i:04X}: {hex_part:<48} {ascii_part}")
    
    # Validaciones
    checks = {
        'Tamaño correcto (20 bytes)': len(response) == 20,
        'Length field = 0x0008': struct.unpack('>H', response[0:2])[0] == 0x08,
        'Component = 0x09': response[3] == 0x09,
        'Command = 0x02': response[5] == 0x02,
        'Msg Type = 0x1000 (RESPONSE)': struct.unpack('>H', response[8:10])[0] == 0x1000,
        'Msg ID preservado': struct.unpack('>H', response[10:12])[0] == msg_id,
        'Payload contiene tag CF4A6D': response[12:15] == bytes([0xCF, 0x4A, 0x6D])
    }
    
    print("\n🔍 Validaciones:")
    all_pass = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check}")
        if not result:
            all_pass = False
    
    print("\n" + "="*70)
    if all_pass:
        print("✅ TEST PASADO - Ping response correcto")
    else:
        print("❌ TEST FALLIDO")
    print("="*70)
    
    return all_pass


def test_empty_response():
    """Test del response builder para comandos 0x0B"""
    print("\n" + "="*70)
    print("TEST 2: Empty Response Builder (0x0B/0x8C y 0x0B/0x40)")
    print("="*70)
    
    builder = BlazeResponseBuilder()
    
    # Test 0x0B/0x8C
    msg_id = 19
    response_8c = builder.build_empty_response(0x0B, 0x8C, msg_id)
    
    print(f"\n📦 Response 0x0B/0x8C: {len(response_8c)} bytes")
    print("   Hex:", ' '.join(f'{b:02X}' for b in response_8c))
    
    # Test 0x0B/0x40
    msg_id = 20
    response_40 = builder.build_empty_response(0x0B, 0x40, msg_id)
    
    print(f"\n📦 Response 0x0B/0x40: {len(response_40)} bytes")
    print("   Hex:", ' '.join(f'{b:02X}' for b in response_40))
    
    # Validaciones
    checks = {
        'Tamaño 0x8C correcto (12 bytes)': len(response_8c) == 12,
        'Tamaño 0x40 correcto (12 bytes)': len(response_40) == 12,
        '0x8C: Length = 0': struct.unpack('>H', response_8c[0:2])[0] == 0,
        '0x8C: Component = 0x0B': response_8c[3] == 0x0B,
        '0x8C: Command = 0x8C': response_8c[5] == 0x8C,
        '0x40: Command = 0x40': response_40[5] == 0x40,
        'Msg Type = 0x1000': struct.unpack('>H', response_8c[8:10])[0] == 0x1000
    }
    
    print("\n🔍 Validaciones:")
    all_pass = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check}")
        if not result:
            all_pass = False
    
    print("\n" + "="*70)
    if all_pass:
        print("✅ TEST PASADO - Empty responses correctos")
    else:
        print("❌ TEST FALLIDO")
    print("="*70)
    
    return all_pass


def test_header_parser():
    """Test del parser de headers Blaze"""
    print("\n" + "="*70)
    print("TEST 3: Blaze Header Parser")
    print("="*70)
    
    proxy = ProxyServer()
    
    # Paquete ping real del COMPLETE_PROTOCOL_MAP (paquete #4)
    ping_packet = bytes.fromhex('00000009000200000000000d')
    
    header = proxy.parse_blaze_header(ping_packet)
    
    print("\n📋 Header parseado:")
    for key, value in header.items():
        if key in ['component', 'command']:
            print(f"   {key}: 0x{value:02X} ({value})")
        else:
            print(f"   {key}: {value}")
    
    # Validaciones
    checks = {
        'Component = 0x09': header['component'] == 0x09,
        'Command = 0x02': header['command'] == 0x02,
        'Msg Type = 0 (REQUEST)': header['msg_type'] == 0,
        'Msg ID = 13': header['msg_id'] == 13
    }
    
    print("\n🔍 Validaciones:")
    all_pass = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check}")
        if not result:
            all_pass = False
    
    print("\n" + "="*70)
    if all_pass:
        print("✅ TEST PASADO - Parser funciona correctamente")
    else:
        print("❌ TEST FALLIDO")
    print("="*70)
    
    return all_pass


def test_auto_responder_logic():
    """Test de la lógica del auto-responder"""
    print("\n" + "="*70)
    print("TEST 4: Auto-Responder Logic")
    print("="*70)
    
    proxy = ProxyServer()
    proxy.authenticated = True
    
    # Test con ping request
    ping_request = bytes.fromhex('00000009000200000000000d')
    ping_response = proxy.build_auto_response(ping_request)
    
    print(f"\n🔔 Ping request procesado:")
    print(f"   Request: {ping_request.hex()}")
    print(f"   Response: {ping_response.hex() if ping_response else 'None'}")
    print(f"   {'✅ Auto-response generado' if ping_response else '❌ No response'}")
    
    # Test con 0x0B/0x8C
    request_8c = bytes.fromhex('000a000b0a8c000000000013a64b34a1017401ca9ddc')
    response_8c = proxy.build_auto_response(request_8c)
    
    print(f"\n🔧 Request 0x0B/0x8C procesado:")
    print(f"   Response generado: {'Sí' if response_8c else 'No'} ({len(response_8c) if response_8c else 0} bytes)")
    
    # Test con comando que NO debe responder
    non_critical = bytes.fromhex('00400001003c000000000002')
    response_none = proxy.build_auto_response(non_critical)
    
    print(f"\n❓ Request no-crítico (0x01/0x3C - auth):")
    print(f"   Response generado: {'Sí' if response_none else 'No (correcto)'}")
    
    # Validaciones
    checks = {
        'Ping genera response': ping_response is not None,
        'Ping response tiene 20 bytes': ping_response and len(ping_response) == 20,
        '0x0B/0x8C genera response': response_8c is not None,
        '0x0B/0x8C response tiene 12 bytes': response_8c and len(response_8c) == 12,
        'Comando no-crítico NO genera response': response_none is None
    }
    
    print("\n🔍 Validaciones:")
    all_pass = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check}")
        if not result:
            all_pass = False
    
    print("\n" + "="*70)
    if all_pass:
        print("✅ TEST PASADO - Auto-responder lógica correcta")
    else:
        print("❌ TEST FALLIDO")
    print("="*70)
    
    return all_pass


if __name__ == '__main__':
    print("\n" + "🧪 "+"="*68)
    print("   SUITE DE TESTS: Auto-Responder Keep-Alive")
    print("="*70 + "\n")
    
    results = []
    
    results.append(('Ping Response Builder', test_ping_response()))
    results.append(('Empty Response Builder', test_empty_response()))
    results.append(('Header Parser', test_header_parser()))
    results.append(('Auto-Responder Logic', test_auto_responder_logic()))
    
    # Resumen
    print("\n\n" + "="*70)
    print("📊 RESUMEN DE TESTS")
    print("="*70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "="*70)
    if all_passed:
        print("🎉 TODOS LOS TESTS PASARON")
        print("   El auto-responder está listo para usar")
    else:
        print("⚠️  ALGUNOS TESTS FALLARON")
        print("   Revisar implementación")
    print("="*70 + "\n")
    
    sys.exit(0 if all_passed else 1)

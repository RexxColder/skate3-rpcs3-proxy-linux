#!/usr/bin/env python3
"""
Herramienta para comparar paquetes capturados con las auditorías de Windows
"""

import sys
from pathlib import Path

def parse_hex_line(line: str) -> bytes:
    """Parsea una línea de hex a bytes"""
    hex_values = line.strip().split()
    return bytes(int(h, 16) for h in hex_values if len(h) == 2)

def compare_packets(linux_hex: str, windows_hex: str):
    """Compara dos paquetes en formato hex"""
    
    linux_bytes = parse_hex_line(linux_hex)
    windows_bytes = parse_hex_line(windows_hex)
    
    print("\n" + "="*70)
    print("COMPARACIÓN DE PAQUETES")
    print("="*70)
    
    print(f"\nLinux:   {len(linux_bytes)} bytes")
    print(f"Windows: {len(windows_bytes)} bytes")
    
    if len(linux_bytes) != len(windows_bytes):
        print(f"\n⚠️  DIFERENTE LONGITUD!")
    
    # Comparar byte por byte
    print("\nDiferencias byte por byte:")
    print("Offset  Linux    Windows  ASCII")
    print("-" * 40)
    
    max_len = max(len(linux_bytes), len(windows_bytes))
    differences = 0
    
    for i in range(max_len):
        l_byte = linux_bytes[i] if i < len(linux_bytes) else None
        w_byte = windows_bytes[i] if i < len(windows_bytes) else None
        
        if l_byte != w_byte:
            differences += 1
            l_str = f"{l_byte:02X}" if l_byte is not None else "--"
            w_str = f"{w_byte:02X}" if w_byte is not None else "--"
            l_chr = chr(l_byte) if l_byte and 32 <= l_byte <= 126 else "."
            w_chr = chr(w_byte) if w_byte and 32 <= w_byte <= 126 else "."
            
            print(f"{i:04X}    {l_str}       {w_str}      {l_chr} / {w_chr}")
    
    if differences == 0:
        print("✅ PAQUETES IDÉNTICOS!")
    else:
        print(f"\n❌ {differences} diferencias encontradas")
    
    # Analizar headers Blaze
    if len(linux_bytes) >= 12 and len(windows_bytes) >= 12:
        print("\n" + "="*70)
        print("ANÁLISIS DE HEADERS BLAZE")
        print("="*70)
        
        print("\n{:<20} {:<10} {:<10}".format("Campo", "Linux", "Windows"))
        print("-" * 40)
        
        # Length
        l_len = int.from_bytes(linux_bytes[0:2], 'big')
        w_len = int.from_bytes(windows_bytes[0:2], 'big')
        match = "✓" if l_len == w_len else "✗"
        print(f"{'Length':<20} {l_len:<10} {w_len:<10} {match}")
        
        # Component
        l_comp = linux_bytes[3]
        w_comp = windows_bytes[3]
        match = "✓" if l_comp == w_comp else "✗"
        print(f"{'Component':<20} 0x{l_comp:02X} ({l_comp:<3}) 0x{w_comp:02X} ({w_comp:<3}) {match}")
        
        # Command
        l_cmd = linux_bytes[5]
        w_cmd = windows_bytes[5]
        match = "✓" if l_cmd == w_cmd else "✗"
        print(f"{'Command':<20} 0x{l_cmd:02X} ({l_cmd:<3}) 0x{w_cmd:02X} ({w_cmd:<3}) {match}")
        
        # Error
        l_err = int.from_bytes(linux_bytes[6:8], 'big')
        w_err = int.from_bytes(windows_bytes[6:8], 'big')
        match = "✓" if l_err == w_err else "✗"
        print(f"{'Error':<20} {l_err:<10} {w_err:<10} {match}")
        
        # Msg Type
        l_type = int.from_bytes(linux_bytes[8:10], 'big')
        w_type = int.from_bytes(windows_bytes[8:10], 'big')
        match = "✓" if l_type == w_type else "✗"
        print(f"{'Msg Type':<20} {l_type:<10} {w_type:<10} {match}")
        
        # Msg ID
        l_id = int.from_bytes(linux_bytes[10:12], 'big')
        w_id = int.from_bytes(windows_bytes[10:12], 'big')
        match = "✓" if l_id == w_id else "✗"
        print(f"{'Msg ID':<20} {l_id:<10} {w_id:<10} {match}")

if __name__ == '__main__':
    print("\n🔬 Herramienta de Comparación de Paquetes")
    print("="*70)
    
    if len(sys.argv) < 3:
        print("\nUso:")
        print("  python3 compare_packets.py <hex_linux> <hex_windows>")
        print("\nEjemplo:")
        print("  python3 compare_packets.py \\")
        print('    "00 46 00 01 00 C8 00 00 00 00 00 02 ..." \\')
        print('    "00 46 00 01 00 C8 00 00 00 00 00 02 ..."')
        print("\nO pega cada hex en archivos y usa:")
        print("  python3 compare_packets.py @linux.hex @windows.hex")
        sys.exit(1)
    
    linux_hex = sys.argv[1]
    windows_hex = sys.argv[2]
    
    # Leer de archivo si empieza con @
    if linux_hex.startswith('@'):
        with open(linux_hex[1:], 'r') as f:
            linux_hex = ' '.join(f.read().split())
    
    if windows_hex.startswith('@'):
        with open(windows_hex[1:], 'r') as f:
            windows_hex = ' '.join(f.read().split())
    
    compare_packets(linux_hex, windows_hex)
    print()

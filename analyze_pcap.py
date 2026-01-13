#!/usr/bin/env python3
"""
Analizador de capturas pcapng del proxy de Skate 3
Extrae y analiza paquetes del protocolo EA Blaze
"""

import sys
from pathlib import Path

try:
    from scapy.all import rdpcap, TCP, Raw
except ImportError:
    print("ERROR: scapy no está instalado")
    print("Instalar con: pip install scapy")
    sys.exit(1)


def analyze_pcap(pcap_file):
    """Analiza archivo pcapng y extrae paquetes Blaze"""
    print(f"\n{'='*80}")
    print(f"Analizando: {pcap_file}")
    print(f"{'='*80}\n")
    
    packets = rdpcap(str(pcap_file))
    print(f"Total de paquetes capturados: {len(packets)}")
    
    # Filtrar paquetes TCP con datos
    tcp_packets = [p for p in packets if TCP in p and Raw in p]
    print(f"Paquetes TCP con datos: {len(tcp_packets)}")
    
    # Puertos relevantes: 42100 (redirector), 9999 (proxy), 10010 (EA server)
    relevant_ports = [42100, 9999, 10010]
    
    blaze_packets = []
    
    for i, pkt in enumerate(tcp_packets):
        sport = pkt[TCP].sport
        dport = pkt[TCP].dport
        
        if sport in relevant_ports or dport in relevant_ports:
            payload = bytes(pkt[Raw])
            
            # Los paquetes Blaze típicamente empiezan con ciertos patterns
            # Header de 12 bytes, primeros 2 bytes = length
            if len(payload) >= 12:
                blaze_packets.append({
                    'index': i,
                    'src': f"{pkt[0][1].src}:{sport}",
                    'dst': f"{pkt[0][1].dst}:{dport}",
                    'payload': payload,
                    'length': len(payload)
                })
    
    print(f"\nPaquetes Blaze encontrados: {len(blaze_packets)}\n")
    
    # Analizar cada paquete Blaze
    for i, pkt in enumerate(blaze_packets[:20]):  # Primeros 20 para no saturar
        print(f"\n--- Paquete #{i+1} ---")
        print(f"Fuente: {pkt['src']}")
        print(f"Destino: {pkt['dst']}")
        print(f"Tamaño: {pkt['length']} bytes")
        
        payload = pkt['payload']
        
        # Parsear header Blaze (12 bytes)
        if len(payload) >= 12:
            length = int.from_bytes(payload[0:2], 'big')
            component = payload[3]
            command = payload[5]
            error_code = int.from_bytes(payload[6:8], 'big')
            msg_type = int.from_bytes(payload[8:10], 'big')
            msg_id = int.from_bytes(payload[10:12], 'big')
            
            print(f"  Length: {length}")
            print(f"  Component: 0x{component:02X}")
            print(f"  Command: 0x{command:02X} ({command})")
            print(f"  Error: {error_code}")
            print(f"  MsgType: {msg_type}")
            print(f"  MsgID: {msg_id}")
            
            # Identificar tipo de paquete
            if component == 0x01 and command == 0xC8:  # Authentication Login
                print("  >>> AUTENTICACIÓN (Login Request)")
            elif component == 0x01 and command == 0x4C:  # Silent Login
                print("  >>> AUTENTICACIÓN (Silent Login)")
            elif component == 0x05:  # Redirector
                print("  >>> REDIRECTOR")
            
            # Mostrar hex dump del payload TDF
            if len(payload) > 12:
                tdf_data = payload[12:]
                print(f"\n  Payload TDF ({len(tdf_data)} bytes):")
                
                # Hex dump de los primeros 256 bytes
                for j in range(0, min(len(tdf_data), 256), 16):
                    hex_str = ' '.join(f'{b:02X}' for b in tdf_data[j:j+16])
                    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in tdf_data[j:j+16])
                    print(f"    {j:04X}: {hex_str:<48}  {ascii_str}")
                
                if len(tdf_data) > 256:
                    print(f"    ... ({len(tdf_data) - 256} bytes restantes)")
    
    return blaze_packets


def save_blaze_packets(blaze_packets, output_file):
    """Guarda paquetes Blaze en un archivo para análisis posterior"""
    import json
    
    export_data = []
    for pkt in blaze_packets:
        export_data.append({
            'src': pkt['src'],
            'dst': pkt['dst'],
            'length': pkt['length'],
            'hex': pkt['payload'].hex()
        })
    
    Path(output_file).write_text(json.dumps(export_data, indent=2))
    print(f"\n✅ Paquetes guardados en: {output_file}")


def main():
    pcap_files = [
        Path("/home/rexx/Escritorio/TEst/server test 1.pcapng"),
        Path("/home/rexx/Escritorio/TEst/server test 2.pcapng")
    ]
    
    all_packets = []
    
    for pcap_file in pcap_files:
        if pcap_file.exists():
            packets = analyze_pcap(pcap_file)
            all_packets.extend(packets)
        else:
            print(f"⚠️  Archivo no encontrado: {pcap_file}")
    
    # Guardar todos los paquetes
    if all_packets:
        output_dir = Path("/home/rexx/.gemini/antigravity/scratch/skate3-proxy-linux")
        save_blaze_packets(all_packets, output_dir / "blaze_packets_analysis.json")


if __name__ == '__main__':
    main()

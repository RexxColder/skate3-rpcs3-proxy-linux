#!/usr/bin/env python3
""" 
Análisis COMPLETO parseando HEX directamente del JSON
"""

import json
import struct

def parse_blaze_from_hex(hex_str):
    """Parsea hex string y extrae header Blaze"""
    try:
        data = bytes.fromhex(hex_str)
        if len(data) < 12:
            return None, data
        
        header = {
            'length': struct.unpack('>H', data[0:2])[0],
            'component': data[3],
            'command': data[5],
            'error': struct.unpack('>H', data[6:8])[0],
            'msg_type': struct.unpack('>H', data[8:10])[0],
            'msg_id': struct.unpack('>H', data[10:12])[0]
        }
        return header, data
    except:
        return None, None

def main():
    with open('blaze_packets_analysis.json', 'r') as f:
        packets = json.load(f)
    
    print(f"\n🔬 Analizand{len(packets)} paquetes de capturas Windows...")
    
    with open('COMPLETE_PROTOCOL_MAP.txt', 'w') as out:
        out.write("="*80 + "\n")
        out.write(f"MAPEO COMPLETO DEL PROTOCOLO - {len(packets)} PAQUETES\n")
        out.write("Análisis exhaustivo byte por byte hasta cierre de conexión\n")
        out.write("="*80 + "\n\n")
        
        comp_names = {
            0x01: "AUTHENTICATION", 0x02: "GAME_STATE", 0x04: "GAME_MANAGER",
            0x05: "REDIRECTOR", 0x07: "STATS", 0x09: "UTIL",
            0x0C: "USER_SESSIONS", 0x19: "SOCIAL"
        }
        
        request_map = {}
        stats = {}
        
        for i, pkt in enumerate(packets):
            src = pkt.get('src', '?')
            dst = pkt.get('dst', '?')
            hex_data = pkt.get('hex', '')
            
            header, data = parse_blaze_from_hex(hex_data)
            
            if not header:
                continue
            
            comp = header['component']
            cmd = header['command']
            
            # Stats
            key = (comp, cmd)
            stats[key] = stats.get(key, 0) + 1
            
            # Dirección
            direction = "GAME→EA" if "159.153" in dst else "EA→GAME" if "159.153" in src else "LOCAL"
            
            # Escribir paquete
            out.write(f"\n{'='*80}\n")
            out.write(f"PAQUETE #{i} - {direction}\n")
            out.write(f"{'='*80}\n")
            out.write(f"Src: {src}\n")
            out.write(f"Dst: {dst}\n")
            out.write(f"Component: 0x{comp:02X} ({comp}) [{comp_names.get(comp, 'UNKNOWN')}]\n")
            out.write(f"Command:   0x{cmd:02X} ({cmd})\n")
            
            msg_type_name = {0: "REQUEST", 4096: "RESPONSE", 8192: "NOTIFICATION"}.get(header['msg_type'], "OTHER")
            out.write(f"Msg Type:  {header['msg_type']} [{msg_type_name}]\n")
            out.write(f"Msg ID:    {header['msg_id']}\n")
            out.write(f"Error:     {header['error']}\n")
            out.write(f"Length:    {len(data)} bytes total ({header['length']} payload)\n")
            
            # Hex dump (primeros 256 bytes)
            preview = data[:256]
            out.write(f"\nHEX DUMP:\n")
            for j in range(0, len(preview), 16):
                hex_line = ' '.join(f'{b:02X}' for b in preview[j:j+16])
                ascii_line = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in preview[j:j+16])
                out.write(f"  {j:04X}: {hex_line:<48} {ascii_line}\n")
            if len(data) > 256:
                out.write(f"  ... ({len(data) - 256} bytes más)\n")
            
            # Request/Response mapping
            if header['msg_type'] == 0:  # REQUEST
                request_map[header['msg_id']] = (i, comp, cmd, len(data))
                out.write(f"\n⏱️  REQUEST - Esperando response (MsgID={header['msg_id']})\n")
            elif header['msg_type'] in [4096, 8192]:
                if header['msg_id'] in request_map:
                    req_i, req_c, req_cmd, req_len = request_map[header['msg_id']]
                    out.write(f"\n✅ RESPONSE para paquete #{req_i}\n")
                    out.write(f"   Request: 0x{req_c:02X}/0x{req_cmd:02X} ({req_len}b)\n")
                    out.write(f"   Latencia: {i - req_i} paquetes\n")
                    out.write(f"   Error: {header['error']}\n")
                    del request_map[header['msg_id']]
        
        # RESUMEN
        out.write(f"\n\n{'='*80}\n")
        out.write("RESUMEN ESTADÍSTICO\n")
        out.write(f"{'='*80}\n\n")
        
        out.write("COMANDOS ÚNICOS Y FRECUENCIA:\n")
        for (comp, cmd), count in sorted(stats.items(), key=lambda x: (-x[1], x[0])):
            name = comp_names.get(comp, "UNKNOWN")
            out.write(f"  0x{comp:02X}/0x{cmd:02X} [{name:15s}] Cmd {cmd:3d}: {count:3d} veces\n")
        
        out.write(f"\n\nREQUESTS SIN RESPUESTA ({len(request_map)}):\n")
        for msg_id, (pkt_i, comp, cmd, length) in sorted(request_map.items()):
            out.write(f"  Pkt #{pkt_i}: 0x{comp:02X}/0x{cmd:02X}, MsgID={msg_id} ({length}b)\n")
    
    print(f"✅ Análisis completo: COMPLETE_PROTOCOL_MAP.txt")
    print(f"   {len(packets)} paquetes, {len(stats)} comandos únicos")

if __name__ == '__main__':
    main()

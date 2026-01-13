#!/usr/bin/env python3
"""
Análisis de paquetes POST-AUTENTICACIÓN
Identifica keep-alive, pings y parches anti-desync
"""

import json
import sys
from collections import defaultdict

def analyze_post_auth_packets(json_file):
    """Analiza paquetes después de la autenticación"""
    
    with open(json_file, 'r') as f:
        packets = json.load(f)
    
    # Encontrar paquete de autenticación
    auth_index = None
    for i, pkt in enumerate(packets):
        if pkt.get('component') == 1 and pkt.get('command') in [60, 200]:
            auth_index = i
            print(f"✅ Autenticación encontrada en paquete #{i}")
            break
    
    if auth_index is None:
        print("❌ No se encontró paquete de autenticación")
        return
    
    # Analizar paquetes posteriores
    print(f"\n{'='*80}")
    print(f"PAQUETES POST-AUTENTICACIÓN (después del #{auth_index})")
    print(f"{'='*80}\n")
    
    # Estadísticas
    component_stats = defaultdict(int)
    command_stats = defaultdict(lambda: defaultdict(int))
    
    # Analizar primeros 50 paquetes post-auth
    post_auth = packets[auth_index+1:auth_index+51]
    
    for i, pkt in enumerate(post_auth, start=1):
        comp = pkt.get('component', '?')
        cmd = pkt.get('command', '?')
        direction = pkt.get('direction', '?')
        length = pkt.get('length', 0)
        msg_type = pkt.get('msg_type', 0)
        
        component_stats[comp] += 1
        command_stats[comp][cmd] += 1
        
        # Mostrar paquetes relevantes
        if i <= 20:  # Primeros 20
            msg_type_str = "REQ" if msg_type == 0 else "RESP"
            print(f"Pkt #{i:2d} | {direction:4s} | Comp: 0x{comp:02X} | "
                  f"Cmd: 0x{cmd:02X} ({cmd:3d}) | {msg_type_str:4s} | "
                  f"{length:4d} bytes")
    
    # Resumen de componentes
    print(f"\n{'='*80}")
    print("ESTADÍSTICAS DE COMPONENTES")
    print(f"{'='*80}\n")
    
    for comp in sorted(component_stats.keys()):
        count = component_stats[comp]
        print(f"Component 0x{comp:02X}: {count} paquetes")
        
        # Comandos de este componente
        for cmd in sorted(command_stats[comp].keys()):
            cmd_count = command_stats[comp][cmd]
            print(f"  → Command 0x{cmd:02X} ({cmd:3d}): {cmd_count} veces")
    
    # Buscar patrones de keep-alive
    print(f"\n{'='*80}")
    print("PATRONES IDENTIFICADOS")
    print(f"{'='*80}\n")
    
    # Buscar pings (component 0x09, command 0x02 típicamente)
    pings = [p for p in post_auth if p.get('component') == 9 and p.get('command') == 2]
    print(f"🔔 Pings (Comp 0x09, Cmd 0x02): {len(pings)} encontrados")
    
    # Buscar component 0x02 (típicamente game state)
    game_state = [p for p in post_auth if p.get('component') == 2]
    print(f"🎮 Game State (Comp 0x02): {len(game_state)} paquetes")
    
    # Buscar command 0x14 (parches anti-desync)
    desync_patches = [p for p in post_auth if p.get('command') == 0x14]
    print(f"🔧 Potenciales anti-desync (Cmd 0x14): {len(desync_patches)} paquetes")
    
    return post_auth

if __name__ == '__main__':
    json_file = 'blaze_packets_analysis.json'
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    
    print(f"\n🔬 Analizando post-autenticación en: {json_file}\n")
    analyze_post_auth_packets(json_file)

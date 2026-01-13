#!/usr/bin/env python3
"""
RPCS3 Memory Patcher
Apply memory patches to RPCS3 process
Based on Form1.cs memory patching logic
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from .scanner import RPCS3MemoryScanner

logger = logging.getLogger(__name__)


@dataclass
class MemoryPatch:
    """Representa un patch de memoria"""
    name: str
    pattern: bytes  # Patrón para encontrar la ubicación
    patch_data: bytes  # Datos a escribir
    offset: int = 0  # Offset desde donde se encuentra el patrón
    applied_address: Optional[int] = None  # Dirección donde se aplicó


class RPCS3MemoryPatcher:
    """
    Aplica parches de memoria a RPCS3.
    Basado en los parches de Form1.cs para Game Speed y Debug Cam.
    """
    
    def __init__(self, scanner: RPCS3MemoryScanner):
        self.scanner = scanner
        self.patches: Dict[str, MemoryPatch] = {}
        self._init_patches()
    
    def _init_patches(self):
        """
        Inicializa los parches conocidos.
        Basados en los strings descifrados y código de Form1.cs.
        """
        
        # Patch de velocidad del juego 1 - NOPs
        # Del string descifrado: "90 90 90 90 90 90 90"
        self.patches['game_speed_1'] = MemoryPatch(
            name="Game  Speed Function 1",
            pattern=bytes([0x90] * 7),  # 7 NOPs
            patch_data=bytes([0x90] * 7),
            offset=0
        )
        
        # Patch de velocidad del juego 2
        # "49 0F 38 F1 44 1E 08 44 89 85 74 04 00 00"
        self.patches['game_speed_2'] = MemoryPatch(
            name="Game Speed Function 2",
            pattern=bytes.fromhex("49 0F 38 F1 44 1E 08 44 89 85 74 04 00 00"),
            patch_data=bytes.fromhex("49 0F 38 F1 44 1E 08 44 89 85 74 04 00 00"),
            offset=0
        )
        
        # Patch de velocidad del juego 3
        # "49 0F 38 F1 44 1E 10 48 83 C4 28"
        self.patches['game_speed_3'] = MemoryPatch(
            name="Game Speed Function 3",
            pattern=bytes.fromhex("49 0F 38 F1 44 1E 10 48 83 C4 28"),
            patch_data=bytes.fromhex("49 0F 38 F1 44 1E 10 48 83 C4 28"),
            offset=0
        )
        
        # Patch de velocidad del juego 4
        # "49 89 44 1E 10 48 83 C4 28 E9 22 00 00 00"
        self.patches['game_speed_4'] = MemoryPatch(
            name="Game Speed Function 4",
            pattern=bytes.fromhex("49 89 44 1E 10 48 83 C4 28 E9 22 00 00 00"),
            patch_data=bytes.fromhex("49 89 44 1E 10 48 83 C4 28 E9 22 00 00 00"),
            offset=0
        )
        
        # Verificación de EBOOT stock
        # Patrón: bytes ([0x60, 0x00, 0x00, 0x00])
        self.patches['eboot_check'] = MemoryPatch(
            name="EBOOT Verification",
            pattern=bytes([0x60, 0x00, 0x00, 0x00]),
            patch_data=bytes([0x60, 0x00, 0x00, 0x00]),  # No modificar, solo verificar
            offset=0
        )
    
    def find_patch_location(self, patch_name: str) -> Optional[int]:
        """
        Encuentra la ubicación de un patch en memoria.
        
        Args:
            patch_name: Nombre del patch
            
        Returns:
            Dirección de memoria o None
        """
        if patch_name not in self.patches:
            logger.error(f"Patch desconocido: {patch_name}")
            return None
        
        patch = self.patches[patch_name]
        
        logger.info(f"Buscando ubicación para patch: {patch.name}")
        addresses = self.scanner.find_pattern(patch.pattern, max_results=1)
        
        if not addresses:
            logger.warning(f"No se encontró ubicación para: {patch.name}")
            return None
        
        address = addresses[0] + patch.offset
        logger.info(f"Patch {patch.name} encontrado en: {address:016X}")
        return address
    
    def apply_patch(self, patch_name: str) -> bool:
        """
        Aplica un patch específico.
        
        Args:
            patch_name: Nombre del patch
            
        Returns:
            True si exitoso
        """
        if patch_name not in self.patches:
            logger.error(f"Patch desconocido: {patch_name}")
            return False
        
        patch = self.patches[patch_name]
        
        # Encontrar ubicación
        address = self.find_patch_location(patch_name)
        if not address:
            return False
        
        # Aplicar patch
        success = self.scanner.write_memory(address, patch.patch_data)
        
        if success:
            patch.applied_address = address
            logger.info(f"✅ Patch {patch.name} aplicado en {address:016X}")
        else:
            logger.error(f"❌ Error aplicando patch {patch.name}")
        
        return success
    
    def verify_eboot(self) -> bool:
        """
        Verifica que el EBOOT sea el stock (sin modificar).
        Basado en Form1.cs líneas relacionadas con verificación.
        
        Returns:
            True si es EBOOT stock
        """
        logger.info("Verificando EBOOT...")
        
        address = self.find_patch_location('eboot_check')
        
        if address:
            logger.info("✅ EBOOT stock verificado")
            return True
        else:
            logger.warning("⚠️  EBOOT no es stock o no se pudo verificar")
            logger.warning("Pueden ocurrir problemas de desincronización")
            return False
    
    def apply_all_game_speed_patches(self) -> int:
        """
        Aplica todos los parches de velocidad del juego.
        
        Returns:
            Cantidad de parches aplicados exitosamente
        """
        logger.info("Aplicando parches de velocidad de juego...")
        
        applied = 0
        for patch_name in ['game_speed_1', 'game_speed_2', 'game_speed_3', 'game_speed_4']:
            if self.apply_patch(patch_name):
                applied += 1
        
        logger.info(f"Aplicados {applied}/4 parches de velocidad")
        return applied
    
    def get_patch_status(self) -> Dict[str, bool]:
        """
        Obtiene el estado de todos los parches.
        
        Returns:
            Dict con nombre de patch y si está aplicado
        """
        status = {}
        for name, patch in self.patches.items():
            status[name] = patch.applied_address is not None
        return status


if __name__ == '__main__':
    # Test del patcher
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        print("Conectando a RPCS3...")
        scanner = RPCS3MemoryScanner()
        patcher = RPCS3MemoryPatcher(scanner)
        
        print(f"\nConectado a RPCS3 PID {scanner.pid}")
        print("\nParches disponibles:")
        for name, patch in patcher.patches.items():
            print(f"  - {patch.name} ({name})")
        
        # Verificar EBOOT
        print("\nVerificando EBOOT...")
        is_stock = patcher.verify_eboot()
        
        if is_stock:
            print("✅ EBOOT stock detectado")
        else:
            print("⚠️  EBOOT modificado o no detectado")
        
        # Intentar aplicar parches (COMENTADO para seguridad)
        # print("\nAplicando parches...")
        # patcher.apply_all_game_speed_patches()
        
        print("\n⚠️  Para aplicar parches, descomenta las líneas en el código")
        print("   y asegúrate de tener permisos adecuados")
        
    except RuntimeError as e:
        print(f"Error: {e}")

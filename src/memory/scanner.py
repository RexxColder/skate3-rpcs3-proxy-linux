#!/usr/bin/env python3
"""
RPCS3 Memory Scanner
Read and search memory of RPCS3 process in Linux
Based on Form1.cs memory manipulation code
"""

import logging
import re
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MemoryRegion:
    """Representa una región de memoria del proceso"""
    start: int
    end: int
    permissions: str
    pathname: str


class RPCS3MemoryScanner:
    """
    Scanner de memoria para procesos RPCS3.
    Implementa lectura de /proc/pid/mem y búsqueda de patrones.
    """
    
    def __init__(self, pid: Optional[int] = None):
        """
        Args:
            pid: Process ID de RPCS3. Si es None, intenta encontrarlo.
        """
        self.pid = pid or self._find_rpcs3_pid()
        if not self.pid:
            raise RuntimeError("No se encontró proceso RPCS3")
        
        self.maps_file = Path(f'/proc/{self.pid}/maps')
        self.mem_file = Path(f'/proc/{self.pid}/mem')
        
        if not self.maps_file.exists():
            raise RuntimeError(f"Proceso {self.pid} no existe")
        
        logger.info(f"Scanner inicializado para RPCS3 PID {self.pid}")
    
    @staticmethod
    def _find_rpcs3_pid() -> Optional[int]:
        """Busca el PID del proceso RPCS3 (nativo o AppImage)"""
        try:
            import subprocess
            
            # Intentar buscar por nombre exacto primero (binario nativo)
            result = subprocess.run(
                ['pgrep', '-x', 'rpcs3'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                pid = int(result.stdout.strip().split('\n')[0])
                logger.info(f"RPCS3 encontrado (nativo) con PID {pid}")
                return pid
            
            # Si no se encuentra, buscar por patrón (incluye AppImages)
            # Buscar cualquier proceso que contenga "rpcs" (case-insensitive)
            result = subprocess.run(
                ['pgrep', '-i', '-f', 'rpcs'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                # Verificar cada PID para encontrar el verdadero RPCS3
                pids = result.stdout.strip().split('\n')
                for pid_str in pids:
                    try:
                        pid = int(pid_str)
                        # Leer comm (nombre del proceso) para verificar
                        with open(f'/proc/{pid}/comm', 'r') as f:
                            comm = f.read().strip().lower()
                            # Buscar "rpcs" en el nombre del proceso
                            if 'rpcs' in comm:
                                logger.info(f"RPCS3 encontrado ({comm}) con PID {pid}")
                                return pid
                    except (ValueError, FileNotFoundError, PermissionError):
                        continue
                    
        except Exception as e:
            logger.warning(f"Error buscando RPCS3: {e}")
        return None
    
    def get_memory_regions(self, writable_only: bool = True) -> List[MemoryRegion]:
        """
        Lee las regiones de memoria desde /proc/pid/maps
        
        Args:
            writable_only: Si True, solo regiones escribibles
            
        Returns:
            Lista de regiones de memoria
        """
        regions = []
        
        try:
            with open(self.maps_file, 'r') as f:
                for line in f:
                    # Formato: address perms offset dev inode pathname
                    # Ejemplo: 7fff-8000 rw-p 00000 00:00 0 [stack]
                    parts = line.split()
                    if len(parts) < 2:
                        continue
                    
                    addr_range = parts[0].split('-')
                    perms = parts[1]
                    pathname = parts[-1] if len(parts) >= 6 else ""
                    
                    # Filtrar regiones según permisos
                    if writable_only and 'w' not in perms:
                        continue
                    
                    start = int(addr_range[0], 16)
                    end = int(addr_range[1], 16)
                    
                    regions.append(MemoryRegion(start, end, perms, pathname))
            
            logger.debug(f"Encontradas {len(regions)} regiones de memoria")
            return regions
            
        except Exception as e:
            logger.error(f"Error leyendo /proc/maps: {e}")
            return []
    
    def read_memory(self, address: int, length: int) -> Optional[bytes]:
        """
        Lee bytes desde una dirección de memoria.
        
        Args:
            address: Dirección de memoria
            length: Cantidad de bytes a leer
            
        Returns:
            Bytes leídos o None si falla
        """
        try:
            with open(self.mem_file, 'rb') as mem:
                mem.seek(address)
                data = mem.read(length)
                return data
        except (OSError, PermissionError) as e:
            logger.warning(f"Error leyendo memoria en {address:016X}: {e}")
            return None
    
    def write_memory(self, address: int, data: bytes) -> bool:
        """
        Escribe bytes en una dirección de memoria.
        
        Args:
            address: Dirección de memoria
            data: Bytes a escribir
            
        Returns:
            True si exitoso, False si falla
        """
        try:
            with open(self.mem_file, 'r+b') as mem:
                mem.seek(address)
                mem.write(data)
                logger.info(f"Escritos {len(data)} bytes en {address:016X}")
                return True
        except (OSError, PermissionError) as e:
            logger.error(f"Error escribiendo memoria en {address:016X}: {e}")
            return False
    
    def find_pattern(
        self,
        pattern: bytes,
        wildcard: int = -1,
        writable_only: bool = True,
        max_results: int = 10
    ) -> List[int]:
        """
        Busca un patrón de bytes en la memoria del proceso.
        Similar a la búsqueda en Form1.cs.
        
        Args:
            pattern: Patrón de bytes a buscar
            wildcard: Valor que representa "cualquier byte" (-1 por defecto)
            writable_only: Solo buscar en regiones escribibles
            max_results: Máximo de resultados a retornar
            
        Returns:
            Lista de direcciones donde se encontró el patrón
        """
        results = []
        regions = self.get_memory_regions(writable_only=writable_only)
        
        logger.info(f"Buscando patrón de {len(pattern)} bytes en {len(regions)} regiones")
        
        for region in regions:
            if len(results) >= max_results:
                break
            
            # Leer región completa
            region_size = region.end - region.start
            
            # Limitar tamaño para evitar out of memory
            if region_size > 100 * 1024 * 1024:  # 100 MB max
                logger.debug(f"Saltando región grande: {region_size / 1024 / 1024:.1f} MB")
                continue
            
            data = self.read_memory(region.start, region_size)
            if not data:
                continue
            
            # Buscar patrón con wildcards
            for i in range(len(data) - len(pattern) + 1):
                match = True
                for j, byte in enumerate(pattern):
                    if byte != wildcard and data[i + j] != byte:
                        match = False
                        break
                
                if match:
                    address = region.start + i
                    results.append(address)
                    logger.debug(f"Patrón encontrado en {address:016X}")
                    
                    if len(results) >= max_results:
                        break
        
        logger.info(f"Patrón encontrado en {len(results)} ubicaciones")
        return results
    
    def find_pattern_from_hex(self, hex_pattern: str, **kwargs) -> List[int]:
        """
        Busca un patrón especificado como string hexadecimal.
        Soporta wildcards con '??'.
        
        Args:
            hex_pattern: Patrón en hex, ej: "90 90 90 90 ?? 90"
            **kwargs: Argumentos para find_pattern
            
        Returns:
            Lista de direcciones
        """
        # Parsear patrón hex
        parts = hex_pattern.replace(',', ' ').split()
        pattern = []
        
        for part in parts:
            if part == '??' or part == '?':
                pattern.append(-1)  # Wildcard
            else:
                try:
                    pattern.append(int(part, 16))
                except ValueError:
                    logger.error(f"Valor hex inválido: {part}")
                    return []
        
        return self.find_pattern(bytes(b if b != -1 else 0 for b in pattern), wildcard=-1, **kwargs)


if __name__ == '__main__':
    # Test del scanner
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        print("Intentando conectar a RPCS3...")
        scanner = RPCS3MemoryScanner()
        
        print(f"\nConectado a RPCS3 PID {scanner.pid}")
        
        regions = scanner.get_memory_regions(writable_only=False)
        print(f"Regiones de memoria: {len(regions)}")
        
        # Mostrar algunas regiones
        print("\nPrimeras 10 regiones:")
        for region in regions[:10]:
            size_mb = (region.end - region.start) / 1024 / 1024
            print(f"  {region.start:016X}-{region.end:016X} {region.permissions} "
                  f"{size_mb:8.2f} MB {region.pathname}")
        
        # Test de lectura
        if regions:
            test_addr = regions[0].start
            test_data = scanner.read_memory(test_addr, 16)
            if test_data:
                hex_str = ' '.join(f'{b:02X}' for b in test_data)
                print(f"\nTest de lectura en {test_addr:016X}:")
                print(f"  {hex_str}")
        
    except RuntimeError as e:
        print(f"Error: {e}")
        print("\nAsegúrate de:")
        print("  1. RPCS3 está corriendo")
        print("  2. Tienes permisos para leer /proc/pid/mem")
        print("  3. ptrace_scope permite acceso (ver NEXT_STEPS.md)")

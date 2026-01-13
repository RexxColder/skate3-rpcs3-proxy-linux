#!/usr/bin/env python3
"""
Update Manager
Auto-update functionality and username downloading
Based on Form1.cs update logic
"""

import logging
import requests
from typing import Optional, Dict
from packaging import version

logger = logging.getLogger(__name__)


class UpdateManager:
    """
    Gestiona actualizaciones y descarga de recursos remotos.
    URLs basadas en strings descifrados del código original.
    """
    
    VERSION = '1.0.3'
    
    # URLs desde GitHub (strings descifrados)
    VERSION_URL = 'https://raw.githubusercontent.com/skate6743/skaterpcs3public/refs/heads/main/version.json'
    UPDATER_URL = 'https://raw.githubusercontent.com/skate6743/skaterpcs3public/refs/heads/main/updater.exe'
    USERNAMES_URL = 'https://raw.githubusercontent.com/skate6743/skaterpcs3public/refs/heads/main/usernames.json'
    
    def __init__(self, config_manager=None):
        """
        Args:
            config_manager: ConfigManager instance para descifrado AES
        """
        self.config_manager = config_manager
    
    def check_update(self) -> Optional[Dict]:
        """
        Verifica si hay actualizaciones disponibles.
        Basado en Form1.cs líneas 175-199
        
        Returns:
            Dict con info de actualización o None si está actualizado
        """
        try:
            logger.info("Verificando actualizaciones...")
            response = requests.get(self.VERSION_URL, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            remote_version = data.get('version', '0.0.0')
            
            logger.info(f"Versión local: {self.VERSION}, remota: {remote_version}")
            
            if version.parse(remote_version) > version.parse(self.VERSION):
                logger.info("¡Nueva versión disponible!")
                return data
            else:
                logger.info("Versión actual está actualizada")
                return None
                
        except Exception as e:
            logger.error(f"Error verificando actualizaciones: {e}")
            return None
    
    def download_usernames(self) -> Dict[str, str]:
        """
        Descarga diccionario de nombres de usuario para spoofing.
        Basado en Form1.cs líneas 284-288
        
        Returns:
            Diccionario de usernames o diccionario vacío si falla
        """
        try:
            logger.info("Descargando usernames...")
            response = requests.get(self.USERNAMES_URL, timeout=10)
            response.raise_for_status()
            
            usernames = response.json()
            logger.info(f"Descargados {len(usernames)} usernames")
            return usernames
            
        except Exception as e:
            logger.error(f"Error descargando usernames: {e}")
            return {}
    
    def decrypt_field_names(self, version_data: Dict) -> list:
        """
        Descifra nombres de campos desde version.json.
        Basado en Form1.cs línea 199
        
        Los nombres cifrados se descifran con AES y se separan por '|'
        Resultado esperado: ['MAIL', 'PASS', 'PNAM']
        
        Args:
            version_data: Dict desde version.json con campo 'test' cifrado
            
        Returns:
            Lista de nombres de campos
        """
        if not self.config_manager:
            logger.warning("No se puede descifrar sin ConfigManager")
            return ['MAIL', 'PASS', 'PNAM']  # Fallback conocido
        
        try:
            encrypted_test = version_data.get('test', '')
            if not encrypted_test:
                return ['MAIL', 'PASS', 'PNAM']
            
            decrypted = self.config_manager.decrypt_aes(encrypted_test)
            fields = decrypted.split('|')
            
            logger.info(f"Campos descifrados: {fields}")
            return fields
            
        except Exception as e:
            logger.error(f"Error descifrando campos: {e}")
            return ['MAIL', 'PASS', 'PNAM']


if __name__ == '__main__':
    # Test
    logging.basicConfig(level=logging.DEBUG)
    
    updater = UpdateManager()
    
    # Check update
    update_info = updater.check_update()
    if update_info:
        print(f"Nueva versión: {update_info}")
    
    # Download usernames
    usernames = updater.download_usernames()
    print(f"Usernames: {list(usernames.keys())[:5]}...")

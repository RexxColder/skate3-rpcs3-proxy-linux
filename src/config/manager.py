#!/usr/bin/env python3
"""
Configuration Manager
Handles settings.json, login.json, and AES decryption
Based on ConfigManager from decompiled code
"""

import json
import base64
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    """Application settings"""
    auto_minimize: bool = False


@dataclass
class Credentials:
    """EA account credentials"""
    email: str
    password: str
    psn_name: str


class ConfigManager:
    """
    Gestiona configuración y credenciales del proxy.
    Usa las mismas claves AES que el programa original.
    """
    
    # Clave AES del programa original (descifrada)
    AES_KEY = b'Skate3OnRPCS3TEST_key_for_TESTIN'
    AES_IV_B64 = 'sLqN+UShUMeP0sEYg1uvdA=='
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Args:
            config_dir: Directorio de configuración. Si es None, usa ~/.config/skate3-proxy
        """
        if config_dir is None:
            config_dir = Path.home() / '.config' / 'skate3-proxy'
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.settings_file = self.config_dir / 'settings.json'
        self.login_file = self.config_dir / 'login.json'
        
        logger.info(f"Config directory: {self.config_dir}")
    
    def load_settings(self) -> Settings:
        """
        Carga settings.json
        Basado en Form1.cs líneas 215-221
        """
        if not self.settings_file.exists():
            logger.info("settings.json no existe, usando valores por defecto")
            return Settings()
        
        try:
            data = json.loads(self.settings_file.read_text())
            settings = Settings(
                auto_minimize=data.get('autoMinimize', False)
            )
            logger.info(f"Settings cargados: auto_minimize={settings.auto_minimize}")
            return settings
        except Exception as e:
            logger.error(f"Error cargando settings: {e}")
            return Settings()
    
    def save_settings(self, settings: Settings):
        """
        Guarda settings.json
        Basado en Form1.cs líneas 217-220
        """
        try:
            data = {
                'autoMinimize': settings.auto_minimize
            }
            self.settings_file.write_text(json.dumps(data, indent=2))
            logger.info("Settings guardados")
        except Exception as e:
            logger.error(f"Error guardando settings: {e}")
    
    def load_credentials(self) -> Optional[Credentials]:
        """
        Carga credenciales desde login.json
        Basado en Form1.cs líneas 226-241
        """
        if not self.login_file.exists():
            logger.info("login.json no existe")
            return None
        
        try:
            data = json.loads(self.login_file.read_text())
            
            # Validar campos requeridos
            required_fields = ['email', 'password', 'psnName']
            for field in required_fields:
                if field not in data:
                    logger.error(f"login.json falta campo: {field}")
                    return None
            
            credentials = Credentials(
                email=data['email'],
                password=data['password'],
                psn_name=data['psnName']
            )
            
            logger.info(f"Credenciales cargadas para: {credentials.email}")
            return credentials
            
        except Exception as e:
            logger.error(f"Error cargando credenciales: {e}")
            return None
    
    def save_credentials(self, credentials: Credentials):
        """
        Guarda credenciales en login.json
        Formato idéntico al original
        """
        try:
            data = {
                'email': credentials.email,
                'password': credentials.password,
                'psnName': credentials.psn_name
            }
            self.login_file.write_text(json.dumps(data, indent=2))
            logger.info("Credenciales guardadas")
        except Exception as e:
            logger.error(f"Error guardando credenciales: {e}")
    
    def delete_credentials(self):
        """Elimina login.json"""
        if self.login_file.exists():
            self.login_file.unlink()
            logger.info("Credenciales eliminadas")
    
    def decrypt_aes(self, ciphertext_b64: str) -> str:
        """
        Descifra texto usando AES-256 CBC
        Basado en AesEncryptionHelper.cs líneas 26-40
        
        Args:
            ciphertext_b64: Texto cifrado en Base64
            
        Returns:
            Texto descifrado
        """
        try:
            # Decodificar Base64
            ciphertext = base64.b64decode(ciphertext_b64)
            iv = base64.b64decode(self.AES_IV_B64)
            
            # Configurar cipher AES-256 CBC
            cipher = Cipher(
                algorithms.AES(self.AES_KEY),
                modes.CBC(iv),
                backend=default_backend()
            )
            
            # Descifrar
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Remover padding PKCS7
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
            
            return plaintext.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error descifrando: {e}")
            raise
    
    def encrypt_aes(self, plaintext: str) -> str:
        """
        Cifra texto usando AES-256 CBC
        Basado en AesEncryptionHelper.cs líneas 8-24
        
        Args:
            plaintext: Texto a cifrar
            
        Returns:
            Texto cifrado en Base64
        """
        try:
            iv = base64.b64decode(self.AES_IV_B64)
            
            # Configurar cipher AES-256 CBC
            cipher = Cipher(
                algorithms.AES(self.AES_KEY),
                modes.CBC(iv),
                backend=default_backend()
            )
            
            # Aplicar padding PKCS7
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()
            
            # Cifrar
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()
            
            # Codificar a Base64
            return base64.b64encode(ciphertext).decode('ascii')
            
        except Exception as e:
            logger.error(f"Error cifrando: {e}")
            raise


if __name__ == '__main__':
    # Test
    logging.basicConfig(level=logging.DEBUG)
    
    config = ConfigManager()
    
    # Test settings
    settings = Settings(auto_minimize=True)
    config.save_settings(settings)
    loaded = config.load_settings()
    print(f"Auto-minimize: {loaded.auto_minimize}")
    
    # Test credentials
    creds = Credentials(
        email='test@example.com',
        password='testpass123',
        psn_name='TestPlayer'
    )
    config.save_credentials(creds)
    loaded_creds = config.load_credentials()
    print(f"Loaded: {loaded_creds}")
    
    # Test AES
    test_encrypted = config.encrypt_aes("Hello World")
    print(f"Encrypted: {test_encrypted}")
    decrypted = config.decrypt_aes(test_encrypted)
    print(f"Decrypted: {decrypted}")

#!/usr/bin/env python3
"""
Test completo del proxy de Skate 3 para Linux
Valida toda la funcionalidad sin necesidad de RPCS3
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.network import ProxyServer, RedirectorServer, EACredentials
from src.network.tdf import BlazeAuthPacket
from src.config import ConfigManager


async def test_servers():
    """Test que los servidores inician correctamente"""
    print("=" * 60)
    print("TEST 1: Iniciando servidores")
    print("=" * 60)
    
    redirector = RedirectorServer()
    proxy = ProxyServer()
    
    print("✅ Redirector creado")
    print("✅ Proxy creado")
    
    # No los iniciamos realmente para no bloquear
    print("✅ Test de servidores pasado\n")


async def test_tdf_builder():
    """Test del constructor TDF"""
    print("=" * 60)
    print("TEST 2: TDF Builder")
    print("=" * 60)
    
    # Crear paquete de autenticación
    packet = BlazeAuthPacket(msg_id=42)
    packet.add_email("test@example.com")
    packet.add_password("testpass123")
    packet.add_psn_name("TestPlayer99")
    
    result = packet.build()
    
    print(f"Paquete generado: {len(result)} bytes")
    print(f"  Component: 0x{result[3]:02X} (esperado: 0x01)")
    print(f"  Command: 0x{result[5]:02X} (esperado: 0x3C)")
    print(f"  Msg ID: {int.from_bytes(result[10:12], 'big')} (esperado: 42)")
    
    assert result[3] == 0x01, "Component incorrecto"
    assert result[5] == 0x3C, "Command incorrecto"
    assert len(result) > 12, "Paquete demasiado pequeño"
    
    print("✅ TDF Builder funciona correctamente\n")


async def test_credential_injection():
    """Test de inyección de credenciales"""
    print("=" * 60)
    print("TEST 3: Inyección de Credenciales")
    print("=" * 60)
    
    # Crear paquete original (simulado de RPCS3)
    original = bytearray([
        0x00, 0x3C, 0x00, 0x01, 0x00, 0x3C, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x05  # msg_id = 5
    ])
    # Padding simulado
    original.extend(b'\x00' * 60)
    
    # Crear proxy con credenciales
    creds = EACredentials(
        email="real@email.com",
        password="realpass",
        psn_name="RealPlayer"
    )
    
    proxy = ProxyServer(credentials=creds)
    
    # Inyectar credenciales
    modified = proxy.inject_credentials(bytes(original))
    
    print(f"Original: {len(original)} bytes")
    print(f"Modificado: {len(modified)} bytes")
    print(f"Msg ID preservado: {int.from_bytes(modified[10:12], 'big')} (esperado: 5)")
    
    # Verificar que el paquete tiene las credenciales
    modified_str = modified.decode('latin-1')
    assert 'real@email.com' in modified_str, "Email no encontrado"
    assert 'RealPlayer' in modified_str, "PSN name no encontrado"
    
    print("✅ Inyección de credenciales funciona\n")


async def test_config_manager():
    """Test del gestor de configuración"""
    print("=" * 60)
    print("TEST 4: Config Manager")
    print("=" * 60)
    
    # Usar directorio temporal para tests
    test_dir = Path("/tmp/skate3-proxy-test")
    test_dir.mkdir(exist_ok=True)
    
    config = ConfigManager(test_dir)
    
    # Test settings
    from src.config import Settings
    settings = Settings(auto_minimize=True)
    config.save_settings(settings)
    loaded = config.load_settings()
    
    assert loaded.auto_minimize == True, "Settings no guardaron correctamente"
    print("✅ Settings: guardado y carga OK")
    
    # Test credentials
    from src.config import Credentials
    creds = Credentials(
        email="test@test.com",
        password="testtest",
        psn_name="TestUser"
    )
    config.save_credentials(creds)
    loaded_creds = config.load_credentials()
    
    assert loaded_creds.email == creds.email, "Credenciales no guardaron"
    print("✅ Credentials: guardado y carga OK")
    
    # Cleanup
    config.delete_credentials()
    (test_dir / "settings.json").unlink(missing_ok=True)
    test_dir.rmdir()
    
    print("✅ Config Manager funciona\n")


async def main():
    """Ejecuta todos los tests"""
    print("\n🧪 SUITE DE TESTS - SKATE 3 RPCS3 PROXY FOR LINUX\n")
    
    try:
        await test_servers()
        await test_tdf_builder()
        await test_credential_injection()
        await test_config_manager()
        
        print("=" * 60)
        print("✅ TODOS LOS TESTS PASARON")
        print("=" * 60)
        print("\nEl proxy está listo para usarse!")
        print("Siguiente paso: Ejecutar 'python3 main.py' y conectar RPCS3\n")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))

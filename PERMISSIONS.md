# 🛡️ Permisos para Manipulación de Memoria en Linux

La manipulación de memoria de RPCS3 requiere permisos especiales en Linux. Aquí están las opciones:

## Opción 1: Modificar ptrace_scope (Más Simple)

```bash
# Ver configuración actual
cat /proc/sys/kernel/yama/ptrace_scope

# Temporalmente (hasta reinicio)
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope

# Permanentemente
echo "kernel.yama.ptrace_scope = 0" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

**Valores de ptrace_scope:**
- `0` = Permitir ptrace a cualquier proceso (menos seguro)
- `1` = Permitir solo a procesos padre-hijo (por defecto)
- `2` = Solo admin puede hacer ptrace
- `3` = Ptrace completamente deshabilitado

## Opción 2: Usar Capabilities (Más Seguro)

```bash
# Dar capability específica al script Python
sudo setcap cap_sys_ptrace=eip /usr/bin/python3

# O solo al proxy
sudo setcap cap_sys_ptrace=eip /ruta/al/main.py
```

## Opción 3: Ejecutar como Root (Menos Recomendado)

```bash
sudo python3 main.py
```

## Verificar Permisos

```bash
# Ver capabilities actuales
getcap /usr/bin/python3

# Test rápido
python3 -c "import os; print(open(f'/proc/{os.getpid()}/mem', 'rb'))"
```

## Nota de Seguridad

⚠️ **Modificar ptrace_scope afecta la seguridad del sistema**.

Solo hazlo si:
- comprendes los riesgos
- estás en un entorno de confianza
- no ejecutas software no confiable

El proxy **funciona sin permisos de memoria**, simplemente no podrá aplicar parches opcionales de desincronización.

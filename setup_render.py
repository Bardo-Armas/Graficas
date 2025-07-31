#!/usr/bin/env python3
"""
Script de configuración automática para Render
"""
import os
import subprocess
import sys

def install_system_packages():
    """Instalar paquetes del sistema si es posible"""
    try:
        print("🔧 Intentando instalar paquetes del sistema...")
        
        # Comandos para instalar FreeTDS
        commands = [
            "apt-get update",
            "apt-get install -y unixodbc-dev freetds-dev freetds-bin"
        ]
        
        for cmd in commands:
            try:
                result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    print(f"✅ {cmd}")
                else:
                    print(f"⚠️ {cmd} - {result.stderr}")
            except subprocess.TimeoutExpired:
                print(f"⚠️ {cmd} - Timeout")
            except Exception as e:
                print(f"⚠️ {cmd} - Error: {e}")
                
    except Exception as e:
        print(f"⚠️ No se pudieron instalar paquetes del sistema: {e}")

def configure_odbc():
    """Configurar ODBC si es posible"""
    try:
        odbcinst_content = """[FreeTDS]
Description = FreeTDS Driver
Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so
FileUsage = 1
"""
        
        # Intentar escribir configuración ODBC
        odbc_paths = ['/etc/odbcinst.ini', './odbcinst.ini']
        
        for path in odbc_paths:
            try:
                with open(path, 'w') as f:
                    f.write(odbcinst_content)
                print(f"✅ Configuración ODBC creada en: {path}")
                os.environ['ODBCINST'] = path
                break
            except PermissionError:
                continue
                
    except Exception as e:
        print(f"⚠️ No se pudo configurar ODBC: {e}")

def main():
    print("🚀 Configurando entorno para Render...")
    
    # Instalar paquetes del sistema
    install_system_packages()
    
    # Configurar ODBC
    configure_odbc()
    
    # Verificar que pymssql esté disponible como fallback
    try:
        import pymssql
        print("✅ pymssql disponible como fallback")
    except ImportError:
        print("⚠️ pymssql no disponible - verificar requirements.txt")
    
    print("✅ Configuración completada")

if __name__ == "__main__":
    main()
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

print("=== DIAGNÓSTICO DE DRIVERS ODBC ===")
print()

# Verificar variables de entorno
print("Variables de entorno:")
print(f"DB_SERVER: {os.getenv('DB_SERVER')}")
print(f"DB_DATABASE: {os.getenv('DB_DATABASE')}")
print(f"DB_USERNAME: {os.getenv('DB_USERNAME')}")
print(f"DB_PASSWORD: {'***' if os.getenv('DB_PASSWORD') else 'NO CONFIGURADA'}")
print(f"DB_DRIVER: {os.getenv('DB_DRIVER')}")
print()

# Verificar drivers disponibles
print("Drivers ODBC disponibles en el sistema:")
drivers = pyodbc.drivers()
if drivers:
    for i, driver in enumerate(drivers, 1):
        print(f"{i}. {driver}")
else:
    print("❌ No se encontraron drivers ODBC instalados.")

print()

# Verificar drivers específicos
target_drivers = ['FreeTDS', 'ODBC Driver 17 for SQL Server', 'SQL Server']
print("Verificación de drivers específicos:")
for driver in target_drivers:
    status = "✅ DISPONIBLE" if driver in drivers else "❌ NO DISPONIBLE"
    print(f"  {driver}: {status}")

print()
print("=== RECOMENDACIONES ===")
if 'FreeTDS' in drivers:
    print("✅ FreeTDS está disponible. Usar: DB_DRIVER={FreeTDS}")
elif any('SQL Server' in d for d in drivers):
    sql_drivers = [d for d in drivers if 'SQL Server' in d]
    print(f"✅ Drivers de SQL Server disponibles: {sql_drivers}")
    print(f"   Usar: DB_DRIVER={{{sql_drivers[0]}}}")
else:
    print("❌ No hay drivers compatibles con SQL Server.")
    print("   Instalar FreeTDS: brew install freetds")
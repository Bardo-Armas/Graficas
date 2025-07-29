import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import pyodbc

load_dotenv()

class DatabaseConfig:
    def __init__(self):
        self.server = os.getenv('DB_SERVER')
        self.database = os.getenv('DB_DATABASE')
        self.username = os.getenv('DB_USERNAME')
        self.password = os.getenv('DB_PASSWORD')
        self.driver = os.getenv('DB_DRIVER', '{FreeTDS}')  # Cambiar default a FreeTDS
        
        print(f"🔧 Configuración de BD:")
        print(f"   Server: {self.server}")
        print(f"   Database: {self.database}")
        print(f"   Username: {self.username}")
        print(f"   Driver configurado: {self.driver}")
    
    def _get_available_driver(self):
        """Detectar el driver ODBC disponible en el sistema"""
        drivers = pyodbc.drivers()
        print(f"🔍 Drivers disponibles en el sistema: {drivers}")
        
        # Si el driver configurado en .env está disponible, usarlo
        driver_name = self.driver.replace('{', '').replace('}', '')
        if driver_name in drivers:
            print(f"✅ Usando driver configurado: {driver_name}")
            return self.driver
        
        # Orden de preferencia de drivers como fallback
        preferred_drivers = [
            'FreeTDS',
            'ODBC Driver 17 for SQL Server',
            'ODBC Driver 18 for SQL Server',
            'ODBC Driver 13 for SQL Server',
            'SQL Server'
        ]
        
        for preferred in preferred_drivers:
            if preferred in drivers:
                print(f"✅ Usando driver fallback: {preferred}")
                return f'{{{preferred}}}'
        
        # Si no encuentra ninguno, mostrar error detallado
        if not drivers:
            raise Exception("❌ No se encontraron drivers ODBC instalados en el sistema")
        else:
            print(f"❌ Drivers disponibles: {drivers}")
            raise Exception(f"No se encontró un driver compatible. Drivers disponibles: {drivers}")
    
    def get_engine(self):
        """Crear engine de SQLAlchemy con manejo de errores mejorado"""
        if not all([self.server, self.database, self.username, self.password]):
            missing = []
            if not self.server: missing.append('DB_SERVER')
            if not self.database: missing.append('DB_DATABASE')
            if not self.username: missing.append('DB_USERNAME')
            if not self.password: missing.append('DB_PASSWORD')
            raise ValueError(f"Faltan variables de entorno: {', '.join(missing)}")
        
        # Detectar driver disponible
        try:
            available_driver = self._get_available_driver()
        except Exception as e:
            print(f"❌ Error detectando driver: {e}")
            raise
        
        # Escapar caracteres especiales en la contraseña
        escaped_password = quote_plus(self.password)
        
        # Limpiar el nombre del driver para la URL
        clean_driver = available_driver.replace(' ', '+').replace('{', '').replace('}', '')
        
        # Construir connection string
        connection_string = (
            f"mssql+pyodbc://{self.username}:{escaped_password}@{self.server}/"
            f"{self.database}?driver={clean_driver}"
        )
        
        print(f"🔗 Connection string: mssql+pyodbc://{self.username}:***@{self.server}/{self.database}?driver={clean_driver}")
        
        try:
            # Configuración específica para FreeTDS
            connect_args = {
                "timeout": 30,
            }
            
            # Si es FreeTDS, agregar configuraciones específicas
            if 'FreeTDS' in available_driver:
                connect_args.update({
                    "TDS_Version": "8.0",
                    "port": "1433"
                })
                print("🔧 Usando configuración específica para FreeTDS")
            
            engine = create_engine(
                connection_string, 
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False,
                connect_args=connect_args
            )
            
            # Probar la conexión con SQLAlchemy 2.0 syntax
            print("🔄 Probando conexión a la base de datos...")
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                print(f"✅ Conexión exitosa! Resultado: {row}")
            
            return engine
            
        except Exception as e:
            print(f"❌ Error de conexión: {str(e)}")
            print(f"🔧 Driver usado: {available_driver}")
            print(f"🔍 Drivers disponibles: {pyodbc.drivers()}")
            
            # Sugerencias específicas
            if 'FreeTDS' not in str(pyodbc.drivers()):
                print("💡 Sugerencia: Instalar FreeTDS con: brew install freetds")
            
            raise
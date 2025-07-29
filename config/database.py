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
        self.driver = os.getenv('DB_DRIVER', '{FreeTDS}')
        
        print(f"🔧 Configuración de BD:")
        print(f"   Server: {self.server}")
        print(f"   Database: {self.database}")
        print(f"   Username: {self.username}")
        print(f"   Driver: {self.driver}")
    
    def _get_available_driver(self):
        """Detectar el driver ODBC disponible en el sistema"""
        try:
            drivers = pyodbc.drivers()
            print(f"🔍 Drivers disponibles: {drivers}")
            
            # Priorizar FreeTDS para Render
            if 'FreeTDS' in drivers:
                print("✅ Usando FreeTDS")
                return '{FreeTDS}'
            
            # Buscar otros drivers de SQL Server
            for driver in drivers:
                if 'SQL Server' in driver:
                    print(f"✅ Usando {driver}")
                    return f'{{{driver}}}'
            
            # Si no encuentra nada, usar el configurado
            print(f"⚠️ Usando driver configurado: {self.driver}")
            return self.driver
            
        except Exception as e:
            print(f"⚠️ Error detectando drivers: {e}")
            print(f"🔧 Usando driver por defecto: {self.driver}")
            return self.driver
    
    def get_engine(self):
        """Crear engine de SQLAlchemy optimizado para Render"""
        if not all([self.server, self.database, self.username, self.password]):
            missing = []
            if not self.server: missing.append('DB_SERVER')
            if not self.database: missing.append('DB_DATABASE')
            if not self.username: missing.append('DB_USERNAME')
            if not self.password: missing.append('DB_PASSWORD')
            raise ValueError(f"Faltan variables de entorno: {', '.join(missing)}")
        
        # Detectar driver disponible
        available_driver = self._get_available_driver()
        
        # Escapar caracteres especiales en la contraseña
        escaped_password = quote_plus(self.password)
        
        # Limpiar el nombre del driver para la URL
        clean_driver = available_driver.replace(' ', '+').replace('{', '').replace('}', '')
        
        # Construir connection string optimizada para Render
        connection_string = (
            f"mssql+pyodbc://{self.username}:{escaped_password}@{self.server}/"
            f"{self.database}?driver={clean_driver}&TDS_Version=8.0&port=1433"
        )
        
        print(f"🔗 Connection string: mssql+pyodbc://{self.username}:***@{self.server}/{self.database}?driver={clean_driver}")
        
        try:
            # Configuración optimizada para Render
            engine = create_engine(
                connection_string, 
                pool_pre_ping=True,
                pool_recycle=1800,  # 30 minutos
                pool_size=5,
                max_overflow=10,
                echo=False,
                connect_args={
                    "timeout": 60,
                    "login_timeout": 60,
                    "autocommit": True
                }
            )
            
            # Probar la conexión
            print("🔄 Probando conexión a la base de datos...")
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                print(f"✅ Conexión exitosa! Resultado: {row}")
            
            return engine
            
        except Exception as e:
            print(f"❌ Error de conexión: {str(e)}")
            print(f"🔧 Driver usado: {available_driver}")
            
            # Información de diagnóstico para Render
            try:
                drivers = pyodbc.drivers()
                print(f"🔍 Drivers disponibles en Render: {drivers}")
            except:
                print("❌ No se pudieron listar los drivers")
            
            raise
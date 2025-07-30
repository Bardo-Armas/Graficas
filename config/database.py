import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

load_dotenv()

class DatabaseConfig:
    def __init__(self):
        self.server = os.getenv('DB_SERVER')
        self.database = os.getenv('DB_DATABASE')
        self.username = os.getenv('DB_USERNAME')
        self.password = os.getenv('DB_PASSWORD')
        self.driver = os.getenv('DB_DRIVER', 'pymssql')
    
    def _try_pyodbc_connection(self):
        """Intentar conexión con pyodbc"""
        try:
            import pyodbc
            
            drivers = pyodbc.drivers()
            print(f"🔍 Drivers ODBC disponibles: {drivers}")
            
            # Buscar FreeTDS o SQL Server drivers
            available_driver = None
            for driver in ['FreeTDS', 'ODBC Driver 17 for SQL Server', 'SQL Server']:
                if driver in drivers:
                    available_driver = driver
                    break
            
            if not available_driver:
                print("⚠️ No se encontraron drivers ODBC compatibles")
                return None
            
            print(f"✅ Usando driver ODBC: {available_driver}")
            
            # Escapar contraseña
            escaped_password = quote_plus(self.password)
            
            # Connection string para pyodbc
            connection_string = (
                f"mssql+pyodbc://{self.username}:{escaped_password}@{self.server}/"
                f"{self.database}?driver={available_driver}&TDS_Version=8.0"
            )
            
            engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                pool_recycle=1800,
                pool_size=3,
                max_overflow=5,
                echo=False
            )
            
            return engine
            
        except ImportError:
            print("⚠️ pyodbc no disponible")
            return None
        except Exception as e:
            print(f"⚠️ Error con pyodbc: {e}")
            return None
    
    def _try_pymssql_connection(self):
        """Intentar conexión con pymssql"""
        try:
            import pymssql
            print("✅ Usando pymssql como driver")
            
            # Escapar contraseña
            escaped_password = quote_plus(self.password)
            
            # Connection string para pymssql
            connection_string = (
                f"mssql+pymssql://{self.username}:{escaped_password}@{self.server}/"
                f"{self.database}"
            )
            
            engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                pool_recycle=1800,
                pool_size=3,
                max_overflow=5,
                echo=False
            )
            
            return engine
            
        except ImportError:
            print("⚠️ pymssql no disponible")
            return None
        except Exception as e:
            print(f"⚠️ Error con pymssql: {e}")
            return None
    
    def get_engine(self):
        """Crear engine de SQLAlchemy con fallback automático"""
        if not all([self.server, self.database, self.username, self.password]):
            missing = []
            if not self.server: missing.append('DB_SERVER')
            if not self.database: missing.append('DB_DATABASE')
            if not self.username: missing.append('DB_USERNAME')
            if not self.password: missing.append('DB_PASSWORD')
            raise ValueError(f"Faltan variables de entorno: {', '.join(missing)}")
        
        # Intentar pyodbc primero
        engine = self._try_pyodbc_connection()
        
        # Si falla, intentar pymssql
        if engine is None:
            print("🔄 Intentando con pymssql...")
            engine = self._try_pymssql_connection()
        
        if engine is None:
            raise Exception("❌ No se pudo establecer conexión con ningún driver disponible")
        
        # Probar la conexión
        try:
            print("🔄 Probando conexión a la base de datos...")
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                print(f"✅ Conexión exitosa! Resultado: {row}")
            
            return engine
            
        except Exception as e:
            print(f"❌ Error de conexión: {str(e)}")
            raise
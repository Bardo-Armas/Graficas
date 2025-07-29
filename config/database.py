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
        self.driver = os.getenv('DB_DRIVER', '{ODBC Driver 17 for SQL Server}')
    
    def _get_available_driver(self):
        """Detectar el driver ODBC disponible en el sistema"""
        drivers = pyodbc.drivers()
        print(f"Drivers disponibles: {drivers}")
        
        # Orden de preferencia de drivers
        preferred_drivers = [
            'ODBC Driver 17 for SQL Server',
            'ODBC Driver 18 for SQL Server',
            'ODBC Driver 13 for SQL Server',
            'FreeTDS',
            'SQL Server'
        ]
        
        for preferred in preferred_drivers:
            if preferred in drivers:
                print(f"Usando driver: {preferred}")
                return f'{{{preferred}}}'
        
        # Si no encuentra ninguno, mostrar error detallado
        if not drivers:
            raise Exception("No se encontraron drivers ODBC instalados en el sistema")
        else:
            print(f"Drivers disponibles: {drivers}")
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
            print(f"Error detectando driver: {e}")
            # Intentar con el driver configurado en .env
            available_driver = self.driver
            print(f"Intentando con driver configurado: {available_driver}")
        
        # Escapar caracteres especiales en la contraseña
        escaped_password = quote_plus(self.password)
        
        # Construir connection string
        connection_string = (
            f"mssql+pyodbc://{self.username}:{escaped_password}@{self.server}/"
            f"{self.database}?driver={available_driver.replace(' ', '+').replace('{', '').replace('}', '')}"
        )
        
        print(f"Connection string (sin password): mssql+pyodbc://{self.username}:***@{self.server}/{self.database}?driver={available_driver}")
        
        try:
            engine = create_engine(
                connection_string, 
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False,
                connect_args={
                    "timeout": 30,
                    "autocommit": True
                }
            )
            
            # Probar la conexión con SQLAlchemy 2.0 syntax
            print("Probando conexión a la base de datos...")
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                print(f"✅ Conexión exitosa! Resultado: {row}")
            
            return engine
            
        except Exception as e:
            print(f"❌ Error de conexión: {str(e)}")
            print(f"Driver usado: {available_driver}")
            print(f"Drivers disponibles en el sistema: {pyodbc.drivers()}")
            raise
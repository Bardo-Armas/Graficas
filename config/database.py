# Importaciones del sistema operativo y manejo de variables de entorno
import os
from dotenv import load_dotenv  # Para cargar variables de entorno desde archivo .env
from sqlalchemy import create_engine, text  # ORM para manejo de base de datos
from urllib.parse import quote_plus  # Para escapar caracteres especiales en URLs

# Cargar variables de entorno desde el archivo .env
# Esto permite mantener credenciales sensibles fuera del código fuente
load_dotenv()

class DatabaseConfig:
    """
    Clase de configuración para la conexión a la base de datos SQL Server.
    
    Esta clase maneja la conexión a SQL Server utilizando múltiples drivers
    con un sistema de fallback automático. Primero intenta usar pyodbc (más robusto)
    y si falla, utiliza pymssql (más ligero) como alternativa.
    
    Características principales:
    - Carga automática de credenciales desde variables de entorno
    - Sistema de fallback entre drivers (pyodbc -> pymssql)
    - Pool de conexiones configurado para optimizar rendimiento
    - Validación automática de conexión
    """
    
    def __init__(self):
        """
        Inicializa la configuración de base de datos cargando las credenciales
        desde las variables de entorno definidas en el archivo .env
        """
        # Servidor de base de datos (ej: localhost, 192.168.1.100, servidor.dominio.com)
        self.server = os.getenv('DB_SERVER')
        
        # Nombre de la base de datos específica a conectar
        self.database = os.getenv('DB_DATABASE')
        
        # Usuario para autenticación en SQL Server
        self.username = os.getenv('DB_USERNAME')
        
        # Contraseña del usuario (se maneja de forma segura)
        self.password = os.getenv('DB_PASSWORD')
        
        # Driver preferido por defecto (pymssql es más ligero y compatible)
        self.driver = os.getenv('DB_DRIVER', 'pymssql')
    
    def _try_pyodbc_connection(self):
        """
        Intenta establecer conexión usando el driver pyodbc.
        
        pyodbc es más robusto y soporta más características avanzadas de SQL Server,
        pero requiere drivers ODBC instalados en el sistema operativo.
        
        Returns:
            sqlalchemy.Engine: Motor de base de datos configurado o None si falla
        """
        try:
            # Importar pyodbc dinámicamente para evitar errores si no está instalado
            import pyodbc
            
            # Obtener lista de drivers ODBC disponibles en el sistema
            drivers = pyodbc.drivers()
            print(f"🔍 Drivers ODBC disponibles: {drivers}")
            
            # Buscar drivers compatibles con SQL Server en orden de preferencia
            # FreeTDS: Driver open-source multiplataforma
            # ODBC Driver 17: Driver oficial de Microsoft más reciente
            # SQL Server: Driver legacy pero ampliamente compatible
            available_driver = None
            for driver in ['FreeTDS', 'ODBC Driver 17 for SQL Server', 'SQL Server']:
                if driver in drivers:
                    available_driver = driver
                    break
            
            # Si no hay drivers compatibles, no se puede usar pyodbc
            if not available_driver:
                print("⚠️ No se encontraron drivers ODBC compatibles")
                return None
            
            print(f"✅ Usando driver ODBC: {available_driver}")
            
            # Escapar caracteres especiales en la contraseña para evitar errores de parsing
            escaped_password = quote_plus(self.password)
            
            # Construir string de conexión para pyodbc
            # TDS_Version=8.0 especifica la versión del protocolo Tabular Data Stream
            connection_string = (
                f"mssql+pyodbc://{self.username}:{escaped_password}@{self.server}/"
                f"{self.database}?driver={available_driver}&TDS_Version=8.0"
            )
            
            # Crear motor SQLAlchemy con configuración optimizada
            engine = create_engine(
                connection_string,
                pool_pre_ping=True,    # Verifica conexiones antes de usarlas
                pool_recycle=1800,     # Recicla conexiones cada 30 minutos
                pool_size=3,           # Mantiene 3 conexiones activas en el pool
                max_overflow=5,        # Permite hasta 5 conexiones adicionales temporales
                echo=False             # No muestra SQL queries en consola (para producción)
            )
            
            return engine
            
        except ImportError:
            # pyodbc no está instalado en el sistema
            print("⚠️ pyodbc no disponible")
            return None
        except Exception as e:
            # Error durante la configuración o conexión con pyodbc
            print(f"⚠️ Error con pyodbc: {e}")
            return None
    
    def _try_pymssql_connection(self):
        """
        Intenta establecer conexión usando el driver pymssql.
        
        pymssql es más ligero y fácil de instalar, pero con menos características
        avanzadas. Es ideal como fallback cuando pyodbc no está disponible.
        
        Returns:
            sqlalchemy.Engine: Motor de base de datos configurado o None si falla
        """
        try:
            # Importar pymssql dinámicamente
            import pymssql
            print("✅ Usando pymssql como driver")
            
            # Escapar caracteres especiales en la contraseña
            escaped_password = quote_plus(self.password)
            
            # Construir string de conexión para pymssql (más simple que pyodbc)
            connection_string = (
                f"mssql+pymssql://{self.username}:{escaped_password}@{self.server}/"
                f"{self.database}"
            )
            
            # Crear motor SQLAlchemy con la misma configuración de pool
            engine = create_engine(
                connection_string,
                pool_pre_ping=True,    # Verifica conexiones antes de usarlas
                pool_recycle=1800,     # Recicla conexiones cada 30 minutos
                pool_size=3,           # Mantiene 3 conexiones activas en el pool
                max_overflow=5,        # Permite hasta 5 conexiones adicionales temporales
                echo=False             # No muestra SQL queries en consola
            )
            
            return engine
            
        except ImportError:
            # pymssql no está instalado en el sistema
            print("⚠️ pymssql no disponible")
            return None
        except Exception as e:
            # Error durante la configuración o conexión con pymssql
            print(f"⚠️ Error con pymssql: {e}")
            return None
    
    def get_engine(self):
        """
        Método principal para obtener un motor de base de datos configurado.
        
        Implementa un sistema de fallback automático:
        1. Valida que todas las credenciales estén disponibles
        2. Intenta conexión con pyodbc (preferido)
        3. Si falla, intenta con pymssql (fallback)
        4. Valida la conexión con una query de prueba
        
        Returns:
            sqlalchemy.Engine: Motor de base de datos listo para usar
            
        Raises:
            ValueError: Si faltan variables de entorno requeridas
            Exception: Si no se puede establecer conexión con ningún driver
        """
        
        # ==========================================
        # VALIDACIÓN DE CREDENCIALES
        # ==========================================
        
        # Verificar que todas las credenciales necesarias estén disponibles
        if not all([self.server, self.database, self.username, self.password]):
            # Identificar específicamente qué variables faltan para facilitar debugging
            missing = []
            if not self.server: missing.append('DB_SERVER')
            if not self.database: missing.append('DB_DATABASE')
            if not self.username: missing.append('DB_USERNAME')
            if not self.password: missing.append('DB_PASSWORD')
            raise ValueError(f"Faltan variables de entorno: {', '.join(missing)}")
        
        # ==========================================
        # SISTEMA DE FALLBACK ENTRE DRIVERS
        # ==========================================
        
        # Primer intento: pyodbc (driver preferido por su robustez)
        engine = self._try_pyodbc_connection()
        
        # Segundo intento: pymssql (fallback más ligero)
        if engine is None:
            print("🔄 Intentando con pymssql...")
            engine = self._try_pymssql_connection()
        
        # Si ambos drivers fallan, la conexión es imposible
        if engine is None:
            raise Exception("❌ No se pudo establecer conexión con ningún driver disponible")
        
        # ==========================================
        # VALIDACIÓN DE CONEXIÓN
        # ==========================================
        
        # Probar la conexión ejecutando una query simple
        try:
            print("🔄 Probando conexión a la base de datos...")
            
            # Ejecutar query de prueba para verificar conectividad
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                print(f"✅ Conexión exitosa! Resultado: {row}")
            
            # Retornar el motor configurado y validado
            return engine
            
        except Exception as e:
            # La conexión falló durante la validación
            print(f"❌ Error de conexión: {str(e)}")
            raise
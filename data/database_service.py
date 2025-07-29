import pandas as pd
import streamlit as st
from config.database import DatabaseConfig
from textwrap import dedent
import pyodbc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

class DatabaseService:
    def __init__(self):
        self.db_config = DatabaseConfig()
    
    @st.cache_data(ttl=300)  # Cache por 5 minutos
    def get_orders_data(_self, fecha_inicio, fecha_fin):
        """Obtener datos de órdenes con cache optimizado"""
        query = dedent(f"""
            SELECT 
                id_order, 
                order_completion_date, 
                order_acceptance_date, 
                costo_creditos, 
                id_restaurant, 
                name_restaurant,
                created_at
            FROM orders_details
            WHERE CONVERT(DATE, order_completion_date) >= '{fecha_inicio}' 
              AND CONVERT(DATE, order_completion_date) <= '{fecha_fin}'
        """)
        
        try:
            print("🔄 Intentando conectar a la base de datos...")
            engine = _self.db_config.get_engine()
            
            print("📊 Ejecutando consulta...")
            # Usar text() para SQLAlchemy 2.0
            df = pd.read_sql(text(query), engine)
            
            print(f"✅ Consulta exitosa. Registros obtenidos: {len(df)}")
            engine.dispose()
            
            return {
                "success": True,
                "data": {
                    "detalle": {
                        "general": {
                            "todos": df.to_dict('records')
                        }
                    }
                }
            }
            
        except pyodbc.Error as e:
            error_msg = f"Error ODBC: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Mostrar información de diagnóstico
            print("🔍 Información de diagnóstico:")
            print(f"   - Drivers disponibles: {pyodbc.drivers()}")
            print(f"   - Servidor: {_self.db_config.server}")
            print(f"   - Base de datos: {_self.db_config.database}")
            print(f"   - Usuario: {_self.db_config.username}")
            print(f"   - Driver configurado: {_self.db_config.driver}")
            
            st.error(f"Error de conexión ODBC: {str(e)}")
            st.info("💡 Sugerencias:")
            st.write("1. Verifica que el driver ODBC esté instalado correctamente")
            st.write("2. Ejecuta: `python check_drivers.py` para ver drivers disponibles")
            st.write("3. Si usas macOS, considera instalar FreeTDS: `brew install freetds`")
            
            return None
            
        except SQLAlchemyError as e:
            error_msg = f"Error SQLAlchemy: {str(e)}"
            print(f"❌ {error_msg}")
            st.error(error_msg)
            return None
            
        except Exception as e:
            error_msg = f"Error general: {str(e)}"
            print(f"❌ {error_msg}")
            st.error(error_msg)
            return None
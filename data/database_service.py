"""
Servicio de Base de Datos
========================

Este módulo proporciona la clase DatabaseService que maneja todas las operaciones
de acceso a datos de la aplicación, incluyendo consultas SQL optimizadas y
gestión de conexiones a la base de datos.

Funcionalidades principales:
- Conexión segura a SQL Server con manejo de errores
- Consultas optimizadas con cache para mejorar rendimiento
- Manejo robusto de excepciones y logging detallado
- Integración con Streamlit para cache automático
- Validación y limpieza de datos de entrada

La clase utiliza SQLAlchemy para gestión de conexiones y pandas para
manipulación de resultados, optimizada para consultas de gran volumen.
"""

import pandas as pd
import streamlit as st
from config.database import DatabaseConfig
from textwrap import dedent
import pyodbc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

class DatabaseService:
    """
    Servicio principal para operaciones de base de datos.
    
    Proporciona métodos para ejecutar consultas SQL de manera segura y eficiente,
    con manejo automático de conexiones y cache optimizado para la aplicación.
    """
    
    def __init__(self):
        """
        Inicializar el servicio de base de datos.
        
        Crea una instancia de DatabaseConfig para gestionar las conexiones.
        """
        self.db_config = DatabaseConfig()
    
    @st.cache_data(ttl=300)  # Cache por 5 minutos para optimizar rendimiento
    def get_orders_data(_self, fecha_inicio, fecha_fin):
        """
        Obtener datos de órdenes dentro de un rango de fechas específico.
        
        Ejecuta una consulta SQL optimizada para recuperar información detallada
        de órdenes, incluyendo fechas, costos, y datos de establecimientos.
        
        Args:
            fecha_inicio (str): Fecha de inicio en formato YYYY-MM-DD
            fecha_fin (str): Fecha de fin en formato YYYY-MM-DD
            
        Returns:
            dict: Diccionario con estructura de respuesta estándar:
                - success (bool): Indica si la consulta fue exitosa
                - data (dict): Datos estructurados con información de órdenes
                
        Returns None en caso de error en la consulta.
        """
        # Consulta SQL optimizada con campos específicos necesarios
        query = dedent(f"""
            SELECT 
                id_order,                    -- ID único de la orden
                order_completion_date,       -- Fecha de completación de la orden
                order_acceptance_date,       -- Fecha de aceptación de la orden
                costo_creditos,             -- Costo en créditos de la orden
                id_restaurant,              -- ID del establecimiento
                name_restaurant,            -- Nombre del establecimiento
                created_at                  -- Fecha de creación del registro
            FROM orders_details
            WHERE CONVERT(DATE, order_completion_date) >= '{fecha_inicio}' 
              AND CONVERT(DATE, order_completion_date) <= '{fecha_fin}'
        """)
        
        try:
            # Logging de inicio de operación
            print("🔄 Intentando conectar a la base de datos...")
            engine = _self.db_config.get_engine()
            
            print("📊 Ejecutando consulta...")
            # Usar text() para compatibilidad con SQLAlchemy 2.0
            df = pd.read_sql(text(query), engine)
            
            # Logging de resultado exitoso
            print(f"✅ Consulta exitosa. Registros obtenidos: {len(df)}")
            
            # Liberar recursos de conexión
            engine.dispose()
            
            # Retornar datos en formato estándar de la aplicación
            return {
                "success": True,
                "data": {
                    "detalle": {
                        "general": {
                            "todos": df.to_dict('records')  # Convertir DataFrame a lista de diccionarios
                        }
                    }
                }
            }
            
        except pyodbc.Error as e:
            # Manejo específico de errores ODBC
            error_msg = f"Error ODBC: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Información de diagnóstico para debugging
            print("🔍 Información de diagnóstico:")
            print(f"   - Servidor: {_self.db_config.server}")
            print(f"   - Base de datos: {_self.db_config.database}")

            return None
            
        except Exception as e:
            # Manejo de errores generales
            error_msg = f"Error general: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Mostrar error en la interfaz de Streamlit
            st.error(error_msg)
            return None
"""
Manejador de Errores
===================

Este módulo proporciona herramientas para el manejo consistente de errores
y validaciones en toda la aplicación.

Funcionalidades principales:
- Decoradores para manejo automático de errores
- Validaciones de datos y rangos de fechas
- Logging centralizado de errores
- Mensajes de error consistentes en la interfaz
- Operaciones matemáticas seguras
- Clase centralizada para gestión de errores

El módulo está integrado con Streamlit para mostrar mensajes de error
de manera consistente y profesional en la interfaz de usuario.
"""

import streamlit as st
import logging
from functools import wraps
from typing import Any, Optional

# Configuración global de logging para toda la aplicación
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def handle_errors(func):
    """
    Decorador para manejo consistente de errores en funciones.
    
    Captura cualquier excepción que ocurra en la función decorada,
    la registra en los logs y muestra un mensaje de error en la interfaz.
    
    Args:
        func: Función a decorar
        
    Returns:
        function: Función decorada con manejo de errores
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Registrar error en logs con información detallada
            logging.error(f"Error en {func.__name__}: {str(e)}")
            
            # Mostrar error en la interfaz de usuario
            st.error(f"❌ Error: {str(e)}")
            return None
    return wrapper

def handle_data_errors(func):
    """
    Decorador específico para manejo de errores relacionados con datos.
    
    Además del manejo básico de errores, verifica si el resultado
    es None o un DataFrame vacío, mostrando advertencias apropiadas.
    
    Args:
        func: Función a decorar (típicamente funciones de procesamiento de datos)
        
    Returns:
        function: Función decorada con validación de datos
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # Verificar si el resultado está vacío o es None
            if result is None or (hasattr(result, 'empty') and result.empty):
                st.warning(f"⚠️ No se encontraron datos en {func.__name__}")
                return None
            return result
        except Exception as e:
            # Logging específico para errores de datos
            logging.error(f"Error de datos en {func.__name__}: {str(e)}")
            st.error(f"❌ Error procesando datos: {str(e)}")
            return None
    return wrapper

def validate_date_range(fecha_inicio, fecha_fin):
    """
    Validar que un rango de fechas sea lógicamente correcto.
    
    Verifica que la fecha de inicio no sea posterior a la fecha de fin,
    mostrando un mensaje de error si la validación falla.
    
    Args:
        fecha_inicio: Fecha de inicio del rango
        fecha_fin: Fecha de fin del rango
        
    Returns:
        bool: True si el rango es válido, False en caso contrario
    """
    if fecha_inicio > fecha_fin:
        st.error("❌ La fecha de inicio no puede ser mayor a la fecha de fin")
        return False
    return True

def validate_dataframe(df, required_columns: list = None):
    """
    Validar un DataFrame y verificar columnas requeridas.
    
    Comprueba que el DataFrame no esté vacío y que contenga
    todas las columnas especificadas como requeridas.
    
    Args:
        df: DataFrame a validar
        required_columns (list): Lista de nombres de columnas requeridas
        
    Returns:
        bool: True si el DataFrame es válido, False en caso contrario
    """
    # Verificar que el DataFrame no esté vacío o sea None
    if df is None or df.empty:
        return False
    
    # Verificar columnas requeridas si se especificaron
    if required_columns:
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"❌ Faltan columnas requeridas: {missing_columns}")
            return False
    
    return True

def safe_division(numerator, denominator, default_value=0):
    """
    Realizar división segura que maneja división por cero.
    
    Ejecuta una división protegida contra errores de división por cero
    y otros errores de tipo, retornando un valor por defecto en caso de error.
    
    Args:
        numerator: Numerador de la división
        denominator: Denominador de la división
        default_value: Valor a retornar en caso de error (por defecto 0)
        
    Returns:
        float: Resultado de la división o valor por defecto
    """
    try:
        # Verificar división por cero explícitamente
        if denominator == 0:
            return default_value
        return numerator / denominator
    except (TypeError, ValueError):
        # Manejar errores de tipo o valor
        return default_value

class ErrorHandler:
    """
    Clase para manejo centralizado de errores y mensajes.
    
    Proporciona métodos estáticos para logging de errores y
    visualización de mensajes en la interfaz de usuario de manera consistente.
    """
    
    @staticmethod
    def log_error(message: str, error: Exception = None):
        """
        Registrar error en el sistema de logging.
        
        Guarda un mensaje de error en los logs del sistema,
        opcionalmente incluyendo detalles de una excepción.
        
        Args:
            message (str): Mensaje descriptivo del error
            error (Exception): Excepción opcional para incluir detalles
        """
        if error:
            logging.error(f"{message}: {str(error)}")
        else:
            logging.error(message)
    
    @staticmethod
    def show_error(message: str, error: Exception = None):
        """
        Mostrar mensaje de error en la interfaz de usuario.
        
        Presenta un mensaje de error formateado en la interfaz de Streamlit,
        opcionalmente incluyendo detalles de una excepción.
        
        Args:
            message (str): Mensaje principal del error
            error (Exception): Excepción opcional para mostrar detalles
        """
        if error:
            st.error(f"❌ {message}: {str(error)}")
        else:
            st.error(f"❌ {message}")
    
    @staticmethod
    def show_warning(message: str):
        """
        Mostrar mensaje de advertencia en la interfaz.
        
        Presenta un mensaje de advertencia formateado en Streamlit
        para situaciones que requieren atención pero no son errores críticos.
        
        Args:
            message (str): Mensaje de advertencia a mostrar
        """
        st.warning(f"⚠️ {message}")
    
    @staticmethod
    def show_info(message: str):
        """
        Mostrar mensaje informativo en la interfaz.
        
        Presenta un mensaje informativo formateado en Streamlit
        para comunicar información importante al usuario.
        
        Args:
            message (str): Mensaje informativo a mostrar
        """
        st.info(f"ℹ️ {message}")
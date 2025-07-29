import streamlit as st
import logging
from functools import wraps
from typing import Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def handle_errors(func):
    """Decorador para manejo consistente de errores"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error en {func.__name__}: {str(e)}")
            st.error(f"❌ Error: {str(e)}")
            return None
    return wrapper

def handle_data_errors(func):
    """Decorador específico para errores de datos"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if result is None or (hasattr(result, 'empty') and result.empty):
                st.warning(f"⚠️ No se encontraron datos en {func.__name__}")
                return None
            return result
        except Exception as e:
            logging.error(f"Error de datos en {func.__name__}: {str(e)}")
            st.error(f"❌ Error procesando datos: {str(e)}")
            return None
    return wrapper

def validate_date_range(fecha_inicio, fecha_fin):
    """Validar rango de fechas"""
    if fecha_inicio > fecha_fin:
        st.error("❌ La fecha de inicio no puede ser mayor a la fecha de fin")
        return False
    return True

def validate_dataframe(df, required_columns: list = None):
    """Validar DataFrame y columnas requeridas"""
    if df is None or df.empty:
        return False
    
    if required_columns:
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"❌ Faltan columnas requeridas: {missing_columns}")
            return False
    
    return True

def safe_division(numerator, denominator, default_value=0):
    """División segura que maneja división por cero"""
    try:
        if denominator == 0:
            return default_value
        return numerator / denominator
    except (TypeError, ValueError):
        return default_value

class ErrorHandler:
    """Clase para manejo centralizado de errores"""
    
    @staticmethod
    def log_error(message: str, error: Exception = None):
        """Registrar error en logs"""
        if error:
            logging.error(f"{message}: {str(error)}")
        else:
            logging.error(message)
    
    @staticmethod
    def show_error(message: str, error: Exception = None):
        """Mostrar error en la interfaz"""
        if error:
            st.error(f"❌ {message}: {str(error)}")
        else:
            st.error(f"❌ {message}")
    
    @staticmethod
    def show_warning(message: str):
        """Mostrar advertencia en la interfaz"""
        st.warning(f"⚠️ {message}")
    
    @staticmethod
    def show_info(message: str):
        """Mostrar información en la interfaz"""
        st.info(f"ℹ️ {message}")
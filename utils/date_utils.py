"""
Utilidades de Fechas
===================

Este módulo contiene la clase DateUtils que proporciona métodos estáticos
para el manejo y formateo de fechas en la aplicación.

Funcionalidades principales:
- Formateo de fechas en español
- Cálculo de rangos de fechas por defecto
- Manejo de períodos mensuales
- Cálculo de números de semana con lógica específica
- Formateo de etiquetas de hora
- Validación de horarios comerciales

La clase incluye constantes para nombres de meses en español y métodos
optimizados para trabajar con datos temporales del negocio.
"""

from datetime import datetime, timedelta
from typing import List, Tuple
import pandas as pd

class DateUtils:
    """
    Utilidades para manejo y formateo de fechas.
    
    Esta clase proporciona métodos estáticos para operaciones comunes
    con fechas, incluyendo formateo en español, cálculos de períodos
    y validaciones de horarios comerciales.
    """
    
    # Diccionario de nombres de meses en español para formateo
    MESES_ESPANOL = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    
    @staticmethod
    def get_default_date_range(days_back: int = 30) -> Tuple[datetime, datetime]:
        """
        Obtener rango de fechas por defecto para análisis.
        
        Calcula un rango de fechas desde una cantidad específica de días
        hacia atrás hasta la fecha actual, útil para configuraciones iniciales.
        
        Args:
            days_back (int): Número de días hacia atrás desde hoy (por defecto 30)
            
        Returns:
            Tuple[datetime, datetime]: Tupla con (fecha_inicio, fecha_fin)
        """
        hoy = datetime.now().date()
        fecha_inicio = hoy - timedelta(days=days_back)
        return fecha_inicio, hoy
    
    @staticmethod
    def format_date_spanish(date) -> str:
        """
        Formatear fecha en español con formato legible.
        
        Convierte una fecha a formato español legible como "15 de Enero de 2024".
        Maneja tanto objetos datetime como strings de fecha.
        
        Args:
            date: Fecha a formatear (datetime, string, o pandas datetime)
            
        Returns:
            str: Fecha formateada en español o string original si hay error
        """
        # Convertir string a datetime si es necesario
        if isinstance(date, str):
            date = pd.to_datetime(date)
        
        # Formatear si el objeto tiene atributo month
        if hasattr(date, 'month'):
            mes_nombre = DateUtils.MESES_ESPANOL[date.month]
            return f"{date.day} de {mes_nombre} de {date.year}"
        
        # Retornar string original si no se puede formatear
        return str(date)
    
    @staticmethod
    def get_month_periods(start_date, end_date) -> List[str]:
        """
        Obtener lista de períodos mensuales entre dos fechas.
        
        Genera una lista de strings con nombres de meses en español
        para todos los meses comprendidos entre las fechas especificadas.
        
        Args:
            start_date: Fecha de inicio del período
            end_date: Fecha de fin del período
            
        Returns:
            List[str]: Lista de meses formateados como "Enero 2024"
        """
        # Crear rango de períodos mensuales con pandas
        meses_periodo = pd.period_range(start=start_date, end=end_date, freq="M")
        
        # Formatear cada período en español
        return [f"{DateUtils.MESES_ESPANOL[p.month]} {p.year}" for p in meses_periodo]
    
    @staticmethod
    def calculate_week_number(fecha, reference_date=None) -> int:
        """
        Calcular número de semana basado en lógica específica del negocio.
        
        Implementa un sistema de numeración de semanas personalizado
        que considera la primera semana del año 2025 como referencia.
        
        Args:
            fecha: Fecha para calcular el número de semana
            reference_date: Fecha de referencia (por defecto 1 enero 2025)
            
        Returns:
            int: Número de semana calculado
        """
        # Establecer fecha de referencia por defecto
        if reference_date is None:
            reference_date = datetime(2025, 1, 1).date()
        
        # Definir límites de la primera semana
        primera_semana_fin = datetime(2025, 1, 5).date()
        segunda_semana_inicio = datetime(2025, 1, 6).date()
        
        # Calcular número de semana según lógica específica
        if fecha <= primera_semana_fin:
            return 1
        else:
            dias_desde_segunda_semana = (fecha - segunda_semana_inicio).days
            return (dias_desde_segunda_semana // 7) + 2
    
    @staticmethod
    def get_week_date_range(week_number: int) -> Tuple[datetime, datetime]:
        """
        Obtener rango de fechas para un número de semana específico.
        
        Calcula las fechas de inicio y fin para una semana dada,
        basado en la lógica de numeración específica del negocio.
        
        Args:
            week_number (int): Número de semana para calcular el rango
            
        Returns:
            Tuple[datetime, datetime]: Tupla con (fecha_inicio, fecha_fin) de la semana
        """
        # Definir primera semana con fechas fijas
        primera_semana_inicio = datetime(2025, 1, 1).date()
        primera_semana_fin = datetime(2025, 1, 5).date()
        
        if week_number == 1:
            return primera_semana_inicio, primera_semana_fin
        else:
            # Calcular fechas para semanas subsecuentes
            dias_desde_inicio = (week_number - 2) * 7
            inicio_semana = datetime(2025, 1, 6).date() + timedelta(days=dias_desde_inicio)
            fin_semana = inicio_semana + timedelta(days=6)
            return inicio_semana, fin_semana
    
    @staticmethod
    def format_hour_label(hour: int) -> str:
        """
        Formatear etiqueta de hora en formato 12 horas (AM/PM).
        
        Convierte una hora en formato 24 horas a formato 12 horas
        con indicadores AM/PM para mejor legibilidad.
        
        Args:
            hour (int): Hora en formato 24 horas (0-23)
            
        Returns:
            str: Hora formateada como "2:00 PM" o "10:00 AM"
        """
        if hour > 12:
            return f"{hour - 12}:00 PM"
        elif hour < 12:
            return f"{hour}:00 AM"
        else:
            return "12:00 PM"
    
    @staticmethod
    def is_business_hour(hour: int) -> bool:
        """
        Verificar si una hora está dentro del horario comercial.
        
        Determina si una hora específica está dentro del rango
        de horario comercial definido (8 AM - 11 PM).
        
        Args:
            hour (int): Hora a verificar en formato 24 horas
            
        Returns:
            bool: True si está en horario comercial, False en caso contrario
        """
        return 8 <= hour <= 23
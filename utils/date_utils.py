from datetime import datetime, timedelta
from typing import List, Tuple
import pandas as pd

class DateUtils:
    """Utilidades para manejo de fechas"""
    
    MESES_ESPANOL = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    
    @staticmethod
    def get_default_date_range(days_back: int = 30) -> Tuple[datetime, datetime]:
        """Obtener rango de fechas por defecto"""
        hoy = datetime.now().date()
        fecha_inicio = hoy - timedelta(days=days_back)
        return fecha_inicio, hoy
    
    @staticmethod
    def format_date_spanish(date) -> str:
        """Formatear fecha en español"""
        if isinstance(date, str):
            date = pd.to_datetime(date)
        
        if hasattr(date, 'month'):
            mes_nombre = DateUtils.MESES_ESPANOL[date.month]
            return f"{date.day} de {mes_nombre} de {date.year}"
        
        return str(date)
    
    @staticmethod
    def get_month_periods(start_date, end_date) -> List[str]:
        """Obtener períodos mensuales entre dos fechas"""
        meses_periodo = pd.period_range(start=start_date, end=end_date, freq="M")
        return [f"{DateUtils.MESES_ESPANOL[p.month]} {p.year}" for p in meses_periodo]
    
    @staticmethod
    def calculate_week_number(fecha, reference_date=None) -> int:
        """Calcular número de semana basado en fecha de referencia"""
        if reference_date is None:
            reference_date = datetime(2025, 1, 1).date()
        
        primera_semana_fin = datetime(2025, 1, 5).date()
        segunda_semana_inicio = datetime(2025, 1, 6).date()
        
        if fecha <= primera_semana_fin:
            return 1
        else:
            dias_desde_segunda_semana = (fecha - segunda_semana_inicio).days
            return (dias_desde_segunda_semana // 7) + 2
    
    @staticmethod
    def get_week_date_range(week_number: int) -> Tuple[datetime, datetime]:
        """Obtener rango de fechas para un número de semana"""
        primera_semana_inicio = datetime(2025, 1, 1).date()
        primera_semana_fin = datetime(2025, 1, 5).date()
        
        if week_number == 1:
            return primera_semana_inicio, primera_semana_fin
        else:
            dias_desde_inicio = (week_number - 2) * 7
            inicio_semana = datetime(2025, 1, 6).date() + timedelta(days=dias_desde_inicio)
            fin_semana = inicio_semana + timedelta(days=6)
            return inicio_semana, fin_semana
    
    @staticmethod
    def format_hour_label(hour: int) -> str:
        """Formatear etiqueta de hora"""
        if hour > 12:
            return f"{hour - 12}:00 PM"
        elif hour < 12:
            return f"{hour}:00 AM"
        else:
            return "12:00 PM"
    
    @staticmethod
    def is_business_hour(hour: int) -> bool:
        """Verificar si es hora de negocio (8 AM - 11 PM)"""
        return 8 <= hour <= 23
# Importación de la clase datetime para manejo de fechas
from datetime import datetime

class AppSettings:
    """
    Clase de configuración centralizada para la aplicación Dashboard Integrado.
    
    Esta clase contiene todas las configuraciones globales de la aplicación,
    incluyendo configuraciones de interfaz, fechas, gráficos y límites operacionales.
    Utiliza variables de clase para facilitar el acceso desde cualquier parte de la aplicación.
    """
    
    # ==========================================
    # CONFIGURACIÓN DE LA INTERFAZ DE USUARIO
    # ==========================================
    
    # Título que aparece en la pestaña del navegador y en el header de la aplicación
    PAGE_TITLE = "Dashboard Integrado"
    
    # Icono emoji que aparece junto al título en la pestaña del navegador
    PAGE_ICON = "📊"
    
    # Layout de Streamlit: "wide" utiliza todo el ancho de la pantalla
    # Otras opciones: "centered" (centrado con márgenes laterales)
    LAYOUT = "wide"
    
    # ==========================================
    # CONFIGURACIÓN DE FECHAS Y TIEMPO
    # ==========================================
    
    # Fecha de inicio por defecto para consultas de datos
    # Se establece el 1 de enero de 2025 como punto de partida estándar
    DEFAULT_START_DATE = datetime(2025, 1, 1).date()
    
    # Tiempo de vida del caché en segundos (300 segundos = 5 minutos)
    # Controla cuánto tiempo se mantienen los datos en caché antes de refrescar
    CACHE_TTL = 300  # 5 minutos
    
    # ==========================================
    # CONFIGURACIÓN DE GRÁFICOS Y VISUALIZACIÓN
    # ==========================================
    
    # Esquema de colores por defecto para los gráficos
    # "Pastel" proporciona colores suaves y agradables a la vista
    DEFAULT_COLOR_SCHEME = "Pastel"
    
    # Altura estándar en píxeles para los gráficos
    # 400px proporciona un buen balance entre visibilidad y espacio en pantalla
    CHART_HEIGHT = 400
    
    # ==========================================
    # LÍMITES Y RESTRICCIONES OPERACIONALES
    # ==========================================
    
    # Número máximo de establecimientos a mostrar en rankings/tops
    # Limita la cantidad de datos para mejorar rendimiento y legibilidad
    MAX_TOP_ESTABLISHMENTS = 10
    
    # Número máximo de peticiones concurrentes a la base de datos
    # Previene sobrecarga del servidor y mejora la estabilidad
    MAX_CONCURRENT_REQUESTS = 5
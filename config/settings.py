from datetime import datetime

class AppSettings:
    # Configuración de la aplicación
    PAGE_TITLE = "Dashboard Integrado"
    PAGE_ICON = "📊"
    LAYOUT = "wide"
    
    # Configuración de fechas
    DEFAULT_START_DATE = datetime(2025, 1, 1).date()
    CACHE_TTL = 300  # 5 minutos
    
    # Configuración de gráficos
    DEFAULT_COLOR_SCHEME = "Pastel"
    CHART_HEIGHT = 400
    
    # Límites
    MAX_TOP_ESTABLISHMENTS = 10
    MAX_CONCURRENT_REQUESTS = 5
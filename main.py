import statistics
import streamlit as st
import traceback
from config.settings import AppSettings
from views.monthly_analysis import MonthlyAnalysisView
from views.general_dashboard import GeneralDashboardView
from views.static_analysis import StaticAnalysisView
from views.map_view import MapView

# Configurar página
st.set_page_config(
    page_title=AppSettings.PAGE_TITLE,
    page_icon=AppSettings.PAGE_ICON,
    layout=AppSettings.LAYOUT
)

def main():
    """Función principal de la aplicación"""
    try:
        st.sidebar.title("Menú Principal")
        
        # Selector de vista
        app_mode = st.sidebar.selectbox(
            "Seleccione el dashboard", 
            ["Análisis Mensual", "Estadísticas Generales", "Estadísticas Semanales", "Mapa de Calor"]
        )
        
        # Renderizar vista seleccionada
        if app_mode == "Análisis Mensual":
            monthly_view = MonthlyAnalysisView()
            monthly_view.render()
        elif app_mode == "Estadísticas Generales":
            general_view = GeneralDashboardView()
            general_view.render()
        elif app_mode == "Estadísticas Semanales":
            statistic_view = StaticAnalysisView()
            statistic_view.render()
        elif app_mode == "Mapa de Calor":
            map_view = MapView()
            map_view.render()
            
    except Exception as e:
        st.error("❌ Error en la aplicación")
        st.error(f"Detalles: {str(e)}")
        
        # Mostrar traceback completo en desarrollo
        if st.checkbox("Mostrar detalles técnicos"):
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
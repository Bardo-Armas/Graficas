import streamlit as st
from config.settings import AppSettings
from views.monthly_analysis import MonthlyAnalysisView
from views.general_dashboard import GeneralDashboardView
from utils.styles import apply_professional_styling

# Configurar página
st.set_page_config(
    page_title=AppSettings.PAGE_TITLE,
    page_icon=AppSettings.PAGE_ICON,
    layout=AppSettings.LAYOUT,
    initial_sidebar_state="expanded"
)

# Aplicar estilos profesionales
apply_professional_styling()

def main():
    """Función principal de la aplicación"""
    
    # Título principal personalizado
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; margin-bottom: 2rem;">
        <h1 style="color: #1f77b4; font-weight: 700; margin: 0;">
            📊 Dashboard Profesional
        </h1>
        <p style="color: #6c757d; margin: 0.5rem 0 0 0;">
            Análisis y visualización de datos empresariales
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar personalizado
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem 0; margin-bottom: 1rem; border-bottom: 1px solid #e6e9ef;">
        <h2 style="color: #1f77b4; font-weight: 600; margin: 0;">
            🎛️ Panel de Control
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Selector de vista
    app_mode = st.sidebar.selectbox(
        "📈 Seleccione el dashboard", 
        ["Análisis Mensual", "Estadísticas Generales"],
        help="Elija el tipo de análisis que desea visualizar"
    )
    
    # Información adicional en sidebar
    st.sidebar.markdown("""
    <div style="margin-top: 2rem; padding: 1rem; background-color: #f8f9fa; border-radius: 8px; border: 1px solid #e6e9ef;">
        <h4 style="color: #1f77b4; margin-top: 0;">ℹ️ Información</h4>
        <p style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0;">
            Dashboard profesional para análisis de datos empresariales con visualizaciones interactivas.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Renderizar vista seleccionada
    if app_mode == "Análisis Mensual":
        monthly_view = MonthlyAnalysisView()
        monthly_view.render()
    else:
        general_view = GeneralDashboardView()
        general_view.render()

if __name__ == "__main__":
    main()
import streamlit as st
from config.settings import AppSettings
from views.monthly_analysis import MonthlyAnalysisView
from views.general_dashboard import GeneralDashboardView

# Configurar página
st.set_page_config(
    page_title=AppSettings.PAGE_TITLE,
    page_icon=AppSettings.PAGE_ICON,
    layout=AppSettings.LAYOUT
)

# Ocultar solo los elementos específicos solicitados
st.markdown("""
<style>
/* Ocultar el botón FORK */
[data-testid="stToolbar"] {display: none !important;}
.stAppToolbar {display: none !important;}

/* Ocultar logo de Git/GitHub */
.github-corner {display: none !important;}
[href*="github.com"] {display: none !important;}
[title*="Fork"] {display: none !important;}
[title*="GitHub"] {display: none !important;}


</style>
""", unsafe_allow_html=True)

def main():
    """Función principal de la aplicación"""
    st.sidebar.title("Menú Principal")
    
    # Selector de vista
    app_mode = st.sidebar.selectbox(
        "Seleccione el dashboard", 
        ["Análisis Mensual", "Estadísticas Generales"]
    )
    
    # Renderizar vista seleccionada
    if app_mode == "Análisis Mensual":
        monthly_view = MonthlyAnalysisView()
        monthly_view.render()
    else:
        general_view = GeneralDashboardView()
        general_view.render()

if __name__ == "__main__":
    main()
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

# Ocultar solo elementos específicos pero mantener el botón de tema
st.markdown("""
<style>
/* Ocultar logo de Git/GitHub y elementos relacionados */
.github-corner {display: none !important;}
[href*="github.com"] {display: none !important;}
[title*="Fork"] {display: none !important;}
[title*="GitHub"] {display: none !important;}

/* Ocultar el menú principal pero mantener botón de tema */
#MainMenu {visibility: hidden;}

/* Ocultar elementos específicos de FORK pero mantener configuraciones */
[data-testid="stToolbar"] > div:first-child {display: none !important;}
.stAppToolbar > div:first-child {display: none !important;}

/* Mantener visible el botón de configuración/tema */
[data-testid="stToolbar"] > div:last-child {display: block !important;}
.stAppToolbar > div:last-child {display: block !important;}

/* Asegurar que el botón de configuración sea visible */
[data-testid="stToolbar"] [data-testid="stActionButton"] {display: block !important;}
.stActionButton[title*="Settings"] {display: block !important;}
.stActionButton[title*="Configuración"] {display: block !important;}
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
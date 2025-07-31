import statistics
import streamlit as st
from config.settings import AppSettings
from views.monthly_analysis import MonthlyAnalysisView
from views.general_dashboard import GeneralDashboardView
from views.static_analysis import StaticAnalysisView

# Configurar página
st.set_page_config(
    page_title=AppSettings.PAGE_TITLE,
    page_icon=AppSettings.PAGE_ICON,
    layout=AppSettings.LAYOUT
)

# CSS más agresivo para ocultar todos los elementos específicos
st.markdown("""
<style>
/* Ocultar COMPLETAMENTE la barra superior */
.stAppHeader {display: none !important;}
.stApp > header {display: none !important;}

/* Ocultar toolbar completo */
.stToolbar {display: none !important;}
[data-testid="stToolbar"] {display: none !important;}

/* Ocultar elementos específicos de GitHub/Fork */
.github-corner {display: none !important;}
.github-fork-ribbon {display: none !important;}
[href*="github.com"] {display: none !important;}
[title*="Fork"] {display: none !important;}
[title*="GitHub"] {display: none !important;}

/* Ocultar burbuja de usuario */
.stAppToolbar {display: none !important;}
[data-testid="stAppToolbar"] {display: none !important;}

/* Ocultar coronita de Streamlit */
.stDeployButton {display: none !important;}
[data-testid="stDeployButton"] {display: none !important;}

/* Ocultar menú principal */
#MainMenu {display: none !important;}

/* Ocultar cualquier botón de acción en la esquina */
.stActionButton {display: none !important;}
[data-testid="stActionButton"] {display: none !important;}

/* Ocultar elementos flotantes */
.stApp::before,
.stApp::after {display: none !important;}

/* Forzar que no aparezcan elementos en la parte superior */
.stAppViewContainer {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

.main {
    padding-top: 1rem !important;
    margin-top: 0 !important;
}

/* Ocultar cualquier iframe o elemento externo */
iframe[src*="github"] {display: none !important;}
iframe[src*="streamlit"] {display: none !important;}

/* Selectores adicionales para elementos persistentes */
.stApp > div:first-child {display: none !important;}
.stAppViewContainer > div:first-child {display: none !important;}

/* Ocultar elementos con atributos específicos */
[data-testid*="toolbar"] {display: none !important;}
[data-testid*="header"] {display: none !important;}
[class*="toolbar"] {display: none !important;}
[class*="header"] {display: none !important;}

/* Mantener SOLO el botón de configuración de tema si es necesario */
/* Descomenta la siguiente línea si quieres mantener el botón de tema */
/* [data-testid="stActionButton"][title*="Settings"] {display: block !important;} */
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
    elif app_mode == "Estadísticas Generales":
        general_view = GeneralDashboardView()
        general_view.render()
    else:  #app_mode == "Estadísticas"
        statistic_view = StaticAnalysisView()
        statistic_view.render()

if __name__ == "__main__":
    main()
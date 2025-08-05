import statistics
import streamlit as st
import traceback
import os
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

def check_password_for_protected_views(view_name):
    """Función para verificar contraseña solo para vistas protegidas"""
    # Definir vistas que requieren contraseña
    protected_views = ["Análisis Mensual", "Estadísticas Generales", "Estadísticas Semanales"]
    
    # Si la vista no está protegida, permitir acceso
    if view_name not in protected_views:
        return True
    
    def password_entered():
        """Verifica si la contraseña ingresada es correcta"""
        correct_password = os.getenv('DASHBOARD_PASSWORD', 'admin123')  # Contraseña por defecto
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown(f"### 🔐 Acceso Restringido - {view_name}")
        st.text_input(
            f"Ingrese la contraseña para acceder a '{view_name}'", 
            type="password", 
            on_change=password_entered, 
            key="password",
            placeholder="Contraseña..."
        )
        st.info("💡 Esta vista requiere autenticación. Contacte al administrador si no tiene acceso.")
        st.info("ℹ️ Puede acceder libremente al 'Mapa de Calor' sin contraseña.")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown(f"### 🔐 Acceso Restringido - {view_name}")
        st.text_input(
            f"Ingrese la contraseña para acceder a '{view_name}'", 
            type="password", 
            on_change=password_entered, 
            key="password",
            placeholder="Contraseña..."
        )
        st.error("❌ Contraseña incorrecta. Intente nuevamente.")
        return False
    else:
        return True

def main():
    """Función principal de la aplicación"""
    try:
        # CSS para ocultar elementos de GitHub y Streamlit
        hide_streamlit_style = """
            <style>
            /* Ocultar botón Fork y elementos de GitHub */
            .viewerBadge_container__1QSob,
            .styles_viewerBadge__1yB5_,
            .viewerBadge_link__1S137,
            .viewerBadge_text__1JaDK {
                display: none !important;
            }
            
            /* Ocultar elementos que contengan "Fork" o "GitHub" */
            [title*="Fork"], 
            [aria-label*="Fork"],
            [alt*="Fork"],
            [title*="GitHub"],
            [aria-label*="GitHub"],
            [alt*="GitHub"] {
                display: none !important;
                visibility: hidden !important;
            }
            
           
            </style>
        """
        st.markdown(hide_streamlit_style, unsafe_allow_html=True)
        
        st.sidebar.title("Menú Principal")
        
        # Selector de vista
        app_mode = st.sidebar.selectbox(
            "Seleccione el dashboard", 
            ["Mapa de Calor", "Análisis Mensual", "Estadísticas Generales", "Estadísticas Semanales"]
        )
        
        # Mostrar estado de autenticación en sidebar
        protected_views = ["Análisis Mensual", "Estadísticas Generales", "Estadísticas Semanales"]
        if app_mode in protected_views:
            if "password_correct" in st.session_state and st.session_state["password_correct"]:
                st.sidebar.success("✅ Sesión activa")
                if st.sidebar.button("🚪 Cerrar Sesión"):
                    st.session_state["password_correct"] = False
                    st.rerun()
            else:
                st.sidebar.warning("🔒 Vista protegida")
        else:
            st.sidebar.info("🌍 Vista pública")
        
        # Verificar autenticación para vistas protegidas
        if not check_password_for_protected_views(app_mode):
            st.stop()
        
        # Renderizar vista seleccionada
        if app_mode == "Mapa de Calor":
            map_view = MapView()
            map_view.render()
        elif app_mode == "Análisis Mensual":
            monthly_view = MonthlyAnalysisView()
            monthly_view.render()
        elif app_mode == "Estadísticas Generales":
            general_view = GeneralDashboardView()
            general_view.render()
        elif app_mode == "Estadísticas Semanales":
            statistic_view = StaticAnalysisView()
            statistic_view.render()
        
            
    except Exception as e:
        st.error("❌ Error en la aplicación")
        st.error(f"Detalles: {str(e)}")
        
        # Mostrar traceback completo en desarrollo
        if st.checkbox("Mostrar detalles técnicos"):
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
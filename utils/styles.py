import streamlit as st

def hide_streamlit_elements():
    """
    Oculta todos los elementos predeterminados de Streamlit para una apariencia profesional
    """
    hide_streamlit_style = """
    <style>
    /* Ocultar el menú principal de Streamlit */
    #MainMenu {visibility: hidden;}
    
    /* Ocultar el footer "Made with Streamlit" */
    footer {visibility: hidden;}
    
    /* Ocultar el header de Streamlit */
    header {visibility: hidden;}
    
    /* Ocultar el botón de deploy */
    .stDeployButton {display: none;}
    
    /* Ocultar toda la barra superior incluyendo FORK y Git */
    .stAppHeader {display: none !important;}
    
    /* Ocultar el toolbar completo */
    .stToolbar {display: none !important;}
    
    /* Ocultar el botón de GitHub/Fork específicamente */
    .stAppToolbar {display: none !important;}
    
    /* Ocultar cualquier elemento con el texto "Fork" */
    [data-testid="stToolbar"] {display: none !important;}
    
    /* Ocultar el menú de configuración */
    .stActionButton {display: none !important;}
    
    /* Ocultar el botón de pantalla completa */
    .stFullScreenFrame {display: none !important;}
    
    /* Ocultar el corner de GitHub */
    .github-corner {display: none !important;}
    
    /* Ocultar cualquier iframe que contenga elementos de GitHub */
    iframe[src*="github"] {display: none !important;}
    
    /* Ocultar elementos específicos de Streamlit Cloud */
    .stAppViewContainer > .main > div[data-testid="stToolbar"] {display: none !important;}
    
    /* Ocultar la barra de herramientas superior completa */
    .stApp > header {display: none !important;}
    
    /* Ocultar cualquier elemento flotante de GitHub */
    .github-fork-ribbon {display: none !important;}
    
    /* Ocultar botones de acción en la esquina */
    .stAppViewBlockContainer .stActionButton {display: none !important;}
    
    /* Estilo adicional para asegurar que no aparezcan elementos flotantes */
    .stApp {
        margin-top: -80px;
    }
    
    /* Ocultar cualquier elemento con atributos relacionados a GitHub */
    [href*="github.com"] {display: none !important;}
    [title*="Fork"] {display: none !important;}
    [title*="GitHub"] {display: none !important;}
    
    /* Ocultar elementos específicos de Streamlit Cloud hosting */
    .stAppViewContainer .stToolbar {display: none !important;}
    .stAppViewContainer .stActionButton {display: none !important;}
    
    /* Asegurar que el contenido principal ocupe todo el espacio */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def apply_custom_theme():
    """
    Aplica un tema personalizado profesional
    """
    custom_theme = """
    <style>
    /* Variables CSS personalizadas */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --background-color: #ffffff;
        --text-color: #262730;
        --border-color: #e6e9ef;
    }
    
    /* Estilo del sidebar */
    .css-1d391kg {
        background-color: #f8f9fa;
        border-right: 1px solid var(--border-color);
    }
    
    /* Estilo del contenido principal */
    .main {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    /* Estilo de títulos */
    .stTitle {
        color: var(--primary-color);
        font-weight: 700;
        margin-bottom: 1.5rem;
    }
    
    /* Estilo de subtítulos */
    .stSubheader {
        color: var(--text-color);
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    /* Estilo de métricas */
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
        margin-bottom: 1rem;
    }
    
    /* Estilo de gráficos */
    .stPlotlyChart {
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 0.5rem;
        background-color: white;
    }
    
    /* Estilo de selectbox */
    .stSelectbox > div > div {
        border: 1px solid var(--border-color);
        border-radius: 4px;
    }
    
    /* Estilo de botones */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #1565c0;
        transform: translateY(-1px);
    }
    
    /* Estilo de dataframes */
    .stDataFrame {
        border: 1px solid var(--border-color);
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Ocultar elementos específicos de Streamlit Cloud */
    .stAppViewContainer > .main > div[data-testid="stToolbar"] {
        display: none !important;
    }
    
    /* Asegurar que no hay espacios en blanco arriba */
    .stAppViewContainer {
        padding-top: 0 !important;
    }
    </style>
    """
    st.markdown(custom_theme, unsafe_allow_html=True)

def add_custom_footer():
    """
    Añade un footer personalizado profesional
    """
    footer = """
    <style>
    .custom-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f8f9fa;
        color: #6c757d;
        text-align: center;
        padding: 10px 0;
        border-top: 1px solid #e6e9ef;
        font-size: 12px;
        z-index: 999;
    }
    
    /* Añadir espacio al contenido principal para el footer */
    .main {
        margin-bottom: 60px;
    }
    </style>
    <div class="custom-footer">
        <p>© 2024 Dashboard Profesional - Análisis de Datos</p>
    </div>
    """
    st.markdown(footer, unsafe_allow_html=True)

def hide_streamlit_cloud_elements():
    """
    Oculta elementos específicos que aparecen en Streamlit Cloud
    """
    cloud_hide_style = """
    <style>
    /* Ocultar elementos específicos de Streamlit Cloud */
    .stAppViewContainer .stToolbar,
    .stAppViewContainer .stActionButton,
    .stAppViewContainer [data-testid="stToolbar"],
    .stApp > header,
    .stAppHeader,
    .stAppToolbar,
    [data-testid="stAppViewBlockContainer"] .stActionButton,
    .github-corner,
    .github-fork-ribbon,
    [href*="github.com"],
    [title*="Fork"],
    [title*="GitHub"],
    iframe[src*="github"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0 !important;
        width: 0 !important;
        position: absolute !important;
        left: -9999px !important;
    }
    
    /* Forzar que el contenido principal empiece desde arriba */
    .stAppViewContainer {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    .main {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Ocultar cualquier elemento flotante */
    .stApp::before,
    .stApp::after {
        display: none !important;
    }
    </style>
    """
    st.markdown(cloud_hide_style, unsafe_allow_html=True)

def apply_professional_styling():
    """
    Aplica todos los estilos profesionales de una vez
    """
    hide_streamlit_elements()
    apply_custom_theme()
    hide_streamlit_cloud_elements()
    add_custom_footer()
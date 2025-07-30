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

def hide_specific_elements():
    """
    Oculta solo los elementos específicos: FORK, Git logo y menú
    """
    hide_style = """
    <style>
    /* Ocultar el botón FORK */
    [data-testid="stToolbar"] {display: none !important;}
    .stAppToolbar {display: none !important;}

    /* Ocultar logo de Git/GitHub */
    .github-corner {display: none !important;}
    [href*="github.com"] {display: none !important;}
    [title*="Fork"] {display: none !important;}
    [title*="GitHub"] {display: none !important;}

    /* Ocultar el menú principal */
    #MainMenu {visibility: hidden;}

    /* Ocultar la barra superior completa */
    .stAppHeader {display: none !important;}
    .stApp > header {display: none !important;}
    </style>
    """
    st.markdown(hide_style, unsafe_allow_html=True)

def apply_professional_styling():
    """
    Aplica todos los estilos profesionales de una vez
    """
    hide_streamlit_elements()

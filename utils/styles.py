"""
Utilidades de Estilos
====================

Este módulo contiene funciones para aplicar estilos CSS personalizados
a la aplicación Streamlit, mejorando la apariencia y experiencia de usuario.

Funcionalidades principales:
- Ocultación de elementos específicos de Streamlit
- Aplicación de estilos profesionales
- Personalización de la interfaz de usuario
- Mejora de la presentación visual

Las funciones utilizan CSS inyectado a través de st.markdown para
modificar la apariencia de elementos específicos de la interfaz.
"""

import streamlit as st

def hide_specific_elements():
    """
    Ocultar elementos específicos de la interfaz de Streamlit.
    
    Aplica CSS personalizado para ocultar elementos no deseados como
    botones de fork, logos de GitHub y otros elementos de la interfaz
    que no son relevantes para la aplicación de negocio.
    
    Esta función mejora la apariencia profesional de la aplicación
    removiendo elementos que pueden distraer al usuario final.
    """
    # CSS personalizado para ocultar elementos específicos
    hide_style = """
    <style>
    /* Ocultar el botón FORK de GitHub */
    /* Ocultar logo de Git/GitHub y elementos relacionados */
    .github-corner {display: none !important;}
    [href*="github.com"] {display: none !important;}
    [title*="Fork"] {display: none !important;}
    [title*="GitHub"] {display: none !important;}

    </style>
    """
    # Inyectar CSS en la aplicación
    st.markdown(hide_style, unsafe_allow_html=True)
 
def apply_professional_styling():
    """
    Aplicar todos los estilos profesionales de manera centralizada.
    
    Función principal que aplica todos los estilos necesarios para
    dar una apariencia profesional a la aplicación. Actualmente
    llama a hide_streamlit_elements() pero puede expandirse para
    incluir más personalizaciones de estilo.
    
    Esta función debe llamarse una vez al inicio de la aplicación
    para asegurar que todos los estilos se apliquen correctamente.
    """
    # Aplicar función de ocultación de elementos (nota: función no definida en el código actual)
    hide_streamlit_elements()

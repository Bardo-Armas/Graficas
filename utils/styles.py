import streamlit as st

def hide_specific_elements():
    """
    Oculta solo los elementos específicos: FORK, Git logo y menú
    """
    hide_style = """
    <style>
    /* Ocultar el botón FORK */
    /* Ocultar logo de Git/GitHub */
    .github-corner {display: none !important;}
    [href*="github.com"] {display: none !important;}
    [title*="Fork"] {display: none !important;}
    [title*="GitHub"] {display: none !important;}

    </style>
    """
    st.markdown(hide_style, unsafe_allow_html=True)
 
def apply_professional_styling():
    """
    Aplica todos los estilos profesionales de una vez
    """
    hide_streamlit_elements()

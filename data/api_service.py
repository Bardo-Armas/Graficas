import requests
import streamlit as st
from utils.error_handler import handle_errors

class APIService:
    def __init__(self):
        self.base_url = "https://da-pw.mx/api/apprisa-panel"
    
    @handle_errors
    @st.cache_data(ttl=300)  # Cache por 5 minutos
    def get_daily_orders_data(_self, fecha_inicio, fecha_fin):
        """Obtener datos de pedidos diarios desde la API"""
        url = f"{_self.base_url}/reportePedidosDiarios"
        params = {
            'fecha_inicio': str(fecha_inicio), 
            'fecha_fin': str(fecha_fin)
        }
        
        try:
            response = requests.post(url, json=params, timeout=120)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success', False):
                return data
            else:
                st.warning("La API no devolvió datos exitosos")
                return None
                
        except requests.exceptions.Timeout:
            st.error("⏱️ Timeout: La API tardó demasiado en responder")
            return None
        except requests.exceptions.ConnectionError:
            st.error("🌐 Error de conexión: No se pudo conectar a la API")
            return None
        except requests.exceptions.HTTPError as e:
            st.error(f"🚫 Error HTTP: {e.response.status_code}")
            return None
        except Exception as e:
            st.error(f"❌ Error inesperado en la API: {str(e)}")
            return None
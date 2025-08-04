import streamlit as st
import pandas as pd
import folium
from folium.plugins import Fullscreen
from streamlit_folium import folium_static
from data.database_service import DatabaseService
from sqlalchemy import text

class MapView:
    """Vista para el mapa de calor de pedidos"""
    
    def __init__(self):
        """Inicializar la vista del mapa"""
        self.db_service = DatabaseService()
    
    @st.cache_data
    def _get_map_data(_self):
        """
        Obtener datos geográficos para el mapa de calor.
        
        Returns:
            pd.DataFrame: DataFrame con coordenadas de clientes
        """
        query = """
        SELECT 
            ISNULL(tac.latitude,ads.ad_latitude) as latitude_client,
            ISNULL(tac.longitude,ads.ad_longitude) as longitude_client
        FROM tbl_orders as tbo
        INNER JOIN tbl_restaurants as tr on tr.id_restaurant = tbo.restaurant
        LEFT OUTER JOIN tbl_address_client as tac on tac.id_address = tbo.id_address
        left outer JOIN addresses ads on tbo.addresses_id = ads.ad_id
        WHERE tbo.[status] not in (39)
        AND tr.id_restaurant NOT IN (205, 234, 102, 10294)
        """
        
        try:
            # Usar el mismo patrón que DatabaseService
            engine = _self.db_service.db_config.get_engine()
            df = pd.read_sql(text(query), engine)
            engine.dispose()
            
            # Convertir a numérico y limpiar datos
            df['latitude_client'] = pd.to_numeric(df['latitude_client'], errors='coerce')
            df['longitude_client'] = pd.to_numeric(df['longitude_client'], errors='coerce')
            
            return df.dropna(subset=['latitude_client', 'longitude_client'])
        except Exception as e:
            st.error(f"Error al obtener datos: {str(e)}")
            return pd.DataFrame()
    
    def _create_heat_map(self, df):
        """
        Crear mapa de calor con los datos geográficos.
        
        Args:
            df (pd.DataFrame): DataFrame con coordenadas
            
        Returns:
            folium.Map: Mapa de calor configurado
        """
        # Crear mapa centrado en el promedio de coordenadas
        m = folium.Map(
            location=[df['latitude_client'].mean(), df['longitude_client'].mean()],
            zoom_start=12,
            control_scale=True,
            tiles=None
        )
        
        # Agregar capas de tiles
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google Satellite',
            name='Google Satellite',
            overlay=True,
            control=True
        ).add_to(m)
        
        folium.TileLayer('OpenStreetMap').add_to(m)
        
        # Configurar tamaño de celda para el grid
        cell_size = 0.01
        
        # Crear grid y contar puntos por celda
        df['lat_grid'] = (df['latitude_client'] // cell_size) * cell_size
        df['lon_grid'] = (df['longitude_client'] // cell_size) * cell_size
        grid_counts = df.groupby(['lat_grid', 'lon_grid']).size().reset_index(name='count')
        
        # Definir colores para diferentes densidades
        color_map = {
            'yellow': (0.5, 0.5, 0.0, 0.7),
            'orange': (0.8, 0.4, 0.0, 0.7),
            'red': (0.8, 0.0, 0.0, 0.7)
        }
        
        def get_color_str(rgba_tuple):
            """Convertir tupla RGBA a string CSS"""
            return f'rgba({int(rgba_tuple[0]*255)}, {int(rgba_tuple[1]*255)}, {int(rgba_tuple[2]*255)}, {rgba_tuple[3]})'
        
        # Agregar rectángulos de calor al mapa
        for _, row in grid_counts.iterrows():
            lat, lon, count = row['lat_grid'], row['lon_grid'], row['count']
            
            # Determinar color basado en densidad
            if count > 50:
                color = color_map['red']
            elif count > 20:
                color = color_map['orange']
            else:
                color = color_map['yellow']
            
            # Definir límites del rectángulo
            bounds = [
                (lat, lon), 
                (lat + cell_size, lon + cell_size)
            ]
            
            # Agregar rectángulo al mapa
            folium.Rectangle(
                bounds=bounds,
                color=None,
                fill=True,
                fill_color=get_color_str(color),
                fill_opacity=color[3],
                weight=0,
                tooltip=f'Conteo: {count}'
            ).add_to(m)
        
        # Agregar controles
        folium.LayerControl().add_to(m)
        
        Fullscreen(
            position="topright",
            title="Pantalla completa",
            title_cancel="Salir de pantalla completa",
            force_separate_button=True
        ).add_to(m)
        
        return m
    
    def _render_statistics(self, df):
        """
        Renderizar estadísticas del mapa.
        
        Args:
            df (pd.DataFrame): DataFrame con datos geográficos
        """
        if not df.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Puntos", len(df))
            
            with col2:
                st.metric("Latitud Promedio", f"{df['latitude_client'].mean():.6f}")
            
            with col3:
                st.metric("Longitud Promedio", f"{df['longitude_client'].mean():.6f}")
            
            with col4:
                # Calcular área aproximada cubierta
                lat_range = df['latitude_client'].max() - df['latitude_client'].min()
                lon_range = df['longitude_client'].max() - df['longitude_client'].min()
                st.metric("Área Cubierta", f"{lat_range:.3f}° x {lon_range:.3f}°")
    
    def render(self):
        """Renderizar la vista completa del mapa"""
        # Aplicar estilos CSS mejorados para centrar el mapa
        centered_map_style = """
            <style>
            /* Ocultar elementos de Streamlit */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* Configuración del contenedor principal */
            .appview-container .main .block-container {
                padding-top: 1rem;
                padding-left: 1rem;
                padding-right: 1rem;
                max-width: 100%;
            }
            
            /* Centrar el contenido */
            .st-emotion-cache-z5fcl4 {
                padding: 0px;
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            
            /* Estilo para el título */
            .map-title {
                text-align: center;
                color: #1f77b4;
                font-size: 2.5rem;
                font-weight: bold;
                margin-bottom: 1rem;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            }
            
            /* Contenedor de la leyenda centrado */
            .legend-container {
                display: flex;
                justify-content: center;
                margin: 1rem 0;
                gap: 1rem;
                flex-wrap: wrap;
            }
            
            /* Contenedor del mapa centrado */
            .map-container {
                display: flex;
                justify-content: center;
                align-items: center;
                width: 100%;
                margin: 1rem 0;
            }
            
            /* Estilo para el mapa */
            .stHtml > div {
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            /* Responsive design */
            @media (max-width: 768px) {
                .map-title {
                    font-size: 2rem;
                }
                .legend-container {
                    flex-direction: column;
                    align-items: center;
                }
            }
            </style>
        """
        st.markdown(centered_map_style, unsafe_allow_html=True)
        
        # Título principal centrado con mejor estilo
        st.markdown("<h1 class='map-title'>🗺️ Mapa de Calor de Pedidos</h1>", unsafe_allow_html=True)
        
        # Obtener datos
        df = self._get_map_data()
        
        if not df.empty:
            # Renderizar leyenda centrada
            st.markdown("<div class='legend-container'>", unsafe_allow_html=True)
            self._render_legend()
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Contenedor centrado para el mapa
            st.markdown("<div class='map-container'>", unsafe_allow_html=True)
            
            # Crear y mostrar mapa
            mapa = self._create_heat_map(df)
            
            # Usar columnas para centrar mejor el mapa
            col1, col2, col3 = st.columns([1, 8, 1])
            with col2:
                folium_static(mapa, height=600, width=None)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Información adicional centrada
            col1, col2, col3 = st.columns([1, 6, 1])
            with col2:
                with st.expander("ℹ️ Información del Mapa", expanded=False):
                    st.write("""
                    **Descripción del Mapa de Calor:**
                    - Cada celda representa un área geográfica de aproximadamente 1.1 km²
                    - Los colores indican la densidad de pedidos en cada área
                    - Puedes cambiar entre vista satelital y OpenStreetMap
                    - Usa el botón de pantalla completa para una mejor visualización
                    - Pasa el cursor sobre las celdas para ver el conteo exacto
                    """)
                    
                    st.write(f"**Datos procesados:** {len(df):,} ubicaciones de pedidos")
                
        else:
            # Mensajes de error también centrados
            col1, col2, col3 = st.columns([1, 4, 1])
            with col2:
                st.warning("⚠️ No se encontraron datos geográficos para mostrar el mapa")
                st.info("🔍 Verifica la conexión a la base de datos y que existan pedidos con coordenadas válidas.")
    
    def _render_legend(self):
        """Renderizar leyenda del mapa de calor centrada"""
        st.markdown("<h3 style='text-align: center; margin-bottom: 1rem;'>Leyenda del Mapa de Calor</h3>", unsafe_allow_html=True)
        
        # Usar columnas para centrar la leyenda
        col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 1])
        
        with col2:
            st.markdown("""
            <div style='background-color: rgba(127, 127, 0, 0.7); padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <strong style='color: white; font-size: 1.1rem;'>🟡 Densidad Baja</strong><br>
                <span style='color: white;'>1-20 pedidos</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style='background-color: rgba(204, 102, 0, 0.7); padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <strong style='color: white; font-size: 1.1rem;'>🟠 Densidad Media</strong><br>
                <span style='color: white;'>21-50 pedidos</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div style='background-color: rgba(204, 0, 0, 0.7); padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <strong style='color: white; font-size: 1.1rem;'>🔴 Densidad Alta</strong><br>
                <span style='color: white;'>50+ pedidos</span>
            </div>
            """, unsafe_allow_html=True)
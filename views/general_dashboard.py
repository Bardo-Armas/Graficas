"""
Vista del Dashboard General
==========================

Este módulo contiene la clase GeneralDashboardView que maneja la interfaz principal
del dashboard de estadísticas generales de la aplicación. Proporciona una vista
completa de los datos de pedidos y establecimientos con múltiples pestañas de análisis.

Características principales:
- Dashboard principal con múltiples pestañas de análisis
- Visualización de top establecimientos
- Análisis de pedidos por hora y concurrencias
- Controles de fecha en sidebar
- Descarga de datos en formato CSV
- Procesamiento concurrente para mejor rendimiento
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from data.database_service import DatabaseService
from data.data_processor import DataProcessor
from utils.chart_utils import ChartUtils
from utils.error_handler import handle_errors, validate_date_range
from utils.date_utils import DateUtils
from config.settings import AppSettings

class GeneralDashboardView:
    """
    Vista principal del dashboard de estadísticas generales.
    
    Esta clase maneja la renderización del dashboard principal que incluye:
    - Gráficas principales con resumen de datos
    - Top 10 establecimientos más activos
    - Análisis de establecimientos y pedidos por día
    - Distribución de pedidos por hora
    - Análisis de concurrencias de pedidos
    
    Attributes:
        db_service (DatabaseService): Servicio para acceso a datos
        data_processor (DataProcessor): Procesador de datos estadísticos
        chart_utils (ChartUtils): Utilidades para creación de gráficos
        date_utils (DateUtils): Utilidades para manejo de fechas
        fecha_inicio (date): Fecha de inicio del rango de análisis
        fecha_fin (date): Fecha de fin del rango de análisis
    """
    
    def __init__(self):
        """
        Inicializar la vista del dashboard general.
        
        Configura todos los servicios necesarios para el funcionamiento
        del dashboard, incluyendo acceso a datos, procesamiento y visualización.
        """
        self.db_service = DatabaseService()
        self.data_processor = DataProcessor()
        self.chart_utils = ChartUtils()
        self.date_utils = DateUtils()
    
    @handle_errors
    def render(self):
        """
        Renderizar la vista completa del dashboard general.
        
        Método principal que coordina la renderización de todos los componentes
        del dashboard, incluyendo título, controles de fecha y pestañas de análisis.
        Incluye manejo automático de errores y validación de fechas.
        """
        st.title("📈 Dashboard de Estadísticas Generales")
        
        # Configurar fechas por defecto (últimos 30 días)
        hoy = datetime.now().date()
        ayer = hoy - timedelta(days=1)
        fecha_inicio_default = hoy - timedelta(days=30)
        
        # Sidebar para controles de fecha
        self._render_sidebar(fecha_inicio_default, hoy)
        
        # Validar que el rango de fechas sea válido
        if not validate_date_range(self.fecha_inicio, self.fecha_fin):
            st.stop()
        
        # Renderizar pestañas principales del dashboard
        self._render_tabs(ayer)
    
    def _render_sidebar(self, fecha_inicio_default, hoy):
        """
        Renderizar sidebar con controles de fecha y actualización.
        
        Crea los controles en el sidebar para selección de rango de fechas
        y botón de actualización de datos con limpieza de caché.
        
        Args:
            fecha_inicio_default (date): Fecha de inicio por defecto
            hoy (date): Fecha actual para límite superior
        """
        with st.sidebar:
            st.header("Fechas")
            # Control de fecha de inicio
            self.fecha_inicio = st.date_input("Desde", value=fecha_inicio_default)
            # Control de fecha de fin
            self.fecha_fin = st.date_input("Hasta", value=hoy)
            
            # Botón para forzar actualización de datos
            if st.button("Actualizar Datos"):
                st.cache_data.clear()
    
    def _render_tabs(self, ayer):
        """
        Renderizar las pestañas principales del dashboard.
        
        Crea y organiza las cinco pestañas principales del dashboard:
        1. Gráficas Principales - Resumen visual de todos los datos
        2. Top 10 Establecimientos - Ranking de establecimientos más activos
        3. Establecimientos y Pedidos - Análisis temporal diario
        4. Pedidos por Hora - Distribución horaria de pedidos
        5. Concurrencias - Análisis de pedidos simultáneos
        
        Args:
            ayer (date): Fecha de ayer para análisis de datos recientes
        """
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Gráficas Principales", "Top 10 Establecimientos", "Establecimientos y Pedidos", 
            "Pedidos por Hora", "Concurrencias"
        ])
        
        with tab1:
            self._render_main_charts_tab(ayer)
        
        with tab2:
            self._render_top_establishments_tab()
        
        with tab3:
            self._render_establishments_orders_tab()
        
        with tab4:
            self._render_hourly_orders_tab(ayer)
        
        with tab5:
            self._render_concurrency_tab(ayer)
        
    
    def _render_main_charts_tab(self, ayer):
        """
        Renderizar pestaña de gráficas principales.
        
        Muestra un resumen visual de todos los datos principales en una vista
        consolidada con cuatro gráficos distribuidos en dos columnas:
        - Top establecimientos y concurrencias (columna izquierda)
        - Establecimientos vs pedidos y pedidos por hora (columna derecha)
        
        Utiliza ThreadPoolExecutor para carga concurrente de datos y mejora
        del rendimiento en la obtención de información de la base de datos.
        
        Args:
            ayer (date): Fecha de referencia para análisis de datos recientes
        """
        # Carga concurrente de datos para mejor rendimiento
        with ThreadPoolExecutor() as executor:
            future_estadistica = executor.submit(
                self.db_service.get_orders_data, 
                self.fecha_inicio, 
                self.fecha_fin
            )
            data_estadistica = future_estadistica.result()
        
        if data_estadistica:
            # Procesar todos los tipos de datos necesarios
            top_10 = self.data_processor.process_top_establishments(data_estadistica)
            df_establecimientospedidos = self.data_processor.process_establishments_orders(data_estadistica)
            contador_horas = self.data_processor.process_hourly_orders(data_estadistica, ayer)
            
            # Procesar datos de concurrencias
            df_estadistica_general = pd.DataFrame(data_estadistica["data"]["detalle"]["general"]["todos"])
            resultado_concurrencia = self.data_processor.process_concurrency(df_estadistica_general, ayer)
            
            # Organizar gráficos en dos columnas para mejor visualización
            col1, col2 = st.columns(2)
            
            # Columna izquierda: Top establecimientos y concurrencias
            with col1:
                if not top_10.empty:
                    fig1 = self.chart_utils.create_top_establishments_chart(
                        top_10, self.fecha_inicio, self.fecha_fin
                    )
                    if fig1:
                        st.plotly_chart(fig1, use_container_width=True, key="grafico_top_establecimientos_tab1")
                
                if resultado_concurrencia[0] is not None:
                    fig4, _, _, _, _ = resultado_concurrencia
                    st.plotly_chart(fig4, use_container_width=True, key="grafico_concurrencia_tab1")
            
            # Columna derecha: Establecimientos vs pedidos y pedidos por hora
            with col2:
                if not df_establecimientospedidos.empty:
                    fig2 = self.chart_utils.create_establishments_orders_chart(
                        df_establecimientospedidos, self.fecha_inicio, self.fecha_fin
                    )
                    if fig2:
                        st.plotly_chart(fig2, use_container_width=True, key="grafico_establecimientos_pedidos_tab1")
                
                if not contador_horas.empty:
                    fig3 = self.chart_utils.create_hourly_orders_chart(contador_horas, ayer)
                    if fig3:
                        st.plotly_chart(fig3, use_container_width=True, key="grafico_pedidos_hora_tab1")
        else:
            st.warning("No se pudieron cargar todos los datos para mostrar las gráficas")
    
    def _render_top_establishments_tab(self):
        """
        Renderizar pestaña de top 10 establecimientos.
        
        Muestra un análisis detallado de los establecimientos más activos
        en el período seleccionado, incluyendo:
        - Métricas principales (total establecimientos y pedidos)
        - Gráfico de pastel con distribución de pedidos
        - Tabla detallada con datos de cada establecimiento
        - Opción de descarga en formato CSV
        
        Los datos se ordenan por número total de pedidos en orden descendente.
        """
        data_estadistica = self.db_service.get_orders_data(self.fecha_inicio, self.fecha_fin)
        
        if data_estadistica:
            top_10 = self.data_processor.process_top_establishments(data_estadistica)
            
            if not top_10.empty:
                # Métricas principales del top 10
                col1, col2 = st.columns(2)
                col1.metric("Total de Establecimientos", len(top_10))
                col2.metric("Pedidos Totales", int(top_10["total_pedidos"].sum()))
                
                # Gráfico de pastel para visualización de distribución
                fig = self.chart_utils.create_top_establishments_chart(
                    top_10, self.fecha_inicio, self.fecha_fin
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key="grafico_top_establecimientos_tab2")
                
                # Tabla interactiva con datos detallados
                st.dataframe(
                    top_10, 
                    column_config={
                        "name_restaurant": "Establecimiento", 
                        "total_pedidos": st.column_config.NumberColumn("Pedidos", format="%d")
                    }, 
                    hide_index=True, 
                    use_container_width=True
                )
                
                # Funcionalidad de descarga de datos
                csv = top_10.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📊 Descargar CSV", 
                    data=csv, 
                    file_name=f"top_establecimientos_{self.fecha_inicio}_{self.fecha_fin}.csv", 
                    mime="text/csv"
                )
            else:
                st.warning("No hay suficientes datos para mostrar el top 10 establecimientos")
        else:
            st.warning("No se encontraron datos para las fechas seleccionadas")
    
    def _render_establishments_orders_tab(self):
        """
        Renderizar pestaña de análisis de establecimientos y pedidos.
        
        Proporciona un análisis temporal detallado de la relación entre
        establecimientos activos y pedidos realizados por día, incluyendo:
        - Resumen estadístico con promedios y ratios
        - Gráfico de dispersión mostrando correlación temporal
        - Tabla con datos diarios ordenados cronológicamente
        - Descarga de datos para análisis posterior
        
        Calcula automáticamente el ratio pedidos/establecimientos para
        identificar eficiencia operativa por día.
        """
        data_estadistica = self.db_service.get_orders_data(self.fecha_inicio, self.fecha_fin)
        
        if data_estadistica:
            df_establecimientospedidos = self.data_processor.process_establishments_orders(data_estadistica)
            
            if not df_establecimientospedidos.empty:
                # Resumen estadístico con métricas clave
                st.subheader("Resumen Estadístico")
                col1, col2, col3 = st.columns(3)
                col1.metric("Establecimientos Activos Promedio", f"{df_establecimientospedidos['Establecimientos'].mean():.0f}")
                col2.metric("Pedidos (promedio)", f"{df_establecimientospedidos['Pedidos'].mean():.0f}")
                col3.metric("Ratio Pedidos/Establecimientos", f"{df_establecimientospedidos['Promedio'].mean():.2f}")
                
                # Gráfico de dispersión para análisis de correlación
                fig = self.chart_utils.create_establishments_orders_chart(
                    df_establecimientospedidos, self.fecha_inicio, self.fecha_fin
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key="grafico_establecimientos_pedidos_tab3")
                
                # Tabla con datos diarios ordenados cronológicamente
                st.dataframe(
                    df_establecimientospedidos[["Fecha", "Establecimientos", "Pedidos", "Promedio"]].sort_values("Fecha", ascending=True), 
                    column_config={
                        "Fecha": st.column_config.DateColumn("Fecha"), 
                        "Establecimientos": st.column_config.NumberColumn("Establecimientos"), 
                        "Pedidos": st.column_config.NumberColumn("Pedidos"), 
                        "Promedio": st.column_config.NumberColumn("Promedio", format="%.2f")
                    }, 
                    hide_index=True, 
                    use_container_width=True
                )
                            # Botón de descarga
                csv = df_establecimientospedidos.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📊 Descargar CSV", 
                    data=csv, 
                    file_name=f"establecimientos_pedidos_{self.fecha_inicio}_{self.fecha_fin}.csv", 
                    mime="text/csv"
                )
            else:
                st.warning("No hay datos de establecimientos y pedidos disponibles")
        else:
            st.warning("No se obtuvieron valores de la API")
    
    def _render_hourly_orders_tab(self, ayer):
        """Renderizar tab de pedidos por hora"""
        fecha_hora = st.date_input("Fecha", value=ayer, key="tab4_fecha")
        data_hora = self.db_service.get_orders_data(self.fecha_inicio, self.fecha_fin)
        
        if data_hora is not None:
            contador_horas = self.data_processor.process_hourly_orders(data_hora, fecha_hora)
            
            if not contador_horas.empty:
                # Métricas
                total_pedidos = contador_horas["pedidos"].sum()
                hora_pico = contador_horas.loc[contador_horas["pedidos"].idxmax()]
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Fecha", fecha_hora.strftime("%Y-%m-%d"))
                col2.metric("Total de Pedidos", total_pedidos)
                col3.metric("Hora Pico", f"{hora_pico['etiqueta_hora']}", f"{hora_pico['pedidos']} pedidos")
                
                # Gráfico
                fig = self.chart_utils.create_hourly_orders_chart(contador_horas, fecha_hora)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key="grafico_pedidos_hora_tab4")
                
                # Tabla de datos
                st.dataframe(
                    contador_horas[["etiqueta_hora", "pedidos"]].rename(columns={"etiqueta_hora": "Hora", "pedidos": "Pedidos"}), 
                    hide_index=True, 
                    use_container_width=True
                )
                
                # Botón de descarga
                csv = contador_horas[["etiqueta_hora", "pedidos"]].to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📊 Descargar CSV", 
                    data=csv, 
                    file_name=f"pedidos_hora_{fecha_hora}.csv", 
                    mime="text/csv"
                )
            else:
                st.warning(f"No hay pedidos registrados para {fecha_hora.strftime('%Y-%m-%d')}")
        else:
            st.warning("No se obtuvieron valores de la API")
    
    def _render_concurrency_tab(self, ayer):
        """Renderizar tab de concurrencias"""
        fecha_concurrencia = st.date_input("Fecha", value=ayer, key="tab5_fecha")
        data_concurrencia = self.db_service.get_orders_data(self.fecha_inicio, self.fecha_fin)
        
        if data_concurrencia is not None:
            df_estadistica = pd.DataFrame(data_concurrencia["data"]["detalle"]["general"]["todos"])
            resultado = self.data_processor.process_concurrency(df_estadistica, fecha_concurrencia)
            
            if resultado[0] is not None:
                fig_concurrencia, max_val, hora_inicio, hora_fin, df_concurrencia = resultado
                
                # Filtrar datos donde Pedidos_Simultaneos > 0
                df_concurrencia = df_concurrencia[df_concurrencia['Pedidos_Simultaneos'] > 0]
                
                # Métricas
                col1, col2 = st.columns(2)
                col1.metric("Máxima Concurrencia", max_val)
                col2.metric("Hora Pico", f"{hora_inicio.strftime('%H:%M')} - {hora_fin.strftime('%H:%M')}")
                
                # Gráfico
                st.plotly_chart(fig_concurrencia, use_container_width=True, key="grafico_concurrencia_tab5")
                
                # Tabla de datos
                st.subheader("Datos de Concurrencia")
                st.dataframe(
                    df_concurrencia, 
                    column_config={
                        "Hora": st.column_config.DatetimeColumn("Hora", format="HH:mm"), 
                        "Pedidos_Simultaneos": st.column_config.NumberColumn("Pedidos Simultáneos")
                    }, 
                    hide_index=True, 
                    use_container_width=True
                )
                
                # Botón de descarga
                csv = df_concurrencia.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📊 Descargar CSV", 
                    data=csv, 
                    file_name=f"concurrencia_{fecha_concurrencia}.csv", 
                    mime="text/csv"
                )
            else:
                st.warning(f"No hay datos para {fecha_concurrencia}")
        else:
            st.warning("No se obtuvieron datos de la API")

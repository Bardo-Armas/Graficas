import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from data.database_service import DatabaseService
from data.api_service import APIService
from data.data_processor import DataProcessor
from utils.chart_utils import ChartUtils
from utils.error_handler import handle_errors, validate_date_range
from utils.date_utils import DateUtils
from config.settings import AppSettings

class GeneralDashboardView:
    def __init__(self):
        self.db_service = DatabaseService()
        self.api_service = APIService()
        self.data_processor = DataProcessor()
        self.chart_utils = ChartUtils()
        self.date_utils = DateUtils()
    
    @handle_errors
    def render(self):
        """Renderizar vista de dashboard general"""
        st.title("📈 Dashboard de Estadísticas Generales")
        
        # Configurar fechas por defecto
        hoy = datetime.now().date()
        ayer = hoy - timedelta(days=1)
        fecha_inicio_default = hoy - timedelta(days=30)
        
        # Sidebar para controles
        self._render_sidebar(fecha_inicio_default, hoy)
        
        # Validar fechas
        if not validate_date_range(self.fecha_inicio, self.fecha_fin):
            st.stop()
        
        # Renderizar tabs
        self._render_tabs(ayer)
    
    def _render_sidebar(self, fecha_inicio_default, hoy):
        """Renderizar sidebar con controles"""
        with st.sidebar:
            st.header("Fechas")
            self.fecha_inicio = st.date_input("Desde", value=fecha_inicio_default)
            self.fecha_fin = st.date_input("Hasta", value=hoy)
            
            if st.button("Actualizar Datos"):
                st.cache_data.clear()
    
    def _render_tabs(self, ayer):
        """Renderizar tabs del dashboard"""
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "Gráficas Principales", "Top 10 Establecimientos", "Establecimientos y Pedidos", 
            "Pedidos por Hora", "Concurrencias", "📦 Pedidos por Semana", "💳 Créditos por Semana"
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
        
        with tab6:
            self._render_weekly_orders_tab()
        
        with tab7:
            self._render_weekly_credits_tab()
    
    def _render_main_charts_tab(self, ayer):
        """Renderizar tab de gráficas principales"""
        with ThreadPoolExecutor() as executor:
            future_estadistica = executor.submit(
                self.db_service.get_orders_data, 
                self.fecha_inicio, 
                self.fecha_fin
            )
            data_estadistica = future_estadistica.result()
        
        if data_estadistica:
            # Procesar datos
            top_10 = self.data_processor.process_top_establishments(data_estadistica)
            df_establecimientospedidos = self.data_processor.process_establishments_orders(data_estadistica)
            contador_horas = self.data_processor.process_hourly_orders(data_estadistica, ayer)
            
            # Procesar concurrencias
            df_estadistica_general = pd.DataFrame(data_estadistica["data"]["detalle"]["general"]["todos"])
            resultado_concurrencia = self.data_processor.process_concurrency(df_estadistica_general, ayer)
            
            # Renderizar gráficos en columnas
            col1, col2 = st.columns(2)
            
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
        """Renderizar tab de top establecimientos"""
        data_estadistica = self.db_service.get_orders_data(self.fecha_inicio, self.fecha_fin)
        
        if data_estadistica:
            top_10 = self.data_processor.process_top_establishments(data_estadistica)
            
            if not top_10.empty:
                # Métricas
                col1, col2 = st.columns(2)
                col1.metric("Total de Establecimientos", len(top_10))
                col2.metric("Pedidos Totales", int(top_10["total_pedidos"].sum()))
                
                # Gráfico
                fig = self.chart_utils.create_top_establishments_chart(
                    top_10, self.fecha_inicio, self.fecha_fin
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key="grafico_top_establecimientos_tab2")
                
                # Tabla de datos
                st.dataframe(
                    top_10, 
                    column_config={
                        "name_restaurant": "Establecimiento", 
                        "total_pedidos": st.column_config.NumberColumn("Pedidos", format="%d")
                    }, 
                    hide_index=True, 
                    use_container_width=True
                )
                
                # Botón de descarga
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
        """Renderizar tab de establecimientos y pedidos"""
        data_estadistica = self.db_service.get_orders_data(self.fecha_inicio, self.fecha_fin)
        
        if data_estadistica:
            df_establecimientospedidos = self.data_processor.process_establishments_orders(data_estadistica)
            
            if not df_establecimientospedidos.empty:
                # Resumen estadístico
                st.subheader("Resumen Estadístico")
                col1, col2, col3 = st.columns(3)
                col1.metric("Establecimientos Activos Promedio", f"{df_establecimientospedidos['Establecimientos'].mean():.0f}")
                col2.metric("Pedidos (promedio)", f"{df_establecimientospedidos['Pedidos'].mean():.0f}")
                col3.metric("Ratio Pedidos/Establecimientos", f"{df_establecimientospedidos['Promedio'].mean():.2f}")
                
                # Gráfico
                fig = self.chart_utils.create_establishments_orders_chart(
                    df_establecimientospedidos, self.fecha_inicio, self.fecha_fin
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key="grafico_establecimientos_pedidos_tab3")
                
                # Tabla de datos
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
    
    def _render_weekly_orders_tab(self):
        """Renderizar tab de pedidos semanales"""
        fecha_actual = datetime.now().date()
        fecha_inicio_sem = AppSettings.DEFAULT_START_DATE
        
        with st.spinner("Obteniendo datos de pedidos..."):
            datos_estadistica_pedidos = self.db_service.get_orders_data(fecha_inicio_sem, fecha_actual)
            
            if datos_estadistica_pedidos and datos_estadistica_pedidos.get("success"):
                pedidos_semanales = self.data_processor.calculate_weekly_data(datos_estadistica_pedidos, "pedidos")
            else:
                st.error("No se pudieron obtener datos de pedidos")
                pedidos_semanales = None
        
        if pedidos_semanales is not None and not pedidos_semanales.empty:
            st.header("Análisis Semanal de Pedidos")
            
            # Métricas
            col1, col2, col3 = st.columns(3)
            total = pedidos_semanales["pedidos_totales"].sum()
            semana_max = pedidos_semanales.loc[pedidos_semanales["pedidos_totales"].idxmax()]
            semana_min = pedidos_semanales.loc[pedidos_semanales["pedidos_totales"].idxmin()]
            
            col1.metric("Pedidos totales", f"{total:,}")
            col2.metric("Semana con más pedidos", f"Semana {semana_max['semana']}", 
                       help=f"{semana_max['rango_fechas']}: {semana_max['pedidos_totales']:,}")
            col3.metric("Semana con menos pedidos", f"Semana {semana_min['semana']}", 
                       help=f"{semana_min['rango_fechas']}: {semana_min['pedidos_totales']:,}")
            
            # Gráfico
            fig = self.chart_utils.create_weekly_chart(pedidos_semanales, "pedidos")
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # Tabla de datos
            st.dataframe(
                pedidos_semanales[["semana", "rango_fechas", "pedidos_totales"]].rename(columns={
                    "semana": "Semana", 
                    "rango_fechas": "Rango", 
                    "pedidos_totales": "Pedidos"
                }), 
                hide_index=True
            )
            
            # Botón de descarga
            csv = pedidos_semanales.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📊 Descargar CSV", 
                data=csv, 
                file_name=f"pedidos_semanales_{fecha_inicio_sem}_{fecha_actual}.csv", 
                mime="text/csv"
            )
        else:
            st.warning("No hay datos de pedidos disponibles")
    
    def _render_weekly_credits_tab(self):
        """Renderizar tab de créditos semanales"""
        fecha_actual = datetime.now().date()
        fecha_inicio_sem = AppSettings.DEFAULT_START_DATE
        
        with st.spinner("Obteniendo datos de créditos y pedidos..."):
            data_creditos_pedidos = self.db_service.get_orders_data(fecha_inicio_sem, fecha_actual)
            
            if data_creditos_pedidos is not None and data_creditos_pedidos.get("success"):
                df_estadistica = pd.DataFrame(data_creditos_pedidos["data"]["detalle"]["general"]["todos"])
                df_estadistica = df_estadistica.dropna(subset=["order_completion_date"])
                
                if not df_estadistica.empty:
                    creditos_semanales = self.data_processor.calculate_weekly_data(data_creditos_pedidos, "creditos")
                    pedidos_semanales_for_credits = self.data_processor.calculate_weekly_data(data_creditos_pedidos, "pedidos")
                    
                    if not creditos_semanales.empty and not pedidos_semanales_for_credits.empty:
                        df_combinado = creditos_semanales.merge(
                            pedidos_semanales_for_credits[["semana", "pedidos_totales"]], 
                            on="semana", 
                            how="left"
                        )
                        df_combinado["creditos_por_pedido"] = df_combinado["creditos_totales"] / df_combinado["pedidos_totales"].replace(0, pd.NA)
                        df_combinado = df_combinado.dropna(subset=["creditos_por_pedido"])
                        
                        if not df_combinado.empty:
                            semana_mas_costosa = df_combinado.loc[df_combinado["creditos_por_pedido"].idxmax()]
                        else:
                            semana_mas_costosa = None
                    else:
                        st.error("No se pudieron obtener datos completos (créditos y pedidos)")
                        df_combinado = None
                else:
                    st.error("No hay datos de estadísticas disponibles para procesar créditos y pedidos.")
                    df_combinado = None
            else:
                st.error("No se pudieron obtener datos de la API para créditos y pedidos.")
                df_combinado = None
        
        if df_combinado is not None and not df_combinado.empty:
            st.header("Análisis Semanal de Créditos")
            
            # Métricas
            col1, col2, col3, col4 = st.columns(4)
            total = df_combinado["creditos_totales"].sum()
            semana_max = df_combinado.loc[df_combinado["creditos_totales"].idxmax()]
            semana_min = df_combinado.loc[df_combinado["creditos_totales"].idxmin()]
            
            col1.metric("Créditos totales", f"{total:,}")
            col2.metric("Semana con más créditos", f"Semana {semana_max['semana']}", 
                       help=f"{semana_max['rango_fechas']}: {semana_max['creditos_totales']:,}")
            col3.metric("Semana con menos créditos", f"Semana {semana_min['semana']}", 
                       help=f"{semana_min['rango_fechas']}: {semana_min['creditos_totales']:,}")
            
            if semana_mas_costosa is not None:
                col4.metric("Semana con envío más costoso", f"Semana {semana_mas_costosa['semana']}", 
                           help=f"{semana_mas_costosa['rango_fechas']}: ${semana_mas_costosa['creditos_por_pedido']:,.2f} por pedido")
            else:
                col4.metric("Semana con envío más costoso", "N/A")
            
            # Gráfico
            fig = self.chart_utils.create_credits_weekly_chart(df_combinado)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # Tabla de datos
            st.subheader("Datos Semanales Detallados")
            st.dataframe(
                df_combinado[["semana", "rango_fechas", "pedidos_totales", "creditos_totales", "creditos_por_pedido"]].rename(
                    columns={
                        "semana": "Semana", 
                        "rango_fechas": "Rango", 
                        "pedidos_totales": "Pedidos", 
                        "creditos_totales": "Créditos",
                        "creditos_por_pedido": "Créditos/Pedido"
                    }
                ).sort_values("Semana"), 
                hide_index=True,
                column_config={
                    "Créditos/Pedido": st.column_config.NumberColumn(format="$%.2f")
                }
            )
            
            # Botón de descarga
            csv = df_combinado.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📊 Descargar CSV", 
                data=csv, 
                file_name=f"creditos_pedidos_semanales_{fecha_inicio_sem}_{fecha_actual}.csv", 
                mime="text/csv"
            )
        else:
            st.warning("No hay datos completos disponibles (créditos y pedidos)")
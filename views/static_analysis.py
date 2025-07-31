import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from data.database_service import DatabaseService
from data.api_service import APIService
from data.data_processor import DataProcessor
from utils.chart_utils import ChartUtils
from utils.error_handler import handle_errors, validate_date_range
from utils.date_utils import DateUtils
from config.settings import AppSettings

class StaticAnalysisView:
    def __init__(self):
        self.db_service = DatabaseService()
        self.api_service = APIService()
        self.data_processor = DataProcessor()
        self.chart_utils = ChartUtils()
        self.date_utils = DateUtils()
    
    @handle_errors
    def render(self):
        """Renderizar vista de análisis estático"""
        st.title("📊 Otros Análisis")
        
        # Configurar año seleccionado
        current_year = datetime.now().year
        years_available = list(range(2025, current_year + 3))
        selected_year = st.sidebar.selectbox(
            "Seleccionar Año", 
            years_available, 
            index=years_available.index(current_year)
        )
        
        # Configurar fechas basadas en el año seleccionado
        fecha_inicio_sem = datetime(selected_year, 1, 1).date()
        fecha_actual = (datetime.now().date() if selected_year == current_year 
                       else datetime(selected_year, 12, 31).date())
        
        # Renderizar tabs
        self._render_tabs(fecha_inicio_sem, fecha_actual, selected_year)
    
    def _render_tabs(self, fecha_inicio_sem, fecha_actual, selected_year):
        """Renderizar tabs del análisis estático"""
        tab1, tab2 = st.tabs(["📦 Pedidos por Semana", "💳 Créditos por Semana"])
        
        with tab1:
            self._render_weekly_orders_tab(fecha_inicio_sem, fecha_actual, selected_year)
        
        with tab2:
            self._render_weekly_credits_tab(fecha_inicio_sem, fecha_actual, selected_year)
    
    def _render_weekly_orders_tab(self, fecha_inicio_sem, fecha_actual, selected_year):
        """Renderizar tab de pedidos semanales"""
        with st.spinner("Obteniendo datos de pedidos..."):
            datos_estadistica_pedidos = self.db_service.get_orders_data(fecha_inicio_sem, fecha_actual)
            
            if datos_estadistica_pedidos and datos_estadistica_pedidos.get("success"):
                pedidos_semanales = self.data_processor.calculate_weekly_data(
                    datos_estadistica_pedidos, "pedidos"
                )
            else:
                st.error("No se pudieron obtener datos de pedidos")
                pedidos_semanales = None
        
        if pedidos_semanales is not None and not pedidos_semanales.empty:
            st.header(f"Análisis Semanal de Pedidos {selected_year}")
            
            # Métricas principales
            col1, col2, col3 = st.columns(3)
            total = pedidos_semanales["pedidos_totales"].sum()
            semana_max = pedidos_semanales.loc[pedidos_semanales["pedidos_totales"].idxmax()]
            semana_min = pedidos_semanales.loc[pedidos_semanales["pedidos_totales"].idxmin()]
            
            col1.metric("Pedidos totales", f"{total:,}")
            col2.metric(
                "Semana con más pedidos", 
                f"Semana {semana_max['semana']}", 
                help=f"{semana_max['rango_fechas']}: {semana_max['pedidos_totales']:,}"
            )
            col3.metric(
                "Semana con menos pedidos", 
                f"Semana {semana_min['semana']}", 
                help=f"{semana_min['rango_fechas']}: {semana_min['pedidos_totales']:,}"
            )
            
            # Gráfico de barras
            fig = px.bar(
                pedidos_semanales, 
                x="semana", 
                y="pedidos_totales", 
                title="Pedidos por Semana", 
                labels={"semana": "Semana", "pedidos_totales": "Total Pedidos"}, 
                hover_data=["rango_fechas"], 
                color="pedidos_totales", 
                color_continuous_scale="reds"
            )
            fig.update_traces(
                hovertemplate="<b>Semana %{x}</b><br>%{customdata[0]}<br>Pedidos: %{y:,}", 
                texttemplate="%{y:,}", 
                textposition="outside"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla de datos
            pedidos_semanales_display = pedidos_semanales.copy()
            if 'fecha_inicio' in pedidos_semanales_display.columns:
                pedidos_semanales_display["fecha_inicio"] = pedidos_semanales_display["fecha_inicio"].astype('datetime64[ns]').dt.strftime('%d-%m-%Y')
            if 'fecha_fin' in pedidos_semanales_display.columns:
                pedidos_semanales_display["fecha_fin"] = pedidos_semanales_display["fecha_fin"].astype('datetime64[ns]').dt.strftime('%d-%m-%Y')
            
            st.dataframe(
                pedidos_semanales_display[["semana", "rango_fechas", "pedidos_totales"]].rename(
                    columns={"semana": "Semana", "rango_fechas": "Rango", "pedidos_totales": "Pedidos"}
                ), 
                hide_index=True
            )
            
            # Botón de descarga
            csv = pedidos_semanales.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📊 Descargar Datos", 
                data=csv, 
                file_name=f"pedidos_semanales_{fecha_inicio_sem.strftime('%d-%m-%Y')}_{fecha_actual.strftime('%d-%m-%Y')}.csv", 
                mime="text/csv"
            )
        else:
            st.warning("No hay datos de pedidos disponibles")
    
    def _render_weekly_credits_tab(self, fecha_inicio_sem, fecha_actual, selected_year):
        """Renderizar tab de créditos semanales"""
        with st.spinner("Obteniendo datos de créditos y pedidos..."):
            data_creditos_pedidos = self.db_service.get_orders_data(fecha_inicio_sem, fecha_actual)
            
            if data_creditos_pedidos is not None and data_creditos_pedidos.get("success"):
                df_estadistica = pd.DataFrame(data_creditos_pedidos["data"]["detalle"]["general"]["todos"])
                df_estadistica = df_estadistica.dropna(subset=["order_completion_date"])
                
                if not df_estadistica.empty:
                    creditos_semanales = self.data_processor.calculate_weekly_data(
                        data_creditos_pedidos, "creditos"
                    )
                    pedidos_semanales_for_credits = self.data_processor.calculate_weekly_data(
                        data_creditos_pedidos, "pedidos"
                    )
                    
                    if (not creditos_semanales.empty and 
                        not pedidos_semanales_for_credits.empty):
                        
                        df_combinado = creditos_semanales.merge(
                            pedidos_semanales_for_credits[["semana", "pedidos_totales"]],
                            on="semana",
                            how="left"
                        )
                        df_combinado["creditos_por_pedido"] = (
                            df_combinado["creditos_totales"] / 
                            df_combinado["pedidos_totales"].replace(0, np.nan)
                        )
                        df_combinado = df_combinado.dropna(subset=["creditos_por_pedido"])
                        
                        if not df_combinado.empty:
                            semana_mas_costosa = df_combinado.loc[
                                df_combinado["creditos_por_pedido"].idxmax()
                            ]
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
            st.header(f"Análisis Semanal de Créditos {selected_year}")
            
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            total = df_combinado["creditos_totales"].sum()
            semana_max = df_combinado.loc[df_combinado["creditos_totales"].idxmax()]
            semana_min = df_combinado.loc[df_combinado["creditos_totales"].idxmin()]
            
            col1.metric("Créditos totales", f"{total:,}")
            col2.metric(
                "Semana con más créditos", 
                f"Semana {semana_max['semana']}",
                help=f"{semana_max['rango_fechas']}: {semana_max['creditos_totales']:,}"
            )
            col3.metric(
                "Semana con menos créditos", 
                f"Semana {semana_min['semana']}",
                help=f"{semana_min['rango_fechas']}: {semana_min['creditos_totales']:,}"
            )
            
            if semana_mas_costosa is not None:
                col4.metric(
                    "Semana con envío más costoso", 
                    f"Semana {semana_mas_costosa['semana']}",
                    help=f"{semana_mas_costosa['rango_fechas']}: ${semana_mas_costosa['creditos_por_pedido']:,.2f} por pedido"
                )
            else:
                col4.metric("Semana con envío más costoso", "N/A")
            
            # Gráfico de créditos
            fig = px.bar(
                df_combinado, 
                x="semana", 
                y="creditos_totales",
                title="Créditos por Semana",
                labels={"semana": "Semana", "creditos_totales": "Total Créditos"},
                hover_data=["rango_fechas", "pedidos_totales", "creditos_por_pedido"],
                color="creditos_totales",
                color_continuous_scale="turbo"
            )
            fig.update_traces(
                hovertemplate="<b>Semana %{x}</b><br>%{customdata[0]}<br>Créditos: %{y:,}<br>Pedidos: %{customdata[1]:,}<br>Créditos/Pedido: $%{customdata[2]:.2f}",
                texttemplate="%{y:,}",
                textposition="outside"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla de datos detallados
            st.subheader("Datos Semanales Detallados")
            df_combinado_display = df_combinado.copy()
            
            if 'fecha_inicio' in df_combinado_display.columns:
                df_combinado_display["fecha_inicio"] = df_combinado_display["fecha_inicio"].astype('datetime64[ns]').dt.strftime('%d-%m-%Y')
            if 'fecha_fin' in df_combinado_display.columns:
                df_combinado_display["fecha_fin"] = df_combinado_display["fecha_fin"].astype('datetime64[ns]').dt.strftime('%d-%m-%Y')
            
            st.dataframe(
                df_combinado_display[["semana", "rango_fechas", "pedidos_totales", "creditos_totales", "creditos_por_pedido"]].rename(
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
                "📊 Descargar Datos Completos",
                data=csv,
                file_name=f"creditos_pedidos_semanales_{fecha_inicio_sem.strftime('%d-%m-%Y')}_{fecha_actual.strftime('%d-%m-%Y')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No hay datos completos disponibles (créditos y pedidos)")



"""
Vista de Análisis Estático (Semanal)
====================================

Este módulo contiene la clase StaticAnalysisView que maneja el análisis estadístico
semanal de la aplicación. Proporciona análisis detallados de pedidos y créditos
organizados por semanas del año con visualizaciones y métricas comparativas.

Características principales:
- Análisis semanal de pedidos y créditos por año
- Selector de año para análisis histórico
- Gráficos de barras con datos semanales
- Métricas de semanas con mayor/menor actividad
- Cálculo de créditos por pedido y análisis de costos
- Descarga de datos en formato CSV
- Manejo robusto de errores y validación de datos
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from data.database_service import DatabaseService
from data.data_processor import DataProcessor
from utils.chart_utils import ChartUtils
from utils.error_handler import handle_errors, validate_date_range
from utils.date_utils import DateUtils
from config.settings import AppSettings

class StaticAnalysisView:
    """
    Vista para análisis estadístico semanal (estático).
    
    Esta clase maneja la renderización del análisis semanal que incluye:
    - Análisis de pedidos por semana del año
    - Análisis de créditos por semana con cálculo de costos
    - Selector de año para análisis histórico
    - Métricas comparativas entre semanas
    - Visualizaciones de barras con datos semanales
    - Funcionalidad de descarga de datos
    
    Attributes:
        db_service (DatabaseService): Servicio para acceso a datos
        data_processor (DataProcessor): Procesador de datos estadísticos
        chart_utils (ChartUtils): Utilidades para creación de gráficos
        date_utils (DateUtils): Utilidades para manejo de fechas
    """
    
    def __init__(self):
        """
        Inicializar la vista de análisis estático.
        
        Configura todos los servicios necesarios para el análisis semanal,
        incluyendo acceso a datos, procesamiento y utilidades de visualización.
        """
        self.db_service = DatabaseService()
        self.data_processor = DataProcessor()
        self.chart_utils = ChartUtils()
        self.date_utils = DateUtils()
    
    @handle_errors
    def render(self):
        """
        Renderizar la vista completa del análisis estático semanal.
        
        Método principal que coordina la renderización del análisis semanal,
        incluyendo selector de año y pestañas para pedidos y créditos.
        """
        st.title("📊 Estadísticas Semanales")
        
        # Configurar selector de año en sidebar
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
        
        # Renderizar pestañas de análisis
        self._render_tabs(fecha_inicio_sem, fecha_actual, selected_year)
    
    def _render_tabs(self, fecha_inicio_sem, fecha_actual, selected_year):
        """
        Renderizar pestañas del análisis estático.
        
        Crea las dos pestañas principales del análisis semanal:
        1. Pedidos por Semana - Análisis de volumen de pedidos
        2. Créditos por Semana - Análisis de costos y créditos utilizados
        
        Args:
            fecha_inicio_sem (date): Fecha de inicio del año
            fecha_actual (date): Fecha actual o fin del año
            selected_year (int): Año seleccionado para análisis
        """
        tab1, tab2 = st.tabs(["📦 Pedidos por Semana", "💳 Créditos por Semana"])
        
        with tab1:
            self._render_weekly_orders_tab(fecha_inicio_sem, fecha_actual, selected_year)
        
        with tab2:
            self._render_weekly_credits_tab(fecha_inicio_sem, fecha_actual, selected_year)
    
    def _render_weekly_orders_tab(self, fecha_inicio_sem, fecha_actual, selected_year):
        """
        Renderizar pestaña de análisis de pedidos semanales.
        
        Muestra el análisis completo de pedidos organizados por semanas,
        incluyendo métricas principales, gráfico de barras y tabla de datos.
        
        Args:
            fecha_inicio_sem (date): Fecha de inicio del período
            fecha_actual (date): Fecha actual del período
            selected_year (int): Año seleccionado para análisis
        """
        with st.spinner("Obteniendo datos de pedidos..."):
            datos_estadistica_pedidos = self.db_service.get_orders_data(fecha_inicio_sem, fecha_actual)
            
            if datos_estadistica_pedidos and datos_estadistica_pedidos.get("success"):
                # Procesar datos semanales de pedidos
                pedidos_semanales = self.data_processor.calculate_weekly_data(
                    datos_estadistica_pedidos, "pedidos", selected_year
                )
            else:
                st.error("No se pudieron obtener datos de pedidos")
                pedidos_semanales = None
        
        if pedidos_semanales is not None and not pedidos_semanales.empty:
            st.header(f"Análisis Semanal de Pedidos {selected_year}")
            
            # Métricas principales del análisis de pedidos
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
            
            # Gráfico de barras con escala de colores
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
            
            # Tabla de datos con formato de fechas
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
            
            # Funcionalidad de descarga de datos
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
        """
        Renderizar pestaña de análisis de créditos semanales.
        
        Muestra el análisis completo de créditos organizados por semanas,
        incluyendo cálculo de créditos por pedido, métricas de costos y
        análisis de semanas más costosas.
        
        Args:
            fecha_inicio_sem (date): Fecha de inicio del período
            fecha_actual (date): Fecha actual del período
            selected_year (int): Año seleccionado para análisis
        """
        with st.spinner("Obteniendo datos de créditos y pedidos..."):
            data_creditos_pedidos = self.db_service.get_orders_data(fecha_inicio_sem, fecha_actual)
            
            if data_creditos_pedidos is not None and data_creditos_pedidos.get("success"):
                try:
                    # Validar estructura de datos recibidos
                    df_estadistica = pd.DataFrame(data_creditos_pedidos["data"]["detalle"]["general"]["todos"])
                    
                    # Verificar existencia de columna crítica
                    if "order_completion_date" not in df_estadistica.columns:
                        st.warning("⚠️ No hay datos en las fechas seleccionadas. Por lo tanto no se puede procesar el análisis de créditos.")
                        return
                    
                    # Verificar datos válidos en la columna
                    if df_estadistica["order_completion_date"].isna().all():
                        st.warning("⚠️ No hay fechas de completado válidas en los datos. No se puede procesar el análisis de créditos.")
                        return
                    
                    # Limpiar datos eliminando registros sin fecha
                    df_estadistica = df_estadistica.dropna(subset=["order_completion_date"])
                    
                    if df_estadistica.empty:
                        st.warning("⚠️ No hay datos válidos después de filtrar por fechas de completado. Intenta con un rango de fechas diferente.")
                        return
                    
                except Exception as e:
                    st.error(f"⚠️ Error al procesar los datos: Los datos recibidos no tienen el formato esperado. Por favor, verifica la conexión con la base de datos.")
                    return
                
                if not df_estadistica.empty:
                    try:
                        # Procesar datos semanales de créditos y pedidos
                        creditos_semanales = self.data_processor.calculate_weekly_data(
                            data_creditos_pedidos, "creditos", selected_year
                        )
                        pedidos_semanales_for_credits = self.data_processor.calculate_weekly_data(
                            data_creditos_pedidos, "pedidos", selected_year
                        )
                        
                        if (not creditos_semanales.empty and 
                            not pedidos_semanales_for_credits.empty):
                            
                            # Combinar datos de créditos y pedidos
                            df_combinado = creditos_semanales.merge(
                                pedidos_semanales_for_credits[["semana", "pedidos_totales"]],
                                on="semana",
                                how="left"
                            )
                            
                            # Calcular créditos por pedido (costo promedio)
                            df_combinado["creditos_por_pedido"] = (
                                df_combinado["creditos_totales"] / 
                                df_combinado["pedidos_totales"].replace(0, np.nan)
                            )
                            df_combinado = df_combinado.dropna(subset=["creditos_por_pedido"])
                            
                            # Identificar semana más costosa
                            if not df_combinado.empty:
                                semana_mas_costosa = df_combinado.loc[
                                    df_combinado["creditos_por_pedido"].idxmax()
                                ]
                            else:
                                semana_mas_costosa = None
                        else:
                            st.warning("⚠️ No se pudieron calcular los datos semanales. Verifica que haya suficientes datos en el período seleccionado.")
                            df_combinado = None
                    except Exception as e:
                        st.error(f"⚠️ Error al calcular datos semanales: No se pudieron procesar los datos correctamente.")
                        df_combinado = None
                else:
                    st.warning("⚠️ No hay datos de estadísticas disponibles para procesar créditos y pedidos.")
                    df_combinado = None
            else:
                st.warning("⚠️ No se pudieron obtener datos de la API. Verifica la conexión con la base de datos.")
                df_combinado = None
        
        if df_combinado is not None and not df_combinado.empty:
            st.header(f"Análisis Semanal de Créditos {selected_year}")
            
            # Métricas principales del análisis de créditos
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
            
            # Métrica de semana más costosa por pedido
            if semana_mas_costosa is not None:
                col4.metric(
                    "Semana con envío más costoso", 
                    f"Semana {semana_mas_costosa['semana']}",
                    help=f"{semana_mas_costosa['rango_fechas']}: ${semana_mas_costosa['creditos_por_pedido']:,.2f} por pedido"
                )
            else:
                col4.metric("Semana con envío más costoso", "N/A")
            
            # Gráfico de barras con escala de colores turbo
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
            
            # Tabla de datos detallados con todas las métricas
            st.subheader("Datos Semanales Detallados")
            df_combinado_display = df_combinado.copy()
            
            # Formatear fechas para visualización
            if 'fecha_inicio' in df_combinado_display.columns:
                df_combinado_display["fecha_inicio"] = df_combinado_display["fecha_inicio"].astype('datetime64[ns]').dt.strftime('%d-%m-%Y')
            if 'fecha_fin' in df_combinado_display.columns:
                df_combinado_display["fecha_fin"] = df_combinado_display["fecha_fin"].astype('datetime64[ns]').dt.strftime('%d-%m-%Y')
            
            # Tabla interactiva con formato de moneda
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
            
            # Funcionalidad de descarga de datos completos
            csv = df_combinado.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📊 Descargar Datos Completos",
                data=csv,
                file_name=f"creditos_pedidos_semanales_{fecha_inicio_sem.strftime('%d-%m-%Y')}_{fecha_actual.strftime('%d-%m-%Y')}.csv",
                mime="text/csv"
            )
        else:
            st.info("📊 No hay datos suficientes para mostrar el análisis de créditos en el período seleccionado. Intenta con un rango de fechas diferente o verifica que haya pedidos completados en este período.")


# Función de compatibilidad para mantener la función original
def otros_dashboard():
    """
    Función de compatibilidad para mantener la interfaz original.
    
    Esta función mantiene la compatibilidad con código existente que
    pueda estar llamando a la función otros_dashboard() directamente.
    Simplemente crea una instancia de StaticAnalysisView y llama a render().
    """
    view = StaticAnalysisView()
    view.render()



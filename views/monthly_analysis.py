import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from data.database_service import DatabaseService
from data.data_processor import DataProcessor
from utils.chart_utils import ChartUtils
from utils.error_handler import handle_errors, validate_date_range
from utils.date_utils import DateUtils
from config.settings import AppSettings

class MonthlyAnalysisView:
    def __init__(self):
        self.db_service = DatabaseService()
        self.data_processor = DataProcessor()
        self.chart_utils = ChartUtils()
        self.date_utils = DateUtils()
    
    @handle_errors
    def render(self):
        """Renderizar vista de análisis mensual"""
        st.title("📈 Análisis Estadístico Mensual")
        
        # Configurar fechas
        fecha_fin = datetime.now().date()
        fecha_inicio = AppSettings.DEFAULT_START_DATE
        
        # Sidebar para selección de mes
        self._render_sidebar(fecha_inicio, fecha_fin)
        
        # Cargar y procesar datos
        with st.spinner("Cargando datos..."):
            data_estadistica = self.db_service.get_orders_data(fecha_inicio, fecha_fin)
            
            if not data_estadistica:
                st.error("No se pudieron cargar los datos")
                return
            
            df_mensual, df_diario_para_grafico, df_estadistica_completa = self.data_processor.process_monthly_data(data_estadistica)
        
        # Renderizar contenido principal
        self._render_monthly_summary(df_mensual, df_diario_para_grafico)
    
    def _render_sidebar(self, fecha_inicio, fecha_fin):
        """Renderizar sidebar con controles"""
        with st.sidebar:
            st.header("Mes")
            meses_disponibles = self.date_utils.get_month_periods(fecha_inicio, fecha_fin)
            
            self.mes_seleccionado = st.selectbox(
                "Seleccionar Mes", 
                meses_disponibles, 
                index=len(meses_disponibles)-1
            )
            
            if st.button("Actualizar Datos"):
                st.cache_data.clear()
    
    def _render_monthly_summary(self, df_mensual, df_diario_para_grafico):
        """Renderizar resumen mensual"""
        if df_mensual.empty:
            st.warning("No hay datos disponibles para el análisis mensual")
            return
        
        st.subheader(f"Resumen de {self.mes_seleccionado}")
        
        # Obtener datos del mes actual
        mes_actual = df_mensual[df_mensual["mes_display"] == self.mes_seleccionado]
        
        if mes_actual.empty:
            st.warning(f"No hay datos para {self.mes_seleccionado}")
            return
        
        mes_actual = mes_actual.iloc[0]
        
        # Obtener mes y año del mes actual
        meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio",
                 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
        mes_num = [k for k, v in meses.items() if v == self.mes_seleccionado.split()[0]][0]
        anio = int(self.mes_seleccionado.split()[1])
        
        # Calcular métricas
        self._render_metrics(df_mensual, df_diario_para_grafico, mes_actual, mes_num, anio)
        
        # Renderizar gráfico de tendencias
        self._render_trends_chart(df_diario_para_grafico, mes_actual, mes_num, anio)
        
        # Renderizar tabla de datos
        self._render_data_table(df_diario_para_grafico, mes_actual, mes_num, anio)
    
    def _render_metrics(self, df_mensual, df_diario_para_grafico, mes_actual, mes_num, anio):
        """Renderizar métricas del mes"""
        # Buscar mes anterior para comparación
        mes_actual_period = mes_actual["mes"]
        mes_anterior_period = mes_actual_period.asfreq('M') - 1
        mes_anterior = df_mensual[df_mensual["mes"] == mes_anterior_period]
        
        # Filtrar datos del mes actual
        df_diario_mes = df_diario_para_grafico[
            (df_diario_para_grafico["fecha"].dt.month == mes_num) & 
            (df_diario_para_grafico["fecha"].dt.year == anio)
        ].copy()

        pedidos_promedio_general = df_diario_mes["total_pedidos"].mean() if not df_diario_mes.empty else 0

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        if not mes_anterior.empty:
            mes_anterior_data = mes_anterior.iloc[0]
            
            # Calcular deltas
            deltas = self._calculate_deltas(df_diario_para_grafico, mes_actual, mes_anterior_data, mes_anterior_period, pedidos_promedio_general)
            
            col1.metric("Establecimientos Activos Promedio", 
                       f"{mes_actual['establecimientos_promedio']:.0f}", 
                       f"{deltas['delta_est_prom']:.1f}%", 
                       delta_color="normal")
            col2.metric("Establecimientos Activos Totales", 
                       f"{mes_actual['establecimientos_unicos']:,.0f}", 
                       f"{deltas['delta_est_tot']:.1f}%", 
                       delta_color="normal")
            col3.metric("Pedidos Totales Realizados", 
                       f"{mes_actual['pedidos_totales']:,.0f}", 
                       f"{deltas['delta_ped_tot']:.1f}%", 
                       delta_color="normal")
            col4.metric("Ratio Pedidos/Establecimientos", 
                       f"{mes_actual['ratio_pedidos_establecimientos']:.2f}", 
                       f"{deltas['delta_ratio']:.1f}%", 
                       delta_color="normal")
            col5.metric("Créditos Totales Utilizados", 
                       f"{mes_actual['creditos_totales']:,.0f}", 
                       f"{deltas['delta_creditos']:.1f}%", 
                       delta_color="normal")
            col6.metric("Pedidos (promedio)", 
                       f"{pedidos_promedio_general:.2f}", 
                       f"{deltas['delta_ped_prom_general']:.1f}%", 
                       delta_color="normal")
        else:
            # Sin comparación
            col1.metric("Establecimientos Activos Promedio", f"{mes_actual['establecimientos_promedio']:.0f}")
            col2.metric("Establecimientos Activos Totales", f"{mes_actual['establecimientos_unicos']:,.0f}")
            col3.metric("Pedidos Totales Realizados", f"{mes_actual['pedidos_totales']:,.0f}")
            col4.metric("Ratio Pedidos/Establecimientos", f"{mes_actual['ratio_pedidos_establecimientos']:.2f}")
            col5.metric("Créditos Totales Utilizados", f"{mes_actual['creditos_totales']:,.0f}")
            col6.metric("Pedidos (promedio)", f"{pedidos_promedio_general:.2f}")
    
    def _calculate_deltas(self, df_diario_para_grafico, mes_actual, mes_anterior_data, mes_anterior_period, pedidos_promedio_general):
        """Calcular deltas para métricas"""
        def safe_percentage_change(current, previous):
            return ((current - previous) / previous) * 100 if previous > 0 else 0
        
        # Calcular pedidos promedio del mes anterior
        df_diario_mes_anterior = df_diario_para_grafico[
            (df_diario_para_grafico["fecha"].dt.month == mes_anterior_period.month) & 
            (df_diario_para_grafico["fecha"].dt.year == mes_anterior_period.year)
        ].copy()
        
        pedidos_promedio_general_ant = df_diario_mes_anterior["total_pedidos"].mean() if not df_diario_mes_anterior.empty else 0
        
        return {
            'delta_est_prom': safe_percentage_change(
                mes_actual["establecimientos_promedio"], 
                mes_anterior_data["establecimientos_promedio"]
            ),
            'delta_est_tot': safe_percentage_change(
                mes_actual["establecimientos_unicos"], 
                mes_anterior_data["establecimientos_unicos"]
            ),
            'delta_ped_tot': safe_percentage_change(
                mes_actual["pedidos_totales"], 
                mes_anterior_data["pedidos_totales"]
            ),
            'delta_ratio': safe_percentage_change(
                mes_actual["ratio_pedidos_establecimientos"], 
                mes_anterior_data["ratio_pedidos_establecimientos"]
            ),
            'delta_creditos': safe_percentage_change(
                mes_actual["creditos_totales"], 
                mes_anterior_data["creditos_totales"]
            ),
            'delta_ped_prom_general': safe_percentage_change(
                pedidos_promedio_general, 
                pedidos_promedio_general_ant
            )
        }
    
    def _render_trends_chart(self, df_diario_para_grafico, mes_actual, mes_num, anio):
        """Renderizar gráfico de tendencias"""
        # Filtrar datos del mes
        df_diario_mes = df_diario_para_grafico[
            (df_diario_para_grafico["fecha"].dt.month == mes_num) & 
            (df_diario_para_grafico["fecha"].dt.year == anio)
        ].copy()
        
        if not df_diario_mes.empty:
            df_diario_mes['ratio'] = df_diario_mes["total_pedidos"] / df_diario_mes["total_establecimientos"].replace(0, np.nan)
            
            # Crear gráfico con plotly.graph_objects
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_diario_mes["fecha"], 
                y=df_diario_mes["total_establecimientos"], 
                name="Establecimientos", 
                line=dict(color="green")
            ))
            fig.add_trace(go.Scatter(
                x=df_diario_mes["fecha"], 
                y=df_diario_mes["total_pedidos"], 
                name="Pedidos", 
                line=dict(color="orange")
            ))
            fig.add_trace(go.Scatter(
                x=df_diario_mes["fecha"], 
                y=df_diario_mes["ratio"], 
                name="Ratio", 
                line=dict(color="blue")
            ))

            fig.update_layout(
                hovermode="x unified",
                title=f"Tendencias diarias - {self.mes_seleccionado}",
                xaxis_title="Fecha",
                yaxis_title="Cantidad"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_data_table(self, df_diario_para_grafico, mes_actual, mes_num, anio):
        """Renderizar tabla de datos"""
        # Filtrar datos del mes
        df_diario_mes = df_diario_para_grafico[
            (df_diario_para_grafico["fecha"].dt.month == mes_num) & 
            (df_diario_para_grafico["fecha"].dt.year == anio)
        ].copy()
        
        if not df_diario_mes.empty:
            df_diario_mes['ratio'] = df_diario_mes["total_pedidos"] / df_diario_mes["total_establecimientos"].replace(0, np.nan)
            
            # Ordenar por fecha descendente
            df_diario_mes = df_diario_mes.sort_values(by="fecha", ascending=False)
            
            st.subheader("Datos")
            
            # Formatear fecha para mostrar
            df_diario_mes_display = df_diario_mes.copy()
            df_diario_mes_display['fecha'] = df_diario_mes_display['fecha'].dt.strftime('%d-%m-%Y')
            
            st.dataframe(
                df_diario_mes_display[['fecha', 'total_pedidos', 'total_establecimientos', 'ratio']].rename(columns={
                    'fecha': 'Fecha', 
                    'total_pedidos': 'Pedidos', 
                    'total_establecimientos': 'Establecimientos', 
                    'ratio': 'Ratio Pedidos/Establecimientos'
                }), 
                hide_index=True,
                use_container_width=True
            )
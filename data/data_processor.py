import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta

class DataProcessor:
    @staticmethod
    def process_top_establishments(data_estadistica, limit=10):
        """Procesar top establecimientos con validación mejorada"""
        if not data_estadistica or not data_estadistica.get("success"):
            return pd.DataFrame()
        
        pedidos = data_estadistica["data"]["detalle"]["general"]["todos"]
        df = pd.DataFrame(pedidos)
        
        if df.empty or "name_restaurant" not in df.columns:
            return pd.DataFrame()
        
        df["order_completion_date"] = pd.to_datetime(df["order_completion_date"], errors='coerce')
        df_filtered = df.dropna(subset=["name_restaurant", "order_completion_date"])
        
        top_establishments = (df_filtered
                            .groupby("name_restaurant")
                            .size()
                            .reset_index(name="total_pedidos")
                            .sort_values("total_pedidos", ascending=False)
                            .head(limit))
        
        return top_establishments
    
    @staticmethod
    def process_establishments_orders(data_estadistica):
        """Procesar datos de establecimientos y pedidos por día"""
        if not data_estadistica or not data_estadistica.get("success"):
            return pd.DataFrame()
        
        df = pd.DataFrame(data_estadistica["data"]["detalle"]["general"]["todos"])
        if df.empty:
            return pd.DataFrame()
        
        df["fecha"] = pd.to_datetime(df["order_completion_date"]).dt.date
        
        # Pedidos por día
        df_pedidos_diarios = df.groupby("fecha").size().reset_index(name="total_pedidos")
        
        # Establecimientos únicos por día
        df_establecimientos_diarios = df.groupby("fecha")["id_restaurant"].nunique().reset_index(name="total_establecimientos")
        
        # Combinar datos
        df_merged = pd.merge(df_pedidos_diarios, df_establecimientos_diarios, on="fecha", how="outer").fillna(0)
        
        df_merged["fecha"] = pd.to_datetime(df_merged["fecha"])
        df_merged["total_establecimientos"] = df_merged["total_establecimientos"].astype(int)
        df_merged["total_pedidos"] = df_merged["total_pedidos"].astype(int)
        df_merged = df_merged.rename(columns={
            "fecha": "Fecha", 
            "total_establecimientos": "Establecimientos", 
            "total_pedidos": "Pedidos"
        })
        df_merged["Promedio"] = df_merged["Pedidos"] / df_merged["Establecimientos"].replace(0, np.nan)
        
        return df_merged
    
    @staticmethod
    def process_hourly_orders(data, fecha):
        """Procesar pedidos por hora para una fecha específica"""
        if not data or not data.get("success"):
            return pd.DataFrame()
        
        pedidos = data["data"]["detalle"]["general"]["todos"]
        df = pd.DataFrame(pedidos)
        
        if df.empty:
            return pd.DataFrame()
        
        df["creacion"] = pd.to_datetime(df["order_completion_date"], errors='coerce')
        df_filtrado = df.loc[df["creacion"].dt.date == fecha].copy()
        
        if df_filtrado.empty:
            return pd.DataFrame()
        
        df_filtrado.loc[:, "hora"] = df_filtrado["creacion"].dt.hour
        df_horario = df_filtrado[(df_filtrado["hora"] >= 8) & (df_filtrado["hora"] <= 23)]
        
        conteo_hora = df_horario.groupby("hora").size()
        horas_rango = pd.DataFrame({"hora": range(8, 24)})
        contador_final = horas_rango.merge(conteo_hora.reset_index(name="pedidos"), on="hora", how="left").fillna(0)
        contador_final["etiqueta_hora"] = contador_final["hora"].apply(
            lambda x: f"{x - 12}:00 PM" if x > 12 else f"{x}:00 AM" if x < 12 else "12:00 PM"
        )
        
        return contador_final
    
    @staticmethod
    def process_concurrency(df, fecha):
        """Procesar concurrencia de pedidos para una fecha específica"""
        if df.empty:
            return None, None, None, None, None
        
        df_filtrado = df.loc[pd.to_datetime(df["order_acceptance_date"]).dt.date == fecha].copy()
        
        if df_filtrado.empty:
            return None, None, None, None, None
        
        df_filtrado.loc[:, "asignacion"] = pd.to_datetime(df_filtrado["order_acceptance_date"])
        df_filtrado.loc[:, "entrega"] = pd.to_datetime(df_filtrado["order_completion_date"], errors='coerce')
        
        df_filtrado = df_filtrado.dropna(subset=["entrega"])
        
        if df_filtrado.empty:
            return None, None, None, None, None
        
        min_time = df_filtrado["asignacion"].min()
        max_time = df_filtrado["entrega"].max()
        segmentos = pd.date_range(start=min_time.floor("h"), end=max_time.ceil("h"), freq="1min")
        
        concurrencia = []
        for i in range(len(segmentos) - 1):
            inicio_seg = segmentos[i]
            fin_seg = segmentos[i + 1]
            contador = ((df_filtrado["asignacion"] <= fin_seg) & (df_filtrado["entrega"] >= inicio_seg)).sum()
            concurrencia.append(contador)
        
        df_concurrencia = pd.DataFrame({"Hora": segmentos[:-1], "Pedidos_Simultaneos": concurrencia})
        
        max_idx = np.argmax(concurrencia)
        max_concurrencia = int(concurrencia[max_idx])
        mejor_inicio = segmentos[max_idx]
        mejor_fin = segmentos[max_idx + 1]
        
        # Crear gráfico
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=segmentos[:-1], 
            y=concurrencia, 
            mode="lines", 
            name="Pedidos concurrentes", 
            line=dict(color="Cyan", width=2), 
            hovertemplate='<b>%{x|%H:%M}</b><br>Pedidos: %{y}'
        ))
        fig.add_trace(go.Scatter(
            x=[mejor_inicio, mejor_fin], 
            y=[max_concurrencia, max_concurrencia], 
            mode="lines", 
            name="Máxima Concurrencia", 
            line=dict(color="Red", width=6, dash="dash"), 
            hovertemplate=f"Máximo: {max_concurrencia} pedidos"
        ))
        fig.update_layout(
            title=f"Concurrencia de Pedidos {fecha}", 
            xaxis_title="Hora", 
            yaxis_title="Pedidos Simultáneos", 
            hovermode="x unified", 
            showlegend=True
        )
        
        return fig, max_concurrencia, mejor_inicio, mejor_fin, df_concurrencia
    
    @staticmethod
    def calculate_weekly_data(data_estadistica, data_type="pedidos"):
        """Calcular datos semanales con mejor manejo de errores"""
        if not data_estadistica or not data_estadistica.get("success"):
            return pd.DataFrame()
        
        df = pd.DataFrame(data_estadistica["data"]["detalle"]["general"]["todos"])
        
        if df.empty:
            return pd.DataFrame()
        
        try:
            if data_type == "pedidos":
                df["fecha"] = pd.to_datetime(df["order_completion_date"]).dt.date
                df_agrupado = df.groupby("fecha").size().reset_index(name="total_pedidos")
                value_col = "total_pedidos"
            else:  # creditos
                df["fecha"] = pd.to_datetime(df["created_at"]).dt.date
                df["costo_creditos"] = pd.to_numeric(df["costo_creditos"], errors="coerce").fillna(0)
                df_agrupado = df.groupby("fecha")["costo_creditos"].sum().reset_index()
                value_col = "costo_creditos"
            
            # Calcular semanas
            df_agrupado["semana"] = DataProcessor._calculate_week_numbers(df_agrupado["fecha"])
            
            # Agrupar por semana
            weekly_data = df_agrupado.groupby("semana")[value_col].sum().reset_index()
            
            # Agregar rangos de fechas
            weekly_data = DataProcessor._add_date_ranges(weekly_data, data_type)
            
            return weekly_data.sort_values("semana")
            
        except Exception as e:
            st.error(f"Error procesando datos semanales: {str(e)}")
            return pd.DataFrame()
    
    @staticmethod
    def process_monthly_data(data_estadistica):
        """Procesar datos para análisis mensual"""
        if not data_estadistica or not data_estadistica.get("success"):
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        meses_espanol = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        
        df_estadistica = pd.DataFrame(data_estadistica["data"]["detalle"]["general"]["todos"])
        if df_estadistica.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        df_estadistica["fecha_completa"] = pd.to_datetime(df_estadistica["order_completion_date"])
        df_estadistica["created_at"] = pd.to_datetime(df_estadistica["created_at"])
        df_estadistica["mes"] = df_estadistica["fecha_completa"].dt.to_period('M')
        
        df_estadistica["creditos"] = pd.to_numeric(df_estadistica["costo_creditos"], errors="coerce").fillna(0)
        
        # Establecimientos activos promedio por mes
        establecimientos_activos_diarios = df_estadistica.groupby([
            df_estadistica["fecha_completa"].dt.date, "mes"
        ])["id_restaurant"].nunique().reset_index()
        establecimientos_activos_diarios.columns = ["fecha", "mes", "establecimientos_activos"]
        establecimientos_promedio_mensual = establecimientos_activos_diarios.groupby("mes")["establecimientos_activos"].mean().reset_index(name="establecimientos_promedio")
        
        # Establecimientos únicos totales por mes
        establecimientos_unicos_totales_mensual = df_estadistica.groupby("mes")["id_restaurant"].nunique().reset_index(name="establecimientos_unicos")
        
        # Pedidos totales por mes
        pedidos_totales_mensual = df_estadistica.groupby("mes").size().reset_index(name="pedidos_totales")
        
        # Combinar datos mensuales
        df_mensual = pd.merge(establecimientos_promedio_mensual, establecimientos_unicos_totales_mensual, on="mes", how="left")
        df_mensual = pd.merge(df_mensual, pedidos_totales_mensual, on="mes", how="left")
        
        # Créditos mensuales
        mensual_creditos = df_estadistica.groupby("mes").agg({"creditos": "sum"}).reset_index()
        mensual_creditos.columns = ["mes", "creditos_totales"]
        df_mensual = pd.merge(df_mensual, mensual_creditos, on="mes", how="left")
        
        # Ratio pedidos/establecimientos
        df_mensual = df_mensual.set_index('mes')
        df_mensual["ratio_pedidos_establecimientos"] = df_estadistica.groupby([
            df_estadistica["fecha_completa"].dt.to_period('M'), 
            df_estadistica["fecha_completa"].dt.date
        ]).apply(
            lambda x: x.shape[0] / x["id_restaurant"].nunique() if x["id_restaurant"].nunique() > 0 else np.nan
        ).groupby(level=0).mean().rename("ratio_pedidos_establecimientos")
        df_mensual = df_mensual.reset_index()
        
        df_mensual["mes_display"] = df_mensual["mes"].apply(lambda x: f"{meses_espanol[x.month]} {x.year}")
        
        # Datos diarios para gráfico
        df_diario_para_grafico = df_estadistica.groupby(df_estadistica["fecha_completa"].dt.date).agg(
            total_pedidos=('id_order', 'size'),
            total_establecimientos=('id_restaurant', 'nunique')
        ).reset_index()
        df_diario_para_grafico.columns = ['fecha', 'total_pedidos', 'total_establecimientos']
        df_diario_para_grafico['fecha'] = pd.to_datetime(df_diario_para_grafico['fecha'])
        
        return df_mensual, df_diario_para_grafico, df_estadistica
    
    @staticmethod
    def _calculate_week_numbers(fechas):
        """Calcular números de semana basado en lógica específica"""
        semanas = []
        for fecha_dt in fechas:
            fecha = fecha_dt.date() if isinstance(fecha_dt, datetime) else fecha_dt
            current_date_year = fecha.year

            week_num = None

            if current_date_year == 2025:
                if datetime(2025, 1, 1).date() <= fecha <= datetime(2025, 1, 5).date():
                    week_num = 1
                elif datetime(2025, 12, 29).date() <= fecha <= datetime(2025, 12, 31).date():
                    week_num = 53
            elif current_date_year == 2026:
                if datetime(2026, 1, 1).date() <= fecha <= datetime(2026, 1, 4).date():
                    week_num = 1
                elif datetime(2026, 1, 5).date() <= fecha <= datetime(2026, 1, 11).date():
                    week_num = 2
                elif datetime(2026, 12, 28).date() <= fecha <= datetime(2026, 12, 31).date():
                    week_num = datetime(2026, 12, 31).isocalendar()[1]
            elif current_date_year == 2027:
                if datetime(2027, 1, 1).date() <= fecha <= datetime(2027, 1, 3).date():
                    week_num = 1
                elif datetime(2027, 1, 4).date() <= fecha <= datetime(2027, 1, 10).date():
                    week_num = 2
                elif datetime(2027, 12, 27).date() <= fecha <= datetime(2027, 12, 31).date():
                    week_num = datetime(2027, 12, 31).isocalendar()[1]

            if week_num is None:
                week_num = fecha.isocalendar()[1]

            semanas.append(week_num)
        return semanas
    
    @staticmethod
    def _add_date_ranges(weekly_data, data_type):
        """Agregar rangos de fechas a datos semanales"""
        primera_semana_inicio = datetime(2025, 1, 1).date()
        primera_semana_fin = datetime(2025, 1, 5).date()
        
        fecha_inicios = []
        fecha_fins = []
        
        for semana in weekly_data["semana"]:
            if semana == 1:
                fecha_inicios.append(primera_semana_inicio)
                fecha_fins.append(primera_semana_fin)
            else:
                dias_desde_inicio = (semana - 2) * 7
                inicio_semana = datetime(2025, 1, 6).date() + timedelta(days=dias_desde_inicio)
                fin_semana = inicio_semana + timedelta(days=6)
                fecha_inicios.append(inicio_semana)
                fecha_fins.append(fin_semana)
        
        weekly_data["fecha_inicio"] = fecha_inicios
        weekly_data["fecha_fin"] = fecha_fins
        weekly_data["rango_fechas"] = weekly_data.apply(
            lambda x: f"{x['fecha_inicio'].strftime('%d/%m/%Y')} - {x['fecha_fin'].strftime('%d/%m/%Y')}", 
            axis=1
        )
        
        # Renombrar columnas según el tipo
        if data_type == "pedidos":
            weekly_data.rename(columns={"total_pedidos": "pedidos_totales"}, inplace=True)
        else:
            weekly_data.rename(columns={"costo_creditos": "creditos_totales"}, inplace=True)
        
        return weekly_data
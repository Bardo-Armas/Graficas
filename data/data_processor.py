"""
Módulo de Procesamiento de Datos
===============================

Este módulo contiene la clase DataProcessor que proporciona métodos estáticos
para procesar y transformar datos de órdenes y establecimientos de la aplicación.

Funcionalidades principales:
- Procesamiento de top establecimientos por volumen de pedidos
- Análisis de pedidos y establecimientos por día
- Análisis de pedidos por hora para fechas específicas
- Cálculo de concurrencia de pedidos en tiempo real
- Procesamiento de datos semanales y mensuales
- Cálculo de números de semana con lógica específica del negocio
- Generación de rangos de fechas para análisis temporales

La clase utiliza pandas para manipulación de datos y plotly para visualizaciones,
optimizada para trabajar con grandes volúmenes de datos de órdenes.
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta

class DataProcessor:
    """
    Procesador de datos para análisis de órdenes y establecimientos.
    
    Esta clase proporciona métodos estáticos para procesar datos de la base de datos
    y transformarlos en formatos útiles para análisis y visualización.
    """
    
    @staticmethod
    def process_top_establishments(data_estadistica, limit=10):
        """
        Procesar y obtener los top establecimientos por número de pedidos.
        
        Args:
            data_estadistica (dict): Datos estadísticos de la API
            limit (int): Número máximo de establecimientos a retornar
            
        Returns:
            pd.DataFrame: DataFrame con establecimientos ordenados por total de pedidos
        """
        # Validación de datos de entrada
        if not data_estadistica or not data_estadistica.get("success"):
            return pd.DataFrame()
        
        pedidos = data_estadistica["data"]["detalle"]["general"]["todos"]
        df = pd.DataFrame(pedidos)
        
        # Verificar que existan las columnas necesarias
        if df.empty or "name_restaurant" not in df.columns:
            return pd.DataFrame()
        
        # Limpiar y filtrar datos
        df["order_completion_date"] = pd.to_datetime(df["order_completion_date"], errors='coerce')
        df_filtered = df.dropna(subset=["name_restaurant", "order_completion_date"])
        
        # Agrupar por establecimiento y contar pedidos
        top_establishments = (df_filtered
                            .groupby("name_restaurant")
                            .size()
                            .reset_index(name="total_pedidos")
                            .sort_values("total_pedidos", ascending=False)
                            .head(limit))
        
        return top_establishments
    
    @staticmethod
    def process_establishments_orders(data_estadistica):
        """
        Procesar datos de establecimientos y pedidos agrupados por día.
        
        Args:
            data_estadistica (dict): Datos estadísticos de la API
            
        Returns:
            pd.DataFrame: DataFrame con métricas diarias de establecimientos y pedidos
        """
        # Validación de datos de entrada
        if not data_estadistica or not data_estadistica.get("success"):
            return pd.DataFrame()
        
        df = pd.DataFrame(data_estadistica["data"]["detalle"]["general"]["todos"])
        if df.empty:
            return pd.DataFrame()
        
        # Convertir fechas y extraer solo la fecha (sin hora)
        df["fecha"] = pd.to_datetime(df["order_completion_date"]).dt.date
        
        # Calcular pedidos totales por día
        df_pedidos_diarios = df.groupby("fecha").size().reset_index(name="total_pedidos")
        
        # Calcular establecimientos únicos por día
        df_establecimientos_diarios = df.groupby("fecha")["id_restaurant"].nunique().reset_index(name="total_establecimientos")
        
        # Combinar ambos datasets
        df_merged = pd.merge(df_pedidos_diarios, df_establecimientos_diarios, on="fecha", how="outer").fillna(0)
        
        # Formatear datos para presentación
        df_merged["fecha"] = pd.to_datetime(df_merged["fecha"])
        df_merged["total_establecimientos"] = df_merged["total_establecimientos"].astype(int)
        df_merged["total_pedidos"] = df_merged["total_pedidos"].astype(int)
        df_merged = df_merged.rename(columns={
            "fecha": "Fecha", 
            "total_establecimientos": "Establecimientos", 
            "total_pedidos": "Pedidos"
        })
        
        # Calcular promedio de pedidos por establecimiento
        df_merged["Promedio"] = df_merged["Pedidos"] / df_merged["Establecimientos"].replace(0, np.nan)
        
        return df_merged
    
    @staticmethod
    def process_hourly_orders(data, fecha):
        """
        Procesar pedidos por hora para una fecha específica.
        
        Args:
            data (dict): Datos de pedidos de la API
            fecha (date): Fecha específica para analizar
            
        Returns:
            pd.DataFrame: DataFrame con conteo de pedidos por hora (8 AM - 11 PM)
        """
        # Validación de datos de entrada
        if not data or not data.get("success"):
            return pd.DataFrame()
        
        pedidos = data["data"]["detalle"]["general"]["todos"]
        df = pd.DataFrame(pedidos)
        
        if df.empty:
            return pd.DataFrame()
        
        # Filtrar por fecha específica
        df["creacion"] = pd.to_datetime(df["order_completion_date"], errors='coerce')
        df_filtrado = df.loc[df["creacion"].dt.date == fecha].copy()
        
        if df_filtrado.empty:
            return pd.DataFrame()
        
        # Extraer hora y filtrar horario comercial (8 AM - 11 PM)
        df_filtrado.loc[:, "hora"] = df_filtrado["creacion"].dt.hour
        df_horario = df_filtrado[(df_filtrado["hora"] >= 8) & (df_filtrado["hora"] <= 23)]
        
        # Contar pedidos por hora
        conteo_hora = df_horario.groupby("hora").size()
        horas_rango = pd.DataFrame({"hora": range(8, 24)})
        contador_final = horas_rango.merge(conteo_hora.reset_index(name="pedidos"), on="hora", how="left").fillna(0)
        
        # Formatear etiquetas de hora para presentación
        contador_final["etiqueta_hora"] = contador_final["hora"].apply(
            lambda x: f"{x - 12}:00 PM" if x > 12 else f"{x}:00 AM" if x < 12 else "12:00 PM"
        )
        
        return contador_final
    
    @staticmethod
    def process_concurrency(df, fecha):
        """
        Procesar y analizar la concurrencia de pedidos para una fecha específica.
        
        Calcula cuántos pedidos están siendo procesados simultáneamente en cada momento,
        identificando picos de concurrencia y generando visualizaciones.
        
        Args:
            df (pd.DataFrame): DataFrame con datos de pedidos
            fecha (date): Fecha específica para analizar
            
        Returns:
            tuple: (figura_plotly, max_concurrencia, hora_inicio_pico, hora_fin_pico, df_concurrencia)
        """
        # Validación de datos de entrada
        if df.empty:
            return None, None, None, None, None
        
        # Filtrar por fecha específica
        df_filtrado = df.loc[pd.to_datetime(df["order_acceptance_date"]).dt.date == fecha].copy()
        
        if df_filtrado.empty:
            return None, None, None, None, None
        
        # Convertir fechas de asignación y entrega
        df_filtrado.loc[:, "asignacion"] = pd.to_datetime(df_filtrado["order_acceptance_date"])
        df_filtrado.loc[:, "entrega"] = pd.to_datetime(df_filtrado["order_completion_date"], errors='coerce')
        
        # Eliminar registros sin fecha de entrega
        df_filtrado = df_filtrado.dropna(subset=["entrega"])
        
        if df_filtrado.empty:
            return None, None, None, None, None
        
        # Crear segmentos de tiempo por minuto
        min_time = df_filtrado["asignacion"].min()
        max_time = df_filtrado["entrega"].max()
        segmentos = pd.date_range(start=min_time.floor("h"), end=max_time.ceil("h"), freq="1min")
        
        # Calcular concurrencia para cada segmento
        concurrencia = []
        for i in range(len(segmentos) - 1):
            inicio_seg = segmentos[i]
            fin_seg = segmentos[i + 1]
            # Contar pedidos activos en este segmento
            contador = ((df_filtrado["asignacion"] <= fin_seg) & (df_filtrado["entrega"] >= inicio_seg)).sum()
            concurrencia.append(contador)
        
        # Crear DataFrame de resultados
        df_concurrencia = pd.DataFrame({"Hora": segmentos[:-1], "Pedidos_Simultaneos": concurrencia})
        
        # Identificar pico de concurrencia
        max_idx = np.argmax(concurrencia)
        max_concurrencia = int(concurrencia[max_idx])
        mejor_inicio = segmentos[max_idx]
        mejor_fin = segmentos[max_idx + 1]
        
        # Crear visualización con Plotly
        fig = go.Figure()
        
        # Línea principal de concurrencia
        fig.add_trace(go.Scatter(
            x=segmentos[:-1], 
            y=concurrencia, 
            mode="lines", 
            name="Pedidos concurrentes", 
            line=dict(color="Cyan", width=2), 
            hovertemplate='<b>%{x|%H:%M}</b><br>Pedidos: %{y}'
        ))
        
        # Línea de máxima concurrencia
        fig.add_trace(go.Scatter(
            x=[mejor_inicio, mejor_fin], 
            y=[max_concurrencia, max_concurrencia], 
            mode="lines", 
            name="Máxima Concurrencia", 
            line=dict(color="Red", width=6, dash="dash"), 
            hovertemplate=f"Máximo: {max_concurrencia} pedidos"
        ))
        
        # Configurar layout del gráfico
        fig.update_layout(
            title=f"Concurrencia de Pedidos {fecha}", 
            xaxis_title="Hora", 
            yaxis_title="Pedidos Simultáneos", 
            hovermode="x unified", 
            showlegend=True
        )
        
        return fig, max_concurrencia, mejor_inicio, mejor_fin, df_concurrencia
    
    @staticmethod
    def calculate_weekly_data(data_estadistica, data_type="pedidos", selected_year=None):
        """
        Calcular y procesar datos agrupados por semana.
        
        Procesa datos de pedidos o créditos agrupándolos por semanas del año,
        con manejo especial de números de semana y rangos de fechas.
        
        Args:
            data_estadistica (dict): Datos estadísticos de la API
            data_type (str): Tipo de datos a procesar ("pedidos" o "creditos")
            selected_year (int): Año específico para filtrar datos
            
        Returns:
            pd.DataFrame: DataFrame con datos agrupados por semana
        """
        # Validación de datos de entrada
        if data_estadistica is None or not data_estadistica.get("success") or not data_estadistica["data"]["detalle"]["general"]["todos"]:
            return pd.DataFrame()

        df = pd.DataFrame(data_estadistica["data"]["detalle"]["general"]["todos"])

        # Procesamiento específico según tipo de datos
        if data_type == "pedidos":
            if "order_completion_date" not in df.columns:
                return pd.DataFrame()
            df["fecha"] = pd.to_datetime(df["order_completion_date"], errors='coerce').dt.date
            col_valor = "total_pedidos"
            df_agrupado = df.dropna(subset=["fecha"]).groupby("fecha").size().reset_index(name="total_pedidos")
        else:
            if "created_at" not in df.columns:
                return pd.DataFrame()
            df["fecha"] = pd.to_datetime(df["created_at"], errors='coerce').dt.date
            col_valor = "costo_creditos"
            df[col_valor] = pd.to_numeric(df["costo_creditos"], errors="coerce").fillna(0)
            df_agrupado = df.dropna(subset=["fecha"]).groupby("fecha")[col_valor].sum().reset_index()

        if df_agrupado.empty:
            return pd.DataFrame()

        # Filtrar por año seleccionado (por defecto año actual)
        if selected_year is None:
            selected_year = datetime.now().year

        df_agrupado = df_agrupado[pd.to_datetime(df_agrupado['fecha']).dt.year == selected_year].copy()

        if df_agrupado.empty:
            return pd.DataFrame()

        # Calcular números de semana con lógica específica
        df_agrupado["semana"] = DataProcessor._calculate_week_numbers(df_agrupado["fecha"])

        # Agrupar por semana
        semanal = df_agrupado.groupby("semana").agg({col_valor: "sum"}).reset_index()

        # Renombrar columnas según el tipo de datos
        if data_type == "pedidos":
            semanal.rename(columns={col_valor: "pedidos_totales"}, inplace=True)
        else:
            semanal.rename(columns={col_valor: "creditos_totales"}, inplace=True)

        # Calcular rangos de fechas para cada semana
        fecha_inicios = []
        fecha_fins = []
        for week_num in semanal["semana"]:
            week_data = df_agrupado[df_agrupado['semana'] == week_num]['fecha']
            if not week_data.empty:
                min_date = week_data.min()
                max_date = week_data.max()
                fecha_inicios.append(min_date)
                fecha_fins.append(max_date)
            else:
                fecha_inicios.append(None)
                fecha_fins.append(None)

        # Agregar información de rangos de fechas
        semanal["fecha_inicio"] = fecha_inicios
        semanal["fecha_fin"] = fecha_fins
        semanal["rango_fechas"] = semanal.apply(lambda x: f"{x['fecha_inicio'].strftime('%d-%m-%Y')} - {x['fecha_fin'].strftime('%d-%m-%Y')}" if x['fecha_inicio'] else "N/A", axis=1)
        
        return semanal.sort_values("semana")
    
    @staticmethod
    def process_monthly_data(data_estadistica):
        """
        Procesar datos para análisis mensual completo.
        
        Genera múltiples métricas mensuales incluyendo establecimientos activos,
        pedidos totales, créditos utilizados y ratios de eficiencia.
        
        Args:
            data_estadistica (dict): Datos estadísticos de la API
            
        Returns:
            tuple: (df_mensual, df_diario_para_grafico, df_estadistica_procesado)
        """
        # Validación de datos de entrada
        if not data_estadistica or not data_estadistica.get("success"):
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Diccionario para nombres de meses en español
        meses_espanol = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        
        # Preparar DataFrame principal
        df_estadistica = pd.DataFrame(data_estadistica["data"]["detalle"]["general"]["todos"])
        if df_estadistica.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Convertir fechas y crear períodos mensuales
        df_estadistica["fecha_completa"] = pd.to_datetime(df_estadistica["order_completion_date"])
        df_estadistica["created_at"] = pd.to_datetime(df_estadistica["created_at"])
        df_estadistica["mes"] = df_estadistica["fecha_completa"].dt.to_period('M')
        
        # Convertir créditos a numérico
        df_estadistica["creditos"] = pd.to_numeric(df_estadistica["costo_creditos"], errors="coerce").fillna(0)
        
        # Calcular establecimientos activos promedio por mes
        establecimientos_activos_diarios = df_estadistica.groupby([
            df_estadistica["fecha_completa"].dt.date, "mes"
        ])["id_restaurant"].nunique().reset_index()
        establecimientos_activos_diarios.columns = ["fecha", "mes", "establecimientos_activos"]
        establecimientos_promedio_mensual = establecimientos_activos_diarios.groupby("mes")["establecimientos_activos"].mean().reset_index(name="establecimientos_promedio")
        
        # Calcular establecimientos únicos totales por mes
        establecimientos_unicos_totales_mensual = df_estadistica.groupby("mes")["id_restaurant"].nunique().reset_index(name="establecimientos_unicos")
        
        # Calcular pedidos totales por mes
        pedidos_totales_mensual = df_estadistica.groupby("mes").size().reset_index(name="pedidos_totales")
        
        # Combinar métricas mensuales
        df_mensual = pd.merge(establecimientos_promedio_mensual, establecimientos_unicos_totales_mensual, on="mes", how="left")
        df_mensual = pd.merge(df_mensual, pedidos_totales_mensual, on="mes", how="left")
        
        # Agregar créditos mensuales
        mensual_creditos = df_estadistica.groupby("mes").agg({"creditos": "sum"}).reset_index()
        mensual_creditos.columns = ["mes", "creditos_totales"]
        df_mensual = pd.merge(df_mensual, mensual_creditos, on="mes", how="left")
        
        # Calcular ratio pedidos/establecimientos (eficiencia)
        df_mensual = df_mensual.set_index('mes')
        df_mensual["ratio_pedidos_establecimientos"] = df_estadistica.groupby([
            df_estadistica["fecha_completa"].dt.to_period('M'), 
            df_estadistica["fecha_completa"].dt.date
        ]).apply(
            lambda x: x.shape[0] / x["id_restaurant"].nunique() if x["id_restaurant"].nunique() > 0 else np.nan
        ).groupby(level=0).mean().rename("ratio_pedidos_establecimientos")
        df_mensual = df_mensual.reset_index()
        
        # Crear etiquetas de mes en español
        df_mensual["mes_display"] = df_mensual["mes"].apply(lambda x: f"{meses_espanol[x.month]} {x.year}")
        
        # Preparar datos diarios para gráficos de tendencias
        df_diario_para_grafico = df_estadistica.groupby(df_estadistica["fecha_completa"].dt.date).agg(
            total_pedidos=('id_order', 'size'),
            total_establecimientos=('id_restaurant', 'nunique')
        ).reset_index()
        df_diario_para_grafico.columns = ['fecha', 'total_pedidos', 'total_establecimientos']
        df_diario_para_grafico['fecha'] = pd.to_datetime(df_diario_para_grafico['fecha'])
        
        return df_mensual, df_diario_para_grafico, df_estadistica
    
    @staticmethod
    def _calculate_week_numbers(fechas):
        """
        Calcular números de semana con lógica específica del negocio.
        
        Implementa reglas especiales para el cálculo de semanas en años específicos,
        manejando casos especiales para inicio y fin de año.
        
        Args:
            fechas (list): Lista de fechas para calcular números de semana
            
        Returns:
            list: Lista de números de semana correspondientes
        """
        semanas = []
        for fecha_dt in fechas:
            # Normalizar fecha a objeto date
            fecha = fecha_dt.date() if isinstance(fecha_dt, datetime) else fecha_dt
            current_date_year = fecha.year

            week_num = None

            # Reglas específicas para año 2025
            if current_date_year == 2025:
                if datetime(2025, 1, 1).date() <= fecha <= datetime(2025, 1, 5).date():
                    week_num = 1
                elif datetime(2025, 12, 29).date() <= fecha <= datetime(2025, 12, 31).date():
                    week_num = 53
            # Reglas específicas para año 2026
            elif current_date_year == 2026:
                if datetime(2026, 1, 1).date() <= fecha <= datetime(2026, 1, 4).date():
                    week_num = 1
                elif datetime(2026, 1, 5).date() <= fecha <= datetime(2026, 1, 11).date():
                    week_num = 2
                elif datetime(2026, 12, 28).date() <= fecha <= datetime(2026, 12, 31).date():
                    week_num = datetime(2026, 12, 31).isocalendar()[1]
            # Reglas específicas para año 2027
            elif current_date_year == 2027:
                if datetime(2027, 1, 1).date() <= fecha <= datetime(2027, 1, 3).date():
                    week_num = 1
                elif datetime(2027, 1, 4).date() <= fecha <= datetime(2027, 1, 10).date():
                    week_num = 2
                elif datetime(2027, 12, 27).date() <= fecha <= datetime(2027, 12, 31).date():
                    week_num = datetime(2027, 12, 31).isocalendar()[1]

            # Usar cálculo ISO estándar si no hay regla específica
            if week_num is None:
                week_num = fecha.isocalendar()[1]

            semanas.append(week_num)
        return semanas
    
    @staticmethod
    def _add_date_ranges(weekly_data, data_type, selected_year):
        """
        Agregar rangos de fechas a datos semanales procesados.
        
        Calcula y agrega las fechas de inicio y fin para cada semana,
        formateando los rangos para presentación.
        
        Args:
            weekly_data (pd.DataFrame): Datos semanales procesados
            data_type (str): Tipo de datos ("pedidos" o "creditos")
            selected_year (int): Año seleccionado para el análisis
            
        Returns:
            pd.DataFrame: DataFrame con rangos de fechas agregados
        """
        # Definir primera semana del año 2025 (referencia)
        primera_semana_inicio = datetime(2025, 1, 1).date()
        primera_semana_fin = datetime(2025, 1, 5).date()
        
        fecha_inicios = []
        fecha_fins = []
        
        # Calcular rangos para cada semana
        for semana in weekly_data["semana"]:
            if semana == 1:
                # Primera semana tiene fechas fijas
                fecha_inicios.append(primera_semana_inicio)
                fecha_fins.append(primera_semana_fin)
            else:
                # Calcular fechas para semanas subsecuentes
                dias_desde_inicio = (semana - 2) * 7
                inicio_semana = datetime(2025, 1, 6).date() + timedelta(days=dias_desde_inicio)
                fin_semana = inicio_semana + timedelta(days=6)
                fecha_inicios.append(inicio_semana)
                fecha_fins.append(fin_semana)
        
        # Agregar columnas de fechas
        weekly_data["fecha_inicio"] = fecha_inicios
        weekly_data["fecha_fin"] = fecha_fins
        weekly_data["rango_fechas"] = weekly_data.apply(
            lambda x: f"{x['fecha_inicio'].strftime('%d/%m/%Y')} - {x['fecha_fin'].strftime('%d/%m/%Y')}", 
            axis=1
        )
        
        # Renombrar columnas según el tipo de datos
        if data_type == "pedidos":
            weekly_data.rename(columns={"total_pedidos": "pedidos_totales"}, inplace=True)
        else:
            weekly_data.rename(columns={"costo_creditos": "creditos_totales"}, inplace=True)
        
        return weekly_data
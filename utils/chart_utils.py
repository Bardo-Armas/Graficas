"""
Utilidades de Gráficos
=====================

Este módulo contiene la clase ChartUtils que proporciona métodos estáticos
para crear visualizaciones interactivas utilizando Plotly Express y Plotly Graph Objects.

Funcionalidades principales:
- Gráficos de pie para top establecimientos
- Gráficos de líneas para tendencias temporales
- Gráficos de barras para análisis por hora y semana
- Gráficos combinados para análisis de múltiples métricas
- Configuración consistente de colores y estilos
- Tooltips informativos y formateo de datos

La clase está optimizada para trabajar con datos de órdenes y establecimientos,
proporcionando visualizaciones claras y profesionales para el dashboard.
"""

import plotly.express as px
import plotly.graph_objects as go
import numpy as np

class ChartUtils:
    """
    Utilidades para creación de gráficos interactivos.
    
    Esta clase proporciona métodos estáticos para generar diferentes tipos
    de visualizaciones utilizando Plotly, con configuraciones optimizadas
    para el análisis de datos de órdenes y establecimientos.
    """
    
    @staticmethod
    def create_top_establishments_chart(top_10, fecha_inicio, fecha_fin):
        """
        Crear gráfico de pie para mostrar los top establecimientos por pedidos.
        
        Genera un gráfico circular (donut chart) que muestra la distribución
        de pedidos entre los principales establecimientos en un período específico.
        
        Args:
            top_10 (pd.DataFrame): DataFrame con top establecimientos y sus totales
            fecha_inicio (datetime): Fecha de inicio del período analizado
            fecha_fin (datetime): Fecha de fin del período analizado
            
        Returns:
            plotly.graph_objects.Figure: Gráfico de pie interactivo o None si no hay datos
        """
        # Validar que existan datos para procesar
        if top_10.empty:
            return None
        
        # Crear gráfico de pie con configuración profesional
        fig = px.pie(
            top_10, 
            names="name_restaurant",           # Nombres de establecimientos
            values="total_pedidos",            # Valores para el gráfico
            title=f"Top 10 Establecimientos: {fecha_inicio.strftime('%Y-%m-%d')} al {fecha_fin.strftime('%Y-%m-%d')}", 
            color_discrete_sequence=px.colors.qualitative.Pastel,  # Paleta de colores suaves
            hole=0.3,                         # Crear efecto donut
            labels={"name_restaurant": "Establecimiento", "total_pedidos": "Pedidos"}
        )
        
        # Personalizar tooltips para mejor experiencia de usuario
        fig.update_traces(
            hovertemplate="<b>%{label}</b><br>Pedidos: %{value}<br>Porcentaje: %{percent}<extra></extra>"
        )
        
        return fig
    
    @staticmethod
    def create_establishments_orders_chart(df, fecha_inicio, fecha_fin):
        """
        Crear gráfico de líneas múltiples para establecimientos, pedidos y promedio.
        
        Genera un gráfico que muestra la evolución temporal de tres métricas:
        establecimientos activos, total de pedidos y promedio de pedidos por establecimiento.
        
        Args:
            df (pd.DataFrame): DataFrame con datos diarios de establecimientos y pedidos
            fecha_inicio (datetime): Fecha de inicio del período
            fecha_fin (datetime): Fecha de fin del período
            
        Returns:
            plotly.graph_objects.Figure: Gráfico de líneas múltiples o None si no hay datos
        """
        # Validar existencia de datos
        if df.empty:
            return None
        
        # Crear figura con múltiples trazas
        fig = go.Figure()
        
        # Línea para establecimientos activos (verde)
        fig.add_trace(go.Scatter(
            x=df["Fecha"], 
            y=df["Establecimientos"], 
            name="Establecimientos", 
            line=dict(color="green")
        ))
        
        # Línea para total de pedidos (naranja)
        fig.add_trace(go.Scatter(
            x=df["Fecha"], 
            y=df["Pedidos"], 
            name="Pedidos", 
            line=dict(color="orange")
        ))
        
        # Línea para promedio de pedidos por establecimiento (azul)
        fig.add_trace(go.Scatter(
            x=df["Fecha"], 
            y=df["Promedio"], 
            name="Promedio", 
            line=dict(color="blue")
        ))
        
        # Configurar layout del gráfico
        fig.update_layout(
            title=f"Pedidos y Establecimientos: {fecha_inicio.strftime('%Y-%m-%d')} al {fecha_fin.strftime('%Y-%m-%d')}", 
            xaxis_title="Fecha", 
            yaxis_title="Cantidad", 
            hovermode="x unified"  # Mostrar todos los valores en el mismo tooltip
        )
        
        return fig
    
    @staticmethod
    def create_hourly_orders_chart(contador_final, fecha):
        """
        Crear gráfico de barras para análisis de pedidos por hora.
        
        Genera un gráfico de barras que muestra la distribución de pedidos
        a lo largo del día en horario comercial (8 AM - 11 PM).
        
        Args:
            contador_final (pd.DataFrame): DataFrame con conteo de pedidos por hora
            fecha (datetime): Fecha específica del análisis
            
        Returns:
            plotly.graph_objects.Figure: Gráfico de barras por hora o None si no hay datos
        """
        # Validar existencia de datos
        if contador_final.empty:
            return None
        
        # Crear gráfico de barras con gradiente de color
        fig = px.bar(
            contador_final, 
            x="etiqueta_hora",                # Etiquetas de hora formateadas (AM/PM)
            y="pedidos",                      # Cantidad de pedidos
            title=f"Pedidos por hora - {fecha.strftime('%Y-%m-%d')}", 
            labels={"etiqueta_hora": "Hora", "pedidos": "Pedidos"}, 
            color="pedidos",                  # Colorear barras según valor
            color_continuous_scale="blues"    # Escala de colores azules
        )
        
        # Personalizar tooltips y etiquetas de datos
        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>Pedidos: %{y}<extra></extra>", 
            texttemplate="%{y}",              # Mostrar valor encima de cada barra
            textposition="outside"            # Posicionar texto fuera de la barra
        )
        
        return fig
    
    @staticmethod
    def create_weekly_chart(weekly_data, data_type="pedidos"):
        """
        Crear gráfico de barras para análisis semanal de pedidos o créditos.
        
        Genera un gráfico de barras que muestra datos agrupados por semana,
        con configuración específica según el tipo de datos (pedidos o créditos).
        
        Args:
            weekly_data (pd.DataFrame): DataFrame con datos semanales procesados
            data_type (str): Tipo de datos ("pedidos" o "creditos")
            
        Returns:
            plotly.graph_objects.Figure: Gráfico de barras semanal o None si no hay datos
        """
        # Validar existencia de datos
        if weekly_data.empty:
            return None
        
        # Configurar parámetros según tipo de datos
        if data_type == "pedidos":
            y_col = "pedidos_totales"
            title = "Pedidos por Semana"
            y_label = "Total Pedidos"
            color_scale = "reds"              # Escala de rojos para pedidos
        else:
            y_col = "creditos_totales"
            title = "Créditos por Semana"
            y_label = "Total Créditos"
            color_scale = "turbo"             # Escala multicolor para créditos
        
        # Crear gráfico de barras con información adicional en hover
        fig = px.bar(
            weekly_data, 
            x="semana",                       # Número de semana
            y=y_col,                         # Columna de valores según tipo
            title=title, 
            labels={"semana": "Semana", y_col: y_label}, 
            hover_data=["rango_fechas"],     # Mostrar rango de fechas en tooltip
            color=y_col,                     # Colorear según valor
            color_continuous_scale=color_scale
        )
        
        # Personalizar tooltips con formato de números
        fig.update_traces(
            hovertemplate=f"<b>Semana %{{x}}</b><br>%{{customdata[0]}}<br>{y_label}: %{{y:,}}<extra></extra>", 
            texttemplate="%{y:,}",           # Formato con separadores de miles
            textposition="outside"
        )
        
        return fig
    
    @staticmethod
    def create_monthly_trends_chart(df_diario_mes, mes_seleccionado):
        """
        Crear gráfico de tendencias diarias para un mes específico.
        
        Genera un gráfico de líneas múltiples que muestra la evolución diaria
        de establecimientos, pedidos y ratio durante un mes seleccionado.
        
        Args:
            df_diario_mes (pd.DataFrame): DataFrame con datos diarios del mes
            mes_seleccionado (str): Nombre del mes seleccionado para el título
            
        Returns:
            plotly.graph_objects.Figure: Gráfico de tendencias mensuales o None si no hay datos
        """
        # Validar existencia de datos
        if df_diario_mes.empty:
            return None
        
        # Crear figura con múltiples líneas de tendencia
        fig = go.Figure()
        
        # Línea de establecimientos activos (verde)
        fig.add_trace(go.Scatter(
            x=df_diario_mes["fecha"], 
            y=df_diario_mes["total_establecimientos"], 
            name="Establecimientos", 
            line=dict(color="green")
        ))
        
        # Línea de pedidos totales (naranja)
        fig.add_trace(go.Scatter(
            x=df_diario_mes["fecha"], 
            y=df_diario_mes["total_pedidos"], 
            name="Pedidos", 
            line=dict(color="orange")
        ))
        
        # Línea de ratio pedidos/establecimientos (azul)
        fig.add_trace(go.Scatter(
            x=df_diario_mes["fecha"], 
            y=df_diario_mes["ratio"], 
            name="Ratio", 
            line=dict(color="blue")
        ))
        
        # Configurar layout para mejor visualización
        fig.update_layout(
            hovermode="x unified",            # Tooltip unificado por fecha
            title=f"Tendencias diarias - {mes_seleccionado}",
            xaxis_title="Fecha",
            yaxis_title="Cantidad"
        )
        
        return fig
    
    @staticmethod
    def create_credits_weekly_chart(df_combinado):
        """
        Crear gráfico semanal de créditos con información detallada.
        
        Genera un gráfico de barras especializado para análisis de créditos,
        incluyendo información adicional como pedidos totales y créditos por pedido.
        
        Args:
            df_combinado (pd.DataFrame): DataFrame con datos combinados de créditos y pedidos
            
        Returns:
            plotly.graph_objects.Figure: Gráfico de créditos semanal o None si no hay datos
        """
        # Validar existencia de datos
        if df_combinado.empty:
            return None
        
        # Crear gráfico de barras con información extendida en hover
        fig = px.bar(
            df_combinado, 
            x="semana", 
            y="creditos_totales", 
            title="Créditos por Semana", 
            labels={"semana": "Semana", "creditos_totales": "Total Créditos"}, 
            hover_data=["rango_fechas", "pedidos_totales", "creditos_por_pedido"],  # Datos adicionales
            color="creditos_totales", 
            color_continuous_scale="turbo"    # Escala de colores vibrante
        )
        
        # Tooltip personalizado con múltiples métricas
        fig.update_traces(
            hovertemplate="<b>Semana %{x}</b><br>%{customdata[0]}<br>Créditos: %{y:,}<br>Pedidos: %{customdata[1]:,}<br>Créditos/Pedido: $%{customdata[2]:.2f}<extra></extra>", 
            texttemplate="%{y:,}",           # Mostrar valor formateado
            textposition="outside"
        )
        
        return fig
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

class ChartUtils:
    @staticmethod
    def create_top_establishments_chart(top_10, fecha_inicio, fecha_fin):
        """Crear gráfico de top establecimientos con configuración consistente"""
        if top_10.empty:
            return None
        
        fig = px.pie(
            top_10, 
            names="name_restaurant", 
            values="total_pedidos", 
            title=f"Top 10 Establecimientos: {fecha_inicio.strftime('%Y-%m-%d')} al {fecha_fin.strftime('%Y-%m-%d')}", 
            color_discrete_sequence=px.colors.qualitative.Pastel, 
            hole=0.3, 
            labels={"name_restaurant": "Establecimiento", "total_pedidos": "Pedidos"}
        )
        
        fig.update_traces(
            hovertemplate="<b>%{label}</b><br>Pedidos: %{value}<br>Porcentaje: %{percent}<extra></extra>"
        )
        
        return fig
    
    @staticmethod
    def create_establishments_orders_chart(df, fecha_inicio, fecha_fin):
        """Crear gráfico de establecimientos y pedidos"""
        if df.empty:
            return None
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["Fecha"], 
            y=df["Establecimientos"], 
            name="Establecimientos", 
            line=dict(color="green")
        ))
        fig.add_trace(go.Scatter(
            x=df["Fecha"], 
            y=df["Pedidos"], 
            name="Pedidos", 
            line=dict(color="orange")
        ))
        fig.add_trace(go.Scatter(
            x=df["Fecha"], 
            y=df["Promedio"], 
            name="Promedio", 
            line=dict(color="blue")
        ))
        
        fig.update_layout(
            title=f"Pedidos y Establecimientos: {fecha_inicio.strftime('%Y-%m-%d')} al {fecha_fin.strftime('%Y-%m-%d')}", 
            xaxis_title="Fecha", 
            yaxis_title="Cantidad", 
            hovermode="x unified"
        )
        
        return fig
    
    @staticmethod
    def create_hourly_orders_chart(contador_final, fecha):
        """Crear gráfico de pedidos por hora"""
        if contador_final.empty:
            return None
        
        fig = px.bar(
            contador_final, 
            x="etiqueta_hora", 
            y="pedidos", 
            title=f"Pedidos por hora - {fecha.strftime('%Y-%m-%d')}", 
            labels={"etiqueta_hora": "Hora", "pedidos": "Pedidos"}, 
            color="pedidos", 
            color_continuous_scale="blues"
        )
        
        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>Pedidos: %{y}<extra></extra>", 
            texttemplate="%{y}", 
            textposition="outside"
        )
        
        return fig
    
    @staticmethod
    def create_weekly_chart(weekly_data, data_type="pedidos"):
        """Crear gráfico semanal con configuración mejorada"""
        if weekly_data.empty:
            return None
        
        if data_type == "pedidos":
            y_col = "pedidos_totales"
            title = "Pedidos por Semana"
            y_label = "Total Pedidos"
            color_scale = "reds"
        else:
            y_col = "creditos_totales"
            title = "Créditos por Semana"
            y_label = "Total Créditos"
            color_scale = "turbo"
        
        fig = px.bar(
            weekly_data, 
            x="semana", 
            y=y_col, 
            title=title, 
            labels={"semana": "Semana", y_col: y_label}, 
            hover_data=["rango_fechas"], 
            color=y_col, 
            color_continuous_scale=color_scale
        )
        
        fig.update_traces(
            hovertemplate=f"<b>Semana %{{x}}</b><br>%{{customdata[0]}}<br>{y_label}: %{{y:,}}<extra></extra>", 
            texttemplate="%{y:,}", 
            textposition="outside"
        )
        
        return fig
    
    @staticmethod
    def create_monthly_trends_chart(df_diario_mes, mes_seleccionado):
        """Crear gráfico de tendencias mensuales"""
        if df_diario_mes.empty:
            return None
        
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
            title=f"Tendencias diarias - {mes_seleccionado}",
            xaxis_title="Fecha",
            yaxis_title="Cantidad"
        )
        
        return fig
    
    @staticmethod
    def create_credits_weekly_chart(df_combinado):
        """Crear gráfico semanal de créditos con información adicional"""
        if df_combinado.empty:
            return None
        
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
            hovertemplate="<b>Semana %{x}</b><br>%{customdata[0]}<br>Créditos: %{y:,}<br>Pedidos: %{customdata[1]:,}<br>Créditos/Pedido: $%{customdata[2]:.2f}<extra></extra>", 
            texttemplate="%{y:,}", 
            textposition="outside"
        )
        
        return fig
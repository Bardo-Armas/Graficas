import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor
from textwrap import dedent
import pyodbc


st.set_page_config(page_title="Dashboard Integrado", page_icon="📊", layout="wide")

def get_db_connection():
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_DATABASE')
    username = os.getenv('DB_USERNAME')
    password = os.getenv('DB_PASSWORD')
    driver = os.getenv('DB_DRIVER', '{ODBC Driver 17 for SQL Server}')
    conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    return pyodbc.connect(conn_str)


def obtener_datos_estadistica(fecha_inicio, fecha_fin):
    query = dedent(f"""
        SELECT
            id_order,
            order_completion_date,
            order_acceptance_date,
            costo_creditos,
            id_restaurant,
            name_restaurant,
            created_at
        FROM orders_details
        WHERE CONVERT(DATE, order_completion_date) >= '{fecha_inicio}'
          AND CONVERT(DATE, order_completion_date) <= '{fecha_fin}'
    """)

    try:
        conn = get_db_connection()
        df = pd.read_sql(query, conn)
        conn.close()

        data = {
            "success": True,
            "data": {
                "detalle": {
                    "general": {
                        "todos": df.to_dict('records')
                    }
                }
            }
        }
        return data
    except Exception as e:
        st.error(f"Error al obtener datos de la base de datos: {str(e)}")
        return None

def procesar_top_establecimientos(data_estadistica):
    pedidos = data_estadistica["data"]["detalle"]["general"]["todos"]
    df = pd.DataFrame(pedidos)
    df["order_completion_date"] = pd.to_datetime(df["order_completion_date"])

    df_filtered = df.dropna(subset=["name_restaurant"])

    top_10 = df_filtered.groupby("name_restaurant").size().reset_index(name="total_pedidos")
    top_10 = top_10.sort_values("total_pedidos", ascending=False).head(10)

    return top_10

def procesar_establecimientos_pedidos(data_estadistica):
    df = pd.DataFrame(data_estadistica["data"]["detalle"]["general"]["todos"])
    df["fecha"] = pd.to_datetime(df["order_completion_date"]).dt.date

    df_pedidos_diarios = df.groupby("fecha").size().reset_index(name="total_pedidos")

    df_establecimientos_diarios = df.groupby("fecha")["id_restaurant"].nunique().reset_index(name="total_establecimientos")

    df_merged = pd.merge(df_pedidos_diarios, df_establecimientos_diarios, on="fecha", how="outer").fillna(0)

    df_merged["fecha"] = pd.to_datetime(df_merged["fecha"])
    df_merged["total_establecimientos"] = df_merged["total_establecimientos"].astype(int)
    df_merged["total_pedidos"] = df_merged["total_pedidos"].astype(int)
    df_merged = df_merged.rename(columns={"fecha": "Fecha", "total_establecimientos": "Establecimientos", "total_pedidos": "Pedidos"})
    df_merged["Promedio"] = df_merged["Pedidos"] / df_merged["Establecimientos"].replace(0, np.nan)
    return df_merged

def procesar_pedidos_hora(data, fecha):
    pedidos = data["data"]["detalle"]["general"]["todos"]
    df = pd.DataFrame(pedidos)
    df["creacion"] = pd.to_datetime(df["order_completion_date"])
    df_filtrado = df.loc[df["creacion"].dt.date == fecha].copy()
    df_filtrado.loc[:, "hora"] = df_filtrado["creacion"].dt.hour
    df_horario = df_filtrado[(df_filtrado["hora"]>=8)&(df_filtrado["hora"]<=23)]
    conteo_hora = df_horario.groupby("hora").size()
    horas_rango = pd.DataFrame({"hora": range(8,23)})
    contador_final = horas_rango.merge(conteo_hora.reset_index(name="pedidos"), on="hora", how="left").fillna(0)
    contador_final["etiqueta_hora"] = contador_final["hora"].apply(lambda x: f"{x - 12}:00 PM" if x > 12 else f"{x}:00 AM" if x < 12 else "12:00 PM")
    return contador_final

def procesar_concurrencias(df, fecha):
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
    for i in range(len(segmentos)-1):
        inicio_seg = segmentos[i]
        fin_seg = segmentos[i+1]
        contador = ((df_filtrado["asignacion"]<=fin_seg)&(df_filtrado["entrega"]>=inicio_seg)).sum()
        concurrencia.append(contador)

    df_concurrencia = pd.DataFrame({"Hora": segmentos[:-1], "Pedidos_Simultaneos": concurrencia})

    max_idx = np.argmax(concurrencia)
    max_concurrencia = int(concurrencia[max_idx])
    mejor_inicio = segmentos[max_idx]
    mejor_fin = segmentos[max_idx+1]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=segmentos[:-1], y=concurrencia, mode="lines", name="Pedidos concurrentes", line=dict(color="Cyan", width=2), hovertemplate='<b>%{x|%H:%M}</b><br>Pedidos: %{y}'))
    fig.add_trace(go.Scatter(x=[mejor_inicio, mejor_fin], y=[max_concurrencia, max_concurrencia], mode="lines", name="Máxima Concurrencia", line=dict(color="Red", width=6, dash="dash"), hovertemplate=f"Máximo: {max_concurrencia} pedidos"))
    fig.update_layout(title=f"Concurrencia de Pedidos {fecha.strftime('%d-%m-%Y')}", xaxis_title="Hora", yaxis_title="Pedidos Simultáneos", hovermode="x unified", showlegend=True)
    return fig, max_concurrencia, mejor_inicio, mejor_fin, df_concurrencia

def grafico_top_establecimientos(top_10, fecha_inicio, fecha_fin):
    fig = px.pie(top_10, names="name_restaurant", values="total_pedidos", title=f"Top 10 Establecimientos: {fecha_inicio.strftime('%d-%m-%Y')} al {fecha_fin.strftime('%d-%m-%Y')}", color_discrete_sequence=px.colors.qualitative.Pastel, hole=0.3, labels={"name_restaurant": "Establecimiento", "total_pedidos":"Pedidos"})
    return fig

def grafico_establecimientos_pedidos(df, fecha_inicio, fecha_fin):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Fecha"], y=df["Establecimientos"], name="Establecimientos", line=dict(color="green")))
    fig.add_trace(go.Scatter(x=df["Fecha"], y=df["Pedidos"], name="Pedidos", line=dict(color="orange")))
    fig.add_trace(go.Scatter(x=df["Fecha"], y=df["Promedio"], name="Promedio", line=dict(color="blue")))
    fig.update_layout(title=f"Pedidos y Establecimientos: {fecha_inicio.strftime('%d-%m-%Y')} al {fecha_fin.strftime('%d-%m-%Y')}", xaxis_title="Fecha", yaxis_title="Cantidad", hovermode="x unified")
    return fig

def grafico_pedidos_hora(contador_final, fecha):
    fig = px.bar(contador_final, x="etiqueta_hora", y="pedidos", title=f"Pedidos por hora - {fecha.strftime('%d-%m-%Y')}", labels={"etiqueta_hora": "Hora", "pedidos": "Pedidos"}, color="pedidos", color_continuous_scale="blues")
    fig.update_traces(hovertemplate="<b>%{x}</b><br>Pedidos: %{y}", texttemplate="%{y}", textposition="outside")
    return fig

def obtener_datos_creditos(fecha_inicio, fecha_fin):
    return obtener_datos_estadistica(fecha_inicio, fecha_fin)

def calcular_semanas(fechas, selected_year):
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

def procesar_datos_semanales(data_estadistica, tipo, selected_year):
    if data_estadistica is None or not data_estadistica.get("success") or not data_estadistica["data"]["detalle"]["general"]["todos"]:
        return pd.DataFrame()

    df = pd.DataFrame(data_estadistica["data"]["detalle"]["general"]["todos"])

    if tipo == "pedidos":
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

    df_agrupado = df_agrupado[pd.to_datetime(df_agrupado['fecha']).dt.year == selected_year].copy()

    if df_agrupado.empty:
        return pd.DataFrame()

    df_agrupado["semana"] = calcular_semanas(df_agrupado["fecha"], selected_year)

    semanal = df_agrupado.groupby("semana").agg({col_valor: "sum"}).reset_index()

    if tipo == "pedidos":
        semanal.rename(columns={col_valor: "pedidos_totales"}, inplace=True)
    else:
        semanal.rename(columns={col_valor: "creditos_totales"}, inplace=True)

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

    semanal["fecha_inicio"] = fecha_inicios
    semanal["fecha_fin"] = fecha_fins
    semanal["rango_fechas"] = semanal.apply(lambda x: f"{x['fecha_inicio'].strftime('%d-%m-%Y')} - {x['fecha_fin'].strftime('%d-%m-%Y')}" if x['fecha_inicio'] else "N/A", axis=1)
    return semanal.sort_values("semana")

def procesar_datos_para_analisis_mensual(data_estadistica):
    meses_espanol = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    df_estadistica = pd.DataFrame(data_estadistica["data"]["detalle"]["general"]["todos"])
    df_estadistica["fecha_completa"] = pd.to_datetime(df_estadistica["order_completion_date"])
    df_estadistica["created_at"] = pd.to_datetime(df_estadistica["created_at"])
    df_estadistica["mes"] = df_estadistica["fecha_completa"].dt.to_period('M')

    df_estadistica["creditos"] = pd.to_numeric(df_estadistica["costo_creditos"], errors="coerce").fillna(0)

    establecimientos_activos_diarios = df_estadistica.groupby([df_estadistica["fecha_completa"].dt.date, "mes"])["id_restaurant"].nunique().reset_index()
    establecimientos_activos_diarios.columns = ["fecha", "mes", "establecimientos_activos"]
    establecimientos_promedio_mensual = establecimientos_activos_diarios.groupby("mes")["establecimientos_activos"].mean().reset_index(name="establecimientos_promedio")

    establecimientos_unicos_totales_mensual = df_estadistica.groupby("mes")["id_restaurant"].nunique().reset_index(name="establecimientos_unicos")

    pedidos_totales_mensual = df_estadistica.groupby("mes").size().reset_index(name="pedidos_totales")

    df_mensual = pd.merge(establecimientos_promedio_mensual, establecimientos_unicos_totales_mensual, on="mes", how="left")
    df_mensual = pd.merge(df_mensual, pedidos_totales_mensual, on="mes", how="left")

    mensual_creditos = df_estadistica.groupby("mes").agg({
        "creditos": "sum"
    }).reset_index()
    mensual_creditos.columns = ["mes", "creditos_totales"]

    df_mensual = pd.merge(df_mensual, mensual_creditos, on="mes", how="left")

    df_mensual = df_mensual.set_index('mes')
    df_mensual["ratio_pedidos_establecimientos"] = df_estadistica.groupby([df_estadistica["fecha_completa"].dt.to_period('M'), df_estadistica["fecha_completa"].dt.date]).apply(
        lambda x: x.shape[0] / x["id_restaurant"].nunique() if x["id_restaurant"].nunique() > 0 else np.nan
    ).groupby(level=0).mean().rename("ratio_pedidos_establecimientos")
    df_mensual = df_mensual.reset_index()

    df_mensual["mes_display"] = df_mensual["mes"].apply(lambda x: f"{meses_espanol[x.month]} {x.year}")

    df_diario_para_grafico = df_estadistica.groupby(df_estadistica["fecha_completa"].dt.date).agg(
        total_pedidos=('id_order', 'size'),
        total_establecimientos=('id_restaurant', 'nunique')
    ).reset_index()
    df_diario_para_grafico.columns = ['fecha', 'total_pedidos', 'total_establecimientos']
    df_diario_para_grafico['fecha'] = pd.to_datetime(df_diario_para_grafico['fecha'])

    return df_mensual, df_diario_para_grafico, df_estadistica

def analisis_mensual():
    st.title("📈Análisis Estadístico Mensual")
    fecha_fin = datetime.now().date()
    fecha_inicio = datetime(2025, 1, 1).date()

    with st.sidebar:
        st.header("Mes")
        meses_periodo = pd.period_range(start=fecha_inicio, end=fecha_fin, freq="M")
        meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio",
                 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
        meses_disponibles = [f"{meses[p.month]} {p.year}" for p in meses_periodo]
        mes_seleccionado = st.selectbox("Seleccionar Mes", meses_disponibles, index=len(meses_disponibles)-1)
        if st.button("Actualizar Datos"):
            st.cache_data.clear()

    with st.spinner("Cargando Datos"):
        data_estadistica = obtener_datos_estadistica(fecha_inicio, fecha_fin)

        if data_estadistica is None:
            st.error("No se pudieron cargar los datos")
            return

        df_mensual, df_diario_para_grafico, df_estadistica_completa = procesar_datos_para_analisis_mensual(data_estadistica)

    st.subheader(f"Resumen de {mes_seleccionado}")

    mes_actual = df_mensual[df_mensual["mes_display"]==mes_seleccionado].iloc[0]
    mes_num = [k for k, v in meses.items() if v == mes_seleccionado.split()[0]][0]
    anio = int(mes_seleccionado.split()[1])

    mes_actual_period = mes_actual["mes"]
    mes_anterior_period = mes_actual_period.asfreq('M') - 1

    mes_anterior = df_mensual[df_mensual["mes"] == mes_anterior_period]

    df_diario_mes = df_diario_para_grafico[(df_diario_para_grafico["fecha"].dt.month == mes_num) & (df_diario_para_grafico["fecha"].dt.year == anio)].copy()

    pedidos_promedio_general = df_diario_mes["total_pedidos"].mean() if not df_diario_mes.empty else 0


    col1, col2, col3, col4, col5, col6 = st.columns(6)

    if not mes_anterior.empty:
        mes_anterior_data = mes_anterior.iloc[0]

        df_diario_mes_anterior = df_diario_para_grafico[(df_diario_para_grafico["fecha"].dt.month == mes_anterior_period.month) & (df_diario_para_grafico["fecha"].dt.year == mes_anterior_period.year)].copy()

        pedidos_promedio_general_ant = df_diario_mes_anterior["total_pedidos"].mean() if not df_diario_mes_anterior.empty else 0

        delta_est_prom = ((mes_actual["establecimientos_promedio"] - mes_anterior_data["establecimientos_promedio"]) / mes_anterior_data["establecimientos_promedio"]) * 100 if mes_anterior_data["establecimientos_promedio"] > 0 else 0
        delta_est_tot = ((mes_actual["establecimientos_unicos"] - mes_anterior_data["establecimientos_unicos"]) / mes_anterior_data["establecimientos_unicos"]) * 100 if mes_anterior_data["establecimientos_unicos"] > 0 else 0
        delta_ped_tot = ((mes_actual["pedidos_totales"] - mes_anterior_data["pedidos_totales"]) / mes_anterior_data["pedidos_totales"]) * 100 if mes_anterior_data["pedidos_totales"] > 0 else 0
        delta_ratio = ((mes_actual["ratio_pedidos_establecimientos"] - mes_anterior_data["ratio_pedidos_establecimientos"]) / mes_anterior_data["ratio_pedidos_establecimientos"]) * 100 if mes_anterior_data["ratio_pedidos_establecimientos"] > 0 else 0
        delta_creditos = ((mes_actual["creditos_totales"] - mes_anterior_data["creditos_totales"]) / mes_anterior_data["creditos_totales"]) * 100 if mes_anterior_data["creditos_totales"] > 0 else 0

        delta_ped_prom_general = ((pedidos_promedio_general - pedidos_promedio_general_ant)/pedidos_promedio_general_ant)*100 if pedidos_promedio_general_ant > 0 else 0

        col1.metric("Establecimientos Activos Promedio", f"{mes_actual['establecimientos_promedio']:.0f}", f"{delta_est_prom:.1f}%", delta_color="normal")
        col2.metric("Establecimientos Activos Totales", f"{mes_actual['establecimientos_unicos']:,.0f}", f"{delta_est_tot:.1f}%", delta_color="normal")
        col3.metric("Pedidos Totales Realizados", f"{mes_actual['pedidos_totales']:,.0f}", f"{delta_ped_tot:.1f}%", delta_color="normal")
        col4.metric("Ratio Pedidos/Establecimientos", f"{mes_actual['ratio_pedidos_establecimientos']:.2f}", f"{delta_ratio:.1f}%", delta_color="normal")
        col5.metric("Créditos Totales Utilizados", f"{mes_actual['creditos_totales']:,.0f}", f"{delta_creditos:.1f}%", delta_color="normal")
        col6.metric("Pedidos (promedio)", f"{pedidos_promedio_general:.2f}", f"{delta_ped_prom_general:.1f}%", delta_color="normal")
    else:
        col1.metric("Establecimientos Activos Promedio", f"{mes_actual['establecimientos_promedio']:.0f}")
        col2.metric("Establecimientos Activos Totales", f"{mes_actual['establecimientos_unicos']:,.0f}")
        col3.metric("Pedidos Totales Realizados", f"{mes_actual['pedidos_totales']:,.0f}")
        col4.metric("Ratio Pedidos/Establecimientos", f"{mes_actual['ratio_pedidos_establecimientos']:.2f}")
        col5.metric("Créditos Totales Utilizados", f"{mes_actual['creditos_totales']:,.0f}")
        col6.metric("Pedidos (promedio)", f"{pedidos_promedio_general:.2f}")

    df_diario_mes['ratio'] = df_diario_mes["total_pedidos"] / df_diario_mes["total_establecimientos"].replace(0, np.nan)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_diario_mes["fecha"], y=df_diario_mes["total_establecimientos"], name="Establecimientos", line=dict(color="green")))
    fig.add_trace(go.Scatter(x=df_diario_mes["fecha"], y=df_diario_mes["total_pedidos"], name="Pedidos", line=dict(color="orange")))
    fig.add_trace(go.Scatter(x=df_diario_mes["fecha"], y=df_diario_mes["ratio"], name="Ratio", line=dict(color="blue")))

    fig.update_layout(
        hovermode="x unified",
        title=f"Tendencias diarias - {mes_seleccionado}",
        xaxis_title="Fecha",
        yaxis_title="Cantidad"
    )
    st.plotly_chart(fig, use_container_width=True)
    df_diario_mes = df_diario_mes.sort_values(by="fecha", ascending=False)
    st.subheader("Datos")
    df_diario_mes['fecha'] = df_diario_mes['fecha'].dt.strftime('%d-%m-%Y')
    st.dataframe(df_diario_mes[['fecha', 'total_pedidos', 'total_establecimientos', 'ratio']].rename(columns={
        'fecha': 'Fecha',
        'total_pedidos': 'Pedidos',
        'total_establecimientos': 'Establecimientos',
        'ratio': 'Ratio Pedidos/Establecimientos'
    }), hide_index=True, use_container_width=True)

def dashboard_general():
    st.title("📈Dashboard de Estadísticas Generales")
    hoy = datetime.now().date()
    ayer = hoy - timedelta(days=1)
    fecha_inicio_default = hoy - timedelta(days=30)

    with st.sidebar:
        st.header("Fechas")
        fecha_inicio = st.date_input("Desde", value=fecha_inicio_default)
        fecha_fin = st.date_input("Hasta", value=hoy)
        if fecha_inicio > fecha_fin:
            st.error("La fecha de inicio no puede ser mayor a la fecha de fin")
            st.stop()
        if st.button("Actualizar Datos"):
            st.cache_data.clear()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Gráficas Principales", "Top 10 Establecimientos", "Establecimientos y Pedidos",
        "Pedidos por Hora", "Concurrencias"
    ])

    with tab1:
        with ThreadPoolExecutor() as executor:
            future_estadistica = executor.submit(obtener_datos_estadistica, fecha_inicio, fecha_fin)
            data_estadistica = future_estadistica.result()

        if data_estadistica:
            top_10 = procesar_top_establecimientos(data_estadistica)
            df_establecimientospedidos = procesar_establecimientos_pedidos(data_estadistica)
            contador_horas = procesar_pedidos_hora(data_estadistica, ayer)
            df_estadistica_general = pd.DataFrame(data_estadistica["data"]["detalle"]["general"]["todos"])
            resultado_concurrencia = procesar_concurrencias(df_estadistica_general, ayer)
            col1, col2 = st.columns(2)
            with col1:
                if not top_10.empty:
                    fig1 = grafico_top_establecimientos(top_10, fecha_inicio, fecha_fin)
                    st.plotly_chart(fig1, use_container_width=True, key="grafico_top_establecimientos_tab1")
                if resultado_concurrencia[0] is not None:
                    fig4, _, _, _, _ = resultado_concurrencia
                    st.plotly_chart(fig4, use_container_width=True, key="grafico_concurrencia_tab1")
            with col2:
                if not contador_horas.empty:
                    fig3 = grafico_pedidos_hora(contador_horas, ayer)
                    st.plotly_chart(fig3, use_container_width=True, key="grafico_pedidos_hora_tab1")
                if not df_establecimientospedidos.empty:
                    fig2 = grafico_establecimientos_pedidos(df_establecimientospedidos, fecha_inicio, fecha_fin)
                    st.plotly_chart(fig2, use_container_width=True, key="grafico_establecimientos_pedidos_tab1")
        else:
            st.warning("No se pudieron cargar todos los datos para mostrar las gráficas")

    with tab2:
        data_estadistica = obtener_datos_estadistica(fecha_inicio, fecha_fin)
        if data_estadistica:
            top_10 = procesar_top_establecimientos(data_estadistica)
            if not top_10.empty:
                col1, col2 = st.columns(2)
                col1.metric("Total de Establecimientos", len(top_10))
                col2.metric("Pedidos Totales", int(top_10["total_pedidos"].sum()))
                fig = grafico_top_establecimientos(top_10, fecha_inicio, fecha_fin)
                st.plotly_chart(fig, use_container_width=True, key="grafico_top_establecimientos_tab2")
                st.dataframe(top_10, column_config={"name_restaurant": "Establecimiento", "total_pedidos":st.column_config.NumberColumn("Pedidos", format="%d")}, hide_index=True, use_container_width=True)
                csv = top_10.to_csv(index=False).encode("utf-8")
                st.download_button("Descargar datos", data=csv, file_name=f"top_establecimientos_{fecha_inicio.strftime('%d-%m-%Y')}_{fecha_fin.strftime('%d-%m-%Y')}.csv", mime="text/csv")
            else:
                st.warning("No hay suficientes datos para mostrar el top 10 establecimientos")
        else:
            st.warning("No se encontraron datos para las fechas seleccionadas")

    with tab3:
        data_estadistica = obtener_datos_estadistica(fecha_inicio, fecha_fin)
        if data_estadistica:
            df_establecimientospedidos = procesar_establecimientos_pedidos(data_estadistica)
            st.subheader("Resumen Estadístico")
            col1, col2, col3 = st.columns(3)
            col1.metric("Establecimientos Activos Promedio", f"{df_establecimientospedidos['Establecimientos'].mean():.0f}")
            col2.metric("Pedidos (promedio)", f"{df_establecimientospedidos['Pedidos'].mean():.0f}")
            col3.metric("Ratio Pedidos/Establecimientos", f"{df_establecimientospedidos['Promedio'].mean():.2f}")
            fig = grafico_establecimientos_pedidos(df_establecimientospedidos, fecha_inicio, fecha_fin)
            st.plotly_chart(fig, use_container_width=True, key="grafico_establecimientos_pedidos_tab3")
            df_establecimientospedidos_display = df_establecimientospedidos.copy()
            df_establecimientospedidos_display["Fecha"] = df_establecimientospedidos_display["Fecha"].dt.strftime('%d-%m-%Y')
            st.dataframe(df_establecimientospedidos_display[["Fecha", "Establecimientos", "Pedidos", "Promedio"]].sort_values("Fecha", ascending=True), column_config={"Fecha": st.column_config.Column("Fecha"), "Establecimientos": st.column_config.NumberColumn("Establecimientos"), "Pedidos": st.column_config.NumberColumn("Pedidos"), "Promedio": st.column_config.NumberColumn("Promedio", format="%.2f")}, hide_index=True, use_container_width=True)
            csv = df_establecimientospedidos.to_csv(index=False).encode("utf-8")
            st.download_button("Descargar Datos", data=csv, file_name=f"establecimientos_pedidos_{fecha_inicio.strftime('%d-%m-%Y')}_{fecha_fin.strftime('%d-%m-%Y')}.csv", mime="text/csv")
        else:
            st.warning("No se obtuvieron valores de la API")

    with tab4:
        fecha_hora = st.date_input("Fecha", value=ayer, key="tab4_fecha")
        data_hora = obtener_datos_estadistica(fecha_inicio, fecha_fin)
        if data_hora is not None:
            contador_horas = procesar_pedidos_hora(data_hora, fecha_hora)
            if not contador_horas.empty:
                total_pedidos = contador_horas["pedidos"].sum()
                hora_pico = contador_horas.loc[contador_horas["pedidos"].idxmax()]
                col1, col2, col3 = st.columns(3)
                col1.metric("Fecha", fecha_hora.strftime("%d-%m-%Y"))
                col2.metric("Total de Pedidos", total_pedidos)
                col3.metric("Hora Pico", f"{hora_pico['etiqueta_hora']}", f"{hora_pico['pedidos']} pedidos")
                fig = grafico_pedidos_hora(contador_horas, fecha_hora)
                st.plotly_chart(fig, use_container_width=True, key="grafico_pedidos_hora_tab4")
                st.dataframe(contador_horas[["etiqueta_hora", "pedidos"]].rename(columns={"etiqueta_hora": "Hora", "pedidos":"Pedidos"}), hide_index=True, use_container_width=True)
                csv = contador_horas[["etiqueta_hora","pedidos"]].to_csv(index=False).encode("utf-8")
                st.download_button("Descargar Datos", data=csv, file_name=f"pedidos_hora_{fecha_hora.strftime('%d-%m-%Y')}.csv", mime="text/csv")
            else:
                st.warning(f"No hay pedidos registrados para {fecha_hora.strftime('%d-%m-%Y')}")
        else:
            st.warning("No se obtuvieron valores de la API")

    with tab5:
        fecha_concurrencia = st.date_input("Fecha", value=ayer, key="tab5_fecha")
        data_concurrencia = obtener_datos_estadistica(fecha_inicio, fecha_fin)
        if data_concurrencia is not None:
            df_estadistica = pd.DataFrame(data_concurrencia["data"]["detalle"]["general"]["todos"])
            resultado = procesar_concurrencias(df_estadistica, fecha_concurrencia)
            if resultado[0] is not None:
                fig_concurrencia, max_val, hora_inicio, hora_fin, df_concurrencia = resultado
                col1, col2 = st.columns(2)
                col1.metric("Máxima Concurrencia", max_val)
                col2.metric("Hora Pico", f"{hora_inicio.strftime('%H:%M')} - {hora_fin.strftime('%H:%M')}")
                st.plotly_chart(fig_concurrencia, use_container_width=True, key="grafico_concurrencia_tab5")
                st.subheader("Datos de Concurrencia")
                df_concurrencia_display = df_concurrencia.copy()
                df_concurrencia_display["Hora"] = df_concurrencia_display["Hora"].dt.strftime('%d-%m-%Y %H:%M')
                st.dataframe(df_concurrencia_display, column_config={"Hora": st.column_config.Column("Hora"), "Pedidos_Simultaneos": st.column_config.NumberColumn("Pedidos Simultáneos")}, hide_index=True, use_container_width=True)
                csv = df_concurrencia.to_csv(index=False).encode("utf-8")
                st.download_button("Descargar Datos de Concurrencia", data=csv, file_name=f"concurrencia_{fecha_concurrencia.strftime('%d-%m-%Y')}.csv", mime="text/csv")
            else:
                st.warning(f"No hay datos para {fecha_concurrencia.strftime('%d-%m-%Y')}")
        else:
            st.warning("No se obtuvieron datos de la API")

def otros_dashboard():
    st.title("📊Otros Análisis")

    current_year = datetime.now().year
    years_available = list(range(2025, current_year + 3))
    selected_year = st.sidebar.selectbox("Seleccionar Año", years_available, index=years_available.index(current_year))

    fecha_inicio_sem = datetime(selected_year, 1, 1).date()
    fecha_actual = datetime.now().date() if selected_year == current_year else datetime(selected_year, 12, 31).date()

    tab1, tab2 = st.tabs(["📦 Pedidos por Semana", "💳 Créditos por Semana"])

    with tab1:
        with st.spinner("Obteniendo datos de pedidos..."):
            datos_estadistica_pedidos = obtener_datos_estadistica(fecha_inicio_sem, fecha_actual)
            if datos_estadistica_pedidos and datos_estadistica_pedidos.get("success"):
                pedidos_semanales = procesar_datos_semanales(datos_estadistica_pedidos, "pedidos", selected_year)
            else:
                st.error("No se pudieron obtener datos de pedidos")
                pedidos_semanales = None
        if pedidos_semanales is not None:
            st.header(f"Análisis Semanal de Pedidos {selected_year}")
            col1, col2, col3 = st.columns(3)
            total = pedidos_semanales["pedidos_totales"].sum()
            semana_max = pedidos_semanales.loc[pedidos_semanales["pedidos_totales"].idxmax()]
            semana_min = pedidos_semanales.loc[pedidos_semanales["pedidos_totales"].idxmin()]
            col1.metric("Pedidos totales", f"{total:,}")
            col2.metric("Semana con más pedidos", f"Semana {semana_max['semana']}", help=f"{semana_max['rango_fechas']}: {semana_max['pedidos_totales']:,}")
            col3.metric("Semana con menos pedidos", f"Semana {semana_min['semana']}", help=f"{semana_min['rango_fechas']}: {semana_min['pedidos_totales']:,}")
            fig = px.bar(pedidos_semanales, x="semana", y="pedidos_totales", title="Pedidos por Semana", labels={"semana": "Semana", "pedidos_totales": "Total Pedidos"}, hover_data=["rango_fechas"], color="pedidos_totales", color_continuous_scale="reds")
            fig.update_traces(hovertemplate="<b>Semana %{x}</b><br>%{customdata[0]}<br>Pedidos: %{y:,}", texttemplate="%{y:,}", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

            pedidos_semanales_display = pedidos_semanales.copy()
            pedidos_semanales_display["fecha_inicio"] = pedidos_semanales_display["fecha_inicio"].astype('datetime64[ns]').dt.strftime('%d-%m-%Y')
            pedidos_semanales_display["fecha_fin"] = pedidos_semanales_display["fecha_fin"].astype('datetime64[ns]').dt.strftime('%d-%m-%Y')
            st.dataframe(pedidos_semanales_display[["semana", "rango_fechas", "pedidos_totales"]].rename(columns={"semana": "Semana", "rango_fechas": "Rango", "pedidos_totales": "Pedidos"}), hide_index=True)
            csv = pedidos_semanales.to_csv(index=False).encode("utf-8")
            st.download_button("Descargar Datos", data=csv, file_name=f"pedidos_semanales_{fecha_inicio_sem.strftime('%d-%m-%Y')}_{fecha_actual.strftime('%d-%m-%Y')}.csv", mime="text/csv")
        else:
            st.warning("No hay datos de pedidos disponibles")

    with tab2:
        with st.spinner("Obteniendo datos de créditos y pedidos..."):
            data_creditos_pedidos = obtener_datos_estadistica(fecha_inicio_sem, fecha_actual)

            if data_creditos_pedidos is not None and data_creditos_pedidos.get("success"):
                df_estadistica = pd.DataFrame(data_creditos_pedidos["data"]["detalle"]["general"]["todos"])
                df_estadistica = df_estadistica.dropna(subset=["order_completion_date"])

                if not df_estadistica.empty:
                    creditos_semanales = procesar_datos_semanales(data_creditos_pedidos, "creditos", selected_year)
                    pedidos_semanales_for_credits = procesar_datos_semanales(data_creditos_pedidos, "pedidos", selected_year)

                    if not creditos_semanales.empty and not pedidos_semanales_for_credits.empty:
                        df_combinado = creditos_semanales.merge(
                            pedidos_semanales_for_credits[["semana", "pedidos_totales"]],
                            on="semana",
                            how="left"
                        )
                        df_combinado["creditos_por_pedido"] = df_combinado["creditos_totales"] / df_combinado["pedidos_totales"].replace(0, np.nan)
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

        if df_combinado is not None:
            st.header(f"Análisis Semanal de Créditos {selected_year}")
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

            fig = px.bar(df_combinado, x="semana", y="creditos_totales",
                                 title="Créditos por Semana",
                                 labels={"semana": "Semana", "creditos_totales": "Total Créditos"},
                                 hover_data=["rango_fechas", "pedidos_totales", "creditos_por_pedido"],
                                 color="creditos_totales",
                                 color_continuous_scale="turbo")
            fig.update_traces(
                hovertemplate="<b>Semana %{x}</b><br>%{customdata[0]}<br>Créditos: %{y:,}<br>Pedidos: %{customdata[1]:,}<br>Créditos/Pedido: $%{customdata[2]:.2f}",
                texttemplate="%{y:,}",
                textposition="outside"
            )
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Datos Semanales Detallados")
            df_combinado_display = df_combinado.copy()
            df_combinado_display["fecha_inicio"] = df_combinado_display["fecha_inicio"].astype('datetime64[ns]').dt.strftime('%d-%m-%Y')
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

            csv = df_combinado.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Descargar Datos Completos",
                data=csv,
                file_name=f"creditos_pedidos_semanales_{fecha_inicio_sem.strftime('%d-%m-%Y')}_{fecha_actual.strftime('%d-%m-%Y')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No hay datos completos disponibles (créditos y pedidos)")

def main():
    st.sidebar.title("Menú Principal")
    app_mode = st.sidebar.selectbox("Seleccione el dashboard",
                                     ["Análisis Mensual", "Estadísticas Generales", "Otros"])

    if app_mode == "Análisis Mensual":
        analisis_mensual()
    elif app_mode == "Estadísticas Generales":
        dashboard_general()
    elif app_mode == "Otros":
        otros_dashboard()

if __name__ == "__main__":
    main()
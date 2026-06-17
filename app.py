import streamlit as st
import pandas as pd
import requests
import sqlite3
import json
import plotly.express as px
import sweetviz as sv
import os

# -------------------------------
# CONFIGURACIÓN
# -------------------------------

st.set_page_config(
    page_title="Compras Públicas Ecuador",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard Compras Públicas Ecuador")
st.markdown("---")

# -------------------------------
# SELECCIÓN DE AÑO
# -------------------------------

anios = ["TODOS"] + [str(i) for i in range(2015, 2027)]

anio = st.sidebar.selectbox(
    "Seleccione un año",
    anios
)

# -------------------------------
# CARGA DE DATOS
# -------------------------------

@st.cache_data
def cargar_datos(anio):

    dataframes = []

    if anio == "TODOS":

        for year in range(2015, 2027):

            try:

                url = f"https://datosabiertos.compraspublicas.gob.ec/PLATAFORMA/api/get_analysis/?year={year}"

                datos = requests.get(url).json()

                if isinstance(datos, list):
                    df_temp = pd.DataFrame(datos)
                else:
                    df_temp = pd.DataFrame([datos])

                df_temp["anio"] = year

                dataframes.append(df_temp)

            except Exception as e:
                st.error(f"Error año {year}: {e}")

    else:

        url = f"https://datosabiertos.compraspublicas.gob.ec/PLATAFORMA/api/get_analysis/?year={anio}"

        datos = requests.get(url).json()

        if isinstance(datos, list):
            df = pd.DataFrame(datos)
        else:
            df = pd.DataFrame([datos])

        df["anio"] = int(anio)

        dataframes.append(df)

    return pd.concat(dataframes, ignore_index=True)

# -------------------------------
# DATAFRAME PRINCIPAL
# -------------------------------

df = cargar_datos(anio)

st.success(f"Registros cargados: {len(df):,}")

# -------------------------------
# LIMPIEZA
# -------------------------------

for col in df.columns:

    if len(df) > 0:

        try:
            if isinstance(df[col].iloc[0], dict):
                df[col] = df[col].apply(json.dumps)
        except:
            pass

# -------------------------------
# SQLITE
# -------------------------------

conn = sqlite3.connect("compras_publicas.db")

df.to_sql(
    "compras_publicas",
    conn,
    if_exists="replace",
    index=False
)

# -------------------------------
# VISTA DE DATOS
# -------------------------------

st.subheader("📋 Datos")

st.dataframe(
    df,
    use_container_width=True
)

# -------------------------------
# INFORMACIÓN GENERAL
# -------------------------------

st.subheader("📈 Estadísticas")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Filas", len(df))

with col2:
    st.metric("Columnas", len(df.columns))

with col3:
    st.metric("Nulos", int(df.isnull().sum().sum()))

# -------------------------------
# RESUMEN
# -------------------------------

st.subheader("📊 Resumen Estadístico")

st.dataframe(
    df.describe(include="all").T,
    use_container_width=True
)

# -------------------------------
# GRÁFICOS AUTOMÁTICOS
# -------------------------------

st.subheader("📉 Visualización")

columnas_numericas = df.select_dtypes(
    include=["int64", "float64"]
).columns

if len(columnas_numericas) > 0:

    variable = st.selectbox(
        "Seleccione variable numérica",
        columnas_numericas
    )

    fig = px.histogram(
        df,
        x=variable,
        title=f"Distribución de {variable}"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:
    st.warning("No existen columnas numéricas.")

# -------------------------------
# SWEETVIZ
# -------------------------------

st.subheader("🍭 Sweetviz")

if st.button("Generar Reporte Sweetviz"):

    reporte = sv.analyze(df)

    reporte.show_html(
        "sweetviz_report.html",
        open_browser=False
    )

    st.success("Reporte generado.")

    with open(
        "sweetviz_report.html",
        "r",
        encoding="utf-8"
    ) as f:

        html = f.read()

        st.components.v1.html(
            html,
            height=900,
            scrolling=True
        )


# -------------------------------
# DESCARGA
# -------------------------------

st.subheader("⬇️ Exportar Datos")

csv = df.to_csv(index=False)

st.download_button(
    label="Descargar CSV",
    data=csv,
    file_name="compras_publicas.csv",
    mime="text/csv"
)

conn.close()
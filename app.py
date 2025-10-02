import os
import pandas as pd
import geopandas as gpd
import numpy as np
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
from dash import dash_table

DATA_DIR = "data"
CSV_CANDIDATES = [
    os.path.join(DATA_DIR, "COVID_muestra_50000.csv")
]

SHAPE_CANDIDATES = [
    os.path.join(DATA_DIR, "COLOMBIA.shp"),
]

csv_path = None
for p in CSV_CANDIDATES:
    if os.path.exists(p):
        csv_path = p
        break

if csv_path is None:
    raise FileNotFoundError("No se encontró el CSV. Coloca tu CSV dentro de data/ (ej: COVID_muestra_50000.csv)")

try:
    df = pd.read_csv(csv_path, encoding="latin1", low_memory=False)
except Exception:
    df = pd.read_csv(csv_path, encoding="utf-8", low_memory=False)


shp_path = None
for p in SHAPE_CANDIDATES:
    if os.path.exists(p):
        shp_path = p
        break

if shp_path is None:
    raise FileNotFoundError("No se encontró el shapefile COLOMBIA.* dentro de data/ (asegúrate de subir .shp .dbf .shx .prj)")

gdf = gpd.read_file(shp_path, encoding="utf-8")

try:
    gdf = gdf.to_crs(epsg=4326)
except Exception:
    pass

# Detectar columnas útiles en el CSV
possible_depto_cols = ["Departamento_nom", "Departamento", "DEPARTAMENTO", "departamento"]
possible_case_cols = ["Caso", "caso", "casos", "Caso_id"]  # cada fila es un caso -> contamos filas
possible_date_cols = ["Fecha_diagnostico", "Fecha Not", "fecha_hoy_casos", "Fecha_not", "fecha", "FECHA_DIAGNOSTICO"]

# Encontrar columna real
col_depto = next((c for c in possible_depto_cols if c in df.columns), None)
col_case = next((c for c in possible_case_cols if c in df.columns), None)
col_date = next((c for c in possible_date_cols if c in df.columns), None)

# Si no hay columna 'caso' asumimos que cada fila es un caso y generamos una columna de conteo
if col_case is None:
    df["_case_dummy"] = 1
    col_case = "_case_dummy"

if col_depto is None:
    # Intentar encontrar alguna columna con 'depart' en el nombre
    col_depto = next((c for c in df.columns if "depart" in c.lower()), None)
    if col_depto is None:
        raise ValueError("No se detectó una columna de departamento en el CSV. Nombres esperados: Departamento_nom, Departamento, DEPARTAMENTO, etc.")

if col_date:
    try:
        df[col_date] = pd.to_datetime(df[col_date], errors="coerce")
    except Exception:
        pass

# Preparar agregados por departamento
# -------------------------
# Queremos un dataframe con: Departamento, Total_Casos
# Si col_case es dummy, contamos filas; si col_case es un contador numérico sumamos.
if df[col_case].dtype.kind in "iufc" and col_case != "_case_dummy":
    # si hay una columna numérica que indica casos por registro (poco común) sumamos
    df_group = df.groupby(col_depto)[col_case].sum().reset_index().rename(columns={col_case: "Total_Casos"})
else:
    df_group = df.groupby(col_depto).size().reset_index(name="Total_Casos")

shp_name_cols = [c for c in gdf.columns if any(k in c.upper() for k in ["CNMBR", "NOMBRE", "NOMB", "DPTO", "NAME"])]
if len(shp_name_cols) == 0:
    raise ValueError("No encuentro una columna con el nombre del departamento dentro del shapefile. Columnas disponibles: " + ", ".join(gdf.columns))


shp_depto_col = shp_name_cols[0]


df_group["__dept_key"] = df_group[col_depto].astype(str).str.strip().str.upper()
gdf["__dept_key"] = gdf[shp_depto_col].astype(str).str.strip().str.upper()

gdf_merged = gdf.merge(df_group[["__dept_key", "Total_Casos"]], on="__dept_key", how="left")
gdf_merged["Total_Casos"] = gdf_merged["Total_Casos"].fillna(0).astype(int)

# Crear app Dash
app = Dash(__name__)
server = app.server  

dept_options = (
    [{"label": d, "value": d} for d in sorted(df_group[col_depto].astype(str).unique())]
    if col_depto in df.columns
    else [{"label": v, "value": v} for v in sorted(gdf_merged[shp_depto_col].astype(str).unique())]
)

app.layout = html.Div([
    html.H2("Dashboard COVID-19 (2021) — basado en Taller 2", style={"textAlign": "center"}),
    html.Div([
        html.Label("Filtrar por Departamento:"),
        dcc.Dropdown(
            id="filtro-depto",
            options=dept_options,
            placeholder="Selecciona un departamento (opcional)",
            value=None,
            multi=False,
            clearable=True,
            style={"width": "60%"}
        )
    ], style={"textAlign": "center", "padding": "10px"}),

    html.Div(id="kpis", style={"display": "flex", "justifyContent": "center", "gap": "2rem", "paddingBottom": "10px"}),

    html.Div([
        dcc.Graph(id="mapa-coropletico", style={"height": "650px"}),
    ], style={"width": "100%"}),

    html.Div([
        dcc.Graph(id="top10-barras", style={"height": "420px"}),
    ]),

    html.H4("Tabla (primeras filas del filtro)"),
    dash_table.DataTable(
        id="tabla",
        page_size=10,
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left", "minWidth": "100px", "maxWidth": "300px"}
    ),

    html.Div(style={"height": "30px"})
])

# Callbacks
@app.callback(
    [
        Output("mapa-coropletico", "figure"),
        Output("top10-barras", "figure"),
        Output("kpis", "children"),
        Output("tabla", "data"),
        Output("tabla", "columns")
    ],
    [Input("filtro-depto", "value")]
)
def actualizar_ui(filtro_depto):
    if filtro_depto:
        df_fil = df[df[col_depto].astype(str).str.upper() == str(filtro_depto).strip().upper()]
    else:
        df_fil = df.copy()

    # KPIs
    total_casos = df_fil.shape[0] if col_case == "_case_dummy" else int(df_fil[col_case].sum())
    try:
        promedio = int(df_fil.groupby(col_depto).size().mean())
    except Exception:
        promedio = 0

    kpi_children = [
        html.Div([
            html.Small("Total casos (filtro)", style={"display": "block", "fontWeight": "600"}),
            html.H3(f"{total_casos:,}")
        ]),
        html.Div([
            html.Small("Promedio casos / depto (filtro)", style={"display": "block", "fontWeight": "600"}),
            html.H3(f"{promedio:,}")
        ])
    ]

    # Mapa coroplético 
    if filtro_depto:
        # recomputar agregados y merge para el mapa 
        casos_fil = df_fil.groupby(col_depto).size().reset_index(name="Total_Casos")
        casos_fil["__dept_key"] = casos_fil[col_depto].astype(str).str.strip().str.upper()
        gdf_map = gdf.merge(casos_fil[["__dept_key", "Total_Casos"]], left_on="__dept_key", right_on="__dept_key", how="left")
        gdf_map["Total_Casos"] = gdf_map["Total_Casos"].fillna(0).astype(int)
    else:
        gdf_map = gdf_merged.copy()

    if "Total_Casos" not in gdf_map.columns:
        gdf_map["Total_Casos"] = 0

    geojson = gdf_map.__geo_interface__

    fig_map = px.choropleth_mapbox(
        gdf_map,
        geojson=geojson,
        locations=gdf_map.index,
        color="Total_Casos",
        hover_name=shp_depto_col,
        hover_data={"Total_Casos": True},
        mapbox_style="carto-positron",
        center={"lat": 4.5, "lon": -74},
        zoom=4,
        opacity=0.7,
        title="Mapa coroplético: casos por departamento (2021)"
    )
    fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})

    # Top 10 barras 
    if filtro_depto:
        top_df = df_fil.groupby(col_depto).size().reset_index(name="Total_Casos").sort_values("Total_Casos", ascending=False).head(10)
    else:
        top_df = df_group.sort_values("Total_Casos", ascending=False).head(10)

    fig_top = px.bar(top_df, x=col_depto if filtro_depto else col_depto, y="Total_Casos",
                     text="Total_Casos", title="Top 10 departamentos con más casos")
    fig_top.update_traces(texttemplate='%{text:,}', textposition='outside')
    fig_top.update_layout(xaxis_tickangle=-45, margin={"t":40, "b":160})

    # Tabla
    display_df = df_fil.head(200)
    data = display_df.to_dict("records")
    columns = [{"name": c, "id": c} for c in display_df.columns]

    return fig_map, fig_top, kpi_children, data, columns

if __name__ == "__main__":
    app.run_server(debug=True, port=8050)


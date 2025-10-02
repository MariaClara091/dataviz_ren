import os
import pandas as pd
import geopandas as gpd
import numpy as np
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
from dash import dash_table

# Configuración para Render
DATA_DIR = "data"
CSV_CANDIDATES = [
    os.path.join(DATA_DIR, "COVID_muestra_50000.csv")
]

SHAPE_CANDIDATES = [
    os.path.join(DATA_DIR, "COLOMBIA.shp"),
]

# Buscar archivos CSV
csv_path = None
for p in CSV_CANDIDATES:
    if os.path.exists(p):
        csv_path = p
        break

if csv_path is None:
    # Si no encuentra en data/, buscar en raíz
    alt_csv = "COVID_muestra_50000.csv"
    if os.path.exists(alt_csv):
        csv_path = alt_csv
    else:
        raise FileNotFoundError("No se encontró el CSV. Asegúrate de que COVID_muestra_50000.csv esté en data/ o en la raíz")

try:
    df = pd.read_csv(csv_path, encoding="latin1", low_memory=False)
except Exception:
    try:
        df = pd.read_csv(csv_path, encoding="utf-8", low_memory=False)
    except Exception as e:
        print(f"Error leyendo CSV: {e}")
        raise

# Buscar shapefile
shp_path = None
for p in SHAPE_CANDIDATES:
    if os.path.exists(p):
        shp_path = p
        break

if shp_path is None:
    # Buscar cualquier archivo .shp en data/
    for file in os.listdir(DATA_DIR):
        if file.endswith('.shp'):
            shp_path = os.path.join(DATA_DIR, file)
            break

if shp_path is None:
    raise FileNotFoundError("No se encontró el shapefile. Asegúrate de subir todos los archivos .shp, .dbf, .shx, .prj")

try:
    gdf = gpd.read_file(shp_path, encoding="utf-8")
except Exception as e:
    print(f"Error leyendo shapefile: {e}")
    # Intentar con encoding alternativo
    try:
        gdf = gpd.read_file(shp_path, encoding="latin1")
    except Exception as e2:
        print(f"Error también con latin1: {e2}")
        raise

try:
    gdf = gdf.to_crs(epsg=4326)
except Exception:
    pass

# Detectar columnas útiles en el CSV
possible_depto_cols = ["Departamento_nom", "Departamento", "DEPARTAMENTO", "departamento", "DPTO", "dpto"]
possible_case_cols = ["Caso", "caso", "casos", "Caso_id"]
possible_date_cols = ["Fecha_diagnostico", "Fecha Not", "fecha_hoy_casos", "Fecha_not", "fecha", "FECHA_DIAGNOSTICO"]

# Encontrar columna real
col_depto = next((c for c in possible_depto_cols if c in df.columns), None)
col_case = next((c for c in possible_case_cols if c in df.columns), None)
col_date = next((c for c in possible_date_cols if c in df.columns), None)

# Debug: mostrar columnas disponibles
print("Columnas en CSV:", df.columns.tolist())
print("Columna departamento detectada:", col_depto)

# Si no hay columna 'caso' asumimos que cada fila es un caso
if col_case is None:
    df["_case_dummy"] = 1
    col_case = "_case_dummy"

if col_depto is None:
    # Buscar cualquier columna que contenga 'depart'
    for col in df.columns:
        if 'depart' in col.lower():
            col_depto = col
            break
    
    if col_depto is None:
        # Si aún no encuentra, usar la primera columna que parezca categórica
        for col in df.columns:
            if df[col].dtype == 'object' and df[col].nunique() < 50:
                col_depto = col
                break
    
    if col_depto is None:
        raise ValueError(f"No se detectó una columna de departamento. Columnas disponibles: {list(df.columns)}")

if col_date:
    try:
        df[col_date] = pd.to_datetime(df[col_date], errors="coerce")
    except Exception:
        pass

# Preparar agregados por departamento
if df[col_case].dtype.kind in "iufc" and col_case != "_case_dummy":
    df_group = df.groupby(col_depto)[col_case].sum().reset_index().rename(columns={col_case: "Total_Casos"})
else:
    df_group = df.groupby(col_depto).size().reset_index(name="Total_Casos")

# Preparar shapefile
print("Columnas en shapefile:", gdf.columns.tolist())

shp_name_cols = [c for c in gdf.columns if any(k in c.upper() for k in ["CNMBR", "NOMBRE", "NOMB", "DPTO", "NAME", "NOMBRE_DPT", "DEPARTAMENTO"])]
if len(shp_name_cols) == 0:
    # Usar la primera columna de texto
    for col in gdf.columns:
        if gdf[col].dtype == 'object':
            shp_name_cols = [col]
            break

if len(shp_name_cols) == 0:
    raise ValueError("No encuentro una columna con nombres en el shapefile")

shp_depto_col = shp_name_cols[0]
print(f"Usando columna '{shp_depto_col}' del shapefile para nombres")

# Crear claves para merge
df_group["__dept_key"] = df_group[col_depto].astype(str).str.strip().str.upper().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('ascii')
gdf["__dept_key"] = gdf[shp_depto_col].astype(str).str.strip().str.upper().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('ascii')

# Debug: mostrar valores únicos
print("Valores únicos en CSV:", df_group["__dept_key"].unique()[:10])
print("Valores únicos en Shapefile:", gdf["__dept_key"].unique()[:10])

gdf_merged = gdf.merge(df_group[["__dept_key", "Total_Casos"]], on="__dept_key", how="left")
gdf_merged["Total_Casos"] = gdf_merged["Total_Casos"].fillna(0).astype(int)

# Crear app Dash
app = Dash(__name__)
server = app.server

# Opciones para el dropdown
dept_options = (
    [{"label": d, "value": d} for d in sorted(df_group[col_depto].astype(str).unique())]
    if col_depto in df.columns
    else [{"label": v, "value": v} for v in sorted(gdf_merged[shp_depto_col].astype(str).unique())]
)

app.layout = html.Div([
    html.H2("Dashboard COVID-19 (2021) — basado en Taller 2", style={"textAlign": "center", "color": "#2c3e50", "marginBottom": "20px"}),
    
    html.Div([
        html.Label("Filtrar por Departamento:", style={"fontWeight": "bold", "marginRight": "10px"}),
        dcc.Dropdown(
            id="filtro-depto",
            options=dept_options,
            placeholder="Selecciona un departamento (opcional)",
            value=None,
            multi=False,
            clearable=True,
            style={"width": "400px", "display": "inline-block"}
        )
    ], style={"textAlign": "center", "padding": "20px", "backgroundColor": "#f8f9fa", "borderRadius": "10px", "marginBottom": "20px"}),

    html.Div(id="kpis", style={"display": "flex", "justifyContent": "center", "gap": "3rem", "padding": "20px", "backgroundColor": "white", "borderRadius": "10px", "marginBottom": "20px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"}),

    html.Div([
        html.H3("Mapa Coroplético de Casos por Departamento", style={"textAlign": "center", "marginBottom": "10px"}),
        dcc.Graph(id="mapa-coropletico", style={"height": "600px", "borderRadius": "10px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"}),
    ], style={"width": "100%", "marginBottom": "20px"}),

    html.Div([
        html.H3("Top 10 Departamentos con Más Casos", style={"textAlign": "center", "marginBottom": "10px"}),
        dcc.Graph(id="top10-barras", style={"height": "500px", "borderRadius": "10px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"}),
    ], style={"marginBottom": "20px"}),

    html.Div([
        html.H3("Datos Detallados (Primeras 200 Filas)", style={"textAlign": "center", "marginBottom": "10px"}),
        dash_table.DataTable(
            id="tabla",
            page_size=10,
            style_table={"overflowX": "auto", "borderRadius": "10px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"},
            style_cell={"textAlign": "left", "minWidth": "100px", "maxWidth": "300px", "padding": "10px"},
            style_header={"backgroundColor": "#2c3e50", "color": "white", "fontWeight": "bold"},
            style_data={"backgroundColor": "#f8f9fa", "color": "black"}
        ),
    ], style={"marginBottom": "30px"}),
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
    try:
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
                html.Small("Total Casos", style={"display": "block", "fontWeight": "600", "color": "#7f8c8d"}),
                html.H3(f"{total_casos:,}", style={"color": "#e74c3c", "margin": "0"})
            ], style={"textAlign": "center", "padding": "15px", "backgroundColor": "#ecf0f1", "borderRadius": "8px", "minWidth": "200px"}),
            
            html.Div([
                html.Small("Promedio por Departamento", style={"display": "block", "fontWeight": "600", "color": "#7f8c8d"}),
                html.H3(f"{promedio:,}", style={"color": "#3498db", "margin": "0"})
            ], style={"textAlign": "center", "padding": "15px", "backgroundColor": "#ecf0f1", "borderRadius": "8px", "minWidth": "200px"}),
            
            html.Div([
                html.Small("Departamentos con Datos", style={"display": "block", "fontWeight": "600", "color": "#7f8c8d"}),
                html.H3(f"{len(df_group):,}", style={"color": "#27ae60", "margin": "0"})
            ], style={"textAlign": "center", "padding": "15px", "backgroundColor": "#ecf0f1", "borderRadius": "8px", "minWidth": "200px"})
        ]

        # Mapa coroplético
        if filtro_depto:
            casos_fil = df_fil.groupby(col_depto).size().reset_index(name="Total_Casos")
            casos_fil["__dept_key"] = casos_fil[col_depto].astype(str).str.strip().str.upper().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('ascii')
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
            color_continuous_scale="Viridis",
            hover_name=shp_depto_col,
            hover_data={"Total_Casos": True},
            mapbox_style="carto-positron",
            center={"lat": 4.5, "lon": -74},
            zoom=4,
            opacity=0.8,
        )
        fig_map.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            coloraxis_colorbar=dict(title="Número de Casos")
        )

        # Top 10 barras
        if filtro_depto:
            top_df = df_fil.groupby(col_depto).size().reset_index(name="Total_Casos").sort_values("Total_Casos", ascending=False).head(10)
        else:
            top_df = df_group.sort_values("Total_Casos", ascending=False).head(10)

        fig_top = px.bar(
            top_df, 
            x=col_depto, 
            y="Total_Casos",
            text="Total_Casos", 
            color="Total_Casos",
            color_continuous_scale="Viridis"
        )
        fig_top.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_top.update_layout(
            xaxis_tickangle=-45,
            margin={"t": 40, "b": 120},
            xaxis_title="Departamento",
            yaxis_title="Total de Casos",
            showlegend=False
        )

        # Tabla
        display_df = df_fil.head(200)
        data = display_df.to_dict("records")
        columns = [{"name": str(c), "id": str(c)} for c in display_df.columns]

        return fig_map, fig_top, kpi_children, data, columns

    except Exception as e:
        print(f"Error en callback: {e}")
        # Retornar figuras vacías en caso de error
        empty_fig = px.line(title=f"Error: {str(e)}")
        return empty_fig, empty_fig, [html.Div(f"Error: {str(e)}")], [], []

if __name__ == "__main__":
    app.run_server(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8050)))


import os
import pandas as pd
import geopandas as gpd
import numpy as np
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
from dash import dash_table

print("Iniciando la aplicación...")

# Configuración de paths
DATA_DIR = "data"

# Verificar archivos existentes
print("Archivos en data/:", os.listdir(DATA_DIR))

# Cargar datos CSV
try:
    csv_path = os.path.join(DATA_DIR, "COVID_muestra_50000.csv")
    print(f"Cargando CSV desde: {csv_path}")
    
    # Probar diferentes encodings
    try:
        df = pd.read_csv(csv_path, encoding="utf-8", low_memory=False)
    except:
        try:
            df = pd.read_csv(csv_path, encoding="latin1", low_memory=False)
        except:
            df = pd.read_csv(csv_path, encoding="iso-8859-1", low_memory=False)
    
    print(f"CSV cargado: {df.shape[0]} filas, {df.shape[1]} columnas")
    print("Columnas:", df.columns.tolist())
    
except Exception as e:
    print(f"Error cargando CSV: {e}")
    # Crear datos de ejemplo si hay error
    df = pd.DataFrame({
        'Departamento_nom': ['BOGOTA', 'ANTIOQUIA', 'VALLE', 'CUNDINAMARCA'] * 100,
        'Edad': np.random.randint(20, 80, 400),
        'Sexo': np.random.choice(['M', 'F'], 400),
        'Estado': np.random.choice(['Leve', 'Moderado', 'Grave'], 400)
    })

# Cargar shapefile con manejo robusto de errores
try:
    shp_path = os.path.join(DATA_DIR, "COLOMBIA.shp")
    print(f"Cargando shapefile desde: {shp_path}")
    
    gdf = gpd.read_file(shp_path)
    print(f"Shapefile cargado: {len(gdf)} geometrías")
    print("Columnas del shapefile:", gdf.columns.tolist())
    
    # Convertir a WGS84 si es necesario
    if gdf.crs != 'EPSG:4326':
        gdf = gdf.to_crs('EPSG:4326')
        print("Shapefile convertido a EPSG:4326")
        
except Exception as e:
    print(f"Error cargando shapefile: {e}")
    print("Usando geometría simplificada...")
    # Crear un GeoDataFrame simple como fallback
    from shapely.geometry import Point
    gdf = gpd.GeoDataFrame({
        'DPTO_CCDGO': ['11', '05', '76', '25'],
        'DPTO_CNMBR': ['BOGOTA', 'ANTIOQUIA', 'VALLE', 'CUNDINAMARCA'],
        'geometry': [Point(-74.0817, 4.6097), Point(-75.5736, 6.2442), 
                    Point(-76.495, 3.395), Point(-74.0758, 4.5981)]
    }, crs='EPSG:4326')

# Detectar columnas en el CSV
possible_depto_cols = ["Departamento_nom", "Departamento", "DEPARTAMENTO", "departamento", "DPTO", "dpto"]
col_depto = next((c for c in possible_depto_cols if c in df.columns), None)

if col_depto is None:
    # Buscar cualquier columna que parezca ser de departamento
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].nunique() < 50:
            col_depto = col
            break

if col_depto is None:
    # Usar la primera columna de texto
    for col in df.columns:
        if df[col].dtype == 'object':
            col_depto = col
            break

if col_depto is None:
    # Último recurso: crear una columna dummy
    df['Departamento_dummy'] = 'COLOMBIA'
    col_depto = 'Departamento_dummy'

print(f"Usando columna de departamento: {col_depto}")

# Detectar columna de nombre en el shapefile
shp_name_cols = [c for c in gdf.columns if any(k in c.upper() for k in 
                ["NOMBRE", "NOMB", "CNMBR", "NAME", "DPTO", "DEPARTAMENTO"])]

if shp_name_cols:
    shp_depto_col = shp_name_cols[0]
else:
    shp_depto_col = gdf.columns[1]  # Segunda columna como fallback

print(f"Usando columna del shapefile: {shp_depto_col}")

# Preparar datos agregados
df_group = df.groupby(col_depto).size().reset_index(name="Total_Casos")

# Función para limpiar texto para merge
def clean_text(text):
    if pd.isna(text):
        return ""
    return str(text).strip().upper().replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')

# Preparar merge
df_group["__dept_key"] = df_group[col_depto].apply(clean_text)
gdf["__dept_key"] = gdf[shp_depto_col].apply(clean_text)

print("Muestras de claves en CSV:", df_group["__dept_key"].head().tolist())
print("Muestras de claves en Shapefile:", gdf["__dept_key"].head().tolist())

# Hacer merge
gdf_merged = gdf.merge(df_group[["__dept_key", "Total_Casos"]], on="__dept_key", how="left")
gdf_merged["Total_Casos"] = gdf_merged["Total_Casos"].fillna(0).astype(int)

print("Merge completado")

# Crear aplicación Dash
app = Dash(__name__)
server = app.server

# Opciones para dropdown
dept_options = [{"label": dept, "value": dept} for dept in sorted(df[col_depto].astype(str).unique())]

# Layout de la aplicación
app.layout = html.Div([
    html.Div([
        html.H1("🌍 Dashboard COVID-19 Colombia", 
                style={"textAlign": "center", "color": "white", "margin": "0"}),
        html.P("Análisis geográfico de casos COVID-19 - 2021", 
               style={"textAlign": "center", "color": "white", "margin": "0"})
    ], style={"backgroundColor": "#2c3e50", "padding": "20px", "marginBottom": "20px"}),
    
    html.Div([
        html.Label("🗺️ Filtrar por Departamento:", 
                  style={"fontWeight": "bold", "marginRight": "10px"}),
        dcc.Dropdown(
            id="filtro-depto",
            options=dept_options,
            placeholder="Selecciona un departamento...",
            value=None,
            style={"width": "400px"}
        )
    ], style={"textAlign": "center", "padding": "20px", "marginBottom": "20px"}),
    
    html.Div(id="kpis", style={
        "display": "flex", 
        "justifyContent": "center", 
        "gap": "20px", 
        "marginBottom": "20px",
        "flexWrap": "wrap"
    }),
    
    html.Div([
        html.Div([
            html.H3("🗺️ Mapa Coroplético de Colombia", 
                   style={"textAlign": "center", "color": "#2c3e50"}),
            dcc.Graph(id="mapa-coropletico", style={"height": "500px"})
        ], style={"flex": "1", "minWidth": "300px", "margin": "10px"})
    ], style={"display": "flex", "flexWrap": "wrap", "justifyContent": "center"}),
    
    html.Div([
        html.Div([
            html.H3("📊 Top 10 Departamentos", 
                   style={"textAlign": "center", "color": "#2c3e50"}),
            dcc.Graph(id="top10-barras", style={"height": "400px"})
        ], style={"flex": "1", "minWidth": "300px", "margin": "10px"})
    ], style={"display": "flex", "flexWrap": "wrap", "justifyContent": "center", "marginBottom": "20px"}),
    
    html.Div([
        html.H3("📋 Datos Detallados", 
               style={"textAlign": "center", "color": "#2c3e50"}),
        html.P("Primeras 100 filas de datos filtrados", 
               style={"textAlign": "center", "color": "#7f8c8d"}),
        dash_table.DataTable(
            id="tabla",
            page_size=10,
            style_table={
                "overflowX": "auto",
                "borderRadius": "10px",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
            },
            style_cell={
                "textAlign": "left",
                "padding": "10px",
                "border": "1px solid #ddd"
            },
            style_header={
                "backgroundColor": "#34495e",
                "color": "white",
                "fontWeight": "bold"
            },
            style_data={
                "backgroundColor": "#f8f9fa"
            }
        )
    ], style={"marginBottom": "30px"}),
    
    html.Footer([
        html.P("Dashboard desarrollado para análisis COVID-19 - Datos 2021", 
               style={"textAlign": "center", "color": "#7f8c8d", "margin": "0"})
    ], style={"padding": "20px", "backgroundColor": "#ecf0f1", "borderRadius": "10px"})
], style={"padding": "20px", "fontFamily": "Arial, sans-serif", "maxWidth": "1200px", "margin": "0 auto"})

# Callback principal
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
def actualizar_dashboard(filtro_depto):
    try:
        # Filtrar datos
        if filtro_depto:
            df_filtrado = df[df[col_depto].astype(str) == str(filtro_depto)]
            # Recalcular agregados para el mapa
            casos_filtro = df_filtrado.groupby(col_depto).size().reset_index(name="Total_Casos")
            casos_filtro["__dept_key"] = casos_filtro[col_depto].apply(clean_text)
            gdf_filtrado = gdf.merge(casos_filtro[["__dept_key", "Total_Casos"]], on="__dept_key", how="left")
            gdf_filtrado["Total_Casos"] = gdf_filtrado["Total_Casos"].fillna(0).astype(int)
        else:
            df_filtrado = df.copy()
            gdf_filtrado = gdf_merged.copy()
        
        # Calcular KPIs
        total_casos = len(df_filtrado)
        num_departamentos = df_filtrado[col_depto].nunique()
        promedio_x_depto = total_casos / num_departamentos if num_departamentos > 0 else 0
        
        kpis = [
            html.Div([
                html.Div(f"{total_casos:,}", style={"fontSize": "2em", "fontWeight": "bold", "color": "#e74c3c"}),
                html.Div("Total Casos", style={"fontSize": "0.9em", "color": "#7f8c8d"})
            ], style={"textAlign": "center", "padding": "20px", "backgroundColor": "white", 
                     "borderRadius": "10px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)", "minWidth": "150px"}),
            
            html.Div([
                html.Div(f"{num_departamentos}", style={"fontSize": "2em", "fontWeight": "bold", "color": "#3498db"}),
                html.Div("Departamentos", style={"fontSize": "0.9em", "color": "#7f8c8d"})
            ], style={"textAlign": "center", "padding": "20px", "backgroundColor": "white", 
                     "borderRadius": "10px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)", "minWidth": "150px"}),
            
            html.Div([
                html.Div(f"{promedio_x_depto:,.0f}", style={"fontSize": "2em", "fontWeight": "bold", "color": "#27ae60"}),
                html.Div("Promedio/Depto", style={"fontSize": "0.9em", "color": "#7f8c8d"})
            ], style={"textAlign": "center", "padding": "20px", "backgroundColor": "white", 
                     "borderRadius": "10px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)", "minWidth": "150px"})
        ]
        
        # Crear mapa coroplético
        geojson = gdf_filtrado.__geo_interface__
        
        fig_mapa = px.choropleth_mapbox(
            gdf_filtrado,
            geojson=geojson,
            locations=gdf_filtrado.index,
            color="Total_Casos",
            color_continuous_scale="Viridis",
            range_color=[0, gdf_filtrado["Total_Casos"].max()] if len(gdf_filtrado) > 0 else [0, 1],
            hover_name=shp_depto_col,
            hover_data={"Total_Casos": True},
            mapbox_style="carto-positron",
            center={"lat": 4.5, "lon": -74},
            zoom=4,
            opacity=0.7
        )
        
        fig_mapa.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            coloraxis_colorbar=dict(title="Nº de Casos")
        )
        
        # Crear gráfico de barras Top 10
        if filtro_depto:
            top_data = df_filtrado.groupby(col_depto).size().reset_index(name="Total_Casos")
        else:
            top_data = df_group.nlargest(10, "Total_Casos")
        
        fig_barras = px.bar(
            top_data,
            x=col_depto,
            y="Total_Casos",
            text="Total_Casos",
            color="Total_Casos",
            color_continuous_scale="Viridis"
        )
        
        fig_barras.update_traces(
            texttemplate='%{text:,}',
            textposition='outside'
        )
        
        fig_barras.update_layout(
            xaxis_tickangle=-45,
            showlegend=False,
            xaxis_title="Departamento",
            yaxis_title="Total de Casos",
            margin={"t": 30, "b": 100}
        )
        
        # Preparar datos para tabla
        columnas_tabla = [col for col in df_filtrado.columns if col in [
            col_depto, 'Edad', 'Sexo', 'Estado', 'Fecha_diagnostico', 
            'Fecha Not', 'Edad', 'Sexo', 'Tipo', 'Ubicacion'
        ]][:6]  # Máximo 6 columnas
        
        datos_tabla = df_filtrado[columnas_tabla].head(100)
        datos_dict = datos_tabla.to_dict('records')
        columnas_dict = [{"name": col, "id": col} for col in datos_tabla.columns]
        
        return fig_mapa, fig_barras, kpis, datos_dict, columnas_dict
        
    except Exception as e:
        print(f"Error en callback: {e}")
        # Figuras vacías en caso de error
        fig_vacia = px.scatter(title="Error cargando datos")
        mensaje_error = html.Div(f"Error: {str(e)}", style={"color": "red", "textAlign": "center"})
        return fig_vacia, fig_vacia, [mensaje_error], [], []

print("Aplicación configurada correctamente")

if __name__ == "__main__":
    app.run_server(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8050)))


import os
import pandas as pd
import geopandas as gpd
import numpy as np
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# ==================== CONFIGURACIÓN MÍNIMA ====================
print("🚀 Iniciando aplicación...")

# Cargar datos
try:
    df = pd.read_csv("data/COVID_muestra_50000.csv", encoding="latin1")
    print("✅ CSV cargado")
except:
    df = pd.read_csv("data/COVID_muestra_50000.csv", encoding="utf-8")
    print("✅ CSV cargado con UTF-8")

# Cargar shapefile
try:
    gdf = gpd.read_file("data/COLOMBIA.shp")
    gdf = gdf.to_crs(epsg=4326)
    print("✅ Shapefile cargado")
except Exception as e:
    print(f"❌ Error con shapefile: {e}")
    # Crear datos de ejemplo si falla
    import json
    gdf = None

# Detectar columna de departamento
col_depto = "Departamento_nom" if "Departamento_nom" in df.columns else "Departamento"
if col_depto not in df.columns:
    for col in df.columns:
        if "depart" in col.lower():
            col_depto = col
            break

print(f"📍 Columna departamento: {col_depto}")

# Preparar datos simples
df_group = df.groupby(col_depto).size().reset_index(name="Total_Casos")

# ==================== APLICACIÓN DASH (MÍNIMA) ====================
app = Dash(__name__)
server = app.server

# Layout simple como el de tu profesora
app.layout = html.Div([
    html.H1("Dashboard COVID-19 Colombia", style={'textAlign': 'center'}),
    
    # Dropdown simple
    dcc.Dropdown(
        id='dropdown-depto',
        options=[{'label': depto, 'value': depto} for depto in sorted(df[col_depto].astype(str).unique())],
        value=None,
        placeholder="Selecciona un departamento...",
        clearable=True
    ),
    
    # KPIs simples
    html.Div(id='kpis-simple', style={'textAlign': 'center', 'margin': '20px'}),
    
    # Mapa
    dcc.Graph(id='mapa-coropletico'),
    
    # Gráfico de barras
    dcc.Graph(id='top10-barras')
])

# ==================== CALLBACK SIMPLE ====================
@app.callback(
    [Output('mapa-coropletico', 'figure'),
     Output('top10-barras', 'figure'),
     Output('kpis-simple', 'children')],
    [Input('dropdown-depto', 'value')]
)
def actualizar_dashboard(filtro_depto):
    
    # Filtrar datos
    if filtro_depto:
        df_filtrado = df[df[col_depto] == filtro_depto]
        titulo_mapa = f"Casos en {filtro_depto}"
    else:
        df_filtrado = df.copy()
        titulo_mapa = "Casos en toda Colombia"
    
    # KPIs
    total_casos = len(df_filtrado)
    
    kpis = html.Div([
        html.H3(f"Total de casos: {total_casos:,}"),
        html.P(f"Departamento: {filtro_depto if filtro_depto else 'Todos'}")
    ])
    
    # Mapa COROPLÉTICO (si tenemos shapefile)
    if gdf is not None:
        try:
            # Preparar datos para mapa
            if filtro_depto:
                casos_depto = df_filtrado.groupby(col_depto).size().reset_index(name="Total_Casos")
            else:
                casos_depto = df_group.copy()
            
            # Hacer merge simple
            gdf_map = gdf.copy()
            gdf_map['depto_key'] = gdf_map.iloc[:,1].astype(str).str.upper()  # Usar primera columna de nombres
            
            casos_depto['depto_key'] = casos_depto[col_depto].astype(str).str.upper()
            
            gdf_merged = gdf_map.merge(casos_depto[['depto_key', 'Total_Casos']], 
                                     on='depto_key', how='left')
            gdf_merged['Total_Casos'] = gdf_merged['Total_Casos'].fillna(0)
            
            # Crear mapa
            fig_mapa = px.choropleth_mapbox(
                gdf_merged,
                geojson=gdf_merged.geometry.__geo_interface__,
                locations=gdf_merged.index,
                color="Total_Casos",
                hover_name=gdf_merged.iloc[:,1],  # Columna de nombres
                mapbox_style="carto-positron",
                center={"lat": 4.5, "lon": -74},
                zoom=4,
                opacity=0.7,
                title=titulo_mapa
            )
            fig_mapa.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
        except Exception as e:
            print(f"Error en mapa: {e}")
            fig_mapa = px.scatter(title="Error cargando mapa")
    else:
        fig_mapa = px.scatter(title="Mapa no disponible")
    
    # Gráfico de barras TOP 10
    if filtro_depto:
        top_data = df_filtrado.groupby(col_depto).size().reset_index(name="Total_Casos")
    else:
        top_data = df_group.nlargest(10, "Total_Casos")
    
    fig_barras = px.bar(
        top_data, 
        x=col_depto, 
        y="Total_Casos",
        title="Top 10 departamentos con más casos"
    )
    
    return fig_mapa, fig_barras, kpis

# ==================== EJECUCIÓN ====================
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8050)))


import dash
from dash import dcc, html, dash_table
import dash.dependencies as dd
import pandas as pd
import geopandas as gpd
import plotly.express as px

df = pd.read_csv("data/COVID_muestra_50000.csv")

# Shapefile de Colombia
shapefile_path = "data/COLOMBIA.shp"
gdf = gpd.read_file(shapefile_path, encoding="utf-8")

# Agrupar casos por departamento
casos_dep = df.groupby("Departamento_nom")["Caso"].count().reset_index()
casos_dep.rename(columns={"Caso": "Total_Casos"}, inplace=True)

# Unir shapefile con dataframe
gdf = gdf.merge(casos_dep, left_on="DPTO_CNMBR", right_on="Departamento_nom", how="left")

# Inicializar app

app = dash.Dash(__name__)
server = app.server  

app.layout = html.Div([
    html.H1("Dashboard COVID-19 en Colombia (2021)", style={"textAlign": "center"}),

    # ---- Filtros ----
    html.Div([
        html.Label("Filtrar por Departamento:"),
        dcc.Dropdown(
            id="filtro_departamento",
            options=[{"label": d, "value": d} for d in df["Departamento_nom"].unique()],
            value=None,
            placeholder="Selecciona un departamento",
            multi=False
        )
    ], style={"width": "40%", "margin": "auto"}),

    # KPIs 
    html.Div([
        html.Div(id="kpi_total", style={"fontSize": 20, "margin": "20px"}),
        html.Div(id="kpi_promedio", style={"fontSize": 20, "margin": "20px"})
    ], style={"display": "flex", "justifyContent": "center"}),

    # Gráficos 
    dcc.Graph(id="mapa"),
    dcc.Graph(id="top10"),

    html.H3("Resumen de datos"),
    dash_table.DataTable(
        id="tabla",
        page_size=10,
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left"}
    )
])

@app.callback(
    [dd.Output("mapa", "figure"),
     dd.Output("top10", "figure"),
     dd.Output("kpi_total", "children"),
     dd.Output("kpi_promedio", "children"),
     dd.Output("tabla", "data"),
     dd.Output("tabla", "columns")],
    [dd.Input("filtro_departamento", "value")]
)
def actualizar_dashboard(dep):
    if dep:
        df_filtrado = df[df["Departamento_nom"] == dep]
    else:
        df_filtrado = df.copy()

    total = df_filtrado.shape[0] 
    promedio = df_filtrado.groupby("Departamento_nom")["Caso"].count().mean()

    kpi1 = f"🔹 Total casos: {total:,}"
    kpi2 = f"🔹 Promedio de casos por departamento: {promedio:,.2f}"

    # Mapa coroplético 
    casos_dep = df_filtrado.groupby("Departamento_nom")["Caso"].count().reset_index()
    casos_dep.rename(columns={"Caso": "Total_Casos"}, inplace=True)
    gdf_mapa = gdf.merge(casos_dep, left_on="DPTO_CNMBR", right_on="Departamento_nom", how="left")

    fig_mapa = px.choropleth_mapbox(
        gdf_mapa,
        geojson=gdf_mapa.geometry.__geo_interface__,
        locations=gdf_mapa.index,
        color="Total_Casos",
        hover_name="DPTO_CNMBR",
        mapbox_style="carto-positron",
        zoom=4, center={"lat": 4.5, "lon": -74},
        opacity=0.7,
        title="Mapa de Casos por Departamento"
    )

    # Top 10 departamentos
    top10 = df.groupby("Departamento_nom")["Caso"].count().nlargest(10).reset_index()
    fig_top10 = px.bar(top10, x="Departamento_nom", y="Caso", text="Caso",
                       title="Top 10 Departamentos con más Casos")
    fig_top10.update_traces(texttemplate='%{text:,}', textposition='outside')

    # Tabla 
    data = df_filtrado.head(20).to_dict("records")
    columns = [{"name": i, "id": i} for i in df_filtrado.columns]

    return fig_mapa, fig_top10, kpi1, kpi2, data, columns

if __name__ == "__main__":
    app.run_server(debug=True)

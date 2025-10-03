import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import warnings
import requests
import json
warnings.filterwarnings("ignore")

# Inicializar la app Dash
app = dash.Dash(__name__)
server = app.server
app.title = "Dashboard COVID-19 Colombia"

# =============================================================================
# CARGAR GEOJSON DE COLOMBIA
# =============================================================================

def cargar_geojson_colombia():
    """Cargar GeoJSON de departamentos de Colombia"""
    try:
        # GeoJSON de departamentos de Colombia
        geojson_url = "https://raw.githubusercontent.com/john-guerra/colombia_mapa/master/colombia.geo.json"
        response = requests.get(geojson_url)
        geojson_data = response.json()
        return geojson_data
    except:
        # Si falla la descripción, crear uno básico
        return None

# Cargar GeoJSON
geojson_colombia = cargar_geojson_colombia()

# =============================================================================
# DATOS ACTUALIZADOS CON LA INFORMACIÓN PROPORCIONADA
# =============================================================================

def cargar_datos_actualizados():
    """Función para crear datos con la información real proporcionada"""
    
    # Datos actualizados basados en la información que proporcionaste
    datos_departamentos = [
        # Departamento, Casos, Población (aproximada)
        ['Bogotá D.C.', 65908, 8000000],
        ['Antioquia', 39941, 6400000],
        ['Valle del Cauca', 27108, 4500000],
        ['Atlántico', 17058, 2500000],
        ['Córdoba', 15566, 1700000],
        ['Santander', 15000, 2200000],
        ['Cundinamarca', 14000, 2800000],
        ['Bolívar', 12000, 2100000],
        ['Nariño', 11000, 1600000],
        ['Boyacá', 10000, 1200000],
        ['Magdalena', 9500, 1400000],
        ['Cesar', 9000, 1200000],
        ['Tolima', 8500, 1300000],
        ['Caldas', 8000, 1000000],
        ['Huila', 7500, 1100000],
        ['Sucre', 7000, 850000],
        ['La Guajira', 6500, 880000],
        ['Cauca', 6000, 1300000],
        ['Risaralda', 5500, 940000],
        ['Norte de Santander', 5000, 1600000],
        ['Quindío', 4500, 540000],
        ['Meta', 4000, 1000000],
        ['Chocó', 3500, 500000],
        ['Casanare', 3000, 420000],
        ['Arauca', 2500, 300000],
        ['Putumayo', 2000, 350000],
        ['Caquetá', 1500, 400000],
        ['San Andrés', 3000, 75000],
        # Departamentos amazónicos con aproximadamente 5 casos
        ['Amazonas', 5, 76000],
        ['Guainía', 5, 48000],
        ['Guaviare', 5, 82000],
        ['Vaupés', 5, 44000],
        ['Vichada', 5, 110000]
    ]
    
    df = pd.DataFrame(datos_departamentos, 
                     columns=['Departamento', 'casos', 'poblacion'])
    
    # Calcular incidencia
    df['incidencia'] = (df['casos'] / df['poblacion']) * 100000
    df['incidencia'] = df['incidencia'].round(1)
    
    return df

# Cargar datos
df_datos = cargar_datos_actualizados()

# =============================================================================
# ESTILOS CSS
# =============================================================================

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 0;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }
            
            /* Header */
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 2rem 0;
                margin-bottom: 2rem;
                text-align: center;
            }
            
            .header h1 {
                margin-bottom: 0.5rem;
                font-weight: bold;
                font-size: 2.5rem;
            }
            
            .header p {
                margin-bottom: 0;
                opacity: 0.9;
                font-size: 1.2rem;
            }
            
            /* KPIs */
            .kpi-container {
                display: flex;
                justify-content: space-between;
                margin-bottom: 2rem;
                gap: 20px;
            }
            
            .kpi-card {
                background: white;
                border-radius: 15px;
                padding: 1.5rem;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                flex: 1;
                transition: transform 0.3s ease;
            }
            
            .kpi-card:hover {
                transform: translateY(-5px);
            }
            
            .kpi-number {
                font-size: 2.5rem;
                font-weight: bold;
                margin-bottom: 0.5rem;
            }
            
            .kpi-casos { color: #1f77b4; }
            .kpi-poblacion { color: #ff7f0e; }
            .kpi-incidencia { color: #2ca02c; }
            
            /* Layout principal */
            .main-layout {
                display: flex;
                gap: 20px;
                margin-bottom: 2rem;
            }
            
            .filters-column {
                width: 300px;
                flex-shrink: 0;
            }
            
            .content-column {
                flex: 1;
            }
            
            /* Filtros */
            .filter-section {
                background: white;
                border-radius: 15px;
                padding: 1.5rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 1rem;
            }
            
            .filter-section h5 {
                color: #2c3e50;
                margin-bottom: 1.5rem;
            }
            
            .dropdown-label {
                font-weight: 600;
                margin-bottom: 0.5rem;
                color: #2c3e50;
                display: block;
            }
            
            .dropdown {
                margin-bottom: 1.5rem;
            }
            
            /* Cards */
            .card {
                background: white;
                border-radius: 15px;
                padding: 1.5rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 1rem;
            }
            
            .card h5 {
                color: #2c3e50;
                margin-bottom: 1rem;
                font-weight: 600;
            }
            
            /* Sección de información */
            .info-section {
                background: white;
                border-radius: 15px;
                padding: 1.5rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-top: 2rem;
            }
            
            .info-section h4 {
                color: #2c3e50;
                margin-bottom: 1rem;
                border-bottom: 2px solid #667eea;
                padding-bottom: 0.5rem;
            }
            
            .info-list {
                margin-bottom: 1.5rem;
            }
            
            .info-list li {
                margin-bottom: 0.5rem;
                line-height: 1.6;
            }
            
            .factors-list {
                background: #f8f9fa;
                padding: 1rem;
                border-radius: 10px;
                margin-top: 1rem;
            }
            
            .factors-list li {
                margin-bottom: 0.5rem;
            }
            
            /* Responsive */
            @media (max-width: 768px) {
                .main-layout {
                    flex-direction: column;
                }
                
                .filters-column {
                    width: 100%;
                }
                
                .kpi-container {
                    flex-direction: column;
                }
                
                .header h1 {
                    font-size: 2rem;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# =============================================================================
# COMPONENTES DEL DASHBOARD
# =============================================================================

# KPIs principales
def crear_kpis():
    total_casos = int(df_datos['casos'].sum())
    total_poblacion = int(df_datos['poblacion'].sum())
    incidencia_promedio = (total_casos / total_poblacion) * 100000
    
    return html.Div([
        html.Div([
            html.Div([
                html.Div(f"{total_casos:,}", className="kpi-number kpi-casos"),
                html.Div("Total de Casos", style={'color': '#6c757d'})
            ], className="kpi-card"),
            
            html.Div([
                html.Div(f"{total_poblacion:,}", className="kpi-number kpi-poblacion"),
                html.Div("Población Total", style={'color': '#6c757d'})
            ], className="kpi-card"),
            
            html.Div([
                html.Div(f"{incidencia_promedio:.1f}", className="kpi-number kpi-incidencia"),
                html.Div("Incidencia Promedio x 100k hab.", style={'color': '#6c757d'})
            ], className="kpi-card")
        ], className="kpi-container")
    ])

# Sección de información
def crear_seccion_info():
    return html.Div([
        html.H4("Análisis de la Distribución de Casos COVID-19 en Colombia"),
        
        html.Div([
            html.Strong("Las principales regiones de concentración fueron:"),
            html.Ul([
                html.Li("Bogotá D.C. con 65,908 casos, siendo el 40% del total"),
                html.Li("Departamento de Antioquia con 39,941 casos, siendo el 15% del total"),
                html.Li("Valle del Cauca con 27,108 casos, siendo el 7% del total"),
                html.Li("Atlántico con 17,058 casos"),
                html.Li("Córdoba con 15,566 casos")
            ], className="info-list"),
            
            html.P([
                "Se ven desigualdades marcadas pues hubo una brecha de 12,600 de 1 entre el departamento con más casos, como Bogotá con 65,908, ",
                "y los menos afectados como los departamentos amazónicos con aprox. 5 casos."
            ]),
            
            html.Div([
                html.Strong("Algunos factores que podrían explicar estas diferencias pueden ser:"),
                html.Ul([
                    html.Li("Conectividad aérea y terrestre"),
                    html.Li("Aislamiento natural de periferias"),
                    html.Li("Acceso a servicios de salud"),
                    html.Li("La gran densidad en centros urbanos"),
                    html.Li("Dificultad para distanciamiento social en áreas marginales")
                ])
            ], className="factors-list"),
            
            html.P([
                "Gracias a la georreferenciación se permitió que se visualizaran las desigualdades evidentes en tablas del top 10. ",
                "También a identificar patrones espaciales de la transmisión del Covid 19 en las áreas urbanas, y así contextualizar ",
                "políticas públicas según realidades regionales con más casos."
            ]),
            
            html.P([
                html.Strong("Conclusión: "),
                "Por ello, la pandemia no afectó uniformemente en todo el país, sino que se reprodujo en las desigualdades territoriales ",
                "como lo son las capitales departamentales, donde la geografía actuó como determinante social de la salud de todos los ",
                "habitantes de Colombia."
            ], style={'fontStyle': 'italic', 'marginTop': '1rem'})
            
        ])
    ], className="info-section")

# Layout principal
app.layout = html.Div([
    # Header
    html.Div([
        html.Div([
            html.H1("Dashboard COVID-19 Colombia"),
            html.P("Distribución e incidencia de casos por departamento - 2021")
        ], className="header")
    ]),
    
    # Contenedor principal
    html.Div([
        # KPIs
        crear_kpis(),
        
        # Layout principal
        html.Div([
            # Columna de filtros
            html.Div([
                html.Div([
                    html.H5("Filtros"),
                    
                    html.Div([
                        html.Label("Tipo de Visualización:", className="dropdown-label"),
                        dcc.Dropdown(
                            id='tipo-visualizacion',
                            options=[
                                {'label': 'Casos Totales', 'value': 'casos'},
                                {'label': 'Incidencia x 100k hab.', 'value': 'incidencia'}
                            ],
                            value='casos',
                            clearable=False
                        )
                    ], className="dropdown"),
                    
                    html.Hr(),
                    
                    html.Div([
                        html.H6("Información del Dashboard", style={'color': '#2c3e50', 'marginBottom': '1rem'}),
                        html.P("Este dashboard muestra la distribución de casos de COVID-19 en Colombia durante 2021."),
                        html.P("• Casos Totales: Número absoluto de casos", style={'marginBottom': '0.5rem', 'fontSize': '0.9rem'}),
                        html.P("• Incidencia: Casos por 100,000 habitantes", style={'marginBottom': '0.5rem', 'fontSize': '0.9rem'})
                    ], style={'fontSize': '0.9rem', 'color': '#6c757d'})
                    
                ], className="filter-section")
            ], className="filters-column"),
            
            # Columna de contenido
            html.Div([
                # Mapa Coroplético
                html.Div([
                    html.Div([
                        html.H5("Mapa Coroplético de Colombia - Distribución COVID-19"),
                        dcc.Graph(id='mapa-coropletico')
                    ], className="card")
                ]),
                
                # Top 10 Departamentos
                html.Div([
                    html.Div([
                        html.H5("Top 10 Departamentos con Mayor Incidencia"),
                        dcc.Graph(id='top-departamentos')
                    ], className="card")
                ])
            ], className="content-column")
        ], className="main-layout"),
        
        # Sección de información
        crear_seccion_info()
        
    ], className="container")
])

# =============================================================================
# CALLBACKS
# =============================================================================

@app.callback(
    [Output('mapa-coropletico', 'figure'),
     Output('top-departamentos', 'figure')],
    [Input('tipo-visualizacion', 'value')]
)
def actualizar_dashboard(tipo_visualizacion):
    
    # Configuración según tipo de visualización
    if tipo_visualizacion == 'casos':
        columna = 'casos'
        titulo_mapa = 'Casos Totales de COVID-19 por Departamento'
        color_scale = 'Blues'
        titulo_top = 'Top 10 Departamentos - Casos Totales'
        color_bar = '#1f77b4'
        hover_template = '<b>%{location}</b><br>Casos: %{z:,}<br>Incidencia: %{customdata[0]:.1f} x100k<br>Población: %{customdata[1]:,}'
    else:
        columna = 'incidencia'
        titulo_mapa = 'Incidencia de COVID-19 (casos por 100,000 hab.)'
        color_scale = 'Reds'
        titulo_top = 'Top 10 Departamentos - Incidencia x 100k hab.'
        color_bar = '#d62728'
        hover_template = '<b>%{location}</b><br>Incidencia: %{z:.1f} x100k<br>Casos: %{customdata[0]:,}<br>Población: %{customdata[1]:,}'
    
    # 1. MAPA COROPLÉTICO CON FORMAS REALES DE DEPARTAMENTOS
    if geojson_colombia:
        # Usar el GeoJSON real
        fig_mapa = px.choropleth(
            df_datos,
            geojson=geojson_colombia,
            locations='Departamento',
            featureidkey='properties.NOMBRE_DPT',
            color=columna,
            color_continuous_scale=color_scale,
            range_color=[df_datos[columna].min(), df_datos[columna].max()],
            labels={columna: titulo_mapa},
            custom_data=['casos', 'poblacion', 'incidencia']
        )
        
        fig_mapa.update_geos(
            fitbounds="locations",
            visible=False,
            bgcolor='rgba(0,0,0,0)'
        )
        
        fig_mapa.update_layout(
            title=titulo_mapa,
            height=500,
            margin={"r":0,"t":40,"l":0,"b":0},
            geo=dict(
                bgcolor='rgba(0,0,0,0)',
                lakecolor='#4dabf7',
                landcolor='rgba(0,0,0,0)'
            )
        )
        
        fig_mapa.update_traces(
            hovertemplate=hover_template
        )
        
    else:
        # Fallback: crear un mapa básico si no hay GeoJSON
        fig_mapa = go.Figure()
        
        # Agregar puntos como fallback
        fig_mapa.add_trace(go.Scattergeo(
            lon = df_datos['Longitud'] if 'Longitud' in df_datos.columns else [-74.0817] * len(df_datos),
            lat = df_datos['Latitud'] if 'Latitud' in df_datos.columns else [4.6097] * len(df_datos),
            text = df_datos['Departamento'],
            marker = dict(
                size = df_datos[columna] / df_datos[columna].max() * 50 + 10,
                color = df_datos[columna],
                colorscale = color_scale,
                showscale = True,
                colorbar = dict(
                    title = "Casos Totales" if tipo_visualizacion == 'casos' else "Incidencia"
                )
            ),
            hovertemplate = "<b>%{text}</b><br>" + 
                          ("Casos: %{marker.color:,}<br>" if tipo_visualizacion == 'casos' else "Incidencia: %{marker.color:.1f}<br>") +
                          "<extra></extra>"
        ))
        
        fig_mapa.update_geos(
            resolution=50,
            showcoastlines=True,
            coastlinecolor="RebeccaPurple",
            showland=True,
            landcolor="lightgray",
            showocean=True,
            oceancolor="lightblue",
            projection_type="mercator"
        )
        
        fig_mapa.update_layout(
            title=titulo_mapa,
            height=500,
            margin={"r":0,"t":40,"l":0,"b":0},
            geo=dict(
                scope="south america",
                center=dict(lat=4, lon=-74),
                projection_scale=5
            )
        )
    
    # 2. TOP 10 DEPARTAMENTOS
    df_top10 = df_datos.nlargest(10, columna)
    
    fig_top = px.bar(
        df_top10,
        x=columna,
        y='Departamento',
        orientation='h',
        title=titulo_top,
        color=columna,
        color_continuous_scale=color_scale,
        height=400
    )
    
    fig_top.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False,
        coloraxis_showscale=False
    )
    
    # Formatear los valores en el gráfico de barras
    if tipo_visualizacion == 'casos':
        fig_top.update_xaxes(tickformat=',')
        # Actualizar hover data para casos
        fig_top.update_traces(
            hovertemplate='<b>%{y}</b><br>Casos: %{x:,}<br>Incidencia: ' + 
                         df_top10['incidencia'].round(1).astype(str) + ' x100k<extra></extra>'
        )
    else:
        fig_top.update_xaxes(ticksuffix=' x100k')
        # Actualizar hover data para incidencia
        fig_top.update_traces(
            hovertemplate='<b>%{y}</b><br>Incidencia: %{x:.1f} x100k<br>Casos: ' + 
                         df_top10['casos'].astype(str) + '<extra></extra>'
        )
    
    return fig_mapa, fig_top

# =============================================================================
# EJECUCIÓN
# =============================================================================

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
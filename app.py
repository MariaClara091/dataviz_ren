import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# Inicializar la app Dash
app = dash.Dash(__name__)
server = app.server
app.title = "Dashboard COVID-19 Colombia"

# =============================================================================
# DATOS SIMULADOS CON COORDENADAS PARA EL MAPA
# =============================================================================

def cargar_datos_con_coordenadas():
    """Función para crear datos simulados con coordenadas de departamentos"""
    
    # Datos de departamentos con coordenadas aproximadas
    datos_departamentos = [
        # Departamento, Lat, Lon, Casos, Población
        ['ANTIOQUIA', 6.2442, -75.5736, 45234, 6400000],
        ['ATLANTICO', 10.9639, -74.7964, 28765, 2500000],
        ['BOGOTÁ', 4.6097, -74.0817, 89234, 8000000],
        ['BOLIVAR', 8.6704, -74.0300, 15678, 2100000],
        ['BOYACA', 5.5350, -73.3678, 12345, 1200000],
        ['CALDAS', 5.2982, -75.2479, 9876, 1000000],
        ['CAQUETA', 1.6146, -75.6062, 5432, 400000],
        ['CAUCA', 2.4417, -76.6066, 8765, 1300000],
        ['CESAR', 9.3373, -73.6536, 11234, 1200000],
        ['CORDOBA', 8.0493, -75.5740, 14567, 1700000],
        ['CUNDINAMARCA', 4.7979, -74.1925, 23456, 2800000],
        ['CHOCO', 5.6919, -76.6582, 6543, 500000],
        ['HUILA', 2.5359, -75.5277, 9876, 1100000],
        ['LA GUAJIRA', 11.3548, -72.5205, 8765, 880000],
        ['MAGDALENA', 10.4113, -74.4057, 13456, 1400000],
        ['META', 3.2719, -73.0877, 7654, 1000000],
        ['NARIÑO', 1.2136, -77.2811, 15678, 1600000],
        ['NORTE SANTANDER', 7.9076, -72.5045, 14321, 1600000],
        ['QUINDIO', 4.5310, -75.6801, 8765, 540000],
        ['RISARALDA', 4.8080, -75.7002, 9543, 940000],
        ['SANTANDER', 6.6437, -73.6536, 18765, 2200000],
        ['SUCRE', 8.8140, -74.7233, 7654, 850000],
        ['TOLIMA', 4.0925, -75.1545, 11234, 1300000],
        ['VALLE', 3.8009, -76.6413, 34567, 4500000],
        ['ARAUCA', 6.5474, -70.9977, 4321, 300000],
        ['CASANARE', 5.7589, -71.5724, 5432, 420000],
        ['PUTUMAYO', 0.8850, -76.5086, 3210, 350000],
        ['AMAZONAS', -1.4429, -71.5724, 1234, 76000],
        ['GUAINIA', 2.5854, -68.5247, 876, 48000],
        ['GUAVIARE', 2.0439, -72.3311, 1543, 82000],
        ['VAUPES', 0.3853, -70.5771, 987, 44000],
        ['VICHADA', 4.4234, -69.2878, 765, 110000],
        ['SAN ANDRES', 12.5567, -81.7185, 5432, 75000]
    ]
    
    df = pd.DataFrame(datos_departamentos, 
                     columns=['Departamento', 'Latitud', 'Longitud', 'casos', 'poblacion'])
    
    # Calcular incidencia
    df['incidencia'] = (df['casos'] / df['poblacion']) * 100000
    df['incidencia'] = df['incidencia'].round(1)
    
    return df

# Cargar datos
df_datos = cargar_datos_con_coordenadas()

# =============================================================================
# ESTILOS CSS SIMPLIFICADOS
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
        ], className="main-layout")
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
    else:
        columna = 'incidencia'
        titulo_mapa = 'Incidencia de COVID-19 (casos por 100,000 hab.)'
        color_scale = 'Reds'
        titulo_top = 'Top 10 Departamentos - Incidencia x 100k hab.'
        color_bar = '#d62728'
    
    # 1. MAPA COROPLÉTICO
    fig_mapa = px.scatter_mapbox(
        df_datos,
        lat="Latitud",
        lon="Longitud",
        size=columna,
        color=columna,
        hover_name="Departamento",
        hover_data={
            "casos": True,
            "incidencia": ":.1f",
            "poblacion": True,
            "Latitud": False,
            "Longitud": False
        },
        size_max=30,
        zoom=4,
        height=500,
        color_continuous_scale=color_scale,
        title=titulo_mapa
    )
    
    fig_mapa.update_layout(
        mapbox_style="open-street-map",
        margin={"r":0,"t":40,"l":0,"b":0},
        mapbox=dict(
            center=dict(lat=4.6, lon=-74.0),
            zoom=4
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
        color_discrete_sequence=[color_bar],
        height=400
    )
    
    fig_top.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False
    )
    
    return fig_mapa, fig_top

# =============================================================================
# EJECUCIÓN
# =============================================================================

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)

import dash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd
import plotly.express as px
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# Inicializar la app Dash
app = dash.Dash(__name__)
server = app.server  # Necesario para deployment en Render
app.title = "Dashboard COVID-19 Colombia"

# =============================================================================
# CARGA Y PROCESAMIENTO DE DATOS (SIMULADO)
# =============================================================================

def cargar_datos_simulados():
    """Función para crear datos simulados para el dashboard"""
    
    # Datos de departamentos de Colombia
    departamentos = [
        'ANTIOQUIA', 'ATLANTICO', 'BOGOTÁ', 'BOLIVAR', 'BOYACA', 'CALDAS', 'CAQUETA', 
        'CAUCA', 'CESAR', 'CORDOBA', 'CUNDINAMARCA', 'CHOCO', 'HUILA', 'LA GUAJIRA',
        'MAGDALENA', 'META', 'NARIÑO', 'NORTE SANTANDER', 'QUINDIO', 'RISARALDA',
        'SANTANDER', 'SUCRE', 'TOLIMA', 'VALLE', 'ARAUCA', 'CASANARE', 'PUTUMAYO',
        'AMAZONAS', 'GUAINIA', 'GUAVIARE', 'VAUPES', 'VICHADA', 'SAN ANDRES'
    ]
    
    # Crear DataFrame simulado
    np.random.seed(42)  # Para reproducibilidad
    
    data = {
        'Departamento': departamentos,
        'casos': np.random.randint(1000, 50000, len(departamentos)),
        'poblacion': np.random.randint(50000, 8000000, len(departamentos))
    }
    
    df_dashboard = pd.DataFrame(data)
    df_dashboard['incidencia'] = (df_dashboard['casos'] / df_dashboard['poblacion']) * 100000
    df_dashboard['incidencia'] = df_dashboard['incidencia'].round(1)
    
    return df_dashboard

# Cargar datos simulados
df_dashboard = cargar_datos_simulados()

# =============================================================================
# ESTILOS CSS PERSONALIZADOS
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
            /* Estilos generales */
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
                border-radius: 0 0 20px 20px;
                text-align: center;
            }
            
            .header h1 {
                margin-bottom: 0.5rem;
                font-weight: bold;
            }
            
            .header p {
                margin-bottom: 0;
                opacity: 0.9;
                font-size: 1.1rem;
            }
            
            /* Sistema de grillas */
            .row {
                display: flex;
                flex-wrap: wrap;
                margin: 0 -10px;
            }
            
            .columns {
                padding: 0 10px;
                box-sizing: border-box;
            }
            
            .three.columns { width: 25%; }
            .four.columns { width: 33.333%; }
            .six.columns { width: 50%; }
            .nine.columns { width: 75%; }
            .twelve.columns { width: 100%; }
            
            /* Tarjetas KPIs */
            .kpi-card {
                background: white;
                border-radius: 15px;
                padding: 1.5rem;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                border: none;
                margin-bottom: 1rem;
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
            
            /* Tarjetas generales */
            .card {
                background: white;
                border-radius: 15px;
                padding: 1.5rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                border: none;
                margin-bottom: 1rem;
                height: 100%;
            }
            
            .card h5 {
                color: #2c3e50;
                margin-bottom: 1rem;
                font-weight: 600;
            }
            
            /* Sección de filtros */
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
            
            /* Dropdowns */
            .dropdown {
                margin-bottom: 1.5rem;
            }
            
            .dropdown-label {
                font-weight: 600;
                margin-bottom: 0.5rem;
                color: #2c3e50;
                display: block;
            }
            
            /* Selectores de Dash */
            .Select-control {
                border-radius: 8px;
                border: 1px solid #ddd;
            }
            
            /* Responsive */
            @media (max-width: 768px) {
                .three.columns, .four.columns, .six.columns, .nine.columns {
                    width: 100%;
                }
                
                .header {
                    padding: 1rem 0;
                }
                
                .header h1 {
                    font-size: 1.5rem;
                }
                
                .kpi-number {
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
    total_casos = int(df_dashboard['casos'].sum())
    total_poblacion = int(df_dashboard['poblacion'].sum())
    incidencia_promedio = (total_casos / total_poblacion) * 100000
    
    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.Div(f"{total_casos:,}", className="kpi-number kpi-casos"),
                    html.Div("Total de Casos", style={'color': '#6c757d'})
                ], className="kpi-card")
            ], className="four columns"),
            
            html.Div([
                html.Div([
                    html.Div(f"{total_poblacion:,}", className="kpi-number kpi-poblacion"),
                    html.Div("Población Total", style={'color': '#6c757d'})
                ], className="kpi-card")
            ], className="four columns"),
            
            html.Div([
                html.Div([
                    html.Div(f"{incidencia_promedio:.1f}", className="kpi-number kpi-incidencia"),
                    html.Div("Incidencia Promedio x 100k hab.", style={'color': '#6c757d'})
                ], className="kpi-card")
            ], className="four columns")
        ], className="row")
    ])

# Layout principal
app.layout = html.Div([
    # Header
    html.Div([
        html.Div([
            html.H1("Dashboard COVID-19 Colombia", 
                   style={'marginBottom': '0.5rem', 'fontWeight': 'bold'}),
            html.P("Distribución e incidencia de casos por departamento - 2021",
                  style={'marginBottom': '0', 'opacity': '0.9', 'fontSize': '1.1rem'})
        ], className="header")
    ]),
    
    # Contenedor principal
    html.Div([
        # KPIs
        crear_kpis(),
        
        # Filtros y Gráficos
        html.Div([
            # Columna de filtros
            html.Div([
                html.Div([
                    html.H5("Filtros"),
                    
                    html.Div([
                        html.Label("Seleccionar Departamento:", className="dropdown-label"),
                        dcc.Dropdown(
                            id='departamento-dropdown',
                            options=[{'label': 'Todos', 'value': 'Todos'}] + 
                                   [{'label': depto, 'value': depto} 
                                    for depto in sorted(df_dashboard['Departamento'].unique())],
                            value='Todos',
                            clearable=False,
                            style={'width': '100%'}
                        )
                    ], className="dropdown"),
                    
                    html.Div([
                        html.Label("Tipo de Visualización:", className="dropdown-label"),
                        dcc.Dropdown(
                            id='tipo-visualizacion',
                            options=[
                                {'label': 'Casos Totales', 'value': 'casos'},
                                {'label': 'Incidencia x 100k hab.', 'value': 'incidencia'}
                            ],
                            value='casos',
                            clearable=False,
                            style={'width': '100%'}
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
            ], className="three columns"),
            
            # Columna de gráficos
            html.Div([
                # Gráfico principal
                html.Div([
                    html.Div([
                        html.Div([
                            html.H5("Distribución por Departamentos"),
                            dcc.Graph(id='mapa-simulado')
                        ], className="card")
                    ], className="twelve columns")
                ], className="row"),
                
                # Gráficos secundarios
                html.Div([
                    html.Div([
                        html.Div([
                            html.H5("Top 10 Departamentos"),
                            dcc.Graph(id='top-departamentos')
                        ], className="card")
                    ], className="six columns"),
                    
                    html.Div([
                        html.Div([
                            html.H5("Distribución de Casos"),
                            dcc.Graph(id='distribucion-casos')
                        ], className="card")
                    ], className="six columns")
                ], className="row"),
                
                # Tabla de datos
                html.Div([
                    html.Div([
                        html.Div([
                            html.H5("Datos por Departamento", style={'marginBottom': '1rem'}),
                            dash_table.DataTable(
                                id='tabla-datos',
                                columns=[
                                    {"name": "Departamento", "id": "Departamento"},
                                    {"name": "Casos", "id": "casos", "type": "numeric", "format": {"specifier": ","}},
                                    {"name": "Población", "id": "poblacion", "type": "numeric", "format": {"specifier": ","}},
                                    {"name": "Incidencia x 100k", "id": "incidencia", "type": "numeric", "format": {"specifier": ".1f"}}
                                ],
                                page_size=10,
                                style_table={'overflowX': 'auto', 'borderRadius': '8px'},
                                style_cell={
                                    'textAlign': 'left',
                                    'padding': '12px',
                                    'fontFamily': 'Segoe UI',
                                    'border': '1px solid #dee2e6'
                                },
                                style_header={
                                    'backgroundColor': '#f8f9fa',
                                    'fontWeight': 'bold',
                                    'border': '1px solid #dee2e6'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': 'rgb(248, 248, 248)'
                                    }
                                ]
                            )
                        ], className="card")
                    ], className="twelve columns")
                ], className="row")
            ], className="nine columns")
        ], className="row")
    ], className="container")
])

# =============================================================================
# CALLBACKS
# =============================================================================

@app.callback(
    [Output('mapa-simulado', 'figure'),
     Output('top-departamentos', 'figure'),
     Output('distribucion-casos', 'figure'),
     Output('tabla-datos', 'data')],
    [Input('departamento-dropdown', 'value'),
     Input('tipo-visualizacion', 'value')]
)
def actualizar_dashboard(departamento_seleccionado, tipo_visualizacion):
    
    # Filtrar datos según selección
    if departamento_seleccionado == 'Todos':
        df_filtrado = df_dashboard.copy()
    else:
        df_filtrado = df_dashboard[df_dashboard['Departamento'] == departamento_seleccionado]
    
    # Configuración según tipo de visualización
    if tipo_visualizacion == 'casos':
        columna = 'casos'
        titulo = 'Casos de COVID-19 por Departamento'
        color = '#1f77b4'
    else:
        columna = 'incidencia'
        titulo = 'Incidencia de COVID-19 (x 100,000 hab.)'
        color = '#d62728'
    
    # 1. Gráfico principal de barras
    fig_mapa = px.bar(
        df_filtrado.sort_values(columna, ascending=True),
        x=columna,
        y='Departamento',
        orientation='h',
        title=titulo,
        color_discrete_sequence=[color]
    )
    
    fig_mapa.update_layout(
        height=400,
        showlegend=False,
        plot_bgcolor='white',
        yaxis={'categoryorder': 'total ascending'},
        margin={'t': 50}
    )
    
    # 2. Top 10 departamentos
    df_top10 = df_dashboard.nlargest(10, columna)
    
    fig_top = px.bar(
        df_top10,
        x=columna,
        y='Departamento',
        orientation='h',
        title=f'Top 10 Departamentos - {titulo}',
        color_discrete_sequence=[color]
    )
    
    fig_top.update_layout(
        height=300,
        showlegend=False,
        plot_bgcolor='white',
        yaxis={'categoryorder': 'total ascending'},
        margin={'t': 50}
    )
    
    # 3. Gráfico de distribución
    if tipo_visualizacion == 'casos':
        bins = [0, 1000, 5000, 10000, 50000, float('inf')]
        labels = ['0-1k', '1k-5k', '5k-10k', '10k-50k', '50k+']
    else:
        bins = [0, 100, 500, 1000, 5000, float('inf')]
        labels = ['0-100', '100-500', '500-1k', '1k-5k', '5k+']
    
    df_dashboard_temp = df_dashboard.copy()
    df_dashboard_temp['rango'] = pd.cut(df_dashboard_temp[columna], bins=bins, labels=labels)
    distribucion = df_dashboard_temp['rango'].value_counts().sort_index()
    
    fig_dist = px.pie(
        values=distribucion.values,
        names=distribucion.index,
        title=f'Distribución de {titulo.split(" - ")[0]}'
    )
    
    fig_dist.update_layout(height=300, margin={'t': 50})
    
    # 4. Datos para la tabla
    tabla_data = df_filtrado.to_dict('records')
    
    return fig_mapa, fig_top, fig_dist, tabla_data

# =============================================================================
# EJECUCIÓN
# =============================================================================

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)

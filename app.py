import os
import pandas as pd
import numpy as np
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
from dash import dash_table
import json

print("Iniciando Dashboard COVID-19 Colombia")

# Configuración
DATA_DIR = "data"

# =============================================================================
# 1. CARGAR DATOS CSV
# =============================================================================
try:
    csv_path = os.path.join(DATA_DIR, "COVID_muestra_50000.csv")
    print(f"Cargando datos desde: {csv_path}")
    
    # Intentar diferentes encodings
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
    df = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(csv_path, encoding=encoding, low_memory=False)
            print(f"CSV cargado con encoding: {encoding}")
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Error con {encoding}: {e}")
            continue
    
    if df is None:
        raise Exception("No se pudo cargar el CSV con ningún encoding")
        
    print(f"Datos cargados: {df.shape[0]:,} filas, {df.shape[1]} columnas")
    print("Columnas disponibles:", df.columns.tolist())
    
except Exception as e:
    print(f"Error cargando CSV: {e}")
    # Crear datos de ejemplo para desarrollo
    print("Creando datos de ejemplo...")
    np.random.seed(42)
    departamentos = ['BOGOTA', 'ANTIOQUIA', 'VALLE', 'CUNDINAMARCA', 'SANTANDER', 
                    'ATLANTICO', 'BOLIVAR', 'NARIÑO', 'BOYACA', 'MAGDALENA']
    
    df = pd.DataFrame({
        'Departamento_nom': np.random.choice(departamentos, 1000),
        'Edad': np.random.randint(20, 80, 1000),
        'Sexo': np.random.choice(['M', 'F'], 1000),
        'Estado': np.random.choice(['Leve', 'Moderado', 'Grave', 'Fallecido'], 1000),
        'Fecha_diagnostico': pd.date_range('2021-01-01', periods=1000, freq='D'),
        'Ciudad': np.random.choice(['Bogotá', 'Medellín', 'Cali', 'Barranquilla'], 1000)
    })

# =============================================================================
# 2. CONFIGURAR COLUMNAS Y DATOS
# =============================================================================
# Detectar columna de departamento
possible_depto_cols = ["Departamento_nom", "Departamento", "DEPARTAMENTO", "departamento", "DPTO", "dpto"]
col_depto = next((c for c in possible_depto_cols if c in df.columns), None)

if col_depto is None:
    # Buscar cualquier columna que contenga 'depart'
    for col in df.columns:
        if 'depart' in col.lower():
            col_depto = col
            break

if col_depto is None:
    # Usar primera columna categórica
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].nunique() < 50:
            col_depto = col
            break

if col_depto is None:
    # Último recurso
    df['Departamento'] = 'COLOMBIA'
    col_depto = 'Departamento'

print(f"Columna de departamento: {col_depto}")

# =============================================================================
# 3. COORDENADAS DE DEPARTAMENTOS (REEMPLAZO DEL SHAPEFILE)
# =============================================================================
departamento_coords = {
    'BOGOTA': {'lat': 4.6097, 'lon': -74.0817, 'capital': 'Bogotá'},
    'ANTIOQUIA': {'lat': 6.2442, 'lon': -75.5736, 'capital': 'Medellín'},
    'VALLE': {'lat': 3.395, 'lon': -76.495, 'capital': 'Cali'},
    'CUNDINAMARCA': {'lat': 4.5981, 'lon': -74.0758, 'capital': 'Bogotá'},
    'SANTANDER': {'lat': 7.1254, 'lon': -73.1198, 'capital': 'Bucaramanga'},
    'ATLANTICO': {'lat': 10.9639, 'lon': -74.7964, 'capital': 'Barranquilla'},
    'BOLIVAR': {'lat': 10.3997, 'lon': -75.5144, 'capital': 'Cartagena'},
    'NARIÑO': {'lat': 1.2136, 'lon': -77.2811, 'capital': 'Pasto'},
    'BOYACA': {'lat': 5.5353, 'lon': -73.3678, 'capital': 'Tunja'},
    'MAGDALENA': {'lat': 11.2408, 'lon': -74.1990, 'capital': 'Santa Marta'},
    'NORTE SANTANDER': {'lat': 7.9463, 'lon': -72.8988, 'capital': 'Cúcuta'},
    'HUILA': {'lat': 2.5359, 'lon': -75.5277, 'capital': 'Neiva'},
    'CAUCA': {'lat': 2.4417, 'lon': -76.6064, 'capital': 'Popayán'},
    'META': {'lat': 4.1510, 'lon': -73.6380, 'capital': 'Villavicencio'},
    'CESAR': {'lat': 10.4631, 'lon': -73.2532, 'capital': 'Valledupar'},
    'CORDOBA': {'lat': 8.7500, 'lon': -75.8833, 'capital': 'Montería'},
    'TOLIMA': {'lat': 4.4389, 'lon': -75.2322, 'capital': 'Ibagué'},
    'CALDAS': {'lat': 5.0589, 'lon': -75.4914, 'capital': 'Manizales'},
    'RISARALDA': {'lat': 4.8020, 'lon': -75.6980, 'capital': 'Pereira'},
    'QUINDIO': {'lat': 4.5310, 'lon': -75.6800, 'capital': 'Armenia'},
    'SUCRE': {'lat': 9.3047, 'lon': -75.3978, 'capital': 'Sincelejo'},
    'LA GUAJIRA': {'lat': 11.5444, 'lon': -72.9072, 'capital': 'Riohacha'},
    'CHOCO': {'lat': 5.6900, 'lon': -76.6600, 'capital': 'Quibdó'},
    'CAQUETA': {'lat': 1.6144, 'lon': -75.6061, 'capital': 'Florencia'},
    'ARAUCA': {'lat': 7.0903, 'lon': -70.7617, 'capital': 'Arauca'},
    'CASANARE': {'lat': 5.3500, 'lon': -72.4100, 'capital': 'Yopal'},
    'PUTUMAYO': {'lat': 0.8850, 'lon': -76.5089, 'capital': 'Mocoa'},
    'AMAZONAS': {'lat': -1.4167, 'lon': -71.5167, 'capital': 'Leticia'},
    'GUAINIA': {'lat': 2.5700, 'lon': -68.1300, 'capital': 'Inírida'},
    'VICHADA': {'lat': 4.4236, 'lon': -69.2878, 'capital': 'Puerto Carreño'},
    'VAUPES': {'lat': 0.3714, 'lon': -70.7667, 'capital': 'Mitú'},
    'SAN ANDRES': {'lat': 12.5567, 'lon': -81.7189, 'capital': 'San Andrés'}
}

# =============================================================================
# 4. PREPARAR DATOS PARA GRÁFICOS
# =============================================================================
# Agregar datos por departamento
df_group = df.groupby(col_depto).size().reset_index(name="Total_Casos")
df_group = df_group.sort_values("Total_Casos", ascending=False)

# Preparar datos para mapa
map_df = df_group.copy()
map_df['depto_upper'] = map_df[col_depto].astype(str).str.upper().str.strip()

# Agregar coordenadas
map_df['lat'] = map_df['depto_upper'].map(lambda x: departamento_coords.get(x, {}).get('lat', 4.5))
map_df['lon'] = map_df['depto_upper'].map(lambda x: departamento_coords.get(x, {}).get('lon', -74))
map_df['capital'] = map_df['depto_upper'].map(lambda x: departamento_coords.get(x, {}).get('capital', 'N/A'))
map_df['size'] = np.log10(map_df['Total_Casos'] + 1) * 15  # Tamaño proporcional

print("Datos preparados para visualización")

# =============================================================================
# 5. CREAR APLICACIÓN DASH
# =============================================================================
app = Dash(__name__)
server = app.server

# Opciones para dropdown
dept_options = [{"label": dept, "value": dept} for dept in sorted(df[col_depto].astype(str).unique())]

app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Dashboard COVID-19 Colombia 2021", 
                style={"textAlign": "center", "color": "white", "margin": "0", "padding": "10px"}),
        html.P("Visualización interactiva de casos por departamento", 
               style={"textAlign": "center", "color": "white", "margin": "0", "paddingBottom": "10px"})
    ], style={"backgroundColor": "#2c3e50", "marginBottom": "20px", "borderRadius": "10px"}),
    
    # Filtros
    html.Div([
        html.Label("Filtrar por Departamento:", 
                  style={"fontWeight": "bold", "marginRight": "10px", "fontSize": "16px"}),
        dcc.Dropdown(
            id="filtro-depto",
            options=dept_options,
            placeholder="Selecciona un departamento...",
            value=None,
            style={"width": "400px", "display": "inline-block"}
        )
    ], style={"textAlign": "center", "padding": "20px", "backgroundColor": "#ecf0f1", 
              "borderRadius": "10px", "marginBottom": "20px"}),
    
    # KPIs
    html.Div(id="kpis", style={
        "display": "flex", 
        "justifyContent": "center", 
        "gap": "20px", 
        "marginBottom": "20px",
        "flexWrap": "wrap"
    }),
    
    # Mapa y Gráfico
    html.Div([
        # Mapa
        html.Div([
            html.H3("Distribución Geográfica de Casos", 
                   style={"textAlign": "center", "color": "#2c3e50", "marginBottom": "15px"}),
            dcc.Graph(id="mapa-casos", style={"height": "500px", "borderRadius": "10px"})
        ], style={"flex": "2", "minWidth": "500px", "margin": "10px", "padding": "15px", 
                 "backgroundColor": "white", "borderRadius": "10px", 
                 "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"}),
        
        # Gráfico de barras
        html.Div([
            html.H3("Top 10 Departamentos", 
                   style={"textAlign": "center", "color": "#2c3e50", "marginBottom": "15px"}),
            dcc.Graph(id="top10-barras", style={"height": "500px", "borderRadius": "10px"})
        ], style={"flex": "1", "minWidth": "400px", "margin": "10px", "padding": "15px",
                 "backgroundColor": "white", "borderRadius": "10px",
                 "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"})
    ], style={"display": "flex", "flexWrap": "wrap", "justifyContent": "center", "gap": "20px", "marginBottom": "20px"}),
    
    # Tabla de datos
    html.Div([
        html.H3("Datos Detallados", 
               style={"textAlign": "center", "color": "#2c3e50", "marginBottom": "10px"}),
        html.P("Primeras 100 filas de datos - " + col_depto, 
               style={"textAlign": "center", "color": "#7f8c8d", "marginBottom": "20px"}),
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
                "border": "1px solid #ddd",
                "minWidth": "100px",
                "maxWidth": "200px"
            },
            style_header={
                "backgroundColor": "#34495e",
                "color": "white",
                "fontWeight": "bold",
                "textAlign": "center"
            },
            style_data={
                "backgroundColor": "#f8f9fa"
            }
        )
    ], style={"marginBottom": "30px", "padding": "20px", "backgroundColor": "white", 
              "borderRadius": "10px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"}),
    
    # Footer
    html.Footer([
        html.P("Dashboard desarrollado para análisis geográfico de casos COVID-19 - 2021", 
               style={"textAlign": "center", "color": "#7f8c8d", "margin": "0", "padding": "10px"})
    ], style={"backgroundColor": "#ecf0f1", "borderRadius": "10px"})
], style={"padding": "20px", "fontFamily": "Arial, sans-serif", "maxWidth": "1400px", "margin": "0 auto"})

# =============================================================================
# 6. CALLBACKS
# =============================================================================
@app.callback(
    [
        Output("mapa-casos", "figure"),
        Output("top10-barras", "figure"),
        Output("kpis", "children"),
        Output("tabla", "data"),
        Output("tabla", "columns")
    ],
    [Input("filtro-depto", "value")]
)
def actualizar_dashboard(filtro_depto):
    try:
        print(f"Actualizando dashboard con filtro: {filtro_depto}")
        
        # Filtrar datos
        if filtro_depto:
            df_filtrado = df[df[col_depto].astype(str) == str(filtro_depto)]
            map_data = map_df[map_df[col_depto].astype(str) == str(filtro_depto)]
        else:
            df_filtrado = df.copy()
            map_data = map_df.copy()
        
        # ==================== KPIs ====================
        total_casos = len(df_filtrado)
        num_departamentos = df_filtrado[col_depto].nunique()
        promedio_x_depto = total_casos / num_departamentos if num_departamentos > 0 else 0
        
        kpis = [
            html.Div([
                html.Div("", style={"fontSize": "2em", "marginBottom": "5px"}),
                html.Div(f"{total_casos:,}", style={"fontSize": "1.8em", "fontWeight": "bold", "color": "#e74c3c"}),
                html.Div("Total de Casos", style={"fontSize": "0.9em", "color": "#7f8c8d"})
            ], style={"textAlign": "center", "padding": "20px", "backgroundColor": "white", 
                     "borderRadius": "10px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)", 
                     "minWidth": "150px"}),
            
            html.Div([
                html.Div("", style={"fontSize": "2em", "marginBottom": "5px"}),
                html.Div(f"{num_departamentos}", style={"fontSize": "1.8em", "fontWeight": "bold", "color": "#3498db"}),
                html.Div("Departamentos", style={"fontSize": "0.9em", "color": "#7f8c8d"})
            ], style={"textAlign": "center", "padding": "20px", "backgroundColor": "white", 
                     "borderRadius": "10px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)", 
                     "minWidth": "150px"}),
            
            html.Div([
                html.Div("", style={"fontSize": "2em", "marginBottom": "5px"}),
                html.Div(f"{promedio_x_depto:,.0f}", style={"fontSize": "1.8em", "fontWeight": "bold", "color": "#27ae60"}),
                html.Div("Promedio por Depto", style={"fontSize": "0.9em", "color": "#7f8c8d"})
            ], style={"textAlign": "center", "padding": "20px", "backgroundColor": "white", 
                     "borderRadius": "10px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)", 
                     "minWidth": "150px"})
        ]
        
        # ==================== MAPA ====================
        fig_mapa = px.scatter_mapbox(
            map_data,
            lat="lat",
            lon="lon",
            size="size",
            color="Total_Casos",
            hover_name=col_depto,
            hover_data={
                "Total_Casos": True,
                "capital": True,
                "lat": False,
                "lon": False,
                "size": False
            },
            color_continuous_scale="Viridis",
            size_max=30,
            zoom=4.5,
            center={"lat": 4.5, "lon": -74},
            title=""
        )
        
        fig_mapa.update_layout(
            mapbox_style="carto-positron",
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            height=500,
            coloraxis_colorbar=dict(
                title="Nº de Casos",
                thickness=15
            )
        )
        
        # ==================== GRÁFICO DE BARRAS ====================
        if filtro_depto:
            top_data = df_filtrado.groupby(col_depto).size().reset_index(name="Total_Casos")
        else:
            top_data = df_group.head(10)
        
        fig_barras = px.bar(
            top_data.head(10),
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
            margin={"t": 30, "b": 100},
            height=500
        )
        
        # ==================== TABLA ====================
        # Seleccionar columnas relevantes para mostrar
        columnas_interes = [
            col_depto, 'Edad', 'Sexo', 'Estado', 'Fecha_diagnostico', 
            'Fecha Not', 'Ciudad', 'Tipo', 'Ubicacion'
        ]
        
        columnas_tabla = [col for col in columnas_interes if col in df_filtrado.columns][:6]
        
        if not columnas_tabla:
            columnas_tabla = df_filtrado.columns[:6].tolist()
        
        datos_tabla = df_filtrado[columnas_tabla].head(100)
        datos_dict = datos_tabla.to_dict('records')
        columnas_dict = [{"name": col, "id": col} for col in datos_tabla.columns]
        
        print("Dashboard actualizado")
        return fig_mapa, fig_barras, kpis, datos_dict, columnas_dict
        
    except Exception as e:
        print(f"Error en callback: {e}")
        import traceback
        traceback.print_exc()
        
        # Figuras de error
        fig_error = px.scatter(title="Error cargando datos")
        mensaje_error = html.Div([
            html.H4("Error en la aplicación", style={"color": "red", "textAlign": "center"}),
            html.P(str(e), style={"textAlign": "center"})
        ])
        
        return fig_error, fig_error, [mensaje_error], [], []

print("Aplicación Dash configurada correctamente")
print("Servidor listo para iniciar")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8050))
    print(f"🚀 Iniciando servidor en puerto {port}")
    app.run_server(debug=False, host='0.0.0.0', port=port)


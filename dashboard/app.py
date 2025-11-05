"""
Dashboard Índice de Seguridad Económica - OPTIMIZADO
Real Instituto Elcano

OPTIMIZACIÓN: DuckDB lee Parquet directamente sin cargar todo en memoria
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import duckdb
import os
import hashlib
from datetime import date
import base64
import requests   # <--- AÑADIR ESTA
import pathlib    # <--- AÑADIR ESTA

# ============================================
# CONFIGURACIÓN
# ============================================

st.set_page_config(
    page_title="Índice de Seguridad Económica | Real Instituto Elcano",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

ELCANO_COLORS = {
    'primary': '#bb2521',
    'secondary': '#2C3A4B',
    'text': '#2c3a4b',
    'background': '#FFFFFF',
}

DEPENDENCY_SCALE = ['#FFEBEE', '#FFCDD2', '#EF9A9A', '#E57373', '#d63834', '#bb2521']

# ============================================
# CSS
# ============================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; font-size: 16px; }
    .main-header {
        background: #FFFFFF;
        padding: 2rem 0 1rem 0;
        border-bottom: 3px solid #bb2521;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        gap: 2rem;
    }
    .main-header img {
        height: 120px;
        width: auto;
    }
    .main-header .header-text {
        flex: 1;
    }
    .main-header h1 { color: #2C3A4B; font-weight: 600; margin: 0; font-size: 6rem !important; line-height: 1.1; }
    h1 { font-size: 6rem !important; }
    .main-header .subtitle { color: #666666; margin: 0.5rem 0 0 0; font-size: 1.2rem; }
    .main-header .red-accent { color: #bb2521; font-weight: 700; }
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-left: 4px solid #bb2521;
        padding: 1.5rem;
        border-radius: 4px;
        height: 100%;
    }
    .kpi-value { font-size: 4rem; font-weight: 700; color: #bb2521; margin: 0; line-height: 1.2; }
    .kpi-label { font-size: 1.1rem; color: #666666; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.5rem; font-weight: 600; }
    .stSelectbox label { font-weight: 500; color: #2C3A4B; font-size: 1.1rem; }
    .stTabs [aria-selected="true"] { color: #bb2521; border-bottom-color: #bb2521; font-size: 1.1rem; }
    .stTabs [data-baseweb="tab"] { font-size: 1.1rem; }
    .footer { margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #E0E0E0; text-align: center; color: #666666; font-size: 1rem; }
    p, div, span { font-size: 1.05rem; }
    .stMetric label { font-size: 1.1rem; }
    .stMetric .css-1xarl3l { font-size: 2.2rem; }
    .stMetric [data-testid="stMetricValue"] { font-size: 2.2rem !important; }
</style>
""", unsafe_allow_html=True)

# ... (Después de tu bloque de CSS) ...

# ============================================
# CONSTANTES DE DATOS
# ============================================

# 1. URL de descarga directa de Google Drive (¡reemplaza con la tuya!)
GDRIVE_FILE_URL = "https://drive.google.com/uc?export=download&id=1BEO33LWp_gMRL1F5aG8X_Cem0QQGgl_i"

# 2. Ruta donde se guardará el archivo en el disco temporal de Streamlit Cloud
LOCAL_FILE_PATH = "/tmp/dependencies_full.parquet"


# ============================================
# FUNCIONES AUXILIARES
# ============================================
# ... (tus funciones get_flag_emoji, etc.) ...

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def get_flag_emoji(country_code):
    """Convierte código ISO-3 a emoji de bandera usando ISO-2"""
    # Mapeo de ISO-3 a ISO-2 (sólo principales, expandir según necesidad)
    iso3_to_iso2 = {
        'USA': 'US', 'CHN': 'CN', 'JPN': 'JP', 'DEU': 'DE', 'GBR': 'GB',
        'FRA': 'FR', 'IND': 'IN', 'ITA': 'IT', 'BRA': 'BR', 'CAN': 'CA',
        'KOR': 'KR', 'RUS': 'RU', 'AUS': 'AU', 'ESP': 'ES', 'MEX': 'MX',
        'IDN': 'ID', 'NLD': 'NL', 'SAU': 'SA', 'TUR': 'TR', 'CHE': 'CH',
        'POL': 'PL', 'BEL': 'BE', 'SWE': 'SE', 'NOR': 'NO', 'AUT': 'AT',
        'ARE': 'AE', 'NGA': 'NG', 'ARG': 'AR', 'ZAF': 'ZA', 'EGY': 'EG',
        'DNK': 'DK', 'SGP': 'SG', 'MYS': 'MY', 'PHL': 'PH', 'VNM': 'VN',
        'THA': 'TH', 'COL': 'CO', 'CHL': 'CL', 'FIN': 'FI', 'PRT': 'PT',
        'IRL': 'IE', 'NZL': 'NZ', 'GRC': 'GR', 'CZE': 'CZ', 'ROU': 'RO',
        'PER': 'PE', 'HKG': 'HK', 'IRQ': 'IQ', 'QAT': 'QA', 'KWT': 'KW',
        'UKR': 'UA', 'MAR': 'MA', 'ECU': 'EC', 'KEN': 'KE', 'ETH': 'ET',
        'HUN': 'HU', 'LUX': 'LU', 'PAK': 'PK', 'BGD': 'BD', 'VEN': 'VE',
        'DZA': 'DZ', 'KAZ': 'KZ', 'OMN': 'OM', 'URY': 'UY', 'HRV': 'HR',
        'BGR': 'BG', 'SVK': 'SK', 'SVN': 'SI', 'LTU': 'LT', 'LVA': 'LV',
        'EST': 'EE', 'BLR': 'BY', 'TUN': 'TN', 'JOR': 'JO', 'LBN': 'LB',
        'LBY': 'LY', 'YEM': 'YE', 'SYR': 'SY', 'ISR': 'IL', 'PAN': 'PA',
        'CRI': 'CR', 'GTM': 'GT', 'DOM': 'DO', 'LKA': 'LK', 'MMR': 'MM',
        'AGO': 'AO', 'TZA': 'TZ', 'GHA': 'GH', 'CMR': 'CM', 'CIV': 'CI',
        'UGA': 'UG', 'SDN': 'SD', 'DRC': 'CD', 'SEN': 'SN', 'ZMB': 'ZM',
        'ZWE': 'ZW', 'RWA': 'RW', 'BWA': 'BW', 'NAM': 'NA', 'MOZ': 'MZ',
        'MDG': 'MG', 'MLI': 'ML', 'NER': 'NE', 'TCD': 'TD', 'BFA': 'BF',
        'GIN': 'GN', 'BEN': 'BJ', 'TGO': 'TG', 'SLE': 'SL', 'LBR': 'LR',
        'MRT': 'MR', 'GMB': 'GM', 'GAB': 'GA', 'GNQ': 'GQ', 'MUS': 'MU',
        'SWZ': 'SZ', 'LSO': 'LS', 'BOL': 'BO', 'PRY': 'PY', 'SLV': 'SV',
        'HND': 'HN', 'NIC': 'NI', 'JAM': 'JM', 'TTO': 'TT', 'GUY': 'GY',
        'SUR': 'SR', 'BHS': 'BS', 'BRB': 'BB', 'ISL': 'IS', 'MLT': 'MT',
        'CYP': 'CY', 'BHR': 'BH', 'BRN': 'BN', 'MNG': 'MN', 'KHM': 'KH',
        'LAO': 'LA', 'NPL': 'NP', 'AFG': 'AF', 'LKA': 'LK', 'BGD': 'BD',
        'MDA': 'MD', 'MKD': 'MK', 'ALB': 'AL', 'BIH': 'BA', 'SRB': 'RS',
        'MNE': 'ME', 'KOS': 'XK', 'GEO': 'GE', 'ARM': 'AM', 'AZE': 'AZ'
    }
    
    iso2 = iso3_to_iso2.get(country_code, None)
    if iso2:
        # Convertir ISO-2 a emoji de bandera
        # Los emojis de banderas usan Regional Indicator Symbols (U+1F1E6 a U+1F1FF)
        return ''.join(chr(0x1F1E6 + ord(c) - ord('A')) for c in iso2)
    return '🏴'  # Bandera negra genérica si no se encuentra

def get_flag_html(country_code, size=20):
    """Genera HTML para mostrar bandera desde flagcdn.com"""
    iso3_to_iso2 = {
        'USA': 'us', 'CHN': 'cn', 'JPN': 'jp', 'DEU': 'de', 'GBR': 'gb',
        'FRA': 'fr', 'IND': 'in', 'ITA': 'it', 'BRA': 'br', 'CAN': 'ca',
        'KOR': 'kr', 'RUS': 'ru', 'AUS': 'au', 'ESP': 'es', 'MEX': 'mx',
        'IDN': 'id', 'NLD': 'nl', 'SAU': 'sa', 'TUR': 'tr', 'CHE': 'ch',
        'POL': 'pl', 'BEL': 'be', 'SWE': 'se', 'NOR': 'no', 'AUT': 'at',
        'ARE': 'ae', 'NGA': 'ng', 'ARG': 'ar', 'ZAF': 'za', 'EGY': 'eg',
        'DNK': 'dk', 'SGP': 'sg', 'MYS': 'my', 'PHL': 'ph', 'VNM': 'vn',
        'THA': 'th', 'COL': 'co', 'CHL': 'cl', 'FIN': 'fi', 'PRT': 'pt',
        'IRL': 'ie', 'NZL': 'nz', 'GRC': 'gr', 'CZE': 'cz', 'ROU': 'ro',
        'PER': 'pe', 'HKG': 'hk', 'IRQ': 'iq', 'QAT': 'qa', 'KWT': 'kw',
        'UKR': 'ua', 'MAR': 'ma', 'ECU': 'ec', 'KEN': 'ke', 'ETH': 'et',
        'HUN': 'hu', 'LUX': 'lu', 'PAK': 'pk', 'BGD': 'bd', 'VEN': 've',
        'DZA': 'dz', 'KAZ': 'kz', 'OMN': 'om', 'URY': 'uy', 'HRV': 'hr',
        'BGR': 'bg', 'SVK': 'sk', 'SVN': 'si', 'LTU': 'lt', 'LVA': 'lv',
        'EST': 'ee', 'BLR': 'by', 'TUN': 'tn', 'JOR': 'jo', 'LBN': 'lb',
        'LBY': 'ly', 'YEM': 'ye', 'SYR': 'sy', 'ISR': 'il', 'PAN': 'pa',
        'CRI': 'cr', 'GTM': 'gt', 'DOM': 'do', 'LKA': 'lk', 'MMR': 'mm',
        'AGO': 'ao', 'TZA': 'tz', 'GHA': 'gh', 'CMR': 'cm', 'CIV': 'ci',
        'UGA': 'ug', 'SDN': 'sd', 'DRC': 'cd', 'SEN': 'sn', 'ZMB': 'zm',
        'ZWE': 'zw', 'RWA': 'rw', 'BWA': 'bw', 'NAM': 'na', 'MOZ': 'mz',
        'MDG': 'mg', 'MLI': 'ml', 'NER': 'ne', 'TCD': 'td', 'BFA': 'bf',
        'GIN': 'gn', 'BEN': 'bj', 'TGO': 'tg', 'SLE': 'sl', 'LBR': 'lr',
        'MRT': 'mr', 'GMB': 'gm', 'GAB': 'ga', 'GNQ': 'gq', 'MUS': 'mu',
        'SWZ': 'sz', 'LSO': 'ls', 'BOL': 'bo', 'PRY': 'py', 'SLV': 'sv',
        'HND': 'hn', 'NIC': 'ni', 'JAM': 'jm', 'TTO': 'tt', 'GUY': 'gy',
        'SUR': 'sr', 'BHS': 'bs', 'BRB': 'bb', 'ISL': 'is', 'MLT': 'mt',
        'CYP': 'cy', 'BHR': 'bh', 'BRN': 'bn', 'MNG': 'mn', 'KHM': 'kh',
        'LAO': 'la', 'NPL': 'np', 'AFG': 'af', 'LKA': 'lk', 'BGD': 'bd',
        'MDA': 'md', 'MKD': 'mk', 'ALB': 'al', 'BIH': 'ba', 'SRB': 'rs',
        'MNE': 'me', 'KOS': 'xk', 'GEO': 'ge', 'ARM': 'am', 'AZE': 'az'
    }
    
    iso2 = iso3_to_iso2.get(country_code, None)
    if iso2:
        return f'<img src="https://flagcdn.com/w{size}/{iso2}.png" width="{size}" style="margin-right: 8px; vertical-align: middle;">'
    return ''

def get_daily_industry(industries_list):
    """
    Selecciona una industria según la fecha actual.
    La misma industria se muestra durante todo el día.
    Cambia automáticamente cada día.
    """
    if not industries_list:
        return None
    seed = int(hashlib.md5(str(date.today()).encode()).hexdigest(), 16)
    return industries_list[seed % len(industries_list)]

# ============================================
# DUCKDB CONNECTION (OPTIMIZADO PARA CLOUD)
# ============================================

@st.cache_resource
def get_duckdb_connection():
    """
    Descarga el Parquet desde GDrive si no existe en el disco temporal,
    luego se conecta con DuckDB (cacheado, se crea una sola vez).
    """
    
    # 1. Comprobar si el archivo ya existe en el disco temporal
    file = pathlib.Path(LOCAL_FILE_PATH)
    
    if not file.exists():
        # Si no existe, mostrar un spinner y descargarlo
        with st.spinner(f"Descargando base de datos (160MB) desde Google Drive... Esto solo pasa una vez."):
            try:
                # Descargar el archivo
                response = requests.get(GDRIVE_FILE_URL, stream=True)
                response.raise_for_status() # Lanza error si la descarga falla
                
                # Guardar el archivo en el disco local
                with open(LOCAL_FILE_PATH, "wb") as f:
                    # Usar iter_content para manejar archivos grandes
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                st.success("¡Base de datos descargada!")
            
            except Exception as e:
                st.error(f"Error al descargar el archivo desde Google Drive: {e}")
                st.error("Asegúrate de que la URL de GDrive es un enlace de descarga directa ('uc?export=download') y que es pública.")
                return None

    # 2. Conectar a DuckDB (ahora que sabemos que el archivo existe)
    try:
        con = duckdb.connect()
        
        # Configurar threads (esto ya lo tenías y es perfecto)
        n_threads = max(2, os.cpu_count() // 2)
        con.execute(f"PRAGMA threads={n_threads}")
        
        # 3. ¡LA CLAVE! Crear la vista leyendo de LOCAL_FILE_PATH
        # (Usamos f-string para insertar la variable)
        con.execute(f"""
            CREATE OR REPLACE VIEW deps AS
            SELECT * FROM read_parquet('{LOCAL_FILE_PATH}')
        """)
        
        return con
        
    except Exception as e:
        st.error(f"Error al conectar con DuckDB: {e}")
        return None


# ============================================
# QUERIES OPTIMIZADAS POR VISTA
# ============================================

@st.cache_data(ttl=600, show_spinner=False)
def query_country_profile(country, top_n=30):
    """Perfil completo de un país: principales dependencias"""
    con = get_duckdb_connection()
    
    # Top dependencias como importador
    sql = """
        SELECT 
            supplier_country,
            industry,
            AVG(dependency_value) as avg_dependency,
            AVG(direct_dependency) as avg_direct,
            AVG(indirect_dependency) as avg_indirect,
            SUM(trade_value) as total_trade,
            COUNT(DISTINCT year) as n_years
        FROM deps
        WHERE dependent_country = $country
        GROUP BY supplier_country, industry
        ORDER BY avg_dependency DESC
        LIMIT $top_n
    """
    
    params = {'country': country, 'top_n': int(top_n)}
    
    return con.execute(sql, params).df()

@st.cache_data(ttl=600, show_spinner=False)
def query_bilateral_evolution(dependent_country, supplier_country, industry):
    """Evolución temporal de dependencia bilateral para una industria específica"""
    con = get_duckdb_connection()
    
    sql = """
        SELECT 
            year,
            AVG(dependency_value) as dependency_value,
            AVG(direct_dependency) as direct_dependency,
            AVG(indirect_dependency) as indirect_dependency,
            AVG(trade_value) as trade_value
        FROM deps
        WHERE dependent_country = $dependent
          AND supplier_country = $supplier
          AND industry = $industry
        GROUP BY year
        ORDER BY year
    """
    
    params = {
        'dependent': dependent_country,
        'supplier': supplier_country,
        'industry': industry
    }
    
    return con.execute(sql, params).df()

@st.cache_data(ttl=600, show_spinner=False)
def query_summary_stats():
    """KPIs principales (rápido, no lee todo el dataset)"""
    con = get_duckdb_connection()
    
    stats = con.execute("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT dependent_country) as countries_dependent,
            COUNT(DISTINCT supplier_country) as countries_supplier,
            COUNT(DISTINCT industry) as industries,
            MIN(year) as min_year,
            MAX(year) as max_year,
            SUM(CASE WHEN dependency_value > 0.8 THEN 1 ELSE 0 END) as critical_dependencies
        FROM deps
    """).fetchone()
    
    return {
        'total_records': stats[0],
        'countries_dependent': stats[1],
        'countries_supplier': stats[2],
        'industries': stats[3],
        'years': [stats[4], stats[5]],
        'critical_dependencies': stats[6]
    }

@st.cache_data(ttl=600, show_spinner=False)
def query_world_map_data(industry, year=None):
    """
    Datos para mapa mundial de una industria específica.
    Agrega dependencia promedio por país dependiente.
    """
    con = get_duckdb_connection()
    
    where_clauses = ["industry = $industry"]
    params = {'industry': industry}
    
    if year and year != "Todos":
        where_clauses.append("year = $year")
        params['year'] = int(year)
    
    where_clause = "WHERE " + " AND ".join(where_clauses)
    
    sql = f"""
        SELECT 
            dependent_country as country_code,
            AVG(dependency_value) as avg_dependency,
            SUM(trade_value) as total_trade,
            COUNT(*) as n_dependencies,
            MAX(dependency_value) as max_dependency
        FROM deps
        {where_clause}
        GROUP BY dependent_country
        ORDER BY avg_dependency DESC
    """
    
    return con.execute(sql, params).df()

@st.cache_data(ttl=600, show_spinner=False)
def query_top_dependencies(year=None, country=None, industry=None, n=15):
    """Top N dependencias críticas (pre-agregado)"""
    con = get_duckdb_connection()
    
    where_clauses = []
    params = {'n': int(n)}
    
    if year and year != "Todos":
        where_clauses.append("year = $year")
        params['year'] = int(year)
    if country and country != "Todos":
        where_clauses.append("(dependent_country = $country OR supplier_country = $country)")
        params['country'] = country
    if industry and industry != "Todos":
        where_clauses.append("industry = $industry")
        params['industry'] = industry
    
    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    sql = f"""
        SELECT 
            dependent_country,
            supplier_country,
            industry,
            AVG(dependency_value) as dependency_value,
            SUM(trade_value) as trade_value
        FROM deps
        {where_clause}
        GROUP BY dependent_country, supplier_country, industry
        ORDER BY dependency_value DESC
        LIMIT $n
    """
    
    return con.execute(sql, params).df()

@st.cache_data(ttl=600, show_spinner=False)
def query_supply_chain_length(year=None, country=None, industry=None):
    """Distribución de longitud de cadenas (agregado)"""
    con = get_duckdb_connection()
    
    where_clauses = []
    params = {}
    
    if year and year != "Todos":
        where_clauses.append("year = $year")
        params['year'] = int(year)
    if country and country != "Todos":
        where_clauses.append("(dependent_country = $country OR supplier_country = $country)")
        params['country'] = country
    if industry and industry != "Todos":
        where_clauses.append("industry = $industry")
        params['industry'] = industry
    
    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    sql = f"""
        SELECT 
            longitud_optima,
            COUNT(*) as count
        FROM deps
        {where_clause}
        GROUP BY longitud_optima
        ORDER BY longitud_optima
    """
    
    return con.execute(sql, params).df()

@st.cache_data(ttl=600, show_spinner=False)
def query_heatmap_data(year=None, country=None, industry=None, top_n=20):
    """Mapa de calor (pre-agregado para top países)"""
    con = get_duckdb_connection()
    
    # Construir WHERE clause y parámetros
    where_clauses = []
    filter_params = []
    
    if year and year != "Todos":
        where_clauses.append("year = ?")
        filter_params.append(int(year))
    if country and country != "Todos":
        where_clauses.append("(dependent_country = ? OR supplier_country = ?)")
        filter_params.extend([country, country])
    if industry and industry != "Todos":
        where_clauses.append("industry = ?")
        filter_params.append(industry)
    
    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    # Obtener top países dependientes
    top_dependent_sql = f"""
        SELECT dependent_country
        FROM deps
        {where_clause}
        GROUP BY dependent_country
        ORDER BY SUM(dependency_value) DESC
        LIMIT ?
    """
    params_dep = filter_params + [int(top_n)]
    top_dependent = con.execute(top_dependent_sql, params_dep).df()['dependent_country'].tolist()
    
    # Obtener top países proveedores
    top_supplier_sql = f"""
        SELECT supplier_country
        FROM deps
        {where_clause}
        GROUP BY supplier_country
        ORDER BY SUM(dependency_value) DESC
        LIMIT ?
    """
    params_sup = filter_params + [int(top_n)]
    top_supplier = con.execute(top_supplier_sql, params_sup).df()['supplier_country'].tolist()
    
    # Si no hay resultados, devolver dataframe vacío
    if not top_dependent or not top_supplier:
        return pd.DataFrame(columns=['dependent_country', 'supplier_country', 'dependency_value'])
    
    # Obtener matriz agregada
    placeholders_dep = ','.join(['?' for _ in top_dependent])
    placeholders_sup = ','.join(['?' for _ in top_supplier])
    
    matrix_sql = f"""
        SELECT 
            dependent_country,
            supplier_country,
            AVG(dependency_value) as dependency_value
        FROM deps
        WHERE dependent_country IN ({placeholders_dep})
          AND supplier_country IN ({placeholders_sup})
          {' AND ' + ' AND '.join(where_clauses) if where_clauses else ''}
        GROUP BY dependent_country, supplier_country
    """
    
    matrix_params = top_dependent + top_supplier + filter_params
    return con.execute(matrix_sql, matrix_params).df()

@st.cache_data(ttl=600, show_spinner=False)
def query_filtered_sample(year=None, country=None, industry=None, limit=100):
    """Muestra de datos filtrados (limitada para preview)"""
    con = get_duckdb_connection()
    
    where_clauses = []
    params = {'limit': int(limit)}
    
    if year and year != "Todos":
        where_clauses.append("year = $year")
        params['year'] = int(year)
    if country and country != "Todos":
        where_clauses.append("(dependent_country = $country OR supplier_country = $country)")
        params['country'] = country
    if industry and industry != "Todos":
        where_clauses.append("industry = $industry")
        params['industry'] = industry
    
    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    sql = f"""
        SELECT *
        FROM deps
        {where_clause}
        LIMIT $limit
    """
    
    return con.execute(sql, params).df()

@st.cache_data(ttl=600)
def get_filter_options():
    """Obtiene las opciones para los filtros (cacheado)"""
    con = get_duckdb_connection()
    
    years = con.execute("SELECT DISTINCT year FROM deps ORDER BY year DESC").df()['year'].tolist()
    countries = con.execute("""
        SELECT DISTINCT country FROM (
            SELECT dependent_country as country FROM deps
            UNION
            SELECT supplier_country as country FROM deps
        ) ORDER BY country
    """).df()['country'].tolist()
    industries = con.execute("SELECT DISTINCT industry FROM deps ORDER BY industry").df()['industry'].tolist()
    
    return years, countries, industries

# ============================================
# FUNCIONES DE VISUALIZACIÓN
# ============================================

def create_kpi_cards(stats: dict):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{stats['years'][0]}-{stats['years'][1]}</div>
            <div class="kpi-label">Años Analizados</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{stats['countries_dependent']:,}</div>
            <div class="kpi-label">Países Analizados</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{stats['industries']:,}</div>
            <div class="kpi-label">Industrias</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{stats['critical_dependencies']:,}</div>
            <div class="kpi-label">Dependencias Críticas</div>
        </div>
        """, unsafe_allow_html=True)

def plot_bilateral_stacked_bars(df: pd.DataFrame, dependent: str, supplier: str, industry: str):
    """Gráfico de barras apiladas mostrando DD y DI por año"""
    fig = go.Figure()
    
    # Barra de Dependencia Directa (base)
    fig.add_trace(go.Bar(
        x=df['year'],
        y=df['direct_dependency'],
        name='Dependencia Directa (DD)',
        marker_color=ELCANO_COLORS['primary'],
        text=df['direct_dependency'].round(3),
        textposition='inside',
        hovertemplate='Año: %{x}<br>DD: %{y:.3f}<extra></extra>'
    ))
    
    # Barra de Dependencia Indirecta (apilada encima)
    fig.add_trace(go.Bar(
        x=df['year'],
        y=df['indirect_dependency'],
        name='Dependencia Indirecta (DI)',
        marker_color=ELCANO_COLORS['secondary'],
        text=df['indirect_dependency'].round(3),
        textposition='inside',
        hovertemplate='Año: %{x}<br>DI: %{y:.3f}<extra></extra>'
    ))
    
    # Título sin banderas (las banderas están en el header arriba del gráfico)
    title_text = f"Evolución de Dependencia: {dependent} ← {supplier}<br><sub>{industry}</sub>"
    
    fig.update_layout(
        title=title_text,
        xaxis_title="Año",
        yaxis_title="Nivel de Dependencia",
        barmode='stack',
        plot_bgcolor='white',
        height=500,
        font=dict(family='Roboto', size=13),
        title_font_size=18,
        xaxis_title_font_size=14,
        yaxis_title_font_size=14,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified'
    )
    
    # Añadir línea de Dependencia Total
    fig.add_trace(go.Scatter(
        x=df['year'],
        y=df['dependency_value'],
        name='Dependencia Total (DT)',
        mode='lines+markers',
        line=dict(color='black', width=2, dash='dash'),
        marker=dict(size=8, color='black'),
        hovertemplate='Año: %{x}<br>DT: %{y:.3f}<extra></extra>'
    ))
    
    return fig

def plot_world_dependency_map(df: pd.DataFrame, industry_name: str):
    """
    Mapa mundial coroplético mostrando nivel de dependencia por país.
    """
    fig = px.choropleth(
        df,
        locations="country_code",
        color="avg_dependency",
        hover_name="country_code",
        hover_data={
            "country_code": False,
            "avg_dependency": ":.3f",
            "max_dependency": ":.3f",
            "n_dependencies": True,
            "total_trade": ":,.0f"
        },
        color_continuous_scale=[
            [0, "#FFFFFF"],
            [0.3, "#FFEBEE"],
            [0.5, "#FFCDD2"],
            [0.7, "#EF9A9A"],
            [0.85, "#d63834"],
            [1, "#bb2521"]
        ],
        labels={
            "avg_dependency": "Dependencia Promedio",
            "max_dependency": "Dependencia Máxima",
            "n_dependencies": "Nº Dependencias",
            "total_trade": "Comercio Total"
        },
        title=f"Mapa Global de Dependencias: {industry_name}"
    )
    
    fig.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='natural earth',
            bgcolor='rgba(0,0,0,0)'
        ),
        height=600,
        font=dict(family='Roboto', size=14),
        plot_bgcolor='white',
        paper_bgcolor='white',
        title_font_size=18,
        coloraxis_colorbar=dict(
            title="Nivel de<br>Dependencia",
            thickness=20,
            len=0.7,
            title_font_size=14,
            tickfont_size=12
        )
    )
    
    return fig

def plot_top_dependencies(df: pd.DataFrame):
    # Crear labels sin banderas para Plotly
    df['label'] = df['dependent_country'] + ' ← ' + df['supplier_country']
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df['label'], x=df['dependency_value'], orientation='h',
        marker=dict(
            color=df['dependency_value'],
            colorscale=[[0, DEPENDENCY_SCALE[0]], [1, DEPENDENCY_SCALE[-1]]],
            showscale=True
        ),
        text=df['dependency_value'].round(3), textposition='auto'
    ))
    
    fig.update_layout(
        title=f"Top {len(df)} Dependencias Más Críticas",
        xaxis_title="Nivel de Dependencia",
        plot_bgcolor='white', height=500, margin=dict(l=200),
        font=dict(family='Roboto', size=13),
        title_font_size=18,
        xaxis_title_font_size=14,
        yaxis_tickfont_size=12
    )
    
    return fig

def plot_supply_chain_length(df: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['longitud_optima'], y=df['count'],
        marker_color=ELCANO_COLORS['primary'],
        text=df['count'], textposition='auto'
    ))
    
    fig.update_layout(
        title="Distribución de Longitud de Cadenas de Suministro",
        xaxis_title="Longitud de Cadena",
        yaxis_title="Número de Dependencias",
        plot_bgcolor='white', height=400,
        font=dict(family='Roboto', size=13),
        title_font_size=18,
        xaxis_title_font_size=14,
        yaxis_title_font_size=14
    )
    
    return fig

def plot_dependency_heatmap(df: pd.DataFrame):
    pivot = df.pivot_table(
        values='dependency_value',
        index='dependent_country',
        columns='supplier_country',
        aggfunc='mean'
    ).fillna(0)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index,
        colorscale=[[0, DEPENDENCY_SCALE[0]], [1, DEPENDENCY_SCALE[-1]]]
    ))
    
    fig.update_layout(
        title="Mapa de Dependencias",
        height=600,
        font=dict(family='Roboto', size=13),
        title_font_size=18,
        xaxis_tickfont_size=11,
        yaxis_tickfont_size=11
    )
    
    return fig

# ============================================
# APLICACIÓN PRINCIPAL
# ============================================

def main():
    # Header con logo y título
    col_logo, col_title = st.columns([1, 4])
    
    with col_logo:
        # Leer logo y convertir a base64
        try:
            logo_path = "logo.png"  # <--- CAMBIAR A ESTO
            with open(logo_path, "rb") as f:
                logo_data = base64.b64encode(f.read()).decode()
            st.markdown(f'<img src="data:image/png;base64,{logo_data}" style="height: 120px; width: auto;" alt="Real Instituto Elcano">', unsafe_allow_html=True)
        except Exception as e:
            st.session_state['logo_error'] = str(e)
    
    with col_title:
        st.title("Índice de Seguridad Económica")
        # Inyectar CSS específico DESPUÉS del título usando el selector exacto
        st.markdown("""
        <style>
        .st-emotion-cache-10trblm {
            font-size: 4rem !important;
            color: #2C3A4B !important;
        }
        .e1nzilvr1 {
            font-size: 4rem !important;
            color: #2C3A4B !important;
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown('<p style="font-size: 1.5rem; color: #666666; margin-top: -1rem; line-height: 1.3;"><span style="color: #bb2521; font-weight: 700; font-size: 1.5rem;">Real Instituto Elcano</span> de Estudios Internacionales y Estratégicos</p>', unsafe_allow_html=True)
    
    # Cargar KPIs (rápido, solo agregaciones)
    with st.spinner('Cargando estadísticas...'):
        stats = query_summary_stats()
        years, countries, industries = get_filter_options()
    
    create_kpi_cards(stats)
    st.markdown("---")
    
    # Sidebar con filtros
    with st.sidebar:
        # Mostrar error de logo si existe
        if 'logo_error' in st.session_state:
            st.warning(f"⚠️ Logo no cargado: {st.session_state['logo_error']}")
        
        st.markdown("### 🔍 Filtros de Datos")
        
        # Por defecto: último año
        year_options = ["Todos"] + years
        selected_year = st.selectbox("Año", year_options, index=1)
        
        country_options = ["Todos"] + countries
        selected_country = st.selectbox("País", country_options)
        
        industry_options = ["Todos"] + industries
        selected_industry = st.selectbox("Industria", industry_options)
        
        st.markdown("---")
        st.markdown("""
        ### 📊 Sobre el Índice
        Visualización optimizada con **DuckDB**.
        Solo carga datos necesarios.
        """)
        st.markdown("© 2025 Real Instituto Elcano")
    
    # Tabs de visualizaciones
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🌍 Mapa Global",
        "🔥 Top Dependencias",
        "🔗 Longitud de Cadenas",
        "🗺️ Mapa de Calor",
        "📈 Evolución Bilateral",
        "🇳 Ficha de País"
    ])
    
    with tab1:
        st.markdown("### 🎲 Industria del Día")
        
        # Seleccionar industria del día
        daily_industry = get_daily_industry(industries)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"**Industria destacada hoy:** {daily_industry}")
            st.caption("La industria destacada cambia automáticamente cada día para mostrar diferentes sectores críticos.")
        
        with col2:
            # Opción manual de cambio
            if st.button("🔄 Otra industria"):
                st.session_state.manual_industry = True
        
        # Permitir selección manual si se pulsa el botón
        if 'manual_industry' in st.session_state and st.session_state.manual_industry:
            selected_map_industry = st.selectbox(
                "Selecciona industria manualmente:",
                industries,
                index=industries.index(daily_industry) if daily_industry in industries else 0
            )
        else:
            selected_map_industry = daily_industry
        
        # Cargar y mostrar mapa
        with st.spinner('Generando mapa mundial...'):
            df_map = query_world_map_data(selected_map_industry, selected_year)
        
        if not df_map.empty:
            st.plotly_chart(
                plot_world_dependency_map(df_map, selected_map_industry),
                use_container_width=True
            )
            
            # Estadísticas del mapa
            st.markdown("#### 📊 Estadísticas Globales")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Países con Dependencia", len(df_map))
            with col2:
                st.metric("Dependencia Promedio Global", f"{df_map['avg_dependency'].mean():.3f}")
            with col3:
                max_country = df_map.loc[df_map['avg_dependency'].idxmax(), 'country_code']
                max_dep = df_map['avg_dependency'].max()
                st.metric(f"Mayor Dependencia", f"{max_country}: {max_dep:.3f}")
        else:
            st.warning("No hay datos disponibles para esta industria con los filtros seleccionados.")
    
    with tab2:
        with st.spinner('Generando visualización...'):
            df_top = query_top_dependencies(selected_year, selected_country, selected_industry, n=15)
        
        if not df_top.empty:
            st.plotly_chart(plot_top_dependencies(df_top), use_container_width=True)
            
            # Mostrar tabla con banderas HTML debajo del gráfico
            st.markdown("### 📊 Detalle con Banderas")
            
            for idx, row in df_top.iterrows():
                col1, col2, col3 = st.columns([3, 3, 2])
                
                with col1:
                    st.markdown(f"{get_flag_html(row['dependent_country'], 24)} **{row['dependent_country']}**", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"{get_flag_html(row['supplier_country'], 24)} {row['supplier_country']}", unsafe_allow_html=True)
                with col3:
                    st.metric("", f"{row['dependency_value']:.3f}", label_visibility="collapsed")
    
    with tab3:
        with st.spinner('Generando visualización...'):
            df_length = query_supply_chain_length(selected_year, selected_country, selected_industry)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.plotly_chart(plot_supply_chain_length(df_length), use_container_width=True)
        with col2:
            st.markdown("### 📊 Estadísticas")
            avg_length = (df_length['longitud_optima'] * df_length['count']).sum() / df_length['count'].sum()
            max_length = df_length['longitud_optima'].max()
            st.metric("Longitud Promedio", f"{avg_length:.2f}")
            st.metric("Longitud Máxima", f"{max_length}")
    
    with tab4:
        with st.spinner('Generando visualización...'):
            df_heatmap = query_heatmap_data(selected_year, selected_country, selected_industry)
        st.plotly_chart(plot_dependency_heatmap(df_heatmap), use_container_width=True)
    
    with tab5:
        st.markdown("### 🔎 Análisis Bilateral de Dependencia")
        st.markdown("Analiza la evolución temporal de la dependencia entre dos países específicos en una industria.")
        
        # Filtros específicos para esta pestaña
        col1, col2, col3 = st.columns(3)
        
        with col1:
            bilateral_dependent = st.selectbox(
                "País Dependiente (Importador)",
                countries,
                key="bilateral_dependent"
            )
        
        with col2:
            bilateral_supplier = st.selectbox(
                "País Proveedor (Exportador)",
                countries,
                key="bilateral_supplier"
            )
        
        with col3:
            bilateral_industry = st.selectbox(
                "Industria",
                industries,
                key="bilateral_industry"
            )
        
        # Validar que no sean el mismo país
        if bilateral_dependent == bilateral_supplier:
            st.warning("⚠️ Por favor, selecciona países diferentes para el análisis bilateral.")
        else:
            # Mostrar relación con banderas
            st.markdown(f"### {get_flag_html(bilateral_dependent, 32)} {bilateral_dependent} ← {get_flag_html(bilateral_supplier, 32)} {bilateral_supplier}", unsafe_allow_html=True)
            st.markdown(f"**Industria:** {bilateral_industry}")
            st.markdown("---")
            
            # Cargar y mostrar gráfico
            with st.spinner('Generando visualización...'):
                df_bilateral = query_bilateral_evolution(
                    bilateral_dependent,
                    bilateral_supplier,
                    bilateral_industry
                )
            
            if not df_bilateral.empty:
                st.plotly_chart(
                    plot_bilateral_stacked_bars(
                        df_bilateral,
                        bilateral_dependent,
                        bilateral_supplier,
                        bilateral_industry
                    ),
                    use_container_width=True
                )
                
                # Estadísticas adicionales
                st.markdown("#### 📊 Estadísticas del Período")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Dependencia Total Promedio",
                        f"{df_bilateral['dependency_value'].mean():.3f}"
                    )
                
                with col2:
                    st.metric(
                        "DD Promedio",
                        f"{df_bilateral['direct_dependency'].mean():.3f}"
                    )
                
                with col3:
                    st.metric(
                        "DI Promedio",
                        f"{df_bilateral['indirect_dependency'].mean():.3f}"
                    )
                
                with col4:
                    ratio_dd = (df_bilateral['direct_dependency'].mean() / 
                               df_bilateral['dependency_value'].mean() * 100)
                    st.metric(
                        "% DD sobre Total",
                        f"{ratio_dd:.1f}%"
                    )
                
                # Mostrar tabla de datos
                with st.expander("📊 Ver datos detallados"):
                    st.dataframe(
                        df_bilateral[['year', 'dependency_value', 'direct_dependency', 
                                     'indirect_dependency', 'trade_value']].round(4),
                        use_container_width=True
                    )
            else:
                st.warning("⚠️ No hay datos disponibles para esta combinación de país dependiente, país proveedor e industria.")
    
    with tab6:
        st.markdown(f"### Ficha de País")
        st.markdown("Analiza las principales dependencias de un país como importador.")
        
        # Selector de país
        col1, col2 = st.columns([2, 1])
        
        with col1:
            profile_country = st.selectbox(
                "Selecciona el país a analizar",
                countries,
                key="profile_country"
            )
        
        with col2:
            top_n = st.slider(
                "Número de dependencias",
                min_value=10,
                max_value=50,
                value=30,
                step=5
            )
        
        # Cargar datos
        with st.spinner('Cargando perfil del país...'):
            df_profile = query_country_profile(profile_country, top_n)
        
        if not df_profile.empty:
            # Header con bandera
            st.markdown(f"{get_flag_html(profile_country, 40)} **{profile_country}**", unsafe_allow_html=True)
            st.markdown(f"**Top {top_n} Dependencias Críticas como Importador**")
            st.markdown("---")
            
            # KPIs del país
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Dependencias Analizadas",
                    len(df_profile)
                )
            
            with col2:
                st.metric(
                    "Dependencia Promedio",
                    f"{df_profile['avg_dependency'].mean():.3f}"
                )
            
            with col3:
                critical_deps = len(df_profile[df_profile['avg_dependency'] > 0.8])
                st.metric(
                    "Dependencias Críticas (>0.8)",
                    critical_deps
                )
            
            with col4:
                unique_suppliers = df_profile['supplier_country'].nunique()
                st.metric(
                    "Países Proveedores",
                    unique_suppliers
                )
            
            st.markdown("---")
            
            # Tabla con banderas
            st.markdown("### 📊 Top Dependencias")
            
            # Crear columnas con HTML personalizado para cada fila
            for idx, row in df_profile.head(top_n).iterrows():
                col1, col2, col3, col4, col5, col6 = st.columns([2, 3, 1, 1, 1, 1])
                
                with col1:
                    st.markdown(f"{get_flag_html(row['supplier_country'], 24)} {row['supplier_country']}", unsafe_allow_html=True)
                with col2:
                    st.text(row['industry'][:40] + '...' if len(row['industry']) > 40 else row['industry'])
                with col3:
                    st.metric("", f"{row['avg_dependency']:.3f}", label_visibility="collapsed")
                with col4:
                    st.metric("", f"{row['avg_direct']:.3f}", label_visibility="collapsed")
                with col5:
                    st.metric("", f"{row['avg_indirect']:.3f}", label_visibility="collapsed")
                with col6:
                    st.text(f"{row['total_trade']:,.0f}")
            
            # Top 10 proveedores (agrupados)
            st.markdown("### 🌟 Top Proveedores")
            top_suppliers = df_profile.groupby('supplier_country').agg({
                'avg_dependency': 'mean',
                'total_trade': 'sum'
            }).sort_values('avg_dependency', ascending=False).head(10)
            
            # Mostrar con banderas HTML
            st.markdown("#### Países con Mayor Dependencia Promedio")
            for idx, (country, data) in enumerate(top_suppliers.iterrows(), 1):
                col1, col2, col3 = st.columns([1, 5, 2])
                with col1:
                    st.markdown(f"**#{idx}**")
                with col2:
                    st.markdown(f"{get_flag_html(country, 28)} **{country}**", unsafe_allow_html=True)
                with col3:
                    st.metric("", f"{data['avg_dependency']:.3f}", label_visibility="collapsed")
            
            # Gráfico de top proveedores con banderas
            fig = go.Figure()
            
            # Labels sin banderas (se mostrarán con HTML arriba)
            supplier_labels = [c for c in top_suppliers.index]
            
            fig.add_trace(go.Bar(
                y=supplier_labels,
                x=top_suppliers['avg_dependency'],
                orientation='h',
                marker_color=ELCANO_COLORS['primary'],
                text=top_suppliers['avg_dependency'].round(3),
                textposition='auto'
            ))
            
            fig.update_layout(
                title=f"Top 10 Países Proveedores de {profile_country}",
                xaxis_title="Dependencia Promedio",
                yaxis_title="",
                plot_bgcolor='white',
                height=400,
                font=dict(family='Roboto', size=13),
                title_font_size=18,
                xaxis_title_font_size=14
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning(f"⚠️ No hay datos disponibles para {profile_country} como país importador.")
    
    # Exportar datos
    st.markdown("---")
    st.markdown("### 📥 Exportar Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👁️ Ver muestra de datos (100 filas)"):
            sample = query_filtered_sample(selected_year, selected_country, selected_industry, limit=100)
            st.dataframe(sample, use_container_width=True, height=400)
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p><strong>Real Instituto Elcano</strong> de Estudios Internacionales y Estratégicos</p>
        <p><a href="https://www.realinstitutoelcano.org" style="color: #bb2521;">www.realinstitutoelcano.org</a></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
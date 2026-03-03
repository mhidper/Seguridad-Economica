import pandas as pd
import json
from pathlib import Path
import base64

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR.parent / "data" / "processed" / "historico"

# 1. Definir lista de países "Top" (Económicamente relevantes + España)
top_countries = ['ESP', 'USA', 'CHN', 'DEU', 'FRA', 'GBR', 'JPN', 'KOR', 'IND', 'BRA', 
                 'RUS', 'ITA', 'CAN', 'AUS', 'MEX', 'TUR', 'NLD', 'SAU', 'CHE', 'BEL', 
                 'SWE', 'POL', 'ARG', 'PRT', 'MAR', 'DZA', 'VNM', 'IDN', 'ZAF', 'IRL']

print(f"[*] Creando base de datos de juguete con {len(top_countries)} países...")

latest_year = 2022
available_years = sorted([int(f.stem.split('_')[1]) for f in DATA_PATH.glob("profiles_*.parquet")])

# A. Datos Históricos (Evolution)
print("[*] Generando históricos...")
all_profiles = []
all_critical = []
for year in available_years:
    try:
        df_p = pd.read_parquet(DATA_PATH / f"profiles_{year}.parquet")
        df_p = df_p[df_p['country'].isin(top_countries)]
        all_profiles.append(df_p[['country', 'year', 'vulnerability', 'importance', 'global_rank']])
        
        f_crit = DATA_PATH / f"critical_{year}.parquet"
        if f_crit.exists():
            df_c = pd.read_parquet(f_crit)
            count = len(df_c[df_c['dependencia_total'] >= 0.7])
            all_critical.append({'year': year, 'count': count})
    except Exception as e:
        print(f"Error en histórico {year}: {e}")

# B. Datos del año actual (2022)
print(f"[*] Procesando año detalle: {latest_year}...")
df_profiles = pd.read_parquet(DATA_PATH / f"profiles_{latest_year}.parquet")
df_profiles = df_profiles[df_profiles['country'].isin(top_countries)]

df_hubs = pd.read_parquet(DATA_PATH / f"hubs_{latest_year}.parquet")
df_hubs = df_hubs[df_hubs['country'].isin(top_countries)].head(20)

# Dependencias (Industrias críticas por país)
df_deps = pd.read_parquet(DATA_PATH / f"dependencies_{latest_year}.parquet")
df_deps = df_deps[df_deps['dependent_country'].isin(top_countries)]
df_deps = df_deps.sort_values('dependency_value', ascending=False).groupby('dependent_country').head(10)

# Bilateral (Relaciones clave entre países)
df_bilat = pd.read_parquet(DATA_PATH / f"bilateral_{latest_year}.parquet")
df_bilat = df_bilat[df_bilat['importer'].isin(top_countries) & df_bilat['exporter'].isin(top_countries)]

# C. Explorer (Sectorial) - Reducción drástica para el "juguete"
print("[*] Procesando explorador sectorial...")
f_exp = DATA_PATH / f"explorer_{latest_year}.parquet"
if f_exp.exists():
    df_exp = pd.read_parquet(f_exp)
    # Solo España como importador para que el juguete sea ligero, o top_countries filtrado
    df_exp = df_exp[df_exp['importer'].isin(top_countries) & df_exp['exporter'].isin(top_countries)]
    df_exp = df_exp.sort_values('dep_total', ascending=False).groupby(['importer', 'industry']).head(3)
    
    indexed_explorer = {}
    for imp, group in df_exp.groupby('importer'):
        indexed_explorer[imp] = {}
        for ind, sub in group.groupby('industry'):
            indexed_explorer[imp][ind] = sub.to_dict(orient='records')
else:
    indexed_explorer = {}

# D. Industrias (Extraídas directamente del explorador para asegurar coincidencia)
if f_exp.exists():
    # Usamos el DataFrame original antes de filtrar para tener todos los nombres posibles
    df_exp_full = pd.read_parquet(f_exp)
    industries_list = sorted([str(n) for n in df_exp_full['industry'].unique() if n])
    industries = [{'industry_name': n} for n in industries_list]
    print(f"[*] Detectadas {len(industries)} industrias únicas.")
else:
    industries = []

# ENSAMBLAJE FINAL
toy_data = {
    'latest_year': latest_year,
    'available_years': available_years,
    'evolution': pd.concat(all_profiles).to_dict(orient='records') if all_profiles else [],
    'critical_evolution': all_critical,
    'industries': industries,
    'profiles': df_profiles.to_dict(orient='records'),
    'hubs': df_hubs.to_dict(orient='records'),
    'dependencies': df_deps.to_dict(orient='records'),
    'bilateral': df_bilat.to_dict(orient='records'),
    'explorer_indexed': indexed_explorer
}

# Guardar
with open(BASE_DIR / 'data_toy.json', 'w', encoding='utf-8') as f:
    json.dump(toy_data, f, ensure_ascii=False, separators=(',', ':'))

# Generar index.html
print("[*] Generando index.html...")
with open(BASE_DIR / 'template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Reemplazar Logo si existe
logo_path = BASE_DIR / "logo_elcano.png"
if logo_path.exists():
    logo_b64 = base64.b64encode(open(logo_path, 'rb').read()).decode()
    html = html.replace('__LOGO_BASE64__', f'data:image/png;base64,{logo_b64}')

with open(BASE_DIR / 'index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"[OK] Archivo 'data_toy.json' creado ({Path(BASE_DIR / 'data_toy.json').stat().st_size / 1024 / 1024:.2f} MB)")
print(f"[OK] index.html generado con éxito.")

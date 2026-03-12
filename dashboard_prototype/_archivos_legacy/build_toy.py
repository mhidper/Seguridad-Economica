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

# ENSAMBLAJE FINAL Y GENERACIÓN POR AÑOS
# D. Industrias (Extraídas directamente del explorador más reciente para asegurar coincidencia global)
f_exp_latest = DATA_PATH / f"explorer_{latest_year}.parquet"
if f_exp_latest.exists():
    df_exp_full = pd.read_parquet(f_exp_latest)
    industries_list = sorted([str(n) for n in df_exp_full['industry'].unique() if n])
    industries = [{'industry_name': n} for n in industries_list]
    print(f"[*] Detectadas {len(industries)} industrias únicas.")
else:
    industries = []

all_evolution_data = pd.concat(all_profiles).to_dict(orient='records') if all_profiles else []

for year in available_years:
    print(f"[*] Generando base de datos Lite para el año {year}...")
    try:
        # Cargar datos específicos para este año
        df_p_year = pd.read_parquet(DATA_PATH / f"profiles_{year}.parquet")
        df_p_year = df_p_year[df_p_year['country'].isin(top_countries)]
        
        df_h_year = pd.read_parquet(DATA_PATH / f"hubs_{year}.parquet")
        df_h_year = df_h_year[df_h_year['country'].isin(top_countries)].head(20)
        
        df_d_year = pd.read_parquet(DATA_PATH / f"dependencies_{year}.parquet")
        df_d_year = df_d_year[df_d_year['dependent_country'].isin(top_countries)]
        df_d_year = df_d_year.sort_values('dependency_value', ascending=False).groupby('dependent_country').head(10)
        
        df_b_year = pd.read_parquet(DATA_PATH / f"bilateral_{year}.parquet")
        df_b_year = df_b_year[df_b_year['importer'].isin(top_countries) & df_b_year['exporter'].isin(top_countries)]
        
        # Explorer (Sectorial) del año
        f_exp_year = DATA_PATH / f"explorer_{year}.parquet"
        indexed_exp_year = {}
        if f_exp_year.exists():
            df_e_y = pd.read_parquet(f_exp_year)
            df_e_y = df_e_y[df_e_y['importer'].isin(top_countries) & df_e_y['exporter'].isin(top_countries)]
            df_e_y = df_e_y.sort_values('dep_total', ascending=False).groupby(['importer', 'industry']).head(3)
            for imp, group in df_e_y.groupby('importer'):
                indexed_exp_year[imp] = {ind: sub.to_dict(orient='records') for ind, sub in group.groupby('industry')}
        
        toy_data = {
            'target_year': year,
            'latest_year': latest_year,
            'available_years': available_years,
            'evolution': all_evolution_data,
            'critical_evolution': all_critical,
            'industries': industries,
            'profiles': df_p_year.to_dict(orient='records'),
            'hubs': df_h_year.to_dict(orient='records'),
            'dependencies': df_d_year.to_dict(orient='records'),
            'bilateral': df_b_year.to_dict(orient='records'),
            'explorer_indexed': indexed_exp_year
        }
        
        # Guardar archivo específico (ej. data_toy_2022.json)
        with open(BASE_DIR / f'data_toy_{year}.json', 'w', encoding='utf-8') as f:
            json.dump(toy_data, f, ensure_ascii=False, separators=(',', ':'))
        
        # Si es el año más reciente, también lo guardamos como data_toy.json por compatibilidad
        if year == latest_year:
            with open(BASE_DIR / 'data_toy.json', 'w', encoding='utf-8') as f:
                json.dump(toy_data, f, ensure_ascii=False, separators=(',', ':'))
                
    except Exception as e:
        print(f"Error generando datos para {year}: {e}")

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

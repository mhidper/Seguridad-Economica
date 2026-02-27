import base64
import pandas as pd
import json
from pathlib import Path

# Configuración de rutas
BASE_DIR = Path(__file__).parent
DATA_DIST = BASE_DIR / "data_dist"
HIST_PATH = BASE_DIR.parent / "data" / "processed" / "historico"

# 1. Logo as base64
logo_path = BASE_DIR / "logo_elcano.png"
if logo_path.exists():
    with open(logo_path, 'rb') as f:
        logo_b64 = base64.b64encode(f.read()).decode()
else:
    logo_b64 = ""

# Detectar años disponibles
available_years = sorted([int(f.stem.split('_')[1]) for f in HIST_PATH.glob("profiles_*.parquet")])
if not available_years:
    print("⚠️ No hay datos en historico/ todavía.")
    exit()

latest_year = available_years[-1]

# 2. Generar el ARCHIVO META (Series temporales ligeras)
print("[*] Generando meta.json (series temporales)...")
meta = {
    'latest_year': latest_year,
    'available_years': available_years
}

all_profiles_list = []
all_critical_list = []

for year in available_years:
    # Perfiles históricos (Vulnerabilidad e Importancia)
    df_p = pd.read_parquet(HIST_PATH / f"profiles_{year}.parquet")
    all_profiles_list.append(df_p[['country', 'year', 'vulnerability', 'importance', 'global_rank']])
    
    # Evolución crítica global
    df_c = pd.read_parquet(HIST_PATH / f"critical_{year}.parquet")
    df_c_filtered = df_c[df_c['dependencia_total'] >= 0.7]
    all_critical_list.append(df_c_filtered[['year', 'dependencia_total']])

meta['evolution'] = pd.concat(all_profiles_list).to_dict(orient='records')
df_glob_all = pd.concat(all_critical_list)
risk_evol = df_glob_all.groupby('year').size().reset_index(name='count')
meta['critical_evolution'] = risk_evol.to_dict(orient='records')

# Catálogo de industrias (estático para todos los años)
ind_path = BASE_DIR.parent / 'data/processed/dependencias_consolidadas/industrias_id_nombre.parquet'
if ind_path.exists():
    df_ind = pd.read_parquet(ind_path)
    df_ind['industry_id'] = df_ind['industry_id'].astype(str)
    meta['industries'] = df_ind.to_dict(orient='records')
else:
    meta['industries'] = []

with open(DATA_DIST / 'meta.json', 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False)

# 3. Generar un ARCHIVO POR AÑO (Detalle pesado)
for year in available_years:
    print(f"[*] Generando detalle para el año {year}...")
    year_data = {}
    
    # Perfiles del año
    df_p = pd.read_parquet(HIST_PATH / f"profiles_{year}.parquet")
    p_cols = ['country', 'vulnerability', 'importance', 'global_rank']
    if 'indirect_share' in df_p.columns: p_cols.append('indirect_share')
    if 'num_suppliers_effective' in df_p.columns: p_cols.append('num_suppliers_effective')
    year_data['profiles'] = df_p[p_cols].to_dict(orient='records')
    
    # Hubs
    df_h = pd.read_parquet(HIST_PATH / f"hubs_{year}.parquet")
    year_data['hubs'] = df_h.head(100).to_dict(orient='records')
    
    # Dependencias Top
    df_d = pd.read_parquet(HIST_PATH / f"dependencies_{year}.parquet")
    df_d = df_d.sort_values('dependency_value', ascending=False).groupby('dependent_country').head(10)
    year_data['dependencies'] = df_d.to_dict(orient='records')
    
    # Bilateral
    df_b = pd.read_parquet(HIST_PATH / f"bilateral_{year}.parquet")
    df_b = df_b[df_b['criticidad'] > 0]
    year_data['bilateral'] = df_b.to_dict(orient='records')
    
    # Explorer Indexed
    f_exp = HIST_PATH / f"explorer_{year}.parquet"
    if f_exp.exists():
        df_e = pd.read_parquet(f_exp)
        esp_mask = (df_e['importer'] == 'ESP') & (df_e['dep_total'] >= 0.01)
        world_mask = (df_e['importer'] != 'ESP') & (df_e['dep_total'] >= 0.05)
        df_e = df_e[esp_mask | world_mask]
        df_e = df_e.sort_values('dep_total', ascending=False).groupby(['importer', 'industry']).head(10)
        
        indexed = {}
        for imp, group in df_e.groupby('importer'):
            indexed[imp] = {}
            for ind, sub in group.groupby('industry'):
                indexed[imp][ind] = sub.to_dict(orient='records')
        year_data['explorer_indexed'] = indexed
    
    with open(DATA_DIST / f'year_{year}.json', 'w', encoding='utf-8') as f:
        json.dump(year_data, f, ensure_ascii=False)

# 4. Generar el index.html final (Lite)
print("[*] Generando index.html (Lite)...")
with open(BASE_DIR / 'template.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('__LOGO_BASE64__', f'data:image/png;base64,{logo_b64}')
# Eliminamos la inyección masiva de datos originales
html = html.replace('const FULL_DATA = __DATA_JSON__;', 'const FULL_DATA = null; // Cargado dinámicamente')

with open(BASE_DIR / 'index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\n[OK] Dashboard fragmentado generado con éxito en dashboard_prototype/data_dist/')
print(f'   - Años procesados: {available_years}')

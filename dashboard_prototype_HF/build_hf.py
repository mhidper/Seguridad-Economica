import base64
import pandas as pd
import json
from pathlib import Path

# 1. Logo as base64
logo_path = Path('logo_elcano.png')
if logo_path.exists():
    with open(logo_path, 'rb') as f:
        logo_b64 = base64.b64encode(f.read()).decode()
else:
    logo_b64 = ""

# 2. Data as JSON
datasets = {}
hist_path = Path('../data/processed/historico')

# Detectar años disponibles
available_years = sorted([int(f.stem.split('_')[1]) for f in hist_path.glob("profiles_*.parquet")])
if not available_years:
    print("⚠️ No hay datos en historico/ todavía.")
    exit()

latest_year = available_years[-1]

datasets['meta'] = {
    'latest_year': latest_year,
    'available_years': available_years
}

# Cargar datos por año
multi_year = {}
all_profiles_list = []
all_critical_list = []

for year in available_years:
    print(f"[*] Optimizando datos de {year}...")
    year_data = {}
    
    # PROFILES: Solo columnas necesarias
    df_p = pd.read_parquet(hist_path / f"profiles_{year}.parquet")
    p_cols = ['country', 'vulnerability', 'importance', 'global_rank']
    if 'indirect_share' in df_p.columns: p_cols.append('indirect_share')
    if 'num_suppliers_effective' in df_p.columns: p_cols.append('num_suppliers_effective')
    
    year_data['profiles'] = df_p[p_cols].to_dict(orient='records')
    all_profiles_list.append(df_p[['country', 'year', 'vulnerability', 'importance']])
    
    # HUBS: Solo top 100
    df_h = pd.read_parquet(hist_path / f"hubs_{year}.parquet")
    year_data['hubs'] = df_h.head(100).to_dict(orient='records')
    
    # CRITICAL: Para el grafico de evolucion global
    df_c = pd.read_parquet(hist_path / f"critical_{year}.parquet")
    df_c_filtered = df_c[df_c['dependencia_total'] >= 0.7]
    all_critical_list.append(df_c_filtered[['year', 'dependencia_total']])
    
    # DEPENDENCIES: Solo top 10 por país
    df_d = pd.read_parquet(hist_path / f"dependencies_{year}.parquet")
    df_d = df_d.sort_values('dependency_value', ascending=False).groupby('dependent_country').head(10)
    year_data['dependencies'] = df_d.to_dict(orient='records')
    
    # BILATERAL
    df_b = pd.read_parquet(hist_path / f"bilateral_{year}.parquet")
    df_b = df_b[df_b['criticidad'] > 0]
    year_data['bilateral'] = df_b.to_dict(orient='records')
    
    # EXPLORER
    f_exp = hist_path / f"explorer_{year}.parquet"
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
        
    multi_year[year] = year_data

datasets['multi_year'] = multi_year

# 3. Datos consolidados para graficos de evolucion
if all_profiles_list:
    datasets['evolution'] = pd.concat(all_profiles_list).to_dict(orient='records')

if all_critical_list:
    df_glob_all = pd.concat(all_critical_list)
    risk_evol = df_glob_all.groupby('year').size().reset_index(name='count')
    datasets['critical_evolution'] = risk_evol.to_dict(orient='records')

# 4. Catálogos
ind_path = Path('../data/processed/dependencias_consolidadas/industrias_id_nombre.parquet')
if ind_path.exists():
    df_ind = pd.read_parquet(ind_path)
    df_ind['industry_id'] = df_ind['industry_id'].astype(str)
    datasets['industries'] = df_ind.to_dict(orient='records')
else:
    datasets['industries'] = []

# 5. Guardar el JSON de datos
print("[*] Guardando data.json...")
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(datasets, f, ensure_ascii=False)

# 6. Generar el index.html estático (sin datos incrustados)
print("[*] Generando index.html...")
with open('template_hf.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('__LOGO_BASE64__', f'data:image/png;base64,{logo_b64}')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\n[OK] Dashboard HF generado con éxito!')
print(f'   - Los datos están externalizados en data.json')

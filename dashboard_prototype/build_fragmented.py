import base64
import pandas as pd
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIST = BASE_DIR / "data_dist"
HIST_PATH = BASE_DIR.parent / "data" / "processed" / "historico"

# 1. Logo as base64
logo_path = BASE_DIR / "logo_elcano.png"
logo_b64 = base64.b64encode(open(logo_path, 'rb').read()).decode() if logo_path.exists() else ""

# Detectar años
available_years = sorted([int(f.stem.split('_')[1]) for f in HIST_PATH.glob("profiles_*.parquet")])
latest_year = available_years[-1]

# 2. META.JSON (Compacto)
print("[*] Generando meta.json...")
all_profiles = []
all_critical = []
for year in available_years:
    df_p = pd.read_parquet(HIST_PATH / f"profiles_{year}.parquet")
    all_profiles.append(df_p[['country', 'year', 'vulnerability', 'importance', 'global_rank']])
    df_c = pd.read_parquet(HIST_PATH / f"critical_{year}.parquet")
    all_critical.append(df_c[df_c['dependencia_total'] >= 0.7][['year', 'dependencia_total']])

meta = {
    'latest_year': latest_year,
    'available_years': available_years,
    'evolution': pd.concat(all_profiles).values.tolist(), # List of lists
    'evolution_cols': ['country', 'year', 'vulnerability', 'importance', 'global_rank'],
    'critical_evolution': pd.concat(all_critical).groupby('year').size().reset_index(name='count').values.tolist()
}

ind_path = BASE_DIR.parent / 'data/processed/dependencias_consolidadas/industrias_id_nombre.parquet'
meta['industries'] = pd.read_parquet(ind_path).values.tolist() if ind_path.exists() else []

with open(DATA_DIST / 'meta.json', 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False)

# 3. YEAR_XXXX.JSON (Ultra Compacto)
def to_compact(df, cols):
    return {'c': cols, 'd': df[cols].values.tolist()}

for year in available_years:
    print(f"[*] Optimizando {year}...")
    # Profiles
    df_p = pd.read_parquet(HIST_PATH / f"profiles_{year}.parquet")
    p_cols = ['country', 'vulnerability', 'importance', 'global_rank']
    if 'indirect_share' in df_p.columns: p_cols.append('indirect_share')
    if 'num_suppliers_effective' in df_p.columns: p_cols.append('num_suppliers_effective')
    
    # Hubs
    df_h = pd.read_parquet(HIST_PATH / f"hubs_{year}.parquet").head(100)
    
    # Dependencies
    df_d = pd.read_parquet(HIST_PATH / f"dependencies_{year}.parquet")
    df_d = df_d.sort_values('dependency_value', ascending=False).groupby('dependent_country').head(10)
    
    # Bilateral
    df_b = pd.read_parquet(HIST_PATH / f"bilateral_{year}.parquet")
    df_b = df_b[df_b['criticidad'] > 0]

    year_data = {
        'profiles': to_compact(df_p, p_cols),
        'hubs': to_compact(df_h, df_h.columns.tolist()),
        'dependencies': to_compact(df_d, df_d.columns.tolist()),
        'bilateral': to_compact(df_b, df_b.columns.tolist())
    }

    # Explorer (este es el más pesado, lo filtramos agresivamente)
    f_exp = HIST_PATH / f"explorer_{year}.parquet"
    if f_exp.exists():
        df_e = pd.read_parquet(f_exp)
        df_e = df_e[(df_e['importer'] == 'ESP') | (df_e['dep_total'] >= 0.1)]
        df_e = df_e.sort_values('dep_total', ascending=False).groupby(['importer', 'industry']).head(5)
        
        indexed = {}
        for imp, group in df_e.groupby('importer'):
            indexed[imp] = {}
            for ind, sub in group.groupby('industry'):
                indexed[imp][ind] = sub.values.tolist()
        year_data['explorer_indexed'] = indexed
        year_data['explorer_cols'] = df_e.columns.tolist()

    with open(DATA_DIST / f'year_{year}.json', 'w', encoding='utf-8') as f:
        json.dump(year_data, f, ensure_ascii=False, separators=(',', ':')) # Sin espacios

print("[OK] Dashboard compactado.")

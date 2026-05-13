import base64
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIST = (BASE_DIR / "data_dist").resolve()
HIST_PATH = (BASE_DIR.parent / "data" / "processed" / "historico").resolve()

# Asegurar DATA_DIST existe
DATA_DIST.mkdir(exist_ok=True)

# 1. Logo as base64
logo_path = BASE_DIR / "logo_elcano.png"
logo_b64 = base64.b64encode(open(logo_path, 'rb').read()).decode() if logo_path.exists() else ""

# Detectar años
available_years = sorted([int(f.stem.split('_')[1]) for f in HIST_PATH.glob("profiles_*.parquet")])
latest_year = available_years[-1]

# 2. Sector Mapping Logic
def get_sector(instr):
    instr = str(instr).lower()
    # Keywords detection (Agri)
    if any(k in instr for k in ['wheat', 'maize', 'crops', 'cattle', 'livestock', 'eggs', 'milk', 'agri', 'farm', 'forest', 'fish']):
        return 'Agri'
    # Keywords detection (MinEn)
    if any(k in instr for k in ['coal', 'oil', 'gas', 'mining', 'fuel', 'crude', 'energy', 'iron ore', 'copper ore', 'electricity']):
        return 'MinEn'
    # Fallback to ID-based
    try:
        iid = int(instr.split(' ')[0])
        if iid <= 10: return 'Agri'
        if iid <= 35: return 'MinEn'
        if iid <= 153: return 'Manuf'
        return 'Serv'
    except:
        if any(k in instr for k in ['service', 'repair', 'trade', 'transport', 'hotel', 'bank', 'insurance', 'public', 'social']):
            return 'Serv'
        return 'Manuf'

# 3. META.JSON (Compacto)
print("[*] Generando meta.json...")
all_profiles = []
all_critical = []
for year in available_years:
    df_p = pd.read_parquet(HIST_PATH / f"profiles_{year}.parquet")
    all_profiles.append(df_p[['country', 'year', 'vulnerability', 'importance', 'global_rank']])
    df_c = pd.read_parquet(HIST_PATH / f"critical_{year}.parquet")
    all_critical.append(df_c[df_c['dependencia_total'] >= 0.7][['year', 'dependencia_total']])

ind_path = BASE_DIR.parent / 'data/processed/dependencias_consolidadas/industrias_id_nombre.parquet'
meta = {
    'latest_year': latest_year,
    'available_years': available_years,
    'evolution': pd.concat(all_profiles).values.tolist(), 
    'evolution_cols': ['country', 'year', 'vulnerability', 'importance', 'global_rank'],
    'critical_evolution': pd.concat(all_critical).groupby('year').size().reset_index(name='count').values.tolist()
}

if ind_path.exists():
    meta['industries'] = pd.read_parquet(ind_path).values.tolist()

with open(DATA_DIST / 'meta.json', 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False)

# 4. YEAR_XXXX.JSON
all_years_data = {}
def to_compact(df, cols):
    return {'c': cols, 'd': df[cols].values.tolist()}

for year in available_years:
    print(f"[*] Procesando datos de {year}...")
    
    # load profiles
    df_p = pd.read_parquet(HIST_PATH / f"profiles_{year}.parquet")
    
    # Sectoral breakdown from explorer (it has direct/indirect split)
    f_exp = HIST_PATH / f"explorer_{year}.parquet"
    if f_exp.exists():
        df_e = pd.read_parquet(f_exp)
        
        # Load mapping
        if ind_path.exists():
            df_ind = pd.read_parquet(ind_path)
            name_to_id = dict(zip(df_ind['industry_descr'], df_ind['industry_id']))
            df_e['sector'] = df_e['industry'].map(name_to_id).apply(get_sector)
        else:
            df_e['sector'] = 'Manuf'
            
        # Group by importer and sector
        sect = df_e.groupby(['importer', 'sector']).agg({
            'dep_direct': 'mean', 'dep_indirect': 'mean'
        }).reset_index()
        
        pivot_d = sect.pivot(index='importer', columns='sector', values='dep_direct').fillna(0)
        pivot_i = sect.pivot(index='importer', columns='sector', values='dep_indirect').fillna(0)
        
        pivot_d.columns = [f's_{c.lower()}_d' for c in pivot_d.columns]
        pivot_i.columns = [f's_{c.lower()}_i' for c in pivot_i.columns]
        
        df_p = df_p.merge(pivot_d, left_on='country', right_index=True, how='left')
        df_p = df_p.merge(pivot_i, left_on='country', right_index=True, how='left').fillna(0)
    
    # NEW: Sectoral Hubs Calculation from Explorer
    print(f"[*] Calculando hubs sectoriales para {year}...")
    sec_hubs = {}
    if f_exp.exists():
        # Get industry-to-sector mapping if exists, else default to all manuf
        # Industry list from explorer must be mapped. 
        # Using the same mapping function as before.
        for sector in ['Agri', 'Manuf', 'Serv', 'MinEn']:
            df_sec = df_e[df_e['sector'] == sector]
            if not df_sec.empty:
                # Group by top_intermediary and sum path_strength as a proxy for hub importance
                h_scores = df_sec.groupby('top_intermediary')['path_strength'].sum().sort_values(ascending=False).head(30)
                # Normalize 0-1
                if not h_scores.empty:
                    m = h_scores.max()
                    sec_hubs[sector] = [[k, float(v/m)] for k, v in h_scores.items() if k]
    
    # 4. Sector aggregation for profiles (since they are missing in raw parquet)
    df_e['sector'] = df_e['industry'].apply(get_sector)
    for s_name in ['Agri', 'MinEn', 'Manuf', 'Serv']:
        sn = s_name.lower()
        # Use mean() instead of sum() to normalize the bars, so they are comparable [0, 1]
        s_means = df_e[df_e['sector'] == s_name].groupby('importer')[['dep_direct', 'dep_indirect']].mean()
        df_p[f's_{sn}_d'] = df_p['country'].map(s_means['dep_direct']).fillna(0)
        df_p[f's_{sn}_i'] = df_p['country'].map(s_means['dep_indirect']).fillna(0)

    p_cols = ['country', 'vulnerability', 'importance', 'global_rank']
    if 'indirect_share' in df_p.columns: p_cols.append('indirect_share')
    if 'num_suppliers_effective' in df_p.columns: p_cols.append('num_suppliers_effective')
    p_cols.extend([f's_{s.lower()}_{x}' for s in ['Agri', 'MinEn', 'Manuf', 'Serv'] for x in ['d', 'i']])

    # Hubs
    df_h = pd.read_parquet(HIST_PATH / f"hubs_{year}.parquet").head(100)
    
    # Full Dependencies (Top 30 industries per country for profile treemap)
    df_d = pd.read_parquet(HIST_PATH / f"dependencies_{year}.parquet")
    df_d = df_d.sort_values('dependency_value', ascending=False).groupby('dependent_country').head(30)
    
    # Bilateral (Direct critical)
    df_b = pd.read_parquet(HIST_PATH / f"bilateral_{year}.parquet")
    df_b = df_b[df_b['criticidad'] > 0]

    year_data = {
        'profiles': to_compact(df_p, p_cols),
        'hubs': to_compact(df_h, df_h.columns.tolist()),
        'sectoral_hubs': sec_hubs,
        'dependencies': to_compact(df_d, df_d.columns.tolist()),
        'bilateral': to_compact(df_b, df_b.columns.tolist())
    }

    # Explorer lite for search
    df_e_lite = df_e[(df_e['importer'] == 'ESP') | (df_e['dep_total'] >= 0.1)]
    df_e_lite = df_e_lite.sort_values('dep_total', ascending=False).groupby(['importer', 'industry']).head(5)
    indexed = {}
    for imp, group in df_e_lite.groupby('importer'):
        indexed[imp] = {}
        for ind, sub in group.groupby('industry'):
            indexed[imp][ind] = sub.values.tolist()
    year_data['explorer_indexed'] = indexed
    year_data['explorer_cols'] = df_e_lite.columns.tolist()
    
    all_years_data[year] = year_data

# Save all year fragments
for year, year_data in all_years_data.items():
    with open(DATA_DIST / f'year_{year}.json', 'w', encoding='utf-8') as f:
        json.dump(year_data, f, separators=(',', ':'))
        
# Generate History Fragment (2016-2022) for the evolution chart
print("[*] Generando history.json...")
history = {}
for year in available_years:
    df_e = pd.read_parquet(HIST_PATH / f"explorer_{year}.parquet").rename(columns={'importer':'country'})
    df_e['sector'] = df_e['industry'].apply(get_sector)
    
    # Aggregate risks
    total_risks = df_e.groupby('country')[['dep_direct', 'dep_indirect']].mean()
    sector_risks = df_e.groupby(['country', 'sector'])[['dep_direct', 'dep_indirect']].mean().unstack(fill_value=0)
    
    for iso3 in df_e['country'].unique():
        if iso3 not in history: history[iso3] = []
        
        t_d = float(total_risks.loc[iso3, 'dep_direct']) if iso3 in total_risks.index else 0
        t_i = float(total_risks.loc[iso3, 'dep_indirect']) if iso3 in total_risks.index else 0
        
        def get_s(sec, field):
            try: return float(sector_risks.loc[iso3, (field, sec)])
            except: return 0

        history[iso3].append({
            'y': int(year),
            't_d': t_d, 't_i': t_i,
            'a_d': get_s('Agri', 'dep_direct'), 'a_i': get_s('Agri', 'dep_indirect'),
            'e_d': get_s('MinEn', 'dep_direct'), 'e_i': get_s('MinEn', 'dep_indirect'),
            'm_d': get_s('Manuf', 'dep_direct'), 'm_i': get_s('Manuf', 'dep_indirect'),
            's_d': get_s('Serv', 'dep_direct'), 's_i': get_s('Serv', 'dep_indirect')
        })
with open(DATA_DIST / 'history.json', 'w', encoding='utf-8') as f:
    json.dump(history, f, separators=(',', ':'))

print(f"[OK] Dashboard {available_years[-1]} actualizado.")

# 5. Generar index.html
print("[*] Sincronizando template.html -> index.html...")
if (BASE_DIR / 'template.html').exists():
    with open(BASE_DIR / 'template.html', 'r', encoding='utf-8') as f:
        html = f.read()
    html = html.replace('__LOGO_BASE64__', f'data:image/png;base64,{logo_b64}')
    html = html.replace('const FULL_DATA = __DATA_JSON__;', 'const FULL_DATA = null;')
    with open(BASE_DIR / 'index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[OK] Dashboard {latest_year} actualizado.")
else:
    print("[!] No se encontró template.html")

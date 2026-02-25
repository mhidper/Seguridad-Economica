import base64
import pandas as pd
import json
from pathlib import Path

# 1. Logo as base64
with open('logo_elcano.png', 'rb') as f:
    logo_b64 = base64.b64encode(f.read()).decode()

# 2. Data as JSON
datasets = {}
hist_path = Path('../data/processed/historico')

# Cargar evolución histórica
all_profiles = []
all_hubs = []
all_critical = []

for f in sorted(hist_path.glob("profiles_*.parquet")):
    year = int(f.stem.split('_')[1])
    df = pd.read_parquet(f)
    all_profiles.append(df)

for f in sorted(hist_path.glob("hubs_*.parquet")):
    df = pd.read_parquet(f)
    all_hubs.append(df)

for f in sorted(hist_path.glob("critical_*.parquet")):
    df = pd.read_parquet(f)
    all_critical.append(df)

# Consolidar para el frontend
if all_profiles:
    latest_profiles = all_profiles[-1]
    datasets['profiles'] = latest_profiles.to_dict(orient='records')
    # Para el gráfico de evolución de cada país
    datasets['evolution'] = pd.concat(all_profiles).to_dict(orient='records')

if all_hubs:
    latest_hubs = all_hubs[-1]
    datasets['hubs'] = latest_hubs.to_dict(orient='records')

if all_critical:
    latest_critical = all_critical[-1]
    # Mostrar solo Top 50 en la tabla para rendimiento
    datasets['critical'] = latest_critical.sort_values('criticidad', ascending=False).head(50).to_dict(orient='records')
    
    # Serie histórica de riesgo global (conteo por año)
    df_glob = pd.concat(all_critical)
    risk_evol = df_glob.groupby('year').size().reset_index(name='count')
    datasets['critical_evolution'] = risk_evol.to_dict(orient='records')

# Últimos detalles específicos del año más reciente
latest_year_file = sorted(hist_path.glob("profiles_*.parquet"))[-1]
latest_year = int(latest_year_file.stem.split('_')[1])

df_deps = pd.read_parquet(hist_path / f"dependencies_{latest_year}.parquet")
datasets['dependencies'] = df_deps.to_dict(orient='records')

df_bilat = pd.read_parquet(hist_path / f"bilateral_{latest_year}.parquet")
datasets['bilateral'] = df_bilat.to_dict(orient='records')

# Nuevo: Explorador por industria
explorer_file = hist_path / f"explorer_{latest_year}.parquet"
if explorer_file.exists():
    df_exp = pd.read_parquet(explorer_file)
    datasets['explorer'] = df_exp.to_dict(orient='records')

# Datos adicionales (catálogos)
df_ind = pd.read_parquet('../data/processed/dependencias_consolidadas/industrias_id_nombre.parquet')
df_ind['industry_id'] = df_ind['industry_id'].astype(str)
datasets['industries'] = df_ind.to_dict(orient='records')

data_json = json.dumps(datasets, ensure_ascii=False)

# 3. Read template and inject
with open('template.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('__LOGO_BASE64__', f'data:image/png;base64,{logo_b64}')
html = html.replace('__DATA_JSON__', data_json)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Done! Logo: {len(logo_b64)} chars, Data: {len(data_json)} chars')

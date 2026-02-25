import base64
import pandas as pd
import json

# 1. Logo as base64
with open('logo_elcano.png', 'rb') as f:
    logo_b64 = base64.b64encode(f.read()).decode()

# 2. Data as JSON
datasets = {}

df = pd.read_parquet('../dashboard/data/country_profiles_lite.parquet')
datasets['profiles'] = df.to_dict(orient='records')

df = pd.read_parquet('../dashboard/data/global_hubs.parquet')
datasets['hubs'] = df.to_dict(orient='records')

df = pd.read_parquet('../data/processed/dependencias_consolidadas/relaciones_criticas.parquet')
datasets['critical'] = df.to_dict(orient='records')

df = pd.read_parquet('../dashboard/data/country_country_criticidad.parquet')
datasets['bilateral'] = df.to_dict(orient='records')

df = pd.read_parquet('../dashboard/data/country_industry_dependencies.parquet')
top_deps = df.sort_values('dependency_value', ascending=False).groupby('dependent_country').head(10)
datasets['dependencies'] = top_deps.to_dict(orient='records')

# 3. Evolution Data
df = pd.read_parquet('../notebooks/analysis/evolution_summary.parquet')
datasets['evolution'] = df.to_dict(orient='records')

df = pd.read_parquet('../notebooks/analysis/critical_evolution.parquet')
datasets['critical_evolution'] = df.to_dict(orient='records')

data_json = json.dumps(datasets, ensure_ascii=False)

# 3. Read template and inject
with open('template.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('__LOGO_BASE64__', f'data:image/png;base64,{logo_b64}')
html = html.replace('__DATA_JSON__', data_json)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Done! Logo: {len(logo_b64)} chars, Data: {len(data_json)} chars')

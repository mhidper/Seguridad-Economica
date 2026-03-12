import pandas as pd
import json

datasets = {}

# 1. Country profiles (236 countries)
df = pd.read_parquet('../dashboard/data/country_profiles_lite.parquet')
datasets['profiles'] = df.to_dict(orient='records')

# 2. Global hubs (top 30)
df = pd.read_parquet('../dashboard/data/global_hubs.parquet')
datasets['hubs'] = df.to_dict(orient='records')

# 3. Critical relations (top 50)
df = pd.read_parquet('../dashboard/data/critical_relations.parquet')
datasets['critical'] = df.to_dict(orient='records')

# 4. Country-country criticality (2327 pairs)
df = pd.read_parquet('../dashboard/data/country_country_criticidad.parquet')
datasets['bilateral'] = df.to_dict(orient='records')

# 5. Country-industry dependencies - top 10 per country
df = pd.read_parquet('../dashboard/data/country_industry_dependencies.parquet')
top_deps = df.sort_values('dependency_value', ascending=False).groupby('dependent_country').head(10)
datasets['dependencies'] = top_deps.to_dict(orient='records')

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(datasets, f, ensure_ascii=False)

for k, v in datasets.items():
    print(f'{k}: {len(v)} records')
print('Done!')

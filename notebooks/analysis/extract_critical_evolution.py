import pandas as pd
from pathlib import Path
import json

data_path = Path(r'c:\Users\Usuario\Documents\Github\Seguridad Economica\data\processed\dependencias_consolidadas')
years = sorted([int(f.name.replace('dependencias', '').replace('.csv.gz', '')) 
                for f in data_path.glob('dependencias20*.csv.gz') if 'borrar' not in f.name])

print(f"Aggregating critical relations for years: {years}")

crit_counts = []
for year in years:
    file_path = data_path / f"dependencias{year}.csv.gz"
    # A relation is "critical" if dependency_value > 0.7
    # Note: We don't have the "redundancia" (caminos_alternativos) in the CSV, 
    # so we'll use "High Dependency" as the metric for historical evolution.
    df = pd.read_csv(file_path, sep=';', usecols=['dependency_value'])
    count = (df['dependency_value'] >= 0.7).sum()
    crit_counts.append({'year': year, 'count': int(count)})

pd.DataFrame(crit_counts).to_parquet('critical_evolution.parquet', index=False)
print("Saved critical_evolution.parquet")

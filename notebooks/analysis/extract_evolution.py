import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

data_path = Path(r'c:\Users\Usuario\Documents\Github\Seguridad Economica\data\processed\dependencias_consolidadas')
years = sorted([int(f.name.replace('dependencias', '').replace('.csv.gz', '')) 
                for f in data_path.glob('dependencias20*.csv.gz') if 'borrar' not in f.name])

print(f"Detected years: {years}")

evolution = []

for year in years:
    print(f"Processing {year}...")
    file_path = data_path / f"dependencias{year}.csv.gz"
    # Load only necessary columns to save memory
    df = pd.read_csv(file_path, sep=';', usecols=['dependent_country', 'supplier_country', 'dependency_value', 'trade_value'])
    
    # Vulnerability (weighted mean of dependency when country is importer)
    vul = df.groupby('dependent_country').apply(
        lambda g: (g['dependency_value'] * g['trade_value']).sum() / g['trade_value'].sum() if g['trade_value'].sum() > 0 else 0
    ).rename('vulnerability')
    
    # Importance (weighted mean of dependency when country is exporter)
    imp = df.groupby('supplier_country').apply(
        lambda g: (g['dependency_value'] * g['trade_value']).sum() / g['trade_value'].sum() if g['trade_value'].sum() > 0 else 0
    ).rename('importance')
    
    year_data = pd.concat([vul, imp], axis=1)
    year_data['year'] = year
    evolution.append(year_data.reset_index().rename(columns={'index': 'country'}))

full_evolution = pd.concat(evolution)
full_evolution.to_parquet('evolution_summary.parquet', index=False)
print("Saved evolution_summary.parquet")

# Plot for ESP, USA, CHN
highlights = ['ESP', 'USA', 'CHN']
plt.figure(figsize=(10, 6))
for c in highlights:
    subset = full_evolution[full_evolution['country'] == c]
    plt.plot(subset['year'], subset['vulnerability'], label=f"{c} Vulnerability", marker='o')

plt.title("Evolution of Economic Vulnerability (ISC)")
plt.legend()
plt.grid(True)
plt.savefig('evolution_plot.png')
print("Saved evolution_plot.png")

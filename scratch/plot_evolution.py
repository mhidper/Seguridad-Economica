import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import seaborn as sns

years = [2016, 2017, 2018, 2019, 2020, 2021, 2022]
base_dir = r"C:\Users\Usuario\Documents\Github\Seguridad Economica\data\processed\historico"
out_path = r"C:\Users\Usuario\Documents\Github\Seguridad Economica\Informes, briefs o notas\informe UE\imagenes\evolucion_idee_ue.png"

eu27_iso3 = ['AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 
             'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 
             'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE']

eu27_agg_data = []
eu_members_stats = []

for year in years:
    # UE27 consolidado
    ue_file = os.path.join(base_dir, f"profiles_{year}_UE.parquet")
    if os.path.exists(ue_file):
        df_ue = pd.read_parquet(ue_file)
        val = df_ue[df_ue['country'] == 'EU27']['vulnerability'].values
        if len(val) > 0:
            eu27_agg_data.append({'Year': year, 'Vulnerability': val[0]})
            
    # Estados individuales
    global_file = os.path.join(base_dir, f"profiles_{year}.parquet")
    if os.path.exists(global_file):
        df_global = pd.read_parquet(global_file)
        members = df_global[df_global['country'].isin(eu27_iso3)]
        vals = members['vulnerability'].values
        if len(vals) > 0:
            eu_members_stats.append({
                'Year': year,
                'Mean': np.mean(vals),
                'P05': np.percentile(vals, 5),
                'P95': np.percentile(vals, 95)
            })

df_agg = pd.DataFrame(eu27_agg_data)
df_stats = pd.DataFrame(eu_members_stats)

plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(10, 6))

# Dibujar la media y el intervalo de los miembros
if not df_stats.empty:
    ax.plot(df_stats['Year'], df_stats['Mean'], color='#8ca2c4', linewidth=3, linestyle='--', label='Media (27 Estados)', zorder=1)
    ax.fill_between(df_stats['Year'], df_stats['P05'], df_stats['P95'], color='#8ca2c4', alpha=0.2, label='Intervalo 90% (27 Estados)', zorder=0)

# Dibujar la línea consolidada de la UE27
if not df_agg.empty:
    ax.plot(df_agg['Year'], df_agg['Vulnerability'], color='#0A3063', linewidth=4, marker='o', markersize=8, label='UE27 (Bloque Consolidado)', zorder=2)

ax.set_title("Evolución del IDEE: Estados Miembros vs UE27 Consolidado (2016-2022)", fontsize=14, pad=20, fontweight='bold')
ax.set_xlabel("Año", fontsize=12)
ax.set_ylabel("Índice de Dependencia Económica Elcano (IDEE)", fontsize=12)
ax.set_xticks(years)
ax.legend(loc='upper left', fontsize=11)

plt.tight_layout()
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"Gráfica guardada en {out_path}")

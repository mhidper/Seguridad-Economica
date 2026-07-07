import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import re

# Configuración de rutas
base_dir = r"C:\Users\Usuario\Documents\Github\Seguridad Economica"
img_dir = os.path.join(base_dir, "Informes, briefs o notas", "informe UE", "imagenes")
os.makedirs(img_dir, exist_ok=True)

# Estilo global de gráficos
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['figure.titlesize'] = 16

# Colores institucionales (Elcano)
c_navy = '#0A3063'
c_blue = '#1F77B4'
c_steel = '#8CA2C4'
c_light_steel = '#C6DBEF'
c_green = '#2E7D32'
c_red = '#B91C1C'

def clean_industry_name(name):
    if not isinstance(name, str):
        return name
    # Eliminar dígitos iniciales seguidos de uno o más espacios (ej: '167 Government...' -> 'Government...')
    return re.sub(r'^\d+\s+', '', name)

# ==========================================
# 1. GENERACIÓN DE FIGURA: top_5_dependencies_china_usa.png
# ==========================================
print("Generando Figura 1: Top 5 dependencias de China y USA...")
df_bilat = pd.read_csv(os.path.join(base_dir, "Informes, briefs o notas", "informe UE", "csvs", "eu27_bilateral_dependencies.csv"))
df_bilat['industry'] = df_bilat['industry'].apply(clean_industry_name)

df_chn = df_bilat[df_bilat['exporter'] == 'CHN'].sort_values('total_dep', ascending=False).head(5).copy()
df_usa = df_bilat[df_bilat['exporter'] == 'USA'].sort_values('total_dep', ascending=False).head(5).copy()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

y_chn = np.arange(len(df_chn))
ax1.barh(y_chn, df_chn['direct_dep'], color=c_navy, label='Directa')
ax1.barh(y_chn, df_chn['indirect_dep'], left=df_chn['direct_dep'], color=c_steel, label='Indirecta')
ax1.set_yticks(y_chn)
labels_chn = [i[:35] + '...' if len(i) > 35 else i for i in df_chn['industry']]
ax1.set_yticklabels(labels_chn)
ax1.invert_yaxis()
ax1.set_title("Top 5 Sectores con Mayor Dependencia de China", fontweight='bold', pad=15)
ax1.set_xlabel("Índice de Dependencia")
ax1.legend(loc='lower right')

y_usa = np.arange(len(df_usa))
ax2.barh(y_usa, df_usa['direct_dep'], color=c_navy, label='Directa')
ax2.barh(y_usa, df_usa['indirect_dep'], left=df_usa['direct_dep'], color=c_steel, label='Indirecta')
ax2.set_yticks(y_usa)
labels_usa = [i[:35] + '...' if len(i) > 35 else i for i in df_usa['industry']]
ax2.set_yticklabels(labels_usa)
ax2.invert_yaxis()
ax2.set_title("Top 5 Sectores con Mayor Dependencia de USA", fontweight='bold', pad=15)
ax2.set_xlabel("Índice de Dependencia")
ax2.legend(loc='lower right')

plt.tight_layout()
fig1_path = os.path.join(img_dir, "top_5_dependencies_china_usa.png")
plt.savefig(fig1_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Guardado en {fig1_path}")

# ==========================================
# 2. GENERACIÓN DE FIGURA: indirect_dependency_hubs.png
# ==========================================
print("Generando Figura 2: Hubs de dependencias indirectas...")
df_explorer = pd.read_parquet(os.path.join(base_dir, "data", "processed", "historico", "explorer_2022_UE.parquet"))
df_eu_ind = df_explorer[df_explorer['importer'] == 'EU27']
df_hubs = df_eu_ind.groupby('top_intermediary')['dep_indirect'].sum().sort_values(ascending=False).head(10).reset_index()

fig, ax = plt.subplots(figsize=(10, 5.5))
sns.barplot(x='dep_indirect', y='top_intermediary', data=df_hubs, color=c_navy, ax=ax)

for index, row in df_hubs.iterrows():
    ax.text(row['dep_indirect'] + 0.1, index, f"{row['dep_indirect']:.2f}", va='center', fontweight='bold')

ax.set_title("Principales Hubs Intermediarios de la Dependencia Indirecta de la UE27 (2022)", fontweight='bold', pad=15)
ax.set_xlabel("Suma Acumulada de Dependencia Indirecta")
ax.set_ylabel("País Intermediario (Hub)")
ax.set_xlim(0, df_hubs['dep_indirect'].max() + 2)

plt.tight_layout()
fig2_path = os.path.join(img_dir, "indirect_dependency_hubs.png")
plt.savefig(fig2_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Guardado en {fig2_path}")

# ==========================================
# 3. GENERACIÓN DE FIGURA: critical_bilateral_relations.png
# ==========================================
print("Generando Figura 3: Relaciones bilaterales críticas...")
df_crit = pd.read_csv(os.path.join(base_dir, "Informes, briefs o notas", "informe UE", "csvs", "top_15_bilateral_dependencies.csv")).head(10).copy()
df_crit['industry'] = df_crit['industry'].apply(clean_industry_name)

fig, ax = plt.subplots(figsize=(11, 6))

y_pos = np.arange(len(df_crit))
ax.barh(y_pos, df_crit['direct_dep'], color=c_navy, label='Directa')
ax.barh(y_pos, df_crit['indirect_dep'], left=df_crit['direct_dep'], color=c_steel, label='Indirecta')

labels_crit = [f"{row['industry'][:35]}... ({row['exporter']})" if len(row['industry']) > 35 else f"{row['industry']} ({row['exporter']})" 
               for _, row in df_crit.iterrows()]
ax.set_yticks(y_pos)
ax.set_yticklabels(labels_crit)
ax.invert_yaxis()

ax.set_title("Top 10 Relaciones Bilaterales de Dependencia Crítica de la UE27 (2022)", fontweight='bold', pad=15)
ax.set_xlabel("Índice de Dependencia (Directa + Indirecta)")
ax.legend(loc='lower right')

plt.tight_layout()
fig3_path = os.path.join(img_dir, "critical_bilateral_relations.png")
plt.savefig(fig3_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Guardado en {fig3_path}")

# ==========================================
# 4. GENERACIÓN DE FIGURA: global_intermediaries.png
# ==========================================
print("Generando Figura 4: Intermediarios globales...")
df_interm = pd.read_csv(os.path.join(base_dir, "Informes, briefs o notas", "informe UE", "csvs", "top_intermediaries_for_eu27.csv")).head(10)

fig, ax = plt.subplots(figsize=(10, 5.5))
sns.barplot(x='path_count', y='intermediary', data=df_interm, color=c_navy, ax=ax)

for index, row in df_interm.iterrows():
    ax.text(row['path_count'] + 20, index, f"{row['path_count']:,}", va='center', fontweight='bold')

ax.set_title("Intermediación en Cadenas de Suministro: Rutas Críticas por País (UE27, 2022)", fontweight='bold', pad=15)
ax.set_xlabel("Número de Rutas de Suministro Críticas Intermediadas")
ax.set_ylabel("País Intermediario")
ax.set_xlim(0, df_interm['path_count'].max() + 150)

plt.tight_layout()
fig4_path = os.path.join(img_dir, "global_intermediaries.png")
plt.savefig(fig4_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Guardado en {fig4_path}")

# ==========================================
# 5. GENERACIÓN DE FIGURA: ue_leadership_sectors.png
# ==========================================
print("Generando Figura 5: Sectores de liderazgo de la UE...")
df_dep_borrar = pd.read_csv(os.path.join(base_dir, "data", "processed", "dependencias_consolidadas", "dependencias2022_borrar.csv.gz"), sep=';', compression='gzip')
df_exports = df_dep_borrar[(df_dep_borrar['supplier_country']=='EU27') & (df_dep_borrar['dependent_country']!='EU27')]
df_lead_sectors = df_exports.groupby('industry')['trade_value'].sum().sort_values(ascending=False).head(10).reset_index()

df_lead_sectors['industry'] = df_lead_sectors['industry'].apply(clean_industry_name)
df_lead_sectors['trade_value_billions'] = df_lead_sectors['trade_value'] / 1000.0

fig, ax = plt.subplots(figsize=(11, 5.5))
sns.barplot(x='trade_value_billions', y='industry', data=df_lead_sectors, color=c_green, ax=ax)

for index, row in df_lead_sectors.iterrows():
    ax.text(row['trade_value_billions'] + 5, index, f"${row['trade_value_billions']:.1f} B", va='center', fontweight='bold')

# Primero, fijar los ticks
ax.set_yticks(range(len(df_lead_sectors)))
labels_lead = [i[:35] + '...' if len(i) > 35 else i for i in df_lead_sectors['industry']]
ax.set_yticklabels(labels_lead)

ax.set_title("Top 10 Sectores de Liderazgo Global de la UE27 por Exportaciones Extra-UE (2022)", fontweight='bold', pad=15)
ax.set_xlabel("Valor de las Exportaciones Extra-UE (Miles de Millones de USD)")
ax.set_ylabel("Sector / Industria")
ax.set_xlim(0, df_lead_sectors['trade_value_billions'].max() + 30)

plt.tight_layout()
fig5_path = os.path.join(img_dir, "ue_leadership_sectors.png")
plt.savefig(fig5_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Guardado en {fig5_path}")

print("¡Todos los gráficos generados con éxito!")

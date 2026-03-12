import pandas as pd
from pathlib import Path
import numpy as np

def analyze_electronics(year, base_path):
    # Load data
    cvg_path = base_path / "metodología" / "cvg-idc" / "output" / "idc_cvg" / f"cvg_decomp_{year}.parquet"
    alpha_path = base_path / "metodología" / "cvg-idc" / "output" / "alpha_matrix_2022.csv"
    explorer_path = base_path / "data" / "processed" / "historico" / f"explorer_{year}.parquet"
    mapping_path = base_path / "metodología" / "cvg-idc" / "output" / "sector_mapping.csv"
    
    cvg_df = pd.read_parquet(cvg_path)
    alpha_df = pd.read_csv(alpha_path, index_col=0)
    map_df = pd.read_csv(mapping_path, sep=';')
    
    # Analyze Spain - Electronics (C26)
    sector_code = 'C26'
    esp_c26 = cvg_df[(cvg_df['importer'] == 'ESP') & (cvg_df['icio_code'] == sector_code)].copy()
    
    # Calculate Hidden Risk percentage
    esp_c26['hidden_risk_pct'] = (esp_c26['hidden_risk'] / esp_c26['dep_cvg'].replace(0, np.nan)) * 100
    
    print(f"\n--- Análisis de Riesgo Oculto - {sector_code} (Electrónica) ---")
    
    # 1. Top 10 by CVG Dependency
    print("\n1. Top 10 Proveedores por Dependencia CVG Real (Directa + Upstream):")
    top_cvg = esp_c26.sort_values('dep_cvg', ascending=False).head(10)
    print(top_cvg[['exporter', 'dep_cvg', 'dep_direct', 'hidden_risk']].to_string(index=False))
    
    # 2. Top 10 by Hidden Risk
    print("\n2. Top 10 Proveedores por mayor Riesgo Oculto absoluto:")
    top_hidden = esp_c26.sort_values('hidden_risk', ascending=False).head(10)
    print(top_hidden[['exporter', 'hidden_risk', 'dep_direct', 'dep_cvg']].to_string(index=False))
    
    # 3. Decomposing China's Hidden Risk
    print("\n3. Descomponiendo el Riesgo Oculto de CHINA y USA en Electrónica:")
    # Get alpha recipe for C26
    recipe = alpha_df[sector_code].sort_values(ascending=False).head(10)
    print("\nReceta de C26 (Top 10 insumos):")
    for up_sector, weight in recipe.items():
        if weight >= 0.01:
            print(f"  - {up_sector}: {weight*100:.1f}%")
            
    # Load raw IDC to see DT in those upstream sectors for ESP-CHN
    def get_id(name):
        try:
            import re
            m = re.match(r"(\d+)", str(name))
            if m: return int(m.group(1))
            return None
        except: return None
        
    idc_df = pd.read_parquet(explorer_path)
    idc_df['industry_id'] = idc_df['industry'].apply(get_id)
    idc_df = idc_df.merge(map_df[['industry_id', 'icio_code']], on='industry_id', how='left')
    
    # Agg to ICIO
    agg_idc = idc_df.groupby(['importer', 'exporter', 'icio_code'])['dep_total'].mean().reset_index()
    
    for country in ['CHN', 'USA', 'DEU']:
        print(f"\n-- Riesgo oculto provocado por {country}: Componentes Upstream --")
        dt_country = agg_idc[(agg_idc['importer'] == 'ESP') & (agg_idc['exporter'] == country)]
        
        contributions = []
        for up_sector, weight in recipe.items():
            dt_up = dt_country[dt_country['icio_code'] == up_sector]['dep_total'].values
            if len(dt_up) > 0:
                contrib = dt_up[0] * weight
                contributions.append({'upstream_sector': up_sector, 'alpha': weight, 'dt_in_upstream': dt_up[0], 'contribution_cvg': contrib})
        
        contrib_df = pd.DataFrame(contributions).sort_values('contribution_cvg', ascending=False).head(5)
        print(contrib_df.to_string(index=False))

if __name__ == "__main__":
    base_path = Path(r"c:\Users\Usuario\Documents\Github\Seguridad Economica")
    analyze_electronics(2022, base_path)

import pandas as pd
import numpy as np
from pathlib import Path
import os

def integrate_cvg(year, base_path):
    print(f"Processing Year {year}...")
    
    # 1. Load data
    explorer_path = base_path / "data" / "processed" / "historico" / f"explorer_{year}.parquet"
    mapping_path = base_path / "metodología" / "cvg-idc" / "output" / "sector_mapping.csv"
    alpha_path = base_path / "metodología" / "cvg-idc" / "output" / "alpha_matrix_2022.csv"
    output_dir = base_path / "metodología" / "cvg-idc" / "output" / "idc_cvg"
    
    if not explorer_path.exists() or not mapping_path.exists() or not alpha_path.exists():
        print("Missing required files.")
        return

    # Load mapping
    map_df = pd.read_csv(mapping_path, sep=';')
    # Map industry names to ICIO codes
    # Industry in explorer is like "154 Manufacturing..."
    def get_id(name):
        try:
            return int(name.split(';')[0].split(' ')[0].split('\t')[0]) # robust split
        except:
            # Try parsing from the start of string
            import re
            m = re.match(r"(\d+)", str(name))
            if m: return int(m.group(1))
            return None

    # Load alpha matrix
    alpha_df = pd.read_csv(alpha_path, index_col=0)
    alpha_matrix = alpha_df.values # 45x45
    icio_sectors = alpha_df.columns.tolist()
    sector_to_idx = {s: i for i, s in enumerate(icio_sectors)}
    
    # Load IDC data
    df = pd.read_parquet(explorer_path)
    df['industry_id'] = df['industry'].apply(get_id)
    
    # Merge with mapping
    df = df.merge(map_df[['industry_id', 'icio_code']], on='industry_id', how='left')
    
    # Aggregate IDC to ICIO level (weighted average by dep_total if needed, but here we just sum/mean)
    # Actually, we want the dependency of a country in a whole sector.
    # For now, let's take the mean dependency in the sector (strategic proxy)
    agg_df = df.groupby(['importer', 'exporter', 'icio_code']).agg({
        'dep_total': 'mean',
        'dep_direct': 'mean'
    }).reset_index()
    
    print(f"Aggregated records to {len(agg_df)} pairs.")

    # Pivot to get a matrix [Pairs x Sectors]
    # Filter to only sectors present in alpha matrix
    agg_df = agg_df[agg_df['icio_code'].isin(icio_sectors)]
    
    # Pivotting is heavy if we have 200*200 pairs.
    # Let's do it by blocks of importers to save memory
    importers = agg_df['importer'].unique()
    
    results = []
    
    for imp in importers:
        imp_data = agg_df[agg_df['importer'] == imp]
        # Pivot: Exporters as rows, ICIO sectors as columns
        # Fill missing dependencies with 0
        pivoted_dt = imp_data.pivot(index='exporter', columns='icio_code', values='dep_total').fillna(0)
        pivoted_dd = imp_data.pivot(index='exporter', columns='icio_code', values='dep_direct').fillna(0)
        
        # Ensure all icio_sectors are present and in correct order
        for s in icio_sectors:
            if s not in pivoted_dt.columns:
                pivoted_dt[s] = 0.0
                pivoted_dd[s] = 0.0
        pivoted_dt = pivoted_dt[icio_sectors]
        pivoted_dd = pivoted_dd[icio_sectors]
        
        # Matrix Multiply
        # DT_cvg = DD + DT * alpha (alpha is sector_source x sector_dest)
        # pivoted_dt is [Exporters x SectorSource]
        # alpha_matrix is [SectorSource x SectorDest]
        # Result is [Exporters x SectorDest]
        
        dt_upstream = pivoted_dt.values @ alpha_matrix
        dt_cvg = pivoted_dd.values + dt_upstream
        
        # Convert back to flat format
        res_df = pd.DataFrame(dt_cvg, index=pivoted_dt.index, columns=pivoted_dt.columns).stack().reset_index()
        res_df.columns = ['exporter', 'icio_code', 'dep_cvg']
        
        dd_df = pd.DataFrame(pivoted_dd.values, index=pivoted_dd.index, columns=pivoted_dd.columns).stack().reset_index()
        dd_df.columns = ['exporter', 'icio_code', 'dep_direct']
        
        dt_df = pd.DataFrame(pivoted_dt.values, index=pivoted_dt.index, columns=pivoted_dt.columns).stack().reset_index()
        dt_df.columns = ['exporter', 'icio_code', 'dep_total_idc']
        
        res_df = res_df.merge(dd_df, on=['exporter', 'icio_code']).merge(dt_df, on=['exporter', 'icio_code'])
        res_df['importer'] = imp
        res_df['hidden_risk'] = res_df['dep_cvg'] - res_df['dep_direct']
        
        results.append(res_df)
    
    final_df = pd.concat(results)
    
    # Save results
    output_dir.mkdir(parents=True, exist_ok=True)
    final_path = output_dir / f"cvg_decomp_{year}.parquet"
    final_df.to_parquet(final_path)
    
    print(f"CVG integration completed. Results saved to {final_path}")
    return final_df

if __name__ == "__main__":
    base_path = Path(r"c:\Users\Usuario\Documents\Github\Seguridad Economica")
    integrate_cvg(2022, base_path)

import pandas as pd
import numpy as np
from pathlib import Path

def parse_icio(file_path, output_path):
    print(f"Loading ICIO data from {file_path}...")
    
    # Read only the header to identify columns
    header_df = pd.read_csv(file_path, nrows=0)
    all_cols = header_df.columns.tolist()
    
    # The first column usually contains the row labels. In this CSV it seems to be 'V1'
    row_label_col = all_cols[0]
    
    # Identify intermediate sectors: ISO3_SectorCode
    # They should not be final demand (HFCE, etc.) or 'OUT' or 'V1'
    final_demand_suffixes = ["HFCE", "NPISH", "GGFC", "GFCF", "INVNT", "DPABR"]
    
    intermediate_cols = [c for c in all_cols if "_" in c and not any(s in c for s in final_demand_suffixes)]
    
    print(f"Detected {len(intermediate_cols)} intermediate sector-country columns.")
    
    # Read the data. To save memory, read only intermediate columns + index
    # Note: index_col=0 will make the first column the index
    try:
        df = pd.read_csv(file_path, usecols=[row_label_col] + intermediate_cols, index_col=0)
    except ValueError as e:
        print(f"Error reading CSV: {e}")
        # Fallback: if names mismatch, read a sample to debug
        return
    
    # The index contains row labels. We want to keep only rows that are also intermediate sectors
    # Some rows might be Value Added, etc.
    valid_rows = [r for r in df.index if r in intermediate_cols]
    df = df.loc[valid_rows]
    
    print("Matrix shape (Intermediate Demand):", df.shape)
    
    # Extract sector codes by removing country prefix (ISO3_)
    # Standard ICIO: USA_C10T12 -> C10T12
    # Important: some sectors might have underscores themselves if they are aggregates
    def get_sector(label):
        parts = label.split('_')
        if len(parts) > 1:
            return '_'.join(parts[1:])
        return label

    # Aggregation
    # Row aggregation: Source Industry
    df['sector_source'] = [get_sector(r) for r in df.index]
    row_agg = df.groupby('sector_source').sum()
    
    # Column aggregation: Destination Industry
    # Transpose to group columns
    col_agg = row_agg.T
    col_agg['sector_dest'] = [get_sector(c) for c in col_agg.index]
    industry_matrix = col_agg.groupby('sector_dest').sum().T
    
    print("Aggregate Industry-to-Industry matrix shape:", industry_matrix.shape)
    
    # Normalize: Each column should sum to the total intermediate inputs of that sector
    col_sums = industry_matrix.sum(axis=0)
    # Ensure no division by zero
    col_sums = col_sums.replace(0, 1)
    alpha_matrix = industry_matrix.div(col_sums, axis=1)
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    alpha_matrix.to_parquet(output_path)
    alpha_matrix.to_csv(output_path.with_suffix('.csv'))
    
    print(f"Alpha matrix (45x45 industries) saved to {output_path}")
    
    # Preview some sectors
    print("\nPreview of Alpha Matrix (first 5 industries):")
    print(alpha_matrix.iloc[:5, :5])
    
    return alpha_matrix

if __name__ == "__main__":
    base_path = Path(r"c:\Users\Usuario\Documents\Github\Seguridad Economica")
    icio_file = base_path / "data" / "raw" / "ICIO" / "2022_SML.csv"
    output_file = base_path / "metodología" / "cvg-idc" / "output" / "alpha_matrix_2022.parquet"
    
    if icio_file.exists():
        parse_icio(icio_file, output_file)
    else:
        print(f"File not found: {icio_file}")

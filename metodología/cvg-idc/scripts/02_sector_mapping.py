import pandas as pd
from pathlib import Path

def create_mapping(itp_csv, icio_codes, output_path):
    itp_df = pd.read_csv(itp_csv, sep=';')
    
    # Pre-defined mapping for ITP sectors to ICIO 2025 codes
    # This is a strategic mapping based on sector names
    
    mapping_rules = {
        # Agriculture (A01-A03)
        (1, 26): "A01", 
        (27, 27): "A02",
        (28, 28): "A03",
        
        # Mining (B)
        (29, 29): "B05", # Coal
        (30, 31): "B06", # Oil/Gas
        (32, 33): "B07", # Ores
        
        # Utilities (D, E)
        (34, 35): "D", # Electricity/Gas
        
        # Food & Textiles (C10-C15)
        (36, 53): "C10T12", # Food, Beverages, Tobacco
        (54, 64): "C13T15", # Textiles, Apparel, Leather
        
        # Wood/Paper/Printing (C16-C18)
        (65, 69): "C16",    # Wood
        (70, 78): "C17_18", # Paper, Printing, Publishing
        
        # Energy/Chemicals/Pharma (C19-C22)
        (79, 81): "C19", # Coke / Refining / Nuclear
        (82, 86): "C20", # Chemicals (except 56)
        (87, 87): "C21", # Pharma (87: Pharmaceuticals)
        (88, 93): "C20", # Soap, etc. (Other chemicals)
        (94, 94): "C22", # Plastic products
        
        # Non-metallic / Metals (C23-C24)
        (95, 101): "C23", # Glass/Cement/Stone
        (102, 102): "C24A", # Iron & Steel
        (103, 103): "C24B", # Non-ferrous
        
        # Fabricated Metal / Machinery / Electronics (C25-C28)
        (104, 108): "C25", 
        (118, 123): "C28", # Special Machinery
        (124, 124): "C26", # Office/Computing
        (125, 130): "C27", # Electrical
        (131, 133): "C26", # Electronic valves, TV/Radio
        (134, 137): "C26", # Medical/Measuring/Optical
        (109, 117): "C28", # General Machinery
        
        # Transport (C29-C30)
        (138, 140): "C29", # Vehicles (138: Motor vehicles, 139: Bodies, 140: Parts)
        (141, 142): "C301", # Ships (Shipbuilding, leisure boats)
        (143, 147): "C302T309", # Planes, Trains, etc.
        
        # Other Mfg / Services (C31-S)
        (148, 153): "C31T33", # Furniture, Sports, Toys
        (154, 155): "C31T33", # Services on physical inputs / repair
        (156, 156): "H49", # Transport (Generic) -> Map to Land by default
        (157, 157): "I", # Travel
        (158, 158): "F", # Construction
        (159, 160): "K", # Finance/Insurance
        (161, 161): "M", # IP
        (162, 162): "J61", # Telecom
        (163, 163): "M", # Business service
        (164, 164): "R", # Heritage/Recr
        (165, 165): "Q", # Health
        (166, 166): "P", # Education
        (167, 167): "O", # Govt
        (168, 170): "S", # Other services
    }
    
    # Handle overlap/gaps
    def find_icio(row):
        itp_id = row['industry_id']
        for (start, end), code in mapping_rules.items():
            if start <= itp_id <= end:
                return code
        return "G" # Default to Trade/Misc
    
    itp_df['icio_code'] = itp_df.apply(find_icio, axis=1)
    
    # Filter to only codes present in our ICIO matrix
    itp_df['icio_valid'] = itp_df['icio_code'].isin(icio_codes)
    
    itp_df.to_csv(output_path, index=False, sep=';')
    print(f"Mapping saved to {output_path}")
    print(f"Mapped {len(itp_df)} ITP industries.")
    print("Missing in ICIO matrix:", itp_df[~itp_df['icio_valid']]['icio_code'].unique())
    
    return itp_df

if __name__ == "__main__":
    base_path = Path(r"c:\Users\Usuario\Documents\Github\Seguridad Economica")
    itp_csv = base_path / "data" / "processed" / "dependencias_consolidadas" / "industrias_id_nombre.csv"
    alpha_csv = base_path / "metodología" / "cvg-idc" / "output" / "alpha_matrix_2022.csv"
    output_path = base_path / "metodología" / "cvg-idc" / "output" / "sector_mapping.csv"
    
    if itp_csv.exists() and alpha_csv.exists():
        # Load alpha matrix to get valid ICIO codes
        alpha_df = pd.read_csv(alpha_csv, index_col=0)
        icio_codes = alpha_df.columns.tolist()
        create_mapping(itp_csv, icio_codes, output_path)
    else:
        print("Required files missing.")

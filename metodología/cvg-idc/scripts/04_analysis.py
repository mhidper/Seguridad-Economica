import pandas as pd
from pathlib import Path

def generate_report(year, base_path):
    # Load data
    cvg_path = base_path / "metodología" / "cvg-idc" / "output" / "idc_cvg" / f"cvg_decomp_{year}.parquet"
    mapping_path = base_path / "metodología" / "cvg-idc" / "output" / "sector_mapping.csv"
    alpha_path = base_path / "metodología" / "cvg-idc" / "output" / "alpha_matrix_2022.csv"
    
    df = pd.read_parquet(cvg_path)
    alpha_df = pd.read_csv(alpha_path, index_col=0)
    
    # Analyze Spain
    esp = df[df['importer'] == 'ESP']
    
    priority_sectors = {
        'C29': 'Motor Vehicles',
        'C26': 'Electronics',
        'C21': 'Pharmaceuticals',
        'C19': 'Energy (Refined)',
        'C20': 'Chemicals',
        'C24A': 'Iron & Steel',
        'C24B': 'Non-ferrous metals'
    }
    
    report = []
    report.append(f"# 📊 Informe de Extensión CVG: Dependencia de España ({year})\n")
    report.append("Este informe analiza la dependencia comercial de España incorporando las Cadenas de Valor Globales (CVG). ")
    report.append("La dependencia CVG suma a la importación directa la vulnerabilidad 'oculta' en los insumos upstream.\n")
    
    for code, name in priority_sectors.items():
        if code not in esp['icio_code'].values: continue
        
        report.append(f"## ⛓️ Cadena de Valor: {name} ({code})")
        
        # Top exporters for this sector
        top_exporters = esp[esp['icio_code'] == code].sort_values('dep_cvg', ascending=False).head(5)
        
        report.append("\n**Top 5 proveedores por dependencia real (Directa + Upstream):**\n")
        report.append("| Exportador | Dependencia CVG |")
        report.append("|------------|-----------------|")
        for _, row in top_exporters.iterrows():
            report.append(f"| {row['exporter']} | {row['dep_cvg']:.4f} |")
        
        # Recipe analysis
        recipe = alpha_df[code].sort_values(ascending=False).head(5)
        report.append("\n**Estructura upstream (Receta de producción):**")
        report.append(f"Este sector requiere los siguientes insumos principales (coeficientes α):")
        for up_code, weight in recipe.items():
            if weight < 0.01: continue
            report.append(f"- **{up_code}**: {weight*100:.1f}%")
        
        report.append("\n---\n")
    
    # Save report
    report_path = base_path / "metodología" / "cvg-idc" / "output" / f"reporte_cvg_esp_{year}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
    
    print(f"Report generated at {report_path}")
    return report_path

if __name__ == "__main__":
    base_path = Path(r"c:\Users\Usuario\Documents\Github\Seguridad Economica")
    generate_report(2022, base_path)

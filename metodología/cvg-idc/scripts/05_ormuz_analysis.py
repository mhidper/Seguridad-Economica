import pandas as pd
from pathlib import Path

base_path = Path(r"c:\Users\Usuario\Documents\Github\Seguridad Economica")
cvg_path = base_path / "metodología" / "cvg-idc" / "output" / "idc_cvg" / "cvg_decomp_2022.parquet"
cvg = pd.read_parquet(cvg_path)

ormuz_isos = ['SAU', 'IRQ', 'ARE', 'KWT', 'QAT', 'IRN', 'OMN', 'BHR']
esp = cvg[(cvg['importer'] == 'ESP') & (cvg['exporter'].isin(ormuz_isos))]

print('Dependencia TOTAL CVG sumada de España hacia los países de Omuz por Sector:')
res = esp.groupby('icio_code')['dep_cvg'].sum().sort_values(ascending=False).head(15)
print(res)

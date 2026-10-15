"""
02b_energia_extraer.py — Convierte el Statistical Review of World Energy (Energy Institute, formato panel)
en un parquet ligero para la regla de energía (comun.energia_referencia).

Entrada: data/raw/Statistical Review of World Energy Narrow format.xlsx (hoja única, formato panel)
Salida:  data/processed/energia/ei_narrow.parquet
"""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from idee_paths import idee_root, comprobar_dentro

R = idee_root()
fuente = sorted((R / "data/raw").glob("Statistical Review of World Energy*.xlsx"))
if not fuente:
    raise FileNotFoundError("No está el Statistical Review of World Energy en data/raw/")
x = pd.ExcelFile(fuente[-1])
d = x.parse(x.sheet_names[0])
esperadas = {"Country", "Year", "ISO3166_alpha3", "Var", "Value"}
faltan = esperadas - set(d.columns)
if faltan:
    raise ValueError(f"El fichero del Energy Institute no tiene las columnas esperadas: {faltan}")
salida = comprobar_dentro(R / "data/processed/energia/ei_narrow.parquet")
salida.parent.mkdir(parents=True, exist_ok=True)
d.to_parquet(salida, index=False)
print(f"{fuente[-1].name}: {len(d):,} filas, {d.Var.nunique()} variables, años {d.Year.min()}-{d.Year.max()} -> {salida.name}")

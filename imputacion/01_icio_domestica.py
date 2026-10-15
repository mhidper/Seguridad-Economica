"""
01_icio_domestica.py — Producción doméstica por país-sector-año desde OCDE ICIO (SML).

Definición, idéntica a la de la ITPD-E para el comercio doméstico:
    doméstica(c,s) = producción(c,s) − exportaciones(c,s)
                   = Σ de la fila (c,s) en las columnas del propio país c (usos intermedios + demanda final)
Se comprueba que la suma de la fila coincide con OUT.
Uso: python imputacion/01_icio_domestica.py 2016 2017 ... (por defecto 2009-2022)
     Opcional: --origen <carpeta> para leer los SML de otra carpeta (solo lectura). Por defecto, data/raw/ICIO.
Salida: data/processed/diagonal/icio_domestica_{año}.parquet
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from idee_paths import idee_root, comprobar_dentro

R = idee_root()
args = sys.argv[1:]
origen = R / "data/raw/ICIO"
if "--origen" in args:
    k = args.index("--origen"); origen = Path(args[k + 1]); args = args[:k] + args[k + 2:]
anios = [int(a) for a in args] or list(range(2009, 2023))
for anio in anios:
    df = pd.read_csv(origen / f"{anio}_SML.csv", index_col=0)
    filas = [i for i in df.index if "_" in i]
    cols = [c for c in df.columns if c != "OUT"]
    X = df.loc[filas, cols].to_numpy(dtype=np.float64)
    pais_fila = np.array([i.split("_", 1)[0] for i in filas])
    pais_col = np.array([c.split("_", 1)[0] for c in cols])
    out = df.loc[filas, "OUT"].to_numpy(dtype=np.float64)
    total = X.sum(axis=1)
    dom = np.array([X[k, pais_col == pais_fila[k]].sum() for k in range(len(filas))])
    err = np.nanmax(np.abs(total - out) / np.maximum(out, 1))
    res = pd.DataFrame({"pais": pais_fila, "sector": [i.split("_", 1)[1] for i in filas], "year": anio,
                        "produccion": out, "domestica": dom, "exportaciones": out - dom})
    f = comprobar_dentro(R / f"data/processed/diagonal/icio_domestica_{anio}.parquet")
    f.parent.mkdir(parents=True, exist_ok=True)
    res.to_parquet(f, index=False)
    print(f"{anio}: {res.pais.nunique()} economías x {res.sector.nunique()} sectores | "
          f"cuadre fila vs OUT (error relativo máx.) = {err:.2e} | doméstica total = {dom.sum()/1e6:,.1f} billones USD")

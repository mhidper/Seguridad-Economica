"""
02_itpd_extraer.py — Diagonal observada, exportaciones e importaciones de la ITPD-E por país-industria-año.

Las 10 partes forman un único CSV troceado por bytes (las filas quedan partidas entre partes).
Cada parte se procesa por separado y se guardan los fragmentos de las costuras; al combinar,
se recomponen esas filas, de modo que no se pierde ningún registro.

Uso:
    python imputacion/02_itpd_extraer.py parte 0      (... hasta 9)
    python imputacion/02_itpd_extraer.py combinar
Salida: data/processed/diagonal/itpd_agregados.parquet
    columnas: pais, industry_id, year, D (doméstico, exportador==importador),
              X (exportaciones a otros países), M (importaciones de otros países)
Solo años >= ANIO_MIN y flujos con trade > 0.
"""
import gzip
import io
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from idee_paths import idee_root, comprobar_dentro

ANIO_MIN = 2005
R = idee_root()
SRC = R / "data/raw/ITP/ITPD_E_R03"
TMP = comprobar_dentro(R / "data/processed/diagonal/itpd_tmp")
COLS = ["exp", "imp", "year", "trade", "ind"]


def agregar(df):
    df = df[(df.year >= ANIO_MIN) & (df.trade > 0)]
    dom = df.exp == df.imp
    D = df[dom].groupby(["exp", "ind", "year"]).trade.sum().rename("D")
    X = df[~dom].groupby(["exp", "ind", "year"]).trade.sum().rename("X")
    M = df[~dom].groupby(["imp", "ind", "year"]).trade.sum().rename("M")
    for s in (D, X, M):
        s.index.names = ["pais", "industry_id", "year"]
    return pd.concat([D, X, M], axis=1).fillna(0.0).reset_index()


def leer(bloque: bytes):
    return pd.read_csv(io.BytesIO(bloque), header=None, usecols=[0, 1, 2, 3, 4], names=COLS,
                       dtype={"exp": str, "imp": str, "year": "int32", "trade": "float64", "ind": "int32"})


def parte(n):
    TMP.mkdir(parents=True, exist_ok=True)
    trozos, cabeza, resto = [], None, b""
    with gzip.open(SRC / f"ITPD_E_R03.csv.parte{n}.gz", "rb") as g:
        while True:
            blk = g.read(1 << 26)
            if not blk:
                break
            buf = resto + blk
            if cabeza is None:
                i = buf.find(b"\n")
                cabeza, buf = buf[: i + 1], buf[i + 1:]
            j = buf.rfind(b"\n")
            if j < 0:
                resto = buf
                continue
            trozos.append(agregar(leer(buf[: j + 1])))
            resto = buf[j + 1:]
    (TMP / f"cabeza{n}.bin").write_bytes(cabeza)
    (TMP / f"cola{n}.bin").write_bytes(resto)
    res = pd.concat(trozos).groupby(["pais", "industry_id", "year"], as_index=False).sum()
    res.to_parquet(TMP / f"parte{n}.parquet", index=False)
    print(f"parte {n}: {len(res):,} celdas país-industria-año; cola de {len(resto)} bytes")


def combinar():
    partes = [pd.read_parquet(TMP / f"parte{n}.parquet") for n in range(10)]
    # Costuras: cola(n) + cabeza(n+1) es exactamente una fila completa
    costuras = b"".join((TMP / f"cola{n}.bin").read_bytes() + (TMP / f"cabeza{n+1}.bin").read_bytes() for n in range(9))
    costuras += (TMP / "cola9.bin").read_bytes()
    assert (TMP / "cabeza0.bin").read_bytes().startswith(b"exporter_iso3"), "La parte 0 debe empezar por la cabecera"
    if costuras.strip():
        filas = leer(costuras if costuras.endswith(b"\n") else costuras + b"\n")
        print(f"filas recompuestas en las costuras: {len(filas)}")
        partes.append(agregar(filas))
    res = pd.concat(partes).groupby(["pais", "industry_id", "year"], as_index=False).sum()
    f = comprobar_dentro(R / "data/processed/diagonal/itpd_agregados.parquet")
    res.to_parquet(f, index=False)
    print(f"itpd_agregados: {len(res):,} celdas | años {res.year.min()}-{res.year.max()} | "
          f"celdas con diagonal observada: {(res.D > 0).sum():,}")


if __name__ == "__main__":
    if sys.argv[1] == "parte":
        parte(int(sys.argv[2]))
    elif sys.argv[1] == "combinar":
        combinar()

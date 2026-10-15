"""
prueba_diagonal.py — Prueba en seco del punto de enganche antes de ejecutar el motor.

Reproduce la tabla `data` que devuelve procesar_datos_itp() para un año (mismas columnas y tipos), aplica
aplicar_diagonal() con el interruptor ENCENDIDO (solo en memoria; el fichero idee_diagonal.py no se toca) y
pasa el resultado por la lógica de crear_matriz_comercio_optimizado() y por la agregación UE27 del motor UE.

Uso:  python herramientas/prueba_diagonal.py extraer <AÑO> <PARTE>   (partes 0..9; guarda filas del año)
      python herramientas/prueba_diagonal.py probar <AÑO>
"""
import gzip, io, sys
from pathlib import Path
import numpy as np
import pandas as pd
SANDBOX = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SANDBOX))
from idee_paths import idee_root, comprobar_dentro
import idee_diagonal

USECOLS = ["exporter_iso3", "importer_iso3", "year", "trade", "industry_id", "industry_descr", "importer_name", "exporter_name"]
DTYPES = {"exporter_iso3": "string", "importer_iso3": "string", "year": "int32", "trade": "float32",
          "industry_id": "int32", "industry_descr": "string", "importer_name": "string", "exporter_name": "string"}
SRC = idee_root() / "data/raw/ITP/ITPD_E_R03"
TMP = comprobar_dentro(idee_root() / "data/processed/diagonal/prueba")
CAB = None


def extraer(anio, n):
    TMP.mkdir(parents=True, exist_ok=True)
    cab = gzip.open(SRC / "ITPD_E_R03.csv.parte0.gz", "rt").readline().strip().split(",")
    trozos, primero, resto = [], None, b""
    with gzip.open(SRC / f"ITPD_E_R03.csv.parte{n}.gz", "rb") as g:
        while True:
            blk = g.read(1 << 26)
            if not blk:
                break
            buf = resto + blk
            if primero is None:
                i = buf.find(b"\n"); primero, buf = buf[: i + 1], buf[i + 1:]
            j = buf.rfind(b"\n")
            if j < 0:
                resto = buf; continue
            df = pd.read_csv(io.BytesIO(buf[: j + 1]), header=None, names=cab, usecols=USECOLS, dtype=str)
            trozos.append(df[df.year == str(anio)])
            resto = buf[j + 1:]
    (TMP / f"cabeza{n}.bin").write_bytes(primero); (TMP / f"cola{n}.bin").write_bytes(resto)
    pd.concat(trozos).to_parquet(TMP / f"filas_{anio}_parte{n}.parquet", index=False)
    print(f"parte {n}: {sum(len(t) for t in trozos):,} filas de {anio}")


def _intactas(o, d, anio):
    """Las filas originales solo cambian en 'trade' de diagonales que el fichero marca como imputadas (residuos)."""
    diag = pd.read_parquet(idee_diagonal.ruta_diagonal(anio))
    sust = set(zip(diag.iso3[diag.fuente.ne("observada")], diag.industry_id[diag.fuente.ne("observada")].astype(int)))
    cambia = ~(o.trade.values == d.trade.values)
    es_diag = (d.exporter_iso3.astype(str) == d.importer_iso3.astype(str)).values
    claves = list(zip(d.exporter_iso3.astype(str), d.industry_id.astype(int)))
    ok_sust = all(es_diag[k] and claves[k] in sust for k in np.where(cambia)[0])
    otras = o.drop(columns="trade").reset_index(drop=True).equals(d.drop(columns="trade").reset_index(drop=True))
    print(f"[prueba] diagonales sustituidas: {int(cambia.sum()):,}")
    return bool(ok_sust and otras)


def _falla_en_alto(data, anio):
    try:
        try:
            idee_diagonal.aplicar_diagonal(data.drop(columns="trade"), anio, verbose=False)   # provoca un error
        except Exception:
            return False                                                # lo habría capturado el notebook
    except idee_diagonal.DiagonalNoAplicada:
        return True
    return False


def probar(anio):
    cab = gzip.open(SRC / "ITPD_E_R03.csv.parte0.gz", "rt").readline().strip().split(",")
    partes = [pd.read_parquet(TMP / f"filas_{anio}_parte{n}.parquet") for n in range(10)]
    cost = b"".join((TMP / f"cola{n}.bin").read_bytes() + (TMP / f"cabeza{n+1}.bin").read_bytes() for n in range(9))
    c = pd.read_csv(io.BytesIO(cost), header=None, names=cab, usecols=USECOLS, dtype=str)
    data = pd.concat(partes + [c[c.year == str(anio)]], ignore_index=True)
    data = data.astype(DTYPES)                                         # igual que procesar_datos_itp
    data.index = np.arange(len(data)) % 500_000                        # índice con etiquetas repetidas, como dask.compute()
    data["importer_iso3"] = data["importer_iso3"].astype("category")
    countries = list(data["importer_iso3"].cat.categories)
    n0, diag0 = len(data), int((data.exporter_iso3.astype(str) == data.importer_iso3.astype(str)).sum())
    print(f"[base] filas {n0:,} | países {len(countries)} | diagonales observadas {diag0:,}")

    idee_diagonal.USAR_DIAGONAL_IMPUTADA = True                        # solo en memoria
    out = idee_diagonal.aplicar_diagonal(data, anio)
    comprobaciones = {
        "mismas columnas y orden": list(out.columns) == list(data.columns),
        "mismos tipos": all(str(out[k].dtype) == str(data[k].dtype) for k in data.columns),
        "lista de países sin cambios": list(out["importer_iso3"].cat.categories) == countries,
        "filas originales intactas salvo diagonales sustituidas": _intactas(out.iloc[:n0], data, anio),
        "error del enganche detiene el notebook (no lo captura except Exception)": _falla_en_alto(data, anio),
        "sin valores nulos nuevos": not out.iloc[n0:].isna().any().any(),
        "solo se añaden diagonales": bool((out.iloc[n0:].exporter_iso3.astype(str) == out.iloc[n0:].importer_iso3.astype(str)).all()),
        "ninguna diagonal duplicada": not out[out.exporter_iso3.astype(str) == out.importer_iso3.astype(str)]
                                         .duplicated(["exporter_iso3", "industry_id"]).any(),
        "valores positivos y finitos": bool(np.isfinite(out.iloc[n0:].trade).all() and (out.iloc[n0:].trade > 0).all()),
        "industry_descr coherente": out.groupby("industry_id").industry_descr.nunique().max() == 1,
    }
    # crear_matriz_comercio_optimizado (misma lógica: pivot exportador x importador por industria)
    codigos = sorted(out["importer_iso3"].unique().tolist())
    ok_mat, n_ind = True, 0
    for ind, g in out.groupby("industry_descr"):
        g = g[g.exporter_iso3.isin(codigos) & g.importer_iso3.isin(codigos)]
        mat = g.pivot_table(index="exporter_iso3", columns="importer_iso3", values="trade", aggfunc="sum",
                            fill_value=0.0, observed=False).reindex(index=codigos, columns=codigos, fill_value=0.0)
        ok_mat &= mat.shape == (len(codigos), len(codigos)) and np.isfinite(mat.values).all()
        n_ind += 1
    comprobaciones[f"matrices construidas ({n_ind} industrias)"] = bool(ok_mat)
    # agregación UE27 (misma lógica que 00_dependency_ue)
    ue27 = ["AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "IRL", "ITA", "LVA",
            "LTU", "LUX", "MLT", "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE"]
    u = out.copy()
    for col in ["exporter_iso3", "importer_iso3", "exporter_name", "importer_name"]:
        u[col] = u[col].astype(str)
    u.loc[u.exporter_iso3.isin(ue27), ["exporter_name", "exporter_iso3"]] = ["European Union 27", "EU27"]
    u.loc[u.importer_iso3.isin(ue27), ["importer_name", "importer_iso3"]] = ["European Union 27", "EU27"]
    u = u.groupby(["exporter_iso3", "importer_iso3", "year", "industry_id", "industry_descr", "importer_name", "exporter_name"],
                  as_index=False, observed=True)["trade"].sum()
    comprobaciones["agregación UE27 sin errores"] = "EU27" in set(u.importer_iso3)
    print("\nComprobaciones:")
    for k, v in comprobaciones.items():
        print(f"  {'OK ' if v else 'FALLO'}  {k}")
    print("\nTODO CORRECTO" if all(comprobaciones.values()) else "\nHAY FALLOS")


if __name__ == "__main__":
    if sys.argv[1] == "extraer":
        extraer(int(sys.argv[2]), int(sys.argv[3]))
    else:
        probar(int(sys.argv[2]))

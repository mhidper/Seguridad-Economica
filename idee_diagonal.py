"""
idee_diagonal.py — Punto único de entrada del cambio metodológico.

Completa la producción doméstica (diagonal exportador == importador) que falta en
la ITPD-E, a partir de los ficheros generados en sandbox/imputacion/.

Reglas:
  * Las celdas con diagonal OBSERVADA en la ITPD-E se conservan, salvo las que el módulo de imputación
    marca como residuo poco creíble (coherencia con la especialización exportadora, ver
    imputacion/comun.py): en el fichero de la diagonal llegan con una fuente distinta de "observada"
    y su valor sustituye al de la ITPD-E. Es el mismo tratamiento que una laguna.
  * Solo se añaden diagonales para países e industrias que ya están en los datos
    del año (no cambia la lista de países ni de industrias del motor).
  * Con USAR_DIAGONAL_IMPUTADA = False la función devuelve los datos intactos:
    el motor reproduce exactamente la versión en producción.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from idee_paths import idee_root

# Interruptor general. False = réplica exacta de producción (línea base).
# Encendido por defecto. Se apaga sin editar este fichero con la variable de entorno IDEE_DIAGONAL=0
# (PowerShell: $env:IDEE_DIAGONAL = "0"), p. ej. para reproducir la versión anterior sin diagonal.
import os
USAR_DIAGONAL_IMPUTADA = os.environ.get("IDEE_DIAGONAL", "1") == "1"   # encendido por defecto desde la migración (15-10-2026); IDEE_DIAGONAL=0 lo apaga


def ruta_diagonal(anio) -> Path:
    return idee_root() / "data" / "processed" / "diagonal" / f"diagonal_{anio}.parquet"


class DiagonalNoAplicada(BaseException):
    """Error al aplicar la diagonal. Hereda de BaseException para que el try/except Exception del notebook no lo
    capture: la ejecución se detiene en el acto en lugar de seguir horas sin diagonal."""


def aplicar_diagonal(data: pd.DataFrame, anio, verbose: bool = True) -> pd.DataFrame:
    try:
        return _aplicar_diagonal(data, anio, verbose)
    except Exception as e:
        raise DiagonalNoAplicada(f"[idee_diagonal] ERROR al aplicar la diagonal de {anio}: {type(e).__name__}: {e}") from e


def _aplicar_diagonal(data: pd.DataFrame, anio, verbose: bool = True) -> pd.DataFrame:
    if not USAR_DIAGONAL_IMPUTADA:
        if verbose:
            print("[idee_diagonal] Interruptor apagado: datos ITPD-E sin modificar (línea base).")
        return data

    f = ruta_diagonal(anio)
    if not f.exists():
        raise FileNotFoundError(f"No existe {f}. Ejecuta antes sandbox/imputacion para el año {anio}.")
    diag = pd.read_parquet(f)  # columnas: iso3, industry_id, trade, fuente

    exp = data["exporter_iso3"].astype(str)
    imp = data["importer_iso3"].astype(str)
    paises = set(imp.unique())
    obs = set(zip(exp[exp == imp], data.loc[exp == imp, "industry_id"].astype(int)))

    d = diag[diag["iso3"].isin(paises) & diag["industry_id"].isin(set(data["industry_id"].astype(int)))]
    d = d[d["trade"] > 0]
    ya = pd.Series([(c, i) in obs for c, i in zip(d["iso3"], d["industry_id"])], index=d.index)
    # residuos poco creíbles: diagonal presente en la ITPD-E pero imputada en el fichero -> se sustituye el valor
    sust = d[ya & d["fuente"].ne("observada")]
    d = d[~ya]
    if len(sust):
        # sustitución por POSICIÓN: el índice que devuelve dask (compute) repite etiquetas entre particiones
        clave = dict(zip(zip(sust["iso3"], sust["industry_id"].astype(int)), sust["trade"]))
        diag_mask = (exp == imp).to_numpy()
        pos = np.flatnonzero(diag_mask)
        ids = data["industry_id"].to_numpy()[pos]
        isos = exp.to_numpy()[pos]
        nuevos = [clave.get((c, int(i))) for c, i in zip(isos, ids)]
        sel = np.array([v is not None for v in nuevos], dtype=bool)
        trade = data["trade"].to_numpy(copy=True)
        trade[pos[sel]] = np.array([v for v in nuevos if v is not None], dtype=trade.dtype)
        data = data.copy()
        data["trade"] = trade

    nombres_ind = data.drop_duplicates("industry_id").set_index("industry_id")["industry_descr"]
    nombres_pais = (pd.concat([
        data[["importer_iso3", "importer_name"]].astype(str).set_axis(["iso3", "name"], axis=1),
        data[["exporter_iso3", "exporter_name"]].astype(str).set_axis(["iso3", "name"], axis=1)])
        .drop_duplicates("iso3").set_index("iso3")["name"])

    nuevo = pd.DataFrame({
        "exporter_iso3": d["iso3"].values,
        "importer_iso3": d["iso3"].values,
        "year": int(anio),
        "trade": d["trade"].values,
        "industry_id": d["industry_id"].values,
        "industry_descr": d["industry_id"].map(nombres_ind).values,
        "importer_name": d["iso3"].map(nombres_pais).values,
        "exporter_name": d["iso3"].map(nombres_pais).values,
    })
    nuevo = nuevo[[c for c in data.columns]]

    cat = isinstance(data["importer_iso3"].dtype, pd.CategoricalDtype)
    cats = data["importer_iso3"].cat.categories if cat else None
    base = data.astype({"importer_iso3": "string"}) if cat else data
    tipos = {c: base[c].dtype for c in base.columns}
    out = pd.concat([base, nuevo.astype(tipos)], ignore_index=True)
    if cat:
        out["importer_iso3"] = out["importer_iso3"].astype(pd.CategoricalDtype(cats))

    if verbose:
        print(f"[idee_diagonal] {anio}: diagonales observadas = {len(obs):,}; "
              f"sustituidas (residuo poco creíble) = {len(sust):,}; "
              f"añadidas = {len(nuevo):,} -> {nuevo['trade'].sum()/1e3:,.0f} mil M$ "
              f"(fuentes: {d['fuente'].value_counts().to_dict()})")
    return out

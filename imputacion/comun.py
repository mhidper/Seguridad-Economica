"""comun.py — utilidades compartidas del módulo de imputación (bloques sectoriales y carga de datos)."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from idee_paths import idee_root, comprobar_dentro  # noqa: F401

R = idee_root()
DIAG = R / "data/processed/diagonal"
ANIOS = list(range(2016, 2023))
MACRO = lambda i: ("Agricultura" if i <= 28 else "Minería y energía" if i <= 35 else
                   "Manufacturas" if i <= 153 else "Servicios")


def mapeo_y_bloques():
    """Devuelve el mapeo 170→ICIO con una columna 'bloque': grupos de industrias que comparten
    algún sector ICIO (componentes conexas), para que cada bloque tenga un único total ICIO."""
    m = pd.read_csv(R / "data/aux/sector_mapping_idee.csv")
    m["sectores"] = m.icio_code.str.split("+")
    padre = {}
    def raiz(x):
        while padre.setdefault(x, x) != x:
            x = padre[x]
        return x
    for secs in m.sectores:
        for s in secs[1:]:
            padre[raiz(s)] = raiz(secs[0])
        raiz(secs[0])
    grupos = {}
    for s in padre:
        grupos.setdefault(raiz(s), set()).add(s)
    m["bloque"] = m.sectores.map(lambda secs: "+".join(sorted(grupos[raiz(secs[0])])))
    def macro(cod):
        c0 = cod.split("+")[0]
        return ("Agricultura" if c0.startswith("A") else "Minería y energía" if c0[0] in "BD" else
                "Manufacturas" if c0.startswith("C") else "Servicios")
    m["macro"] = m.icio_code.map(macro)
    return m


def icio_bloques(m):
    """Producción doméstica ICIO agregada por país-bloque-año."""
    sec2bloque = {s: b for b in m.bloque.unique() for s in b.split("+")}
    d = pd.concat(pd.read_parquet(DIAG / f"icio_domestica_{a}.parquet") for a in ANIOS)
    d = d[d.sector.isin(sec2bloque)]
    d["bloque"] = d.sector.map(sec2bloque)
    return d.groupby(["pais", "bloque", "year"], as_index=False)[["domestica", "produccion"]].sum()


# ---------------------------------------------------------------------------------------------------------
# Coherencia con la especialización exportadora (auditoría de 11-10-2026; prueba en 03d_backtest_coherencia_exportadora).
# El ITPD-E calcula D = producción - exportaciones. Cuando la producción declarada apenas supera a las exportaciones,
# D es un residuo dominado por el error de medida (p. ej. Italia, farmacia: 8.445 M$ en 2005 y 322 M$ en 2015 con
# exportaciones crecientes). Referencia de la celda: la producción doméstica ICIO de su bloque repartida según el peso
# de la industria en las exportaciones del país dentro del bloque (ambas exportaciones del ITPD-E, de modo que las
# reexportaciones se compensan): ref = ICIO_bloque x X(c,i) / X(c,bloque). Si D < PHI x ref, la diagonal observada
# no se usa como ancla, y ningún valor imputado queda por debajo de PHI x ref (suelo).
PHI_COHERENCIA = 0.10
PHI_ENERGIA = 0.25       # umbral de credibilidad frente a la referencia energética (ver itpd_creible)


def ref_exportadora(df, pais="pais", anio="year"):
    """ICIO_bloque x X(c,i)/X(c,bloque) del mismo año. df necesita pais, year, bloque, X y DI."""
    xcb = df.groupby([pais, "bloque", anio]).X.transform("sum")
    return (df.DI * df.X / xcb).where((xcb > 0) & (df.DI > 0))


def itpd_creible(m):
    """itpd_agregados con bloque, DI (ICIO del bloque, todos los años ICIO), ref_exportadora y la marca 'creible'."""
    sec2bloque = {s: b for b in m.bloque.unique() for s in b.split("+")}
    anios = sorted(int(p.stem.split("_")[-1]) for p in DIAG.glob("icio_domestica_*.parquet"))
    d = pd.concat(pd.read_parquet(DIAG / f"icio_domestica_{a}.parquet") for a in anios)
    d = d[d.sector.isin(sec2bloque) & (d.pais != "ROW")].assign(bloque=lambda x: x.sector.map(sec2bloque))
    d = d.groupby(["pais", "bloque", "year"], as_index=False).domestica.sum().rename(columns={"domestica": "DI"})
    ag = pd.read_parquet(DIAG / "itpd_agregados.parquet").merge(m[["industry_id", "bloque"]], on="industry_id")
    ag = ag.merge(d, on=["pais", "bloque", "year"], how="left")
    ag["ref_x"] = ref_exportadora(ag)
    # países fuera de la ICIO en crudo y gas y en refino: referencia energética
    en = energia_referencia()
    paises_icio = set(d.pais)
    ag = ag.merge(en[["pais", "industry_id", "year", "E"]], on=["pais", "industry_id", "year"], how="left")
    ag.loc[ag.pais.isin(paises_icio), "E"] = np.nan
    ag["ref_x"] = ag.ref_x.where(ag.E.isna(), ag.E.where(ag.E > 0))
    ag["creible"] = ~no_creible(ag.D, ag.ref_x)
    # la referencia energética es una estimación directa de la producción (error mediano en log ≈ 0,6, factor ≈ 1,9;
    # 03e): un dato por debajo del 25 % de ella queda a más de dos errores típicos y se trata como residuo
    en_ok = ag.E.notna() & (ag.E > 0)
    ag.loc[en_ok, "creible"] = ~(ag.D[en_ok] < PHI_ENERGIA * ag.E[en_ok])
    return ag


# ---------------------------------------------------------------------------------------------------------
# Energía en países fuera de la ICIO (decisión del 12-10-2026; prueba en 03e_backtest_energia.py).
# Para crudo y gas (industria 31) y refino (80), la producción se toma del Statistical Review of World Energy
# (Energy Institute): volumen físico x valor por unidad. El valor por unidad de cada año es la mediana entre países
# ICIO de producción ICIO del sector (B06, C19) / volumen, por la escala ITPD/ICIO de la industria.
# Referencia energética: E = q x producción estimada, con q la cuota doméstica mediana 2016-2022 del país
# (producción - exportaciones ITPD, sobre producción). Si q < 2 %, no hay referencia y se mantienen las demás reglas.
IND_ENERGIA = {80: "C19", 31: "B06"}
BOE_POR_BCM = 6.1        # millones de barriles equivalentes por bcm de gas natural


def energia_referencia():
    """DataFrame pais, industry_id, year, V (millones de barriles), vu (USD por barril), E (M$, puede ser <= 0)."""
    f = R / "data/processed/energia/ei_narrow.parquet"
    if not f.exists():
        return pd.DataFrame(columns=["pais", "industry_id", "year", "V", "vu", "E"])
    ei = pd.read_parquet(f)
    ei = ei[ei.ISO3166_alpha3.notna() & ~ei.ISO3166_alpha3.str.contains("-")]
    v = ei.pivot_table(index=["ISO3166_alpha3", "Year"], columns="Var", values="Value", aggfunc="first")
    vol = pd.DataFrame({80: v.get("refthru_kbd") * 365 / 1000,
                        31: v.get("oilprod_kbd").fillna(0) * 365 / 1000 + v.get("gasprod_bcm").fillna(0) * BOE_POR_BCM})
    vol = vol.rename_axis(["pais", "year"]).reset_index().melt(id_vars=["pais", "year"], var_name="industry_id", value_name="V")
    vol = vol[vol.V > 0].astype({"industry_id": int, "year": int})
    anios = sorted(int(p.stem.split("_")[-1]) for p in DIAG.glob("icio_domestica_*.parquet"))
    ic = pd.concat(pd.read_parquet(DIAG / f"icio_domestica_{a}.parquet") for a in anios)
    icp = pd.concat([ic[ic.sector == s][["pais", "year", "produccion"]].assign(industry_id=i) for i, s in IND_ENERGIA.items()])
    ag = pd.read_parquet(DIAG / "itpd_agregados.parquet")
    ag = ag[ag.industry_id.isin(IND_ENERGIA)]
    b = vol.merge(icp, on=["pais", "year", "industry_id"])
    b = b[b.produccion > 0]
    u = (b.produccion / b.V).groupby([b.industry_id, b.year]).median().rename("u")
    o = ag[ag.D > 0].merge(icp, on=["pais", "year", "industry_id"])
    o = o[o.produccion > 0]
    esc = ((o.D + o.X) / o.produccion).groupby(o.industry_id).median().rename("esc")
    vu = u.reset_index().join(esc, on="industry_id").assign(vu=lambda d: d.u * d.esc)[["industry_id", "year", "vu"]]
    out = vol.merge(vu, on=["industry_id", "year"]).merge(ag[["pais", "industry_id", "year", "X"]],
                                                          on=["pais", "industry_id", "year"], how="left")
    out["P"] = out.V * out.vu
    out["E_anual"] = out.P - out.X.fillna(0)
    # cuota doméstica de la producción como parámetro estructural del país (mediana 2016-2022, acotada a [0, 1]):
    # evita que la volatilidad de las exportaciones de un año (reexportaciones, almacenamiento) mueva la serie
    q = out[out.year.between(2016, 2022)].assign(q=lambda d: (d.E_anual / d.P).clip(0, 1))
    qs = q.groupby(["pais", "industry_id"]).q.median().rename("q")
    out = out.join(qs, on=["pais", "industry_id"])
    out["E"] = (out.q * out.P).where(out.q >= 0.02)
    return out[["pais", "industry_id", "year", "V", "vu", "P", "q", "E"]]


def no_creible(D, ref):
    """True si la diagonal es un residuo poco creíble frente a su referencia exportadora."""
    return ref.notna() & (ref > 0) & (D < PHI_COHERENCIA * ref)


# ---------------------------------------------------------------------------------------------------------
# Guardado compatible con el entorno de producción («dependencias», pyarrow 19).
# Los parquet escritos con pyarrow >= 20 incluyen estadísticas que pyarrow 19 no sabe leer
# ("Repetition level histogram size mismatch"). Los ficheros que lee el motor (diagonal_{año}.parquet) se
# escriben con pyarrow 19: directamente si este Python ya lo es, o mediante un Python auxiliar con pyarrow 19
# (variable de entorno IDEE_PYTHON_PA19 o ~/venvs/pa19). Si no hay forma de escribirlos compatibles, se detiene.
# ---------------------------------------------------------------------------------------------------------
def guardar_parquet_compatible(df, ruta):
    import os, subprocess, tempfile
    import pyarrow as pa, pyarrow.feather as ft
    ruta = comprobar_dentro(Path(ruta))
    # mismo entorno que el motor (lo indica el pipeline al ejecutar en el PC de cálculo): se escribe directamente,
    # porque el motor leerá con este mismo pyarrow
    if int(pa.__version__.split(".")[0]) <= 19 or os.environ.get("IDEE_MISMO_ENTORNO_MOTOR") == "1":
        df.to_parquet(ruta, index=False)
        return ruta
    py19 = os.environ.get("IDEE_PYTHON_PA19", str(Path.home() / "venvs/pa19/bin/python"))
    if not Path(py19).exists():
        raise RuntimeError(f"pyarrow {pa.__version__} escribe parquet ilegibles para el entorno de producción (pyarrow 19) "
                           f"y no se encuentra un Python con pyarrow 19 en {py19}. Define IDEE_PYTHON_PA19.")
    with tempfile.TemporaryDirectory() as tmp:
        ipc = Path(tmp) / "tabla.arrow"
        ft.write_feather(pa.Table.from_pandas(df, preserve_index=False), ipc, compression="uncompressed")
        codigo = ("import sys, pyarrow.feather as ft, pyarrow.parquet as pq, pyarrow as pa\n"
                  "assert pa.__version__.startswith('19.'), pa.__version__\n"
                  "t = ft.read_table(sys.argv[1]); pq.write_table(t, sys.argv[2]); pq.read_table(sys.argv[2])\n")
        subprocess.run([py19, "-c", codigo, str(ipc), str(ruta)], check=True)
    return ruta

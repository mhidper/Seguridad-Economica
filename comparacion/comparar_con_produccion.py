"""
Compara las salidas del sandbox con las de producción (producción solo se lee).

Uso:
    py sandbox/comparacion/comparar_con_produccion.py 2019            # entregables IBM (historico/)
    py sandbox/comparacion/comparar_con_produccion.py 2019 --motor    # + salidas intermedias del motor

Veredicto por fichero:
  IDÉNTICO   mismas columnas, mismas filas y diferencias numéricas <= 1e-6
  DIFIERE    mismas columnas, pero cambian filas o valores (se informa cuánto)
  VALORES IGUALES, TIPOS DISTINTOS  mismos valores pero alguna columna cambia de tipo (IBM podría notarlo)
  ILEGIBLE   la versión de pyarrow no puede leer algún fichero
  ESTRUCTURA columnas distintas (esto NO debe ocurrir nunca: IBM depende de ellas)
  FALTA      el fichero no existe en el sandbox
Con el interruptor de idee_diagonal.py APAGADO todo debe salir IDÉNTICO.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

TOL = 1e-6
SANDBOX = Path(__file__).resolve().parents[1]
PROD = SANDBOX.parent
sys.path.insert(0, str(SANDBOX)); from idee_paths import historico_referencia   # versión publicada anterior
anios = [a for a in sys.argv[1:] if not a.startswith("--")]
if not anios:
    sys.exit("Uso: py sandbox/comparacion/comparar_con_produccion.py <AÑO> [<AÑO> ...] [--motor]")
motor = "--motor" in sys.argv
ENTREGABLES = ["profiles", "dependencies", "explorer", "bilateral", "critical", "hubs", "hubs_sector"]
MOTOR = ["intermediarios_globales", "country_profiles", "relaciones_criticas", "caminos_significativos"]


def normalizar(df):
    df = df.copy()
    for c in df.columns:
        if df[c].dtype == object or str(df[c].dtype) in ("string", "category"):
            df[c] = df[c].astype(str)
    num = [c for c in df.columns if np.issubdtype(df[c].dtype, np.number)]
    txt = [c for c in df.columns if c not in num]
    orden = txt + num
    df = df.sort_values(orden, kind="mergesort").reset_index(drop=True)
    return df, txt, num


def comparar(fp, fs):
    if not fs.exists():
        return {"veredicto": "FALTA"}
    import pyarrow as pa
    import pyarrow.parquet as pq
    try:
        ta, tb = pq.read_table(fp), pq.read_table(fs)
    except OSError as e:
        return {"veredicto": "ILEGIBLE",
                "detalle": f"pyarrow {pa.__version__} no puede leer el fichero ({e}). "
                           "Los entregables de producción se escribieron con pyarrow 21: hace falta pyarrow >= 21 para compararlos."}
    if ta.schema.equals(tb.schema) and ta.equals(tb):  # vía rápida: misma tabla, mismo orden
        return {"filas_prod": ta.num_rows, "filas_sandbox": tb.num_rows, "tipos_iguales": True,
                "filas_texto_distintas": 0, "max_dif_numerica": 0.0, "columna_max_dif": "", "veredicto": "IDÉNTICO"}
    a, b = ta.to_pandas(), tb.to_pandas()
    r = {"filas_prod": len(a), "filas_sandbox": len(b)}
    if list(a.columns) != list(b.columns):
        r["veredicto"] = "ESTRUCTURA"
        r["detalle"] = f"solo prod: {set(a.columns)-set(b.columns)} | solo sandbox: {set(b.columns)-set(a.columns)}"
        return r
    r["tipos_iguales"] = all(str(a[c].dtype) == str(b[c].dtype) for c in a.columns)
    if len(a) != len(b):
        r["veredicto"] = "DIFIERE"
        r["detalle"] = f"cambia el número de filas ({len(b)-len(a):+d})"
        return r
    a, txt, num = normalizar(a)
    b, _, _ = normalizar(b)
    dif_txt = int((a[txt] != b[txt]).any(axis=1).sum()) if txt else 0
    difs = {c: float((a[c].astype(float) - b[c].astype(float)).abs().max()) for c in num}
    r["filas_texto_distintas"] = dif_txt
    r["max_dif_numerica"] = max(difs.values()) if difs else 0.0
    r["columna_max_dif"] = max(difs, key=difs.get) if difs else ""
    r["veredicto"] = "IDÉNTICO" if dif_txt == 0 and r["max_dif_numerica"] <= TOL else "DIFIERE"
    if r["veredicto"] == "IDÉNTICO" and not r["tipos_iguales"]:
        r["veredicto"] = "VALORES IGUALES, TIPOS DISTINTOS"
        r["detalle"] = "; ".join(f"{c}: {a[c].dtype} vs {b[c].dtype}" for c in a.columns if str(ta.schema.field(c).type) != str(tb.schema.field(c).type))
    return r


filas = []
for anio in anios:
    for suf in ["", "_UE"]:
        grupos = [("historico", ENTREGABLES)] + ([("dependencias_consolidadas", MOTOR)] if motor else [])
        for carpeta, nombres in grupos:
            for n in nombres:
                base = historico_referencia() if carpeta == "historico" else PROD / "data" / "processed" / carpeta
                fp = base / f"{n}_{anio}{suf}.parquet"
                if fp.exists():
                    filas.append({"año": f"{anio}{suf}", "fichero": f"{carpeta}/{fp.name}",
                                  **comparar(fp, SANDBOX / "data" / "processed" / carpeta / fp.name)})

res = pd.DataFrame(filas)
pd.set_option("display.width", 250, "display.max_colwidth", 80)
print(res.to_string(index=False))
print("\nRESUMEN:", res["veredicto"].value_counts().to_dict())
out = SANDBOX / "comparacion" / f"informe_comparacion_{'_'.join(anios)}.csv"
res.to_csv(out, index=False)
print(f"Informe guardado en {out}")

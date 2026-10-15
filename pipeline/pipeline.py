"""
pipeline.py — Cálculo del IDEE de principio a fin, con la producción doméstica (diagonal) completada.

Encadena las piezas que ya existen y están validadas, y decide qué hay que rehacer comparando las huellas de los
ficheros con las de la última ejecución (pipeline/estado.json):

  E1 Inventario de fuentes   ITPD-E, OCDE ICIO, Energy Institute, mapeo sectorial: qué hay, qué ha cambiado, qué falta.
  E2 Diagnóstico de la diagonal   Parte del comercio con producción doméstica observada y creíble, por año.
  E3 Construcción de la diagonal  Solo los pasos cuyas entradas han cambiado (00, 01, 02, 02b) y, si algo cambia,
                                  imputación + ajustes + controles + decisiones (04, 04b, 05, 06) para toda la serie.
                                  Puerta: 0 celdas pendientes, rojo <= 1 % por año, ficheros legibles por el motor.
  E4 Años afectados          Años cuya diagonal (o código del motor) ha cambiado desde su último cálculo.
  E5 Motor                   Global y UE por año (herramientas/ejecutar_motor.py), reanudable.
  E6 Arquitecto              Ficheros de entrega (7 por año y versión).
  E7 Verificación            Comparación con la versión publicada anterior (idee_paths.historico_referencia),
                             casos de los revisores, auditoría, datos del visor.
  (La publicación —subir los entregables a GitHub, de donde los toma IBM— NO forma parte del pipeline: requiere una
   orden expresa.)

Uso (desde la raíz del repositorio, entorno «dependencias»):
  python sandbox/pipeline/pipeline.py                      # modo plan: dice qué haría y por qué, sin ejecutar nada
  python sandbox/pipeline/pipeline.py --ejecutar           # ejecuta lo necesario hasta la verificación
  python sandbox/pipeline/pipeline.py --ejecutar --hasta diagonal     # solo E1-E3
  python sandbox/pipeline/pipeline.py --anios 2020-2022    # limita E4-E7 a esos años
  python sandbox/pipeline/pipeline.py --registrar-estado   # da por buenas las salidas actuales (solo tras validarlas)
  python sandbox/pipeline/pipeline.py --ejecutar --forzar  # rehace todo desde cero (certificación)
  python sandbox/pipeline/pipeline.py --ejecutar --anios 2022 --rehacer-anios 2022   # repite un año concreto
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

S = Path(__file__).resolve().parents[1]          # raíz del sandbox (o del proyecto, tras la migración)
REPO = S.parent if S.name.lower() == "sandbox" else S   # carpeta desde la que se lanzan los pasos
PY = sys.executable
ESTADO_F = S / "pipeline" / "estado.json"
REG_DIR = S / "pipeline" / "registro"
DIAG = S / "data/processed/diagonal"
HIST = S / "data/processed/historico"
sys.path.insert(0, str(S / "imputacion"))
sys.path.insert(0, str(S))

UMBRAL_ROJO = 1.0          # % máximo de importaciones imputadas en rojo por año (puerta de la diagonal)
VENTANA_ANCLAS = 7         # años de historia que usa la regla a (comun / 04_imputar)


# ------------------------------------------------------------------ utilidades
class Registro:
    def __init__(self):
        REG_DIR.mkdir(parents=True, exist_ok=True)
        self.f = open(REG_DIR / f"{dt.datetime.now():%Y%m%d_%H%M%S}.log", "w", encoding="utf-8")

    def __call__(self, *a):
        t = " ".join(str(x) for x in a)
        print(t, flush=True)
        self.f.write(t + "\n"); self.f.flush()


def huella(p: Path) -> str:
    """Huella rápida del contenido: tamaño + sha256 de los primeros y últimos 4 MB."""
    h = hashlib.sha256(); n = p.stat().st_size; h.update(str(n).encode())
    with open(p, "rb") as f:
        h.update(f.read(1 << 22))
        if n > (1 << 23):
            f.seek(-(1 << 22), 2); h.update(f.read())
    return h.hexdigest()[:16]


def huellas(patrones):
    out = {}
    for pat in patrones:
        fs = sorted(S.glob(pat))
        if not fs:
            out[pat] = None
        for f in fs:
            out[str(f.relative_to(S)).replace("\\", "/")] = huella(f)
    return out


def leer_estado():
    if ESTADO_F.exists():
        return json.loads(ESTADO_F.read_text(encoding="utf-8"))
    return {"pasos": {}, "motor": {}, "arquitecto": {}}


def guardar_estado(e):
    ESTADO_F.parent.mkdir(parents=True, exist_ok=True)
    ESTADO_F.write_text(json.dumps(e, indent=1, ensure_ascii=False), encoding="utf-8")


def ejecutar(cmd, log, env=None, capturar=False):
    log("   $", " ".join(str(c) for c in cmd))
    r = subprocess.run([str(c) for c in cmd], cwd=REPO, env=env, text=True,
                       capture_output=capturar, encoding="utf-8", errors="replace")
    if capturar:
        for l in (r.stdout or "").splitlines()[-25:]:
            log("     ", l)
        if r.returncode != 0:
            for l in (r.stderr or "").splitlines()[-25:]:
                log("   !", l)
    return r


def anios_icio():
    return sorted(int(p.name.split("_")[0]) for p in (S / "data/raw/ICIO").glob("*_SML.csv"))


# ------------------------------------------------------------------ pasos de la diagonal (E3)
PASOS = [
    {"id": "mapeo", "desc": "Mapeo 170 industrias -> ICIO (00)",
     "entradas": ["data/aux/sector_mapping_original.csv", "imputacion/00_mapeo_sectores.py"],
     "salidas": ["data/aux/sector_mapping_idee.csv"],
     "cmds": lambda: [[PY, S / "imputacion/00_mapeo_sectores.py"]]},
    {"id": "icio", "desc": "Producción doméstica OCDE ICIO (01)",
     "entradas": ["data/raw/ICIO/*_SML.csv", "imputacion/01_icio_domestica.py"],
     "salidas": ["data/processed/diagonal/icio_domestica_*.parquet"],
     "cmds": lambda: [[PY, S / "imputacion/01_icio_domestica.py", *[a for a in anios_icio() if a >= 2009]]]},
    {"id": "itpd", "desc": "Diagonal, exportaciones e importaciones ITPD-E (02)",
     "entradas": ["data/raw/ITP/ITPD_E_R03/*.gz", "imputacion/02_itpd_extraer.py"],
     "salidas": ["data/processed/diagonal/itpd_agregados.parquet"],
     "cmds": lambda: [[PY, S / "imputacion/02_itpd_extraer.py", "parte", i] for i in range(10)]
                     + [[PY, S / "imputacion/02_itpd_extraer.py", "combinar"]]},
    {"id": "energia", "desc": "Statistical Review of World Energy (02b)",
     "entradas": ["data/raw/Statistical Review of World Energy*.xlsx", "imputacion/02b_energia_extraer.py"],
     "salidas": ["data/processed/energia/ei_narrow.parquet"],
     "cmds": lambda: [[PY, S / "imputacion/02b_energia_extraer.py"]]},
    {"id": "imputacion", "desc": "Imputación, ajustes, controles y decisiones (04, 04b, 05, 06)",
     "entradas": ["data/aux/sector_mapping_idee.csv", "data/aux/traduccion_industrias_IDEE_ES_EN.csv",
                  "data/processed/diagonal/icio_domestica_*.parquet", "data/processed/diagonal/itpd_agregados.parquet",
                  "data/processed/energia/ei_narrow.parquet", "imputacion/comun.py", "imputacion/04_imputar.py",
                  "imputacion/04b_ajustes.py", "imputacion/05_controles.py", "imputacion/06_decisiones_rojos.py"],
     "salidas": ["data/processed/diagonal/diagonal_20??.parquet", "data/processed/diagonal/diagonal_detalle_20??.parquet",
                 "data/processed/diagonal/controles_celdas.parquet", "comparacion/DECISIONES_ROJOS.csv"],
     "cmds": lambda: [[PY, S / f"imputacion/{f}"] for f in
                      ["04_imputar.py", "04b_ajustes.py", "05_controles.py", "06_decisiones_rojos.py"]]},
]
CODIGO_MOTOR = ["idee_diagonal.py", "idee_paths.py", "notebooks/analysis/00_dependency.ipynb",
                "notebooks/analysis/00_dependency_ue.ipynb", "herramientas/ejecutar_motor.py"]
CODIGO_ARQ = ["notebooks/analysis/idc_architect.py"]
VERSIONES = {"global": "", "ue": "_UE"}


def paso_pendiente(p, estado):
    """Devuelve (pendiente, motivo)."""
    actual = huellas(p["entradas"])
    faltan_ent = [k for k, v in actual.items() if v is None]
    if faltan_ent:
        return True, f"faltan entradas: {faltan_ent}"
    if not all(list(S.glob(o)) for o in p["salidas"]):
        return True, "faltan salidas"
    previo = estado["pasos"].get(p["id"], {}).get("entradas")
    if previo is None:
        return True, "sin registro de ejecución"
    cambios = sorted(set(k for k in actual if actual.get(k) != previo.get(k)) | (set(previo) - set(actual)))
    if cambios:
        return True, "cambian: " + ", ".join(cambios[:6]) + (" …" if len(cambios) > 6 else "")
    return False, "al día"


# ------------------------------------------------------------------ E1 inventario
def e1_inventario(log, anios):
    log("\nE1 · Inventario de fuentes")
    import comun
    problemas = []
    ic = anios_icio()
    log(f"   OCDE ICIO: {ic[0]}-{ic[-1]} ({len(ic)} años)")
    ag = DIAG / "itpd_agregados.parquet"
    if ag.exists():
        import pandas as pd
        y = sorted(pd.read_parquet(ag, columns=["year"]).year.unique())
        log(f"   ITPD-E (extracción actual): {y[0]}-{y[-1]}")
    else:
        y = []; log("   ITPD-E: sin extraer todavía")
    ei = S / "data/processed/energia/ei_narrow.parquet"
    if ei.exists():
        import pandas as pd
        e = pd.read_parquet(ei, columns=["Year"]); log(f"   Energy Institute: {e.Year.min()}-{e.Year.max()}")
    else:
        log("   Energy Institute: sin extraer todavía")
    log(f"   Serie de la diagonal (comun.ANIOS): {comun.ANIOS[0]}-{comun.ANIOS[-1]}")
    fuera = [a for a in anios if a not in comun.ANIOS]
    if fuera:
        problemas.append(f"años pedidos fuera de comun.ANIOS {fuera}: hay que ampliar la serie de la diagonal")
    sin_icio = [a for a in range(min(anios) - VENTANA_ANCLAS, max(anios) + 1) if a not in ic and a >= 2009]
    if sin_icio:
        problemas.append(f"faltan tablas ICIO para {sin_icio} (la regla a usa hasta {VENTANA_ANCLAS} años de historia)")
    if y and [a for a in anios if a not in y]:
        problemas.append(f"la extracción ITPD-E no tiene {[a for a in anios if a not in y]}")
    for p in problemas:
        log("   ✗", p)
    if not problemas:
        log("   ✓ fuentes completas para los años pedidos")
    return problemas


# ------------------------------------------------------------------ E2 diagnóstico
def e2_diagnostico(log):
    log("\nE2 · Diagnóstico de la diagonal (parte de las importaciones mundiales)")
    import comun, pandas as pd
    if not (DIAG / "itpd_agregados.parquet").exists():
        log("   (pendiente de la extracción ITPD-E)"); return
    a = comun.itpd_creible(comun.mapeo_y_bloques())
    a = a[a.year.isin(comun.ANIOS) & (a.M > 0)]
    g = a.assign(obs=a.M.where(a.D > 0, 0), cre=a.M.where((a.D > 0) & a.creible, 0),
                 res=(a.D > 0) & ~a.creible).groupby("year").agg(M=("M", "sum"), obs=("obs", "sum"), cre=("cre", "sum"),
                                                                 residuos=("res", "sum"))
    log("   año   observada   creíble   a completar   residuos (celdas)")
    for y, r in g.iterrows():
        log(f"   {y}   {100*r.obs/r.M:6.1f} %   {100*r.cre/r.M:6.1f} %   {100*(1-r.cre/r.M):6.1f} %      {int(r.residuos):,}")


# ------------------------------------------------------------------ E3 diagonal
def puerta_diagonal(log):
    import pandas as pd, comun
    fallos = []
    d = pd.read_csv(S / "comparacion/DECISIONES_ROJOS.csv")
    n_r = int((d.causa.astype(str) == "REVISAR").sum()) if "causa" in d else 0
    if n_r:
        fallos.append(f"{n_r} celdas en rojo sin decisión (comparacion/DECISIONES_ROJOS.csv)")
    c = pd.read_parquet(DIAG / "controles_celdas.parquet", columns=["year", "imp", "semaforo", "M"])
    c = c[c.imp]
    rojo = (c[c.semaforo == "rojo"].groupby("year").M.sum() / c.groupby("year").M.sum() * 100).reindex(comun.ANIOS).fillna(0)
    for y, v in rojo.items():
        if v > UMBRAL_ROJO:
            fallos.append(f"{y}: {v:.2f} % de las importaciones imputadas en rojo (máximo {UMBRAL_ROJO} %)")
    log("   rojo por año (%):", ", ".join(f"{y} {v:.1f}" for y, v in rojo.items()))
    for y in comun.ANIOS:
        f = DIAG / f"diagonal_{y}.parquet"
        try:
            t = pd.read_parquet(f)
            if t.trade.isna().any() or (t.trade <= 0).any() or len(t) < 20000:
                fallos.append(f"diagonal_{y}: valores no válidos o demasiado pocas filas ({len(t)})")
        except Exception as e:
            fallos.append(f"diagonal_{y} ilegible: {e}")
    # legibilidad con el pyarrow del motor
    import pyarrow
    if int(pyarrow.__version__.split(".")[0]) <= 19:
        log(f"   ✓ ficheros leídos con pyarrow {pyarrow.__version__} (el del motor)")
    else:
        log(f"   · pyarrow {pyarrow.__version__}: la compatibilidad con el motor la garantiza comun.guardar_parquet_compatible")
    for f in fallos:
        log("   ✗", f)
    return fallos


def e3_diagonal(log, estado, ejecutar_):
    log("\nE3 · Construcción de la diagonal")
    pend = []
    for p in PASOS:
        necesita, motivo = paso_pendiente(p, estado)
        # si un paso anterior se rehace, la imputación también
        if p["id"] == "imputacion" and pend:
            necesita, motivo = True, motivo if motivo != "al día" else f"se rehacen {pend}"
        log(f"   {'→ REHACER' if necesita else '✓ al día  '}  {p['desc']}: {motivo}")
        if necesita:
            pend.append(p["id"])
    if not pend:
        return [], False
    if not ejecutar_:
        return [], True
    for p in PASOS:
        if p["id"] not in pend:
            continue
        log(f"   ▶ {p['desc']}")
        for cmd in p["cmds"]():
            # el pipeline corre en el mismo entorno que el motor: la diagonal se escribe con su mismo pyarrow
            r = ejecutar(cmd, log, env=dict(os.environ, IDEE_MISMO_ENTORNO_MOTOR="1"), capturar=True)
            if r.returncode != 0:
                return [f"falló {p['id']}: {' '.join(map(str, cmd))}"], True
        estado["pasos"][p["id"]] = {"entradas": huellas(p["entradas"]), "fecha": f"{dt.datetime.now():%Y-%m-%d %H:%M}"}
        guardar_estado(estado)
    log("   Puerta de calidad de la diagonal")
    return puerta_diagonal(log), True


# ------------------------------------------------------------------ E4-E6 motor y arquitecto
def clave_motor(y):
    return {"diagonal": huella(DIAG / f"diagonal_{y}.parquet") if (DIAG / f"diagonal_{y}.parquet").exists() else None,
            "codigo": huellas(CODIGO_MOTOR)}


def e4_afectados(log, estado, anios):
    log("\nE4 · Años afectados")
    motor, arq = [], []
    for y in anios:
        k = clave_motor(y)
        for v, suf in VERSIONES.items():
            prev = estado["motor"].get(f"{y}|{v}")
            if prev is None:
                motivo = "sin registro"
            elif prev.get("diagonal") != k["diagonal"]:
                motivo = "ha cambiado la diagonal"
            elif prev.get("codigo") != k["codigo"]:
                motivo = "ha cambiado el código del motor"
            else:
                motivo = None
            if motivo:
                motor.append((y, v)); log(f"   → motor {y} {v}: {motivo}")
        salidas_ok = all((HIST / f"profiles_{y}{suf}.parquet").exists() for suf in VERSIONES.values())
        prev = estado["arquitecto"].get(str(y))
        if any(m[0] == y for m in motor) or not salidas_ok or prev is None or prev.get("codigo") != huellas(CODIGO_ARQ):
            arq.append(y); log(f"   → arquitecto {y}")
    if not motor and not arq:
        log("   ✓ todos los años están al día")
    return motor, arq


def e5_motor(log, estado, motor):
    log("\nE5 · Motor")
    env = dict(os.environ, IDEE_DIAGONAL="1")
    r = ejecutar([PY, S / "herramientas/comprobar_entorno.py"], log, env=env, capturar=True)
    if r.returncode != 0 or "TODO CORRECTO" not in (r.stdout or ""):
        return ["la comprobación previa del entorno no termina en TODO CORRECTO"]
    for y, v in motor:
        t0 = dt.datetime.now()
        r = ejecutar([PY, S / "herramientas/ejecutar_motor.py", y, v], log, env=env, capturar=True)
        if r.returncode != 0 or "EJECUCIÓN VÁLIDA" not in (r.stdout or ""):
            return [f"motor {y} {v}: ejecución no válida (ver registro)"]
        estado["motor"][f"{y}|{v}"] = {**clave_motor(y), "fecha": f"{dt.datetime.now():%Y-%m-%d %H:%M}",
                                       "minutos": round((dt.datetime.now() - t0).seconds / 60, 1)}
        guardar_estado(estado)
    return []


def e6_arquitecto(log, estado, arq):
    log("\nE6 · Arquitecto")
    if not arq:
        log("   nada que hacer"); return []
    args = [a for y in arq for a in (str(y), f"{y}_UE")]
    r = ejecutar([PY, S / "notebooks/analysis/idc_architect.py", *args], log, env=dict(os.environ, IDEE_DIAGONAL="1"), capturar=True)
    if r.returncode != 0 or f"PROCESO COMPLETADO PARA {arq[-1]}_UE" not in (r.stdout or ""):
        return ["el arquitecto no terminó correctamente"]
    for y in arq:
        estado["arquitecto"][str(y)] = {"codigo": huellas(CODIGO_ARQ), "fecha": f"{dt.datetime.now():%Y-%m-%d %H:%M}"}
    guardar_estado(estado)
    return []


# ------------------------------------------------------------------ E7 verificación
def e7_verificacion(log, anios):
    log("\nE7 · Verificación")
    import pyarrow
    if int(pyarrow.__version__.split(".")[0]) < 21:
        log(f"   ✗ pyarrow {pyarrow.__version__} no lee los entregables publicados: la comparación necesita pyarrow >= 21")
        return ["verificación no realizada (pyarrow < 21)"]
    fallos = []
    for y in anios:
        for script in ["comparacion/comparar_con_produccion.py", "comparacion/revision_anio.py",
                       "comparacion/auditoria_exportadores.py"]:
            r = ejecutar([PY, S / script, y], log, capturar=True)
            if r.returncode != 0:
                fallos.append(f"{script} {y} terminó con error")
    r = ejecutar([PY, S / "visor/exportar_datos.py", *anios], log, capturar=True)
    if r.returncode != 0:
        fallos.append("no se pudieron regenerar los datos del visor")
    return fallos


# ------------------------------------------------------------------ registro del estado actual
def registrar_estado(log, anios):
    """Da por buenas las salidas actuales (diagonal, motor y arquitecto). Solo tras una validación completa."""
    e = leer_estado()
    for p in PASOS:
        e["pasos"][p["id"]] = {"entradas": huellas(p["entradas"]), "fecha": "registrado"}
    for y in anios:
        for v, suf in VERSIONES.items():
            if not (HIST / f"profiles_{y}{suf}.parquet").exists():
                log(f"   ✗ faltan salidas de {y} {v}: no se registra"); continue
            e["motor"][f"{y}|{v}"] = {**clave_motor(y), "fecha": "registrado"}
        e["arquitecto"][str(y)] = {"codigo": huellas(CODIGO_ARQ), "fecha": "registrado"}
    guardar_estado(e)
    log(f"   estado registrado en {ESTADO_F.relative_to(S)}")


# ------------------------------------------------------------------ principal
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ejecutar", action="store_true", help="ejecuta (por defecto solo planifica)")
    ap.add_argument("--hasta", choices=["diagonal", "motor", "arquitecto", "verificacion"], default="verificacion")
    ap.add_argument("--anios", default=None, help="p. ej. 2016-2022 o 2019,2022 (por defecto, la serie de la diagonal)")
    ap.add_argument("--registrar-estado", action="store_true")
    ap.add_argument("--forzar", action="store_true", help="rehace todo, ignorando el estado (certificación desde cero)")
    ap.add_argument("--rehacer-anios", default="", help="fuerza motor y arquitecto de esos años (p. ej. 2022)")
    a = ap.parse_args()
    import comun
    if a.anios:
        anios = []
        for parte in a.anios.split(","):
            x = parte.split("-"); anios += list(range(int(x[0]), int(x[-1]) + 1))
    else:
        anios = list(comun.ANIOS)
    log = Registro()
    modo = "EJECUCIÓN" if a.ejecutar else "PLAN (no se ejecuta nada)"
    log(f"IDEE · pipeline · {dt.datetime.now():%Y-%m-%d %H:%M} · {modo} · años {anios[0]}-{anios[-1]} · raíz {S}")
    if a.registrar_estado:
        registrar_estado(log, anios); return 0
    estado = leer_estado() if not a.forzar else {"pasos": {}, "motor": {}, "arquitecto": {}}
    if a.forzar:
        log("   --forzar: se ignora el estado anterior; se rehace todo")

    if e1_inventario(log, anios):
        log("\nPARADA en E1: fuentes incompletas."); return 2
    e2_diagnostico(log)
    fallos, cambio_diag = e3_diagonal(log, estado, a.ejecutar)
    if fallos:
        log("\nPARADA en E3:", *fallos); return 2
    if a.hasta == "diagonal":
        log("\nFin (hasta diagonal)."); return 0
    if cambio_diag and not a.ejecutar:
        log("\nE4 · Años afectados: se determinarán cuando se rehaga la diagonal (en el plan se dan por afectados todos)")
        motor, arq = [(y, v) for y in anios for v in VERSIONES], anios
    else:
        if a.rehacer_anios:
            forz = [int(x) for x in a.rehacer_anios.split(",")]
            for y in forz:
                for v in VERSIONES:
                    estado["motor"].pop(f"{y}|{v}", None)
                estado["arquitecto"].pop(str(y), None)
            log(f"   --rehacer-anios: se fuerzan motor y arquitecto de {forz}")
        motor, arq = e4_afectados(log, estado, anios)
    if not a.ejecutar:
        horas = sum(0.75 if v == "global" else 0.5 for _, v in motor)
        log(f"\nPLAN: {len(motor)} ejecuciones del motor (≈ {horas:.1f} h), arquitecto para {arq or 'ningún año'}, "
            f"verificación de {anios[0]}-{anios[-1]}. Para ejecutar: añadir --ejecutar.")
        return 0
    if motor and (f := e5_motor(log, estado, motor)):
        log("\nPARADA en E5:", *f); return 2
    if a.hasta == "motor":
        return 0
    if (f := e6_arquitecto(log, estado, arq)):
        log("\nPARADA en E6:", *f); return 2
    if a.hasta == "arquitecto":
        return 0
    f = e7_verificacion(log, anios)
    log("\nRESULTADO:", "VÁLIDO" if not f else "CON AVISOS: " + "; ".join(f))
    return 0 if not f else 1


if __name__ == "__main__":
    sys.exit(main())

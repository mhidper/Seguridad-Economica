"""
Comprobación previa obligatoria antes de cualquier cálculo (sandbox o proyecto).

Uso (desde la raíz del repositorio):
    python herramientas/comprobar_entorno.py   (en el sandbox: sandbox/herramientas/...)

Termina con "TODO CORRECTO" o con la lista de fallos. Si hay fallos, no se calcula nada.
"""
import hashlib
import importlib
import sys
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[1]     # raíz del cálculo: el sandbox o, tras la migración, el proyecto
PROD = SANDBOX.parent
ES_SANDBOX = SANDBOX.name.lower() == "sandbox"
fallos = []


def sha256(p, bloque=1 << 22):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(bloque):
            h.update(chunk)
    return h.hexdigest()


print("1) Datos brutos" + (" copiados al sandbox" if ES_SANDBOX else " del proyecto"))
for rel in (["data/raw/ITP/ITPD_E_R03", "data/raw/ICIO"] if ES_SANDBOX else []):
    orig = sorted((PROD / rel).glob("*"))
    for f in orig:
        g = SANDBOX / rel / f.name
        if not g.exists():
            fallos.append(f"falta {g.relative_to(SANDBOX)}")
        elif g.stat().st_size != f.stat().st_size:
            fallos.append(f"tamaño distinto: {g.relative_to(SANDBOX)} ({g.stat().st_size} vs {f.stat().st_size})")
        elif sha256(g) != sha256(f):
            fallos.append(f"contenido distinto: {g.relative_to(SANDBOX)}")
        else:
            print(f"   OK  {rel}/{f.name}")

if not ES_SANDBOX:
    for rel, patron in [("data/raw/ITP/ITPD_E_R03", "*.gz"), ("data/raw/ICIO", "*_SML.csv")]:
        n = len(list((SANDBOX / rel).glob(patron)))
        print(f"   {'OK ' if n else 'FALTA'} {rel}: {n} ficheros")
        if not n:
            fallos.append(f"faltan los datos brutos de {rel}")

print("2) Raíz del proyecto e interruptor")
sys.path.insert(0, str(SANDBOX))
import idee_paths  # noqa: E402
import idee_diagonal  # noqa: E402
if idee_paths.idee_root() != SANDBOX:
    fallos.append(f"idee_root() no apunta a la raíz del cálculo: {idee_paths.idee_root()}")
print(f"   interruptor USAR_DIAGONAL_IMPUTADA = {idee_diagonal.USAR_DIAGONAL_IMPUTADA}")
if idee_diagonal.USAR_DIAGONAL_IMPUTADA:
    faltan = [a for a in range(2016, 2023) if not idee_diagonal.ruta_diagonal(a).exists()]
    if faltan:
        fallos.append(f"interruptor encendido pero faltan ficheros de diagonal para: {faltan}")
    else:
        print("   OK  ficheros diagonal_2016..2022.parquet presentes")
        # lectura REAL con el pyarrow de este entorno (el mismo que usará el motor)
        import pandas as _pd, pyarrow as _pa
        for a in range(2016, 2023):
            try:
                _d = _pd.read_parquet(idee_diagonal.ruta_diagonal(a))
                assert {"iso3", "industry_id", "trade", "fuente"} <= set(_d.columns) and len(_d) > 0
                print(f"   OK  diagonal_{a}.parquet legible con pyarrow {_pa.__version__} ({len(_d):,} filas)")
            except Exception as e:
                fallos.append(f"diagonal_{a}.parquet NO se puede leer con pyarrow {_pa.__version__}: {e}")

print("3) Copias de scripts sin rutas a producción")
for rel in ["notebooks/analysis/00_dependency.ipynb", "notebooks/analysis/00_dependency_ue.ipynb",
            "notebooks/analysis/idc_architect.py"]:
    t = (SANDBOX / rel).read_text(encoding="utf-8")
    if "cwd().parent.parent" in t or 'p.name == "Seguridad Economica"' in t or 'base_path.name != "Seguridad Economica"' in t:
        fallos.append(f"{rel} conserva rutas que apuntan a producción")
    else:
        print(f"   OK  {rel}")

print("4) Paquetes de Python")
for m in ["pandas", "numpy", "pyarrow", "dask", "torch", "joblib", "tqdm", "scipy", "nbformat", "nbclient", "ipykernel"]:
    try:
        importlib.import_module(m)
        print(f"   OK  {m}")
    except ImportError:
        fallos.append(f"falta el paquete {m}")

print("5) Entorno de Python (producción usó el entorno «dependencias», Python 3.12.9, GPU RTX 4060)")
print(f"   ejecutable: {sys.executable}")
print(f"   versión:    {sys.version.split()[0]}")
if not sys.version.startswith("3.12"):
    fallos.append(f"versión de Python {sys.version.split()[0]}; producción usó 3.12.9 (¿está activado el entorno «dependencias»?)")
try:
    import torch
    gpu = torch.cuda.is_available()
    print(f"   torch {torch.__version__} | GPU disponible: {gpu}" + (f" ({torch.cuda.get_device_name(0)})" if gpu else ""))
    if not gpu:
        fallos.append("torch no ve la GPU; producción calculó con GPU y la línea base no sería comparable")
except ImportError:
    pass

print()
if fallos:
    print("FALLOS:")
    for x in fallos:
        print("   -", x)
    sys.exit(1)
print("TODO CORRECTO")

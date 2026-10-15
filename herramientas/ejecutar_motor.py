"""
Ejecuta el motor del sandbox para un año sin editar el notebook.

Uso (desde cualquier carpeta):
    py sandbox/herramientas/ejecutar_motor.py 2019 global
    py sandbox/herramientas/ejecutar_motor.py 2019 ue

Qué hace:
  1. Lee sandbox/notebooks/analysis/00_dependency(.ipynb | _ue.ipynb).
  2. Sustituye en memoria la línea `anio = ...` por el año pedido.
  3. Lo ejecuta con la carpeta de trabajo sandbox/notebooks/analysis.
  4. Guarda el notebook ejecutado (con todas sus salidas) en sandbox/ejecuciones/.
El notebook original del sandbox no se modifica.
Requisitos: pip install nbformat nbclient ipykernel
"""
import os
import re
import sys
import time
from pathlib import Path

try:
    import nbformat
    from nbclient import NotebookClient
except ImportError:
    sys.exit("Faltan paquetes. Ejecuta: pip install nbformat nbclient ipykernel")

SANDBOX = Path(__file__).resolve().parents[1]
CARPETA = SANDBOX / "notebooks" / "analysis"
NOTEBOOKS = {"global": "00_dependency.ipynb", "ue": "00_dependency_ue.ipynb"}

if len(sys.argv) != 3 or sys.argv[2].lower() not in NOTEBOOKS or not sys.argv[1].isdigit():
    sys.exit("Uso: py sandbox/herramientas/ejecutar_motor.py <AÑO> <global|ue>")
anio, version = int(sys.argv[1]), sys.argv[2].lower()

nb = nbformat.read(CARPETA / NOTEBOOKS[version], as_version=4)
hechos = 0
for c in nb.cells:
    if c.cell_type == "code" and re.search(r"^\s*anio\s*=\s*\d{4}\s*$", c.source, flags=re.M):
        c.source = re.sub(r"^(\s*)anio\s*=\s*\d{4}\s*$", rf"\g<1>anio = {anio}", c.source, flags=re.M)
        hechos += 1
if hechos != 1:
    sys.exit(f"ERROR: se esperaba exactamente una celda con 'anio = AAAA' y hay {hechos}. No se ejecuta nada.")

# Celda de control (solo en memoria): el kernel debe usar el mismo Python que lanza este script
control = nbformat.v4.new_code_cell(
    "import sys, os\n"
    f"_esperado = os.path.normcase(os.path.abspath(r'{sys.executable}'))\n"
    "_real = os.path.normcase(os.path.abspath(sys.executable))\n"
    "print('[control] Python del kernel:', sys.executable, '| cwd:', os.getcwd())\n"
    "assert _real == _esperado, f'El kernel usa otro Python ({_real}); se esperaba {_esperado}'\n"
    f"_diag_esperado = {os.environ.get('IDEE_DIAGONAL', '0')!r}\n"
    "print('[control] IDEE_DIAGONAL en el kernel:', os.environ.get('IDEE_DIAGONAL', '0'))\n"
    "assert os.environ.get('IDEE_DIAGONAL', '0') == _diag_esperado, 'El interruptor no ha llegado al kernel'\n")
nb.cells.insert(0, control)

sys.path.insert(0, str(SANDBOX))
import idee_diagonal  # noqa: E402  (solo para informar del estado del interruptor)
print(f"[ejecutar_motor] Año {anio} | versión {version} | interruptor diagonal = {idee_diagonal.USAR_DIAGONAL_IMPUTADA}")

t0 = time.time()
salida = SANDBOX / "ejecuciones" / f"{Path(NOTEBOOKS[version]).stem}_{anio}_diag{'ON' if idee_diagonal.USAR_DIAGONAL_IMPUTADA else 'OFF'}.ipynb"
salida.parent.mkdir(exist_ok=True)
detenida = None
try:
    NotebookClient(nb, timeout=None, kernel_name="python3",
                   resources={"metadata": {"path": str(CARPETA)}}).execute()
    print(f"[ejecutar_motor] OK en {(time.time()-t0)/60:.1f} min")
except Exception as e:   # p. ej. DiagonalNoAplicada: el notebook se detiene en la celda que falla
    detenida = str(e).strip().splitlines()[-1] if str(e).strip() else type(e).__name__
    print(f"[ejecutar_motor] Ejecución detenida tras {(time.time()-t0)/60:.1f} min")
finally:
    nbformat.write(nb, salida)
    print(f"[ejecutar_motor] Notebook ejecutado guardado en {salida}")

# ---- Validación de la ejecución: el notebook captura errores con try/except y puede seguir sin avisar ----
texto = ""
for c in nb.cells:
    for o in c.get("outputs", []):
        if o.get("output_type") == "stream":
            texto += "".join(o.get("text", ""))
problemas = [l for l in texto.splitlines() if "Error en la ejecución principal" in l or "Error durante el procesamiento" in l]
if detenida:
    problemas.insert(0, f"ejecución detenida por error: {detenida}")
esperada = f"[idee_diagonal] {anio}: diagonales observadas" if idee_diagonal.USAR_DIAGONAL_IMPUTADA else "[idee_diagonal] Interruptor apagado"
if esperada not in texto:
    problemas.append(f"no aparece la línea esperada «{esperada}…»")
if problemas:
    invalido = salida.with_name(salida.stem + "_NO_VALIDA.ipynb")
    salida.replace(invalido)
    print("\n[ejecutar_motor] *** EJECUCIÓN NO VÁLIDA *** (notebook renombrado a " + invalido.name + ")")
    for p_ in problemas:
        print("   -", p_)
    sys.exit(2)
print(f"[ejecutar_motor] EJECUCIÓN VÁLIDA: diagonal {'aplicada' if idee_diagonal.USAR_DIAGONAL_IMPUTADA else 'apagada (línea base)'} y sin errores capturados")

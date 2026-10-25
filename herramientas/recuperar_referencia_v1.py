"""
Recupera la copia de referencia de los entregables publicados antes de la versión 2 (la que tenía IBM), que las
verificaciones usan como «versión publicada anterior» (idee_paths.historico_referencia).

Origen: la etiqueta de git v1-sin-diagonal. Destino: data/processed/_archivo/historico_v1_sin_diagonal/ (git la ignora).
Uso, desde la raíz del repositorio:  python herramientas/recuperar_referencia_v1.py
"""
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DEST = RAIZ / "data/processed/_archivo/historico_v1_sin_diagonal"
DEST.mkdir(parents=True, exist_ok=True)
nombres = subprocess.run(["git", "ls-tree", "--name-only", "v1-sin-diagonal", "data/processed/historico/"],
                         cwd=RAIZ, capture_output=True, text=True, check=True).stdout.split()
n = 0
for ruta in nombres:
    if not ruta.endswith(".parquet"):
        continue
    datos = subprocess.run(["git", "show", f"v1-sin-diagonal:{ruta}"], cwd=RAIZ, capture_output=True, check=True).stdout
    (DEST / Path(ruta).name).write_bytes(datos)
    n += 1
(DEST / "LEEME.md").write_text(
    "# Entregables publicados antes de la versión 2 (sin diagonal completada)\n\n"
    "Copia exacta de data/processed/historico en la etiqueta git v1-sin-diagonal. Es la referencia con la que comparan\n"
    "las verificaciones (idee_paths.historico_referencia). No se modifica.\n", encoding="utf-8")
print(f"{n} ficheros recuperados en {DEST}" + ("" if n == 98 else "  ¡ATENCIÓN: se esperaban 98!"))

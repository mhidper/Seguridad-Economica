"""
idee_paths.py — Resolución única de la raíz del proyecto IDEE.

La raíz es la carpeta que contiene este fichero. Así, el mismo código funciona
sin cambios en el sandbox (sandbox/idee_paths.py -> raíz = sandbox) y, tras la
sustitución, en el proyecto principal (idee_paths.py en la raíz del repo).

Uso en notebooks y scripts:
    from pathlib import Path; import sys
    sys.path.insert(0, str(next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "idee_paths.py").exists())))
    from idee_paths import idee_root
"""
import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent


def idee_root() -> Path:
    """Raíz del proyecto (carpeta que contiene idee_paths.py)."""
    return _ROOT


def es_sandbox() -> bool:
    return _ROOT.name.lower() == "sandbox"


def historico_referencia() -> Path:
    """Carpeta con los entregables de la versión publicada anterior, contra la que se comparan los resultados nuevos.

    - En el sandbox: los entregables del proyecto principal (lo que tiene IBM hoy).
    - En el proyecto: la copia archivada de la versión anterior, data/processed/_archivo/historico_v1_sin_diagonal.
    - La variable de entorno IDEE_REFERENCIA, si existe, tiene prioridad.
    """
    if os.environ.get("IDEE_REFERENCIA"):
        return Path(os.environ["IDEE_REFERENCIA"])
    if es_sandbox():
        return _ROOT.parent / "data" / "processed" / "historico"
    return _ROOT / "data" / "processed" / "_archivo" / "historico_v1_sin_diagonal"


def comprobar_dentro(ruta) -> Path:
    """Lanza un error si una ruta de escritura queda fuera de la raíz."""
    r = Path(ruta).resolve()
    if _ROOT not in r.parents and r != _ROOT:
        raise PermissionError(f"Escritura fuera de la raíz IDEE bloqueada: {r} (raíz: {_ROOT})")
    return r


print(f"[idee_paths] raíz del proyecto: {_ROOT}{'  (SANDBOX)' if es_sandbox() else ''}")

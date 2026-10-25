"""
Trocea el CSV completo de la ITPD-E R03 (descargado de la USITC) en las 10 partes comprimidas que usa el proyecto:
data/raw/ITP/ITPD_E_R03/ITPD_E_R03.csv.parte{0..9}.gz, de 810 MB cada una sin comprimir (los mismos cortes que la
función comprimir_dividir_archivo de notebooks/analysis/00_dependency.ipynb, pero leyendo por bloques, sin cargar el
fichero entero en memoria).

Uso, desde la raíz del repositorio:  python herramientas/trocear_itpd.py "C:/ruta/a/ITPDE_R03.csv"
"""
import gzip, sys
from pathlib import Path

TAM = 810 * 1024 * 1024
BLOQUE = 64 * 1024 * 1024
origen = Path(sys.argv[1])
destino = Path(__file__).resolve().parents[1] / "data/raw/ITP/ITPD_E_R03"
destino.mkdir(parents=True, exist_ok=True)
with open(origen, "rb") as f:
    i = 0
    while True:
        pendiente, escrito = TAM, 0
        primero = f.read(min(BLOQUE, pendiente))
        if not primero:
            break
        with gzip.open(destino / f"ITPD_E_R03.csv.parte{i}.gz", "wb") as g:
            datos = primero
            while datos:
                g.write(datos); escrito += len(datos); pendiente -= len(datos)
                datos = f.read(min(BLOQUE, pendiente)) if pendiente > 0 else b""
        print(f"parte {i}: {escrito / 1e6:,.0f} MB")
        i += 1
print(f"{i} partes en {destino}" + ("" if i == 10 else "  (el proyecto tenía 10; revisa que el CSV sea el completo)"))

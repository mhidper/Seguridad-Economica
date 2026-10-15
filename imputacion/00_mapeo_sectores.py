"""
00_mapeo_sectores.py — Mapeo corregido de las 170 industrias ITPD-E a sectores OCDE ICIO.

Parte de data/aux/sector_mapping_original.csv (copia de metodología/cvg-idc/output/sector_mapping.csv)
y corrige las asignaciones que no respetan la correspondencia CIIU Rev.3 (ITPD-E) → CIIU Rev.4 (ICIO).
Un código compuesto ("H49+H50+...") significa la suma de esos sectores ICIO.
Salida: data/aux/sector_mapping_idee.csv
"""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from idee_paths import idee_root

R = idee_root()
m = pd.read_csv(R / "data/aux/sector_mapping_original.csv", sep=";")

CAMBIOS = {
    5:  ("C10T12", "Productos derivados de cereales: manufactura alimentaria (CIIU 106-107), no cultivo"),
    8:  ("C10T12", "Piensos y alimentos para animales: manufactura (CIIU 108)"),
    10: ("C10T12", "Otros edulcorantes (glucosa, jarabes): manufactura (CIIU 106/107)"),
    14: ("C10T12", "Frutas preparadas y zumos: manufactura (CIIU 103)"),
    15: ("C10T12", "Hortalizas preparadas: manufactura (CIIU 103)"),
    30: ("B05", "Lignito: CIIU Rev.4 05 (carbón y lignito), no 06 (petróleo y gas)"),
    33: ("B08", "Otras minas y canteras: CIIU Rev.4 08"),
    73: ("J58T60", "Edición de libros: en CIIU Rev.4 la edición pasa a la sección J (58)"),
    74: ("J58T60", "Edición de periódicos: CIIU Rev.4 58"),
    75: ("J58T60", "Edición de soportes grabados: CIIU Rev.4 59"),
    76: ("J58T60", "Otras actividades de edición: CIIU Rev.4 58"),
    81: ("C20", "Combustible nuclear: en CIIU Rev.4 pasa mayoritariamente a química básica (2011)"),
    91: ("C22", "Neumáticos: caucho y plásticos es C22 en ICIO"),
    92: ("C22", "Otros productos de caucho: C22"),
    93: ("C22", "Productos de plástico: C22"),
    94: ("C23", "Vidrio: CIIU Rev.4 231, dentro de minerales no metálicos (C23)"),
    121: ("C25", "Armas y municiones: CIIU Rev.4 252, productos metálicos (C25)"),
    123: ("C27", "Electrodomésticos: CIIU Rev.4 275, material eléctrico (C27)"),
    156: ("H49+H50+H51+H52+H53", "Transporte (balanza de pagos): todos los modos, no solo terrestre"),
    162: ("J61+J62_63", "Telecomunicaciones, informática e información: J61 + J62-63"),
    163: ("M+N", "Otros servicios empresariales: profesionales (M) y administrativos (N)"),
    169: ("G", "Servicios relacionados con el comercio: comercio mayorista y minorista (G)"),
}

m["icio_original"] = m["icio_code"]
m["cambio"] = False
m["motivo"] = ""
for i, (cod, mot) in CAMBIOS.items():
    k = m["industry_id"] == i
    assert k.sum() == 1, i
    m.loc[k, ["icio_code", "cambio", "motivo"]] = [cod, True, mot]

NOTAS = {
    134: "Ambiguo: material médico se reparte en CIIU Rev.4 entre 266 (C26) y 325 (C31T33); se mantiene C26",
    154: "Servicios de manufactura sobre insumos ajenos: sin equivalente directo; se asocia a manufacturas diversas y reparación (C31T33)",
    155: "Mantenimiento y reparación: C33 está dentro de C31T33",
    157: "Viajes (balanza de pagos): gasto de no residentes; contraparte doméstica más próxima, hostelería (I)",
    161: "Cargos por propiedad intelectual: sin sector propio; se asocia a servicios profesionales y científicos (M)",
    167: "Bienes y servicios del gobierno n.c.o.p.: administración pública (O)",
    168: "Servicios no asignados: partida residual; se asocia a otros servicios (S)",
}
for i, n in NOTAS.items():
    m.loc[m["industry_id"] == i, "motivo"] = n

m = m[["industry_id", "industry_descr", "icio_code", "icio_original", "cambio", "motivo"]]
out = R / "data/aux/sector_mapping_idee.csv"
m.to_csv(out, index=False, encoding="utf-8")
print(f"{m.cambio.sum()} cambios; {m.icio_code.nunique()} códigos ICIO (simples o compuestos). Guardado en {out}")

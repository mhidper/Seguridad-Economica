"""
06_decisiones_rojos.py — Ninguna celda en rojo sin decisión.

Cada serie país-industria con alguna celda en rojo tras 05_controles.py se asigna a una causa con una decisión:
  A  Mayor productor mundial      C7/C6 en un país que está entre los 3 mayores exportadores de la industria:
                                   superar el máximo de los países con dato es esperable. -> Se acepta.
  B  Cambio real en la ICIO       C4 cuando la propia producción doméstica ICIO del bloque cambia más de x2 o /2
                                   ese año (p. ej. cierre de la refinería de Nueva Zelanda, 2022). -> Se acepta.
  C  Dato de partida volátil      reglas a / a0 / a-ROW: el salto o la distancia vienen de la diagonal observada
                                   de la ITPD que sirve de ancla, no de la imputación. -> Se acepta.
  D  Economía pequeña / sin ICIO  reglas e / e+país: volatilidad del comercio de economías pequeñas. -> Se acepta.
  I  Energía fuera de ICIO       la producción de las estadísticas energéticas se aparta del dato ITPD del propio país
                                  (bajo o volátil); se prefiere la fuente sectorial. -> Se acepta.
  H  Cociente de la industria     regla b pura con salto interanual por el cambio del cociente mediano de otros
                                  países (pocos países observados). -> Se acepta (inmaterial; se documenta).
  E  Bloque sin referencia        C2 por debajo de la escala del bloque en industrias sin diagonal observada
                                   suficiente (p. ej. edición, J58T60). -> Se acepta.
  F  Exceso por lo observado      C2 (y el salto C4 que puede acompañarlo) en celdas ya reducidas por el ajuste 4
                                   (sufijo -bloque): el exceso lo causan las diagonales observadas, que no se
                                   modifican. -> Se acepta.
  G  Tope de seguridad activo     C4 en series empalmadas topadas a 1,5 x el sector ICIO completo: sin el tope el
                                   valor sería imposible; el salto es el mal menor. -> Se acepta.
  R  Revisar                      cualquier otra combinación: revisión individual obligatoria.
Salida: comparacion/DECISIONES_ROJOS.csv y resumen en pantalla.
"""
from comun import *

C = pd.read_parquet(DIAG / "controles_celdas.parquet")
ag = pd.read_parquet(DIAG / "itpd_agregados.parquet")
xa = ag[ag.year.isin(ANIOS)].copy()
xa["rk"] = xa.groupby(["industry_id", "year"]).X.rank(ascending=False, method="first")
top3 = set(zip(xa.pais[xa.rk <= 3], xa.industry_id[xa.rk <= 3]))
S = C.sort_values(["iso3", "industry_id", "year"]).copy()
S["DI_yoy"] = S.DI / S.groupby(["iso3", "industry_id"]).DI.shift(1)
R = S[S.imp & (S.semaforo == "rojo")]


def causa(f):
    fallos = set(f.fallos.split(","))
    base = f.fuente.split("-")[0]
    if fallos & {"C7", "C6"} and (f.iso3, f.industry_id) in top3 and fallos <= {"C6", "C7", "C4"}:
        return "A"
    if fallos <= {"C4", "C6"} and (f.DI_yoy > 2 or f.DI_yoy < 0.5):
        return "B"
    if base in ("a", "a0") or f.fuente.startswith("a-ROW"):
        return "C"
    if base in ("e", "e+país"):
        return "D"
    if fallos <= {"C2", "C6", "C7"} and f.ratio_bloque < 0.5:
        return "E"
    if "-empalme" in f.fuente and f.fuente.endswith("-bloque") and fallos <= {"C4", "C6"}:
        return "G"
    if fallos <= {"C2", "C4", "C6", "C7"} and f.fuente.endswith("-bloque"):
        return "F"
    if f.fuente == "en" and fallos <= {"C3", "C4", "C5", "C6"}:
        return "I"                                 # estadística energética frente al dato ITPD del propio país
    if base == "b" and fallos <= {"C4", "C6"} and f.fuente == "b":
        return "H"                                 # salto del cociente mediano de la industria entre años
    return "R"


R = R.assign(causa=R.apply(causa, axis=1))
DESC = {"A": "Mayor productor mundial", "B": "Cambio real en la ICIO", "C": "Dato de partida volátil (ITPD)",
        "D": "Economía pequeña / fuera de ICIO", "E": "Bloque sin referencia",
        "H": "Cambio del cociente mediano de la industria (regla b)",
        "I": "Estadística energética frente al dato ITPD (fuera de ICIO)",
        "F": "Exceso del bloque por diagonales observadas", "G": "Tope de seguridad activo", "R": "REVISAR"}
tab = R.groupby("causa").agg(celdas=("M", "size"), series=("industry_id", lambda s: R.loc[s.index].groupby(["iso3", "industry_id"]).ngroups),
                             M=("M", "sum"))
tab["% M imputado"] = (tab.M / C[C.imp].M.sum() * 100).round(3)
tab.index = [f"{k} {DESC[k]}" for k in tab.index]
print(tab.drop(columns="M").to_string())
out = R[["iso3", "industry_id", "industria", "year", "fuente", "M", "trade", "sig", "fallos", "ratio_bloque", "yoy", "DI_yoy", "causa"]]
out = out.assign(decision=out.causa.map(lambda k: "revisión individual" if k == "R" else "aceptada"), causa=out.causa.map(DESC))
out.sort_values(["decision", "M"], ascending=[False, False]).to_csv(R_ := (R_DIR := idee_root() / "comparacion") / "DECISIONES_ROJOS.csv", index=False)
pend = out[out.decision == "revisión individual"].sort_values("M", ascending=False)
pd.set_option("display.width", 250, "display.max_colwidth", 30)
print(f"\nCeldas a revisar: {len(pend)}")
print(pend.head(25).round(3).to_string(index=False))

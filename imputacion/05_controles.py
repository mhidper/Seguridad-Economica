"""
05_controles.py — Batería de controles de calidad de la diagonal imputada, con semáforo por celda.

Controles (umbrales fijos, decididos antes de ver resultados):
  C1 validez        valor finito y > 0                                              rojo si falla
  C2 suma bloque    suma de diagonales (observadas + imputadas) del país en el bloque / (kappa_B x producción
                    doméstica ICIO), con kappa_B la escala ITPD/ICIO típica del bloque. amarillo fuera de [0,5; 2]; rojo > 3
  C3 dato propio    imputado / dato observado más próximo del propio país (<= 7 años)
                    amarillo fuera de [0,5; 2]; rojo fuera de [0,2; 5]
  C4 continuidad    cociente interanual de la serie 2016-2022 cuando interviene una celda imputada
                    amarillo fuera de [0,5; 2]; rojo fuera de [0,2; 5]
  C5 cuota          |cambio de D/(D+M)| frente al último observado del país: amarillo > 15 pp; rojo > 30 pp
  C6 plausibilidad  cuota D/(D+M) imputada fuera de los percentiles 1-99 de las observadas en la industria: amarillo
  C7 magnitud       imputado frente al máximo mundial observado en la industria (si hay >= 10 países con dato):
                    amarillo > 1,5 x; rojo > 5 x
                    (el máximo excluye a los países sin dato, p. ej. China, por eso no es rojo directamente)
  C2 no se aplica a celdas ancladas a la historia propia (a, a0, a-ROW, empalmes): se contrastan con C3 y C5.
  Materialidad: C2, C3, C4 y C7 solo cuentan si el valor alternativo de referencia cambia la cuota doméstica
  D/(D+M) en 5 puntos o más; si no, el cociente extremo no afecta al índice y la celda queda en verde.
Salidas: data/processed/diagonal/controles_celdas.parquet y comparacion/INFORME_CONTROLES_DIAGONAL.md
"""
from comun import *

m = mapeo_y_bloques()
nom = pd.read_csv(R / "data/aux/traduccion_industrias_IDEE_ES_EN.csv", encoding="utf-8-sig").set_index("industry_id").industry_name_es
det = pd.concat([pd.read_parquet(DIAG / f"diagonal_detalle_{t}.parquet") for t in ANIOS], ignore_index=True)
ag = pd.read_parquet(DIAG / "itpd_agregados.parquet")
_cr = itpd_creible(m)
obsall = _cr[(_cr.D > 0) & _cr.creible][["pais", "industry_id", "year", "D", "X", "M"]]   # solo diagonales creíbles
det["sig"] = det.trade / (det.trade + det.M)
C = det.copy()
C["imp"] = C.fuente != "observada"
imp = C["imp"]

# C1
C["C1"] = np.where(np.isfinite(C.trade) & (C.trade > 0), "verde", "rojo")

# C2: suma del bloque (todas las diagonales observadas del país, también de industrias sin importaciones, + imputadas)
obs_b = obsall[obsall.year.isin(ANIOS)].merge(m[["industry_id", "bloque"]], on="industry_id").rename(columns={"pais": "iso3"})
obs_b = obs_b.groupby(["iso3", "bloque", "year"]).D.sum().rename("Dobs_bloque")
imp_b = C[imp].groupby(["iso3", "bloque", "year"]).trade.sum().rename("Dimp_bloque")
ref = C[imp].groupby(["iso3", "bloque", "year"]).agg(DI=("DI", "first"))
blq = pd.concat([obs_b, imp_b, ref], axis=1).dropna(subset=["Dimp_bloque", "DI"])
blq = blq[blq.DI > 0]
kB = pd.read_csv(DIAG / "parametros_kappa_bloque.csv", index_col=0).kappa_B
blq["kappa_B"] = blq.index.get_level_values("bloque").map(kB).fillna(1.0)
blq["ratio_bloque"] = (blq.Dobs_bloque.fillna(0) + blq.Dimp_bloque) / (blq.kappa_B * blq.DI)
C = C.join(blq[["ratio_bloque"]], on=["iso3", "bloque", "year"])
C["C2"] = np.select([C.ratio_bloque > 3, (C.ratio_bloque < 0.5) | (C.ratio_bloque > 2)], ["rojo", "amarillo"], "verde")
# Las celdas ancladas a la historia propia (a, a0, a-ROW, empalmes) conservan la relación ITPD/ICIO del propio país;
# se contrastan con su dato observado (C3, C5), no con la escala típica del bloque.
C.loc[C.fuente.isin(["a", "a0", "a-ROW"]) | C.fuente.str.endswith("-empalme"), "C2"] = "verde"

# C3 y C5: dato observado más próximo del propio país (solo diagonales creíbles: comun.PHI_COHERENCIA)
obs_cr = obsall
o = obs_cr.rename(columns={"pais": "iso3", "year": "tau", "D": "Dtau", "M": "Mtau"})[["iso3", "industry_id", "tau", "Dtau", "Mtau"]]
p = C[imp][["iso3", "industry_id", "year"]].reset_index().merge(o, on=["iso3", "industry_id"])
p = p[(p.tau - p.year).abs().between(1, 7)]
p["d"] = (p.tau - p.year).abs()
p = p.sort_values(["d", "tau"]).groupby("index").first()
C = C.join(p[["tau", "Dtau", "Mtau"]])
C["ratio_propio"] = C.trade / C.Dtau
C["dsig_propio"] = (C.sig - C.Dtau / (C.Dtau + C.Mtau)).abs()
r = C.ratio_propio
C["C3"] = np.select([(r < 0.2) | (r > 5), (r < 0.5) | (r > 2)], ["rojo", "amarillo"], "verde")
C["C5"] = np.select([C.dsig_propio > 0.30, C.dsig_propio > 0.15], ["rojo", "amarillo"], "verde")

# C4: continuidad temporal (se calcula en una copia ordenada y se reincorpora por índice)
S = C.sort_values(["iso3", "industry_id", "year"])
g = S.groupby(["iso3", "industry_id"])
prev_t, prev_y, prev_imp = g.trade.shift(1), g.year.shift(1), g.imp.shift(1)
yoy = (S.trade / prev_t).where((prev_y == S.year - 1) & (S.imp | (prev_imp == True)))
C["yoy"] = yoy.reindex(C.index)
C["C4"] = np.select([(C.yoy < 0.2) | (C.yoy > 5), (C.yoy < 0.5) | (C.yoy > 2)], ["rojo", "amarillo"], "verde")

# C6: plausibilidad de la cuota doméstica
so = det[det.fuente == "observada"].groupby("industry_id").sig.quantile([0.01, 0.99]).unstack()
C = C.join(so.rename(columns={0.01: "sig_p01", 0.99: "sig_p99"}), on="industry_id")
C["C6"] = np.where(C.imp & ((C.sig < C.sig_p01) | (C.sig > C.sig_p99)), "amarillo", "verde")

# C7: magnitud frente al máximo mundial observado
gmx = obsall.groupby("industry_id").agg(Dmax_mundo=("D", "max"), n_paises=("pais", "nunique"))
mx = gmx.Dmax_mundo.where(gmx.n_paises >= 10)   # solo si la industria tiene diagonal observada en >= 10 países
C = C.join(mx, on="industry_id")
C["C7"] = np.select([C.imp & (C.trade > 5 * C.Dmax_mundo), C.imp & (C.trade > 1.5 * C.Dmax_mundo)], ["rojo", "amarillo"], "verde")

# Materialidad: cuota doméstica con el valor alternativo de referencia de cada control
sig_alt = lambda D: D / (D + C.M)
alt = {"C2": C.trade / C.ratio_bloque.clip(lower=1e-9),            # valor que dejaría el bloque en su escala típica
       "C3": C.Dtau,                                                # dato propio observado más próximo
       "C4": C.trade / C.yoy,                                       # valor del año anterior
       "C7": 1.5 * C.Dmax_mundo}                                     # máximo mundial observado x 1,5
for k, v in alt.items():
    inmaterial = (C.sig - sig_alt(v)).abs() < 0.05
    C.loc[inmaterial.fillna(False) & (C[k] != "verde"), k] = "verde"

ctrl = ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]
for k in ctrl:
    C.loc[~C.imp, k] = "verde"           # las observadas no se evalúan (no se modifican)
orden = {"verde": 0, "amarillo": 1, "rojo": 2}
C["semaforo"] = C[ctrl].apply(lambda col: col.map(orden)).max(axis=1).map({v: k for k, v in orden.items()})
C["fallos"] = C[ctrl].apply(lambda f: ",".join(k for k in ctrl if f[k] != "verde"), axis=1)
C["industria"] = C.industry_id.map(nom)
C.to_parquet(comprobar_dentro(DIAG / "controles_celdas.parquet"), index=False)

# ---------- Resúmenes ----------
I = C[C.fuente != "observada"]
tab = I.pivot_table(index="fuente", columns="semaforo", values="M", aggfunc="sum").fillna(0)
tab = (tab.div(tab.sum(1), axis=0) * 100).round(1)
cnt = I.pivot_table(index="fuente", columns="semaforo", values="M", aggfunc="size").fillna(0).astype(int)
porctl = pd.DataFrame({k: [(I[k] == "amarillo").sum(), (I[k] == "rojo").sum()] for k in ctrl}, index=["amarillo", "rojo"]).T
print("Celdas imputadas por fuente y semáforo (número):\n", cnt.to_string())
print("\n% de las importaciones de cada fuente por semáforo:\n", tab.to_string())
print("\nFallos por control (número de celdas):\n", porctl.to_string())
print("\nSemáforo por año (% importaciones de celdas imputadas):")
print((I.pivot_table(index="year", columns="semaforo", values="M", aggfunc="sum").pipe(lambda d: d.div(d.sum(1), axis=0)) * 100).round(1).to_string())


# ---------- Informe en Markdown ----------
casos = [("SAU", 31, "Arabia Saudí · crudo y gas"), ("ITA", 50, "Italia · vinos"), ("USA", 35, "EE. UU. · gas por tubería"),
         ("BRA", 17, "Brasil · bovino vivo"), ("MEX", 165, "México · salud"), ("MEX", 34, "México · electricidad"),
         ("RUS", 32, "Rusia · mineral de hierro"), ("RUS", 81, "Rusia · combustible nuclear")]
filas = []
for iso, i, n in casos:
    for y in (2019, 2022):
        r = C[(C.iso3 == iso) & (C.industry_id == i) & (C.year == y)]
        if len(r):
            r = r.iloc[0]
            filas.append(f"| {n} | {y} | {r.fuente} | {r.M:,.0f} | {r.trade:,.0f} | {100*r.sig:.1f} % | {r.semaforo} |")
rojos = I[I.semaforo == "rojo"].sort_values("M", ascending=False).head(40)
md = ["# Controles de la diagonal imputada", "",
      "Generado por `imputacion/05_controles.py`. Umbrales y definiciones en la cabecera del script.", "",
      "## Celdas imputadas por fuente y semáforo (% de las importaciones de cada fuente)", "", tab.to_markdown(), "",
      "## Semáforo por año (% de las importaciones de celdas imputadas)", "",
      (I.pivot_table(index="year", columns="semaforo", values="M", aggfunc="sum").pipe(lambda d: d.div(d.sum(1), axis=0)) * 100).round(1).to_markdown(), "",
      "## Fallos por control (número de celdas)", "", porctl.to_markdown(), "",
      "## Casos señalados por los revisores", "", "| Caso | Año | Fuente | Importaciones (M$) | Diagonal (M$) | Cuota doméstica | Semáforo |",
      "|---|---|---|---|---|---|---|", *filas, "",
      "## Las 40 celdas en rojo con más importaciones (todas los años)", "",
      rojos[["iso3", "industry_id", "industria", "year", "fuente", "M", "trade", "sig", "Dtau", "tau", "ratio_bloque", "yoy", "fallos"]]
      .round(3).to_markdown(index=False)]
(R / "comparacion" / "INFORME_CONTROLES_DIAGONAL.md").write_text("\n".join(md), encoding="utf-8")
print("Informe: comparacion/INFORME_CONTROLES_DIAGONAL.md")

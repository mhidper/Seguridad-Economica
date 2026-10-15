"""
03b_backtest_anclas_antiguas.py — ¿Mejoran las anclas anteriores a 2016 a la regla b?

Se toman celdas observadas en 2016-2021 y se finge que solo hay datos hasta 2015 (situación de China):
  regla a con anclas <= 2015 (hasta 3, ponderadas por 1/distancia, distancia <= 7 años)  frente a
  regla b (cociente mediano de otros países del año x ICIO del bloque) en las MISMAS celdas.
Se mide el error en la cuota doméstica D/(D+M) ponderado por importaciones, por distancia al ancla más cercana.
Salida: data/processed/diagonal/backtest_anclas_antiguas.csv
"""
from comun import *

m = mapeo_y_bloques()
sec2b = {s: b for b in m.bloque.unique() for s in b.split("+")}
ic = pd.concat(pd.read_parquet(DIAG / f"icio_domestica_{y}.parquet") for y in range(2009, 2023))
ic = ic[ic.sector.isin(sec2b)].assign(bloque=lambda d: d.sector.map(sec2b))
ic = ic.groupby(["pais", "bloque", "year"], as_index=False).domestica.sum().rename(columns={"domestica": "DI"})
icio_p = set(ic.pais) - {"ROW"}
a = pd.read_parquet(DIAG / "itpd_agregados.parquet").merge(m[["industry_id", "bloque", "macro"]], on="industry_id")
a = a[a.pais.isin(icio_p)].merge(ic, on=["pais", "bloque", "year"], how="left")
ob = a[(a.D > 0) & (a.DI > 0)].copy()
ob["rho"] = ob.D / ob.DI

objetivo = ob[ob.year.between(2016, 2021) & (ob.M > 0)][["pais", "industry_id", "year", "D", "M", "DI", "macro"]]
anc = ob[ob.year <= 2015][["pais", "industry_id", "year", "rho"]].rename(columns={"year": "tau"})
p = objetivo.merge(anc, on=["pais", "industry_id"])
p["dist"] = p.year - p.tau
p = p[p.dist <= 7].sort_values("dist").groupby(["pais", "industry_id", "year"]).head(3)
p["w"] = 1 / p.dist
g = p.assign(rw=p.rho * p.w).groupby(["pais", "industry_id", "year"]).agg(
    rw=("rw", "sum"), w=("w", "sum"), dmin=("dist", "min"), D=("D", "first"), M=("M", "first"), DI=("DI", "first"),
    macro=("macro", "first")).reset_index()
g["Da"] = g.rw / g.w * g.DI
# regla b en las mismas celdas (mediana de otros países del mismo año)
grp = {k: v for k, v in ob[ob.year.between(2016, 2021)].groupby(["industry_id", "year"])}
g["rho_b"] = [np.median(grp[(i, t)].rho[grp[(i, t)].pais != c]) if (i, t) in grp and (grp[(i, t)].pais != c).sum() >= 3 else np.nan
              for c, i, t in zip(g.pais, g.industry_id, g.year)]
g["Db"] = g.rho_b * g.DI
g = g.dropna(subset=["Da", "Db"])


def err(D, Dh, M):
    return 100 * float(np.average(((D / (D + M)) - (Dh / (Dh + M))).abs(), weights=M))


filas = []
for etiqueta, q in [("todas", g.index == g.index)] + [(f"ancla más cercana a {d} años", g.dmin == d) for d in range(1, 8)] + \
        [(f"macro: {mm}", g.macro == mm) for mm in ["Agricultura", "Manufacturas", "Minería y energía", "Servicios"]]:
    x = g[q]
    if len(x) < 30:
        continue
    filas.append({"subconjunto": etiqueta, "n": len(x), "error_a_anclas_antiguas_pp": err(x.D, x.Da, x.M),
                  "error_b_pp": err(x.D, x.Db, x.M),
                  "a_mejor_en_%_celdas": 100 * float(((x.Da / (x.Da + x.M) - x.D / (x.D + x.M)).abs() <
                                                      (x.Db / (x.Db + x.M) - x.D / (x.D + x.M)).abs()).mean())})
r = pd.DataFrame(filas)
r.to_csv(comprobar_dentro(DIAG / "backtest_anclas_antiguas.csv"), index=False)
print(r.round(2).to_string(index=False))

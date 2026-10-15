"""
03c_backtest_sin_diagonal.py — Regla para industrias sin diagonal en NINGÚN país (b-export).

Se simula que cada industria observada no tuviera diagonal en ningún país (se excluye del cálculo de sus propios
parámetros) y se compara, en las celdas observadas de países ICIO (2016-2021):
  (i)   b-export actual: rho = peso de la industria en las exportaciones MUNDIALES del bloque x conversión del bloque
  (ii)  país:  D^ = kappa_B x ICIO_bloque(c) x peso de la industria en las exportaciones DEL PAÍS en el bloque
  (iii) media geométrica de (i) y (ii)
  (iv)  combinada: (ii) si el país exporta la industria; (i) si no la exporta
  (v)   el mayor de (i) y (ii): exportar poco no lleva la diagonal a cero
Métrica: error en la cuota doméstica D/(D+M), ponderado por importaciones (como en 03_backtest).
"""
from comun import *

m = mapeo_y_bloques()
bl = m.set_index("industry_id").bloque
a = pd.read_parquet(DIAG / "itpd_agregados.parquet").merge(m[["industry_id", "bloque", "macro"]], on="industry_id")
ic = pd.concat(pd.read_parquet(DIAG / f"icio_domestica_{y}.parquet") for y in ANIOS)
s2b = {s: b for b in m.bloque.unique() for s in b.split("+")}
ic = ic[ic.sector.isin(s2b)].assign(bloque=lambda d: d.sector.map(s2b)).groupby(["pais", "bloque", "year"], as_index=False).domestica.sum()
a = a[a.year.between(2016, 2021)].merge(ic.rename(columns={"domestica": "DI"}), on=["pais", "bloque", "year"])
kB = pd.read_csv(DIAG / "parametros_kappa_bloque.csv", index_col=0).kappa_B
ob = a[(a.D > 0) & (a.DI > 0)].copy(); ob["rho"] = ob.D / ob.DI
rho_i = ob.groupby("industry_id").rho.median()
xw = a.groupby("industry_id").X.sum(); xsh = xw / xw.groupby(bl.reindex(xw.index)).transform("sum")
q = (rho_i / xsh.reindex(rho_i.index)).replace([np.inf, -np.inf], np.nan)
qb = pd.DataFrame({"q": q, "b": bl.reindex(q.index)})
# conversión del bloque dejando fuera la propia industria
conv_loo = {i: qb[(qb.b == qb.b[i]) & (qb.index != i)].q.median() for i in qb.index}
c = ob[ob.M > 0].copy()
c["D_i"] = c.industry_id.map(lambda i: xsh.get(i, np.nan) * conv_loo.get(i, np.nan)) * c.DI
Xcb = a.groupby(["pais", "bloque", "year"]).X.sum().rename("Xcb")
c = c.join(Xcb, on=["pais", "bloque", "year"])
c["D_ii"] = c.bloque.map(kB).fillna(1) * c.DI * c.X / c.Xcb.replace(0, np.nan)
c["D_iii"] = np.sqrt(c.D_i * c.D_ii)
c["D_iv"] = np.where(c.X > 0, c.D_ii, c.D_i)            # (iv) país si exporta la industria; si no, estructura mundial
c["D_v"] = np.fmax(c.D_i, c.D_ii)                          # (v) el mayor de (i) y (ii)


def err(d, col):
    d = d.dropna(subset=[col]); d = d[d[col] > 0]
    s, sh = d.D / (d.D + d.M), d[col] / (d[col] + d.M)
    return len(d), 100 * float(np.average((s - sh).abs(), weights=d.M)), float(np.median(np.abs(np.log(d[col] / d.D))))


filas = []
for nom, col in [("(i) b-export actual: estructura exportadora MUNDIAL", "D_i"), ("(ii) estructura exportadora DEL PAÍS", "D_ii"),
                 ("(iii) media geométrica de (i) y (ii)", "D_iii"), ("(iv) combinada: (ii) si el país exporta la industria, (i) si no", "D_iv"),
                 ("(v) el mayor de (i) y (ii)", "D_v")]:
    n, e, l = err(c, col)
    filas.append({"regla": nom, "n": n, "error_sigma_pp": round(e, 2), "MALE_log_D": round(l, 3)})
    # solo celdas en las que el país es exportador relevante de la industria (peso > 5 % de sus exportaciones del bloque)
    n2, e2, l2 = err(c[c.X / c.Xcb > 0.05], col)
    filas.append({"regla": nom + " · exportador relevante (>5 % del bloque)", "n": n2, "error_sigma_pp": round(e2, 2), "MALE_log_D": round(l2, 3)})
for nom2, q2 in [("exportador marginal (<1 % del bloque)", (c.X / c.Xcb < 0.01))]:
    for col2 in ["D_ii", "D_iv", "D_v"]:
        n2, e2, l2 = err(c[q2], col2)
        filas.append({"regla": f"{col2} · {nom2}", "n": n2, "error_sigma_pp": round(e2, 2), "MALE_log_D": round(l2, 3)})
n0, e0, l0 = err(c[c.X == 0], "D_i")
filas.append({"regla": "(i) en celdas donde el país NO exporta la industria", "n": n0, "error_sigma_pp": round(e0, 2), "MALE_log_D": round(l0, 3)})
r = pd.DataFrame(filas); r.to_csv(comprobar_dentro(DIAG / "backtest_sin_diagonal.csv"), index=False)
print(r.to_string(index=False))

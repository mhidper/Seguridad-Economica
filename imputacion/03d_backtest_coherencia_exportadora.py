"""
03d_backtest_coherencia_exportadora.py — Prueba de un suelo de coherencia con la especialización exportadora.

Motivo (auditoría de 11-10-2026): en industrias donde un país es gran exportador, algunas diagonales imputadas
(y algunas observadas en el ITPD-E) son residuos minúsculos de restar exportaciones a la producción. Se compara la
diagonal con su referencia exportadora: ref = ICIO_bloque x X(c,i)/X(c,bloque) (peso de la industria en las
exportaciones ITPD-E del país dentro del bloque). Suelo propuesto: D >= phi * ref.

Prueba: celdas observadas de países ICIO, 2016-2021. Se ocultan y se estiman con
 (1) regla b2 (cociente mediano de otros países x ICIO del bloque), con y sin suelo;
 (2) regla a-idw (historia propia, 3 anclas a <= 7 años), con y sin suelo.
Error en sigma = D/(D+M), ponderado por M (como en 03). Se informa también del subconjunto de grandes exportadores
(VCR >= 2 y X >= M y X >= 50, o top-5 mundial con cuota >= 5 %).
Salida: data/processed/diagonal/backtest_coherencia_exportadora.csv
"""
from comun import *

m = mapeo_y_bloques()
a = pd.read_parquet(DIAG / "itpd_agregados.parquet")
a = a[a.year.isin(ANIOS)].merge(m[["industry_id", "bloque", "macro"]], on="industry_id")
ic = icio_bloques(m)
a = a.merge(ic[["pais", "bloque", "year", "domestica"]].rename(columns={"domestica": "DI"}),
            on=["pais", "bloque", "year"], how="left")
a["ref"] = ref_exportadora(a)
# especialización exportadora
a["Xw_i"] = a.groupby(["industry_id", "year"]).X.transform("sum")
a["X_c"] = a.groupby(["pais", "year"]).X.transform("sum")
a["Xw"] = a.groupby("year").X.transform("sum")
a["RCA"] = (a.X / a.X_c) / (a.Xw_i / a.Xw)
a["rk"] = a.groupby(["industry_id", "year"]).X.rank(ascending=False, method="min")
a["gran"] = ((a.RCA >= 2) & (a.X >= a.M) & (a.X >= 50)) | ((a.rk <= 5) & (a.X / a.Xw_i >= 0.05))
icio_paises = set(pd.read_parquet(DIAG / "icio_domestica_2019.parquet").pais) - {"ROW"}
obs = a[(a.D > 0) & (a.DI > 0) & a.pais.isin(icio_paises)].copy()
obs["rho"] = obs.D / obs.DI
obs["anom"] = obs.D / obs.ref


def metricas(nombre, df, pred):
    d = df.assign(Dh=pred).dropna(subset=["Dh"])
    d = d[d.Dh > 0]
    s, sh = d.D / (d.D + d.M), d.Dh / (d.Dh + d.M)
    w = d.M.where(d.M > 0, 0)
    e = (s - sh).abs()
    out = {"regla": nombre, "n": len(d), "error_sigma_pp": 100 * float(np.average(e, weights=w)),
           "MALE_log_D": float(np.median(np.abs(np.log(d.Dh / d.D))))}
    g = d.gran
    out.update({"n_gran": int(g.sum()), "error_sigma_pp_gran": 100 * float(np.average(e[g], weights=w[g])),
                "sesgo_sigma_pp_gran": 100 * float(np.average((sh - s)[g], weights=w[g])),
                "n_resto": int((~g).sum()), "error_sigma_pp_resto": 100 * float(np.average(e[~g], weights=w[~g]))})
    return out


def suelo(df, pred, phi):
    return np.maximum(pred, (phi * df.ref).fillna(0)) if phi > 0 else pred


ob = obs[obs.year.between(2016, 2021)].copy()
# --- distribución de la anomalía en las celdas observadas ---
q = ob[ob.ref > 0]
print("Cuantiles de D/ref en celdas observadas — grandes exportadores:")
print(q[q.gran].anom.quantile([.01, .05, .1, .25, .5]).round(3).to_dict())
print("— resto:", q[~q.gran].anom.quantile([.01, .05, .1, .25, .5]).round(3).to_dict())

# --- b2 ---
grp = {k: v for k, v in ob.groupby(["industry_id", "year"])}
rho_med = np.full(len(ob), np.nan)
for (i, t), idx in ob.groupby(["industry_id", "year"]).groups.items():
    g = grp[(i, t)]
    for ix in idx:
        v = g.rho[g.pais != ob.at[ix, "pais"]].values
        if len(v) >= 3:
            rho_med[ob.index.get_loc(ix)] = np.median(v)
ob["b2"] = rho_med * ob.DI
# --- a-idw ---
pares = ob[["pais", "industry_id", "year"]].merge(
    obs[["pais", "industry_id", "year", "rho"]].rename(columns={"year": "tau"}), on=["pais", "industry_id"])
pares = pares[(pares.tau != pares.year) & ((pares.tau - pares.year).abs() <= 7)]
pares["dist"] = (pares.tau - pares.year).abs()
pares = pares.sort_values(["dist", "tau"]).groupby(["pais", "industry_id", "year"]).head(3)
pares["w"] = 1.0 / pares.dist
pares["rw"] = pares.rho * pares.w
r = pares.groupby(["pais", "industry_id", "year"]).agg(rw=("rw", "sum"), w=("w", "sum"))
ob = ob.join((r.rw / r.w).rename("r_idw"), on=["pais", "industry_id", "year"])
ob["aidw"] = ob.r_idw * ob.DI

res = []
for phi in [0, 0.02, 0.05, 0.1, 0.2, 0.3]:
    res.append(metricas(f"b2 con suelo phi={phi}", ob, suelo(ob, ob.b2, phi)))
for phi in [0, 0.02, 0.05, 0.1, 0.2, 0.3]:
    res.append(metricas(f"a-idw con suelo phi={phi}", ob, suelo(ob, ob.aidw, phi)))
# a-idw descartando anclas no creíbles (anomalía < phi) y con suelo
for phi in [0.05, 0.1, 0.2]:
    pc = pares.merge(obs[["pais", "industry_id", "year", "anom"]].rename(columns={"year": "tau"}),
                     on=["pais", "industry_id", "tau"])
    pc = pc[~(pc.anom < phi)]
    rc = pc.groupby(["pais", "industry_id", "year"]).agg(rw=("rw", "sum"), w=("w", "sum"))
    pr = ob.join((rc.rw / rc.w).rename("rc"), on=["pais", "industry_id", "year"]).rc * ob.DI
    res.append(metricas(f"a-idw anclas creíbles + suelo phi={phi}", ob, suelo(ob, pr, phi)))
out = pd.DataFrame(res)
out.to_csv(DIAG / "backtest_coherencia_exportadora.csv", index=False)
pd.set_option("display.width", 250)
print(out.round(2).to_string())

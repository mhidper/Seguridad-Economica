"""
03_backtest.py — Elige la regla de imputación con datos reales: se ocultan diagonales observadas,
se estiman con cada variante y se mide el error.

Métrica principal: error absoluto en la cuota doméstica del suministro, sigma = D / (D + M),
ponderado por las importaciones M (es la parte del índice que cambia con la diagonal).
Métrica secundaria: error absoluto mediano en log(D).
Periodo de prueba: 2016-2021 (años con ICIO y diagonales observadas).
Salida: data/processed/diagonal/backtest_reglas.csv
"""
from comun import *

m = mapeo_y_bloques()
a = pd.read_parquet(DIAG / "itpd_agregados.parquet")
a = a[a.year.isin(ANIOS)].merge(m[["industry_id", "bloque", "macro"]], on="industry_id")
ic = icio_bloques(m)
a = a.merge(ic[["pais", "bloque", "year", "domestica"]].rename(columns={"domestica": "DI"}),
            on=["pais", "bloque", "year"], how="left")
obs = a[(a.D > 0) & (a.DI > 0)].copy()
obs["rho"] = obs.D / obs.DI


def metricas(nombre, df, pred):
    d = df.assign(Dh=pred).dropna(subset=["Dh"])
    d = d[d.Dh > 0]
    s, sh = d.D / (d.D + d.M), d.Dh / (d.Dh + d.M)
    w = d.M.where(d.M > 0, 0)
    return {"regla": nombre, "n": len(d), "error_sigma_pp": 100 * float(np.average((s - sh).abs(), weights=w)),
            "error_sigma_pp_mediana": 100 * float((s - sh).abs().median()),
            "MALE_log_D": float(np.median(np.abs(np.log(d.Dh / d.D)))),
            "dentro_25pct": float((np.abs(np.log(d.Dh / d.D)) < np.log(1.25)).mean())}


res = []
# ---------- Regla a): historia propia (ocultar el año t y usar otros años observados a <=7 años) ----------
o = obs[obs.year <= 2021]
pares = o[["pais", "industry_id", "year", "D", "M", "DI"]].merge(
    obs[["pais", "industry_id", "year", "D", "rho"]].rename(columns={"year": "tau", "D": "Dtau"}),
    on=["pais", "industry_id"])
pares = pares[(pares.tau != pares.year) & ((pares.tau - pares.year).abs() <= 7)]
pares["dist"] = (pares.tau - pares.year).abs()
pares = pares.sort_values(["dist", "tau"]).groupby(["pais", "industry_id", "year"]).head(3)
g = pares.groupby(["pais", "industry_id", "year"]).agg(rho=("rho", "mean"), Dniv=("Dtau", "first"),
                                                       D=("D", "first"), M=("M", "first"), DI=("DI", "first")).reset_index()
res.append(metricas("a) cociente propio x ICIO del año (media de 3 años más próximos)", g, g.rho * g.DI))
res.append(metricas("a0) arrastrar el nivel del año más próximo (referencia)", g, g.Dniv))
pares["w"] = 1.0 / pares.dist
g2 = pares.groupby(["pais", "industry_id", "year"]).apply(
    lambda d: pd.Series({"r_near": d.rho.iloc[0], "r_med": d.rho.median(), "r_idw": np.average(d.rho, weights=d.w),
                         "D": d.D.iloc[0], "M": d.M.iloc[0], "DI": d.DI.iloc[0]}), include_groups=False).reset_index()
res.append(metricas("a-cercano) cociente del año observado más próximo", g2, g2.r_near * g2.DI))
res.append(metricas("a-mediana) mediana de los 3 cocientes más próximos", g2, g2.r_med * g2.DI))
res.append(metricas("a-idw) media ponderada por 1/distancia de los 3 más próximos", g2, g2.r_idw * g2.DI))

# ---------- Reglas para celdas sin historia: bloques completos (todas las industrias activas observadas) ----------
act = a[(a.X > 0) | (a.M > 0) | (a.D > 0)]
blk = act.groupby(["pais", "bloque", "year"]).agg(n=("industry_id", "size"), nobs=("D", lambda s: (s > 0).sum()),
                                                  Dsum=("D", "sum")).reset_index()
comp = blk[(blk.n == blk.nobs) & (blk.n >= 2)]
c = act.merge(comp[["pais", "bloque", "year", "Dsum"]], on=["pais", "bloque", "year"])
c = c[c.DI > 0]
# factor de escala ITPD/ICIO por bloque (mediana en bloques completos, excluyendo el propio país)
kap = (comp.merge(ic.rename(columns={"domestica": "DI"}), on=["pais", "bloque", "year"])
       .assign(r=lambda x: x.Dsum / x.DI).query("r > 0"))
kap_b = kap.groupby("bloque").r.median()
kap_m = kap.merge(m[["bloque", "macro"]].drop_duplicates("bloque"), on="bloque").groupby("macro").r.median()
c["kappa"] = c.bloque.map(kap_b).fillna(c.macro.map(kap_m))
# estructura mundial: cuota de la industria en el bloque, con los demás países de bloques completos
tot_i = c.groupby(["industry_id", "year"]).D.sum()
tot_b = c.groupby(["bloque", "year"]).D.sum()
c["W"] = [(tot_i[(i, t)] - d) / max(tot_b[(b, t)] - s, 1e-9) for i, t, b, d, s in
          zip(c.industry_id, c.year, c.bloque, c.D, c.Dsum)]
c["W"] = c.W.clip(lower=0)
for col in ["X", "M"]:
    c[f"sh_{col}"] = c[col] / c.groupby(["pais", "bloque", "year"])[col].transform("sum").replace(0, np.nan)
c["sh_XM"] = (c.X + c.M) / (c.X + c.M).groupby([c.pais, c.bloque, c.year]).transform("sum").replace(0, np.nan)
c["sh_W"] = c.W / c.groupby(["pais", "bloque", "year"]).W.transform("sum").replace(0, np.nan)
c["sh_WX"] = np.sqrt(c.sh_W.fillna(0) * c.sh_X.fillna(0))
c["sh_WX"] = c.sh_WX / c.groupby(["pais", "bloque", "year"]).sh_WX.transform("sum").replace(0, np.nan)
c["sh_WXM"] = np.cbrt(c.sh_W.fillna(0) * c.sh_X.fillna(0) * c.sh_M.fillna(0))
c["sh_WXM"] = c.sh_WXM / c.groupby(["pais", "bloque", "year"]).sh_WXM.transform("sum").replace(0, np.nan)

for w, nom in [("sh_X", "exportaciones"), ("sh_M", "importaciones"), ("sh_XM", "exportaciones+importaciones"),
               ("sh_W", "estructura mundial"), ("sh_WX", "media geom. mundial y exportaciones"),
               ("sh_WXM", "media geom. mundial, export. e import.")]:
    # b-total: sin hermanas observadas -> kappa x ICIO del bloque x cuota
    res.append(metricas(f"b-total) kappa x ICIO x cuota por {nom}", c, c.kappa * c.DI * c[w]))
    # b-hermanas: el resto del bloque observado (dejar uno fuera)
    sw = c.groupby(["pais", "bloque", "year"])[w].transform("sum")
    res.append(metricas(f"b-hermanas) resto del bloque x cuota por {nom}", c,
                        (c.Dsum - c.D) * c[w] / (sw - c[w]).replace(0, np.nan)))

# ---------- Variantes de la estructura mundial ----------
# (1) mediana entre países (menos dominada por los grandes) y (2) inclinada por ventaja comparativa revelada
c["sh_c"] = c.D / c.Dsum
med = {k: g for k, g in c.groupby(["industry_id", "year"]).sh_c}
c["Wmed"] = [float(np.median(np.delete(med[(i, t)].values, list(med[(i, t)].index).index(ix)))) if len(med[(i, t)]) > 1 else np.nan
             for i, t, ix in zip(c.industry_id, c.year, c.index)]
c["sh_Wmed"] = c.Wmed / c.groupby(["pais", "bloque", "year"]).Wmed.transform("sum").replace(0, np.nan)
xw = a.groupby(["industry_id", "year"]).X.sum() / a.groupby(["bloque", "year"]).X.sum().reindex(
    pd.MultiIndex.from_frame(a.drop_duplicates(["industry_id", "year"])[["bloque", "year"]])).values
c["xw"] = [xw.get((i, t), np.nan) for i, t in zip(c.industry_id, c.year)]
c["rca"] = (c.sh_X / c.xw).replace([np.inf, -np.inf], np.nan).fillna(0)
for beta in [0.25, 0.5]:
    v = c.sh_W.fillna(0) * (c.rca + 0.01) ** beta
    c[f"sh_Wrca{beta}"] = v / v.groupby([c.pais, c.bloque, c.year]).transform("sum").replace(0, np.nan)
    res.append(metricas(f"b-total) kappa x ICIO x estructura mundial x VCR^{beta}", c, c.kappa * c.DI * c[f"sh_Wrca{beta}"]))
res.append(metricas("b-total) kappa x ICIO x estructura mundial (mediana entre países)", c, c.kappa * c.DI * c.sh_Wmed))

# ---------- Residuo del bloque: total ICIO escalado menos las hermanas observadas ----------
resid = c.kappa * c.DI - (c.Dsum - c.D)
res.append(metricas("b-residuo) kappa x ICIO menos hermanas observadas (si > 0)", c, resid.where(resid > 0)))
res.append(metricas("b-residuo-acotado) residuo limitado a [0.5, 2] x estructura mundial", c,
                    resid.clip(lower=0.5 * c.kappa * c.DI * c.sh_Wmed, upper=2 * c.kappa * c.DI * c.sh_Wmed)))

# ---------- Regla d) países fuera de la ICIO: cuota doméstica mediana de la industria en otros países ----------
icio_paises = set(pd.read_parquet(DIAG / "icio_domestica_2019.parquet").pais) - {"ROW"}
ob = a[(a.D > 0) & (a.M > 0)].copy()
ob["sig"] = ob.D / (ob.D + ob.M)
ob["en_icio"] = ob.pais.isin(icio_paises)
for grupo, nom in [(False, "fuera de la ICIO"), (True, "en la ICIO")]:
    gq = ob[ob.en_icio == grupo]
    tot = gq.groupby(["industry_id", "year"]).sig
    med = {k: v.values for k, v in tot}
    sh = np.array([np.median(np.delete(med[(i, t)], np.where(med[(i, t)] == sg)[0][:1])) if len(med[(i, t)]) > 1 else np.nan
                   for i, t, sg in zip(gq.industry_id, gq.year, gq.sig)])
    res.append(metricas(f"d) cuota doméstica mediana de la industria ({nom})", gq, sh / (1 - sh) * gq.M))

# ---------- Países fuera de la ICIO: el sector "ROW" de la ICIO hace de total ----------
row = ic[ic.pais == "ROW"].rename(columns={"domestica": "DIrow"})[["bloque", "year", "DIrow"]]
fu = a[~a.pais.isin(icio_paises)].merge(row, on=["bloque", "year"], how="left")
fo = fu[(fu.D > 0) & (fu.DIrow > 0)].copy()
fo["rho"] = fo.D / fo.DIrow
pr = fo[fo.year <= 2021][["pais", "industry_id", "year", "D", "M"]].merge(
    fo[["pais", "industry_id", "year", "rho", "D"]].rename(columns={"year": "tau", "D": "Dtau"}), on=["pais", "industry_id"])
pr = pr[(pr.tau != pr.year) & ((pr.tau - pr.year).abs() <= 7)]
pr["dist"] = (pr.tau - pr.year).abs()
pr = pr.sort_values(["dist", "tau"]).groupby(["pais", "industry_id", "year"]).head(3)
gg = pr.groupby(["pais", "industry_id", "year"]).agg(rho=("rho", "mean"), Dniv=("Dtau", "first"), D=("D", "first"),
                                                     M=("M", "first")).reset_index()
gg = gg.merge(row.merge(m[["industry_id", "bloque"]], on="bloque")[["industry_id", "year", "DIrow"]], on=["industry_id", "year"])
res.append(metricas("a-ROW) historia propia x crecimiento del resto del mundo ICIO", gg, gg.rho * gg.DIrow))
res.append(metricas("a0-ROW) arrastrar el nivel (referencia)", gg, gg.Dniv))
# sin historia: parte del país en el resto del mundo (por comercio del bloque) x estructura mundial
fu["XM"] = fu.X + fu.M
tb = fu.groupby(["bloque", "year"])[["X", "M", "XM"]].transform("sum")
cb = fu.groupby(["pais", "bloque", "year"])[["X", "M", "XM"]].transform("sum")
wmed = c.groupby(["industry_id", "year"]).sh_c.median().rename("wm")
fu = fu.merge(wmed, on=["industry_id", "year"], how="left")
fu["wm"] = fu.wm / fu.groupby(["pais", "bloque", "year"]).wm.transform("sum").replace(0, np.nan)
fu["kappa"] = fu.bloque.map(kap_b).fillna(fu.macro.map(kap_m))
fe = fu[(fu.D > 0) & (fu.M > 0)]
for col, nom in [("M", "importaciones"), ("X", "exportaciones"), ("XM", "comercio total")]:
    parte = (cb.loc[fe.index, col] / tb.loc[fe.index, col])
    res.append(metricas(f"d-ROW) kappa x ROW x parte del país por {nom} x estructura mundial", fe,
                        fe.kappa * fe.DIrow * parte * fe.wm))

# ---------- Modelo de la cuota doméstica (logit) para celdas sin historia ----------
# logit(sigma) = efecto industria + b1 log M_cel + b2 log(1+X_cel) + b3 log M_pais + b4 log X_pais + b5 log(1+D_pais_otras)
# Validación cruzada por grupos de países (5 grupos): el error se mide en países que el modelo no ha visto.
def modelo_sigma(df_fit, df_pred):
    def diseño(d):
        Z = pd.get_dummies(d.industry_id.astype(str), prefix="i", dtype=float)
        Z["lM"] = np.log(d.M); Z["lX"] = np.log1p(d.X)
        Z["lMp"] = np.log(d.Mp); Z["lXp"] = np.log1p(d.Xp)
        return Z
    Zf, Zp = diseño(df_fit), diseño(df_pred)
    Zp = Zp.reindex(columns=Zf.columns, fill_value=0.0)
    y = np.log(df_fit.sig / (1 - df_fit.sig))
    beta, *_ = np.linalg.lstsq(Zf.values, y.values, rcond=None)
    z = Zp.values @ beta
    return 1 / (1 + np.exp(-z))

base = a[(a.M > 0)].copy()
pais_tot = base.groupby(["pais", "year"])[["M", "X"]].sum().rename(columns={"M": "Mp", "X": "Xp"})
base = base.join(pais_tot, on=["pais", "year"])
mo = base[(base.D > 0)].copy()
mo["sig"] = (mo.D / (mo.D + mo.M)).clip(1e-4, 1 - 1e-4)
mo["en_icio"] = mo.pais.isin(icio_paises)
paises = np.array(sorted(mo.pais.unique()))
rng = np.random.default_rng(0)
grupo = dict(zip(paises, rng.integers(0, 5, len(paises))))
mo["g"] = mo.pais.map(grupo)
pred = pd.Series(np.nan, index=mo.index)
for k in range(5):
    pred[mo.g == k] = modelo_sigma(mo[mo.g != k], mo[mo.g == k])
for grupo_icio, nom in [(False, "fuera de la ICIO"), (True, "en la ICIO")]:
    q = mo.en_icio == grupo_icio
    res.append(metricas(f"e) modelo logit de la cuota doméstica, validación por países ({nom})", mo[q],
                        pred[q] / (1 - pred[q]) * mo.M[q]))

# e+país) añade el efecto propio del país, estimado con SUS OTRAS industrias observadas ese año (dejando fuera la celda)
zfull = np.log(pred / (1 - pred))
resid = np.log(mo.sig / (1 - mo.sig)) - zfull
gk = [mo.pais, mo.year]
n_ = resid.groupby(gk).transform("size"); s_ = resid.groupby(gk).transform("sum")
efecto = ((s_ - resid) / (n_ - 1)).where(n_ >= 4)          # al menos 3 industrias hermanas observadas
zp = zfull + efecto.fillna(0)
pp = 1 / (1 + np.exp(-zp))
for grupo_icio, nom in [(False, "fuera de la ICIO"), (True, "en la ICIO")]:
    q = (mo.en_icio == grupo_icio) & efecto.notna()
    res.append(metricas(f"e+país) modelo logit + efecto del país ({nom})", mo[q], pp[q] / (1 - pp[q]) * mo.M[q]))

# ---------- b2) cociente mediano de otros países: D^ = mediana_k(D_k,i / ICIO_k,bloque) x ICIO_c,bloque ----------
# No necesita bloques completos: usa todas las celdas observadas de la industria en otros países ICIO del mismo año.
ob2 = obs[obs.pais.isin(icio_paises) & obs.year.between(2016, 2021)].copy()
grp = {k: v for k, v in ob2.groupby(["industry_id", "year"])}
def med_otros(df):
    out = np.full(len(df), np.nan)
    for (i, t), idx in df.groupby(["industry_id", "year"]).groups.items():
        g = grp.get((i, t))
        if g is None:
            continue
        for j, ix in enumerate(idx):
            v = g.rho[g.pais != df.at[ix, "pais"]].values
            if len(v) >= 3:
                out[df.index.get_loc(ix)] = np.median(v)
    return out
ob2["rho_med"] = med_otros(ob2)
res.append(metricas("b2) cociente mediano de otros países x ICIO del bloque (todas las observadas)", ob2, ob2.rho_med * ob2.DI))
cb = c[c.pais.isin(icio_paises)].copy()
cb["rho_med"] = med_otros(cb.assign(rho=cb.D / cb.DI))
res.append(metricas("b2) ídem, solo en bloques completos (comparable con b-total)", cb, cb.rho_med * cb.DI))
# por macrosector
for mac in ["Agricultura", "Manufacturas", "Minería y energía", "Servicios"]:
    q = ob2.macro == mac
    res.append(metricas(f"b2) ... {mac}", ob2[q], ob2.rho_med[q] * ob2.DI[q]))

# ---------- b2+país) efecto propio del país: mediana de log(rho_c,j / rho_mediano_j) en sus OTRAS industrias observadas ----------
ob2["lr"] = np.log(ob2.rho / ob2.rho_med)
def efecto(df, clave):
    s_ = df.groupby(clave).lr
    tot, n_ = s_.transform("sum"), s_.transform("count")
    # media sin la propia celda (mediana LOO sería más cara; la media recortada se aproxima con clip)
    lr = df.lr.clip(-2, 2)
    tot = lr.groupby([df[k] for k in clave]).transform("sum")
    return ((tot - lr) / (n_ - 1)).where(n_ - 1 >= 3)
ef_b = efecto(ob2, ["pais", "bloque", "year"])
ef_m = efecto(ob2, ["pais", "macro", "year"])
ef = ef_b.fillna(ef_m).fillna(0)
res.append(metricas("b2+país) cociente mediano x efecto del país (bloque o macrosector)", ob2, ob2.rho_med * np.exp(ef) * ob2.DI))
for mac in ["Agricultura", "Manufacturas", "Minería y energía", "Servicios"]:
    q = ob2.macro == mac
    res.append(metricas(f"b2+país) ... {mac}", ob2[q], (ob2.rho_med * np.exp(ef) * ob2.DI)[q]))
res.append(metricas("b2+país) ... solo celdas SIN efecto disponible", ob2[ef == 0], (ob2.rho_med * ob2.DI)[ef == 0]))

# ---------- b3) repartir el total del bloque: kappa_B x ICIO x rho_mediano_i / suma de rho_mediano de las industrias activas ----------
rmed_i = ob2.groupby("industry_id").rho.median()
actb = a[a.pais.isin(icio_paises) & a.year.between(2016, 2021) & ((a.X > 0) | (a.M > 0) | (a.D > 0))].copy()
actb["rt"] = actb.industry_id.map(rmed_i)
actb["rt"] = actb.rt.fillna(actb.groupby("bloque").rt.transform("median"))
den = actb.groupby(["pais", "bloque", "year"]).rt.sum().rename("den")
cov = actb[actb.D > 0].groupby(["pais", "bloque", "year"]).agg(rt_obs=("rt", "sum"), Dobs=("D", "sum"), DI=("DI", "first"))
cov = cov.join(den)
cov["cob"] = cov.rt_obs / cov.den
cov = cov[(cov.cob >= 0.5) & (cov.DI > 0)]
cov["k"] = cov.Dobs / (cov.DI * cov.cob)
kB = cov.groupby(level="bloque").k.median()
ob3 = ob2.join(den, on=["pais", "bloque", "year"])
ob3["rt"] = ob3.industry_id.map(rmed_i)
ob3["kB"] = ob3.bloque.map(kB)
b3 = ob3.kB * ob3.DI * ob3.rho_med / ob3.den
res.append(metricas("b3) kappa_B x ICIO x reparto por rho mediano (todas las observadas)", ob3, b3))
for mac in ["Agricultura", "Manufacturas", "Minería y energía", "Servicios"]:
    q = ob3.macro == mac
    res.append(metricas(f"b3) ... {mac}", ob3[q], b3[q]))
# b3-residuo: total del bloque menos las hermanas observadas, repartido por rho; acotado a [0,5; 2] x b3
sib = ob3.join(cov[["Dobs"]], on=["pais", "bloque", "year"])
dob = actb[actb.D > 0].groupby(["pais", "bloque", "year"]).agg(Dobs_all=("D", "sum"), rt_obs_all=("rt", "sum"))
sib = sib.join(dob, on=["pais", "bloque", "year"])
resto = sib.kB * sib.DI - (sib.Dobs_all - sib.D)
rt_no = sib.den - (sib.rt_obs_all - sib.rt)
b3r = (resto * sib.rt / rt_no).clip(lower=0.5 * b3, upper=2 * b3)
res.append(metricas("b3-residuo) total del bloque menos hermanas observadas, acotado [0,5; 2] x b3", sib, b3r.fillna(b3)))
print("kappa_B (reparto por rho):", kB.round(2).to_dict())

r = pd.DataFrame(res)
r.to_csv(comprobar_dentro(DIAG / "backtest_reglas.csv"), index=False)
pd.set_option("display.width", 200, "display.max_colwidth", 70)
print(r.round(3).to_string(index=False))
print("\nkappa por macrosector:", kap_m.round(2).to_dict())

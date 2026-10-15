"""
04_imputar.py — Construye la diagonal doméstica completa por país-industria-año.

Jerarquía (elegida con 03_backtest.py; error en la cuota doméstica D/(D+M), ponderado por importaciones):
  observada  Diagonal de la ITPD-E. No se modifica nunca.
  a          Historia propia: hasta 3 años observados a <= VENTANA años (anteriores o posteriores) con ICIO
             disponible. rho = D / ICIO_bloque en esos años (media ponderada por 1/distancia); D^ = rho x ICIO_bloque(t).
             Países fuera de la ICIO: se usa el agregado "ROW" de la ICIO.                     (2,5 pp / 4,3 pp)
  b          País ICIO sin historia: D^ = rho_i,t x ICIO_bloque(t), con rho_i,t = mediana entre países ICIO de
             D / ICIO_bloque en los años t-1, t y t+1 (mínimo 3 observaciones; si no, mediana de todos los años).  (9,7 pp)
  b-solo     Industrias sin diagonal en ningún país que forman bloque solas (p. ej. pesca, A03): rho = 1.
  b-export   Industrias sin diagonal en ningún país: D^ = kappa_B x ICIO_bloque(c) x peso de la industria en las
             exportaciones DEL PAÍS en el bloque (media 2016-2022, constante en la serie), si ese peso es >= 1 %; si el país
             no la exporta o es marginal: peso en las exportaciones mundiales del bloque x conversión del bloque.                                                                 (12,4 pp)
  e          País fuera de la ICIO sin historia: modelo logit de la cuota doméstica (efecto industria + tamaño del
             flujo y del país) + efecto propio del país (media de sus residuos 2016-2021, mín. 5 celdas). La cuota
             se acota a los percentiles 1-99 de las observadas en la industria y se aplica a las importaciones
             medias de 3 años (t-1, t, t+1), para no trasladar a la diagonal la volatilidad anual del comercio.
Solo se imputan celdas con importaciones > 0 (si M = 0 la diagonal no interviene en el índice).

Uso: python 04_imputar.py [años]       (por defecto 2016-2022)
Salidas en data/processed/diagonal/:
  diagonal_{año}.parquet          iso3, industry_id, trade, fuente   (lo que lee idee_diagonal.py)
  diagonal_detalle_{año}.parquet  + M, X, bloque, ICIO del bloque, rho, años de anclaje, kappa, peso...
"""
import sys
from comun import *

VENTANA = 7          # antigüedad máxima del dato de partida (años), decidida el 10-10-2026
MAX_ANCLAS = 3

anios = [int(x) for x in sys.argv[1:]] or ANIOS
m = mapeo_y_bloques()
a = pd.read_parquet(DIAG / "itpd_agregados.parquet").merge(m[["industry_id", "bloque", "macro"]], on="industry_id")

# ICIO por bloque para todos los años disponibles (incluidos 2009-2015 si se han descargado)
anios_icio = sorted(int(p.stem.split("_")[-1]) for p in DIAG.glob("icio_domestica_*.parquet"))
sec2b = {s: b for b in m.bloque.unique() for s in b.split("+")}
ic = pd.concat(pd.read_parquet(DIAG / f"icio_domestica_{y}.parquet") for y in anios_icio)
ic = ic[ic.sector.isin(sec2b)].assign(bloque=lambda d: d.sector.map(sec2b))
ic = ic.groupby(["pais", "bloque", "year"], as_index=False).domestica.sum().rename(columns={"domestica": "DI"})
paises_icio = set(ic.pais) - {"ROW"}
row = ic[ic.pais == "ROW"][["bloque", "year", "DI"]].rename(columns={"DI": "DIrow"})
print(f"Años ICIO disponibles: {anios_icio}")

a = a.merge(ic, on=["pais", "bloque", "year"], how="left").merge(row, on=["bloque", "year"], how="left")
a["en_icio"] = a.pais.isin(paises_icio)
a["DIref"] = np.where(a.en_icio, a.DI, a.DIrow)          # total de referencia: propio o ROW
# coherencia exportadora (comun.PHI_COHERENCIA): marca de diagonales observadas poco creíbles
_cr = itpd_creible(m)[["pais", "industry_id", "year", "ref_x", "creible"]]
a = a.merge(_cr, on=["pais", "industry_id", "year"], how="left")
a["creible"] = a.creible.fillna(True).astype(bool)
print(f"Diagonales observadas 2009-2022 poco creíbles (D < {PHI_COHERENCIA} x ICIO_bloque x peso exportador): "
      f"{int(((a.D > 0) & ~a.creible & a.year.between(2009, 2022)).sum())} de {int(((a.D > 0) & a.year.between(2009, 2022)).sum())}")

# ---------- Regla b: cociente mediano de otros países ICIO (estimado con 2016-2021) ----------
# rho_i,t = mediana entre países ICIO de D_c,i,t / ICIO_c,bloque,t   (mínimo 3 países)
ob = a[(a.D > 0) & a.creible & (a.DI > 0) & a.en_icio & a.year.between(2016, 2022)].copy()
ob["rho"] = ob.D / ob.DI
# ventana de 3 años (t-1, t, t+1): el cociente es un parámetro estructural y así no oscila con la muestra de países
ob3 = pd.concat([ob[["pais", "industry_id", "year", "rho"]].assign(year=ob.year + k) for k in (-1, 0, 1)])
g_it = ob3.groupby(["industry_id", "year"]).agg(median=("rho", "median"), paises=("pais", "nunique"))
rho_it = g_it["median"][g_it["paises"] >= 3]     # al menos 3 países distintos en la ventana; si no, mediana 2016-2022
g_i = ob.groupby("industry_id").rho.agg(["median", "size"])
rho_i = g_i["median"][g_i["size"] >= 3]
# Industrias sin diagonal en ningún país ICIO: rho a partir de su peso en las exportaciones mundiales del bloque,
# convertido con la relación mediana rho / peso exportador de las industrias observadas del mismo bloque.
bl = m.set_index("industry_id").bloque
xw = a[a.year.between(2016, 2022)].groupby("industry_id").X.sum()
xsh = xw / xw.groupby(bl.reindex(xw.index)).transform("sum")
conv = (pd.concat([rho_i.rename("r"), xsh.rename("x")], axis=1).dropna()
        .assign(q=lambda d: d.r / d.x.replace(0, np.nan), b=lambda d: bl.reindex(d.index).values)
        .groupby("b").q.median())


solas = set(m.groupby("bloque").industry_id.transform("size").pipe(lambda n: m.industry_id[n == 1]))


def rho_b(i, t):
    if (i, t) in rho_it.index:
        return rho_it[(i, t)], "b"
    if i in rho_i.index:
        return rho_i[i], "b"                      # mediana de otros años
    if i in solas:
        return 1.0, "b-solo"                      # única industria de su bloque: toda la producción doméstica ICIO
    return xsh.get(i, 0) * conv.get(bl[i], np.nan), "b-export"


# Escala ITPD/ICIO por bloque, kappa_B (se usa en el control C2): con bloques observados en >= 50 %
# (cobertura medida con rho mediano), kappa = D observado / (ICIO x cobertura); mediana por bloque.
actb = a[a.en_icio & a.year.between(2016, 2021) & ((a.X > 0) | (a.M > 0) | (a.D > 0))].copy()
actb["rt"] = actb.industry_id.map(rho_i)
actb["rt"] = actb.rt.fillna(actb.groupby("bloque").rt.transform("median"))
den = actb.groupby(["pais", "bloque", "year"]).rt.sum().rename("den")
cov = actb[(actb.D > 0) & actb.creible].groupby(["pais", "bloque", "year"]).agg(rt_obs=("rt", "sum"), Dobs=("D", "sum"), DI=("DI", "first")).join(den)
cov = cov[(cov.rt_obs / cov.den >= 0.5) & (cov.DI > 0)]
kappa_B = (cov.Dobs / (cov.DI * cov.rt_obs / cov.den)).groupby(level="bloque").median().rename("kappa_B")
kappa_B.to_csv(comprobar_dentro(DIAG / "parametros_kappa_bloque.csv"))

# Modelo logit de la cuota doméstica (regla e)
base = a[a.year.between(2016, 2021) & (a.M > 0)].copy()
pt = a.groupby(["pais", "year"])[["M", "X"]].sum().rename(columns={"M": "Mp", "X": "Xp"})


def diseno(d, cols=None):
    Z = pd.get_dummies(d.industry_id.astype(str), prefix="i", dtype=float)
    Z["lM"], Z["lX"] = np.log(d.M.values), np.log1p(d.X.values)
    Z["lMp"], Z["lXp"] = np.log(d.Mp.values), np.log1p(d.Xp.values)
    return Z if cols is None else Z.reindex(columns=cols, fill_value=0.0)


fit = base[base.D > 0].join(pt, on=["pais", "year"])
fit = fit[fit.Mp > 0]
sig = (fit.D / (fit.D + fit.M)).clip(1e-4, 1 - 1e-4)
Zf = diseno(fit)
beta, *_ = np.linalg.lstsq(Zf.values, np.log(sig / (1 - sig)).values, rcond=None)
fit["res"] = np.log(sig / (1 - sig)).values - Zf.values @ beta
# Cota de la regla e: la cuota doméstica imputada no sale del rango observado (percentiles 1-99) de la industria
sig_rango = pd.DataFrame({"p01": sig.groupby(fit.industry_id).quantile(0.01), "p99": sig.groupby(fit.industry_id).quantile(0.99)})

# Efecto propio del país (regla e): media de residuos de TODAS sus celdas observadas 2016-2021 (mín. 5), estable en el tiempo
ep = fit.groupby("pais").res.agg(["mean", "size"])
efecto_pais = ep["mean"][ep["size"] >= 5]
# Importaciones medias de 3 años (t-1, t, t+1) para que la regla e no herede la volatilidad anual de las importaciones
mm = a[["pais", "industry_id", "year", "M"]].copy()
Mmedia = pd.concat([mm.assign(year=mm.year + d) for d in (-1, 0, 1)]).groupby(["pais", "industry_id", "year"]).M.mean().rename("Mmedia")

pt3 = pd.concat([pt.reset_index().assign(year=lambda d: d.year + k) for k in (-1, 0, 1)]).groupby(["pais", "year"])[["Mp", "Xp"]].mean()

# Exportaciones medias 2016-2022 por país-bloque-industria (regla b-export)
xpais = a[a.year.between(2016, 2022)].groupby(["pais", "bloque", "industry_id"]).X.sum() / 7

ENERGIA = energia_referencia()
print(f"Referencia energética: {ENERGIA.pais.nunique()} países con volumen físico (Energy Institute)")

# ---------- Imputación por año ----------
obs_hist = a[(a.D > 0) & a.creible & (a.DIref > 0)][["pais", "industry_id", "year", "D", "DIref"]].rename(
    columns={"year": "tau", "D": "Dtau", "DIref": "DItau"})
for t in anios:
    c = a[(a.year == t) & (a.M > 0)].copy().join(Mmedia, on=["pais", "industry_id", "year"])
    # diagonales observadas creíbles; los residuos poco creíbles se tratan como lagunas (se imputan y el enganche
    # del motor sustituye su valor)
    oc = (c.D > 0) & c.creible
    obs = c[oc].assign(fuente="observada", trade=lambda d: d.D)
    f = c[~oc].copy()
    f["residuo"] = f.D > 0

    # a) historia propia
    h = f[["pais", "industry_id"]].merge(obs_hist, on=["pais", "industry_id"])
    h = h[(h.tau != t) & ((h.tau - t).abs() <= VENTANA)]
    h["dist"] = (h.tau - t).abs()
    h = h.sort_values(["dist", "tau"]).groupby(["pais", "industry_id"]).head(MAX_ANCLAS)
    h["rho"] = h.Dtau / h.DItau
    h["w"] = 1.0 / h.dist                                   # media ponderada por cercanía (mejor variante en 03_backtest)
    h["rw"] = h.rho * h.w
    ha = h.groupby(["pais", "industry_id"]).agg(rw=("rw", "sum"), w=("w", "sum"),
                                                anclas=("tau", lambda s: ",".join(map(str, sorted(s))))).reset_index()
    ha["rho"] = ha.rw / ha.w
    ha = ha.drop(columns=["rw", "w"])
    f = f.merge(ha, on=["pais", "industry_id"], how="left")
    ia = f.rho.notna() & (f.DIref > 0)
    f.loc[ia, "trade"] = f.rho[ia] * f.DIref[ia]
    f.loc[ia, "fuente"] = np.where(f.en_icio[ia], "a", "a-ROW")

    # b) país ICIO sin historia: rho mediano de otros países x ICIO del bloque
    ib = f.trade.isna() & f.en_icio & (f.DI > 0)
    rb = [rho_b(i, t) for i in f.industry_id]
    f["rho_b"] = [x[0] for x in rb]
    f.loc[ib, "trade"] = f.rho_b[ib] * f.DI[ib]
    f.loc[ib, "fuente"] = [rb[k][1] for k in np.where(ib)[0]]
    # b-export con la estructura exportadora DEL PAÍS (03c_backtest_sin_diagonal: 12,4 pp frente a 22,1 pp con la mundial):
    # D^ = kappa_B x ICIO_bloque(c) x X(c,i) / X(c,bloque), si el país exporta la industria; si no, se mantiene la mundial.
    # peso exportador del país en el bloque como parámetro estructural de la serie: medias 2016-2022, igual para todos
    # los años (evita saltos entre años y cambios de variante); se aplica si es >= 1 %. Si es marginal o nulo, se
    # mantiene la estructura mundial (03c: en exportadores marginales ambas aciertan igual de poco).
    x3 = xpais.rename("X3")
    Xcb = x3.groupby(level=["pais", "bloque"]).sum().rename("Xcb")
    f = f.join(x3, on=["pais", "bloque", "industry_id"]).join(Xcb, on=["pais", "bloque"])
    ibx = f.fuente.eq("b-export") & (f.Xcb > 0) & (f.X3 / f.Xcb >= 0.01)
    f.loc[ibx, "trade"] = f.bloque[ibx].map(kappa_B).fillna(1.0) * f.DI[ibx] * f.X3[ibx] / f.Xcb[ibx]

    # e) fuera de la ICIO sin historia: modelo logit + efecto país
    ie = f.trade.isna()
    if ie.any():
        # entradas del modelo en medias de 3 años (importaciones de la celda y comercio total del país)
        fe = f[ie].join(pt3, on=["pais", "year"]).assign(M=lambda d: d.Mmedia)
        z = diseno(fe, Zf.columns).values @ beta
        ef = fe.pais.map(efecto_pais).fillna(0).values
        s_hat = 1 / (1 + np.exp(-(z + ef)))
        lo = fe.industry_id.map(sig_rango.p01).fillna(0.0).values
        hi = fe.industry_id.map(sig_rango.p99).fillna(0.95).values
        s_hat = np.clip(s_hat, lo, np.minimum(hi, 0.99))
        f.loc[ie, "trade"] = s_hat / (1 - s_hat) * f.Mmedia[ie].values
        f.loc[ie, "fuente"] = np.where(ef != 0, "e+país", "e")

    # energía (crudo y gas, refino) en países fuera de la ICIO: producción de estadísticas energéticas - exportaciones
    f = f.drop(columns=[c for c in ["E"] if c in f.columns]).merge(
        ENERGIA[ENERGIA.year == t][["pais", "industry_id", "E"]], on=["pais", "industry_id"], how="left")
    ien = ~f.en_icio & (f.E > 0)
    f.loc[ien, "trade"] = f.E[ien]
    f.loc[ien, "fuente"] = "en"

    # suelo de coherencia exportadora: ningún valor imputado por debajo de PHI x ICIO_bloque x peso exportador del
    # país en el bloque (peso estructural 2016-2022, el mismo que usa b-export, para no crear saltos entre años)
    piso = (PHI_COHERENCIA * f.DI * f.X3 / f.Xcb).where((f.Xcb > 0) & (f.DI > 0))
    f["suelo"] = f.trade.notna() & piso.notna() & (f.trade < piso)
    f.loc[f.suelo, "trade"] = piso[f.suelo]

    det = pd.concat([obs, f], ignore_index=True)
    det = det.rename(columns={"pais": "iso3"})
    det.to_parquet(comprobar_dentro(DIAG / f"diagonal_detalle_{t}.parquet"), index=False)
    guardar_parquet_compatible(det[["iso3", "industry_id", "trade", "fuente"]], DIAG / f"diagonal_{t}.parquet")
    pm = det.groupby("fuente").M.sum() / det.M.sum() * 100
    print(f"{t}: {len(det):,} celdas con importaciones | % de importaciones por fuente: " +
          ", ".join(f"{k} {v:.1f}" for k, v in pm.sort_values(ascending=False).items()) +
          f" | sin valor: {det.trade.isna().sum()}")

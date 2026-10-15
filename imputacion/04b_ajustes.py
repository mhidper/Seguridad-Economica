"""
04b_ajustes.py — Ajustes de coherencia sobre la diagonal imputada (se ejecuta después de 04_imputar.py).

Ajuste 1 · Seguridad de la regla a: se usa el nivel del dato propio observado más próximo (variante a0, 3,2 pp
           de error en la prueba; fuente -> "a0") si la regla a / a-ROW
             (i)  aleja la cuota doméstica D/(D+M) más de 30 puntos de la del dato propio, o
             (ii) da un valor más de 5 veces mayor o menor que ese dato y mueve la cuota 5 puntos o más.
Ajuste 2 · Empalme entre reglas: si en 2016-2022 la serie de una celda país-industria alterna la regla a (o a0)
           con reglas sin historia (b, b-export, b-solo, e, e+país), los años sin historia se reescalan para
           enlazar con el nivel del año más próximo con regla a, manteniendo la evolución de su propia regla.
           Fuente -> "<regla>-empalme".
Ajuste 3 · Tope de las reglas sin historia del grupo b: un valor imputado no puede superar 1,5 veces el máximo
           observado en cualquier país para esa industria (si hay >= 10 países con dato), salvo que el país esté
           entre los 3 mayores exportadores mundiales de la industria ese año. Fuente -> "<regla>-tope".
Ajuste 4 · Topes de bloque (países ICIO; kappa_B = escala ITPD/ICIO típica del bloque):
           (i)  ninguna industria imputada supera 1,5 x kappa_B x producción doméstica ICIO del bloque;
           (ii) si la suma del bloque (observadas + imputadas) supera 2 x kappa_B x ICIO, la parte imputada sin
                historia propia (excluidos los empalmes, ya anclados a la regla a) se reduce en proporción hasta ese límite, como mucho al 25 % de su valor. El factor
                es constante por país-bloque (media de los factores anuales) para no introducir saltos entre años.
           Fuente -> "<regla>-bloque".
Ninguna diagonal observada creíble se modifica (los residuos poco creíbles se tratan como lagunas). El valor previo se conserva en `trade_previo`.
Reescribe diagonal_{año}.parquet y diagonal_detalle_{año}.parquet.
"""
from comun import *

UMBRAL_SIG = 0.30
det = pd.concat([pd.read_parquet(DIAG / f"diagonal_detalle_{t}.parquet") for t in ANIOS], ignore_index=True)
if "trade_previo" in det.columns:            # repetible: se parte siempre del resultado de 04_imputar.py
    det["trade"], det["fuente"] = det.trade_previo, det.fuente_previa
    det = det.drop(columns=[c for c in ["trade_previo", "fuente_previa", "D_ref", "M_ref", "tau_ref"] if c in det.columns])
det["trade_previo"], det["fuente_previa"] = det.trade, det.fuente
ag = pd.read_parquet(DIAG / "itpd_agregados.parquet")
# anclas: solo diagonales observadas creíbles (coherencia exportadora, ver comun.PHI_COHERENCIA)
_cr = itpd_creible(mapeo_y_bloques())
ag = ag.merge(_cr[["pais", "industry_id", "year", "creible"]], on=["pais", "industry_id", "year"], how="left")
ag["creible"] = ag.creible.fillna(True).astype(bool)
obs = ag[(ag.D > 0) & ag.creible].rename(columns={"pais": "iso3", "year": "tau", "D": "Dtau", "M": "Mtau"})[["iso3", "industry_id", "tau", "Dtau", "Mtau"]]

# ---- Ajuste 1 ----
ia = det.fuente.isin(["a", "a-ROW"])
p = det[ia][["iso3", "industry_id", "year"]].reset_index().merge(obs, on=["iso3", "industry_id"])
p = p[(p.tau - p.year).abs().between(1, 7)]
p["d"] = (p.tau - p.year).abs()
p = p.sort_values(["d", "tau"]).groupby("index").first()
det = det.join(p[["Dtau", "Mtau", "tau"]].rename(columns={"Dtau": "D_ref", "Mtau": "M_ref", "tau": "tau_ref"}))
sig = det.trade / (det.trade + det.M)
sig_ref = det.D_ref / (det.D_ref + det.M_ref)
ratio_ref = det.trade / det.D_ref
cambia = ia & (((sig - sig_ref).abs() > UMBRAL_SIG) |
               (((ratio_ref > 5) | (ratio_ref < 0.2)) & ((sig - sig_ref).abs() >= 0.05)))
# por serie: si salta en algún año, toda la serie país-industria con regla a pasa a a0 (evita alternancias a <-> a0)
series = set(zip(det.iso3[cambia], det.industry_id[cambia]))
cambia = ia & pd.Series([(c, i) in series for c, i in zip(det.iso3, det.industry_id)], index=det.index) & det.D_ref.notna()
det.loc[cambia, "trade"] = det.D_ref[cambia]
det.loc[cambia, "fuente"] = "a0"
print(f"Ajuste 1: {cambia.sum()} celdas de regla a pasan a a0 (nivel del dato propio más próximo)")

# ---- Ajuste 2 ----
CON_HIST = {"a", "a0", "a-ROW"}
SIN_HIST = {"b", "b-export", "b-solo", "e", "e+país"}
n_emp = 0
for (iso, ind), g in det[det.fuente != "observada"].groupby(["iso3", "industry_id"]):
    fu = set(g.fuente)
    if not (fu & CON_HIST and fu & SIN_HIST):
        continue
    g = g.sort_values("year")
    con = g[g.fuente.isin(CON_HIST)]
    for ix, r in g[g.fuente.isin(SIN_HIST)].iterrows():
        k = (con.year - r.year).abs().idxmin()            # año más próximo con historia
        # valor de la propia regla sin historia en el año más próximo al de enlace, llevado al año de enlace con la
        # dinámica de su regla: producción ICIO del bloque (familia b) o importaciones medias (familia e)
        base = g[g.fuente.isin(SIN_HIST)]
        kb = (base.year - det.at[k, "year"]).abs().idxmin()
        if r.fuente.startswith("b") and det.at[kb, "DI"] > 0 and det.at[k, "DI"] > 0:
            contrafactual = det.at[kb, "trade_previo"] * det.at[k, "DI"] / det.at[kb, "DI"]
        else:
            contrafactual = det.at[kb, "trade_previo"] * det.at[k, "Mmedia"] / det.at[kb, "Mmedia"]
        factor = det.at[k, "trade"] / contrafactual if contrafactual and contrafactual > 0 else np.nan
        if np.isfinite(factor) and factor > 0:
            det.at[ix, "trade"] = det.at[ix, "trade_previo"] * factor
            det.at[ix, "fuente"] = f"{r.fuente}-empalme"
            n_emp += 1
print(f"Ajuste 2: {n_emp} celdas empalmadas con el nivel de la regla a del año más próximo")

# ---- Ajuste 3 ----
gmx = obs.groupby("industry_id").agg(Dmax=("Dtau", "max"), n=("iso3", "nunique"))
dmax = gmx.Dmax.where(gmx.n >= 10)
xa = ag[ag.year.isin(ANIOS)].copy()
xa["rk"] = xa.groupby(["industry_id", "year"]).X.rank(ascending=False, method="first")
top3 = set(zip(xa.pais[xa.rk <= 3], xa.industry_id[xa.rk <= 3], xa.year[xa.rk <= 3]))
tope = 1.5 * det.industry_id.map(dmax)
fam_b = det.fuente.str.startswith("b")
es_top = pd.Series([(c, i, y) in top3 for c, i, y in zip(det.iso3, det.industry_id, det.year)], index=det.index)
aplica = fam_b & tope.notna() & (det.trade > tope) & ~es_top
det.loc[aplica, "trade"] = tope[aplica]
det.loc[aplica, "fuente"] = det.fuente[aplica] + "-tope"
print(f"Ajuste 3: {aplica.sum()} celdas de la familia b topadas en 1,5 x máximo observado")

# ---- Ajuste 4 ----
kB = pd.read_csv(DIAG / "parametros_kappa_bloque.csv", index_col=0).kappa_B
det["kB"] = det.bloque.map(kB).fillna(1.0)
SIN = det.fuente.str.match(r"^(b|e)")               # familias sin historia propia (incl. empalmes y topes)
lim_i = 1.5 * det.kB * det.DI
c1 = SIN & det.DI.gt(0) & (det.trade > lim_i)
det.loc[c1, "trade"] = lim_i[c1]
det.loc[c1, "fuente"] = det.fuente[c1] + "-bloque"
obs_b = obs.rename(columns={"tau": "year", "Dtau": "D"}).merge(
    det[["industry_id", "bloque"]].drop_duplicates(), on="industry_id").groupby(["iso3", "bloque", "year"]).D.sum()
imp_tot = det[det.fuente != "observada"].groupby(["iso3", "bloque", "year"]).trade.sum()
imp_sin = det[SIN].groupby(["iso3", "bloque", "year"]).trade.sum()
ref = det.groupby(["iso3", "bloque", "year"]).agg(DI=("DI", "first"), kB=("kB", "first"))
bq = pd.concat([obs_b.rename("obs"), imp_tot.rename("imp"), imp_sin.rename("sin"), ref], axis=1).fillna({"obs": 0, "imp": 0, "sin": 0})
bq = bq[bq.DI > 0]
exceso = bq.obs + bq.imp - 2 * bq.kB * bq.DI
bq["f"] = (1 - exceso.clip(lower=0) / bq.sin.where(bq.sin > 0)).clip(lower=0.25, upper=1.0).fillna(1.0)
# factor constante por país-bloque (media de los años), para no crear saltos entre años
fser = bq.f.groupby(level=["iso3", "bloque"]).mean().rename("f_bloque")
det = det.join(fser, on=["iso3", "bloque"])
# las celdas empalmadas ya están ancladas al nivel de la regla a del año contiguo: no se reducen (romperían el empalme)
c2 = SIN & ~det.fuente.str.contains("-empalme") & det.f_bloque.lt(1)
det.loc[c2, "trade"] = det.trade[c2] * det.f_bloque[c2]
det.loc[c2 & ~det.fuente.str.endswith("-bloque"), "fuente"] = det.fuente + "-bloque"
print(f"Ajuste 4: {c1.sum()} celdas topadas al 1,5 x bloque; {c2.sum()} celdas reducidas por exceso del bloque")
det = det.drop(columns=["kB", "f_bloque"])

# ---- Ajuste 5 · Suelo de coherencia exportadora (después de empalmes y topes) ----
piso = (PHI_COHERENCIA * det.DI * det.X3 / det.Xcb).where((det.Xcb > 0) & (det.DI > 0))
c5 = det.fuente.ne("observada") & piso.notna() & (det.trade < piso)
det.loc[c5, "trade"] = piso[c5]
det["suelo"] = c5
print(f"Ajuste 5: {c5.sum()} celdas elevadas al suelo de coherencia exportadora ({PHI_COHERENCIA} x ICIO_bloque x peso exportador)")

for t in ANIOS:
    d = det[det.year == t]
    d.to_parquet(comprobar_dentro(DIAG / f"diagonal_detalle_{t}.parquet"), index=False)
    # fichero que lee el motor: formato compatible con pyarrow 19 (entorno de producción)
    guardar_parquet_compatible(d[["iso3", "industry_id", "trade", "fuente"]], DIAG / f"diagonal_{t}.parquet")
print(det.groupby("fuente").M.sum().div(det.M.sum()).mul(100).round(1).sort_values(ascending=False).to_dict())

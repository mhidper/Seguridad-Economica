"""
03e_backtest_energia.py — Regla de energía para países fuera de la ICIO (crudo y gas, industria 31; refino, 80).

Producción = volumen físico del Statistical Review of World Energy (Energy Institute) x valor por unidad.
  refino: refthru_kbd (crudo procesado en refinerías); crudo y gas: oilprod_kbd + gasprod_bcm (en barriles equivalentes).
Valor por unidad, año t: mediana entre países ICIO de producción ICIO del sector / volumen (C19 para refino, B06 para
crudo y gas), multiplicada por la escala ITPD/ICIO de la industria (mediana de producción ITPD observada / producción
ICIO, todos los años). D^ = producción^ - exportaciones ITPD.
Prueba: celdas observadas (D > 0, 2009-2021) de países con volumen; el valor por unidad se calcula sin el propio país.
Salida: data/processed/diagonal/backtest_energia.csv
"""
from comun import *

BOE_POR_BCM = 6.1        # millones de barriles equivalentes por bcm de gas natural
ei = pd.read_parquet(R / "data/processed/energia/ei_narrow.parquet")
ei = ei[ei.ISO3166_alpha3.notna() & ~ei.ISO3166_alpha3.str.contains("-")]
v = ei.pivot_table(index=["ISO3166_alpha3", "Year"], columns="Var", values="Value", aggfunc="first")
vol = pd.DataFrame({
    80: v.get("refthru_kbd") * 365 / 1000,                                            # millones de barriles
    31: v.get("oilprod_kbd").fillna(0) * 365 / 1000 + v.get("gasprod_bcm").fillna(0) * BOE_POR_BCM,
}).rename_axis(["pais", "year"]).reset_index().melt(id_vars=["pais", "year"], var_name="industry_id", value_name="V")
vol = vol[vol.V > 0]
vol["industry_id"] = vol.industry_id.astype(int)
SEC = {80: "C19", 31: "B06"}
anios = sorted(int(p.stem.split("_")[-1]) for p in DIAG.glob("icio_domestica_*.parquet"))
ic = pd.concat(pd.read_parquet(DIAG / f"icio_domestica_{a}.parquet") for a in anios)
paises_icio = set(ic.pais) - {"ROW"}
icp = pd.concat([ic[ic.sector == s][["pais", "year", "produccion"]].assign(industry_id=i) for i, s in SEC.items()])
ag = pd.read_parquet(DIAG / "itpd_agregados.parquet")
ag = ag[ag.industry_id.isin(SEC)]


def valor_unidad(excluir=None):
    """Valor por unidad (USD por barril) por industria y año: mediana ICIO x escala ITPD/ICIO."""
    b = vol.merge(icp, on=["pais", "year", "industry_id"])
    b = b[(b.produccion > 0) & (b.pais != excluir)]
    u = (b.produccion / b.V).groupby([b.industry_id, b.year]).median().rename("u")
    o = ag[(ag.D > 0) & (ag.pais != excluir)].merge(icp, on=["pais", "year", "industry_id"])
    o = o[o.produccion > 0]
    esc = ((o.D + o.X) / o.produccion).groupby(o.industry_id).median().rename("esc")
    return u.reset_index().join(esc, on="industry_id").assign(vu=lambda d: d.u * d.esc)[["industry_id", "year", "vu"]]


if __name__ == "__main__":
    obs = ag[(ag.D > 0) & ag.year.between(2009, 2021)].merge(vol, on=["pais", "year", "industry_id"])
    res = []
    for c, g in obs.groupby("pais"):
        vu = valor_unidad(excluir=c)
        g = g.merge(vu, on=["industry_id", "year"])
        g["Dh"] = g.V * g.vu - g.X
        res.append(g)
    r = pd.concat(res)
    r["icio"] = r.pais.isin(paises_icio)
    ok = r.Dh > 0
    s, sh = r.D / (r.D + r.M), (r.Dh.clip(lower=0) / (r.Dh.clip(lower=0) + r.M))
    r["err"] = (s - sh).abs()
    filas = []
    for (ind, icio), g in r.groupby(["industry_id", "icio"]):
        w = g.M.clip(lower=0)
        filas.append({"industria": ind, "en_icio": icio, "celdas": len(g), "con_estimación_positiva": int((g.Dh > 0).sum()),
                      "error_sigma_pp": round(100 * np.average(g.err, weights=w) if w.sum() > 0 else np.nan, 2),
                      "error_sigma_pp_mediana": round(100 * g.err.median(), 2),
                      "error_mediano_logD": round(float(np.median(np.abs(np.log(g.Dh[g.Dh > 0] / g.D[g.Dh > 0])))), 2)})
    out = pd.DataFrame(filas)
    out.to_csv(DIAG / "backtest_energia.csv", index=False)
    print(out.to_string(index=False))
    print(valor_unidad().pivot(index="year", columns="industry_id", values="vu").round(1).tail(8))

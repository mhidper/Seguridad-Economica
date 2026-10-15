"""Auditoría: ¿aparecen dependencias altas en industrias donde el país es gran productor/exportador?
Uso: python comparacion/auditoria_exportadores.py AÑO   (requiere pyarrow >= 21 para leer producción)"""
import sys, re, pandas as pd, numpy as np
from pathlib import Path
S = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(S)); from idee_paths import historico_referencia
REF = historico_referencia()   # entregables de la versión publicada anterior
y = int(sys.argv[1])
sufijo = "_v1" if "--v1" in sys.argv else ""
nom = pd.read_csv(S/"data/aux/traduccion_industrias_IDEE_ES_EN.csv")
n2id = dict(zip(nom.industry_name_en, nom.industry_id)); id2es = dict(zip(nom.industry_id, nom.industry_name_es))
def iid(s):
    m = re.match(r"^(\d+) ", s)
    return int(m.group(1)) if m else n2id.get(s, np.nan)
def maxdep(ruta):
    e = pd.read_parquet(ruta, columns=["importer","exporter","industry","dep_total","dep_direct","trade_value"])
    e["industry_id"] = e.industry.map({s: iid(s) for s in e.industry.unique()})
    assert e.industry_id.notna().all(), e[e.industry_id.isna()].industry.unique()[:5]
    e = e.sort_values("dep_total", ascending=False)
    top = e.drop_duplicates(["importer","industry_id"])[["importer","industry_id","exporter","dep_total","dep_direct","trade_value"]]
    sumtv = e.groupby(["importer","industry_id"]).trade_value.sum().rename("M_tv")
    return top.join(sumtv, on=["importer","industry_id"]).rename(columns={"importer":"iso3"})
# salidas del sandbox a auditar: por defecto las actuales; con --v1, las archivadas (diagonal anterior)
arch = S/"_archivo/diagonal_v1/historico" if "--v1" in sys.argv else S/"data/processed/historico"
sb = maxdep(arch/f"explorer_{y}.parquet"); pr = maxdep(REF/f"explorer_{y}.parquet")
# Especialización exportadora (ITPD-E)
a = pd.read_parquet(S/"data/processed/diagonal/itpd_agregados.parquet"); a = a[a.year == y].rename(columns={"pais":"iso3"})
a["Xw_i"] = a.groupby("industry_id").X.transform("sum"); a["X_c"] = a.groupby("iso3").X.transform("sum")
Xw = a.X.sum(); a["RCA"] = (a.X/a.X_c)/(a.Xw_i/Xw); a["cuota_mundial"] = a.X/a.Xw_i
a["rango_mundial"] = a.groupby("industry_id").X.rank(ascending=False, method="min")
dg = pd.read_parquet(S/f"data/processed/diagonal/diagonal_detalle_{y}.parquet")[["iso3","industry_id","trade","fuente"]]
t = a[["iso3","industry_id","X","M","RCA","cuota_mundial","rango_mundial"]].merge(dg, on=["iso3","industry_id"], how="left")
t["sigma"] = t.trade/(t.trade + t.M)
t["gran_exportador"] = ((t.RCA >= 2) & (t.X >= t.M) & (t.X >= 50)) | ((t.rango_mundial <= 5) & (t.cuota_mundial >= 0.05))
t = t.merge(sb.add_suffix("_sb").rename(columns={"iso3_sb":"iso3","industry_id_sb":"industry_id"}), on=["iso3","industry_id"], how="left")
t = t.merge(pr.add_suffix("_pr").rename(columns={"iso3_pr":"iso3","industry_id_pr":"industry_id"}), on=["iso3","industry_id"], how="left")
# Dependencia directa recalculada con la diagonal revisada (aprox.: trade_value / (D nueva + importaciones retenidas))
t["dep_dir_nueva"] = t.trade_value_sb/(t.trade + t.M_tv_sb)
t["industria"] = t.industry_id.map(id2es)
(S/"comparacion/auditoria").mkdir(parents=True, exist_ok=True)   # carpeta de resultados (no se versiona)
t.to_parquet(S/f"comparacion/auditoria/auditoria_{y}{sufijo}.parquet")
g = t[t.gran_exportador]
def tab(df, c): return {"≥0,5": int((df[c]>=0.5).sum()), "0,3-0,5": int(df[c].between(0.3,0.5,inclusive="left").sum())}
print(f"== {y}: celdas gran exportador = {len(g)}")
print(" dep. máxima de un proveedor, producción:", tab(g,"dep_total_pr"), " sandbox:", tab(g,"dep_total_sb"))
print(" sigma < 0,5 en gran exportador:", int((g.sigma<0.5).sum()), " de ellas imputadas:", int(((g.sigma<0.5)&(g.fuente!="observada")).sum()))

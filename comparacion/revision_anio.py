"""Revisión de un año calculado con la diagonal: métricas globales, casos de revisores, España.
Uso: python comparacion/revision_anio.py AÑO   (pyarrow >= 21)"""
import sys, re, pandas as pd, numpy as np
from pathlib import Path
spearman = lambda a, b: pd.Series(a).rank().corr(pd.Series(b).rank())
S = Path(__file__).resolve().parents[1]; y = int(sys.argv[1])
sys.path.insert(0, str(S)); from idee_paths import historico_referencia
P = historico_referencia()                       # entregables de la versión publicada anterior
SH = S / "data/processed/historico"             # entregables nuevos
H = lambda base, f: base/f"{f}_{y}.parquet"
out = {}
for ver, suf in [("global", ""), ("UE", "_UE")]:
    dp = pd.read_parquet(P/f"dependencies_{y}{suf}.parquet"); ds = pd.read_parquet(SH/f"dependencies_{y}{suf}.parquet")
    pp = pd.read_parquet(P/f"profiles_{y}{suf}.parquet"); ps = pd.read_parquet(SH/f"profiles_{y}{suf}.parquet")
    m = pp.merge(ps, on="country", suffixes=("_p", "_s"))
    out[ver] = {"top15 = 1,0 (prod)": int((dp.dependency_value >= 0.9999).sum()), "top15 = 1,0 (nueva)": int((ds.dependency_value >= 0.9999).sum()),
                "mediana top15 prod": round(dp.dependency_value.median(), 3), "mediana top15 nueva": round(ds.dependency_value.median(), 3),
                "vulnerabilidad media prod": round(pp.vulnerability.mean(), 3), "vulnerabilidad media nueva": round(ps.vulnerability.mean(), 3),
                "correlación de rangos": round(spearman(m.vulnerability_p.values, m.vulnerability_s.values), 3)}
print(pd.DataFrame(out).to_string())
nom = pd.read_csv(S/"data/aux/traduccion_industrias_IDEE_ES_EN.csv"); n2id = dict(zip(nom.industry_name_en, nom.industry_id))
def top(base):
    e = pd.read_parquet(H(base, "explorer"), columns=["importer", "exporter", "industry", "dep_total"])
    e["industry_id"] = e.industry.map({s: (int(re.match(r"^(\d+) ", s).group(1)) if re.match(r"^(\d+) ", s) else n2id.get(s)) for s in e.industry.unique()})
    return e.sort_values("dep_total", ascending=False).drop_duplicates(["importer", "industry_id"])
tp, ts = top(P), top(SH)
casos = [("SAU", 31, "Arabia Saudí · crudo y gas"), ("ITA", 50, "Italia · vinos"), ("USA", 35, "EE. UU. · gas por tubería"),
         ("BRA", 17, "Brasil · bovino vivo"), ("MEX", 165, "México · salud"), ("MEX", 34, "México · electricidad"),
         ("RUS", 32, "Rusia · mineral de hierro"), ("RUS", 81, "Rusia · combustible nuclear")]
filas = []
for iso, ind, txt in casos:
    a = tp[(tp.importer == iso) & (tp.industry_id == ind)]; b = ts[(ts.importer == iso) & (ts.industry_id == ind)]
    filas.append({"caso": txt, "prod": f"{a.dep_total.iloc[0]:.2f} {a.exporter.iloc[0]}" if len(a) else "—",
                  "nueva": f"{b.dep_total.iloc[0]:.2f} {b.exporter.iloc[0]}" if len(b) else "sin dependencia relevante"})
print(pd.DataFrame(filas).to_string(index=False))

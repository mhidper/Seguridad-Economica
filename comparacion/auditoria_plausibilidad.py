"""Segunda etapa: compara la diagonal de cada celda con su referencia exportadora (comun.ref_exportadora)."""
import sys, pandas as pd, numpy as np
from pathlib import Path
S = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(S/"imputacion"))
from comun import mapeo_y_bloques, itpd_creible
m = mapeo_y_bloques(); cr = itpd_creible(m)
for y in [2019, 2022]:
    t = pd.read_parquet(S/f"comparacion/auditoria/auditoria_{y}.parquet")
    t = t.drop(columns=[c for c in ["bloque","rB","rcel","anomalia","dep_nueva","ref_x","creible"] if c in t.columns])
    t = t.merge(cr[cr.year==y][["pais","industry_id","bloque","ref_x","creible"]].rename(columns={"pais":"iso3"}), on=["iso3","industry_id"], how="left")
    t["anomalia"] = t.trade/t.ref_x
    t["dep_nueva"] = (t.dep_total_sb*t.dep_dir_nueva/t.dep_direct_sb).where(t.dep_direct_sb>0, t.dep_total_sb)
    (S/"comparacion/auditoria").mkdir(parents=True, exist_ok=True)
    t.to_parquet(S/f"comparacion/auditoria/auditoria_{y}.parquet")
    g = t[t.gran_exportador & t.ref_x.notna()]
    sos = g[(g.anomalia < 0.1) & (g.dep_nueva >= 0.3)]
    print(y, "gran exportador con ICIO:", len(g), "| sospechosas (D < 10% de la referencia exportadora y dep ≥ 0,3):", len(sos),
          "| ≥0,5:", int((sos.dep_nueva>=0.5).sum()))
    print(sos.fuente.str.split("-").str[0].value_counts().to_dict())
    print(sos.sort_values("X", ascending=False)[["iso3","industria","bloque","X","M","trade","fuente","sigma","ref_x","anomalia","exporter_sb","dep_nueva"]].head(40).round(3).to_string())

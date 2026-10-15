"""
exportar_datos.py — Prepara los datos del visor local (visor/index.html) a partir de los ficheros de entrega.

Lee, para cada año y ámbito (mundo / UE), los parquet de producción (versión publicada, la que tiene IBM) y los del
sandbox (versión nueva), y escribe visor/datos/AAAA_ambito_version.js con lo necesario para las vistas del visor.
Uso (requiere pyarrow >= 21 para leer los ficheros de producción):  python visor/exportar_datos.py [años]
"""
import sys, re, json
from pathlib import Path
import numpy as np, pandas as pd

S = Path(__file__).resolve().parents[1]; OUT = S / "visor" / "datos"; OUT.mkdir(parents=True, exist_ok=True)
ANIOS = [int(a) for a in sys.argv[1:]] or list(range(2016, 2023))
sys.path.insert(0, str(S)); from idee_paths import historico_referencia
VERS = {"ibm": historico_referencia(), "nueva": S / "data/processed/historico"}   # "ibm": versión publicada anterior
nom = pd.read_csv(S / "data/aux/traduccion_industrias_IDEE_ES_EN.csv", encoding="utf-8-sig")
n2id = dict(zip(nom.industry_name_en, nom.industry_id))


def iid(s):
    m = re.match(r"^(\d+) ", s)
    return int(m.group(1)) if m else n2id.get(s)


def r(x, k=3):
    return None if pd.isna(x) else round(float(x), k)


# nombres de países (ITPD-E) y nombres de industrias
paises = {}
for f in sorted((S / "data/processed/diagonal/prueba").glob("filas_2019_parte*.parquet")):
    d = pd.read_parquet(f, columns=["exporter_iso3", "exporter_name"]).drop_duplicates()
    paises.update(dict(zip(d.exporter_iso3.astype(str), d.exporter_name.astype(str))))
paises["EU27"] = "Unión Europea (27)"
meta = {"paises": paises,
        "industrias": {int(i): [es, en, m] for i, es, en, m in zip(nom.industry_id, nom.industry_name_es, nom.industry_name_en, nom.macro_sector)},
        "anios": list(range(2016, 2023))}
(OUT / "meta.js").write_text("window.VISOR_META=" + json.dumps(meta, ensure_ascii=False) + ";", encoding="utf-8")

# diagonal (cuota doméstica y regla), solo versión nueva y ámbito mundo
def diagonal(y):
    f = S / f"data/processed/diagonal/diagonal_detalle_{y}.parquet"
    if not f.exists():
        return {}
    d = pd.read_parquet(f, columns=["iso3", "industry_id", "trade", "M", "fuente"])
    d["sig"] = d.trade / (d.trade + d.M)
    return {(a, int(b)): (r(s), fu) for a, b, s, fu in zip(d.iso3, d.industry_id, d.sig, d.fuente)}


serie = {}
for y in ANIOS:
    dg = diagonal(y)
    for amb, suf in [("mundo", ""), ("ue", "_UE")]:
        for ver, base in VERS.items():
            fp = base / f"profiles_{y}{suf}.parquet"
            if not fp.exists():
                print("falta", fp); continue
            pr = pd.read_parquet(fp)
            dep = pd.read_parquet(base / f"dependencies_{y}{suf}.parquet")
            ex = pd.read_parquet(base / f"explorer_{y}{suf}.parquet",
                                 columns=["importer", "exporter", "industry", "dep_total", "dep_direct", "dep_indirect", "trade_value", "trade_weight"])
            hb = pd.read_parquet(base / f"hubs_{y}{suf}.parquet")
            ex["ind"] = ex.industry.map({s: iid(s) for s in ex.industry.unique()})
            dep["ind"] = dep.industry.map({s: iid(s) for s in dep.industry.unique()})
            ex = ex.sort_values("dep_total", ascending=False)
            # dependencia «como en la web»: media de dep_total entre proveedores ponderada por el valor del comercio
            # (comprobado contra /api/countries/{iso}/sector/top-dependencies de la web de IBM)
            tv = ex.trade_value.astype(float)
            wv = (ex.assign(a=tv * ex.dep_total, b=tv * ex.dep_direct, t=tv)
                    .groupby(["importer", "ind"])[["a", "b", "t"]].sum())
            wv["wt"] = wv.a / wv.t.where(wv.t > 0); wv["wd"] = wv.b / wv.t.where(wv.t > 0)
            SD = ex.groupby(["importer", "ind"]).dep_direct.sum().to_dict()   # dependencia exterior: suma de las directas
            WT = wv.wt.to_dict(); WD = wv.wd.to_dict(); TT = wv.t.to_dict()   # TT: importaciones de la industria (suma de proveedores)
            # máximo por importador-industria
            mx = ex.drop_duplicates(["importer", "ind"])
            ind = {}
            for i, g in mx.groupby("ind"):
                filas = []
                for a, b, t, di, w in zip(g.importer, g.exporter, g.dep_total, g.dep_direct, g.trade_weight):
                    s_, fu = dg.get((a, int(i)), (None, None)) if (ver == "nueva" and amb == "mundo") else (None, None)
                    filas.append([a, r(t), b, r(di), r(TT.get((a, i)), 1), s_, fu, r(WT.get((a, i))), r(WD.get((a, i))), r(SD.get((a, i)))])
                ind[int(i)] = filas
            # proveedores (top 5) en las industrias del Top 15 y en las 25 con más importaciones de cada país
            top = {c: [[int(i), r(v)] for i, v in zip(g.ind, g.dependency_value)] for c, g in dep.groupby("dependent_country")}
            peso = mx[["importer", "ind"]].assign(trade_weight=[TT.get((a, b), 0) for a, b in zip(mx.importer, mx.ind)])
            sel = set()
            for c, g in peso.groupby("importer"):
                sel |= {(c, int(i)) for i in g.nlargest(25, "trade_weight").ind}
            for c, l in top.items():
                sel |= {(c, i) for i, _ in l}
            ex5 = ex.groupby(["importer", "ind"]).head(5)
            ex5 = ex5[[(a, int(b)) in sel for a, b in zip(ex5.importer, ex5.ind)]]
            sup = {}
            for (c, i), g in ex5.groupby(["importer", "ind"]):
                sup.setdefault(c, {})[int(i)] = [[b, r(t), r(d1), r(d2)] for b, t, d1, d2 in zip(g.exporter, g.dep_total, g.dep_direct, g.dep_indirect)]
            # socios: dependencia media ponderada por importaciones de la industria
            ex["w"] = [TT.get((a, b), 0) for a, b in zip(ex.importer, ex.ind)]
            ag = ex.assign(x=ex.dep_total * ex.w).groupby(["importer", "exporter"]).x.sum()
            tot = peso.groupby("importer").trade_weight.sum()
            ag = (ag / tot.reindex(ag.index.get_level_values(0)).values).rename("v").reset_index()
            part = {c: [[b, r(v)] for b, v in zip(g.nlargest(15, "v").exporter, g.nlargest(15, "v").v)] for c, g in ag.groupby("importer")}
            prof = [[c, r(v), int(k), r(s), r(n, 2)] for c, v, k, s, n in zip(pr.country, pr.vulnerability, pr.global_rank, pr.indirect_share, pr.num_suppliers_effective)]
            hubs = [[c, r(s), int(k)] for c, s, k in zip(hb.country, hb.global_score, hb.global_rank)]
            for c, v in zip(pr.country, pr.vulnerability):
                serie.setdefault(f"{amb}|{ver}", {}).setdefault(c, {})[y] = r(v)
            datos = {"prof": prof, "top": top, "ind": ind, "sup": sup, "part": part, "hubs": hubs}
            clave = f"{y}|{amb}|{ver}"
            (OUT / f"{y}_{amb}_{ver}.js").write_text(f"window.VISOR_DATA=window.VISOR_DATA||{{}};window.VISOR_DATA['{clave}']="
                                                      + json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + ";", encoding="utf-8")
            print(clave, f"{(OUT / f'{y}_{amb}_{ver}.js').stat().st_size/1e6:.1f} MB", flush=True)
# serie (se fusiona con la existente si se exportan años sueltos)
fs = OUT / "serie.json"
prev = json.loads(fs.read_text(encoding="utf-8")) if fs.exists() else {}
for k, d in serie.items():
    for c, yy in d.items():
        prev.setdefault(k, {}).setdefault(c, {}).update({str(a): v for a, v in yy.items()})
fs.write_text(json.dumps(prev), encoding="utf-8")
(OUT / "serie.js").write_text("window.VISOR_SERIE=" + json.dumps(prev) + ";", encoding="utf-8")

import pickle
from pathlib import Path

pkl = Path("../../data/processed/dependencias_consolidadas/all_results_2022.pkl")
with open(pkl, "rb") as f:
    all_results = pickle.load(f)

# Buscar industrias relacionadas con baterias
bat_industries = [k for k in all_results.keys() if "batter" in k.lower() or "accumul" in k.lower()]

for ind in bat_industries:
    deps = all_results[ind]["results"]["dependencies"]
    esp_deps = [d for d in deps if d["importador"] == "ESP"]
    esp_deps.sort(key=lambda x: x["dependencia_total"], reverse=True)
    
    with open("_batteries_result.txt", "w") as out:
        out.write(f"=== {ind} ===\n")
        out.write(f"Paises de los que España depende en {ind}:\n\n")
        out.write(f"{'Exportador':10s} {'Dep.Total':>10s} {'Directa':>10s} {'Indirecta':>10s}\n")
        out.write("-" * 45 + "\n")
        for d in esp_deps[:15]:
            out.write(f"{d['exportador']:10s} {d['dependencia_total']:10.4f} {d['dependencia_directa']:10.4f} {d['dependencia_indirecta']:10.4f}\n")
        
        out.write(f"\n\nCAMINOS COMERCIALES hacia España en {ind}:\n")
        out.write("(Por donde llegan realmente las baterias)\n\n")
        paths = all_results[ind]["results"]["critical_paths"]
        esp_paths = [p for p in paths if p["importador"] == "ESP"]
        esp_paths.sort(key=lambda x: x["fuerza"], reverse=True)
        for p in esp_paths[:10]:
            inter = " -> ".join(p["intermediarios"])
            out.write(f"  {p['exportador']} -> [{inter}] -> ESP  fuerza={p['fuerza']:.4f}\n")

print(open("_batteries_result.txt").read())

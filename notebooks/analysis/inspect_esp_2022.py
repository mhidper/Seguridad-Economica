import pickle
from pathlib import Path

def analyze_esp_2022():
    pkl_path = Path("../../data/processed/dependencias_consolidadas/all_results_2022.pkl")
    if not pkl_path.exists():
        print(f"File not found: {pkl_path}")
        return

    with open(pkl_path, "rb") as f:
        data = pickle.load(f)

    results = []
    for industry, content in data.items():
        deps = content.get('results', {}).get('dependencies', [])
        for dep in deps:
            if dep.get('importador') == 'ESP':
                # Solo nos interesan donde el riesgo indirecto sea relevante (>2%)
                if dep.get('dependencia_indirecta', 0) > 0.02:
                    results.append({
                        'industry': industry,
                        'exporter': dep.get('exportador'),
                        'direct': dep.get('dependencia_directa', 0),
                        'indirect': dep.get('dependencia_indirecta', 0),
                        'total': dep.get('dependencia_total', 0)
                    })

    # Ordenar por el componente indirecto más fuerte
    results.sort(key=lambda x: x['indirect'], reverse=True)

    print(f"{'Industria':<50} | {'Exp':<5} | {'Directa':<8} | {'Indirecta':<10} | {'Total':<8}")
    print("-" * 95)
    for r in results[:40]:  # Mostrar los top 40 casos
        print(f"{str(r['industry'])[:50]:<50} | {r['exporter']:<5} | {r['direct']:<8.4f} | {r['indirect']:<10.4f} | {r['total']:<8.4f}")

if __name__ == "__main__":
    analyze_esp_2022()

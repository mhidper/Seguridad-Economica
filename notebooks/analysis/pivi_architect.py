import pandas as pd
import numpy as np
import pickle
from pathlib import Path
import sys
from collections import defaultdict

def process_year(year):
    print(f"\n--- ARQUITECTO PIVI: Procesando año {year} ---")
    
    # Buscar la raíz del proyecto
    base_path = Path.cwd()
    while base_path.name != "Seguridad Economica" and base_path.parent != base_path:
        base_path = base_path.parent
    processed_dir = base_path / "data" / "processed" / "dependencias_consolidadas"
    output_dir = base_path / "data" / "processed" / "historico"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Cargar el PKL oficial del motor
    pkl_path = processed_dir / f"all_results_{year}.pkl"
    if not pkl_path.exists():
        # Fallback por si acaso
        pkl_path = processed_dir / "all_results.pkl"
        if not pkl_path.exists():
            print(f"❌ Error: No se encuentra el archivo de resultados para {year}")
            return False
            
    print(f"📂 Cargando {pkl_path}...")
    with open(pkl_path, "rb") as f:
        all_results = pickle.load(f)
    print(f"✅ Cargadas {len(all_results)} industrias")

    # 2. Calcular HUBS GLOBALES (Frecuencia y Fuerza)
    print("🛰️ Calculando Hubs...")
    freq_counter = defaultdict(int)
    strength_counter = defaultdict(float)
    
    for industry, data in all_results.items():
        res = data.get('results', {})
        for country, f in res.get('intermediary_frequency', {}).items():
            freq_counter[country] += f
        for country, s in res.get('intermediary_strength', {}).items():
            strength_counter[country] += s
            
    hubs = pd.DataFrame({
        "country": list(freq_counter.keys()),
        "frequency_total": [freq_counter[c] for c in freq_counter.keys()],
        "strength_total": [strength_counter[c] for c in freq_counter.keys()],
    })
    
    # Normalización para el score de Hubs
    if not hubs.empty:
        max_f = hubs["frequency_total"].max()
        max_s = hubs["strength_total"].max()
        hubs["freq_norm"] = hubs["frequency_total"] / max_f if max_f > 0 else 0
        hubs["strength_norm"] = hubs["strength_total"] / max_s if max_s > 0 else 0
        hubs["global_score"] = (0.4 * hubs["freq_norm"]) + (0.6 * hubs["strength_norm"])
        hubs["global_rank"] = hubs["global_score"].rank(ascending=False, method='min').astype(int)
        hubs = hubs.sort_values("global_score", ascending=False)
        hubs["year"] = year

    # 3. Calcular RELACIONES CRÍTICAS (Con Redundancia Real)
    print("⚠️ Identificando Relaciones Críticas...")
    critical_links = []
    
    for industry, data in all_results.items():
        # Reconstruimos la lógica de criticidad: Dep >= 0.7 y Caminos < 3
        # El motor ya calculó dependencies y significant_paths
        for dep in data['results']['dependencies']:
            if dep['dependencia_total'] >= 0.7:
                # Contar caminos alternativos significativos para esta relación
                pair_key = f"{dep['exportador']}->{dep['importador']}"
                alt_paths = data['results']['critical_intermediaries'].get(pair_key, [])
                num_paths = len(alt_paths)
                
                if num_paths < 3:
                    critical_links.append({
                        "year": year,
                        "industry": industry,
                        "exportador": dep['exportador'],
                        "importador": dep['importador'],
                        "dependencia_total": dep['dependencia_total'],
                        "caminos_alternativos": num_paths,
                        "criticidad": 1 - (num_paths / 3)
                    })
    
    df_critical = pd.DataFrame(critical_links)

    # 4. TRABAJO DE DETALLE: Dependencias por Industria y Bilaterales
    print("📊 Extrayendo detalle por industria y bilateral...")
    industry_deps = []
    bilateral_risk = []
    
    for industry, data in all_results.items():
        # Top dependencias para Treemap
        for dep in data['results']['dependencies']:
            industry_deps.append({
                "dependent_country": dep['importador'],
                "industry": industry,
                "dependency_value": dep['dependencia_total']
            })
            
            # Bilat (solo si es significativa)
            if dep['dependencia_total'] > 0.05:
                # Buscar si es crítica para el indicador de proveedores
                pair_key = f"{dep['exportador']}->{dep['importador']}"
                num_paths = len(data['results']['critical_intermediaries'].get(pair_key, []))
                bilateral_risk.append({
                    "exporter": dep['exportador'],
                    "importer": dep['importador'],
                    "industry": industry,
                    "criticidad": 1 - (num_paths / 3) if dep['dependencia_total'] >= 0.7 else 0,
                    "dependency": dep['dependencia_total']
                })

    df_ind_deps = pd.DataFrame(industry_deps)
    # Nos quedamos solo con las 15 principales por país para no saturar el JSON
    df_ind_deps = df_ind_deps.sort_values('dependency_value', ascending=False).groupby('dependent_country').head(15)
    
    df_bilat = pd.DataFrame(bilateral_risk)

    # 4b. EXPLORADOR POR INDUSTRIA: Proveedores por país/industria con caminos
    print("🔍 Generando explorador por industria (proveedores + rutas)...")
    industry_explorer = []
    
    for industry, data in all_results.items():
        deps = data['results']['dependencies']
        paths = data['results']['critical_paths']
        
        # Indexar caminos para búsqueda rápida: (importador, exportador) -> lista de caminos
        paths_idx = defaultdict(list)
        for p in paths:
            paths_idx[(p['importador'], p['exportador'])].append(p)
        
        # Agrupar dependencias por importador
        by_importer = defaultdict(list)
        for dep in deps:
            by_importer[dep['importador']].append(dep)
        
        # Para cada importador, quedarnos con sus top 5 proveedores
        for importer, importer_deps in by_importer.items():
            importer_deps.sort(key=lambda x: x['dependencia_total'], reverse=True)
            for dep in importer_deps[:5]:
                # Buscar el camino más fuerte para esta relación usando el índice
                pair_paths = paths_idx.get((importer, dep['exportador']), [])
                
                top_path = ""
                path_strength = 0.0
                if pair_paths:
                    best = max(pair_paths, key=lambda x: x['fuerza'])
                    top_path = " → ".join(best['intermediarios'])
                    path_strength = best['fuerza']
                
                industry_explorer.append({
                    "importer": importer,
                    "exporter": dep['exportador'],
                    "industry": industry,
                    "dep_total": round(dep['dependencia_total'], 4),
                    "dep_direct": round(dep['dependencia_directa'], 4),
                    "dep_indirect": round(dep['dependencia_indirecta'], 4),
                    "top_intermediary": top_path,
                    "path_strength": round(path_strength, 4)
                })
    
    df_explorer = pd.DataFrame(industry_explorer)

    # 5. Calcular PERFILES DE PAÍS (Vulnerabilidad e Importancia)
    print("👤 Generando Perfiles de País...")
    country_stats = []
    
    # Agregamos por país importador (vulnerabilidad) y exportador (importancia)
    for industry, data in all_results.items():
        for dep in data['results']['dependencies']:
            # Dato para vulnerabilidad (importador)
            country_stats.append({
                "country": dep['importador'],
                "vulnerability": dep['dependencia_total'],
                "trade_weight": dep['trade_value'],
                "role": "importer"
            })
            # Dato para importancia (exportador)
            country_stats.append({
                "country": dep['exportador'],
                "importance": dep['dependencia_total'],
                "trade_weight": dep['trade_value'],
                "role": "exporter"
            })

    df_stats = pd.DataFrame(country_stats)
    
    # Agregación Final
    profiles_vul = df_stats[df_stats['role'] == "importer"].groupby('country').apply(
        lambda x: np.average(x['vulnerability'], weights=x['trade_weight']) if x['trade_weight'].sum() > 0 else 0
    ).rename('vulnerability')
    
    profiles_imp = df_stats[df_stats['role'] == "exporter"].groupby('country').apply(
        lambda x: np.average(x['importance'], weights=x['trade_weight']) if x['trade_weight'].sum() > 0 else 0
    ).rename('importance')
    
    profiles = pd.concat([profiles_vul, profiles_imp], axis=1).fillna(0).reset_index()
    profiles["year"] = year
    # Ranking de vulnerabilidad
    profiles["global_rank"] = profiles["vulnerability"].rank(ascending=False).astype(int)

    # 6. GUARDAR RESULTADOS OFICIALES
    hubs.to_parquet(output_dir / f"hubs_{year}.parquet", index=False)
    df_critical.to_parquet(output_dir / f"critical_{year}.parquet", index=False)
    profiles.to_parquet(output_dir / f"profiles_{year}.parquet", index=False)
    df_ind_deps.to_parquet(output_dir / f"dependencies_{year}.parquet", index=False)
    df_bilat.to_parquet(output_dir / f"bilateral_{year}.parquet", index=False)
    df_explorer.to_parquet(output_dir / f"explorer_{year}.parquet", index=False)
    
    print(f"\n✅ PROCESO COMPLETADO PARA {year}")
    print(f"📍 Archivos guardados en: {output_dir}")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        years = [int(y) for y in sys.argv[1:]]
    else:
        # Por defecto, si no hay argumentos, buscar lo que haya
        print("Uso: python pivi_architect.py 2022 2021...")
        sys.exit(1)
        
    for y in years:
        process_year(y)

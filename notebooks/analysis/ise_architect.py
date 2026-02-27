import pandas as pd
import numpy as np
import pickle
from pathlib import Path
import sys
from collections import defaultdict

def process_year(year):
    print(f"\n--- ARQUITECTO ISE: Procesando ao {year} ---")
    
    # Buscar la raz del proyecto
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
            print(f" Error: No se encuentra el archivo de resultados para {year}")
            return False
            
    print(f"[*] Cargando {pkl_path}...")
    with open(pkl_path, "rb") as f:
        all_results = pickle.load(f)
    print(f" Cargadas {len(all_results)} industrias")

    # 2. Calcular HUBS GLOBALES (Frecuencia y Fuerza)
    print("[*] Calculando Hubs...")
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
    
    # Normalizacin para el score de Hubs
    if not hubs.empty:
        max_f = hubs["frequency_total"].max()
        max_s = hubs["strength_total"].max()
        hubs["freq_norm"] = hubs["frequency_total"] / max_f if max_f > 0 else 0
        hubs["strength_norm"] = hubs["strength_total"] / max_s if max_s > 0 else 0
        hubs["global_score"] = (0.4 * hubs["freq_norm"]) + (0.6 * hubs["strength_norm"])
        hubs["global_rank"] = hubs["global_score"].rank(ascending=False, method='min').astype(int)
        hubs = hubs.sort_values("global_score", ascending=False)
        hubs["year"] = year

    # 3. Calcular RELACIONES CRTICAS (Con Redundancia Real)
    print("[*] Identificando Relaciones de Riesgo...")
    critical_links = []
    
    for industry, data in all_results.items():
        # Reconstruimos la lgica de criticidad: Dep >= 0.7 y Caminos < 3
        # El motor ya calcul dependencies y significant_paths
        # Broaden threshold for better distribution in chart (Dep >= 0.5, any paths)
        for dep in data['results']['dependencies']:
            if dep['dependencia_total'] >= 0.5:
                # Contar caminos alternativos
                pair_key = f"{dep['exportador']}->{dep['importador']}"
                num_paths = len(data['results']['critical_intermediaries'].get(pair_key, []))
                
                critical_links.append({
                    "year": year,
                    "industry": industry,
                    "exportador": dep['exportador'],
                    "importador": dep['importador'],
                    "dependencia_total": dep['dependencia_total'],
                    "dependencia_directa": dep['dependencia_directa'],
                    "dependencia_indirecta": dep['dependencia_indirecta'],
                    "hidden_risk_factor": dep['dependencia_indirecta'] / (dep['dependencia_total'] + 1e-9),
                    "hidden_risk_abs": dep['dependencia_total'] - dep['dependencia_directa'],
                    "caminos_alternativos": num_paths,
                    "criticidad": 1 - (min(num_paths, 3) / 3)
                })
    
    df_critical = pd.DataFrame(critical_links)

    # 4. TRABAJO DE DETALLE: Dependencias por Industria y Bilaterales
    print("[*] Extrayendo detalle por industria y bilateral...")
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
                # Buscar si es crtica para el indicador de proveedores
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
    # Nos quedamos solo con las 15 principales por pas para no saturar el JSON
    df_ind_deps = df_ind_deps.sort_values('dependency_value', ascending=False).groupby('dependent_country').head(15)
    
    df_bilat = pd.DataFrame(bilateral_risk)

    # 4b. EXPLORADOR POR INDUSTRIA: Proveedores por pas/industria con caminos
    print("[*] Generando explorador por industria...")
    industry_explorer = []
    
    for industry, data in all_results.items():
        deps = data['results']['dependencies']
        paths = data['results']['critical_paths']
        
        # Indexar caminos para bsqueda rpida: (importador, exportador) -> lista de caminos
        paths_idx = defaultdict(list)
        for p in paths:
            paths_idx[(p['importador'], p['exportador'])].append(p)
        
        # Agrupar dependencias por importador
        by_importer = defaultdict(list)
        for dep in deps:
            by_importer[dep['importador']].append(dep)
        
        # Para cada importador, calcular su HHI específico en esta industria
        for importer, importer_deps in by_importer.items():
            # Concentración HHI = suma de cuadrados de las cuotas de mercado (0-1)
            # Solo sobre proveedores con dependencia > 0
            valid_deps = [d['dependencia_total'] for d in importer_deps if d['dependencia_total'] > 0]
            if valid_deps:
                # Normalizar para que sumen 1 (análisis de cuota de mercado relativa de los proveedores)
                total_cat = sum(valid_deps)
                hhi = sum([(v/total_cat)**2 for v in valid_deps])
                eff_suppliers = 1.0 / hhi
            else:
                hhi = 1.0
                eff_suppliers = 1.0

            importer_deps.sort(key=lambda x: x['dependencia_total'], reverse=True)
            for dep in importer_deps[:20]:
                pair_paths = paths_idx.get((importer, dep['exportador']), [])
                top_path = ""
                path_strength = 0.0
                if pair_paths:
                    best = max(pair_paths, key=lambda x: x['fuerza'])
                    top_path = "  ".join(best['intermediarios'])
                    path_strength = best['fuerza']
                
                industry_explorer.append({
                    "importer": importer,
                    "exporter": dep['exportador'],
                    "industry": industry,
                    "dep_total": round(dep['dependencia_total'], 4),
                    "dep_direct": round(dep['dependencia_directa'], 4),
                    "dep_indirect": round(dep['dependencia_indirecta'], 4),
                    "top_intermediary": top_path,
                    "path_strength": round(path_strength, 4),
                    "hhi_sector": round(hhi, 4),
                    "eff_suppliers_sector": round(eff_suppliers, 2)
                })
    
    df_explorer = pd.DataFrame(industry_explorer)

    # 5. Calcular PERFILES DE PAS (Vulnerabilidad e Importancia)
    print("[*] Generando Perfiles de Pas...")
    country_stats = []
    
    for industry, data in all_results.items():
        for dep in data['results']['dependencies']:
            # Dato para vulnerabilidad (importador)
            # Calculamos HHI por industria/importador para agregar despues
            country_stats.append({
                "country": dep['importador'],
                "industry": industry,
                "vulnerability": dep['dependencia_total'],
                "indirect": dep['dependencia_indirecta'],
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
    
    # Agregacin por pas (Importador - Vulnerabilidad)
    df_importers = df_stats[df_stats['role'] == "importer"]
    
    def agg_importer(x):
        if x['trade_weight'].sum() == 0: 
            return pd.Series([0, 0, 0], index=['vulnerability', 'indirect_share', 'num_suppliers_effective'])
        
        # 1. Vulnerabilidad media ponderada por el peso del comercio de la industria
        vul = np.average(x['vulnerability'], weights=x['trade_weight'])
        
        # 2. Share indirecto
        indirs = np.average(x['indirect'], weights=x['trade_weight'])
        ind_share = indirs / vul if vul > 0 else 0
        
        # 3. PROVEEDORES EFECTIVOS (CORREGIDO):
        # Primero calculamos el HHI por industria dentro de este país
        def get_hhi_sector(sub):
            # HHI = suma de cuadrados de dependencias normalizadas
            if sub['vulnerability'].sum() == 0: return 1.0
            norm_deps = sub['vulnerability'] / sub['vulnerability'].sum()
            return (norm_deps**2).sum()
        
        # Calculamos HHI para cada industria
        hhis_by_ind = x.groupby('industry').apply(get_hhi_sector)
        # Invertimos para obtener proveedores efectivos y promediamos (ponderado por peso industria)
        eff_suppliers_by_ind = 1.0 / hhis_by_ind
        
        # Promedio nacional de proveedores efectivos
        weights = x.groupby('industry')['trade_weight'].sum()
        # Asegurar coincidencia de indices
        eff_suppliers_by_ind = eff_suppliers_by_ind.loc[weights.index]
        avg_eff_suppliers = np.average(eff_suppliers_by_ind, weights=weights)
        
        return pd.Series([vul, ind_share, avg_eff_suppliers], 
                        index=['vulnerability', 'indirect_share', 'num_suppliers_effective'])

    profiles_vul = df_importers.groupby('country').apply(agg_importer)
    
    # Agregacin por pas (Exportador - Importancia)
    profiles_imp = df_stats[df_stats['role'] == "exporter"].groupby('country').apply(
        lambda x: np.average(x['importance'], weights=x['trade_weight']) if x['trade_weight'].sum() > 0 else 0
    ).rename('importance')
    
    profiles = pd.concat([profiles_vul, profiles_imp], axis=1).fillna(0).reset_index()
    profiles["year"] = year
    profiles["global_rank"] = profiles["vulnerability"].rank(ascending=False).astype(int)

    # 6. GUARDAR RESULTADOS OFICIALES
    hubs.to_parquet(output_dir / f"hubs_{year}.parquet", index=False)
    df_critical.to_parquet(output_dir / f"critical_{year}.parquet", index=False)
    profiles.to_parquet(output_dir / f"profiles_{year}.parquet", index=False)
    df_ind_deps.to_parquet(output_dir / f"dependencies_{year}.parquet", index=False)
    df_bilat.to_parquet(output_dir / f"bilateral_{year}.parquet", index=False)
    df_explorer.to_parquet(output_dir / f"explorer_{year}.parquet", index=False)
    df_explorer.to_parquet(output_dir / f"explorer_{year}.parquet", index=False)
    
    print(f"\n PROCESO COMPLETADO PARA {year}")
    print(f" Archivos guardados en: {output_dir}")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        years = [int(y) for y in sys.argv[1:]]
    else:
        # Por defecto, si no hay argumentos, buscar lo que haya
        print("Uso: python ise_architect.py 2022 2021...")
        sys.exit(1)
        
    for y in years:
        process_year(y)

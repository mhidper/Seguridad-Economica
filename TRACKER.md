# 📋 TRACKER — Proyecto PIVI (Seguridad Económica)
> Última actualización: 2026-02-25

## 🎯 Objetivo
Mantener un inventario vivo de todos los ficheros del proyecto.  
Cada fichero tiene un **estado** y una **acción pendiente**.

---

## 1. PIPELINE DE DATOS

### 1.1 Datos Brutos (no tocar)
| Fichero | Ubicación | Descripción | Estado |
|---------|-----------|-------------|--------|
| `ITPD_E_R03.csv.parteX.gz` | `data/raw/ITP/ITPD_E_R03/` | Datos ITP comprimidos (10 partes) | ✅ OK — Fuente original |

### 1.2 Motor (`00_dependency.ipynb`)
**Entrada:** Datos brutos ITP  
**Salida:** Un `all_results_{año}.pkl` por cada año procesado

| all_results_2022.pkl (1,4 GB) | `data/processed/dependencias_consolidadas/` | Motor (00) | ✅ Generado |
| all_results_2021.pkl (1,4 GB) | `data/processed/dependencias_consolidadas/` | Motor (00) | ✅ Generado |
| all_results_2020.pkl | `data/processed/dependencias_consolidadas/` | Motor (00) | ⏳ Pendiente — Lanzar hoy |
| `all_results_2019.pkl` | `data/processed/dependencias_consolidadas/` | Motor (00) | ⏳ Pendiente — Lanzar hoy |
| `all_results.pkl` (1,4 GB) | `data/processed/dependencias_consolidadas/` | Motor (00) — versión antigua | 🗑️ BORRAR — Duplicado de 2022, sin año en nombre |

### 1.3 Arquitecto (`pivi_architect.py`)
**Entrada:** `all_results_{año}.pkl`  
**Salida:** 5 Parquets por año en `data/processed/historico/`

| Fichero | Ubicación | Contenido | Estado |
|---------|-----------|-----------|--------|
| `profiles_{año}.parquet` | `historico/` | Vulnerabilidad e importancia por país | ✅ 2021-22 OK |
| `hubs_{año}.parquet` | `historico/` | Ranking intermediación global | ✅ 2021-22 OK |
| `critical_{año}.parquet` | `historico/` | Relaciones alta-dep + baja-redundancia | ✅ 2021-22 OK |
| `dependencies_{año}.parquet` | `historico/` | Top 15 dependencias industria/país (Treemap) | ✅ 2021-22 OK |
| `bilateral_{año}.parquet` | `historico/` | Detalle bilateral de riesgo | ✅ 2021-22 OK |
| `explorer_{año}.parquet` | `historico/` | **NUEVO**: Explorador por industria | ✅ 2021-22 OK |

### 1.4 Constructor del Dashboard (`build.py`)
**Entrada:** Todos los Parquets de `historico/` + catálogos  
**Salida:** `index.html` (dashboard autocontenido)

| Fichero | Ubicación | Estado |
|---------|-----------|--------|
| `build.py` | `dashboard_prototype/` | ✅ Actualizado para multiaño |
| `template.html` | `dashboard_prototype/` | ✅ Listo con gráficos de evolución |
| `index.html` | `dashboard_prototype/` | ⏳ Regenerar cuando tengamos ≥2 años |

---

## 2. FICHEROS NECESARIOS (CONSERVAR)

### Carpeta `data/processed/dependencias_consolidadas/`
| Fichero | Necesario | Motivo |
|---------|-----------|--------|
| `all_results_{año}.pkl` | ✅ SÍ | Fuente oficial de todos los datos del dashboard |
| `industrias_id_nombre.parquet` | ✅ SÍ | Catálogo de industrias (170) |
| `industrias_id_nombre.csv` | ⚠️ Redundante | Mismo contenido que el .parquet |
| `dependencias20XX.csv.gz` (22 ficheros) | ⚠️ REVISAR | Resúmenes sin intermediarios. Útiles como backup ligero |

### Carpeta `data/processed/historico/`
| Fichero | Necesario | Motivo |
|---------|-----------|--------|
| `profiles_{año}.parquet` | ✅ SÍ | Dashboard: mapa, KPIs, evolución |
| `hubs_{año}.parquet` | ✅ SÍ | Dashboard: ranking hubs |
| `critical_{año}.parquet` | ✅ SÍ | Dashboard: gráfico de riesgo |
| `dependencies_{año}.parquet` | ✅ SÍ | Dashboard: treemap por industria |
| `bilateral_{año}.parquet` | ✅ SÍ | Dashboard: proveedores críticos |

### Carpeta `notebooks/analysis/`
| Fichero | Necesario | Motivo |
|---------|-----------|--------|
| `00_dependency.ipynb` | ✅ SÍ | Motor PIVI |
| `01_build_foundations.ipynb` | ⚠️ REVISAR | Reemplazado parcialmente por `pivi_architect.py` |
| `02_exploit_ise.ipynb` | ✅ SÍ | Análisis exploratorio |
| `pivi_architect.py` | ✅ SÍ | Nuevo arquitecto automatizado |
| `comunidades.ipynb` | ✅ SÍ | Análisis de clusters |

---

## 3. FICHEROS A ELIMINAR (cuando confirmemos)

| Fichero | Ubicación | Motivo |
|---------|-----------|--------|
| `all_results.pkl` | `dependencias_consolidadas/` | Duplicado sin año. Ya tenemos `all_results_2022.pkl` |
| `dependencias2022_borrar.csv.gz` | `dependencias_consolidadas/` | Nombre indica que es temporal |
| `country_profiles.parquet` | `dependencias_consolidadas/` | Reemplazado por `historico/profiles_{año}.parquet` |
| `intermediarios_globales.parquet` | `dependencias_consolidadas/` | Reemplazado por `historico/hubs_{año}.parquet` |
| `relaciones_criticas.parquet` | `dependencias_consolidadas/` | Reemplazado por `historico/critical_{año}.parquet` |
| `caminos_significativos.parquet` | `dependencias_consolidadas/` | Datos contenidos en los `.pkl` |
| `evolution_summary.parquet` | `notebooks/analysis/` | Generado por script temporal (datos aproximados) |
| `critical_evolution.parquet` | `notebooks/analysis/` | Generado por script temporal (datos aproximados) |
| `evolution_plot.png` | `notebooks/analysis/` | Gráfico temporal |
| `extract_evolution.py` | `notebooks/analysis/` | Script temporal, reemplazado por `pivi_architect.py` |
| `extract_critical_evolution.py` | `notebooks/analysis/` | Script temporal, reemplazado por `pivi_architect.py` |
| `_check_batteries.py` | `notebooks/analysis/` | Script de diagnóstico puntual |
| `_batteries_result.txt` | `notebooks/analysis/` | Resultado de diagnóstico puntual |
| **Carpeta `dashboard/`** | raíz | Dashboard antiguo (Streamlit). Reemplazado por `dashboard_prototype/` |
| `data/processed/critical_relations.csv.gz` | `data/processed/` | Versión antigua pre-pipeline |
| `data/processed/dependencies_full.csv.gz` | `data/processed/` | Versión antigua, 600+ MB |
| `data/processed/intermediary_roles.csv.gz` | `data/processed/` | Pre-pipeline |
| `data/processed/intermediary_summary.csv.gz` | `data/processed/` | Pre-pipeline |
| `data/processed/parquet_files/` | `data/processed/` | Carpeta antigua |
| `dashboard_prototype/convert_data.py` | `dashboard_prototype/` | Script antiguo de conversión |
| `dashboard_prototype/patch.py` | `dashboard_prototype/` | Parche temporal |

---

## 4. CARPETA `dashboard/` (Dashboard antiguo — Streamlit)

| Fichero | Necesario | Motivo |
|---------|-----------|--------|
| `app.py` | 🗑️ NO | App Streamlit — reemplazada por dashboard estático |
| `data_utils.py` | 🗑️ NO | Utilidades del dashboard antiguo |
| `requirements.txt` | 🗑️ NO | Dependencias del dashboard antiguo |
| `logo.png` | ⚠️ MOVER | Si es el logo Elcano, conservar en otro sitio |
| `data/*.parquet` (5 ficheros) | 🗑️ NO | Datos del dashboard antiguo, reemplazados por `historico/` |

---

## 5. PLAN DE EJECUCIÓN (hoy 25 feb 2026)

| Paso | Acción | Tiempo est. | Estado |
|------|--------|-------------|--------|
| 1 | Motor 2022 | 55 min | ✅ Completado |
| 2 | Arquitecto 2022 | 2 min | ✅ Completado |
| 3 | Motor 2021 | ~55 min | ⏳ Siguiente |
| 4 | Arquitecto 2021 | 2 min | ⏳ Tras paso 3 |
| 5 | Motor 2020 | ~55 min | ⏳ Tras paso 4 |
| 6 | Arquitecto 2020 | 2 min | ⏳ Tras paso 5 |
| 7 | Motor 2019 | ~55 min | ⏳ Tras paso 6 |
| 8 | Arquitecto 2019 | 2 min | ⏳ Tras paso 7 |
| 9 | Reconstruir dashboard | 5 min | ⏳ Tras paso 8 |
| 10 | Limpieza de ficheros | 10 min | ⏳ Al final |

---

## 6. VISUALIZACIONES PENDIENTES

| Visualización | Datos necesarios | Estado |
|---------------|-----------------|--------|
| Mapa de vulnerabilidad | `profiles_{año}` | ✅ Datos listos |
| Ranking de Hubs | `hubs_{año}` | ✅ Datos listos |
| Gráfico de riesgo (criticidad vs redundancia) | `critical_{año}` | ✅ Datos listos |
| Treemap de industrias por país | `dependencies_{año}` | ✅ Datos listos |
| Proveedores críticos | `bilateral_{año}` | ✅ Datos listos |
| Evolución temporal (tendencia global) | Múltiples `critical_{año}` | ⏳ Necesita ≥2 años |
| Evolución temporal (por país) | Múltiples `profiles_{año}` | ⏳ Necesita ≥2 años |
| **🆕 Explorador por industria** | `all_results_{año}.pkl` | 📐 Diseñar — Dep. de ESP en baterías, etc. |

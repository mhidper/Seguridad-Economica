# 📋 TRACKER — Proyecto IDC (Índice de Dependencia Comercial)
> Última actualización: 2026-02-26 (V2.1 - Radar de Riesgo Oculto e Indexación O(1))

## 🎯 Objetivo
Mantener un inventario vivo de todos los ficheros del proyecto.  
Cada fichero tiene un **estado** y una **acción pendiente**.

---

## 1. PIPELINE DE PRODUCCIÓN (Automatizado)

### 1.1 Motor (`00_dependency.ipynb`)
**Genera el conocimiento base.** Procesa datos brutos de comercio ITP para identificar dependencias directas e indirectas por industria.
| Fichero | Ubicación | Descripción | Estado |
|---------|-----------|-------------|--------|
| `all_results_{año}.pkl` | `data/processed/dependencias_consolidadas/` | Resultados detallados por industria (1,4 GB/año) | ✅ 2016-2022 OK |

### 1.2 Arquitecto (`idc_architect.py`)
**Estructura el historial.** Transforma los .pkl masivos en archivos Parquet ligeros y estructurados por año.
**Salida en:** `data/processed/historico/`
| Fichero | Contenido | Estado |
|---------|-----------|--------|
| `profiles_{año}.parquet` | Vulnerabilidad, importancia y métricas por país (IDC) | ✅ 2016-2022 OK |
| `hubs_{año}.parquet` | Ranking y métricas de intermediación comercial global | ✅ 2016-2022 OK |
| `critical_{año}.parquet` | Relaciones de alto riesgo (Global) | ✅ 2016-2022 OK |
| `dependencies_{año}.parquet` | Perfil de importación sectorial (para Treemaps) | ✅ 2016-2022 OK |
| `explorer_{año}.parquet` | **Industria Explorer**: Rutas y dependencias por sector | ✅ 2016-2022 OK |

### 1.3 Constructor (`dashboard_prototype/build.py`)
**Genera la interfaz.** Empaqueta, optimiza e inyecta los datos en la UI.
| Fichero | Ubicación | Estado |
|---------|-----------|--------|
| `build.py` | `dashboard_prototype/` | ✅ OK — Con Indexador O(1) por Importador/Industria |
| `template.html` | `dashboard_prototype/` | ✅ OK — Con Radar de Riesgo Oculto e Indexación O(1) |
| `index.html` | `dashboard_prototype/` | ✅ GENERADO — Dashboard global 2016-2022 (~280MB) |
| `_archivos_legacy/` | `dashboard_prototype/` | 📁 Ficheros antiguos y maquetas (Mover para no confundir) |

---

## 2. ESTADO DE LOS DATOS

| Año | PKL Base | Parquets Historico | Integrado en Dashboard |
| 2015| ⏳ Pendiente | ❌ | ❌ |
| 2016| ✅ | ✅ | ✅ |
| 2017| ✅ | ✅ | ✅ |
| 2018| ✅ | ✅ | ✅ |
| 2019| ✅ | ✅ | ✅ |
| 2020| ✅ | ✅ | ✅ |
| 2021| ✅ | ✅ | ✅ |
| 2022| ✅ | ✅ | ✅ |

---

## 3. MEJORAS RECIENTES (Handover Ready)
1.  **Radar de Riesgo Oculto**: Sustitución del scatter global por un radar sectorial (Directo vs Indirecto).
2.  **Optimización O(1)**: Los datos del explorador se sirven pre-indexados, eliminando latencia en el frontend.
3.  **Inclusión España**: España forzado en el pipeline para asegurar cobertura total de sus vulnerabilidades.

---

## 4. PRÓXIMOS PASOS (Nuevas Funcionalidades)
1.  **Migración Backend**: Para despliegue web oficial, usar DuckDB para servir los archivos .parquet.
2.  **Validación Geopolítica**: Cruzar con indicadores de afinidad política para refinar el riesgo de fragmentación.
3.  **Análisis de Resiliencia**: Calcular escenarios de sustitución (alternativas de suministro).

---
*Mantenido por el equipo del Real Instituto Elcano.*

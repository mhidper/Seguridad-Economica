# 📊 ISE — Índice de Seguridad Económica
**Real Instituto Elcano**  
> Última actualización: 26/02/2026 — *Versión Multi-año Unificada (V2.1 - Radar de Riesgo Oculto)*

Análisis de dependencias económicas en cadenas de suministro globales. El **ISE** cuantifica la vulnerabilidad de las economías midiendo dependencias directas e indirectas en el comercio bilateral por industria, en un contexto de fragmentación geoeconómica.

---

## 🏗️ Estructura del Proyecto e Importancia de Archivos

El sistema se organiza en un pipeline lineal de producción que transforma datos brutos de comercio en conocimiento estratégico.

### 1. Motor de Cálculo (`notebooks/analysis/00_dependency.ipynb`)
**El cerebro matemático.** Utiliza cálculo matricial acelerado (GPU/PyTorch) para procesar la base de datos ITP (236 países, 170 industrias).
-   **Función:** Calcula las dependencias indirectas (vulnerabilidad a través de intermediarios) de hasta longitud 5.
-   **Output:** Genera archivos `all_results_{año}.pkl` (1.4 GB/año), que contienen el grafo completo de riesgos.

### 2. El Arquitecto (`notebooks/analysis/ise_architect.py`)
**El estructurador oficial.** Transforma los masivos `.pkl` en tablas relacionales ligeras.
-   **Ubicación de Salida:** `data/processed/historico/`
-   **Archivos Generados:**
    -   `profiles_{año}.parquet`: Rankings globales y perfiles de vulnerabilidad.
    -   `hubs_{año}.parquet`: Nodos de intermediación crítica.
    -   `critical_{año}.parquet`: Alertas de dependencias bilaterales de alto riesgo.
    -   `explorer_{año}.parquet`: Rutas e industrias específicas (optimizado mediante indexación O(1)).

- **Poda Inteligente:** Para mantener la fluidez en el navegador, se filtra el riesgo por debajo del 1% (ESP) / 5% (Global) y se limita al Top 10 de proveedores por industria.

### 3. El Constructor de Dashboard (`dashboard_prototype/build.py`)
**El empaquetador.** Toma los datos del historial, aplica filtros de relevancia y genera el prototipo interactivo.
-   **Output:** `dashboard_prototype/index.html` (Dashboard autocontenido, optimizado mediante indexación por diccionarios).

---

## 📂 Flujo de Datos Visual

```mermaid
graph TD
    A[ITP Raw Data (.csv.gz)] --> B(00_dependency.ipynb)
    B -- "Calcula matrices" --> C{all_results_YYYY.pkl}
    C --> D(ise_architect.py)
    D -- "Estructura tablas" --> E[(Carpeta Historico / Parquet)]
    E --> F(build.py)
    F -- "Crea Dashboard" --> G[index.html Final]
```

---

## 🏢 Guía de Implementación Profesional (Handover)

El dashboard actual es un **prototipo funcional de alto rendimiento** (HTML/JS/Plotly) diseñado para la portabilidad. Para transformar este repositorio en una plataforma web profesional de nivel corporativo, se recomienda:

### 🚀 Recomendaciones de Arquitectura
1.  **Motor de Base de Datos:** No se recomienda servir un archivo HTML de +280MB en producción. Utilizar un backend (FastAPI o Node.js) conectado a una base de datos analítica orientada a columnas como **DuckDB** o **ClickHouse**. Estas herramientas leen los archivos `.parquet` de la carpeta `historico/` de forma nativa e instantánea.
2.  **API de Datos:** Exponer endpoints JSON que devuelvan solo las "tajadas" de datos necesarias para cada vista.
3.  **Frontend Framework:** Migrar la lógica de `template.html` (basada en JavaScript vainilla) a **React** o **Vue.js**.
4.  **Mapa y Globo:** La implementación actual de Plotly es robusta. Para una experiencia más premium, considerar **Deck.gl** o **Mapbox GL**.

### 📈 Explotación de los Datos
- Los archivos en `data/processed/historico/` son la **fuente de verdad**. Cada registro representa un grafo de suministro global.
- **Riesgo Oculto (Efecto ISE)**: El valor diferencial es la detección de vulnerabilidades indirectas masivas en proveedores directos menores. Se visualiza específicamente en el nuevo Radar del Explorador.
- **Rendimiento y Escalabilidad**: El prototipo utiliza indexación por diccionarios (`explorer_indexed`) y una poda estratégica (ESP >= 1%, Global >= 5%, Top 10) para manejar ~280MB de datos en memoria. En una implementación pro, el backend debe realizar estos filtros dinámicamente sobre la base de datos completa.

---

## 🛠️ Requisitos Técnicos

-   **Python 3.10+**
-   **GPU NVIDIA:** Altamente recomendada para el notebook `00_dependency`.
-   **Dependencias Core:** pandas, numpy, torch, plotly, pyarrow (para Parquet).

---

## 👥 Equipo (Real Instituto Elcano)
-   Manuel Alejandro Hidalgo
-   Miguel Otero

---
*Este proyecto es propiedad del Real Instituto Elcano. El código y los datos generados son para fines de análisis estratégico de seguridad económica.*

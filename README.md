# 📊 ISE — Índice de Seguridad Económica
**Real Instituto Elcano**  
> Última actualización: 26/02/2026 — *Versión Multi-año Unificada (V2.1 - Radar de Riesgo Oculto)*

Análisis de dependencias económicas en cadenas de suministro globales. El **ISE** cuantifica la vulnerabilidad de las economías midiendo dependencias directas e indirectas en el comercio bilateral por industria, en un contexto de fragmentación geoeconómica.

---

---

## 🏗️ Prototipo "Lite" vs. Sistema de Producción

Para facilitar la visualización inmediata y el despliegue en **GitHub Pages**, el repositorio incluye un sistema de generación de datos "Lite".

### 1. El Generador de Juguete (`build_toy.py`)
Este script crea una versión reducida pero 100% funcional del ecosistema de datos:
- **Reducción de Escala:** Selecciona un subconjunto (ej. 30 países) en lugar de los 236 originales.
- **Fragmentación de Archivos:** Genera archivos `data_toy_YYYY.json` individuales por año. Esto permite que el navegador solo descargue el año que el usuario está consultando, optimizando la memoria (archivos de ~7MB vs. el archivo consolidado de +300MB).
- **Propósito:** Validar la UX/UI, probar las visualizaciones y demostrar la capacidad multi-año sin necesidad de un servidor backend.

### 2. El Dashboard (`dashboard_prototype/template.html`)
El frontend está diseñado como una **Single Page Application (SPA)** reactiva que:
- Implementa una arquitectura de carga bajo demanda (Lazy Loading) de archivos JSON.
- Utiliza **Plotly.js** para renderizar mapas coropléticos, globos 3D y radares de riesgo indirecto.
- Mantiene el estado global del año y sincroniza todos los componentes (KPIs, Mapas, Rankings, Explorador) automáticamente al cambiar de periodo.

---

## 🏢 Guía de Handover para Implementación Profesional

Esta sección es crítica para la empresa encargada de la web definitiva. El objetivo es escalar el prototipo actual a una plataforma robusta.

### 📦 El "Contrato" de Datos (API Contract)
El esquema JSON generado por `build_toy.py` debe considerarse como la especificación técnica de la API. Si el backend profesional sirve JSONs con la misma estructura que `data_toy.json`, el frontend funcionará con el 100% de los datos sin cambios significativos.

**Campos clave que la API debe servir:**
- `kpis`: Resumen estadístico global por año.
- `map_data`: Valores del ISE por país (ISO3) para el mapamundi.
- `hubs_data`: Rankings de intermediación y scores de centralidad.
- `explorer_indexed`: (Crítico) Un diccionario indexado por `industry_id` que contiene las rutas de dependencia directa e indirecta.
- `target_year`: El año de los datos servidos.
- `available_years`: Lista de periodos disponibles para el selector.

### 🚀 Hoja de Ruta de Escalabilidad
1.  **Backend vs. Archivos Estáticos:** Abandonar los archivos `.json` estáticos. El backend debe consultar los archivos `.parquet` ubicados en `data/processed/historico/` (fuente de verdad procesada).
2.  **Motor 추천 (Recomendado):** Utilizar **DuckDB** en el servidor. Permite realizar consultas SQL analíticas sobre archivos Parquet en milisegundos.
3.  **Migración a Framework Pro:** Se recomienda portar la lógica de `template.html` (Javascript Vainilla) a **Next.js (React)** o **Nuxt (Vue)** para mejorar la gestión de estados complejos y SEO.
4.  **Optimización de Búsqueda:** Implementar la búsqueda de países e industrias mediante una base de datos vectorial o un índice simple en el backend, evitando cargar los nombres de 170 industrias y 230 países en el cliente.
5.  **Visualización Premium:** Sustituir los mapas de Plotly por soluciones más fluidas como **Mapbox GL** o **Deck.gl** si se requiere manejar miles de flujos comerciales simultáneos.

---

## 🛠️ Requisitos Técnicos

-   **Python 3.10+**
-   **GPU NVIDIA:** Altamente recomendada para el motor de cálculo (`00_dependency.ipynb`).
-   **Dependencias Core:** pandas, numpy, torch, plotly, pyarrow (para manejo de Parquet).

---

## 👥 Equipo (Real Instituto Elcano)
-   Manuel Alejandro Hidalgo
-   Miguel Otero

---
*Este proyecto es propiedad del Real Instituto Elcano. El código y los datos generados son para fines de análisis estratégico de seguridad económica.*

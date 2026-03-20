# 📋 Guión de Reunión: Desarrollo Frontend Dashboard IDC-CVG

**Objetivo de la sesión:** Alinear la arquitectura de datos existente con la propuesta de experiencia de usuario y visualización de la agencia de desarrollo web.

---

## PARTE 1: Ciclo de Vida y Origen de los Datos (Top-to-Bottom)
*Mensaje clave: "Los datos de la web son una versión optimizada de nuestro motor de cálculo macroeconómico."*

### 1.1 El Origen: Los Archivos Maestros (Parquet)
Todo nace en la carpeta de datos procesados del repositorio. Estos archivos son el "Cerebro" del modelo, calculados previamente en Python:
*   **Ubicación:** `data/processed/historico/`
*   **Naturaleza:** Archivos `.parquet` (formato profesional de alta velocidad).
*   **Contenido:** Aquí reside la información bruta de **perfiles**, **hubs**, **dependencias críticas** y, sobre todo, la matriz **Bilateral** (quién depende de quién exactamente).

### 1.2 El Puente: Script de Transformación (`build_fragmented.py`)
Este script actúa como una "cocina". Coge los archivos Parquet pesados y los transforma en lo que la web necesita:
1.  **Limpia y filtra:** Elimina datos innecesarios para que la web no pese gigabytes.
2.  **Traduce:** Convierte de Parquet (Binario) a JSON (Texto legible por web).
3.  **Fragmenta:** Crea un archivo por cada año para que el usuario solo cargue lo que está viendo.

### 1.3 El Destino: Datos de Consumo Web (JSON)
Es lo que entregamos a la empresa de desarrollo para que "pinte" el dashboard:
*   **Ubicación:** `dashboard_prototype/data_dist/`
*   **Archivos:** `meta.json` (global) y `year_YYYY.json` (anual).

---

## PARTE 2: La Arquitectura de Consumo (Frontend)
*Mensaje clave para la agencia: "Os damos archivos estáticos. No necesitáis montar una base de datos ni una API."*

### 2.1 Estructura de Bloques por Año
Cada archivo anual (`year_2022.json`, etc.) contiene los pilares de la visualización:
1.  **`bilateral` (¡NUEVO/CRÍTICO!):** Contiene la relación directa Exporter -> Importer. Es lo que permite saber, por ejemplo, el grado de dependencia de España respecto a China en un sector.
2.  **`profiles`**: Resumen macro del país (riesgo, importancia, rango global).
3.  **`hubs`**: Ranking de las potencias que controlan el suministro mundial.
4.  **`dependencies`**: Listado de los 10 sectores más peligrosos para cada país.

### 2.2 El Formato Matricial (Optimización)
Usamos un formato de compresión para que la web vuele:
*   **`c` (Columns):** Los nombres de las columnas (ej: `["exporter", "importer", "dependency"]`).
*   **`d` (Data):** Los valores puros (ej: `["CHN", "ESP", 0.85]`).
*   *Nota Dev:* Deben mapear la posición del dato con la posición de la columna en memoria.

---

## PARTE 3: Diseño, KPIs y Experiencia de Usuario (UI/UX)
*Mensaje clave: "Navegación de lo macro (Mundo) a lo micro (Sector/País)."*

### 3.1 Métricas Estrella
*   **Vulnerabilidad Global**: Riesgo total del país frente al exterior.
*   **Indirect Share**: Cuánto de ese riesgo es "oculto" (proviene de terceros países en la cadena).
*   **Global Score**: El poder de interrupción que tiene un país "Hub".

### 3.2 Navegación en Capas (User Journey)
1.  **Nivel 0: El Globo (Gancho):** Vista exploratoria 3D de la vulnerabilidad mundial. Al pinchar en un país, el globo se orienta y lanza arcos hacia sus proveedores principales.
2.  **Nivel 1: La Ficha de País (Acción Inmediata):** Un resumen tipo "DNI" con KPIs flash y el **Radar de Riesgo (Directo vs Indirecto)**.
3.  **Nivel 2: Los Grandes Bloques de Análisis (Exploración Profunda):**

### 3.3 El Doble Pivot: País vs Sector

#### A. Dimensión País (Visión Geopolítica)
*   **Pivot:** "Yo soy España, ¿qué me pasa?"
*   **Integración de Criticidad:** Desglose por sectores donde se identifiquen nominalmente los culpables del riesgo. 
    *   *Ejemplo:* "En el sector **Química**, tus países más críticos son **China (85%)**, **EE.UU. (40%)** y **Alemania (20%)**".
*   **Evolución:** Gráfico de líneas del IDC total del país a lo largo de los años.

#### B. Dimensión Sectorial (Visión de Mercado/Suministro)
*   **Pivot:** "Me interesa el sector Microchips, ¿quién manda?"
*   **Integración de Hubs:** Identificación de los países que actúan como cuellos de botella para ese sector específico.
*   **Análisis Dinámico (Tiempo):** ¿Han cambiado los Hubs? 
    *   *Visualización:* Una "carrera de barras" o un gráfico de líneas comparando los Hub Scores de las potencias sectoriales (ej: Ver cómo China ha ganado peso frente a Japón en Electrónica desde 2016).

---

### 3.4 Visualizaciones Clave
1.  **Mapa de Conexiones (Bilateral):** Usar el bloque `bilateral` para dibujar flujos nominales de criticidad.
2.  **Radar de Riesgo "Iceberg":** Para distinguir entre dependencia visible y oculta.
3.  **Matriz de Concentración Sectorial:** Para visualizar la fragilidad de un sector según el número de Hubs que lo controlan.

---

## 📂 PARTE 4: Guía de Referencia de Ficheros y Muestras (Dev Specs)

Diles a los programadores: *"Aquí tenéis la chuleta técnica de qué hay en cada sitio y cómo se lee."*

### 🔵 Fase 1: Materia Prima (Backend/Data)
**Directorio:** `data/processed/historico/`
Archivos profesionales de alta densidad (formato Parquet).

| Archivo | Ejemplo de Datos (Muestra) | Propósito |
| :--- | :--- | :--- |
| **`bilateral_2022.parquet`** | `{'exporter': 'CHN', 'importer': 'ESP', 'industry': 'Electronics', 'dependency': 0.85}` | La red completa de flujos país-a-país. |
| **`hubs_2022.parquet`** | `{'country': 'CHN', 'global_score': 0.89, 'strength_total': 7834.3}` | Ranking de potencias controladoras. |
| ****`profiles_2022.parquet`**** | `{'country': 'ESP', 'vulnerability': 0.15, 'indirect_share': 0.45}` | Resumen estadístico nacional. |

---

### 🟡 Fase 2: Transformación (Script Python)
**Ubicación:** Raíz del proyecto.
*   **Script:** `build_fragmented.py`
*   **¿Qué hace?:** Lee los Parquet de arriba y "cocina" los JSON fragmentados de abajo.

---

### 🟢 Fase 3: Producto Web (Frontend Readiness)
**Directorio:** `dashboard_prototype/data_dist/`
Ficheros ligeros listos para el navegador.

#### Muestra de `meta.json` (El Diccionario Global)
```json
{
  "latest_year": 2022,
  "available_years": [2016, 2017, 2018, 2019, 2020, 2021, 2022],
  "industries": [ ["131", "Electronic valves tubes etc."], ["138", "Motor vehicles"] ],
  "evolution": [ ["ESP", 2022, 0.24, 0.17, 232], ["CHN", 2022, 0.25, 0.62, 223] ]
}
```

#### Muestra de `year_2022.json` (La Foto Anual)
```json
{
  "profiles": { "c": ["country", "vulnerability"], "d": [ ["ESP", 0.24], ["CHN", 0.25] ] },
  "hubs": { "c": ["country", "global_score"], "d": [ ["CHN", 0.89], ["USA", 0.75] ] },
  "bilateral": { "c": ["exporter", "importer", "industry", "dependency"], "d": [ ["CHN", "ESP", 131, 0.95] ] }
}
```

---

## 🗺️ PARTE 5: Esquema Visual de la Estructura (Resumen)

```text
PROYECTO SEGURIDAD ECONÓMICA
│
├── 🔴 TOP: data/processed/historico/  (Materia Prima: .parquet)
│           ├── bilateral_2022.parquet
│           ├── hubs_2022.parquet
│           └── ...
│
├── 🟡 MID: build_fragmented.py        (Procesador / Puente)
│
└── 🟢 BOTTOM: dashboard_prototype/data_dist/  (Producto Web: .json)
               ├── meta.json
               └── year_2022.json
```

---

## 💡 PARTE 6: FAQs para la Reunión

*   **¿Cómo se actualiza la web?** Simplemente sustituyendo los archivos en `data_dist`.
*   **¿Cómo lanzarlo localmente?** `cd dashboard_prototype; py -m http.server 8000`
*   **¿Se pueden ver dependencias entre dos países?** Sí, usando el bloque `bilateral`.
*   **¿Qué pasa si hay 170 industrias?** Se recomienda mostrar solo el Top 10/20 por defecto para no saturar al usuario.

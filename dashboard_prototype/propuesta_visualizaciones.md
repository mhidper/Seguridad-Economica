# Propuesta de Nuevas Visualizaciones: Seguridad Económica Elcano

## 0. Mapa de Datos y Fuentes

Todos los datos se encuentran en `../data/processed/historico/`. Cada archivo existe en versiones anuales (sufijo `_{year}`, de 2016 a 2022). A continuación se describe en detalle la estructura, indicadores y usos de cada fuente de datos, seguidos de una **tabla resumen**.

---

### 0.1 `profiles_{year}.parquet` — Perfil Agregado por País

**Estructura:** Cross-Sectional (País). Una fila por país (código ISO3). ~236 filas por año.

| Columna | Tipo | Descripción | Rango |
| :--- | :--- | :--- | :--- |
| `country` | `str` | Código ISO3 del país (ej: `ESP`, `USA`, `CHN`). **Clave primaria.** | — |
| `vulnerability` | `float64` | **Índice de Seguridad Económica (ISE)**. Mide la exposición agregada del país a disrupciones en sus cadenas de suministro. Combina dependencia directa e indirecta ponderada por la importancia de cada industria. | 0 – 1 |
| `indirect_share` | `float64` | Proporción del riesgo total que proviene de dependencias **indirectas** (vía intermediarios), frente a las directas. Valores altos indican que el país depende de "eslabones ocultos". | 0 – 1 |
| `num_suppliers_effective` | `float64` | **Número Efectivo de Proveedores** (Diversificación). Basado en el inverso del índice Herfindahl. Valores bajos indican alta concentración de proveedores (peligro). | > 0 |
| `importance` | `float64` | **Peso Estratégico Global** del país como proveedor para otros. Mide cuánto depende el mundo de este país. | 0 – 1 |
| `year` | `int64` | Año del corte de datos. | 2016–2022 |
| `global_rank` | `int32` | Posición del país en el ranking mundial de vulnerabilidad (1 = más vulnerable). | 1 – 236 |

**Usos previstos:**
*   KPIs principales en la ficha de país (ISE, Ranking, Diversificación).
*   Series temporales de evolución del ISE (2016-2022).
*   Ordenación y filtrado del listado global de países.

---

### 0.2 `explorer_{year}.parquet` — Dependencias País-Industria

**Estructura:** Cruce (País-Industria). Una fila por cada combinación de `importer` + `exporter` + `industry`. ~680.000 filas por año. Este es el archivo más grande y granular.

| Columna | Tipo | Descripción | Rango |
| :--- | :--- | :--- | :--- |
| `importer` | `str` | Código ISO3 del país **importador** (el que tiene la dependencia). | — |
| `exporter` | `str` | Código ISO3 del país **exportador** (el que suministra). | — |
| `industry` | `str` | Nombre de la industria/producto (ej: `"154 Manufacturing services..."`, `"Eggs"`, `"Crude petroleum"`). Algunos llevan ID numérico al inicio; otros no. | — |
| `dep_total` | `float64` | **Dependencia Total**. Suma de la directa e indirecta. Mide la vulnerabilidad completa de A respecto a B en esa industria. | 0 – 1 |
| `dep_direct` | `float64` | **Dependencia Directa**. Cuánto depende A de B sin intermediarios. | 0 – 1 |
| `dep_indirect` | `float64` | **Dependencia Indirecta**. Riesgo surgido a través de terceros países que canalizan el suministro. | 0 – 1 |
| `top_intermediary` | `str` | Código ISO3 del **principal intermediario** en la cadena de suministro entre A y B para esa industria. | — |
| `path_strength` | `float64` | **Fuerza de la Ruta**. Mide cuánto del flujo comercial pasa por el `top_intermediary`. Valores altos indican un cuello de botella crítico. | 0 – 1 |

**Usos previstos:**
*   Treemaps de composición de riesgos por país.
*   Cálculo de las **4 categorías sectoriales** (Agro, Energía, Manufactura, Servicios) mediante clasificación semántica del campo `industry`.
*   Diagramas Sankey de flujo (Exportador → Intermediario → Importador).
*   Identificación de cuellos de botella industriales.

---

### 0.3 `hubs_{year}.parquet` — Centralidad e Intermediación

**Estructura:** Cross-Sectional (País). Una fila por país. ~236 filas por año. Mide la posición de cada país como **nodo de tránsito** en la red comercial global.

| Columna | Tipo | Descripción | Rango |
| :--- | :--- | :--- | :--- |
| `country` | `str` | Código ISO3 del país. **Clave primaria.** | — |
| `frequency_total` | `int64` | **Frecuencia de Intermediación**. Número de veces que este país aparece como `top_intermediary` en las relaciones globales. Mide cuántas rutas comerciales pasan por él. | ≥ 0 |
| `strength_total` | `float64` | **Fuerza de Intermediación**. Suma de las `path_strength` de todas las rutas que pasan por este país. Mide la intensidad acumulada de su papel como hub. | ≥ 0 |
| `freq_norm` | `float64` | Frecuencia normalizada (0-1) respecto al máximo global. | 0 – 1 |
| `strength_norm` | `float64` | Fuerza normalizada (0-1) respecto al máximo global. | 0 – 1 |
| `global_score` | `float64` | **Puntuación Global de Hub**. Promedio de `freq_norm` y `strength_norm`. Sintetiza la importancia del país como intermediario. | 0 – 1 |
| `global_rank` | `int32` | Posición en el ranking mundial de hubs (1 = mayor intermediario). | 1 – 236 |
| `year` | `int64` | Año del corte de datos. | 2016–2022 |

**Usos previstos:**
*   Rankings de "Países Pivote" (ej: Alemania, China como hubs).
*   Mapas de influencia estratégica y soberanía de tránsito.
*   Identificación de países cuya disrupción afectaría a múltiples cadenas de suministro.

---

### 0.4 `bilateral_{year}.parquet` — Relaciones Bilaterales

**Estructura:** Matriz Bilateral (Formato Long). Una fila por cada tripleta `exporter` + `importer` + `industry`. ~325.000 filas por año. Representa la red de dependencias bilaterales desagregada por producto.

| Columna | Tipo | Descripción | Rango |
| :--- | :--- | :--- | :--- |
| `exporter` | `str` | Código ISO3 del país exportador. | — |
| `importer` | `str` | Código ISO3 del país importador. | — |
| `industry` | `str` | Nombre de la industria/producto. | — |
| `criticidad` | `float64` | **Criticidad Bilateral**. Mide la importancia estratégica de esta relación comercial específica. Combina el volumen de comercio con la dificultad de sustitución del proveedor. | 0 – 1 |
| `dependency` | `float64` | **Dependencia Bilateral**. Grado en que el importador depende del exportador para esa industria. | 0 – 1 |

**Usos previstos:**
*   Análisis de socios directos ("¿De quién depende España en semiconductores?").
*   Alertas de riesgo bilateral (filtrar pares con alta criticidad y alta dependencia).
*   Inputs para el gráfico de "Principales Socios" en la ficha de país.

---

### 0.5 `dependencies_{year}.parquet` — Rankings Globales de Productos

**Estructura:** Cruce (País-Producto). Una fila por combinación de `dependent_country` + `industry`. ~3.540 filas por año. Es el archivo más compacto; contiene solo los productos con dependencias significativas.

| Columna | Tipo | Descripción | Rango |
| :--- | :--- | :--- | :--- |
| `dependent_country` | `str` | Código ISO3 del país dependiente. | — |
| `industry` | `str` | Nombre del producto/industria que genera la dependencia. | — |
| `dependency_value` | `float64` | **Valor de Dependencia**. Intensidad de la dependencia del país en ese producto específico. | 0 – 1 |

**Usos previstos:**
*   Rankings granulares: "Top 10 productos más críticos para España".
*   Alimentación del Treemap de riesgos críticos.
*   Identificación de industrias vulnerables a nivel global.

---

### Tabla Resumen

| Archivo Fuente | Estructura / Cobertura | Granularidad (Fila) | Indicadores Clave | Uso Previsto |
| :--- | :--- | :--- | :--- | :--- |
| **`profiles_{year}`** | Cross-Sectional (País) | 1 fila por país | `vulnerability`, `importance`, `num_suppliers_effective` | KPIs, Rankings ISE, Series Temporales |
| **`explorer_{year}`** | Cruce (País × País × Industria) | 1 fila por relación bilateral-industria | `dep_direct`, `dep_indirect`, `path_strength` | Treemaps, Análisis Sectorial, Sankey |
| **`hubs_{year}`** | Cross-Sectional (Centralidad) | 1 fila por país | `frequency_total`, `global_score` | Mapas de influencia, Rankings de Hubs |
| **`bilateral_{year}`** | Matriz Bilateral (Long) | 1 fila por par país-industria | `criticidad`, `dependency` | Análisis de socios, Alertas bilaterales |
| **`dependencies_{year}`** | Cruce (País × Producto) | 1 fila por país-producto | `dependency_value` | Rankings de productos críticos |

**Nota Técnica para el Desarrollo:**

*   **Optimización de Memoria (Tidy Data)**: Los archivos NO son matrices cuadradas densas ($N \times N$), sino listas "largas" (formato Tidy) donde cada fila es una relación activa. Esto permite una carga rápida en el frontend.
*   **Series Temporales**: La dimensión "Tiempo" se maneja mediante el sufijo `{year}`. Cada archivo es un "corte anual" independiente.
*   **Heterogeneidad en `industry`**: Los nombres de producto no siguen un formato uniforme (algunos llevan ID numérico, otros solo texto libre como `"Eggs"` o `"Crude petroleum"`). El motor de clasificación semántica en `build_fragmented.py` resuelve esta ambigüedad.

---

Esta propuesta detalla la integración de visualizaciones avanzadas en el dashboard, inspiradas en los benchmarks internacionales de complejidad económica (OEC, Atlas, Spiceflow) y aprovechando las variables de red disponibles en nuestra base de datos.

## 1. Perfil de País: Mezcla de Riesgos (Estilo OEC/Atlas)

### Treemap de Dependencias Críticas
*   **Variable:** `industry` y `dep_total`.
*   **Visualización:** Sustituir la tabla de "Top Dependencias" por un **Treemap interactivo**.
*   **Uso:** El tamaño de cada cuadro representa el peso de la dependencia en la seguridad económica del país. El color se asigna por sector (Manufactura, Energético, etc.).
*   **Valor:** Permite identificar de un vistazo si la vulnerabilidad de un país está concentrada en un solo sector o atomizada en muchos productos.

### Gráfico de Evolución Sectorial (Small Multiples)
*   **Variable:** Intensidad de la Vulnerabilidad agregada por **Media (Promedio)**.
*   **Visualización:** Cuatro gráficos independientes apilados verticalmente (Agro, Energía, Manufactura, Servicios).
*   **Lógica de Clasificación Semántica (Mapping):**
    *   Debido a la heterogeneidad de los nombres de producto en los Parquet (algunos con ID numérico y otros solo texto), se utiliza una clasificación híbrida:
    *   **Energía/Minería:** Detecta IDs específicos y palabras clave como `oil`, `gas`, `fuel`, `crude`, `coal`, `mining`, `energy`.
    *   **Agricultura:** Detecta IDs iniciales y términos como `wheat`, `maize`, `crops`, `livestock`, `eggs`, `fish`.
    *   **Manufactura:** Cubre el núcleo de transformación industrial (IDs 36-153).
    *   **Servicios:** IDs > 153 y términos de servicios (`transport`, `financial`, `repair`, `public`).
*   **Normalización (Media vs Suma):**
    *   **Por qué NO sumar:** Sectores con miles de productos (Servicios) eclipsan visualmente a sectores críticos de pocos productos (Energía).
    *   **Propósito:** Al usar el **Promedio**, la escala es siempre 0-1 (o 0-100%). Esto mide la "Intensidad del Riesgo". Permite observar si la vulnerabilidad media de las importaciones energéticas ha bajado, reflejando una mejora en la seguridad nacional.
*   **Valor:** Responder a: ¿Es hoy cada kilo de gas importado menos arriesgado que hace 7 años? (Tendencia de resiliencia estructural).

### Brecha Directa/Indirecta por Sector
*   **Visualización:** Gráfico de barras agrupadas/apiladas (Directa en Rojo, Indirecta en Azul).
*   **Cálculo:** También usa la **Media** por sector para que las barras de Energía y Manufactura sean comparables y no queden a "cero" por escala frente a Servicios.

---

## 2. Explorador Industrial: El "Rastro" del Riesgo (Estilo Spiceflow)

### Diagrama de Flujo (Sankey)
*   **Variable:** `exporter` (Origen) → `top_intermediary` (Hub) → `importer` (Destino).
*   **Visualización:** Una cinta de flujo que conecta los tres puntos. El grosor de la cinta es la `path_strength`.
*   **Valor:** Visualización CRÍTICA para que el usuario entienda que el riesgo no es bilateral (A depende de B), sino de red (A depende de B porque B es el único camino desde C).

---

## 3. Sección de Hubs: Análisis de Red Avanzado

### Matriz de Resiliencia Industrial
*   **Variable:** `num_suppliers_effective` (Eficiencia/Diversificación) vs `vulnerability` (Riesgo).
*   **Visualización:** Gráfico de cuadrantes (Scatter plot avanzado).
*   **Valor:** Clasificar industrias en:
    *   **Seguras:** Diversificadas y con baja dependencia.
    *   **Trampas de Eficiencia:** Muy dependientes de pocos proveedores (Baja diversificación).
    *   **Zonas de Alerta:** Alta dependencia y alta centralidad de hubs.

### Mapa de "Soberanía de Tránsito"
*   **Variable:** `top_intermediary == importer`.
*   **Visualización:** Capa de color especial en el mapa global.
*   **Valor:** Resaltar países que han "internalizado" sus rutas de suministro críticas, actuando ellos mismos como sus propios hubs.

---

## 4. Estructura de Datos y Flujo de Trabajo

*   **Archivo Maestro:** `explorer_{year}.parquet`. Contiene el 90% de la información necesaria para los flujos y treemaps.
*   **Pipeline:** El script `build_fragmented.py` deberá extraer fragmentos de datos específicos para alimentar los Treemaps y Sankeys sin sobrecargar el navegador.
*   **Tecnología:** Se mantendrá **Plotly.js** para Treemaps y Mapas, e integraremos **D3.js** o los módulos de **Sankey de Plotly** para los diagramas de flujo.

---

## Próximos Pasos (Hoja de Ruta)

1.  **Fase A:** Implementar el Treemap en el modal de Perfil del País (Impacto visual inmediato).
2.  **Fase B:** Crear el nuevo componente de Flujo Industrial con Sankey.
3.  **Fase C:** Segmentar el Dashboard en pestañas (General, Redes, Industrial) para manejar la mayor complejidad visual, similar al EPO Technology Dashboard.

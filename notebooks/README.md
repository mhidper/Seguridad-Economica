# 📓 Directorio de Notebooks y Análisis

Este directorio es el núcleo de cálculo, investigación y manipulación de datos del proyecto **Índice de Dependencia Económica Elcano (IDEE)**. El IDEE evalúa la posición de fortaleza o vulnerabilidad de un país en el contexto del comercio internacional de una mercancía, bien o servicio a nivel internacional. Las redes de comercio entre varios países, de un determinado producto, no implican que las adquisiciones de un país consumidor final de ese bien dependa de todos los países, pero sí de un entramado de relaciones comerciales de intermediación que puede llegar a afectarle no solo de forma directa, sino indirecta.

### 🔍 ¿Por qué el índice puede superar 1?
El IDEE es una **métrica de exposición**, no una probabilidad o cuota. Cuando existen múltiples intermediarios independientes que importan el mismo producto de un proveedor común (por ejemplo, importas de Alemania, Francia e Italia, y los tres dependen de China), la vulnerabilidad ante un shock en el origen es extremadamente alta porque todas las rutas se verán afectadas al mismo tiempo. Al sumar las fuerzas de estos caminos paralelos de intermediación, la Dependencia Total ($DT$) puede superar matemáticamente el valor de 1 (100%). Esto no es un doble conteo, sino información valiosa sobre la redundancia y fragilidad del entramado comercial.

### 📦 Recuadro didáctico: Qué mide y qué no mide el IDEE
* **Red comercial, no trazabilidad física**: Mide la dependencia logística y financiera en los flujos comerciales sectoriales brutos ($T_{ab} = x_{ab} / S_b$, donde $S_b$ es la suma de importaciones y producción local), no la trayectoria física de un átomo o producto concreto.
* **Supuesto de proporcionalidad (mixing)**: Las exportaciones de un país combinan proporcionalmente lo que produce y lo que importa en ese sector.
* **Diferencia con el HHI**: El HHI solo ve aduanas directas; el IDEE revela la concentración de origen real en la red.
* **Diferencia con TiVA**: TiVA mide el valor añadido neto cruzando múltiples industrias; el IDEE mide la vulnerabilidad bruta dentro del mismo sector. Aquí conviven tanto los *scripts* de producción que alimentan el *dashboard* web, como investigaciones ad-hoc y recursos gráficos orientados a informes.

## 📂 Estructura del Directorio

### 1. Notebooks Raíz (Exploración y Preparación)
*   **`00_data_processing.ipynb`**: Herramienta auxiliar de *Data Science*. Toma los archivos anuales brutos de dependencias (`.csv.gz`) y los consolida/optimiza en un único archivo global `dependencies_full.parquet`. Ideal para hacer consultas rápidas con Pandas (no interviene en la producción web).
*   **`01_exploration_CVG.ipynb`**: Investigación profunda sobre Cadenas de Valor Globales (CVG). Analiza interdependencias de sectores productivos específicos (como la industria del automóvil) rastreando cadenas enteras (*upstream*) utilizando matrices input-output (como la base de datos WIOD).

### 2. Subdirectorios Principales

#### ⚙️ `analysis/` (Pipeline Principal de Producción)
Contiene los *scripts* críticos que definen la metodología y calculan el IDEE oficial:
*   **`00_dependency.ipynb` (El Motor)**: Procesa los datos comerciales masivos para calcular todas las dependencias directas e indirectas por industria.
*   **`idc_architect.py` (El Arquitecto)**: Destila y condensa los pesados cálculos matemáticos del Motor en archivos `.parquet` ágiles y analíticos (vulnerabilidad, hubs, rutas).

#### 📊 `visualization/` (Publicaciones y Gráficos)
Dedicado a la creación de material visual estático (PNG, PDF) para ser incluido en documentos de texto o presentaciones oficiales:
*   **`nota_elcano.ipynb`**: Figuras oficiales para la "Nota Elcano".
*   **`chimerica.ipynb`**: Análisis sobre la relación e interdependencia tecnológica/económica entre China y EE. UU.
*   **`figuras_espana_ministro.ipynb`**: Material gráfico enfocado exclusivamente en las dependencias y la posición estratégica de España para uso directivo.
*   **`figuras.ipynb` y `figuras_new.ipynb`**: Librería general de rutinas para graficar mapas de calor, barras cruzadas, etc.
*   **`images/`**: Directorio donde se guardan automáticamente todas estas figuras.

#### 📝 `paper_ise/` (Redacción Académica)
*   **`ejercicio_paper.ipynb`**: Cálculos, demostraciones o casos de estudio reducidos diseñados específicamente para respaldar teóricamente el artículo metodológico de LaTeX (`methodology.tex`). Sirve de puente entre la teoría matemática documentada y la práctica real.

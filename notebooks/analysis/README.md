# ⚙️ Pipeline de Producción (Directorio Analysis)

Este subdirectorio contiene el corazón algorítmico y estadístico del **Índice de Dependencia Económica Elcano (IDEE)**. El IDEE evalúa la posición de fortaleza o vulnerabilidad de un país en el contexto del comercio internacional de una mercancía, bien o servicio a nivel internacional. Las redes de comercio entre varios países, de un determinado producto, no implican que las adquisiciones de un país consumidor final de ese bien dependa de todos los países, pero sí de un entramado de relaciones comerciales de intermediación que puede llegar a afectarle no solo de forma directa, sino indirecta.

### 🔍 ¿Por qué el índice puede superar 1?
El IDEE es una **métrica de exposición**, no una probabilidad o cuota. Cuando existen múltiples intermediarios independientes que importan el mismo producto de un proveedor común (por ejemplo, importas de Alemania, Francia e Italia, y los tres dependen de China), la vulnerabilidad ante un shock en el origen es extremadamente alta porque todas las rutas se verán afectadas al mismo tiempo. Al sumar las fuerzas de estos caminos paralelos de intermediación, la Dependencia Total ($DT$) puede superar matemáticamente el valor de 1 (100%). Esto no es un doble conteo, sino información valiosa sobre la redundancia y fragilidad del entramado comercial.

### 📦 Recuadro didáctico: Qué mide y qué no mide el IDEE
* **Red comercial, no trazabilidad física**: Mide la dependencia logística y financiera en los flujos comerciales sectoriales brutos ($T_{ab} = x_{ab} / S_b$, donde $S_b$ es la suma de importaciones y producción local), no la trayectoria física de un átomo o producto concreto.
* **Supuesto de proporcionalidad (mixing)**: Las exportaciones de un país combinan proporcionalmente lo que produce y lo que importa en ese sector.
* **Diferencia con el HHI**: El HHI solo ve aduanas directas; el IDEE revela la concentración de origen real en la red.
* **Diferencia con TiVA**: TiVA mide el valor añadido neto cruzando múltiples industrias; el IDEE mide la vulnerabilidad bruta dentro del mismo sector. Aquí residen los *scripts* principales de producción, encargados de procesar la base de datos de comercio bruto, calcular las vulnerabilidades sistémicas en cadena (directas e indirectas) y estructurar los resultados finales.

## 📂 Contenido Principal (El Pipeline)

### 1. El Motor de Cálculo
*   **`00_dependency.ipynb`**: Es el **Cerebro** del proyecto. 
    *   Procesa los datos estandarizados.
    *   Aplica la metodología PIVI (análisis de caminos en grafos) para rastrear dependencias directas e indirectas por industria a lo largo de las cadenas de valor globales.
    *   Calcula las métricas de frecuencia y fuerza de intermediación.
    *   **Salida**: Diccionarios completos de red guardados en archivos masivos con compresión nativa `all_results_{año}.pkl.gz`.

### 2. El Arquitecto de Datos
*   **`idc_architect.py`**: Es el componente de **Ingeniería y Destilación**.
    *   Actúa tomando los archivos pesados `.pkl` generados por el Motor.
    *   Agrega los resultados para calcular el IDEE a nivel nacional, los índices de concentración (HHI) y el desglose del Riesgo Oculto.
    *   **Salida**: Genera bases de datos estructuradas ultraligeras (`profiles_{año}.parquet`, `explorer_{año}.parquet` (que incluye los ponderadores en dólares brutos `trade_value` y `trade_weight`), `hubs_{año}.parquet`, etc.) que se envían a `data/processed/historico/` para alimentar la web.

## 🛠️ Herramientas Auxiliares e Histórico

*   **`inspect_esp_2022.py`**: *Script* auxiliar de inspección rápida de datos. Permite extraer y validar información crítica específica sobre España en el año 2022 directamente desde consola, sirviendo como testeo de calidad (QA) del *output* del modelo.
*   **`research_archives/`**: Copias de seguridad de pruebas analíticas y exploraciones matemáticas que guiaron el desarrollo actual del índice. Se conservan como memoria metodológica.

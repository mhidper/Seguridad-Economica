# Nota Metodológica: Extensión CVG del IDC

**Fecha:** Marzo 2026
**Estado:** Primera iteración metodológica completada y validada.

## 1. Visión General
Esta nota documenta los avances, descubrimientos y la arquitectura desarrollada para integrar las **Cadenas de Valor Globales (CVG)** en el marco del **Índice de Dependencia Comercial (IDC)**. El objetivo principal es pasar de medir la vulnerabilidad puramente comercial y aduanera (primer nivel o de red simple) a cuantificar la vulnerabilidad estructural o "riesgo oculto" (dependencia "upstream").

### ¿Qué aporta el enfoque CVG?
El informe tradicional de comercio exterior solo mide a quién compramos el bien final. Sin embargo, en la economía global del siglo XXI, ese producto es el ensamblaje final de cientos de piezas y recursos aportados por terceros países. La extensión CVG persigue responder: *Si hay una disrupción en A, ¿cómo afecta a nuestra compra final proveniente de B?*

---

## 2. Origen de Datos y "Receta de Producción"
Originalmente en el paper teórico se contemplaba el uso de la base de datos WIOD 2014. No obstante, para obtener mayor granularidad, países y cobertura temporal más reciente, se optó finalmente por utilizar la **OECD ICIO (Inter-Country Input-Output) - Edición 2025 (extendida)**.

*   **Matriz $\alpha$ (Receta global):** A partir del archivo en bruto de la OECD (`2022_SML.csv`), desarrollamos un parser matricial (`01_parse_icio.py`) que extrajo las transacciones intermedias y las agregó a nivel global para obtener la matriz $\alpha$ industrial (tamaño 45x45 en la nomenclatura ISIC Rev.4).
*   **Interpretación:** Esta matriz extrae las especificaciones de fabricación. Por ejemplo, nos permite demostrar de manera objetivable que a nivel global el 10.7% del ensamblaje del sector Farmacéutico (C21) y el 9.6% de la Agricultura química requiere Química Pesada/Avanzada (C20) como insumo necesario.

---

## 3. Mapping Estratégico (ITP a ICIO)
El índice nativo (IDC) opera con altísima resolución trabajando con **170 industrias granulares ITP**, mientras que la matriz ICIO estandariza la macroeconomía en **45 agregados**.
*   **Solución:** Se desarrolló un diccionario puente o mapping de alta fiabilidad (`02_sector_mapping.py`) que encuadra estratégicamente cada una de las 170 industrias dentro de su nodo pertinente ICIO.
*   **Casos clave controlados:** Farmacia (ID 87 $\to$ C21), Electrónica (Múltiples IDs como 124, 131-137 $\to$ C26), Vehículos de motor y chasis (IDs 138-140 $\to$ C29).

---

## 4. Arquitectura de Integración (La Ecuación CVG)
Para descubrir y medir estadísticamente el **Riesgo Oculto**, se programó la conjunción matricial del IDC Parquet con la matriz de coeficientes $\alpha$.
A través de `03_integrate_cvg.py`, materializamos el cálculo por bloques:

$$DT_{CVG} = DependenciaDirecta + \sum (\alpha \times DependenciaUpstream(Total))$$

De este modo el modelo asume que: Nuestra vulnerabilidad global en Coches respecto a Alemania no es solo las veces que ellos nos lo importan y nosotros no tenemos diversificación para comprarlo en otro sitio, sino que incluye el riesgo de que Alemania no sea capaz de ensamblarlo si Alemania sufre de una sobredependencia del Aluminio en China o Rusia.

---

## 5. Hallazgos Preliminares: Redefinición de los Cuellos de Botella (España 2022)

Tras procesar la matriz a nivel mundial para 2022, comprobamos el marco empírico sobre el caso español, donde emergen evidencias fundamentales en la naturaleza del riesgo, agrupando las cadenas en dos perfiles geopolíticos muy marcados:

### Caso A: Dependencia Upstream Física y Energética (Sector Salud y Automoción)
*   *Análisis:* Examinando al Sector Farmacéutico y la Automoción, encontramos fuertes anclajes hacia la dependencia **Física**, que a su vez pivota intensamente sobre subproductos petroquímicos (`C20` y `C19`) o el Acero (`C24A`). El desabastecimiento de "metales básicos" o "fertilizantes/solventes" paraliza por propagación upstream a los proveedores alemanes y chinos de España. 
*   *Relevancia:* Sectores como la automoción pueden presentar un riesgo indirecto de bloqueo frente a tensionamientos remotos (ej. Bloqueos en Ormuz) aunque la balanza comercial de España carezca de importaciones directas de la zona del conflicto. La crisis viaja por onda expansiva.

### Caso B: Dependencia Upstream Intangible (Sector Electrónica C26)
*   *Análisis:* A la hora de calcular topografías del riesgo para la tecnología y las pantallas LED o los microcomponentes (`06_electronics_analysis.py`), la lógica dice que China debería liderar nuestra vulnerabilidad con enorme holgura. Empero, el **Top #1 de Riesgo Oculto resultante fue EE.UU**.
*   *Relevancia:* La matriz reveló que casi un 3% (un peso colosal) del valor de la electrónica reside en los servicios empresariales subyacentes, software cerrado, y licencias por **Propiedad Intelectual (Sector M)** o finanzas **(Sector K)**. La electrónica tiene un cerebro occidental de papel y un cuerpo asiático. Nuestro riesgo oculto tecnológico es, en gran medida, un monopolio de patentes y diseño estadounidense, exponiendo la trampa de medir solo las pantallas cristalinas en la frontera.

---

## 6. Próximos pasos a retomar
Cuando el desarrollo regrese al frente activo en los próximos días, el *roadmap* pendiente consta de:
1.  **Exploración Estadística:** Analizar la desviación estándar de la diferencia entre $DT_{IDC}$ original y $DT_{CVG}$ para obtener un índice puro de `Hidden_Risk Index` global por países.
2.  **Impactos Visuales:** Construir gráficos de Redes o Diagramas de Sankey que perfilen visualmente la evaporación del origen del coche que ensambla y vende Alemania hasta la mina de Acero china en un PDF estético.
3.  **Transferencia Textual a los Deliverables:** Con los datos ya materializados analíticamente (scripts en Python funcionales), proceder con la incorporación teórica/práctica a través de apartados en los capítulos dedicados del paper académico `ise_cvg.tex`, añadiendo las métricas del efecto látigo.

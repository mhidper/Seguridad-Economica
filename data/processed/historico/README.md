# Directorio Histórico de Salidas (Dashboard IBM)

Este directorio contiene los archivos Parquet procesados por el motor arquitecto (`idc_architect.py`). Estos ficheros representan la ingesta final de datos (backend) utilizada para visualizar los indicadores de Seguridad Económica en el dashboard web interactivo.

## Nota sobre versiones "UE"
Todos los ficheros descritos a continuación pueden presentar un sufijo `_UE` en su nombre (por ejemplo, `profiles_2022_UE.parquet` en contraposición a `profiles_2022.parquet`).
La estructura, columnas e información que contienen **son idénticas** en ambos casos. La única diferencia es que la versión `_UE` consolida a los 27 Estados miembros de la Unión Europea como una única entidad soberana (con el código `EU27`), eliminando el comercio intracomunitario para revelar la dependencia real del bloque europeo frente al resto del mundo.

---

## Estructura y Contenido de los Ficheros

### 1. `profiles_{año}.parquet` (Perfiles Nacionales)
Contiene las estadísticas agregadas a nivel de país, necesarias para pintar los mapas y los rankings generales.
*   **`country`**: Código ISO-3 del país.
*   **`vulnerability`**: Índice de Dependencia Económica Elcano (IDEE) / Vulnerabilidad Total agregada.
*   **`indirect_share`**: Qué porcentaje del riesgo total se debe a dependencias indirectas (vía terceros).
*   **`num_suppliers_effective`**: Número efectivo de proveedores (inverso del Índice Herfindahl-Hirschman, HHI) agregado.
*   **`importance`**: Relevancia sistémica del país como exportador global (poder de mercado).
*   **`global_rank`**: Posición del país en el ranking mundial de vulnerabilidad.
*   **`year`**: Año de los datos.

### 2. `hubs_{año}.parquet` (Global Hub Score)
Ranking global de países actuando como intermediarios críticos en las redes de suministro.
*   **`country`**: Código ISO-3 del país intermediario.
*   **`frequency_total`**: Cuántas veces aparece en rutas críticas.
*   **`strength_total`**: Suma de las fuerzas (dependencias originadas) de los caminos en los que intermedia.
*   **`freq_norm` / `strength_norm`**: Valores normalizados (0-1) frente al líder global.
*   **`global_score`**: Índice de Hub Global (GHS) compuesto (0.4 Frecuencia + 0.6 Fuerza).
*   **`global_rank`**: Posición mundial como Hub.

### 3. `hubs_sector_{año}.parquet` (Hubs Desagregados)
Misma métrica que la anterior, pero calculada y ranqueada dentro de cada industria específica.
*   Incluye columnas equivalentes (score, rango), pero segmentadas por la columna **`industry`** (nombre del sector).

### 4. `explorer_{año}.parquet` (Explorador Industrial)
Es el fichero más granular y extenso. Contiene la radiografía profunda de la dependencia de un país respecto a sus proveedores (hasta el Top 20) dentro de un sector, alimentando la pestaña "Industry Explorer".
*   **`importer` / `exporter`**: País dependiente y su proveedor.
*   **`industry`**: Sector analizado.
*   **`dep_total`**: Dependencia comercial total.
*   **`dep_direct` / `dep_indirect`**: Desglose entre dependencia aduanera directa y riesgo transitivo.
*   **`top_intermediary`**: Cadena de texto con los países puente del camino más crítico (ej: "CHN  DEU").
*   **`path_strength`**: Severidad de ese camino principal.
*   **`hhi_sector` / `eff_suppliers_sector`**: Concentración de mercado en ese sector concreto.

### 5. `critical_{año}.parquet` (Relaciones Críticas y Riesgo Oculto)
Filtra y almacena solo aquellos vínculos comerciales con muy alta dependencia ($DT \ge 0.5$). Se usa para levantar banderas de alerta sobre escasez de alternativas.
*   Contiene la dependencia directa/indirecta y los factores de **`hidden_risk_abs`** (riesgo adicional no capturado en aduanas).
*   **`caminos_alternativos`**: Número de rutas puente encontradas para sortear cuellos de botella.
*   **`criticidad`**: Indicador de 0 a 1 que señala el peligro por falta de diversificación (baja penalización si existen 3 o más rutas).

### 6. `bilateral_{año}.parquet` (Mapeo de Riesgo Bilateral)
Fichero de relaciones comerciales de riesgo medio y alto ($DT > 0.05$). Utilizado fundamentalmente para pintar redes y gráficos de flujos.
*   Registra el **`exporter`**, **`importer`**, la industria y el nivel de **`criticidad`** y **`dependency`**.

### 7. `dependencies_{año}.parquet` (Top Dependencias para Treemaps)
Resumen súper ligero que contiene únicamente el Top 15 de vulnerabilidades más fuertes por país. 
*   **`dependent_country`**: País analizado.
*   **`industry`**: Sector dependiente.
*   **`dependency_value`**: Magnitud del riesgo.
*   Se utiliza para renderizar rápidamente gráficos de bloques (Treemaps) sin tener que procesar la red entera.

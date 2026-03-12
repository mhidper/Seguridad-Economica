# 📋 Guión de Reunión: Desarrollo Frontend Dashboard IDC-CVG

**Objetivo de la sesión:** Alinear la arquitectura de datos existente con la propuesta de experiencia de usuario y visualización de la agencia de desarrollo web.

---

## PARTE 1: La Arquitectura de los Datos (Backend & Data)
*Mensaje clave para la agencia: "No necesitamos que desarrolléis un backend complejo ni una base de datos SQL. Os daremos archivos JSON estáticos altamente optimizados que el cliente (navegador) consumirá directamente."*

### 1.1 Estructura de los Archivos
Entregaremos un directorio de datos estructurado en dos niveles:
*   **`meta.json`**: El archivo maestro. Contiene el diccionario/catálogo de todas las industrias (170 sectores), el listado de años y matrices pequeñas con la evolución histórica global.
*   **`year_YYYY.json`**: Un archivo por cada año (desde 2016 hasta 2022). Son "fotos fijas" del estado del mundo en ese momento.

### 1.2 El Formato Matricial (¡Ojo Devs!)
Para ahorrar ancho de banda y garantizar latencia casi cero, **no** usamos un array de objetos normal. Usamos un formato columna-dato:
```json
{
  "c": ["country", "vulnerability", "importance"], 
  "d": [ 
         ["ESP", 0.15, 0.11], 
         ["CHN", 0.24, 0.53] 
       ]
}
```
*   *Nota para ellos:* El Frontend tendrá que "zipear" o emparejar las keys `"c"` con los arrays en `"d"` al cargarlos en memoria.

### 1.3 Bloques de datos por Año
Cada `year_YYYY.json` proporciona tres bloques clave que alimentarán las vistas:
1.  **`profiles`**: Perfil macro de cada país (`vulnerability`, `importance`, `indirect_share`).
2.  **`hubs`**: Quiénes son las grandes potencias cuello de botella (`global_score`).
3.  **`dependencies`**: El detalle micro. Qué país exacto, depende de qué sector y con qué gravedad (`dependency_value`).

### 1.4 Cruces y Relaciones (Claves Primarias)
Toda la reactividad del dashboard gira en torno a dos variables de cruce muy simples:
*   **Código de País**: Formato ISO-3 (ej. `ESP`, `USA`, `CHN`).
*   **Código de Industria**: Numérico (del 1 al 170). Se cruza con el catálogo en `meta.json` para obtener el nombre legible (ej. "Motor Vehicles").

### 1.5 Temporalidad
*   **Alcance:** Serie histórica anual completa (actualmente 2016-2022).
*   **Actualizaciones:** Una actualización anual (cuando se publican y procesan las tablas macroeconómicas de la OECD). No hay oscilaciones diarias ni en tiempo real.

---

## PARTE 2: Reglas de Negocio (El Concepto Clave)
*Mensaje clave para la agencia: "Cuidado con los textos y etiquetas de la interfaz. Esto no es un simple panel de aduanas."*

*   **El concepto del Riesgo Oculto (CVG):** Trabajamos con Cadenas de Valor Globales. Si los datos muestran que España tiene un alto riesgo con China en "Automoción", **no significa necesariamente que importemos coches chinos**. Significa que los proveedores globales de los que compramos coches (ej. Alemania) dependen críticamente de los metales o chips de China para fabricarlos. 
*   **Lenguaje UX sugerido:** No usar "Le compramos a...", sino "Riesgo originado en..." o "Dependencia estructural de...".

---

## PARTE 3: Diseño, KPIs y Experiencia de Usuario (UI/UX)
*Mensaje clave para la agencia: "El usuario debe viajar en un embudo: de una vista mundial (macro) hasta descubrir la anatomía técnica de un sector concreto de un país (micro)."*

### 3.1 Las Métricas Core (Lo que hay que destacar)
1.  **Vulnerabilidad Global**: Termómetro general del riesgo (0 a 1).
2.  **Porcentaje de Riesgo Oculto (`indirect_share`)**: Nuestro factor diferencial. Qué parte de mi vulnerabilidad no la veo en la frontera, sino que viene "heredada".
3.  **Poder de Interrupción (`global_score`)**: Exclusivo para los gigantes. Cuántas cadenas mundiales dependen de ellos.

### 3.2 Visualizaciones Solicitadas
Sugerencias exactas para el equipo de diseño:
*   **Vista Macro Geopolítica:**
    *   **Scatter Plot (4 cuadrantes):** Eje X (Importancia) vs Eje Y (Vulnerabilidad). Nos separa visualmente a los líderes de los rehenes.
    *   **Mapa Coroplético:** Un globo / mapa mundial coloreado según calor de vulnerabilidad.
*   **Vista Nacional (al hacer clic en un País):**
    *   **Bar Charts Horizontales:** Un Ranking Top 10 de sectores críticos, con las barras coloreadas en dos tonos diferenciando "Riesgo Directo" de "Riesgo Oculto".
*   **Vista Micro Sectorial (El Efecto Látigo):**
    *   **Sankey Diagram (Nodos y Cuerdas):** Crítico para contar la historia de las cadenas de valor. Cómo la dependencia fluye de país en país hasta llegar a nosotros.

### 3.3 Expectativas de Navegación y Rendimiento
Acuerdos a cerrar en la reunión:
*   **Time-Slider Play/Pause**: Navegación principal en el pie de página para cambiar de año (2016 -> 2022) o animar la evolución. Tiene que ser una transición fluida/animada sin recargar toda la URL.
*   **Gestión de Volumen:** Nunca pintar las 170 industrias de golpe. Aplicar paginación o mostrar siempre el "Top 10" por defecto con botón "Ver más".
*   **Buscador Global:** Un *input autocomplete* donde el usuario escriba países o sectores y la vista salte directamente ahí.
*   **Transiciones instantáneas:** Como el JSON está cargado en la web, al filtrar o buscar no debe haber *spinners* o ruedas de carga lentas.

---

## 💡 PARTE 4: FAQs (Batería defensiva para preguntas técnicas)

*   *Dev:* **¿Cómo se conectará la web al servidor para traer esto?**
    *   *Respuesta:* No hace falta conexión dinámica a BBDD. Los `.json` estáticos vivirán en la misma carpeta web o en un directorio S3/CDN simple. Solo tenéis que hacer `fetch` del fichero del año correspondiente.
*   *Dev:* **El JSON tiene un formato raro con listas dentro de listas, ¿por qué?**
    *   *Respuesta:* Porque rebaja el peso del archivo casi a la mitad. Para recorrerlos, solo necesitan mapear la lista `"c"` como las *keys* de objeto al leer la lista `"d"`.
*   *Dev:* **¿Van a entrar nuevos campos o cambiar nombres de columna?**
    *   *Respuesta:* La estructura de la versión actual está cerrada y congelada en producción. Siéntanse libres de programar bajo los esquemas entregados.

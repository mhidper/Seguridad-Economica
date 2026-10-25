
## 15. Actualización anual y política de revisiones

### 15.1 Por qué un año nuevo puede mover los anteriores

La diagonal de un año no depende solo de los datos de ese año. Tres piezas usan información de otros años:

- **Anclas de la regla a.** Toman hasta tres observaciones creíbles del propio país e industria en un radio de siete
  años, anteriores **o posteriores**. Un año nuevo con observaciones puede cambiar el ancla de años previos.
- **Ventanas y empalmes.** El cociente ρ de la regla b se calcula en una ventana t−1, t, t+1, y el ajuste 2 empalma
  las series con el año más próximo con historia propia. El último año de la serie solo tiene vecinos por un lado;
  cuando llega uno nuevo, deja de ser el extremo.
- **Parámetros estructurales.** El peso exportador medio de cada país en su bloque (reglas b-export y b-solo, topes de
  bloque), la mediana de respaldo de ρ y la cuota doméstica energética q se calculan sobre la ventana 2016-2022; la
  escala κ_B, sobre 2016-2021. Si se reestimaran al añadir un año, cambiarían todos los años de la serie.

### 15.2 Cuánto se mueven: simulación con 2022

Se rehizo la diagonal como si 2022 aún no existiera (datos y parámetros hasta 2021) y se comparó con dos formas de
incorporar 2022: reestimando los parámetros con la ventana ampliada o manteniéndolos fijos. Δσ es el cambio absoluto
en la cuota doméstica del suministro, ponderado por importaciones (detalle en
`sandbox/comparacion/INFORME_SIMULACION_REVISIONES.md`).

| Año revisado | Reestimar: importaciones afectadas | Reestimar: celdas con Δσ > 5 pp | Fijar: importaciones afectadas | Fijar: celdas con Δσ > 5 pp |
|---|---|---|---|---|
| 2016-2020 (cada año) | 5,1-5,6 % | 16-30 | 0,9-1,0 % | 6-19 |
| 2021 (t−1) | 12,4 % | 730 | 4,2 % | 663 |

Con los parámetros fijos, los años anteriores a t−1 apenas se mueven (Δσ medio ≤ 0,02 pp; el residuo procede de las
anclas posteriores de la regla a). El año t−1 cambia en cualquier caso, porque deja de ser el extremo de la serie.

### 15.3 Política

1. **Parámetros de calibración fijos.** La ventana de calibración (2016-2022; 2016-2021 para κ_B) forma parte de la
   versión de la metodología. No se reestima al añadir años.
2. **Actualización ordinaria (llega el año t).** Se recalcula la diagonal completa, pero solo se recalculan y publican
   los años t y t−1. Los años anteriores conservan los valores publicados. Las cifras de los dos últimos años se
   presentan como provisionales.
3. **Revisión de la serie.** Toda la serie se recalcula y se publica como una nueva versión cuando cambia la metodología,
   cuando una nueva edición de la ITPD-E o de la ICIO revisa años pasados de forma relevante, o cuando se amplía la
   ventana de calibración. Cada revisión se acompaña de una nota con la comparación entre versiones.
4. **Requisito de datos.** Un año solo entra en el índice si existe la ICIO de ese año; si la ITPD-E llega antes, el
   pipeline se detiene y avisa.
5. **Trazabilidad.** Cada versión publicada se archiva completa (entregables, diagonal y parámetros) y el pipeline
   registra con qué versión se calculó cada año.

### 15.4 Estado de la implementación

- Aplicado: parámetros calculados una sola vez sobre la ventana 2016-2022; parada del pipeline si falta la ICIO;
  registro de huellas por año (`pipeline/estado.json`); archivo de la serie validada (`_archivo/validado_v3`).
- Pendiente antes de la primera actualización ordinaria: (i) reunir la ventana de calibración, hoy escrita en varios
  scripts, en una constante única de `imputacion/comun.py`, y derivar los años de la serie de los datos disponibles;
  (ii) añadir al pipeline el modo de actualización ordinaria, que limita motor y arquitecto a t y t−1 y conserva los
  años cerrados de la versión anterior.

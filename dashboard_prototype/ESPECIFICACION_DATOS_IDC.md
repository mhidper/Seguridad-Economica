# Especificación de datos · Dashboard de Dependencia Comercial (IDC)

**Versión**: 1.0 · 13 de mayo de 2026
**Destinatario**: equipo técnico responsable del dashboard final
**Propósito**: enumerar los ficheros fuente disponibles, los ficheros derivados necesarios para el frontend y los procesos de transformación que conectan unos con otros.

---

## 1. Vista general

El dashboard se organiza en **cuatro niveles de análisis**, cada uno con sus propias necesidades de datos:

| Nivel | Vista | Pregunta que responde |
|------|-------|----------------------|
| 1 | País / Sector | ¿De quién depende este país en este sector y cuánto? |
| 2 | País / País | ¿En qué sectores depende este país de aquel otro? |
| 3 | Comparativa multilateral | ¿Cómo se compara la dependencia de varios países frente al mismo proveedor en el mismo sector? |
| 4 | Interdependencia Global | ¿Qué países son Hubs mundiales y cómo evoluciona su centralidad? |

Cada nivel consume uno o más ficheros JSON precomputados desde los datos fuente.

---

## 2. Datos fuente disponibles

Los siguientes ficheros se generan en el pipeline de cálculo del IDC (Real Instituto Elcano / equipo de investigación). Son la **fuente de verdad**.

### 2.1 Parquets bilaterales anuales

**Ubicación**: `bilateral_YYYY.parquet` (uno por año, 2016 a último año disponible)

**Estructura**:

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `exporter` | str (ISO-3) | País proveedor |
| `importer` | str (ISO-3) | País dependiente |
| `industry` | str | Nombre de la industria (170 categorías, mezcla de servicios numerados 154-170 y productos específicos) |
| `criticidad` | float | Indicador signado de criticidad bilateral. Rango aproximado: −17 a +1. Valores muy negativos indican alta concentración del proveedor. |
| `dependency` | float | Cuota del exportador en las importaciones del importador para esa industria. Rango: 0,05 a 1,00. (Se aplica poda inferior a 0,05 para evitar inflación de datos irrelevantes.) |

**Volumen típico**: ~324.000 filas, 23 MB en memoria (parquet ~3 MB en disco).

**Cobertura**: 204 exportadores × 236 importadores × 170 industrias (con poda).

### 2.2 Ficheros existentes del pipeline actual

Ya en producción en `data_dist/`:

- `data_dist/meta.json` — metadatos generales (años disponibles, listado de industrias, año por defecto).
- `data_dist/year_YYYY.json` — perfiles país-sector por año (IDC, diversificación, ranking global, sectores macro-agregados, dependencias agregadas, `explorer_indexed` para Nivel 1).
- `data_dist/history.json` — series temporales por país de los indicadores agregados.

Estos ficheros alimentan el **Nivel 1** tal cual existe hoy y **no requieren modificación**.

---

## 3. Datos derivados que el frontend necesita

A partir de los parquets bilaterales hay que generar los siguientes JSON. Todos se cargan en el navegador, así que conviene mantenerlos ligeros.

### 3.1 `bilateral_YYYY.json` (uno por año) — Niveles 2 y 3

Versión indexada y comprimida del parquet bilateral, optimizada para consulta directa desde el navegador.

**Estructura**:

```json
{
  "year": 2022,
  "industries": ["Games and toys", "Pharmaceuticals ...", ...],
  "by_pair": {
    "ESP": {
      "CHN": [
        {"i": "Lighting equipment...", "d": 0.8753, "c": -5.67},
        {"i": "Sports goods", "d": 0.8622, "c": -7.67},
        ...
      ],
      "DEU": [...]
    },
    "DEU": {...}
  },
  "by_supplier_industry": {
    "CHN": {
      "Games and toys": [
        {"m": "JPN", "d": 0.986, "c": -2.00},
        {"m": "USA", "d": 0.985, "c": -2.67},
        ...
      ]
    }
  }
}
```

**Notas**:
- `by_pair[importer][exporter]` lista todas las industrias en que existe dependencia, ordenadas desc por `d`.
- `by_supplier_industry[exporter][industry]` lista todos los importadores, ordenados desc por `d`.
- Las claves abreviadas (`i` = industry, `d` = dependency, `c` = criticidad, `m` = importer) son obligatorias por compatibilidad con el código frontend.
- En la **demo** se filtró a 30 importadores y 20 industrias clave para mantener el tamaño bajo (487 KB). La **versión final** debe contener todos los importadores y todas las industrias relevantes, pero conviene evaluar el tamaño resultante; si supera ~5 MB, considerar segmentación por importador (`bilateral_YYYY_ESP.json`, `bilateral_YYYY_DEU.json`, etc., cargados on-demand al seleccionar país en N2/N3).

**Frecuencia de regeneración**: una vez por año, cuando llega un nuevo parquet.

### 3.2 `hubs_global.json` — Nivel 4

Índice de Hub Global (HG) precalculado para todos los años disponibles.

**Estructura propuesta para la versión final** (con histórico real):

```json
{
  "years_available": [2016, 2017, ..., 2022],
  "sectors": ["Games and toys", ...],
  "hg_total": {
    "2022": {
      "CHN": {"hg": 19616.39, "n": 24951, "norm": 100.00, "log": 2.00},
      "USA": {"hg": 2556.14, "n": 23375, "norm": 13.03, "log": 1.11},
      ...
    },
    "2021": {...}
  },
  "hg_by_sector": {
    "2022": {
      "Games and toys": {
        "CHN": {"hg": 632.63, "n": 228, "norm": 100.00, "log": 2.00},
        ...
      }
    }
  }
}
```

**Diferencia con la versión demo actual**:
- La demo trae un solo año (2022) y una serie temporal sintética. La versión final debe traer **un mapa por año**, calculado desde cada parquet histórico.
- En la demo el campo `series_demo` proporciona valores sintéticos. En la versión final ese campo desaparece y la serie temporal se construye en el frontend juntando `hg_total[año][país]` para todos los años.

**Tamaño estimado en versión final**: ~70 KB × 7 años para el agregado, más ~50 KB × 7 años × 20 sectores demo. Total estimado: ~7-8 MB si se incluyen las 170 industrias. **Recomendación**: para Nivel 4 con cobertura completa, separar en `hubs_total_all_years.json` (ligero, ~500 KB) y `hubs_sector_INDUSTRY.json` (uno por industria, ~50 KB cada uno, cargado on-demand).

**Frecuencia de regeneración**: una vez por año, cuando llega un nuevo parquet.

---

## 4. Procesos de transformación (parquet → JSON)

### 4.1 Generación de `bilateral_YYYY.json`

**Input**: `bilateral_YYYY.parquet`
**Output**: `bilateral_YYYY.json`

Algoritmo (pseudo-Python):

```python
import pandas as pd, json

df = pd.read_parquet(f'bilateral_{year}.parquet')

# Si se aplica filtro por industrias y/o importadores, hacerlo aquí.
# Versión final: idealmente no filtrar.

# Índice 1: by_pair
by_pair = {}
for (imp, exp), g in df.groupby(['importer', 'exporter']):
    by_pair.setdefault(imp, {})[exp] = [
        {'i': r.industry, 'd': round(r.dependency, 4), 'c': round(r.criticidad, 2)}
        for r in g.sort_values('dependency', ascending=False).itertuples()
    ]

# Índice 2: by_supplier_industry
by_si = {}
for (exp, ind), g in df.groupby(['exporter', 'industry']):
    by_si.setdefault(exp, {})[ind] = [
        {'m': r.importer, 'd': round(r.dependency, 4), 'c': round(r.criticidad, 2)}
        for r in g.sort_values('dependency', ascending=False).itertuples()
    ]

out = {
    'year': year,
    'industries': sorted(df['industry'].unique().tolist()),
    'by_pair': by_pair,
    'by_supplier_industry': by_si,
}

with open(f'bilateral_{year}.json', 'w') as f:
    json.dump(out, f, separators=(',', ':'))
```

### 4.2 Generación de `hubs_global.json`

**Input**: `bilateral_YYYY.parquet` para todos los años disponibles.
**Output**: `hubs_global.json`

**Definición del Índice de Hub Global (HG)**:

Para cada fila bilateral, contribución al HG = `|criticidad| × dependency`.

HG de un país (como exportador) en un año = **suma** de las contribuciones de todas sus filas (todos los importadores y todas las industrias).

HG normalizado dentro de un año = `HG_país / max(HG_de_todos_los_países_ese_año) × 100`.

HG logarítmico = `log10(max(HG_norm, 0.01))` — usado solo para coloreado del mapa, porque la distribución es de cola muy larga (China domina, escala lineal aplasta visualmente al resto).

Algoritmo:

```python
import pandas as pd, numpy as np, json

hg_total_all = {}
hg_by_sector_all = {}

for year in range(2016, 2023):  # ajustar al rango real disponible
    df = pd.read_parquet(f'bilateral_{year}.parquet')
    df['w'] = df['criticidad'].abs() * df['dependency']

    # HG agregado (todos los sectores)
    s = df.groupby('exporter').agg(hg=('w','sum'), n=('w','count')).reset_index()
    s['norm'] = (s['hg'] / s['hg'].max() * 100).round(3)
    s['log']  = np.log10(s['norm'].clip(lower=0.01)).round(3)

    hg_total_all[str(year)] = {
        r.exporter: {'hg': round(r.hg, 2), 'n': int(r.n), 'norm': r.norm, 'log': r.log}
        for r in s.itertuples()
    }

    # HG por sector
    hg_by_sector_all[str(year)] = {}
    for ind, sub in df.groupby('industry'):
        ss = sub.groupby('exporter').agg(hg=('w','sum'), n=('w','count')).reset_index()
        if ss['hg'].max() == 0: continue
        ss['norm'] = (ss['hg'] / ss['hg'].max() * 100).round(3)
        ss['log']  = np.log10(ss['norm'].clip(lower=0.01)).round(3)
        hg_by_sector_all[str(year)][ind] = {
            r.exporter: {'hg': round(r.hg, 3), 'n': int(r.n), 'norm': r.norm, 'log': r.log}
            for r in ss.itertuples()
        }

out = {
    'years_available': sorted(hg_total_all.keys()),
    'sectors': sorted({ind for y in hg_by_sector_all.values() for ind in y.keys()}),
    'hg_total': hg_total_all,
    'hg_by_sector': hg_by_sector_all,
}

with open('hubs_global.json', 'w') as f:
    json.dump(out, f, separators=(',', ':'))
```

**Notas metodológicas**:

- La elección de **suma** (no media) es deliberada: ser Hub mundial combina amplitud (en cuántos sitios eres relevante) e intensidad (cuán crítico eres allí). Una media penaliza injustamente a países con red amplia, una suma integra ambas dimensiones de forma natural.
- El uso de `|criticidad|` (valor absoluto) ignora el signo. Si en una iteración futura se decide que el signo importa (criticidad negativa = "concentración mala" frente a positiva = "concentración buena"), se debe documentar y modificar este paso.
- La normalización es **relativa al máximo de cada año**, no a un máximo global histórico. Esto significa que un país puede subir o bajar en el ranking incluso sin cambiar su HG absoluto, si otro país cambia. Es la convención más legible para el lector general, pero conviene que en la metodología publicada quede explicitado.

---

## 5. Estructura de carpetas recomendada en producción

```
proyecto/
├── index.html
├── data_dist/
│   ├── meta.json                    [pipeline existente]
│   ├── history.json                 [pipeline existente]
│   ├── year_2016.json … year_2022.json    [pipeline existente]
│   ├── bilateral_2016.json … bilateral_2022.json  [NUEVO — Niveles 2 y 3]
│   └── hubs_global.json             [NUEVO — Nivel 4]
└── (assets, etc.)
```

El frontend ya está preparado para localizar estos ficheros. Para los `bilateral_YYYY.json`, si se opta por la versión segmentada (por importador), la nomenclatura debe ser `bilateral_YYYY_ISO3.json` y el frontend deberá adaptarse para cargar el segmento correcto al seleccionar país.

---

## 6. Lo que falta por decidir

Aspectos que la versión demo no cierra y que el equipo técnico final deberá resolver con el equipo de investigación:

1. **Cobertura sectorial del Nivel 4**: la demo trabaja con 20 industrias. ¿La versión final incluye las 170? Si sí, conviene partir el JSON en ficheros por sector para no cargar todo de golpe.
2. **Estrategia de carga del Nivel 2-3**: ¿se carga el `bilateral_YYYY.json` completo (puede llegar a varios MB) o se segmenta por país y se carga on-demand?
3. **Agregaciones regionales** (UE, Mercosur, ASEAN, etc.): no contempladas en esta versión. La aproximación correcta no es promediar países, sino colapsar la matriz original a la dimensión regional antes de calcular indicadores. Pendiente para una iteración futura.
4. **Definición operativa de "Hub"**: la fórmula propuesta (suma de |criticidad| × dependency) es una decisión metodológica del equipo de investigación. Si se cambia, todos los JSON derivados deben regenerarse.
5. **Tratamiento del signo de la criticidad**: la versión actual ignora el signo (valor absoluto). Verificar con el equipo de investigación si esto es semánticamente correcto o si conviene distinguir.

---

## 7. Glosario de campos

| Campo | Significado | Origen |
|-------|------------|--------|
| `exporter` / `importer` | Códigos ISO-3 de país | Parquet fuente |
| `industry` | Nombre de industria (170 valores) | Parquet fuente |
| `dependency` (`d`) | Cuota del exportador en importaciones del importador para esa industria | Parquet fuente |
| `criticidad` (`c`) | Indicador signado de criticidad bilateral | Parquet fuente |
| `hg` | Hub Global: Σ (|criticidad| × dependency) por exportador | Derivado |
| `norm` | HG normalizado 0-100 (sobre el máximo del año/sector) | Derivado |
| `log` | log10(norm) para coloreado en escala logarítmica | Derivado |
| `n` | Número de pares bilaterales en los que el país aparece como exportador | Derivado |

# Índice de Seguridad Económica
**Real Instituto Elcano**

Análisis de dependencias económicas en cadenas de suministro globales. Este proyecto desarrolla el **Indicador de Seguridad Comercial (ISC)**, que cuantifica la seguridad económica de los países midiendo dependencias directas e indirectas en el comercio bilateral por industria.

---

## 🎯 Objetivo

Desarrollar un índice que cuantifique la seguridad económica de los países, entendida como la capacidad de resistir disrupciones en sus cadenas de suministro y comercio internacional, en un contexto de fragmentación geoeconómica y tensiones comerciales.

---

## 🔬 Metodología

El Indicador de Seguridad Comercial (ISC) se construye a partir de:

- **Fuente de datos**: International Trade and Production Database (ITP) — datos comerciales bilaterales por industria (236 países, 170 industrias).
- **Dependencia directa**: Medición del flujo comercial inmediato entre pares de países.
- **Dependencia indirecta**: Análisis de cadenas de intermediarios (hasta longitud 5) que canalizan flujos comerciales.
- **Perfiles de país**: Vulnerabilidad, importancia como exportador, número efectivo de proveedores e intermediación global.

---

## 📁 Estructura del Proyecto

```
Seguridad-Economica/
├── data/
│   ├── raw/                        # Datos ITP originales (.csv.gz en partes)
│   └── processed/                  # Datos procesados (.parquet, .pkl, .csv.gz)
│       └── dependencias_consolidadas/  # Outputs principales del pipeline
│
├── notebooks/                      # 📓 Notebooks de análisis
│   ├── 00_data_processing.ipynb        # Procesamiento alternativo (csv.gz → parquet)
│   ├── 01_exploration_CVG.ipynb        # Análisis cadena de valor automotriz (WIOD)
│   │
│   ├── analysis/                       # 🔬 Pipeline principal ISC
│   │   ├── dependency_v4.ipynb             # CORE: carga ITP, matrices, cálculo dependencias
│   │   ├── 01_build_foundations.ipynb      # CORE: construye DataFrames analíticos
│   │   ├── 02_exploit_pivi.ipynb           # CORE: explotación de resultados
│   │   ├── comunidades.ipynb               # Detección de comunidades
│   │   └── _archive/                       # Versiones anteriores (v1–v3)
│   │
│   ├── visualization/                  # 📊 Generación de figuras
│   │   ├── nota_elcano.ipynb               # Figuras para informe Elcano
│   │   ├── figuras.ipynb                   # Figuras generales
│   │   ├── figuras_new.ipynb               # Figuras actualizadas
│   │   ├── figuras_espana_ministro.ipynb   # Figuras España (presentación)
│   │   └── chimerica.ipynb                 # Análisis China-América
│   │
│   └── paper_ise/                      # 📝 Ejercicios para el paper
│       └── ejercicio_paper.ipynb
│
├── dashboard/                      # 🎨 Dashboard interactivo (Streamlit)
│   ├── app.py                          # Aplicación principal
│   ├── data_utils.py                   # Funciones de utilidad
│   └── .streamlit/                     # Configuración
│
├── docs/                           # 📚 Documentación
│   ├── Informes, briefs o notas/       # Documentos de divulgación
│   │   ├── informe ministerio/             # Informe para el Ministerio
│   │   ├── nota Elcano/                    # Notas y briefs Elcano
│   │   └── policy brief USA/              # Policy brief aranceles EEUU
│   ├── bibliografía/                   # Papers académicos de referencia
│   ├── dashboard/                      # Documentación técnica del dashboard
│   ├── images/                         # Imágenes centralizadas
│   │   ├── figures/                        # Figuras generales
│   │   ├── logos/                          # Logos institucionales
│   │   └── paper_figures/                  # Figuras del paper
│   ├── latex/                          # Documentos LaTeX
│   │   ├── paper/                          # Paper académico (.tex, .pdf)
│   │   ├── presentations/                  # Presentaciones Beamer
│   │   └── Tablas/                         # Tablas LaTeX
│   ├── metodología/                    # Anexo metodológico
│   └── trabajos pendientes/            # Documentos de gestión interna
│
├── requirements.txt                # Dependencias Python
└── README.md
```

---

## � Quick Start

### 1️⃣ Instalación
```bash
git clone [URL]
cd Seguridad-Economica
pip install -r requirements.txt
```

### 2️⃣ Pipeline principal (ISC)
Ejecutar en orden:
```bash
# Paso 1: Carga de datos ITP y cálculo de dependencias
jupyter notebook notebooks/analysis/dependency_v4.ipynb

# Paso 2: Construcción de DataFrames analíticos
jupyter notebook notebooks/analysis/01_build_foundations.ipynb

# Paso 3: Explotación y análisis de resultados
jupyter notebook notebooks/analysis/02_exploit_pivi.ipynb
```

### 3️⃣ Dashboard
```bash
cd dashboard
streamlit run app.py
```

---

## 📊 Pipeline de Datos

```
Datos ITP brutos (.gz)
    └─→ dependency_v4.ipynb
            Carga, matrices bilaterales 236×236, cálculo de dependencias
            └─→ all_results.pkl + dependencias{año}.csv.gz
                    └─→ 01_build_foundations.ipynb
                            Construye: intermediarios_globales, country_profiles,
                            relaciones_criticas, caminos_significativos (.parquet)
                            └─→ 02_exploit_pivi.ipynb (análisis ISC)
                            └─→ visualization/*.ipynb (gráficos)
                            └─→ dashboard/app.py (visualización interactiva)
```

---

## 📝 Notebooks

### Pipeline principal
| Notebook | Descripción |
|----------|-------------|
| `analysis/dependency_v4.ipynb` | Carga datos ITP, crea matrices de comercio bilateral, calcula dependencias directas e indirectas (GPU + paralelización) |
| `analysis/01_build_foundations.ipynb` | Construye 4 DataFrames analíticos a partir de los resultados del cálculo |
| `analysis/02_exploit_pivi.ipynb` | Explotación y análisis del Indicador de Seguridad Comercial |

### Análisis complementarios
| Notebook | Descripción |
|----------|-------------|
| `00_data_processing.ipynb` | Procesamiento alternativo de archivos csv.gz → parquet consolidado |
| `01_exploration_CVG.ipynb` | Análisis de la cadena de valor del sector automotriz (datos WIOD) |
| `analysis/comunidades.ipynb` | Detección de comunidades en la red de dependencias |

### Visualización
| Notebook | Descripción |
|----------|-------------|
| `visualization/nota_elcano.ipynb` | Figuras para el informe del Real Instituto Elcano |
| `visualization/figuras*.ipynb` | Generación de figuras para distintos contextos |
| `visualization/chimerica.ipynb` | Análisis visual de la relación China-América |

---

## 🔧 Requisitos técnicos

- Python 3.10+
- GPU NVIDIA (opcional, pero recomendado para `dependency_v4.ipynb`)
- Librerías principales: `pandas`, `numpy`, `torch`, `dask`, `joblib`, `scipy`, `matplotlib`, `streamlit`

---

## 👥 Equipo

**Real Instituto Elcano**
- Manuel Alejandro Hidalgo

Príncipe de Vergara, 51
28006 Madrid, España
[www.realinstitutoelcano.org](https://www.realinstitutoelcano.org)

---

**Última actualización:** 24/02/2026

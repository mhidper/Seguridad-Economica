# Índice de Seguridad Económica
**Real Instituto Elcano**

Análisis de dependencias económicas en cadenas de suministro globales.

---

## 🚀 Quick Start

### 1️⃣ Procesar Datos
```bash
jupyter notebook notebooks/00_data_processing.ipynb
```

### 2️⃣ Ejecutar Dashboard
```bash
cd dashboard
streamlit run app.py
```

---

## 📁 Estructura del Proyecto

```
Seguridad-Economica/
├── data/
│   ├── raw/                    # Datos originales (.csv.gz)
│   └── processed/              # Datos procesados (.parquet)
│
├── dashboard/                  # 🎨 Dashboard interactivo
│   ├── app.py                 # Aplicación Streamlit
│   ├── data_utils.py          # Funciones de utilidad
│   └── .streamlit/            # Configuración
│
├── notebooks/                  # 📓 Análisis
│   ├── 00_data_processing.ipynb    # Procesamiento de datos
│   ├── 01_exploration_*.ipynb      # Exploración
│   ├── 02_analysis.ipynb           # Análisis detallado
│   ├── 03_visualization.ipynb      # Visualizaciones
│   └── paper_ise/                  # Paper académico
│
└── docs/                       # 📚 Documentación
    ├── metodología/
    ├── reports/
    └── dashboard/
```

---

## 🔧 Instalación

```bash
git clone [URL]
cd Seguridad-Economica
pip install -r requirements.txt
```

---

## 📊 Dashboard

Dashboard interactivo con visualizaciones de:
- Evolución temporal de dependencias
- Top dependencias críticas
- Longitud de cadenas de suministro
- Mapas de calor de dependencias

**Deployment:** Ver [docs/dashboard/README_dashboard.md](docs/dashboard/README_dashboard.md)

---

## 📝 Notebooks

| Notebook | Descripción |
|----------|-------------|
| `00_data_processing.ipynb` | Convierte CSVs a Parquet |
| `01_exploration_*.ipynb` | Exploración inicial de datos |
| `02_analysis.ipynb` | Análisis de dependencias |
| `03_visualization.ipynb` | Visualizaciones para paper |

---

## 👥 Equipo

**Real Instituto Elcano**  
Príncipe de Vergara, 51  
28006 Madrid, España  
[www.realinstitutoelcano.org](https://www.realinstitutoelcano.org)

---

**Última actualización:** 17/10/2025

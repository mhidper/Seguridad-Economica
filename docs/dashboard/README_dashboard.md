# Dashboard Índice de Seguridad Económica
## Real Instituto Elcano

Dashboard interactivo para visualizar dependencias económicas en cadenas de suministro globales.

---

## 📋 Estructura del Proyecto

```
economic-security-index/
├── data/
│   ├── raw/                          # CSVs originales (.csv.gz)
│   │   ├── dependencias2020.csv.gz
│   │   ├── dependencias2021.csv.gz
│   │   └── dependencias2022.csv.gz
│   └── processed/                    # Datos procesados
│       └── dependencies_full.parquet
├── notebooks/
│   └── process_data.ipynb           # Notebook de procesamiento
├── app.py                           # Aplicación Streamlit principal
├── data_utils.py                    # Funciones de utilidad
├── requirements.txt                 # Dependencias Python
├── .streamlit/
│   └── config.toml                  # Configuración de Streamlit
└── README.md                        # Este archivo
```

---

## 🚀 Quick Start Local

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Procesar Datos

Ejecuta el notebook `notebooks/process_data.ipynb` para:
- Leer los CSV comprimidos
- Redondear decimales
- Generar el archivo Parquet consolidado

### 3. Ejecutar Dashboard

```bash
streamlit run app.py
```

El dashboard estará disponible en `http://localhost:8501`

---

## ☁️ Deployment en Streamlit Cloud

### Paso 1: Preparar Repositorio GitHub

1. **Crear repositorio** en GitHub (público o privado)

2. **Estructura mínima requerida:**
```
tu-repo/
├── app.py
├── data_utils.py
├── requirements.txt
├── .streamlit/
│   └── config.toml
└── processed/
    └── dependencies_full.parquet
```

⚠️ **Importante:** El archivo Parquet debe estar en el repositorio. GitHub permite archivos hasta 100MB.

3. **Push al repositorio:**
```bash
git init
git add .
git commit -m "Initial commit: Economic Security Dashboard"
git remote add origin https://github.com/tu-usuario/tu-repo.git
git push -u origin main
```

### Paso 2: Deploy en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)

2. **Sign in** con tu cuenta de GitHub

3. Click en **"New app"**

4. Configura:
   - **Repository:** tu-usuario/tu-repo
   - **Branch:** main
   - **Main file path:** app.py

5. Click **"Deploy"**

¡Listo! Tu dashboard estará disponible en `https://tu-app.streamlit.app`

---

## 📦 requirements.txt

Crea este archivo con las dependencias:

```
streamlit==1.28.0
pandas==2.1.0
plotly==5.17.0
pyarrow==13.0.0
openpyxl==3.1.2
```

---

## ⚙️ Configuración de Streamlit

Crea `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#0066CC"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F8F9FA"
textColor = "#212529"
font = "sans serif"

[server]
maxUploadSize = 200
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

---

## 🔄 Actualización de Datos

### Opción A: Manual (Recomendada para MVP)

1. Ejecuta notebook de procesamiento localmente
2. Sube nuevo Parquet a GitHub
3. Streamlit Cloud redeploya automáticamente

### Opción B: Automatizada (Futura)

```python
# En app.py, agregar función de recarga
if st.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.experimental_rerun()
```

---

## 🎨 Personalización

### Cambiar Colores

Edita en `data_utils.py`:

```python
ELCANO_COLORS = {
    'primary': '#TU_COLOR',
    'secondary': '#TU_COLOR',
    # ...
}
```

### Añadir Logo

En `app.py`, reemplaza:

```python
st.image("https://via.placeholder.com/200x80/003366/FFFFFF?text=Real+Instituto+Elcano")
```

Por:

```python
st.image("ruta/a/tu/logo.png")
```

O añade el logo al repositorio y usa ruta relativa.

---

## 📊 Uso del Dashboard

### Filtros Disponibles

- **Año:** Selecciona un año específico o "Todos"
- **País:** Filtra por país (como dependiente o proveedor)
- **Industria:** Filtra por sector industrial

### Pestañas de Visualización

1. **Evolución Temporal:** Tendencias de dependencias a lo largo del tiempo
2. **Top Dependencias:** Relaciones más críticas
3. **Longitud de Cadenas:** Distribución de complejidad de cadenas
4. **Mapa de Calor:** Matriz de dependencias entre países

### Exportación de Datos

- Descarga datos filtrados en CSV
- Vista previa de datos en tabla interactiva

---

## 🔧 Troubleshooting

### Error: "File not found"

**Solución:** Verifica que `processed/dependencies_full.parquet` existe en el repositorio.

### Error: "Memory limit exceeded"

**Solución:** 
1. Reduce el tamaño del Parquet comprimiendo más
2. Considera Streamlit Cloud paid tier
3. Filtra datos antes de cargar

### Dashboard lento

**Solución:**
1. Usa `@st.cache_data` en funciones de carga
2. Reduce número de registros en visualizaciones
3. Optimiza queries con pandas

---

## 🔐 Seguridad y Privacidad

- No incluyas API keys en el código
- Usa Streamlit Secrets para configuraciones sensibles
- Los datos del dashboard son públicos (o usa repo privado)

---

## 📈 Migración a Dash (Futuro)

El código está preparado para migración:

1. **data_utils.py** es agnóstico al framework
2. Funciones de visualización separadas
3. Lógica de negocio modular

Pasos para migrar:

```python
# En lugar de Streamlit
import dash
from dash import dcc, html

# Reutiliza data_utils.py
from data_utils import load_dependencies_data, filter_data
```

---

## 🤝 Contribuciones

Para contribuir:

1. Fork del repositorio
2. Crea branch: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m 'Add nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Crea Pull Request

---

## 📝 Licencia

Este proyecto es del Real Instituto Elcano de Estudios Internacionales y Estratégicos.

---

## 📧 Contacto

**Real Instituto Elcano**  
Príncipe de Vergara, 51  
28006 Madrid, España

Web: [www.realinstitutoelcano.org](https://www.realinstitutoelcano.org)

---

## 🗺️ Roadmap

### Fase 1: MVP (Semana 1) ✅
- [x] Dashboard básico con 4 visualizaciones
- [x] Filtros interactivos
- [x] Deploy en Streamlit Cloud

### Fase 2: Mejoras (Semanas 2-3)
- [ ] Visualizaciones de red (grafos)
- [ ] Análisis por bloques geopolíticos
- [ ] Comparativas temporales avanzadas
- [ ] Exportación a PDF

### Fase 3: Avanzado (Mes 2)
- [ ] Simulaciones de escenarios
- [ ] Indicadores de vulnerabilidad
- [ ] API REST para datos
- [ ] Migración a Dash + servidor propio

---

## 🎯 KPIs del Proyecto

| Métrica | Objetivo | Estado |
|---------|----------|--------|
| Tiempo de carga | < 3s | ✅ |
| Usuarios simultáneos | 50+ | 🔄 |
| Visualizaciones | 4+ | ✅ |
| Datos procesados | 3 años | ✅ |
| Disponibilidad | 99% | 🔄 |

---

## 📚 Recursos Adicionales

- [Documentación Streamlit](https://docs.streamlit.io)
- [Plotly Python](https://plotly.com/python/)
- [Pandas Best Practices](https://pandas.pydata.org/docs/)
- [Harvard Atlas of Economic Complexity](https://atlas.cid.harvard.edu/)

---

**Última actualización:** Octubre 2025  
**Versión:** 1.0.0
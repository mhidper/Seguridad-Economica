# Índice de Seguridad Económica (ISE) - Real Instituto Elcano

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CUDA Accelerated](https://img.shields.io/badge/CUDA-Accelerated-green.svg)](https://developer.nvidia.com/cuda-zone)

**Un indicador innovador para medir vulnerabilidades comerciales reales en un mundo de creciente fragmentación geoeconómica**

---

## 📋 Descripción del Proyecto

El **Índice de Seguridad Económica (ISE)** es una herramienta analítica avanzada desarrollada por el Real Instituto Elcano que revoluciona la medición de dependencias comerciales al capturar tanto **dependencias directas como indirectas** a través de intermediarios en las cadenas globales de valor.

### 🎯 El Problema que Resolvemos

Los indicadores tradicionales (HHI, concentración de importaciones) solo ven relaciones bilaterales directas, subestimando sistemáticamente las vulnerabilidades reales. Un país puede parecer comercialmente diversificado pero depender críticamente de una potencia económica a través de múltiples intermediarios.

### 🔬 Nuestra Solución

El ISE revela **dependencias ocultas** mediante:
- **Dependencias Directas (DD)**: Importaciones bilaterales tradicionales
- **Dependencias Indirectas (DI)**: Rutas comerciales a través de hasta 5 intermediarios
- **Dependencias Totales (DT)**: DD + DI = Vulnerabilidad real
- **Ratio de Ocultamiento**: DT/DD mide cuánto subestiman los métodos tradicionales

## 🔑 Características Clave

### 🚀 Metodología Innovadora
- **Combinación única**: Matrices Input-Output + Teoría de Redes + Algoritmos de Propagación de Shock
- **Aceleración GPU**: Procesamiento optimizado para 170 industrias × 237 países
- **Algoritmos adaptativos**: Criterios de convergencia y relevancia para eficiencia computacional

### 📊 Cobertura Extensiva
- **237 países** con cobertura global completa
- **170 sectores industriales** con detalle granular
- **Base de datos ITP 2019** con datos comerciales bilaterales

### 🔗 Extensión CVG (Cadenas de Valor Globales)
- **Análisis upstream**: Descomposición sectorial de dependencias
- **Integración WIOD**: Coeficientes técnicos de producción
- **39 sectores upstream** identificados para automóviles
- **Vulnerabilidades sistémicas** en insumos críticos

## 📈 Hallazgos Principales

### 🚨 Dependencias Ocultas Extremas
```
Caso Croacia-EE.UU. (Legumbres secas):
- Dependencia Directa: 0.5%
- Dependencia Total: 54.9%
- Ratio de Ocultamiento: 107.7x
```

### 🌏 Concentración de Poder Estructural
| País | Centralidad | Dominancia Sectorial |
|------|-------------|---------------------|
| 🇨🇳 China | 114.71 | 26/39 sectores upstream |
| 🇺🇸 EE.UU. | 57.90 | Dominancia aeroespacial |
| 🇬🇧 Reino Unido | 45.10 | Hub financiero |
| 🇩🇪 Alemania | 44.34 | Especialización tecnológica |

### ⚡ Vulnerabilidades Críticas
**Top 5 Sectores de Alto Riesgo:**
1. **Equipos informáticos**: Dependencia China 82.3% (EE.UU.)
2. **Aeronaves**: Dependencia EE.UU. 89.6% (Estonia)
3. **Baterías**: Concentración China 100% intermediación
4. **Semiconductores**: Vulnerabilidad Taiwan sistémica
5. **Metales básicos**: Cadena China-dominada (32.7%)

## 🛠️ Estructura del Proyecto

```
Seguridad-Economica/
├── src/
│   ├── data/
│   │   ├── raw/ITP/          # Datos comerciales originales
│   │   └── processed/        # Datos procesados y matrices
│   ├── notebooks/
│   │   ├── analysis/         # Cálculos principales del ISE
│   │   └── visualization/    # Generación de figuras y tablas
│   ├── core/
│   │   ├── ise_calculator.py # Algoritmos principales del ISE
│   │   ├── cvg_analyzer.py   # Análisis de cadenas de valor
│   │   └── network_utils.py  # Utilidades de teoría de redes
│   └── utils/
│       ├── data_processing.py # Procesamiento de datos
│       └── gpu_acceleration.py # Optimización GPU
├── papers/
│   ├── ise_methodology.pdf   # Paper metodológico principal
│   └── cvg_extension.pdf     # Extensión cadenas de valor
├── outputs/
│   ├── figures/             # Gráficos para publicación
│   ├── tables/              # Tablas en formato LaTeX
│   └── results/             # Matrices de dependencias
└── docs/
    ├── methodology.md       # Documentación técnica
    └── user_guide.md        # Guía de usuario
```

## 🚀 Instalación y Uso

### Requisitos del Sistema
```bash
# Requisitos básicos
Python 3.8+
CUDA 11.0+ (opcional, para aceleración GPU)
16GB RAM mínimo
```

### Instalación
```bash
# Clonar repositorio
git clone https://github.com/mhidper/Seguridad-Economica.git
cd Seguridad-Economica

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### Uso Básico
```python
from src.core.ise_calculator import calculate_all_dependencies
from src.utils.data_processing import load_trade_matrix

# Cargar datos comerciales
trade_matrix = load_trade_matrix('data/processed/matrices/')

# Calcular dependencias ISE
results = calculate_all_dependencies(
    trade_matrix, 
    max_path_length=5,
    convergence_threshold=0.01
)

# Acceder a resultados
total_dependencies = results['dependencies']
critical_intermediaries = results['intermediary_centrality']
```

### Análisis CVG
```python
from src.core.cvg_analyzer import explore_automotive_value_chains

# Analizar cadenas de valor automotrices
cvg_results = explore_automotive_value_chains(
    wiod_path='data/external/WIOD/',
    target_sector='C29',  # Automóviles
    min_intensity=0.005   # 0.5% mínimo
)
```

## 📊 Resultados y Visualizaciones

### 🎯 Comparación Métodos Tradicionales vs ISE
![Dependency Comparison](outputs/figures/dependency_comparison.png)
*Puntos sobre la diagonal revelan dependencias ocultas*

### 🌍 Mapas de Calor Sectoriales
![Sectoral Heatmaps](outputs/figures/sectoral_heatmaps.png)
*Dependencias totales por sector estratégico entre bloques comerciales*

### 🔗 Intermediarios Críticos Globales
![Critical Intermediaries](outputs/figures/intermediary_centrality.png)
*Países clave que controlan múltiples cadenas de valor*

### 📈 Análisis CVG Automotriz
![Automotive CVG](outputs/figures/automotive_cvg_analysis.png)
*39 sectores upstream que alimentan la industria automotriz*

## 🎓 Casos de Uso y Aplicaciones

### 🏛️ Para Gobiernos y Organismos Internacionales
- **Evaluación de autonomía estratégica** real vs aparente
- **Simulación de escenarios geopolíticos** (crisis Taiwan, guerra comercial)
- **Priorización sectorial** para estrategias de diversificación
- **Identificación de vulnerabilidades sistémicas** antes de crisis

### 🏢 Para Empresas Multinacionales
- **Análisis de riesgos** en cadenas de suministro complejas
- **Identificación de proveedores críticos** indirectos
- **Evaluación de exposición geopolítica** por sector
- **Estrategias de diversificación** informadas por datos

### 🎯 Para Investigadores y Académicos
- **Metodología innovadora** para estudios de comercio internacional
- **Datos procesados** para investigación en fragmentación geoeconómica
- **Herramientas de análisis** reproducibles y escalables
- **Marcos conceptuales** para seguridad económica

## 📚 Publicaciones y Papers

### 📄 Papers Académicos
1. **"Critical Networks and Structural Power: An Application of the Economic Security Index"**
   - *Autores*: Hidalgo-Pérez, M.A., Díaz-Lanchas, J., Otero-Iglesias, M.
   - *Status*: En revisión
   - *Archivo*: `papers/ise_methodology.pdf`

2. **"Extensión del ISE mediante Cadenas de Valor Globales"**
   - *Autores*: Hidalgo-Pérez, M.A., Díaz-Lanchas, J.
   - *Status*: Documento de trabajo
   - *Archivo*: `papers/cvg_extension.pdf`

### 🎯 Relevancia Política Actual
- **Guerra comercial 2025**: Evaluación de vulnerabilidades por escalada arancelaria
- **Crisis Taiwan**: Análisis de riesgo sistémico en semiconductores
- **Autonomía estratégica europea**: Identificación de dependencias críticas UE
- **Fragmentación geoeconómica**: Mapeo de connector countries

## 🔧 Especificaciones Técnicas

### ⚡ Optimizaciones de Rendimiento
- **Aceleración GPU**: NVIDIA CUDA para cálculos matriciales
- **Paralelización**: ThreadPoolExecutor para múltiples cores
- **Matrices sparse**: Optimización para redes comerciales sparse
- **Memoización**: Cache de subresultados para eficiencia

### 🔢 Algoritmos Clave
```python
# Dependencia Total
DT_ij = DD_ij + DI_ij

# Dependencia Indirecta (iterativa)
DI_ij^(l) = Σ F(p) for all paths p of length l

# Fuerza de Ruta
F(p) = (x_i,k1 / S_j) × Π(x_kn,kn+1 / S_kn+1)

# Centralidad de Intermediarios
C_k = α·(φ_k/max φ_i) + (1-α)·(ψ_k/max ψ_i)
```

### 📊 Métricas de Validación
- **Convergencia**: ε = 0.01 (1%)
- **Relevancia**: θ = 0.05% comercio global
- **Longitud máxima**: L_max = 5 intermediarios
- **Cobertura**: 99.2% comercio global capturado

## 🤝 Contribución y Colaboración

### 👥 Equipo Principal
- **Dr. Manuel Hidalgo-Pérez** - Universidad Pablo de Olavide & Real Instituto Elcano
- **Dr. Jorge Díaz-Lanchas** - Universidad Autónoma de Madrid
- **Dr. Miguel Otero-Iglesias** - Real Instituto Elcano

### 🤲 Cómo Contribuir
1. **Fork** el repositorio
2. **Clone** tu fork localmente
3. **Crea una rama** para tu contribución (`git checkout -b feature/nueva-funcionalidad`)
4. **Commit** tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
5. **Push** a la rama (`git push origin feature/nueva-funcionalidad`)
6. **Crea un Pull Request**

### 🐛 Reportar Issues
- Usa el sistema de issues de GitHub
- Incluye detalles de reproducción
- Especifica versión de Python y sistema operativo
- Adjunta logs de error si están disponibles

## 📞 Contacto y Soporte

### 📧 Contacto Principal
- **Email**: mhidper@upo.es
- **Institución**: Real Instituto Elcano
- **Web**: [realinstitutoelcano.org](https://www.realinstitutoelcano.org)

### 💬 Comunidad
- **Issues**: Para reportar problemas técnicos
- **Discussions**: Para preguntas metodológicas
- **Twitter**: [@RealInstitutoElcano](https://twitter.com/rielcano)

## 📜 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- **Real Instituto Elcano** por el apoyo institucional y financiación
- **Universidad Pablo de Olavide** y **Universidad Autónoma de Madrid** por recursos académicos
- **ESADE EcPol** por colaboración en análisis de política económica
- **Comunidad científica** en comercio internacional y redes complejas

---

## 📈 Estadísticas del Proyecto

![GitHub last commit](https://img.shields.io/github/last-commit/mhidper/Seguridad-Economica)
![GitHub issues](https://img.shields.io/github/issues/mhidper/Seguridad-Economica)
![GitHub pull requests](https://img.shields.io/github/issues-pr/mhidper/Seguridad-Economica)

**Contribuye a revolucionar el análisis de seguridad económica en la era de fragmentación geoeconómica** 🌍⚡

---

*"En un mundo de creciente fragmentación geoeconómica, entender las dependencias ocultas no es una opción académica, es una necesidad estratégica"* - Real Instituto Elcano
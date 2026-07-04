import os
from pathlib import Path

base_dir = Path(r"c:\Users\Usuario\Documents\Github\Seguridad Economica")

print("Starting custom concept injection...")

# 1. Update README.md (Root)
readme_path = base_dir / "README.md"
if readme_path.exists():
    content = readme_path.read_text(encoding="utf-8")
    
    old_text = "El **Índice de Dependencia Económica Elcano (IDEE)** es una métrica avanzada diseñada por el **Real Instituto Elcano** para identificar y cuantificar la vulnerabilidad de las naciones ante interrupciones en las cadenas globales de suministro. Supera la medición tradicional de \"volumen de comercio\" al enfocarse en la **estructura de dependencia** y la **capacidad de sustitución**."
    
    new_text = "El **Índice de Dependencia Económica Elcano (IDEE)** es una métrica avanzada diseñada por el **Real Instituto Elcano** para evaluar la posición de fortaleza o vulnerabilidad de un país en el contexto del comercio internacional de una mercancía, bien o servicio específico a nivel internacional.\n\nEn un mercado global interconectado, las adquisiciones de un país consumidor final de un bien no implican que este dependa de todos los países, pero sí de un entramado de relaciones de intermediación comercial. Aunque un importador no adquiera un bien directamente de un determinado productor, está insertado en una red sectorial de reexportación. Por tanto, una disrupción en cualquier eslabón de este entramado comercial puede llegar a afectarle no solo de forma directa, sino también indirecta. El IDEE supera la miopía de las estadísticas bilaterales tradicionales, cuantificando cómo el riesgo se propaga a través de la red de suministro de cada sector."
    
    content = content.replace(old_text, new_text)
    readme_path.write_text(content, encoding="utf-8")
    print("Root README.md updated.")

# 2. Update notebooks/README.md
nb_readme_path = base_dir / "notebooks" / "README.md"
if nb_readme_path.exists():
    content = nb_readme_path.read_text(encoding="utf-8")
    
    old_text = "Este directorio es el núcleo de cálculo, investigación y manipulación de datos del proyecto **Índice de Dependencia Económica Elcano (IDEE)**."
    
    new_text = "Este directorio es el núcleo de cálculo, investigación y manipulación de datos del proyecto **Índice de Dependencia Económica Elcano (IDEE)**. El IDEE evalúa la posición de fortaleza o vulnerabilidad de un país en el contexto del comercio internacional de una mercancía, bien o servicio a nivel internacional. Las redes de comercio entre varios países, de un determinado producto, no implican que las adquisiciones de un país consumidor final de ese bien dependa de todos los países, pero sí de un entramado de relaciones comerciales de intermediación que puede llegar a afectarle no solo de forma directa, sino indirecta."
    
    content = content.replace(old_text, new_text)
    nb_readme_path.write_text(content, encoding="utf-8")
    print("notebooks/README.md updated.")

# 3. Update notebooks/analysis/README.md
anal_readme_path = base_dir / "notebooks" / "analysis" / "README.md"
if anal_readme_path.exists():
    content = anal_readme_path.read_text(encoding="utf-8")
    
    old_text = "Este subdirectorio contiene el corazón algorítmico y estadístico del **Índice de Dependencia Económica Elcano (IDEE)**."
    
    new_text = "Este subdirectorio contiene el corazón algorítmico y estadístico del **Índice de Dependencia Económica Elcano (IDEE)**. El IDEE evalúa la posición de fortaleza o vulnerabilidad de un país en el contexto del comercio internacional de una mercancía, bien o servicio a nivel internacional. Las redes de comercio entre varios países, de un determinado producto, no implican que las adquisiciones de un país consumidor final de ese bien dependa de todos los países, pero sí de un entramado de relaciones comerciales de intermediación que puede llegar a afectarle no solo de forma directa, sino indirecta."
    
    content = content.replace(old_text, new_text)
    anal_readme_path.write_text(content, encoding="utf-8")
    print("notebooks/analysis/README.md updated.")

# 4. LaTeX files
latex_es_paths = [
    base_dir / "dashboard_prototype" / "metodología" / "metodologia.tex",
    base_dir / "metodología" / "paper" / "metodologia.tex",
]

latex_en_paths = [
    base_dir / "dashboard_prototype" / "metodología" / "methodology.tex",
    base_dir / "metodología" / "paper" / "methodology.tex",
]

latex_es_old = r"""\subsection{Conceptualización}
La propuesta de este trabajo es un indicador integral que combina el análisis matricial, la teoría de redes y los algoritmos de propagación para identificar y cuantificar vulnerabilidades ocultas."""

latex_es_new = r"""\subsection{Conceptualización}
La propuesta de este trabajo es un indicador integral diseñado para evaluar la posición de fortaleza o vulnerabilidad de un país en el contexto del comercio internacional de una mercancía, bien o servicio específico a nivel internacional.

En un mercado global interconectado, las adquisiciones de un país consumidor final de un bien no implican que este dependa de todos los países, pero sí de un entramado de relaciones comerciales de intermediación. Aunque un importador no adquiera un producto directamente de un determinado productor, está insertado en una red sectorial de reexportación. Por tanto, una disrupción en cualquier eslabón de este entramado comercial puede llegar a afectarle no solo de forma directa, sino también indirecta. El IDEE supera la miopía de las métricas bilaterales clásicas, haciendo visible el riesgo de intermediación comercial que fluye a través de la red de suministro de cada sector."""

latex_en_old = r"""\subsection{Conceptualization}
The proposal of this work is a comprehensive indicator that combines matrix analysis, network theory, and propagation algorithms to identify and quantify hidden vulnerabilities."""

latex_en_new = r"""\subsection{Conceptualization}
The proposal of this work is a comprehensive indicator designed to evaluate the strong or weak position of a country in the context of international trade of a specific commodity, good, or service at the international level.

In an interconnected global market, the acquisitions of a final consuming country do not imply that it depends on all countries, but indeed on a network of trade intermediation relations. Even if an importer does not acquire a good directly from a specific producer, it is embedded in a sectoral re-export network; thus, a disruption in any link of this commercial framework can affect it not only directly, but also indirectly. The IDEE system overcomes the myopia of traditional bilateral metrics, making visible the risk of trade intermediation that flows through the supply network of each sector."""

# Update Spanish LaTeX
for path in latex_es_paths:
    if path.exists():
        content = path.read_text(encoding="utf-8")
        content = content.replace(latex_es_old, latex_es_new)
        # Also clean up the English subsubsection name that was left in the Spanish version:
        content = content.replace(r"\subsubsection{Definition of Direct and Indirect Dependency}",
                                  r"\subsubsection{Definición de Dependencia Directa e Indirecta}")
        path.write_text(content, encoding="utf-8")
        print(f"LaTeX ES: {path.name} updated with definition.")

# Update English LaTeX
for path in latex_en_paths:
    if path.exists():
        content = path.read_text(encoding="utf-8")
        content = content.replace(latex_en_old, latex_en_new)
        path.write_text(content, encoding="utf-8")
        print(f"LaTeX EN: {path.name} updated with definition.")

print("All file definitions updated.")

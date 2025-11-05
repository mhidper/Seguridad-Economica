"""
data_utils.py
Funciones de utilidad para el Dashboard de Seguridad Económica

Este módulo contiene todas las funciones de procesamiento de datos
separadas de la lógica de visualización, facilitando la migración
a otras plataformas (Dash, Flask, etc.)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# ============================================
# CONSTANTES
# ============================================

ELCANO_COLORS = {
    'primary': '#003366',
    'secondary': '#0066CC',
    'accent': '#CC0000',
    'success': '#28A745',
    'warning': '#FFC107',
    'light_gray': '#F8F9FA',
    'medium_gray': '#6C757D',
    'dark': '#212529',
}

DEPENDENCY_SCALE = ['#E8F4F8', '#B3D9E6', '#7BBFD4', '#3E9FBD', '#0066CC', '#003366']

# ============================================
# FUNCIONES DE CARGA
# ============================================

def load_dependencies_data(file_path: str = "processed/dependencies_full.parquet") -> pd.DataFrame:
    """
    Carga el archivo Parquet con los datos de dependencias
    
    Args:
        file_path: Ruta al archivo Parquet
        
    Returns:
        DataFrame con los datos de dependencias
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el formato del archivo es incorrecto
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {file_path}")
    
    try:
        df = pd.read_parquet(file_path)
        
        # Validar columnas requeridas
        required_columns = [
            'industry', 'dependent_country', 'supplier_country',
            'dependency_value', 'direct_dependency', 'indirect_dependency',
            'trade_value', 'longitud_optima', 'year'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Columnas faltantes en el dataset: {missing_columns}")
        
        return df
        
    except Exception as e:
        raise ValueError(f"Error al cargar o validar el archivo: {e}")

# ============================================
# FUNCIONES DE ESTADÍSTICAS
# ============================================

def get_summary_statistics(df: pd.DataFrame) -> Dict:
    """
    Calcula estadísticas resumidas del dataset completo
    
    Args:
        df: DataFrame con datos de dependencias
        
    Returns:
        Diccionario con estadísticas clave
    """
    return {
        'total_records': len(df),
        'years': sorted(df['year'].unique().tolist()),
        'countries_dependent': df['dependent_country'].nunique(),
        'countries_supplier': df['supplier_country'].nunique(),
        'industries': df['industry'].nunique(),
        'avg_dependency': df['dependency_value'].mean(),
        'median_dependency': df['dependency_value'].median(),
        'critical_dependencies': len(df[df['dependency_value'] > 0.8]),
        'max_dependency': df['dependency_value'].max(),
        'min_dependency': df['dependency_value'].min(),
        'avg_trade_value': df['trade_value'].mean(),
        'total_trade_value': df['trade_value'].sum(),
    }

def get_country_statistics(df: pd.DataFrame, country: str) -> Dict:
    """
    Calcula estadísticas específicas para un país
    
    Args:
        df: DataFrame con datos de dependencias
        country: Código del país a analizar
        
    Returns:
        Diccionario con estadísticas del país
    """
    as_dependent = df[df['dependent_country'] == country]
    as_supplier = df[df['supplier_country'] == country]
    
    return {
        'dependencies_count': len(as_dependent),
        'supplies_count': len(as_supplier),
        'avg_dependency_as_dependent': as_dependent['dependency_value'].mean() if len(as_dependent) > 0 else 0,
        'critical_dependencies': len(as_dependent[as_dependent['dependency_value'] > 0.8]),
        'main_suppliers': as_dependent.nlargest(5, 'dependency_value')['supplier_country'].tolist() if len(as_dependent) > 0 else [],
        'main_clients': as_supplier.nlargest(5, 'dependency_value')['dependent_country'].tolist() if len(as_supplier) > 0 else [],
        'industries_dependent': as_dependent['industry'].nunique(),
        'industries_supplier': as_supplier['industry'].nunique(),
    }

# ============================================
# FUNCIONES DE FILTRADO
# ============================================

def filter_data(
    df: pd.DataFrame,
    year: Optional[int] = None,
    country: Optional[str] = None,
    industry: Optional[str] = None,
    min_dependency: Optional[float] = None,
    max_dependency: Optional[float] = None,
    chain_length: Optional[int] = None
) -> pd.DataFrame:
    """
    Filtra el dataframe según múltiples criterios
    
    Args:
        df: DataFrame con datos de dependencias
        year: Año específico (None = todos)
        country: País (busca en dependent y supplier)
        industry: Industria específica
        min_dependency: Dependencia mínima
        max_dependency: Dependencia máxima
        chain_length: Longitud específica de cadena
        
    Returns:
        DataFrame filtrado
    """
    filtered = df.copy()
    
    if year is not None:
        filtered = filtered[filtered['year'] == year]
    
    if country is not None:
        filtered = filtered[
            (filtered['dependent_country'] == country) | 
            (filtered['supplier_country'] == country)
        ]
    
    if industry is not None:
        filtered = filtered[filtered['industry'] == industry]
    
    if min_dependency is not None:
        filtered = filtered[filtered['dependency_value'] >= min_dependency]
    
    if max_dependency is not None:
        filtered = filtered[filtered['dependency_value'] <= max_dependency]
    
    if chain_length is not None:
        filtered = filtered[filtered['longitud_optima'] == chain_length]
    
    return filtered

def get_critical_dependencies(
    df: pd.DataFrame,
    threshold: float = 0.8,
    top_n: Optional[int] = None
) -> pd.DataFrame:
    """
    Obtiene las dependencias críticas (por encima de un umbral)
    
    Args:
        df: DataFrame con datos de dependencias
        threshold: Umbral de dependencia crítica (default: 0.8)
        top_n: Número máximo de resultados (None = todos)
        
    Returns:
        DataFrame con dependencias críticas ordenadas
    """
    critical = df[df['dependency_value'] >= threshold].copy()
    critical = critical.sort_values('dependency_value', ascending=False)
    
    if top_n is not None:
        critical = critical.head(top_n)
    
    return critical

# ============================================
# FUNCIONES DE AGREGACIÓN
# ============================================

def aggregate_temporal(df: pd.DataFrame, metric: str = 'dependency_value') -> pd.DataFrame:
    """
    Agrega datos por año para análisis temporal
    
    Args:
        df: DataFrame con datos de dependencias
        metric: Métrica a agregar ('dependency_value', 'trade_value', etc.)
        
    Returns:
        DataFrame agregado por año
    """
    temporal = df.groupby('year').agg({
        'dependency_value': ['mean', 'median', 'std', 'count'],
        'direct_dependency': 'mean',
        'indirect_dependency': 'mean',
        'trade_value': ['sum', 'mean'],
        'longitud_optima': 'mean'
    }).reset_index()
    
    temporal.columns = ['_'.join(col).strip('_') for col in temporal.columns.values]
    
    return temporal

def aggregate_by_country(df: pd.DataFrame, as_role: str = 'dependent') -> pd.DataFrame:
    """
    Agrega datos por país
    
    Args:
        df: DataFrame con datos de dependencias
        as_role: 'dependent' o 'supplier' - rol del país a analizar
        
    Returns:
        DataFrame agregado por país
    """
    country_col = f'{
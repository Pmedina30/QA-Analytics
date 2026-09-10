"""
data_quality.py
===============
Módulo de análisis de calidad de datos para el QA Analytics Dashboard.

Propósito:
    Analizar el dataset de evaluaciones QA e identificar problemas de calidad
    antes de comenzar cualquier análisis. Un análisis confiable requiere datos
    confiables — este módulo garantiza que entendemos el estado real de los datos.

Autor: QA Analytics Project
Fecha: 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES — Rangos y categorías válidas
# ─────────────────────────────────────────────────────────────────────────────

VALID_SCORE_MIN = 0
VALID_SCORE_MAX = 100

VALID_CSAT_MIN = 1
VALID_CSAT_MAX = 5

VALID_CRITICAL_ERROR = {"Yes", "No"}
VALID_STATUS = {"Pass", "Fail"}


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES DE VALIDACIÓN INDIVIDUALES
# ─────────────────────────────────────────────────────────────────────────────

def count_records(df: pd.DataFrame) -> dict:
    """
    Retorna dimensiones básicas del dataset.
    
    Args:
        df: DataFrame con los datos crudos.
    
    Returns:
        Diccionario con total de filas y columnas.
    """
    return {
        "total_records": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns)
    }


def check_duplicates(df: pd.DataFrame) -> dict:
    """
    Detecta filas completamente duplicadas y Evaluation_IDs duplicados.
    
    Por qué importa: Los duplicados inflan los KPIs artificialmente y
    pueden sesgar promedios, tasas y tendencias.
    
    Args:
        df: DataFrame con los datos crudos.
    
    Returns:
        Diccionario con conteo de duplicados.
    """
    full_duplicates = df.duplicated().sum()
    id_duplicates = df.duplicated(subset=["Evaluation_ID"]).sum()

    return {
        "full_duplicate_rows": int(full_duplicates),
        "duplicate_evaluation_ids": int(id_duplicates)
    }


def check_missing_values(df: pd.DataFrame) -> dict:
    """
    Cuenta valores nulos por columna y calcula el porcentaje de completitud.
    
    Por qué importa: Los valores nulos pueden excluir registros de cálculos
    o generar resultados incorrectos si no se manejan explícitamente.
    
    Args:
        df: DataFrame con los datos crudos.
    
    Returns:
        Diccionario con nulos por columna y total.
    """
    nulls_per_col = df.isnull().sum()
    pct_per_col = (nulls_per_col / len(df) * 100).round(2)

    missing_detail = {}
    for col in df.columns:
        missing_detail[col] = {
            "missing_count": int(nulls_per_col[col]),
            "missing_pct": float(pct_per_col[col])
        }

    return {
        "total_missing": int(nulls_per_col.sum()),
        "by_column": missing_detail
    }


def check_evaluation_scores(df: pd.DataFrame) -> dict:
    """
    Valida que Evaluation_Score esté en el rango [0, 100].
    
    Rango válido: 0–100 puntos. Un score de 110 o -5 indica error
    de captura o lógica de evaluación incorrecta.
    
    Args:
        df: DataFrame con los datos crudos.
    
    Returns:
        Diccionario con conteo de scores inválidos.
    """
    invalid_mask = (
        df["Evaluation_Score"].isna() |
        (df["Evaluation_Score"] < VALID_SCORE_MIN) |
        (df["Evaluation_Score"] > VALID_SCORE_MAX)
    )
    invalid_count = int(invalid_mask.sum())

    return {
        "invalid_qa_scores": invalid_count,
        "score_min_found": float(df["Evaluation_Score"].min()),
        "score_max_found": float(df["Evaluation_Score"].max())
    }


def check_csat(df: pd.DataFrame) -> dict:
    """
    Valida que Customer_Satisfaction esté en el rango [1, 5].
    
    Rango válido: 1–5 (escala Likert estándar). Valores fuera de
    este rango sugieren error de sistema o captura incorrecta.
    
    Args:
        df: DataFrame con los datos crudos.
    
    Returns:
        Diccionario con conteo de CSAT inválidos.
    """
    invalid_mask = (
        df["Customer_Satisfaction"].isna() |
        (df["Customer_Satisfaction"] < VALID_CSAT_MIN) |
        (df["Customer_Satisfaction"] > VALID_CSAT_MAX)
    )
    invalid_count = int(invalid_mask.sum())

    return {
        "invalid_csat": invalid_count,
        "csat_min_found": float(df["Customer_Satisfaction"].min()) if df["Customer_Satisfaction"].notna().any() else None,
        "csat_max_found": float(df["Customer_Satisfaction"].max()) if df["Customer_Satisfaction"].notna().any() else None
    }


def check_resolution_time(df: pd.DataFrame) -> dict:
    """
    Valida que Resolution_Time_Min sea mayor que 0.
    
    Un tiempo de resolución de 0 o negativo es imposible operacionalmente
    y debe tratarse como dato inválido o error de sistema.
    
    Args:
        df: DataFrame con los datos crudos.
    
    Returns:
        Diccionario con conteo de tiempos inválidos.
    """
    invalid_mask = df["Resolution_Time_Min"] <= 0
    invalid_count = int(invalid_mask.sum())

    return {
        "invalid_resolution_time": invalid_count,
        "resolution_min_found": float(df["Resolution_Time_Min"].min()),
        "resolution_max_found": float(df["Resolution_Time_Min"].max())
    }


def check_errors_column(df: pd.DataFrame) -> dict:
    """
    Valida que la columna Errors sea >= 0.
    
    El número de errores no puede ser negativo; un valor negativo
    indica un problema de captura o codificación.
    
    Args:
        df: DataFrame con los datos crudos.
    
    Returns:
        Diccionario con conteo de valores de errores inválidos.
    """
    invalid_mask = df["Errors"] < 0
    invalid_count = int(invalid_mask.sum())

    return {
        "invalid_errors": invalid_count,
        "errors_min_found": int(df["Errors"].min()),
        "errors_max_found": int(df["Errors"].max())
    }


def check_categorical_columns(df: pd.DataFrame) -> dict:
    """
    Valida las columnas categóricas contra sus valores permitidos.
    
    Valores fuera de los conjuntos permitidos pueden causar errores
    de filtrado y cálculos incorrectos de tasas.
    
    Args:
        df: DataFrame con los datos crudos.
    
    Returns:
        Diccionario con conteo de categorías inválidas por columna.
    """
    # Critical_Error: solo "Yes" o "No"
    invalid_critical = int(
        (~df["Critical_Error"].isin(VALID_CRITICAL_ERROR)).sum()
    ) if "Critical_Error" in df.columns else 0

    # Status: solo "Pass" o "Fail"
    invalid_status = int(
        (~df["Status"].isin(VALID_STATUS)).sum()
    ) if "Status" in df.columns else 0

    # Valores únicos encontrados (para diagnóstico)
    found_critical = sorted(df["Critical_Error"].dropna().unique().tolist())
    found_status = sorted(df["Status"].dropna().unique().tolist())

    return {
        "invalid_critical_error": invalid_critical,
        "invalid_status": invalid_status,
        "unique_critical_error_values": found_critical,
        "unique_status_values": found_status
    }


def check_dates(df: pd.DataFrame, date_col: str = "Date") -> dict:
    """
    Intenta parsear la columna de fechas e identifica valores no parseables.
    
    Las fechas inválidas impiden el análisis de tendencias por período
    (semanal, mensual) y deben identificarse antes del análisis temporal.
    
    Args:
        df: DataFrame con los datos crudos.
        date_col: Nombre de la columna de fecha.
    
    Returns:
        Diccionario con información de validación de fechas.
    """
    try:
        parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
        invalid_dates = int(parsed_dates.isna().sum())
        date_min = str(parsed_dates.min().date()) if not parsed_dates.isna().all() else None
        date_max = str(parsed_dates.max().date()) if not parsed_dates.isna().all() else None
    except Exception as e:
        invalid_dates = len(df)
        date_min = None
        date_max = None

    return {
        "invalid_dates": invalid_dates,
        "date_min": date_min,
        "date_max": date_max
    }


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL — Reporte completo de calidad
# ─────────────────────────────────────────────────────────────────────────────

def calculate_quality_score(results: dict) -> float:
    """
    Calcula el Data Quality Score global del dataset.
    
    Metodología:
        El score mide el porcentaje de "celdas válidas" sobre el total
        de celdas evaluadas, penalizando: duplicados, valores nulos,
        valores fuera de rango y categorías inválidas.
    
        Fórmula:
            total_issues = duplicados + nulos + scores_inválidos +
                           csat_inválidos + tiempos_inválidos +
                           errores_inválidos + categorías_inválidas +
                           fechas_inválidas
    
            DQ Score = max(0, 1 - total_issues / total_records) * 100
    
        Interpretación:
            >= 98%  → Alta calidad (producción lista)
            95–97%  → Buena calidad (limpieza menor requerida)
            90–94%  → Calidad aceptable (limpieza moderada)
            < 90%   → Calidad baja (revisión requerida)
    
    Args:
        results: Diccionario con los resultados de todas las validaciones.
    
    Returns:
        Score de calidad entre 0 y 100.
    """
    total_records = results["dimensions"]["total_records"]
    if total_records == 0:
        return 0.0

    total_issues = (
        results["duplicates"]["full_duplicate_rows"] +
        results["missing"]["total_missing"] +
        results["scores"]["invalid_qa_scores"] +
        results["csat"]["invalid_csat"] +
        results["resolution"]["invalid_resolution_time"] +
        results["errors_col"]["invalid_errors"] +
        results["categories"]["invalid_critical_error"] +
        results["categories"]["invalid_status"] +
        results["dates"]["invalid_dates"]
    )

    score = max(0, (1 - total_issues / total_records)) * 100
    return round(score, 2)


def run_data_quality_report(df: pd.DataFrame) -> dict:
    """
    Ejecuta el análisis completo de calidad de datos.
    
    Esta es la función principal del módulo. Combina todas las validaciones
    individuales en un reporte estructurado que puede usarse para:
    - Decidir si los datos son confiables para análisis
    - Identificar qué transformaciones de limpieza son necesarias
    - Documentar el estado de calidad del dataset
    
    Args:
        df: DataFrame con los datos crudos del CSV de evaluaciones.
    
    Returns:
        Diccionario con el reporte completo de calidad de datos.
    """
    print("=" * 60)
    print("   DATA QUALITY ANALYSIS — QA Evaluations 2026")
    print("=" * 60)

    results = {
        "report_generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dimensions": count_records(df),
        "duplicates": check_duplicates(df),
        "missing": check_missing_values(df),
        "scores": check_evaluation_scores(df),
        "csat": check_csat(df),
        "resolution": check_resolution_time(df),
        "errors_col": check_errors_column(df),
        "categories": check_categorical_columns(df),
        "dates": check_dates(df)
    }

    # Calcular quality score global
    results["data_quality_score"] = calculate_quality_score(results)

    # ── Imprimir resumen en consola ──────────────────────────────────────────
    d = results
    print(f"\n📊 DIMENSIONS")
    print(f"   Total Records   : {d['dimensions']['total_records']:,}")
    print(f"   Total Columns   : {d['dimensions']['total_columns']}")

    print(f"\n🔁 DUPLICATES")
    print(f"   Full Duplicates       : {d['duplicates']['full_duplicate_rows']:,}")
    print(f"   Duplicate IDs         : {d['duplicates']['duplicate_evaluation_ids']:,}")

    print(f"\n❓ MISSING VALUES")
    print(f"   Total Missing         : {d['missing']['total_missing']:,}")
    for col, info in d['missing']['by_column'].items():
        if info['missing_count'] > 0:
            print(f"   {col:<30} {info['missing_count']:>6,} ({info['missing_pct']:.2f}%)")

    print(f"\n✅ VALIDATION CHECKS")
    print(f"   Invalid QA Scores     : {d['scores']['invalid_qa_scores']:,}")
    print(f"   Invalid CSAT          : {d['csat']['invalid_csat']:,}")
    print(f"   Invalid Resolution Time: {d['resolution']['invalid_resolution_time']:,}")
    print(f"   Invalid Errors Col    : {d['errors_col']['invalid_errors']:,}")
    print(f"   Invalid Critical_Error: {d['categories']['invalid_critical_error']:,}")
    print(f"   Invalid Status        : {d['categories']['invalid_status']:,}")
    print(f"   Invalid Dates         : {d['dates']['invalid_dates']:,}")

    print(f"\n📅 DATE RANGE")
    print(f"   From : {d['dates']['date_min']}")
    print(f"   To   : {d['dates']['date_max']}")

    dq_score = d['data_quality_score']
    label = (
        "🟢 ALTA CALIDAD" if dq_score >= 98 else
        "🟡 BUENA CALIDAD" if dq_score >= 95 else
        "🟠 CALIDAD ACEPTABLE" if dq_score >= 90 else
        "🔴 CALIDAD BAJA"
    )
    print(f"\n{'='*60}")
    print(f"   DATA QUALITY SCORE: {dq_score:.2f}%  {label}")
    print(f"{'='*60}\n")

    return results


def results_to_dataframe(results: dict) -> pd.DataFrame:
    """
    Convierte el reporte de calidad a un DataFrame para exportar a CSV/Excel.
    
    Args:
        results: Diccionario retornado por run_data_quality_report().
    
    Returns:
        DataFrame con las métricas de calidad en formato tabular.
    """
    rows = [
        {"Metric": "Report Generated At",      "Value": results["report_generated_at"],                                "Category": "Info"},
        {"Metric": "Total Records",            "Value": results["dimensions"]["total_records"],                         "Category": "Dimensions"},
        {"Metric": "Total Columns",            "Value": results["dimensions"]["total_columns"],                         "Category": "Dimensions"},
        {"Metric": "Full Duplicate Rows",      "Value": results["duplicates"]["full_duplicate_rows"],                   "Category": "Duplicates"},
        {"Metric": "Duplicate Evaluation IDs","Value": results["duplicates"]["duplicate_evaluation_ids"],               "Category": "Duplicates"},
        {"Metric": "Total Missing Values",     "Value": results["missing"]["total_missing"],                            "Category": "Missing Values"},
        {"Metric": "Invalid QA Scores",        "Value": results["scores"]["invalid_qa_scores"],                         "Category": "Validation"},
        {"Metric": "Invalid CSAT",             "Value": results["csat"]["invalid_csat"],                                "Category": "Validation"},
        {"Metric": "Invalid Resolution Time",  "Value": results["resolution"]["invalid_resolution_time"],               "Category": "Validation"},
        {"Metric": "Invalid Errors Column",    "Value": results["errors_col"]["invalid_errors"],                        "Category": "Validation"},
        {"Metric": "Invalid Critical Error",   "Value": results["categories"]["invalid_critical_error"],                "Category": "Validation"},
        {"Metric": "Invalid Status",           "Value": results["categories"]["invalid_status"],                        "Category": "Validation"},
        {"Metric": "Invalid Dates",            "Value": results["dates"]["invalid_dates"],                              "Category": "Validation"},
        {"Metric": "Date Range Start",         "Value": results["dates"]["date_min"],                                   "Category": "Date Range"},
        {"Metric": "Date Range End",           "Value": results["dates"]["date_max"],                                   "Category": "Date Range"},
        {"Metric": "DATA QUALITY SCORE (%)",   "Value": results["data_quality_score"],                                  "Category": "Overall"},
    ]

    # Agregar nulos por columna
    for col, info in results["missing"]["by_column"].items():
        rows.append({
            "Metric": f"Missing — {col}",
            "Value": info["missing_count"],
            "Category": "Missing by Column"
        })

    return pd.DataFrame(rows)

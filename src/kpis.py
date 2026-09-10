"""
kpis.py
=======
Módulo de cálculo de KPIs para el QA Analytics Dashboard.

Propósito:
    Calcular los indicadores clave de desempeño (KPIs) que miden la calidad
    operacional del contact center. Cada KPI tiene un target definido y
    un contexto de negocio que explica por qué importa.

Targets operacionales:
    QA Score       >= 85%
    Pass Rate      >= 85%
    Critical Error Rate < 2%
    CSAT           >= 4.2

Autor: QA Analytics Project
Fecha: 2026
"""

import pandas as pd
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# TARGETS OPERACIONALES
# ─────────────────────────────────────────────────────────────────────────────

TARGETS = {
    "qa_score":           {"value": 85.0, "operator": ">=", "label": "QA Score >= 85%"},
    "pass_rate":          {"value": 85.0, "operator": ">=", "label": "Pass Rate >= 85%"},
    "critical_error_rate":{"value": 2.0,  "operator": "<",  "label": "Critical Error Rate < 2%"},
    "csat":               {"value": 4.2,  "operator": ">=", "label": "CSAT >= 4.2"},
}


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES KPI INDIVIDUALES
# ─────────────────────────────────────────────────────────────────────────────

def total_evaluations(df: pd.DataFrame) -> int:
    """
    Cuenta el total de evaluaciones en el período.
    
    Contexto de negocio: El volumen de evaluaciones impacta la
    representatividad de los KPIs. Un promedio basado en 10 evaluaciones
    es menos confiable que uno basado en 500.
    
    Args:
        df: DataFrame limpio (solo registros válidos).
    
    Returns:
        Número entero de evaluaciones.
    """
    return len(df)


def average_qa_score(df: pd.DataFrame) -> float:
    """
    Calcula el promedio de Evaluation_Score.
    
    Contexto de negocio: El QA Score mide la adherencia del agente al
    protocolo de atención. El target >= 85 refleja el estándar mínimo
    aceptable para mantener la calidad del servicio.
    
    Args:
        df: DataFrame limpio.
    
    Returns:
        Promedio del QA Score redondeado a 2 decimales.
    """
    return round(df["Evaluation_Score"].mean(), 2)


def pass_rate(df: pd.DataFrame) -> float:
    """
    Calcula el porcentaje de evaluaciones con Status == "Pass".
    
    Contexto de negocio: La tasa de aprobación mide qué porcentaje de
    interacciones cumplen el estándar mínimo definido por la organización.
    Una caída en Pass Rate es una señal temprana de deterioro de calidad.
    
    Args:
        df: DataFrame limpio.
    
    Returns:
        Pass Rate como porcentaje (0–100).
    """
    if len(df) == 0:
        return 0.0
    rate = df["Pass_Flag"].sum() / len(df) * 100
    return round(rate, 2)


def fail_rate(df: pd.DataFrame) -> float:
    """
    Calcula el porcentaje de evaluaciones con Status == "Fail".
    
    Complemento del Pass Rate. Útil para reportes donde el foco está
    en cuantificar el problema (ej: "5% de las interacciones fallan").
    
    Args:
        df: DataFrame limpio.
    
    Returns:
        Fail Rate como porcentaje (0–100).
    """
    return round(100 - pass_rate(df), 2)


def critical_error_rate(df: pd.DataFrame) -> float:
    """
    Calcula el porcentaje de evaluaciones con Critical_Error == "Yes".
    
    Contexto de negocio: Un error crítico es aquel que puede causar daño
    directo al cliente, a la empresa o incumplimiento regulatorio. El
    target < 2% refleja cero tolerancia operacional a errores de alto impacto.
    
    Args:
        df: DataFrame limpio.
    
    Returns:
        Critical Error Rate como porcentaje (0–100).
    """
    if len(df) == 0:
        return 0.0
    rate = df["Critical_Error_Flag"].sum() / len(df) * 100
    return round(rate, 2)


def average_errors(df: pd.DataFrame) -> float:
    """
    Calcula el promedio de errores por evaluación.
    
    Contexto de negocio: Muestra la carga de errores promedio por interacción.
    Combinado con Critical Error Rate permite distinguir entre errores
    menores frecuentes vs. errores críticos esporádicos.
    
    Args:
        df: DataFrame limpio.
    
    Returns:
        Promedio de errores redondeado a 2 decimales.
    """
    return round(df["Errors"].mean(), 2)


def average_csat(df: pd.DataFrame) -> float:
    """
    Calcula el promedio de Customer_Satisfaction (escala 1–5).
    
    Contexto de negocio: CSAT mide la percepción del cliente sobre la calidad
    del servicio recibido. Es el indicador que más directamente captura el
    impacto de la calidad en la experiencia del cliente. Target >= 4.2/5.
    
    Args:
        df: DataFrame limpio.
    
    Returns:
        CSAT promedio redondeado a 2 decimales.
    """
    return round(df["Customer_Satisfaction"].mean(), 2)


def average_resolution_time(df: pd.DataFrame) -> float:
    """
    Calcula el tiempo de resolución promedio en minutos.
    
    Contexto de negocio: No se asume un target arbitrario. Se analiza la
    tendencia para identificar si el tiempo aumenta, disminuye o se mantiene
    estable. Aumentos sostenidos pueden indicar procesos complejos o
    falta de capacitación.
    
    Args:
        df: DataFrame limpio.
    
    Returns:
        Tiempo promedio en minutos redondeado a 2 decimales.
    """
    return round(df["Resolution_Time_Min"].mean(), 2)


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL — CALCULAR TODOS LOS KPIs
# ─────────────────────────────────────────────────────────────────────────────

def calculate_all_kpis(df: pd.DataFrame) -> dict:
    """
    Calcula todos los KPIs del dashboard y compara con targets.
    
    Args:
        df: DataFrame limpio (solo registros data_valid=True).
    
    Returns:
        Diccionario con todos los KPIs, targets y estado (on_target/off_target).
    """
    kpis = {
        "total_evaluations":    total_evaluations(df),
        "average_qa_score":     average_qa_score(df),
        "pass_rate":            pass_rate(df),
        "fail_rate":            fail_rate(df),
        "critical_error_rate":  critical_error_rate(df),
        "average_errors":       average_errors(df),
        "average_csat":         average_csat(df),
        "average_resolution_time": average_resolution_time(df),
    }

    # Evaluar estado contra targets
    kpis["qa_score_on_target"]    = kpis["average_qa_score"] >= TARGETS["qa_score"]["value"]
    kpis["pass_rate_on_target"]   = kpis["pass_rate"] >= TARGETS["pass_rate"]["value"]
    kpis["crit_err_on_target"]    = kpis["critical_error_rate"] < TARGETS["critical_error_rate"]["value"]
    kpis["csat_on_target"]        = kpis["average_csat"] >= TARGETS["csat"]["value"]

    return kpis


def print_kpi_summary(kpis: dict) -> None:
    """
    Imprime el resumen ejecutivo de KPIs con indicadores de desempeño.
    
    Args:
        kpis: Diccionario retornado por calculate_all_kpis().
    """
    def status_icon(on_target: bool) -> str:
        return "✅" if on_target else "❌"

    print("\n" + "=" * 60)
    print("   KPI EXECUTIVE SUMMARY")
    print("=" * 60)
    print(f"   Total Evaluations     : {kpis['total_evaluations']:,}")
    print(f"")
    print(f"   Avg QA Score          : {kpis['average_qa_score']:.2f}%  "
          f"{status_icon(kpis['qa_score_on_target'])}  (Target: >= 85%)")
    print(f"   Pass Rate             : {kpis['pass_rate']:.2f}%  "
          f"{status_icon(kpis['pass_rate_on_target'])}  (Target: >= 85%)")
    print(f"   Fail Rate             : {kpis['fail_rate']:.2f}%")
    print(f"   Critical Error Rate   : {kpis['critical_error_rate']:.2f}%  "
          f"{status_icon(kpis['crit_err_on_target'])}  (Target: < 2%)")
    print(f"   Avg Errors / Eval     : {kpis['average_errors']:.2f}")
    print(f"   Avg CSAT              : {kpis['average_csat']:.2f} / 5.0  "
          f"{status_icon(kpis['csat_on_target'])}  (Target: >= 4.2)")
    print(f"   Avg Resolution Time   : {kpis['average_resolution_time']:.2f} min")
    print("=" * 60 + "\n")


def kpis_to_dataframe(kpis: dict) -> pd.DataFrame:
    """
    Convierte el diccionario de KPIs a DataFrame para exportar.
    
    Args:
        kpis: Diccionario retornado por calculate_all_kpis().
    
    Returns:
        DataFrame con KPIs, targets y estado de cumplimiento.
    """
    rows = [
        {
            "KPI":          "Total Evaluations",
            "Value":        kpis["total_evaluations"],
            "Target":       "N/A",
            "Status":       "N/A",
            "Unit":         "count"
        },
        {
            "KPI":          "Average QA Score",
            "Value":        kpis["average_qa_score"],
            "Target":       ">= 85%",
            "Status":       "On Target" if kpis["qa_score_on_target"] else "Below Target",
            "Unit":         "%"
        },
        {
            "KPI":          "Pass Rate",
            "Value":        kpis["pass_rate"],
            "Target":       ">= 85%",
            "Status":       "On Target" if kpis["pass_rate_on_target"] else "Below Target",
            "Unit":         "%"
        },
        {
            "KPI":          "Fail Rate",
            "Value":        kpis["fail_rate"],
            "Target":       "< 15%",
            "Status":       "On Target" if kpis["pass_rate_on_target"] else "Above Target",
            "Unit":         "%"
        },
        {
            "KPI":          "Critical Error Rate",
            "Value":        kpis["critical_error_rate"],
            "Target":       "< 2%",
            "Status":       "On Target" if kpis["crit_err_on_target"] else "Above Target",
            "Unit":         "%"
        },
        {
            "KPI":          "Average Errors per Evaluation",
            "Value":        kpis["average_errors"],
            "Target":       "N/A",
            "Status":       "N/A",
            "Unit":         "count"
        },
        {
            "KPI":          "Average CSAT",
            "Value":        kpis["average_csat"],
            "Target":       ">= 4.2",
            "Status":       "On Target" if kpis["csat_on_target"] else "Below Target",
            "Unit":         "1–5 scale"
        },
        {
            "KPI":          "Average Resolution Time",
            "Value":        kpis["average_resolution_time"],
            "Target":       "Trend Analysis",
            "Status":       "Monitor",
            "Unit":         "minutes"
        },
    ]
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# DISTRIBUCIÓN DE QA CATEGORIES
# ─────────────────────────────────────────────────────────────────────────────

def qa_category_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la distribución de registros por categoría QA.
    
    Permite identificar qué proporción del workforce está en cada nivel
    de desempeño, sin limitarse a un promedio global.
    
    Args:
        df: DataFrame limpio.
    
    Returns:
        DataFrame con conteo y porcentaje por categoría QA.
    """
    category_order = ["Excellent", "Good", "Meets Target", "Below Target"]
    counts = df["QA_Category"].value_counts()

    result = pd.DataFrame({
        "QA_Category": category_order,
        "Count": [counts.get(cat, 0) for cat in category_order]
    })
    result["Percentage"] = (result["Count"] / len(df) * 100).round(2)
    return result

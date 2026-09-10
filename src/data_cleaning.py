"""
data_cleaning.py
================
Pipeline de limpieza y transformación de datos para el QA Analytics Dashboard.

Propósito:
    Convertir el dataset crudo en un dataset limpio, consistente y enriquecido
    con columnas derivadas que faciliten el análisis de KPIs y tendencias.

Principio fundamental:
    NUNCA sobrescribir el dataset original. El archivo limpio se guarda
    en output/qa_clean.csv manteniendo la trazabilidad y reproducibilidad.

Autor: QA Analytics Project
Fecha: 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────

VALID_SCORE_MIN = 0
VALID_SCORE_MAX = 100
VALID_CSAT_MIN = 1
VALID_CSAT_MAX = 5
VALID_CRITICAL_ERROR = {"Yes", "No"}
VALID_STATUS = {"Pass", "Fail"}

# Categorías QA según umbrales de desempeño operacional
QA_CATEGORIES = [
    (95, float("inf"), "Excellent"),
    (90, 95,           "Good"),
    (85, 90,           "Meets Target"),
    (0,  85,           "Below Target"),
]


# ─────────────────────────────────────────────────────────────────────────────
# PASO 1 — ELIMINAR DUPLICADOS
# ─────────────────────────────────────────────────────────────────────────────

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Elimina filas completamente duplicadas y conserva solo el primer
    Evaluation_ID en caso de IDs duplicados.
    
    Por qué: Los duplicados inflan artificialmente el volumen de evaluaciones,
    afectando conteos, tasas y promedios. Se prioriza el primero encontrado
    asumiendo que es el registro original.
    
    Args:
        df: DataFrame crudo.
    
    Returns:
        DataFrame sin duplicados.
    """
    initial_count = len(df)

    # Paso 1: eliminar filas 100% idénticas
    df = df.drop_duplicates()
    after_full_dedup = len(df)

    # Paso 2: eliminar IDs duplicados (conservar el primero)
    df = df.drop_duplicates(subset=["Evaluation_ID"], keep="first")
    final_count = len(df)

    removed_full = initial_count - after_full_dedup
    removed_id = after_full_dedup - final_count

    if removed_full > 0 or removed_id > 0:
        print(f"   ✓ Duplicados eliminados: {removed_full} filas completas, {removed_id} IDs duplicados")
    else:
        print("   ✓ Sin duplicados encontrados")

    return df.reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# PASO 2 — CONVERTIR FECHAS
# ─────────────────────────────────────────────────────────────────────────────

def convert_dates(df: pd.DataFrame, date_col: str = "Date") -> pd.DataFrame:
    """
    Convierte la columna de fechas a tipo datetime.
    
    Por qué: Sin datetime nativo no es posible realizar análisis por
    semana, mes, trimestre ni calcular tendencias temporales. Las filas
    con fechas no parseables se marcan como NaT para manejo explícito.
    
    Args:
        df: DataFrame de trabajo.
        date_col: Nombre de la columna de fecha.
    
    Returns:
        DataFrame con la columna de fecha como datetime.
    """
    df = df.copy()
    original_non_null = df[date_col].notna().sum()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    invalid_dates = df[date_col].isna().sum()

    print(f"   ✓ Fechas convertidas a datetime. Fechas inválidas: {invalid_dates:,}")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# PASO 3 — MANEJAR VALORES NULOS
# ─────────────────────────────────────────────────────────────────────────────

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Maneja los valores nulos de manera explícita y documentada.
    
    Estrategia por columna:
    - Supervisor: "Unknown" — conservar el registro; desconocer el supervisor
      no invalida la evaluación en sí misma.
    - Customer_Satisfaction: mediana del grupo (Agent + Process) para
      respetar la distribución sin inflar con promedios globales.
      Fallback: mediana global si el grupo tiene menos de 3 observaciones.
    
    Por qué mediana y no media para CSAT:
        CSAT es una escala ordinal Likert (1–5). La mediana es más robusta
        ante distribuciones asimétricas y valores extremos en escalas ordinales.
    
    Args:
        df: DataFrame de trabajo.
    
    Returns:
        DataFrame con nulos manejados.
    """
    df = df.copy()

    # Supervisor — rellenar con "Unknown"
    sup_nulls = df["Supervisor"].isna().sum()
    if sup_nulls > 0:
        df["Supervisor"] = df["Supervisor"].fillna("Unknown")
        print(f"   ✓ Supervisor: {sup_nulls:,} nulos → 'Unknown'")

    # Customer_Satisfaction — imputar con mediana por grupo (Agent + Process)
    csat_nulls = df["Customer_Satisfaction"].isna().sum()
    if csat_nulls > 0:
        global_median = df["Customer_Satisfaction"].median()

        def fill_csat(group):
            if group["Customer_Satisfaction"].notna().sum() >= 3:
                fill_val = group["Customer_Satisfaction"].median()
            else:
                fill_val = global_median
            return group["Customer_Satisfaction"].fillna(fill_val)

        df["Customer_Satisfaction"] = (
            df.groupby(["Agent", "Process"], group_keys=False)
              .apply(fill_csat)
        )

        remaining = df["Customer_Satisfaction"].isna().sum()
        if remaining > 0:
            df["Customer_Satisfaction"] = df["Customer_Satisfaction"].fillna(global_median)

        print(f"   ✓ Customer_Satisfaction: {csat_nulls:,} nulos → imputados con mediana grupal")

    return df


# ─────────────────────────────────────────────────────────────────────────────
# PASO 4 — VALIDAR RANGOS Y FILTRAR
# ─────────────────────────────────────────────────────────────────────────────

def validate_ranges(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifica y etiqueta registros con valores fuera de rango.
    
    Decisión de diseño: En lugar de eliminar registros inválidos, se agrega
    una columna 'data_valid' para trazabilidad. El pipeline de análisis
    puede filtrar por esta columna. Esto permite auditar cuántos registros
    fueron excluidos y por qué.
    
    Args:
        df: DataFrame de trabajo.
    
    Returns:
        DataFrame con columna 'data_valid' (True/False).
    """
    df = df.copy()

    valid_score = df["Evaluation_Score"].between(VALID_SCORE_MIN, VALID_SCORE_MAX)
    valid_csat = df["Customer_Satisfaction"].between(VALID_CSAT_MIN, VALID_CSAT_MAX)
    valid_resolution = df["Resolution_Time_Min"] > 0
    valid_errors = df["Errors"] >= 0
    valid_critical = df["Critical_Error"].isin(VALID_CRITICAL_ERROR)
    valid_status = df["Status"].isin(VALID_STATUS)
    valid_date = df["Date"].notna()

    df["data_valid"] = (
        valid_score & valid_csat & valid_resolution &
        valid_errors & valid_critical & valid_status & valid_date
    )

    invalid_count = (~df["data_valid"]).sum()
    print(f"   ✓ Registros inválidos marcados: {invalid_count:,} (columna 'data_valid' = False)")

    return df


# ─────────────────────────────────────────────────────────────────────────────
# PASO 5 — NORMALIZAR CATEGORÍAS
# ─────────────────────────────────────────────────────────────────────────────

def normalize_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza columnas categóricas: strip de espacios, capitalización consistente.
    
    Por qué: Diferencias de capitalización o espacios extra crean categorías
    falsas ("pass" ≠ "Pass" ≠ "PASS") que fragmentan análisis y filtros.
    
    Args:
        df: DataFrame de trabajo.
    
    Returns:
        DataFrame con categorías normalizadas.
    """
    df = df.copy()
    string_cols = ["Agent", "Team", "Supervisor", "Process", "Critical_Error", "Status"]

    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    # Critical_Error y Status deben ser Title Case (Yes/No, Pass/Fail)
    # title() ya los maneja correctamente
    print("   ✓ Categorías normalizadas (strip + title case)")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# PASO 6 — CREAR COLUMNAS DERIVADAS
# ─────────────────────────────────────────────────────────────────────────────

def assign_qa_category(score: float) -> str:
    """
    Asigna la categoría de desempeño basada en el QA Score.
    
    Umbrales definidos por el estándar operacional QA:
        >= 95   → Excellent     (supera el target significativamente)
        90–94.99 → Good         (supera el target)
        85–89.99 → Meets Target (cumple el target mínimo)
        < 85    → Below Target  (no cumple el target)
    
    Args:
        score: Evaluation_Score numérico.
    
    Returns:
        String con la categoría asignada.
    """
    if pd.isna(score):
        return "Unknown"
    for low, high, label in QA_CATEGORIES:
        if low <= score < high:
            return label
    return "Excellent" if score >= 95 else "Below Target"


def create_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea columnas derivadas para facilitar el análisis temporal y de segmentación.
    
    Columnas creadas:
    - Week          : Número de semana ISO del año
    - Month         : Número de mes (1–12)
    - Month_Name    : Nombre del mes (January, February, …)
    - Year          : Año de la evaluación
    - Day_of_Week   : Nombre del día (Monday, Tuesday, …)
    - QA_Category   : Categoría de desempeño (Excellent/Good/Meets Target/Below Target)
    - Critical_Error_Flag : 1 si Critical_Error == "Yes", 0 si no
    - Pass_Flag     : 1 si Status == "Pass", 0 si no
    
    Por qué estas columnas:
        Week y Month permiten análisis de tendencias temporales sin
        necesidad de operaciones de date truncation en cada consulta.
        QA_Category habilita segmentación cualitativa del desempeño.
        Los flags (0/1) permiten calcular tasas con simple promedio o suma.
    
    Args:
        df: DataFrame con fechas ya convertidas a datetime.
    
    Returns:
        DataFrame enriquecido con columnas derivadas.
    """
    df = df.copy()

    # Columnas temporales — solo si la fecha es válida
    df["Week"] = df["Date"].dt.isocalendar().week.astype("Int64")
    df["Month"] = df["Date"].dt.month.astype("Int64")
    df["Month_Name"] = df["Date"].dt.strftime("%B")
    df["Year"] = df["Date"].dt.year.astype("Int64")
    df["Day_of_Week"] = df["Date"].dt.strftime("%A")

    # Categoría QA basada en Evaluation_Score
    df["QA_Category"] = df["Evaluation_Score"].apply(assign_qa_category)

    # Flags numéricos (0/1) para cálculo de tasas
    df["Critical_Error_Flag"] = (df["Critical_Error"] == "Yes").astype(int)
    df["Pass_Flag"] = (df["Status"] == "Pass").astype(int)

    print("   ✓ Columnas derivadas creadas: Week, Month, Month_Name, Year,")
    print("     Day_of_Week, QA_Category, Critical_Error_Flag, Pass_Flag")

    return df


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE COMPLETO
# ─────────────────────────────────────────────────────────────────────────────

def run_cleaning_pipeline(df_raw: pd.DataFrame, output_path: str | Path = None) -> pd.DataFrame:
    """
    Ejecuta el pipeline completo de limpieza en secuencia.
    
    Pipeline:
        1. Eliminar duplicados
        2. Convertir fechas
        3. Manejar valores nulos
        4. Validar rangos
        5. Normalizar categorías
        6. Crear columnas derivadas
        7. (Opcional) Guardar CSV limpio
    
    Args:
        df_raw: DataFrame con el dataset crudo.
        output_path: Ruta donde guardar el CSV limpio. Si es None, no guarda.
    
    Returns:
        DataFrame limpio y enriquecido.
    """
    print("\n" + "=" * 60)
    print("   DATA CLEANING PIPELINE")
    print("=" * 60)
    print(f"\n   Dataset crudo: {len(df_raw):,} registros\n")

    # No modificar el original — trabajar con una copia
    df = df_raw.copy()

    print("📌 Paso 1: Eliminar duplicados")
    df = remove_duplicates(df)

    print("\n📌 Paso 2: Convertir fechas")
    df = convert_dates(df)

    print("\n📌 Paso 3: Manejar valores nulos")
    df = handle_missing_values(df)

    print("\n📌 Paso 4: Validar rangos")
    df = validate_ranges(df)

    print("\n📌 Paso 5: Normalizar categorías")
    df = normalize_categories(df)

    print("\n📌 Paso 6: Crear columnas derivadas")
    df = create_derived_columns(df)

    # ── Resumen final ────────────────────────────────────────────────────────
    valid_count = df["data_valid"].sum()
    invalid_count = (~df["data_valid"]).sum()

    print(f"\n{'─'*60}")
    print(f"   Registros limpios (data_valid=True)  : {valid_count:,}")
    print(f"   Registros marcados inválidos         : {invalid_count:,}")
    print(f"   Total registros procesados           : {len(df):,}")

    # ── Guardar si se especificó ruta ────────────────────────────────────────
    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"\n   💾 Dataset limpio guardado en: {output_path}")

    print("=" * 60 + "\n")

    return df


def get_clean_dataset(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Retorna solo los registros válidos del dataset limpio.
    
    Uso recomendado para análisis de KPIs y visualizaciones. Excluye
    registros con data_valid=False para evitar sesgar los resultados.
    
    Args:
        df_clean: DataFrame completo retornado por run_cleaning_pipeline().
    
    Returns:
        DataFrame filtrado con solo registros válidos.
    """
    return df_clean[df_clean["data_valid"] == True].copy()

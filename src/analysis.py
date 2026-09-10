"""
analysis.py
===========
Módulo de análisis de negocio para el QA Analytics Dashboard.

Propósito:
    Realizar análisis multidimensionales del desempeño: por equipo,
    proceso, agente y tendencia temporal. Responde preguntas de negocio
    específicas que los KPIs globales no pueden responder por sí solos.

Autor: QA Analytics Project
Fecha: 2026
"""

import pandas as pd
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────

# Mínimo de evaluaciones para incluir un agente en rankings.
# Razón: Con menos de 30 evaluaciones, el promedio es poco representativo
# estadísticamente y puede inflar o deflactar el desempeño real de un agente.
MIN_EVALUATIONS_FOR_RANKING = 30

QA_TARGET = 85.0


# ─────────────────────────────────────────────────────────────────────────────
# TEAM PERFORMANCE
# ─────────────────────────────────────────────────────────────────────────────

def team_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el desempeño de cada equipo.
    
    Métricas por equipo:
    - Evaluations: Volumen total de evaluaciones
    - Avg_QA_Score: Promedio del score de calidad
    - Pass_Rate: % de evaluaciones aprobadas
    - Critical_Error_Rate: % de errores críticos
    - Avg_CSAT: Promedio de satisfacción del cliente
    - Avg_Resolution_Time: Tiempo promedio de resolución (min)
    
    Ordenado por Avg_QA_Score descendente (mejor a peor).
    
    Por qué ordenar por QA Score: Es el KPI central del área de calidad.
    Otros KPIs como Pass Rate y CSAT complementan el análisis pero el
    QA Score es el indicador más controlado por el equipo de calidad.
    
    Args:
        df: DataFrame limpio (solo registros válidos).
    
    Returns:
        DataFrame con métricas por equipo, ordenado por QA Score desc.
    """
    team_agg = df.groupby("Team").agg(
        Evaluations          = ("Evaluation_ID", "count"),
        Avg_QA_Score         = ("Evaluation_Score", "mean"),
        Pass_Rate            = ("Pass_Flag", "mean"),
        Critical_Error_Rate  = ("Critical_Error_Flag", "mean"),
        Avg_CSAT             = ("Customer_Satisfaction", "mean"),
        Avg_Resolution_Time  = ("Resolution_Time_Min", "mean"),
    ).reset_index()

    # Convertir rates a porcentaje
    team_agg["Pass_Rate"] = (team_agg["Pass_Rate"] * 100).round(2)
    team_agg["Critical_Error_Rate"] = (team_agg["Critical_Error_Rate"] * 100).round(2)
    team_agg["Avg_QA_Score"] = team_agg["Avg_QA_Score"].round(2)
    team_agg["Avg_CSAT"] = team_agg["Avg_CSAT"].round(2)
    team_agg["Avg_Resolution_Time"] = team_agg["Avg_Resolution_Time"].round(2)

    # Agregar indicadores de target
    team_agg["QA_On_Target"] = team_agg["Avg_QA_Score"] >= QA_TARGET
    team_agg["Pass_On_Target"] = team_agg["Pass_Rate"] >= 85
    team_agg["CritErr_On_Target"] = team_agg["Critical_Error_Rate"] < 2
    team_agg["CSAT_On_Target"] = team_agg["Avg_CSAT"] >= 4.2

    return team_agg.sort_values("Avg_QA_Score", ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# PROCESS PERFORMANCE
# ─────────────────────────────────────────────────────────────────────────────

def process_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el desempeño de cada proceso.
    
    Métricas adicionales:
    - Total_Errors: Suma total de errores en el proceso
    - Total_Critical_Errors: Conteo de errores críticos absolutos
    - Avg_Errors: Promedio de errores por evaluación
    
    Los procesos con mayor tasa de errores críticos son los que
    representan mayor riesgo operacional y deben priorizarse para
    capacitación o revisión de protocolo.
    
    Args:
        df: DataFrame limpio.
    
    Returns:
        DataFrame con métricas por proceso, ordenado por Critical_Error_Rate desc.
    """
    proc_agg = df.groupby("Process").agg(
        Evaluations          = ("Evaluation_ID", "count"),
        Avg_QA_Score         = ("Evaluation_Score", "mean"),
        Total_Errors         = ("Errors", "sum"),
        Avg_Errors           = ("Errors", "mean"),
        Total_Critical_Errors= ("Critical_Error_Flag", "sum"),
        Critical_Error_Rate  = ("Critical_Error_Flag", "mean"),
        Avg_CSAT             = ("Customer_Satisfaction", "mean"),
        Avg_Resolution_Time  = ("Resolution_Time_Min", "mean"),
    ).reset_index()

    # Formato
    proc_agg["Avg_QA_Score"] = proc_agg["Avg_QA_Score"].round(2)
    proc_agg["Avg_Errors"] = proc_agg["Avg_Errors"].round(2)
    proc_agg["Critical_Error_Rate"] = (proc_agg["Critical_Error_Rate"] * 100).round(2)
    proc_agg["Avg_CSAT"] = proc_agg["Avg_CSAT"].round(2)
    proc_agg["Avg_Resolution_Time"] = proc_agg["Avg_Resolution_Time"].round(2)

    return proc_agg.sort_values("Critical_Error_Rate", ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# AGENT PERFORMANCE
# ─────────────────────────────────────────────────────────────────────────────

def agent_performance(df: pd.DataFrame,
                      min_evaluations: int = MIN_EVALUATIONS_FOR_RANKING) -> pd.DataFrame:
    """
    Calcula el desempeño por agente.
    
    Consideración estadística importante:
        Solo se incluyen en los rankings a agentes con al menos
        min_evaluations evaluaciones. Con menos evaluaciones, el promedio
        puede ser altamente variable y no refleja el desempeño real.
    
        Ejemplo: un agente con 5 evaluaciones y score 95 aparecería como
        top performer, pero con 5 datos no podemos concluir eso con
        confianza estadística razonable.
    
        El umbral de 30 es un mínimo práctico ampliamente usado en
        analytics operacional. No es un umbral estadístico estricto
        sino una heurística conservadora para evitar conclusiones
        prematuras sobre individuos.
    
    Args:
        df: DataFrame limpio.
        min_evaluations: Mínimo de evaluaciones requeridas para ranking.
    
    Returns:
        DataFrame con métricas por agente (todos), con columna 'Eligible_for_Ranking'.
    """
    agent_agg = df.groupby(["Agent", "Team", "Supervisor"]).agg(
        Evaluations          = ("Evaluation_ID", "count"),
        Avg_QA_Score         = ("Evaluation_Score", "mean"),
        Pass_Rate            = ("Pass_Flag", "mean"),
        Avg_CSAT             = ("Customer_Satisfaction", "mean"),
        Total_Errors         = ("Errors", "sum"),
        Avg_Errors           = ("Errors", "mean"),
        Total_Critical_Errors= ("Critical_Error_Flag", "sum"),
        Critical_Error_Rate  = ("Critical_Error_Flag", "mean"),
        Avg_Resolution_Time  = ("Resolution_Time_Min", "mean"),
    ).reset_index()

    # Formato
    agent_agg["Avg_QA_Score"] = agent_agg["Avg_QA_Score"].round(2)
    agent_agg["Pass_Rate"] = (agent_agg["Pass_Rate"] * 100).round(2)
    agent_agg["Avg_CSAT"] = agent_agg["Avg_CSAT"].round(2)
    agent_agg["Avg_Errors"] = agent_agg["Avg_Errors"].round(2)
    agent_agg["Critical_Error_Rate"] = (agent_agg["Critical_Error_Rate"] * 100).round(2)
    agent_agg["Avg_Resolution_Time"] = agent_agg["Avg_Resolution_Time"].round(2)

    # Eligibilidad para ranking
    agent_agg["Eligible_for_Ranking"] = agent_agg["Evaluations"] >= min_evaluations
    agent_agg["QA_Below_Target"] = agent_agg["Avg_QA_Score"] < QA_TARGET

    return agent_agg.sort_values("Avg_QA_Score", ascending=False).reset_index(drop=True)


def top_agents(agent_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Retorna los N mejores agentes elegibles para ranking.
    
    Args:
        agent_df: DataFrame retornado por agent_performance().
        n: Número de agentes a retornar.
    
    Returns:
        DataFrame con los N mejores agentes.
    """
    eligible = agent_df[agent_df["Eligible_for_Ranking"] == True].copy()
    return eligible.nlargest(n, "Avg_QA_Score").reset_index(drop=True)


def bottom_agents(agent_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Retorna los N peores agentes elegibles para ranking.
    
    Args:
        agent_df: DataFrame retornado por agent_performance().
        n: Número de agentes a retornar.
    
    Returns:
        DataFrame con los N peores agentes (menor QA Score).
    """
    eligible = agent_df[agent_df["Eligible_for_Ranking"] == True].copy()
    return eligible.nsmallest(n, "Avg_QA_Score").reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# TREND ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def daily_trend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el desempeño diario de KPIs.
    
    Útil para identificar días específicos con problemas de calidad
    o eventos que impactaron el desempeño (ej: lanzamiento de producto,
    cambio de proceso, ausentismo alto).
    
    Args:
        df: DataFrame limpio con columna Date como datetime.
    
    Returns:
        DataFrame con métricas diarias.
    """
    daily = df.groupby(df["Date"].dt.date).agg(
        Evaluations         = ("Evaluation_ID", "count"),
        Avg_QA_Score        = ("Evaluation_Score", "mean"),
        Pass_Rate           = ("Pass_Flag", "mean"),
        Critical_Error_Rate = ("Critical_Error_Flag", "mean"),
        Avg_CSAT            = ("Customer_Satisfaction", "mean"),
        Avg_Resolution_Time = ("Resolution_Time_Min", "mean"),
    ).reset_index()

    daily.columns = ["Date"] + list(daily.columns[1:])
    daily["Date"] = pd.to_datetime(daily["Date"])
    daily["Pass_Rate"] = (daily["Pass_Rate"] * 100).round(2)
    daily["Critical_Error_Rate"] = (daily["Critical_Error_Rate"] * 100).round(2)
    daily["Avg_QA_Score"] = daily["Avg_QA_Score"].round(2)
    daily["Avg_CSAT"] = daily["Avg_CSAT"].round(2)
    daily["Avg_Resolution_Time"] = daily["Avg_Resolution_Time"].round(2)

    return daily.sort_values("Date").reset_index(drop=True)


def weekly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el desempeño semanal de KPIs.
    
    La agregación semanal reduce el ruido del análisis diario y permite
    identificar patrones más estables. Es el nivel de análisis más útil
    para reportes de supervisión recurrentes.
    
    Args:
        df: DataFrame limpio.
    
    Returns:
        DataFrame con métricas semanales.
    """
    weekly = df.groupby(["Year", "Week"]).agg(
        Evaluations         = ("Evaluation_ID", "count"),
        Avg_QA_Score        = ("Evaluation_Score", "mean"),
        Pass_Rate           = ("Pass_Flag", "mean"),
        Critical_Error_Rate = ("Critical_Error_Flag", "mean"),
        Avg_CSAT            = ("Customer_Satisfaction", "mean"),
        Avg_Resolution_Time = ("Resolution_Time_Min", "mean"),
    ).reset_index()

    weekly["Pass_Rate"] = (weekly["Pass_Rate"] * 100).round(2)
    weekly["Critical_Error_Rate"] = (weekly["Critical_Error_Rate"] * 100).round(2)
    weekly["Avg_QA_Score"] = weekly["Avg_QA_Score"].round(2)
    weekly["Avg_CSAT"] = weekly["Avg_CSAT"].round(2)
    weekly["Avg_Resolution_Time"] = weekly["Avg_Resolution_Time"].round(2)
    weekly["Week_Label"] = weekly["Year"].astype(str) + "-W" + weekly["Week"].astype(str).str.zfill(2)

    return weekly.sort_values(["Year", "Week"]).reset_index(drop=True)


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el desempeño mensual de KPIs.
    
    El análisis mensual es el estándar para reportes ejecutivos y
    benchmarking de desempeño. Permite ver la evolución del trimestre
    y comparar meses del mismo año.
    
    Args:
        df: DataFrame limpio.
    
    Returns:
        DataFrame con métricas mensuales.
    """
    monthly = df.groupby(["Year", "Month", "Month_Name"]).agg(
        Evaluations         = ("Evaluation_ID", "count"),
        Avg_QA_Score        = ("Evaluation_Score", "mean"),
        Pass_Rate           = ("Pass_Flag", "mean"),
        Critical_Error_Rate = ("Critical_Error_Flag", "mean"),
        Avg_CSAT            = ("Customer_Satisfaction", "mean"),
        Avg_Resolution_Time = ("Resolution_Time_Min", "mean"),
    ).reset_index()

    monthly["Pass_Rate"] = (monthly["Pass_Rate"] * 100).round(2)
    monthly["Critical_Error_Rate"] = (monthly["Critical_Error_Rate"] * 100).round(2)
    monthly["Avg_QA_Score"] = monthly["Avg_QA_Score"].round(2)
    monthly["Avg_CSAT"] = monthly["Avg_CSAT"].round(2)
    monthly["Avg_Resolution_Time"] = monthly["Avg_Resolution_Time"].round(2)

    return monthly.sort_values(["Year", "Month"]).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# CORRELATION ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def correlation_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analiza las correlaciones entre variables numéricas clave.
    
    ADVERTENCIA ESTADÍSTICA IMPORTANTE:
        Correlación no implica causalidad. Una correlación alta entre
        QA Score y CSAT no significa que mejorar el QA Score causará
        automáticamente mayor CSAT. Pueden existir variables confusoras
        (tipo de proceso, complejidad del caso, etc.).
    
    Interpretación de Pearson r:
        |r| >= 0.7 → Correlación fuerte
        |r| 0.4–0.69 → Correlación moderada
        |r| 0.2–0.39 → Correlación débil
        |r| < 0.2 → Sin correlación práctica relevante
    
    Args:
        df: DataFrame limpio con columnas numéricas.
    
    Returns:
        DataFrame con correlaciones entre pares de variables clave.
    """
    numeric_cols = [
        "Evaluation_Score", "Customer_Satisfaction",
        "Resolution_Time_Min", "Errors", "Critical_Error_Flag"
    ]

    corr_matrix = df[numeric_cols].corr(method="pearson")

    # Pares específicos de interés de negocio
    pairs = [
        ("Evaluation_Score", "Customer_Satisfaction",  "QA Score vs CSAT"),
        ("Evaluation_Score", "Resolution_Time_Min",    "QA Score vs Resolution Time"),
        ("Errors",           "Customer_Satisfaction",  "Errors vs CSAT"),
        ("Critical_Error_Flag","Evaluation_Score",     "Critical Errors vs QA Score"),
    ]

    rows = []
    for col1, col2, label in pairs:
        r = corr_matrix.loc[col1, col2]
        strength = (
            "Strong"   if abs(r) >= 0.7 else
            "Moderate" if abs(r) >= 0.4 else
            "Weak"     if abs(r) >= 0.2 else
            "Negligible"
        )
        direction = "Positive" if r > 0 else "Negative" if r < 0 else "None"
        rows.append({
            "Relationship":   label,
            "Pearson_r":      round(r, 4),
            "Strength":       strength,
            "Direction":      direction,
            "Interpretation": f"{strength} {direction.lower()} correlation (r = {r:.4f})"
        })

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# EXECUTIVE INSIGHTS
# ─────────────────────────────────────────────────────────────────────────────

def generate_executive_insights(
    df: pd.DataFrame,
    kpis: dict,
    team_df: pd.DataFrame,
    process_df: pd.DataFrame,
    agent_df: pd.DataFrame,
    monthly_df: pd.DataFrame,
    corr_df: pd.DataFrame
) -> str:
    """
    Genera un resumen ejecutivo automático basado en los datos analizados.
    
    Separado en:
    - FACTS: Hechos observados directamente de los datos (sin interpretación)
    - INSIGHTS: Interpretaciones de negocio apoyadas por los datos
    - RECOMMENDATIONS: Sugerencias accionables basadas en evidencia
    
    PRINCIPIO: No se inventan explicaciones causales que los datos no permitan
    demostrar. Las recomendaciones son hipótesis para investigar, no
    conclusiones definitivas.
    
    Args:
        df: DataFrame limpio.
        kpis: Diccionario de KPIs.
        team_df: DataFrame de team_performance().
        process_df: DataFrame de process_performance().
        agent_df: DataFrame de agent_performance().
        monthly_df: DataFrame de monthly_trend().
        corr_df: DataFrame de correlation_analysis().
    
    Returns:
        String con el reporte ejecutivo formateado.
    """
    # ── Datos para el reporte ────────────────────────────────────────────────
    best_team = team_df.iloc[0]["Team"] if len(team_df) > 0 else "N/A"
    best_team_score = team_df.iloc[0]["Avg_QA_Score"] if len(team_df) > 0 else 0
    worst_team = team_df.iloc[-1]["Team"] if len(team_df) > 0 else "N/A"
    worst_team_score = team_df.iloc[-1]["Avg_QA_Score"] if len(team_df) > 0 else 0

    # Proceso con más errores críticos
    worst_process = process_df.iloc[0]["Process"] if len(process_df) > 0 else "N/A"
    worst_process_crit = process_df.iloc[0]["Critical_Error_Rate"] if len(process_df) > 0 else 0

    # Agentes debajo del target (elegibles para ranking)
    eligible = agent_df[agent_df["Eligible_for_Ranking"] == True]
    agents_below = eligible[eligible["QA_Below_Target"] == True]
    n_below = len(agents_below)
    n_eligible = len(eligible)

    # Tendencia — comparar primer mes vs último mes
    if len(monthly_df) >= 2:
        first_month_score = monthly_df.iloc[0]["Avg_QA_Score"]
        last_month_score = monthly_df.iloc[-1]["Avg_QA_Score"]
        trend_direction = "mejorando" if last_month_score > first_month_score else "deteriorando"
        trend_diff = abs(last_month_score - first_month_score)
    else:
        trend_direction = "sin datos suficientes"
        first_month_score = last_month_score = trend_diff = 0

    # Correlación QA vs CSAT
    qa_csat_corr = corr_df[corr_df["Relationship"] == "QA Score vs CSAT"]
    if len(qa_csat_corr) > 0:
        r_val = qa_csat_corr.iloc[0]["Pearson_r"]
        corr_strength = qa_csat_corr.iloc[0]["Strength"]
        corr_direction = qa_csat_corr.iloc[0]["Direction"]
    else:
        r_val = corr_strength = corr_direction = "N/A"

    # Riesgo principal
    risks = []
    if not kpis["crit_err_on_target"]:
        risks.append(f"Critical Error Rate ({kpis['critical_error_rate']:.2f}%) supera el target de 2%")
    if not kpis["qa_score_on_target"]:
        risks.append(f"QA Score ({kpis['average_qa_score']:.2f}%) está por debajo del target de 85%")
    if not kpis["pass_rate_on_target"]:
        risks.append(f"Pass Rate ({kpis['pass_rate']:.2f}%) está por debajo del target de 85%")
    if not kpis["csat_on_target"]:
        risks.append(f"CSAT ({kpis['average_csat']:.2f}) está por debajo del target de 4.2")
    main_risk = risks[0] if risks else "Todos los KPIs principales están dentro del target"

    # ── Generar reporte ──────────────────────────────────────────────────────
    report = f"""
{'='*70}
  EXECUTIVE INSIGHTS REPORT — QA Evaluations 2026
  Generated: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}
{'='*70}

━━━ FACTS (Hechos observados directamente de los datos) ━━━━━━━━━━━━━━━━━━

  F1. El dataset contiene {kpis['total_evaluations']:,} evaluaciones válidas para el análisis.

  F2. El QA Score promedio general es {kpis['average_qa_score']:.2f}%
      {"✅ CUMPLE" if kpis['qa_score_on_target'] else "❌ NO CUMPLE"} el target de >= 85%.

  F3. La tasa de aprobación (Pass Rate) es {kpis['pass_rate']:.2f}%
      {"✅ CUMPLE" if kpis['pass_rate_on_target'] else "❌ NO CUMPLE"} el target de >= 85%.

  F4. La tasa de errores críticos es {kpis['critical_error_rate']:.2f}%
      {"✅ CUMPLE" if kpis['crit_err_on_target'] else "❌ NO CUMPLE"} el target de < 2%.

  F5. El CSAT promedio es {kpis['average_csat']:.2f} / 5.0
      {"✅ CUMPLE" if kpis['csat_on_target'] else "❌ NO CUMPLE"} el target de >= 4.2.

  F6. El mejor equipo por QA Score es {best_team} ({best_team_score:.2f}%).
      El equipo con menor desempeño es {worst_team} ({worst_team_score:.2f}%).

  F7. El proceso con mayor tasa de errores críticos es {worst_process}
      ({worst_process_crit:.2f}%).

  F8. {n_below} de {n_eligible} agentes elegibles para ranking están por debajo del target de QA.
      (Se excluyen agentes con menos de {eligible["Evaluations"].min() if len(eligible) > 0 else "N/A"} evaluaciones)

  F9. Tendencia: El QA Score está {trend_direction}.
      Primer período: {first_month_score:.2f}% → Último período: {last_month_score:.2f}%
      Diferencia: {trend_diff:.2f} puntos porcentuales.

  F10. Correlación QA Score vs CSAT: Pearson r = {r_val if isinstance(r_val, str) else f"{r_val:.4f}"}
       ({corr_strength} {corr_direction if isinstance(corr_direction, str) else corr_direction.lower()} correlation)

━━━ INSIGHTS (Interpretaciones de negocio apoyadas en los datos) ━━━━━━━━━

  I1. La diferencia entre el mejor y peor equipo
      ({best_team_score:.2f}% vs {worst_team_score:.2f}%) sugiere que el desempeño varía
      significativamente entre equipos. Esto puede indicar diferencias en
      supervisión, capacitación o complejidad de los procesos asignados.
      → Requiere investigación para determinar la causa raíz.

  I2. El proceso {worst_process} tiene la mayor concentración de errores
      críticos. Esto convierte a este proceso en el principal riesgo
      operacional. Puede indicar: protocolo complejo, capacitación
      insuficiente, o ambigüedad en las guías de evaluación.
      → Hipótesis a investigar, no conclusión definitiva.

  I3. La correlación {corr_strength if isinstance(corr_strength, str) else ""} entre QA Score y CSAT 
      {"sugiere que hay alguna relación entre la calidad evaluada y la satisfacción del cliente, aunque no es lo suficientemente fuerte para establecer una relación directa y lineal." if isinstance(r_val, float) and abs(r_val) < 0.7 else "sugiere una relación notable entre calidad evaluada y satisfacción del cliente."}
      ⚠️  IMPORTANTE: Correlación ≠ Causalidad. Existen factores no
      capturados en este dataset que también afectan la satisfacción.

  I4. {n_below} agentes por debajo del target representan una oportunidad
      de mejora a través de coaching individualizado. Los patrones en sus
      evaluaciones pueden revelar brechas de habilidad o conocimiento
      específicas.

━━━ RECOMMENDATIONS (Sugerencias accionables basadas en evidencia) ━━━━━━

  R1. PRIORIDAD ALTA: Investigar el proceso {worst_process}.
      Revisar las guías de evaluación y realizar sesiones de calibración
      para asegurar consistencia en las evaluaciones de este proceso.

  R2. Implementar un plan de coaching para los {n_below} agentes bajo target,
      priorizando aquellos con mayor volumen de evaluaciones y mayor
      desviación del target.

  R3. Analizar las prácticas del equipo {best_team} para identificar
      factores replicables en equipos con menor desempeño.

  R4. Establecer revisiones semanales de la tendencia de QA Score para
      detectar deterioros antes de que se conviertan en problemas crónicos.

  R5. Investigar si existe relación entre el tipo de proceso asignado a
      cada agente y su desempeño, ya que la complejidad del proceso puede
      ser un factor confusor en las comparaciones individuales.

  ⚠️  PRINCIPAL RIESGO DE CALIDAD:
      {main_risk}

{'='*70}
"""
    return report

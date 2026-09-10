"""
run_analysis.py
===============
Script principal del QA Analytics Pipeline.

Uso:
    python run_analysis.py

Descripción:
    Ejecuta el pipeline completo de análisis de calidad en el siguiente orden:

    1. Cargar datos crudos
    2. Análisis de calidad de datos (Data Quality Report)
    3. Limpieza y transformación (Data Cleaning Pipeline)
    4. Cálculo de KPIs
    5. Análisis de negocio (Team / Process / Agent / Trends / Correlations)
    6. Generación de visualizaciones
    7. Exportación de resultados (CSV + Excel)
    8. Reporte ejecutivo de insights

Autor: QA Analytics Project
Fecha: 2026
"""

import sys
import os
import time
from pathlib import Path

# Fix Windows Unicode encoding (PowerShell/cmd default is cp1252)
import io
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd

# ─── Asegurar que src/ está en el path ──────────────────────────────────────
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from data_quality  import run_data_quality_report, results_to_dataframe
from data_cleaning import run_cleaning_pipeline, get_clean_dataset
from kpis          import (calculate_all_kpis, print_kpi_summary,
                           kpis_to_dataframe, qa_category_distribution)
from analysis      import (team_performance, process_performance,
                           agent_performance, top_agents, bottom_agents,
                           daily_trend, weekly_trend, monthly_trend,
                           correlation_analysis, generate_executive_insights)
from visualizations import generate_all_visualizations


# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────

DATA_PATH   = ROOT / "Data"  / "qa_evaluations_2026.csv"
OUTPUT_DIR  = ROOT / "Output"
VIZ_DIR     = ROOT / "visualizations"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
VIZ_DIR.mkdir(parents=True, exist_ok=True)

CLEAN_CSV_PATH    = OUTPUT_DIR / "qa_clean.csv"
DQ_REPORT_PATH    = OUTPUT_DIR / "data_quality_report.csv"
SUMMARY_XLSX_PATH = OUTPUT_DIR / "qa_summary.xlsx"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def section(title: str) -> None:
    """Imprime un separador de sección con formato."""
    print(f"\n{'━'*60}")
    print(f"  STEP: {title}")
    print(f"{'━'*60}")


def elapsed(start: float) -> str:
    """Retorna el tiempo transcurrido en formato legible."""
    secs = time.time() - start
    return f"{secs:.1f}s"


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    pipeline_start = time.time()

    print("\n" + "█" * 60)
    print("  QA ANALYTICS PIPELINE — 2026")
    print("  Iniciando pipeline completo...")
    print("█" * 60)

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 1: CARGAR DATOS
    # ──────────────────────────────────────────────────────────────────────────
    section("1/8 — Load Raw Data")
    t = time.time()

    if not DATA_PATH.exists():
        print(f"\n  ❌ ERROR: No se encontró el archivo: {DATA_PATH}")
        print("  Asegúrate de que 'qa_evaluations_2026.csv' está en la carpeta Data/")
        sys.exit(1)

    df_raw = pd.read_csv(DATA_PATH)
    print(f"  ✅ Datos cargados: {len(df_raw):,} registros × {len(df_raw.columns)} columnas  [{elapsed(t)}]")

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 2: DATA QUALITY REPORT
    # ──────────────────────────────────────────────────────────────────────────
    section("2/8 — Data Quality Analysis")
    t = time.time()

    dq_results = run_data_quality_report(df_raw)
    dq_df = results_to_dataframe(dq_results)
    dq_df.to_csv(DQ_REPORT_PATH, index=False)
    print(f"  ✅ Reporte de calidad exportado → {DQ_REPORT_PATH.name}  [{elapsed(t)}]")

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 3: DATA CLEANING
    # ──────────────────────────────────────────────────────────────────────────
    section("3/8 — Data Cleaning Pipeline")
    t = time.time()

    df_clean_full = run_cleaning_pipeline(df_raw, output_path=CLEAN_CSV_PATH)
    df = get_clean_dataset(df_clean_full)
    print(f"  ✅ Dataset limpio: {len(df):,} registros válidos  [{elapsed(t)}]")

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 4: KPI CALCULATION
    # ──────────────────────────────────────────────────────────────────────────
    section("4/8 — KPI Calculation")
    t = time.time()

    kpis = calculate_all_kpis(df)
    print_kpi_summary(kpis)
    kpi_df = kpis_to_dataframe(kpis)
    qa_cat_df = qa_category_distribution(df)
    print(f"  ✅ KPIs calculados  [{elapsed(t)}]")

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 5: BUSINESS ANALYSIS
    # ──────────────────────────────────────────────────────────────────────────
    section("5/8 — Business Analysis")
    t = time.time()

    team_df    = team_performance(df)
    process_df = process_performance(df)
    agent_df   = agent_performance(df)
    top_df     = top_agents(agent_df, n=10)
    bottom_df  = bottom_agents(agent_df, n=10)

    daily_df   = daily_trend(df)
    weekly_df  = weekly_trend(df)
    monthly_df = monthly_trend(df)

    corr_df    = correlation_analysis(df)

    print(f"  Teams analizados   : {len(team_df)}")
    print(f"  Procesos analizados: {len(process_df)}")
    print(f"  Agentes analizados : {len(agent_df)}")
    print(f"  Meses de datos     : {len(monthly_df)}")

    print("\n  Correlaciones:")
    for _, row in corr_df.iterrows():
        print(f"    {row['Relationship']:<35} r = {row['Pearson_r']:>7.4f}  [{row['Strength']}]")

    print(f"\n  ✅ Análisis de negocio completado  [{elapsed(t)}]")

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 6: VISUALIZATIONS
    # ──────────────────────────────────────────────────────────────────────────
    section("6/8 — Generate Visualizations")
    t = time.time()

    viz_paths = generate_all_visualizations(
        df=df,
        monthly_df=monthly_df,
        team_df=team_df,
        process_df=process_df,
        top_agents_df=top_df,
        bottom_agents_df=bottom_df,
        output_dir=VIZ_DIR
    )
    print(f"  ✅ {len(viz_paths)} visualizaciones generadas  [{elapsed(t)}]")

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 7: EXCEL OUTPUT
    # ──────────────────────────────────────────────────────────────────────────
    section("7/8 — Export Excel Summary")
    t = time.time()

    with pd.ExcelWriter(SUMMARY_XLSX_PATH, engine="openpyxl") as writer:
        dq_df.to_excel(writer, sheet_name="Data Quality", index=False)
        kpi_df.to_excel(writer, sheet_name="KPIs", index=False)
        team_df.to_excel(writer, sheet_name="Team Analysis", index=False)
        process_df.to_excel(writer, sheet_name="Process Analysis", index=False)
        agent_df.to_excel(writer, sheet_name="Agent Analysis", index=False)
        monthly_df.to_excel(writer, sheet_name="Monthly Trend", index=False)
        corr_df.to_excel(writer, sheet_name="Correlations", index=False)
        qa_cat_df.to_excel(writer, sheet_name="QA Categories", index=False)

    print(f"  ✅ Excel exportado → {SUMMARY_XLSX_PATH.name}  [{elapsed(t)}]")

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 8: EXECUTIVE INSIGHTS
    # ──────────────────────────────────────────────────────────────────────────
    section("8/8 — Executive Insights Report")
    t = time.time()

    insights = generate_executive_insights(
        df=df,
        kpis=kpis,
        team_df=team_df,
        process_df=process_df,
        agent_df=agent_df,
        monthly_df=monthly_df,
        corr_df=corr_df
    )
    print(insights)

    # Guardar insights como archivo de texto
    insights_path = OUTPUT_DIR / "executive_insights.txt"
    with open(insights_path, "w", encoding="utf-8") as f:
        f.write(insights)
    print(f"  ✅ Insights guardados → {insights_path.name}  [{elapsed(t)}]")

    # ──────────────────────────────────────────────────────────────────────────
    # RESUMEN FINAL
    # ──────────────────────────────────────────────────────────────────────────
    total_time = elapsed(pipeline_start)
    print("\n" + "█" * 60)
    print("  ✅ PIPELINE COMPLETADO EXITOSAMENTE")
    print(f"  Tiempo total: {total_time}")
    print("\n  Archivos generados:")
    print(f"    📄 {CLEAN_CSV_PATH.relative_to(ROOT)}")
    print(f"    📄 {DQ_REPORT_PATH.relative_to(ROOT)}")
    print(f"    📊 {SUMMARY_XLSX_PATH.relative_to(ROOT)}")
    print(f"    📄 {insights_path.relative_to(ROOT)}")
    for name, path in viz_paths.items():
        print(f"    🖼️  {Path(path).relative_to(ROOT)}")
    print("█" * 60 + "\n")


if __name__ == "__main__":
    main()

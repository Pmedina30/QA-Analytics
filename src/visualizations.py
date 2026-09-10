"""
visualizations.py
=================
Módulo de visualizaciones profesionales para el QA Analytics Dashboard.

Propósito:
    Crear gráficos claros y accionables usando Matplotlib. Cada gráfico
    está diseñado para comunicar una insight específica de negocio, no
    solo mostrar datos.

Convención de colores:
    Verde  (#2ecc71) → desempeño positivo / on target
    Amarillo (#f39c12) → atención / cerca del límite
    Rojo   (#e74c3c) → debajo del target / riesgo
    Azul   (#3498db) → referencia / neutral
    Gris   (#95a5a6) → target line / referencia

Autor: QA Analytics Project
Fecha: 2026
"""

import matplotlib
matplotlib.use("Agg")   # backend sin GUI — necesario para guardar sin pantalla

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import numpy as np
from pathlib import Path

# ─── Paleta y estilo global ──────────────────────────────────────────────────
COLOR_GREEN   = "#2ecc71"
COLOR_YELLOW  = "#f39c12"
COLOR_RED     = "#e74c3c"
COLOR_BLUE    = "#3498db"
COLOR_DARK    = "#2c3e50"
COLOR_GRAY    = "#95a5a6"
COLOR_BG      = "#f8f9fa"

plt.rcParams.update({
    "figure.facecolor": COLOR_BG,
    "axes.facecolor":   COLOR_BG,
    "axes.edgecolor":   "#dee2e6",
    "axes.labelcolor":  COLOR_DARK,
    "axes.titlesize":   14,
    "axes.titleweight": "bold",
    "axes.titlepad":    14,
    "axes.labelsize":   11,
    "xtick.labelsize":  10,
    "ytick.labelsize":  10,
    "text.color":       COLOR_DARK,
    "grid.color":       "#dee2e6",
    "grid.linestyle":   "--",
    "grid.alpha":       0.7,
    "legend.fontsize":  10,
    "legend.framealpha": 0.9,
    "font.family":      "DejaVu Sans",
})

QA_TARGET     = 85.0
CSAT_TARGET   = 4.2
CRIT_TARGET   = 2.0


def _save(fig: plt.Figure, path: Path, dpi: int = 150) -> None:
    """Guarda figura y cierra para liberar memoria."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor=COLOR_BG)
    plt.close(fig)
    print(f"   💾 Guardado: {path.name}")


def _bar_color_by_target(values: pd.Series, target: float, op: str = ">=") -> list:
    """Retorna lista de colores según cumplimiento de target."""
    colors = []
    for v in values:
        if op == ">=":
            colors.append(COLOR_GREEN if v >= target else COLOR_RED)
        elif op == "<":
            colors.append(COLOR_GREEN if v < target else COLOR_RED)
    return colors


# ─────────────────────────────────────────────────────────────────────────────
# 1. QA SCORE TREND (Línea mensual)
# ─────────────────────────────────────────────────────────────────────────────

def plot_qa_trend(monthly_df: pd.DataFrame, output_dir: Path) -> Path:
    """
    Gráfico de tendencia del QA Score mensual.

    Qué muestra: Evolución del QA Score promedio mes a mes.
    Por qué importa: Permite detectar deterioros sostenidos o mejoras
    que los promedios globales ocultan.
    """
    fig, ax = plt.subplots(figsize=(12, 5))

    labels = monthly_df["Month_Name"].astype(str)
    scores = monthly_df["Avg_QA_Score"]

    ax.plot(labels, scores, color=COLOR_BLUE, linewidth=2.5,
            marker="o", markersize=7, zorder=3, label="Avg QA Score")
    ax.fill_between(range(len(labels)), scores, alpha=0.12, color=COLOR_BLUE)

    # Target line
    ax.axhline(QA_TARGET, color=COLOR_RED, linestyle="--",
               linewidth=1.5, label=f"Target ({QA_TARGET}%)", zorder=2)

    # Anotar último valor
    ax.annotate(f"{scores.iloc[-1]:.1f}%",
                xy=(len(labels) - 1, scores.iloc[-1]),
                xytext=(0, 12), textcoords="offset points",
                ha="center", fontsize=10, fontweight="bold", color=COLOR_DARK)

    ax.set_title("QA Score Trend — Monthly Average")
    ax.set_xlabel("Month")
    ax.set_ylabel("QA Score (%)")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylim(max(0, scores.min() - 5), min(100, scores.max() + 5))
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter("%.1f"))
    ax.legend(loc="lower right")
    ax.grid(True, axis="y")

    path = output_dir / "qa_trend.png"
    _save(fig, path)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 2. QA SCORE BY TEAM (Barras horizontales)
# ─────────────────────────────────────────────────────────────────────────────

def plot_qa_by_team(team_df: pd.DataFrame, output_dir: Path) -> Path:
    """
    Gráfico de QA Score promedio por equipo.

    Qué muestra: Comparación de desempeño entre equipos.
    Por qué importa: Identifica equipos que superan o no alcanzan el target,
    permitiendo focalizar supervisión y coaching donde más se necesita.
    """
    df = team_df.sort_values("Avg_QA_Score", ascending=True)
    colors = _bar_color_by_target(df["Avg_QA_Score"], QA_TARGET, ">=")

    fig, ax = plt.subplots(figsize=(10, max(4, len(df) * 0.7)))

    bars = ax.barh(df["Team"], df["Avg_QA_Score"], color=colors,
                   height=0.6, zorder=3)
    ax.axvline(QA_TARGET, color=COLOR_RED, linestyle="--",
               linewidth=1.5, label=f"Target ({QA_TARGET}%)")

    for bar, val in zip(bars, df["Avg_QA_Score"]):
        ax.text(val + 0.2, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=10, fontweight="bold")

    ax.set_title("Average QA Score by Team")
    ax.set_xlabel("Avg QA Score (%)")
    ax.set_xlim(0, max(df["Avg_QA_Score"].max() + 5, 100))
    ax.legend()
    ax.grid(True, axis="x")

    path = output_dir / "qa_by_team.png"
    _save(fig, path)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 3. CRITICAL ERRORS BY PROCESS (Barras verticales)
# ─────────────────────────────────────────────────────────────────────────────

def plot_errors_by_process(process_df: pd.DataFrame, output_dir: Path) -> Path:
    """
    Gráfico de tasa de errores críticos por proceso.

    Qué muestra: Qué procesos concentran más errores críticos.
    Por qué importa: Los errores críticos son el principal riesgo operacional.
    Identificar el proceso más problemático guía la priorización de acciones.
    """
    df = process_df.sort_values("Critical_Error_Rate", ascending=False)
    colors = _bar_color_by_target(df["Critical_Error_Rate"], CRIT_TARGET, "<")

    fig, ax = plt.subplots(figsize=(12, 5))

    bars = ax.bar(df["Process"], df["Critical_Error_Rate"],
                  color=colors, zorder=3)
    ax.axhline(CRIT_TARGET, color=COLOR_RED, linestyle="--",
               linewidth=1.5, label=f"Target (< {CRIT_TARGET}%)")

    for bar, val in zip(bars, df["Critical_Error_Rate"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{val:.2f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_title("Critical Error Rate by Process")
    ax.set_xlabel("Process")
    ax.set_ylabel("Critical Error Rate (%)")
    ax.set_xticklabels(df["Process"], rotation=30, ha="right")
    ax.legend()
    ax.grid(True, axis="y")

    path = output_dir / "errors_by_process.png"
    _save(fig, path)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 4 & 5. AGENT PERFORMANCE — TOP 10 & BOTTOM 10
# ─────────────────────────────────────────────────────────────────────────────

def plot_agent_performance(top_df: pd.DataFrame, bottom_df: pd.DataFrame,
                           output_dir: Path) -> Path:
    """
    Gráfico de Top 10 y Bottom 10 agentes por QA Score.

    Qué muestra: Los mejores y peores agentes elegibles para ranking.
    Por qué importa: Permite reconocer el alto desempeño y focalizar
    coaching en los agentes que más lo necesitan.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("Agent Performance — Top 10 & Bottom 10\n"
                 f"(Min. {30} evaluaciones para ranking)",
                 fontsize=14, fontweight="bold", color=COLOR_DARK)

    # ── Top 10 ───────────────────────────────────────────────────────────────
    top = top_df.sort_values("Avg_QA_Score", ascending=True)
    bars1 = ax1.barh(top["Agent"], top["Avg_QA_Score"],
                     color=COLOR_GREEN, height=0.6, zorder=3)
    ax1.axvline(QA_TARGET, color=COLOR_RED, linestyle="--",
                linewidth=1.5, label=f"Target ({QA_TARGET}%)")
    for bar, val in zip(bars1, top["Avg_QA_Score"]):
        ax1.text(val + 0.1, bar.get_y() + bar.get_height() / 2,
                 f"{val:.1f}%", va="center", fontsize=9, fontweight="bold")
    ax1.set_title("🏆 Top 10 Agents", fontsize=12)
    ax1.set_xlabel("Avg QA Score (%)")
    ax1.set_xlim(max(0, top["Avg_QA_Score"].min() - 3), 102)
    ax1.legend(loc="lower right")
    ax1.grid(True, axis="x")

    # ── Bottom 10 ────────────────────────────────────────────────────────────
    bot = bottom_df.sort_values("Avg_QA_Score", ascending=False)
    bars2 = ax2.barh(bot["Agent"], bot["Avg_QA_Score"],
                     color=COLOR_RED, height=0.6, zorder=3)
    ax2.axvline(QA_TARGET, color=COLOR_RED, linestyle="--",
                linewidth=1.5, label=f"Target ({QA_TARGET}%)")
    for bar, val in zip(bars2, bot["Avg_QA_Score"]):
        ax2.text(val + 0.1, bar.get_y() + bar.get_height() / 2,
                 f"{val:.1f}%", va="center", fontsize=9, fontweight="bold")
    ax2.set_title("⚠️ Bottom 10 Agents", fontsize=12)
    ax2.set_xlabel("Avg QA Score (%)")
    ax2.set_xlim(max(0, bot["Avg_QA_Score"].min() - 3), 100)
    ax2.legend(loc="lower right")
    ax2.grid(True, axis="x")

    plt.tight_layout()
    path = output_dir / "agent_performance.png"
    _save(fig, path)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 6. CSAT TREND (Línea mensual)
# ─────────────────────────────────────────────────────────────────────────────

def plot_csat_trend(monthly_df: pd.DataFrame, output_dir: Path) -> Path:
    """
    Gráfico de tendencia del CSAT mensual.

    Qué muestra: Evolución de la satisfacción del cliente mes a mes.
    Por qué importa: CSAT es el indicador más cercano al impacto en el cliente.
    Un CSAT en descenso puede anticipar pérdida de clientes.
    """
    fig, ax = plt.subplots(figsize=(12, 5))

    labels = monthly_df["Month_Name"].astype(str)
    csat = monthly_df["Avg_CSAT"]

    ax.plot(labels, csat, color=COLOR_YELLOW, linewidth=2.5,
            marker="s", markersize=7, zorder=3, label="Avg CSAT")
    ax.fill_between(range(len(labels)), csat, alpha=0.12, color=COLOR_YELLOW)
    ax.axhline(CSAT_TARGET, color=COLOR_RED, linestyle="--",
               linewidth=1.5, label=f"Target ({CSAT_TARGET})")

    ax.annotate(f"{csat.iloc[-1]:.2f}",
                xy=(len(labels) - 1, csat.iloc[-1]),
                xytext=(0, 12), textcoords="offset points",
                ha="center", fontsize=10, fontweight="bold", color=COLOR_DARK)

    ax.set_title("Customer Satisfaction (CSAT) Trend — Monthly Average")
    ax.set_xlabel("Month")
    ax.set_ylabel("CSAT (1–5 scale)")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylim(max(1, csat.min() - 0.3), 5.2)
    ax.legend(loc="lower right")
    ax.grid(True, axis="y")

    path = output_dir / "csat_trend.png"
    _save(fig, path)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 7. QA SCORE vs CSAT (Scatter)
# ─────────────────────────────────────────────────────────────────────────────

def plot_qa_vs_csat(df: pd.DataFrame, output_dir: Path,
                    sample_n: int = 2000) -> Path:
    """
    Scatter plot de QA Score vs Customer Satisfaction.

    Qué muestra: Si existe relación visual entre el score de calidad y la
    satisfacción del cliente a nivel de evaluación individual.
    Por qué importa: Apoya o cuestiona el supuesto de que mayor calidad
    evaluada se traduce en mayor satisfacción del cliente.

    Nota estadística: Se usa una muestra para rendimiento visual.
    La línea de tendencia (regresión lineal) es solo indicativa.
    """
    sample = df.sample(min(sample_n, len(df)), random_state=42)

    fig, ax = plt.subplots(figsize=(10, 6))

    scatter = ax.scatter(
        sample["Evaluation_Score"],
        sample["Customer_Satisfaction"],
        alpha=0.35, s=15, color=COLOR_BLUE, zorder=3
    )

    # Línea de tendencia (regresión lineal)
    z = np.polyfit(sample["Evaluation_Score"], sample["Customer_Satisfaction"], 1)
    p = np.poly1d(z)
    x_line = np.linspace(sample["Evaluation_Score"].min(),
                         sample["Evaluation_Score"].max(), 200)
    ax.plot(x_line, p(x_line), color=COLOR_RED, linewidth=2,
            linestyle="-", label="Trend (Linear Regression)")

    # Correlación
    r = sample["Evaluation_Score"].corr(sample["Customer_Satisfaction"])
    ax.text(0.05, 0.93, f"Pearson r = {r:.4f}",
            transform=ax.transAxes, fontsize=11,
            color=COLOR_DARK, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    ax.text(0.05, 0.86, "⚠️ Correlación ≠ Causalidad",
            transform=ax.transAxes, fontsize=9, color=COLOR_YELLOW)

    ax.set_title("QA Score vs Customer Satisfaction (CSAT)")
    ax.set_xlabel("Evaluation Score (%)")
    ax.set_ylabel("Customer Satisfaction (1–5)")
    ax.legend()
    ax.grid(True)

    path = output_dir / "qa_vs_csat.png"
    _save(fig, path)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 8. ERROR DISTRIBUTION (Histograma)
# ─────────────────────────────────────────────────────────────────────────────

def plot_error_distribution(df: pd.DataFrame, output_dir: Path) -> Path:
    """
    Histograma de distribución de errores por evaluación.

    Qué muestra: Cómo se distribuye el número de errores entre evaluaciones.
    Por qué importa: Permite identificar si los errores son mayormente bajos
    (distribución sesgada a la izquierda) o si hay una cola de evaluaciones
    con muchos errores que jala el promedio hacia arriba.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Error Distribution Analysis", fontsize=14,
                 fontweight="bold", color=COLOR_DARK)

    # ── Distribución de errores totales ──────────────────────────────────────
    counts = df["Errors"].value_counts().sort_index()
    colors_bar = [COLOR_GREEN if i == 0 else
                  (COLOR_YELLOW if i <= 2 else COLOR_RED)
                  for i in counts.index]
    ax1.bar(counts.index.astype(str), counts.values, color=colors_bar, zorder=3)
    ax1.set_title("Distribution of Errors per Evaluation")
    ax1.set_xlabel("Number of Errors")
    ax1.set_ylabel("Number of Evaluations")
    for x, y in zip(range(len(counts)), counts.values):
        ax1.text(x, y + 20, f"{y:,}", ha="center", fontsize=9, fontweight="bold")
    ax1.grid(True, axis="y")

    # ── QA Score por categoría ────────────────────────────────────────────────
    cat_order = ["Excellent", "Good", "Meets Target", "Below Target"]
    cat_colors = [COLOR_GREEN, COLOR_BLUE, COLOR_YELLOW, COLOR_RED]
    cat_counts = [df[df["QA_Category"] == c].shape[0] for c in cat_order]
    cat_pcts = [c / len(df) * 100 for c in cat_counts]

    bars = ax2.bar(cat_order, cat_pcts, color=cat_colors, zorder=3)
    for bar, val, cnt in zip(bars, cat_pcts, cat_counts):
        ax2.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.3,
                 f"{val:.1f}%\n({cnt:,})",
                 ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax2.set_title("QA Category Distribution")
    ax2.set_xlabel("QA Category")
    ax2.set_ylabel("% of Evaluations")
    ax2.grid(True, axis="y")

    plt.tight_layout()
    path = output_dir / "error_distribution.png"
    _save(fig, path)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL — Generar todas las visualizaciones
# ─────────────────────────────────────────────────────────────────────────────

def generate_all_visualizations(
    df: pd.DataFrame,
    monthly_df: pd.DataFrame,
    team_df: pd.DataFrame,
    process_df: pd.DataFrame,
    top_agents_df: pd.DataFrame,
    bottom_agents_df: pd.DataFrame,
    output_dir: str | Path = "visualizations"
) -> dict:
    """
    Genera todas las visualizaciones del dashboard y las guarda en disco.

    Args:
        df: DataFrame limpio (registros válidos).
        monthly_df: DataFrame de monthly_trend().
        team_df: DataFrame de team_performance().
        process_df: DataFrame de process_performance().
        top_agents_df: DataFrame de top_agents().
        bottom_agents_df: DataFrame de bottom_agents().
        output_dir: Directorio donde guardar las imágenes.

    Returns:
        Diccionario con rutas de las imágenes generadas.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("   GENERATING VISUALIZATIONS")
    print("=" * 60)

    paths = {}
    paths["qa_trend"]          = plot_qa_trend(monthly_df, output_dir)
    paths["qa_by_team"]        = plot_qa_by_team(team_df, output_dir)
    paths["errors_by_process"] = plot_errors_by_process(process_df, output_dir)
    paths["agent_performance"] = plot_agent_performance(top_agents_df, bottom_agents_df, output_dir)
    paths["csat_trend"]        = plot_csat_trend(monthly_df, output_dir)
    paths["qa_vs_csat"]        = plot_qa_vs_csat(df, output_dir)
    paths["error_distribution"]= plot_error_distribution(df, output_dir)

    print(f"\n   ✅ {len(paths)} visualizaciones generadas en: {output_dir}\n")
    return paths


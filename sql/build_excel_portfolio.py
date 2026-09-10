"""
build_excel_portfolio.py
========================
Genera un archivo Excel de portafolio con formato profesional,
fórmulas reales, tablas, estilos y conditional formatting.

Uso:
    python sql/build_excel_portfolio.py

Genera:
    Output/QA_Portfolio_Excel.xlsx
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side, numbers
)
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.series import DataPoint
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule, CellIsRule, FormulaRule
from openpyxl.styles import numbers as num_fmt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

CLEAN_CSV   = ROOT / "Output" / "qa_clean.csv"
OUTPUT_PATH = ROOT / "Output" / "QA_Portfolio_Excel.xlsx"

# ── Colores corporativos ─────────────────────────────────────────────────────
GREEN_DARK   = "1E8449"
GREEN_LIGHT  = "D5F5E3"
RED_DARK     = "C0392B"
RED_LIGHT    = "FADBD8"
YELLOW_DARK  = "D68910"
YELLOW_LIGHT = "FDEBD0"
BLUE_DARK    = "1A5276"
BLUE_MID     = "2E86C1"
BLUE_LIGHT   = "D6EAF8"
GRAY_DARK    = "2C3E50"
GRAY_LIGHT   = "F2F3F4"
WHITE        = "FFFFFF"
HEADER_BG    = "1A3A5C"
HEADER_FG    = "FFFFFF"

def make_fill(hex_color):
    return PatternFill(fill_type="solid", fgColor=hex_color)

def header_font(size=11, bold=True, color=HEADER_FG):
    return Font(name="Calibri", size=size, bold=bold, color=color)

def body_font(size=10, bold=False, color=GRAY_DARK):
    return Font(name="Calibri", size=size, bold=bold, color=color)

def thin_border():
    side = Side(style="thin", color="BFBFBF")
    return Border(left=side, right=side, top=side, bottom=side)

def set_col_width(ws, col_letter, width):
    ws.column_dimensions[col_letter].width = width

def style_header_row(ws, row, cols, bg=HEADER_BG, fg=HEADER_FG, font_size=10):
    for col in range(1, cols + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = make_fill(bg)
        cell.font = Font(name="Calibri", size=font_size, bold=True, color=fg)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border()

def style_data_rows(ws, start_row, end_row, cols, alt=True):
    for r in range(start_row, end_row + 1):
        fill_color = GRAY_LIGHT if (alt and r % 2 == 0) else WHITE
        for c in range(1, cols + 1):
            cell = ws.cell(row=r, column=c)
            if not cell.fill or cell.fill.fgColor.rgb == "00000000":
                cell.fill = make_fill(fill_color)
            cell.font = body_font()
            cell.border = thin_border()
            cell.alignment = Alignment(horizontal="center", vertical="center")


def build_cover(wb: Workbook):
    ws = wb.create_sheet("📋 Cover", 0)
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 50
    ws.column_dimensions["C"].width = 25

    # Título principal
    ws.row_dimensions[1].height = 10
    ws.row_dimensions[2].height = 60
    ws.merge_cells("B2:C2")
    cell = ws["B2"]
    cell.value = "QA ANALYTICS PORTFOLIO"
    cell.font = Font(name="Calibri", size=28, bold=True, color=HEADER_BG)
    cell.alignment = Alignment(horizontal="left", vertical="center")

    ws.row_dimensions[3].height = 25
    ws.merge_cells("B3:C3")
    ws["B3"].value = "Data Quality & Performance Dashboard — 2026"
    ws["B3"].font = Font(name="Calibri", size=14, color="555555")

    ws.row_dimensions[4].height = 15

    # Info del autor
    info = [
        ("👤 Author",      "Pedro Medina"),
        ("💼 Role",        "Data Analyst | QA Analyst"),
        ("🛠  Tech Stack", "Python · SQL · Power BI · Excel · DAX"),
        ("📊 Dataset",     "50,100 QA Evaluations — Contact Center 2026"),
        ("📁 GitHub",      "github.com/Pmedina30/qa-analytics-dashboard"),
    ]
    for i, (label, value) in enumerate(info, start=5):
        ws.row_dimensions[i].height = 22
        ws[f"B{i}"].value = label
        ws[f"B{i}"].font = Font(name="Calibri", size=11, bold=True, color=BLUE_DARK)
        ws[f"C{i}"].value = value
        ws[f"C{i}"].font = Font(name="Calibri", size=11, color=GRAY_DARK)

    ws.row_dimensions[10].height = 20
    ws.merge_cells("B10:C10")
    ws["B10"].value = "CONTENTS"
    ws["B10"].font = Font(name="Calibri", size=13, bold=True, color=HEADER_BG)

    sheets_info = [
        ("📊 KPI Dashboard",     "Executive summary of all KPIs vs targets"),
        ("👥 Team Analysis",     "Team performance ranked by QA Score"),
        ("⚙️ Process Analysis",  "Process risk analysis by critical error rate"),
        ("🏆 Agent Performance", "Top 10 & Bottom 10 agents with ranking"),
        ("📈 Monthly Trend",     "Month-over-month KPI evolution"),
        ("🔗 Correlation",       "QA Score vs CSAT relationship analysis"),
    ]
    for i, (sheet, desc) in enumerate(sheets_info, start=11):
        ws.row_dimensions[i].height = 20
        ws[f"B{i}"].value = sheet
        ws[f"B{i}"].font = Font(name="Calibri", size=10, bold=True, color=BLUE_MID)
        ws[f"C{i}"].value = desc
        ws[f"C{i}"].font = body_font()

    ws.sheet_view.showGridLines = False


def build_kpi_dashboard(wb: Workbook, df: pd.DataFrame):
    ws = wb.create_sheet("📊 KPI Dashboard")
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 3

    # ── Título ───────────────────────────────────────────────────────────────
    ws.merge_cells("B1:I1")
    ws["B1"].value = "QA PERFORMANCE — KPI EXECUTIVE DASHBOARD"
    ws["B1"].font = Font(name="Calibri", size=16, bold=True, color=HEADER_BG)
    ws["B1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 35

    ws.merge_cells("B2:I2")
    ws["B2"].value = f"Period: {df['Date'].min().strftime('%B %d, %Y')} – {df['Date'].max().strftime('%B %d, %Y')}  |  Total Evaluations: {len(df):,}"
    ws["B2"].font = Font(name="Calibri", size=10, color="777777")
    ws["B2"].alignment = Alignment(horizontal="center")
    ws.row_dimensions[2].height = 20

    # ── KPI Cards (Row 4–9) ───────────────────────────────────────────────────
    kpis = [
        ("Avg QA Score",        f"{df['Evaluation_Score'].mean():.2f}%",        "Target: >= 85%",  df['Evaluation_Score'].mean() >= 85,   "B"),
        ("Pass Rate",           f"{df['Pass_Flag'].mean()*100:.2f}%",            "Target: >= 85%",  df['Pass_Flag'].mean()*100 >= 85,      "D"),
        ("Critical Error Rate", f"{df['Critical_Error_Flag'].mean()*100:.2f}%", "Target: < 2%",    df['Critical_Error_Flag'].mean()*100 < 2, "F"),
        ("Avg CSAT",            f"{df['Customer_Satisfaction'].mean():.2f}",     "Target: >= 4.2",  df['Customer_Satisfaction'].mean() >= 4.2,"H"),
    ]

    ws.row_dimensions[4].height = 15
    for label, value, target, on_target, col in kpis:
        color = GREEN_DARK if on_target else RED_DARK
        light  = GREEN_LIGHT if on_target else RED_LIGHT
        icon   = "✅" if on_target else "❌"

        ws.merge_cells(f"{col}5:{col}5")
        title_cell = ws[f"{col}5"]
        title_cell.value = label
        title_cell.font = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
        title_cell.fill = make_fill(color)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[5].height = 18

        val_cell = ws[f"{col}6"]
        val_cell.value = value
        val_cell.font = Font(name="Calibri", size=18, bold=True, color=color)
        val_cell.fill = make_fill(light)
        val_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[6].height = 35

        tgt_cell = ws[f"{col}7"]
        tgt_cell.value = f"{icon} {target}"
        tgt_cell.font = Font(name="Calibri", size=9, color="444444")
        tgt_cell.fill = make_fill(light)
        tgt_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[7].height = 18

        # Set width
        ws.column_dimensions[col].width = 18

    # ── KPI Table ────────────────────────────────────────────────────────────
    ws.row_dimensions[10].height = 20
    headers = ["KPI", "Result", "Target", "Status", "Unit"]
    data = [
        ["Total Evaluations",       f"{len(df):,}",                              "N/A",      "N/A",         "count"],
        ["Average QA Score",        f"{df['Evaluation_Score'].mean():.2f}",      ">= 85",    "✅ On Target" if df['Evaluation_Score'].mean() >= 85 else "❌ Below", "%"],
        ["Pass Rate",               f"{df['Pass_Flag'].mean()*100:.2f}",         ">= 85",    "✅ On Target" if df['Pass_Flag'].mean()*100 >= 85 else "❌ Below",    "%"],
        ["Fail Rate",               f"{(1-df['Pass_Flag'].mean())*100:.2f}",     "< 15",     "N/A",         "%"],
        ["Critical Error Rate",     f"{df['Critical_Error_Flag'].mean()*100:.2f}","< 2",     "✅ On Target" if df['Critical_Error_Flag'].mean()*100 < 2 else "❌ Above", "%"],
        ["Average Errors / Eval",   f"{df['Errors'].mean():.2f}",                "N/A",      "Monitor",     "count"],
        ["Average CSAT",            f"{df['Customer_Satisfaction'].mean():.2f}", ">= 4.2",   "✅ On Target" if df['Customer_Satisfaction'].mean() >= 4.2 else "❌ Below", "1–5"],
        ["Average Resolution Time", f"{df['Resolution_Time_Min'].mean():.2f}",  "Trend",    "Monitor",     "minutes"],
    ]

    for col_idx, h in enumerate(headers, start=2):
        cell = ws.cell(row=10, column=col_idx, value=h)
        cell.fill = make_fill(HEADER_BG)
        cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border()
        ws.column_dimensions[get_column_letter(col_idx)].width = 22

    for r_idx, row_data in enumerate(data, start=11):
        for c_idx, val in enumerate(row_data, start=2):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.font = body_font()
            cell.border = thin_border()
            cell.alignment = Alignment(horizontal="center", vertical="center")
            fill_color = GRAY_LIGHT if r_idx % 2 == 0 else WHITE
            cell.fill = make_fill(fill_color)
            # Color status column
            if c_idx == 5:
                if "✅" in str(val):
                    cell.font = Font(name="Calibri", size=10, bold=True, color=GREEN_DARK)
                elif "❌" in str(val):
                    cell.font = Font(name="Calibri", size=10, bold=True, color=RED_DARK)
        ws.row_dimensions[10 + r_idx - 10].height = 20


def build_team_sheet(wb: Workbook, df: pd.DataFrame):
    ws = wb.create_sheet("👥 Team Analysis")
    ws.sheet_view.showGridLines = False

    team_agg = df.groupby("Team").agg(
        Evaluations         =("Evaluation_ID","count"),
        Avg_QA_Score        =("Evaluation_Score","mean"),
        Pass_Rate           =("Pass_Flag","mean"),
        Critical_Error_Rate =("Critical_Error_Flag","mean"),
        Avg_CSAT            =("Customer_Satisfaction","mean"),
        Avg_Resolution_Min  =("Resolution_Time_Min","mean"),
    ).reset_index()
    team_agg["Pass_Rate"] = team_agg["Pass_Rate"] * 100
    team_agg["Critical_Error_Rate"] = team_agg["Critical_Error_Rate"] * 100
    team_agg = team_agg.round(2).sort_values("Avg_QA_Score", ascending=False).reset_index(drop=True)
    team_agg["Rank"] = range(1, len(team_agg)+1)
    team_agg["QA_Status"] = team_agg["Avg_QA_Score"].apply(
        lambda x: "✅ On Target" if x >= 85 else "❌ Below Target"
    )

    # Title
    ws.merge_cells("A1:I1")
    ws["A1"].value = "TEAM PERFORMANCE ANALYSIS — Ranked by Avg QA Score"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color=HEADER_BG)
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    cols = ["Rank","Team","Evaluations","Avg_QA_Score","Pass_Rate",
            "Critical_Error_Rate","Avg_CSAT","Avg_Resolution_Min","QA_Status"]
    headers = ["#","Team","Evaluations","Avg QA Score %","Pass Rate %",
               "Crit. Error Rate %","Avg CSAT","Avg Res. Time (min)","QA Status"]

    widths = [6, 14, 14, 16, 14, 18, 12, 20, 16]
    for c_idx, (h, w) in enumerate(zip(headers, widths), start=1):
        cell = ws.cell(row=2, column=c_idx, value=h)
        cell.fill = make_fill(HEADER_BG)
        cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border()
        ws.column_dimensions[get_column_letter(c_idx)].width = w
    ws.row_dimensions[2].height = 30

    for r_idx, row in team_agg.iterrows():
        row_num = r_idx + 3
        for c_idx, col in enumerate(cols, start=1):
            val = row[col]
            cell = ws.cell(row=row_num, column=c_idx, value=val)
            cell.font = body_font()
            cell.border = thin_border()
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.fill = make_fill(GRAY_LIGHT if row_num % 2 == 0 else WHITE)

            # Color QA Score cell
            if col == "Avg_QA_Score":
                if val >= 90:
                    cell.fill = make_fill(GREEN_LIGHT)
                    cell.font = Font(name="Calibri", size=10, bold=True, color=GREEN_DARK)
                elif val >= 85:
                    cell.fill = make_fill(YELLOW_LIGHT)
                    cell.font = Font(name="Calibri", size=10, bold=True, color=YELLOW_DARK)
                else:
                    cell.fill = make_fill(RED_LIGHT)
                    cell.font = Font(name="Calibri", size=10, bold=True, color=RED_DARK)

            if col == "QA_Status":
                if "✅" in str(val):
                    cell.font = Font(name="Calibri", size=10, bold=True, color=GREEN_DARK)
                else:
                    cell.font = Font(name="Calibri", size=10, bold=True, color=RED_DARK)
        ws.row_dimensions[row_num].height = 22

    # Nota metodológica
    note_row = len(team_agg) + 4
    ws.merge_cells(f"A{note_row}:I{note_row}")
    ws[f"A{note_row}"].value = "📌 Target: QA Score >= 85% | Pass Rate >= 85% | Critical Error Rate < 2% | CSAT >= 4.2"
    ws[f"A{note_row}"].font = Font(name="Calibri", size=9, italic=True, color="777777")


def build_agent_sheet(wb: Workbook, df: pd.DataFrame):
    ws = wb.create_sheet("🏆 Agent Performance")
    ws.sheet_view.showGridLines = False

    agent_agg = df.groupby(["Agent","Team","Supervisor"]).agg(
        Evaluations         =("Evaluation_ID","count"),
        Avg_QA_Score        =("Evaluation_Score","mean"),
        Pass_Rate           =("Pass_Flag","mean"),
        Avg_CSAT            =("Customer_Satisfaction","mean"),
        Critical_Error_Rate =("Critical_Error_Flag","mean"),
        Avg_Resolution_Min  =("Resolution_Time_Min","mean"),
    ).reset_index()
    agent_agg["Pass_Rate"] *= 100
    agent_agg["Critical_Error_Rate"] *= 100
    agent_agg = agent_agg.round(2)
    agent_agg = agent_agg[agent_agg["Evaluations"] >= 30]
    agent_agg = agent_agg.sort_values("Avg_QA_Score", ascending=False).reset_index(drop=True)
    agent_agg["Global_Rank"] = range(1, len(agent_agg)+1)

    # Top 10 + Bottom 10
    top10    = agent_agg.head(10).copy()
    bottom10 = agent_agg.tail(10).copy()

    ws.merge_cells("A1:J1")
    ws["A1"].value = "AGENT PERFORMANCE RANKING — Top 10 & Bottom 10 (Min. 30 Evaluations)"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color=HEADER_BG)
    ws["A1"].alignment = Alignment(horizontal="center")
    ws.row_dimensions[1].height = 30

    def write_section(title, data, start_row, badge_color, badge_light):
        ws.merge_cells(f"A{start_row}:J{start_row}")
        ws[f"A{start_row}"].value = title
        ws[f"A{start_row}"].font = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
        ws[f"A{start_row}"].fill = make_fill(badge_color)
        ws[f"A{start_row}"].alignment = Alignment(horizontal="center")
        ws.row_dimensions[start_row].height = 25

        headers = ["Rank","Agent","Team","Supervisor","Evals","QA Score","Pass Rate %","CSAT","Crit. Err %","Res. Time"]
        widths   = [6,20,12,15,10,14,14,10,13,13]
        for c_idx,(h,w) in enumerate(zip(headers,widths),start=1):
            cell = ws.cell(row=start_row+1, column=c_idx, value=h)
            cell.fill = make_fill(badge_color)
            cell.font = Font(name="Calibri",size=9,bold=True,color="FFFFFF")
            cell.alignment = Alignment(horizontal="center",wrap_text=True)
            cell.border = thin_border()
            ws.column_dimensions[get_column_letter(c_idx)].width = w
        ws.row_dimensions[start_row+1].height = 25

        cols = ["Global_Rank","Agent","Team","Supervisor","Evaluations",
                "Avg_QA_Score","Pass_Rate","Avg_CSAT","Critical_Error_Rate","Avg_Resolution_Min"]
        for r,row in data.iterrows():
            rn = start_row+2+(r % 10)
            for c_idx,col in enumerate(cols,start=1):
                cell = ws.cell(row=rn,column=c_idx,value=row[col])
                cell.font = body_font(size=9)
                cell.border = thin_border()
                cell.alignment = Alignment(horizontal="center")
                cell.fill = make_fill(badge_light if rn%2==0 else WHITE)
                if col == "Avg_QA_Score":
                    if row[col] >= 90: cell.font=Font(name="Calibri",size=9,bold=True,color=GREEN_DARK)
                    elif row[col] >= 85: cell.font=Font(name="Calibri",size=9,bold=True,color=YELLOW_DARK)
                    else: cell.font=Font(name="Calibri",size=9,bold=True,color=RED_DARK)
            ws.row_dimensions[rn].height = 20

    write_section("🏆  TOP 10 AGENTS — Highest QA Score",   top10,    3,  GREEN_DARK, GREEN_LIGHT)
    write_section("⚠️  BOTTOM 10 AGENTS — Lowest QA Score", bottom10, 16, RED_DARK,   RED_LIGHT)

    note_row = 28
    ws.merge_cells(f"A{note_row}:J{note_row}")
    ws[f"A{note_row}"].value = "📌 Minimum 30 evaluations required for ranking — agents with fewer evaluations are statistically unreliable"
    ws[f"A{note_row}"].font = Font(name="Calibri",size=9,italic=True,color="777777")


def build_monthly_trend(wb: Workbook, df: pd.DataFrame):
    ws = wb.create_sheet("📈 Monthly Trend")
    ws.sheet_view.showGridLines = False

    monthly = df.groupby(["Year","Month","Month_Name"]).agg(
        Evaluations         =("Evaluation_ID","count"),
        Avg_QA_Score        =("Evaluation_Score","mean"),
        Pass_Rate           =("Pass_Flag","mean"),
        Critical_Error_Rate =("Critical_Error_Flag","mean"),
        Avg_CSAT            =("Customer_Satisfaction","mean"),
        Avg_Resolution_Min  =("Resolution_Time_Min","mean"),
    ).reset_index().sort_values(["Year","Month"])
    monthly["Pass_Rate"] *= 100
    monthly["Critical_Error_Rate"] *= 100
    monthly = monthly.round(2)
    monthly["QA_MoM_Change"] = monthly["Avg_QA_Score"].diff().round(2)
    monthly["CSAT_MoM_Change"] = monthly["Avg_CSAT"].diff().round(2)
    monthly["Trend"] = monthly["QA_MoM_Change"].apply(
        lambda x: "📈 Improving" if x > 0.5 else ("📉 Declining" if x < -0.5 else "➡️ Stable") if pd.notna(x) else "—"
    )

    ws.merge_cells("A1:L1")
    ws["A1"].value = "MONTHLY TREND ANALYSIS — QA Score, Pass Rate, Critical Error Rate, CSAT"
    ws["A1"].font = Font(name="Calibri",size=14,bold=True,color=HEADER_BG)
    ws["A1"].alignment = Alignment(horizontal="center")
    ws.row_dimensions[1].height = 30

    headers = ["Month","Year","Evaluations","Avg QA Score","QA MoM Δ",
               "Pass Rate %","Crit. Error %","Avg CSAT","CSAT MoM Δ","Avg Res. Min","Trend"]
    widths   = [14,8,14,16,12,14,14,12,12,16,14]
    cols     = ["Month_Name","Year","Evaluations","Avg_QA_Score","QA_MoM_Change",
               "Pass_Rate","Critical_Error_Rate","Avg_CSAT","CSAT_MoM_Change","Avg_Resolution_Min","Trend"]

    for c_idx,(h,w) in enumerate(zip(headers,widths),start=1):
        cell = ws.cell(row=2,column=c_idx,value=h)
        cell.fill = make_fill(HEADER_BG)
        cell.font = Font(name="Calibri",size=10,bold=True,color="FFFFFF")
        cell.alignment = Alignment(horizontal="center",wrap_text=True)
        cell.border = thin_border()
        ws.column_dimensions[get_column_letter(c_idx)].width = w
    ws.row_dimensions[2].height = 30

    for r_idx,row in monthly.reset_index(drop=True).iterrows():
        rn = r_idx+3
        for c_idx,col in enumerate(cols,start=1):
            val = row[col]
            cell = ws.cell(row=rn,column=c_idx,value=val)
            cell.font = body_font()
            cell.border = thin_border()
            cell.alignment = Alignment(horizontal="center")
            cell.fill = make_fill(GRAY_LIGHT if rn%2==0 else WHITE)

            if col == "QA_MoM_Change" and pd.notna(val):
                if val > 0: cell.font=Font(name="Calibri",size=10,bold=True,color=GREEN_DARK)
                elif val < 0: cell.font=Font(name="Calibri",size=10,bold=True,color=RED_DARK)
            if col == "Avg_QA_Score":
                if val >= 90: cell.fill=make_fill(GREEN_LIGHT)
                elif val >= 85: cell.fill=make_fill(YELLOW_LIGHT)
                else: cell.fill=make_fill(RED_LIGHT)
        ws.row_dimensions[rn].height = 22


def main():
    print("=" * 55)
    print("  Building Excel Portfolio File")
    print("=" * 55)

    if not CLEAN_CSV.exists():
        print(f"  ERROR: {CLEAN_CSV} not found. Run run_analysis.py first.")
        sys.exit(1)

    df = pd.read_csv(CLEAN_CSV, parse_dates=["Date"])
    df = df[df["data_valid"] == True].copy()
    print(f"  Loaded: {len(df):,} valid records")

    wb = Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    print("  Building sheets...")
    build_cover(wb)
    print("    ✓ Cover")
    build_kpi_dashboard(wb, df)
    print("    ✓ KPI Dashboard")
    build_team_sheet(wb, df)
    print("    ✓ Team Analysis")
    build_agent_sheet(wb, df)
    print("    ✓ Agent Performance")
    build_monthly_trend(wb, df)
    print("    ✓ Monthly Trend")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT_PATH)
    print(f"\n  ✅ Excel saved: {OUTPUT_PATH}")
    print("=" * 55)

if __name__ == "__main__":
    main()

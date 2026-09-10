# QA Analytics & Data Quality Dashboard

> **Proyecto profesional de Quality Assurance + Data Analytics**
> Construido con Python · Pandas · NumPy · Matplotlib · Power BI · DAX

---

## Project Overview

Este proyecto simula un entorno real de **Quality Assurance Analytics** en un contact center. Combina técnicas de ingeniería de datos, análisis estadístico y visualización de negocio para responder preguntas operacionales críticas sobre la calidad del servicio.

El pipeline procesa **50,100 evaluaciones de agentes** del año 2026, calcula KPIs de calidad, identifica patrones de desempeño y genera un dashboard ejecutivo interactivo en Power BI.

---

## Business Problem

Los equipos de QA en contact centers generan grandes volúmenes de datos de evaluación que raramente se analizan de manera sistemática. Las preguntas de negocio sin respuesta incluyen:

- ¿Qué tan confiable es la calidad de nuestros datos de evaluación?
- ¿Qué equipos y procesos representan mayor riesgo operacional?
- ¿Está mejorando o deteriorando la calidad en el tiempo?
- ¿Qué agentes necesitan coaching y cuáles pueden ser mentores?
- ¿Existe relación entre el score de calidad y la satisfacción del cliente?

Este proyecto responde todas estas preguntas con un pipeline reproducible y documentado.

---

## Dataset

| Atributo | Detalle |
|----------|---------|
| Archivo | `Data/qa_evaluations_2026.csv` |
| Registros | 50,100 |
| Columnas | 12 |
| Período | 2026 |
| Fuente | Evaluaciones de calidad internas |

### Columnas

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `Evaluation_ID` | int | Identificador único de la evaluación |
| `Date` | date | Fecha de la evaluación |
| `Agent` | str | Nombre del agente evaluado |
| `Team` | str | Equipo al que pertenece el agente |
| `Supervisor` | str | Supervisor del agente |
| `Process` | str | Proceso evaluado (Billing, Retention, etc.) |
| `Evaluation_Score` | float | Score de calidad (0–100) |
| `Errors` | int | Número de errores identificados |
| `Critical_Error` | str | Indica si hubo error crítico (Yes/No) |
| `Customer_Satisfaction` | float | CSAT del cliente (1–5) |
| `Resolution_Time_Min` | float | Tiempo de resolución en minutos |
| `Status` | str | Resultado de la evaluación (Pass/Fail) |

---

## Technologies

| Tecnología | Uso |
|-----------|-----|
| **Python 3.11+** | Lenguaje principal del pipeline |
| **Pandas** | Manipulación y análisis de datos |
| **NumPy** | Cálculos numéricos y estadísticos |
| **Matplotlib** | Visualizaciones profesionales |
| **OpenPyXL** | Exportación a Excel (.xlsx) |
| **Jupyter Notebook** | Análisis interactivo y documentado |
| **Power BI Desktop** | Dashboard ejecutivo de BI |
| **DAX** | Medidas calculadas en Power BI |

---

## Data Quality

El módulo `src/data_quality.py` ejecuta **14 validaciones** automáticas:

| Validación | Descripción |
|-----------|-------------|
| Total de registros | Dimensiones del dataset |
| Duplicados completos | Filas 100% idénticas |
| IDs duplicados | Evaluation_IDs repetidos |
| Valores nulos | Por columna y total |
| QA Score inválido | Fuera del rango 0–100 |
| CSAT inválido | Fuera del rango 1–5 |
| Resolution Time inválido | Valores <= 0 |
| Errors negativos | Valores < 0 |
| Critical_Error inválido | Valores ≠ Yes/No |
| Status inválido | Valores ≠ Pass/Fail |
| Fechas inválidas | No parseables |
| Rango de fechas | Min y Max del período |

### Data Quality Score

```
DQ Score = max(0, 1 - total_issues / total_records) × 100

Donde total_issues = duplicados + nulos + valores inválidos
```

| Score | Nivel |
|-------|-------|
| >= 98% | Alta calidad |
| 95–97% | Buena calidad |
| 90–94% | Calidad aceptable |
| < 90% | Calidad baja |

---

## Data Cleaning

Pipeline de **6 pasos** en `src/data_cleaning.py`:

1. **Eliminar duplicados** — filas completas e IDs repetidos
2. **Convertir fechas** — string → datetime para análisis temporal
3. **Manejar nulos** — Supervisor → "Unknown"; CSAT → mediana grupal
4. **Validar rangos** — marcar registros inválidos sin eliminarlos (columna `data_valid`)
5. **Normalizar categorías** — strip + title case para evitar fragmentación
6. **Crear columnas derivadas** — Week, Month, Year, Day_of_Week, QA_Category, flags

> **Principio fundamental:** El dataset original nunca se modifica.
> El dataset limpio se guarda en `output/qa_clean.csv`.

---

## KPI Framework

| KPI | Target | Fórmula |
|-----|--------|---------|
| QA Score | >= 85% | `mean(Evaluation_Score)` |
| Pass Rate | >= 85% | `sum(Pass_Flag) / count × 100` |
| Critical Error Rate | < 2% | `sum(Critical_Error_Flag) / count × 100` |
| CSAT | >= 4.2 | `mean(Customer_Satisfaction)` |
| Resolution Time | Tendencia | `mean(Resolution_Time_Min)` |

---

## Analysis

El módulo `src/analysis.py` calcula:

- **Team Performance** — KPIs por equipo, ordenado por QA Score desc
- **Process Performance** — KPIs por proceso, ordenado por Critical Error Rate desc
- **Agent Performance** — KPIs por agente (solo elegibles con >= 30 evaluaciones para ranking)
- **Top 10 / Bottom 10 Agents** — Rankings de desempeño
- **Daily / Weekly / Monthly Trends** — Evolución temporal de KPIs
- **Correlation Analysis** — Pearson r entre variables clave con advertencia de causalidad
- **Executive Insights** — Reporte automático de Facts / Insights / Recommendations

### Nota sobre el mínimo de evaluaciones para ranking

Se requieren **mínimo 30 evaluaciones** para incluir a un agente en el ranking. Con menos datos, el promedio es estadísticamente poco representativo (alta varianza), y las conclusiones sobre el desempeño individual serían prematuras. Este umbral es una heurística conservadora, no un límite estadístico estricto.

---

## Power BI Dashboard

El dashboard tiene **3 páginas**:

### Página 1 — Executive Overview
KPI Cards + QA Score Trend + QA by Team + Critical Errors by Process + Agent Performance

### Página 2 — Quality Analysis
QA by Team y Process + Error Distribution + CSAT Trend + Resolution Time Trend + QA Category Distribution

### Página 3 — Agent Performance
Tabla completa con conditional formatting + Top 10 / Bottom 10 + Ranking

Ver `powerbi/README_POWERBI.md` para instrucciones detalladas de construcción.
Ver `powerbi/DAX_MEASURES.md` para todas las medidas DAX con explicaciones.

---

## Business Insights

El reporte ejecutivo (`output/executive_insights.txt`) responde:

1. ¿Cuál es el QA Score general? → Con comparación vs target
2. ¿Cuál es el mejor / peor equipo? → Con scores específicos
3. ¿Qué proceso tiene más errores críticos? → Con tasa
4. ¿Qué agentes están debajo del target? → Solo elegibles
5. ¿La calidad está mejorando o empeorando? → Comparación primer vs último mes
6. ¿Existe relación QA Score–CSAT? → Pearson r con advertencia de causalidad
7. ¿Cuál es el principal riesgo de calidad? → KPI más crítico fuera de target

---

## How to Run

### Requisitos previos
```bash
pip install -r requirements.txt
```

### Ejecutar el pipeline completo
```bash
python run_analysis.py
```

### Ejecutar el notebook interactivo
```bash
jupyter notebook Notebooks/QA_Analysis.ipynb
```

### Archivos generados
| Archivo | Descripción |
|---------|-------------|
| `Output/qa_clean.csv` | Dataset limpio con columnas derivadas |
| `Output/data_quality_report.csv` | Reporte de calidad de datos |
| `Output/qa_summary.xlsx` | Excel con 8 hojas de análisis |
| `Output/executive_insights.txt` | Reporte ejecutivo automático |
| `visualizations/*.png` | 7 gráficos profesionales |

---

## Project Structure

```
QA-Analytics/
│
├── Data/
│   └── qa_evaluations_2026.csv        ← Dataset crudo (no modificar)
│
├── Notebooks/
│   └── QA_Analysis.ipynb              ← Análisis interactivo documentado
│
├── src/
│   ├── data_quality.py                ← 14 validaciones automáticas
│   ├── data_cleaning.py               ← Pipeline de limpieza en 6 pasos
│   ├── kpis.py                        ← Cálculo de KPIs con targets
│   ├── analysis.py                    ← Análisis de negocio multidimensional
│   └── visualizations.py              ← 8 gráficos profesionales
│
├── Output/
│   ├── qa_clean.csv                   ← Dataset limpio (generado)
│   ├── data_quality_report.csv        ← Reporte DQ (generado)
│   ├── qa_summary.xlsx                ← Excel ejecutivo (generado)
│   └── executive_insights.txt         ← Insights automáticos (generado)
│
├── visualizations/
│   ├── qa_trend.png
│   ├── qa_by_team.png
│   ├── errors_by_process.png
│   ├── agent_performance.png
│   ├── csat_trend.png
│   ├── qa_vs_csat.png
│   └── error_distribution.png
│
├── powerbi/
│   ├── README_POWERBI.md              ← Guía de construcción del dashboard
│   └── DAX_MEASURES.md               ← Todas las medidas DAX documentadas
│
├── run_analysis.py                    ← Pipeline principal (un solo comando)
├── requirements.txt
└── README.md
```

---

## Skills Demonstrated

### Python & Data Engineering
- ✅ **Python** — Código modular, funciones documentadas, manejo de errores
- ✅ **Pandas** — Limpieza, transformación, agregación, groupby, merge
- ✅ **NumPy** — Cálculos numéricos, correlaciones, estadísticas descriptivas
- ✅ **Data Cleaning** — Pipeline reproducible de 6 pasos sin modificar el original
- ✅ **Data Quality** — 14 validaciones automáticas + Data Quality Score compuesto

### Analytics & Statistics
- ✅ **Exploratory Data Analysis (EDA)** — Distribuciones, outliers, rangos
- ✅ **KPI Analysis** — Diseño de indicadores con targets y estado de cumplimiento
- ✅ **Statistical Thinking** — Correlación de Pearson con advertencia de causalidad
- ✅ **Business Analysis** — Team, Process, Agent y Trend analysis

### Visualization & BI
- ✅ **Data Visualization** — 8 gráficos profesionales con Matplotlib
- ✅ **Power BI** — Dashboard de 3 páginas con KPI Cards, slicers, trends
- ✅ **DAX** — 20+ medidas calculadas con conditional formatting
- ✅ **Business Intelligence** — Insights ejecutivos orientados a decisión

---

## Author

**QA Analytics Project — 2026**
Diseñado como portafolio profesional para roles de QA Analyst / Data Analyst.

> *"Los datos de calidad solo tienen valor cuando se transforman en decisiones de negocio."*


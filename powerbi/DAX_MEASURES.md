# DAX Measures — QA Performance Dashboard

> **Propósito:** Todas las medidas DAX necesarias para construir el QA Performance Dashboard en Power BI.
> Cada medida incluye: nombre, código DAX, explicación y unidad.

---

## Convenciones de nombrado

| Prefijo | Significado |
|---------|-------------|
| `[KPI_]` | Indicador clave de desempeño |
| `[RATE_]` | Tasa expresada en % |
| `[AVG_]` | Promedio |
| `[CNT_]` | Conteo |
| `[TARGET_]` | Valor de target |

---

## 1. Medidas base de volumen

### Total Evaluations
```dax
[KPI_Total Evaluations] =
COUNTROWS( qa_clean )
```
**Explicación:** Cuenta todas las filas visibles en el contexto de filtro actual (slicer de fecha, equipo, etc.).
**Unidad:** Número entero.

---

### Agents Evaluated
```dax
[CNT_Agents Evaluated] =
DISTINCTCOUNT( qa_clean[Agent] )
```
**Explicación:** Número de agentes únicos evaluados en el período filtrado. Ayuda a entender la cobertura del programa de calidad.
**Unidad:** Número entero.

---

## 2. Medidas de QA Score

### Average QA Score
```dax
[AVG_QA Score] =
AVERAGE( qa_clean[Evaluation_Score] )
```
**Explicación:** Promedio de `Evaluation_Score` en el contexto de filtro actual.
**Formato sugerido:** `##.00"%"`
**Unidad:** Porcentaje (0–100).

---

### QA Score vs Target
```dax
[KPI_QA Score vs Target] =
[AVG_QA Score] - [TARGET_QA Score]
```
**Explicación:** Diferencia entre el score actual y el target. Positivo = supera el target. Negativo = debajo del target.
**Uso:** KPI Card con formato condicional.

---

### Target QA Score
```dax
[TARGET_QA Score] = 85
```
**Explicación:** Constante que representa el target mínimo de QA Score definido por el área de calidad.

---

## 3. Medidas de Pass / Fail Rate

### Pass Rate
```dax
[RATE_Pass Rate] =
DIVIDE(
    COUNTROWS( FILTER( qa_clean, qa_clean[Status] = "Pass" ) ),
    COUNTROWS( qa_clean ),
    0
)
```
**Explicación:** Proporción de evaluaciones aprobadas. `DIVIDE` maneja la división por cero retornando 0.
**Formato sugerido:** `0.00%`
**Unidad:** Porcentaje (0–1 internamente, mostrar como %).

---

### Fail Rate
```dax
[RATE_Fail Rate] =
1 - [RATE_Pass Rate]
```
**Explicación:** Complemento del Pass Rate. Evita recalcular el denominador.
**Formato sugerido:** `0.00%`

---

### Pass Rate %
```dax
[RATE_Pass Rate %] =
[RATE_Pass Rate] * 100
```
**Explicación:** Versión en escala 0–100 para visuales que no usan formato %. Útil para KPI Cards con texto.

---

## 4. Critical Error Rate

### Critical Error Rate
```dax
[RATE_Critical Error Rate] =
DIVIDE(
    COUNTROWS( FILTER( qa_clean, qa_clean[Critical_Error] = "Yes" ) ),
    COUNTROWS( qa_clean ),
    0
)
```
**Explicación:** Proporción de evaluaciones con error crítico. El target es < 2%.
**Formato sugerido:** `0.00%`

---

### Critical Error Rate %
```dax
[RATE_Critical Error Rate %] =
[RATE_Critical Error Rate] * 100
```

---

### Critical Errors Count
```dax
[CNT_Critical Errors] =
COUNTROWS( FILTER( qa_clean, qa_clean[Critical_Error] = "Yes" ) )
```
**Explicación:** Número absoluto de evaluaciones con error crítico. Útil para tablas de detalle.

---

## 5. Errores

### Average Errors
```dax
[AVG_Errors per Evaluation] =
AVERAGE( qa_clean[Errors] )
```
**Explicación:** Promedio de errores por evaluación en el contexto filtrado.
**Formato sugerido:** `0.00`

---

### Total Errors
```dax
[CNT_Total Errors] =
SUM( qa_clean[Errors] )
```

---

## 6. CSAT

### Average CSAT
```dax
[AVG_CSAT] =
AVERAGE( qa_clean[Customer_Satisfaction] )
```
**Explicación:** Promedio de satisfacción del cliente en escala 1–5. Target >= 4.2.
**Formato sugerido:** `0.00`

---

### Target CSAT
```dax
[TARGET_CSAT] = 4.2
```

---

### CSAT vs Target
```dax
[KPI_CSAT vs Target] =
[AVG_CSAT] - [TARGET_CSAT]
```
**Uso:** KPI Card con formato condicional (positivo = verde, negativo = rojo).

---

## 7. Resolution Time

### Average Resolution Time
```dax
[AVG_Resolution Time (Min)] =
AVERAGE( qa_clean[Resolution_Time_Min] )
```
**Explicación:** Tiempo promedio de resolución en minutos. Se analiza como tendencia, no contra un target fijo.
**Formato sugerido:** `0.0 "min"`

---

### Max Resolution Time
```dax
[MAX_Resolution Time] =
MAX( qa_clean[Resolution_Time_Min] )
```

---

### Min Resolution Time
```dax
[MIN_Resolution Time] =
MIN( qa_clean[Resolution_Time_Min] )
```

---

## 8. Ranking de agentes

### Agents Below QA Target
```dax
[CNT_Agents Below Target] =
CALCULATE(
    DISTINCTCOUNT( qa_clean[Agent] ),
    FILTER(
        SUMMARIZE(
            qa_clean,
            qa_clean[Agent],
            "AgentScore", AVERAGE( qa_clean[Evaluation_Score] )
        ),
        [AgentScore] < 85
    )
)
```
**Explicación:** Cuenta agentes cuyo promedio de QA Score está debajo de 85%. Requiere SUMMARIZE para calcular el promedio por agente primero.

---

### Top Agent by QA Score
```dax
[TOP_Agent by QA Score] =
TOPN(
    1,
    SUMMARIZE(
        qa_clean,
        qa_clean[Agent],
        "Score", AVERAGE( qa_clean[Evaluation_Score] )
    ),
    [Score],
    DESC
)
```
> ⚠️ Esta medida retorna una tabla. Para mostrar el nombre usa:

```dax
[TOP_Agent Name] =
CALCULATE(
    FIRSTNONBLANK( qa_clean[Agent], 1 ),
    TOPN(
        1,
        SUMMARIZE(
            qa_clean,
            qa_clean[Agent],
            "Score", AVERAGE( qa_clean[Evaluation_Score] )
        ),
        [Score],
        DESC
    )
)
```

---

### Bottom Agent by QA Score
```dax
[BOTTOM_Agent Name] =
CALCULATE(
    FIRSTNONBLANK( qa_clean[Agent], 1 ),
    TOPN(
        1,
        SUMMARIZE(
            qa_clean,
            qa_clean[Agent],
            "Score", AVERAGE( qa_clean[Evaluation_Score] )
        ),
        [Score],
        ASC
    )
)
```

---

## 9. Medidas de formato condicional

### Color QA Score
```dax
[COLOR_QA Score] =
SWITCH(
    TRUE(),
    [AVG_QA Score] >= 90, "#2ecc71",   -- Verde
    [AVG_QA Score] >= 85, "#f39c12",   -- Amarillo
    "#e74c3c"                           -- Rojo
)
```
**Uso:** Campo de color de fondo en KPI Card o tabla.

---

### Color Pass Rate
```dax
[COLOR_Pass Rate] =
IF( [RATE_Pass Rate %] >= 85, "#2ecc71", "#e74c3c" )
```

---

### Color Critical Error Rate
```dax
[COLOR_Critical Error Rate] =
IF( [RATE_Critical Error Rate %] < 2, "#2ecc71", "#e74c3c" )
```

---

### Color CSAT
```dax
[COLOR_CSAT] =
SWITCH(
    TRUE(),
    [AVG_CSAT] >= 4.2, "#2ecc71",
    [AVG_CSAT] >= 3.8, "#f39c12",
    "#e74c3c"
)
```

---

## 10. Calendar Table (si no usas la columna Date directamente)

```dax
CalendarTable =
ADDCOLUMNS(
    CALENDARAUTO(),
    "Year",        YEAR( [Date] ),
    "Month Number",MONTH( [Date] ),
    "Month Name",  FORMAT( [Date], "MMMM" ),
    "Quarter",     "Q" & FORMAT( QUARTER( [Date] ), "0" ),
    "Week",        WEEKNUM( [Date], 2 ),
    "Day of Week", FORMAT( [Date], "dddd" ),
    "Is Weekday",  IF( WEEKDAY( [Date], 2 ) <= 5, TRUE, FALSE )
)
```

**Cómo relacionar con la tabla de evaluaciones:**
1. En Power BI Desktop → Vista "Model" (ícono de diagrama).
2. Arrastra `CalendarTable[Date]` hacia `qa_clean[Date]`.
3. Tipo de relación: **Muchos a uno** (qa_clean → CalendarTable).
4. Dirección de filtro: **Single** (CalendarTable → qa_clean).
5. Marca la CalendarTable como **Date Table** (click derecho → Mark as date table → Date).

---

## Resumen de medidas

| Medida | Categoría | Formato |
|--------|-----------|---------|
| `[KPI_Total Evaluations]` | Volumen | `#,##0` |
| `[CNT_Agents Evaluated]` | Volumen | `#,##0` |
| `[AVG_QA Score]` | QA Score | `0.00"%"` |
| `[RATE_Pass Rate]` | Pass/Fail | `0.00%` |
| `[RATE_Fail Rate]` | Pass/Fail | `0.00%` |
| `[RATE_Critical Error Rate]` | Errores | `0.00%` |
| `[AVG_Errors per Evaluation]` | Errores | `0.00` |
| `[AVG_CSAT]` | CSAT | `0.00` |
| `[AVG_Resolution Time (Min)]` | Tiempo | `0.0` |
| `[CNT_Agents Below Target]` | Agentes | `#,##0` |
| `[TOP_Agent Name]` | Agentes | Texto |
| `[BOTTOM_Agent Name]` | Agentes | Texto |


# Power BI Dashboard — QA Performance Dashboard
## Guía completa de construcción desde cero

---

## Paso 1 — Importar el dataset limpio

1. Abre **Power BI Desktop**.
2. Clic en **Home → Get Data → Text/CSV**.
3. Navega a `output/qa_clean.csv` y haz clic en **Load**.
4. En el panel derecho verás la tabla `qa_clean`.

> **Importante:** No uses el archivo crudo `qa_evaluations_2026.csv`.
> El archivo `qa_clean.csv` contiene todas las columnas derivadas necesarias
> (Week, Month, QA_Category, Pass_Flag, Critical_Error_Flag) y los datos ya limpios.

---

## Paso 2 — Transformar datos en Power Query (si es necesario)

1. Clic en **Transform Data** (Power Query Editor).
2. Verificar que la columna `Date` tenga tipo **Date**.
3. Verificar que `Evaluation_Score`, `Customer_Satisfaction`, `Resolution_Time_Min`
   sean tipo **Decimal Number**.
4. Verificar que `Errors`, `Pass_Flag`, `Critical_Error_Flag` sean tipo **Whole Number**.
5. Clic en **Close & Apply**.

---

## Paso 3 — Crear la Calendar Table (opcional pero recomendado)

En la pestaña **Modeling → New Table**, pega el DAX de `DAX_MEASURES.md`.

Luego en la vista **Model**:
- Relaciona `CalendarTable[Date]` → `qa_clean[Date]`
- Dirección: Single (CalendarTable filtra qa_clean)
- Cardinalidad: Many-to-one

---

## Paso 4 — Crear las medidas DAX

1. En el panel de datos, haz clic derecho sobre `qa_clean` → **New Measure**.
2. Pega cada medida de `DAX_MEASURES.md`.
3. Agrúpalas en una tabla de medidas:
   - Crea una nueva tabla vacía: **Enter Data** → nombre `_Measures`.
   - Mueve todas las medidas ahí desde el panel de campos.

---

## Modelo de datos recomendado

Para este proyecto (una sola fuente de datos), el modelo es estrella simple:

```
CalendarTable ─────────────────────┐
(Date Table)                       │
                                   ▼
                             [ qa_clean ]
                          (Tabla de hechos)
```

Si en el futuro agregas tablas de dimensiones separadas (Agentes, Procesos, Equipos),
el modelo crecería a un esquema estrella completo:

```
dim_Agent ──────────────────────────┐
dim_Team  ──────────────────────────┤
dim_Process ─────────────────────── ▼
CalendarTable ──────────────── [ fact_evaluations ]
dim_Supervisor ─────────────────────┘
```

---

## Página 1 — EXECUTIVE OVERVIEW

### Diseño de la página
- Tamaño de página: **16:9** (1280×720 px)
- Fondo: Blanco o gris muy claro (`#f8f9fa`)
- Fuente: Segoe UI

### Título de página
- Insertar **Text Box** en la parte superior.
- Texto: `QA PERFORMANCE DASHBOARD`
- Fuente: Segoe UI Bold, 24pt, color `#2c3e50`
- Subtítulo: `Quality Assurance Analytics — 2026`

### KPI Cards (fila superior)
Insertar 5 **Card** visuals en una fila horizontal:

| Card | Medida | Formato | Color condicional |
|------|--------|---------|-------------------|
| Total Evaluations | `[KPI_Total Evaluations]` | `#,##0` | Ninguno |
| Avg QA Score | `[AVG_QA Score]` | `0.00` | `[COLOR_QA Score]` |
| Pass Rate | `[RATE_Pass Rate %]` | `0.00"%"` | `[COLOR_Pass Rate]` |
| Critical Error Rate | `[RATE_Critical Error Rate %]` | `0.00"%"` | `[COLOR_Critical Error Rate]` |
| Avg CSAT | `[AVG_CSAT]` | `0.00` | `[COLOR_CSAT]` |

**Configurar formato condicional en cada Card:**
- Card visual → Format → Callout value → Background color → Field value → seleccionar la medida `[COLOR_...]` correspondiente.

### Visuales principales

**QA Score Trend (Línea)**
- Visual: **Line Chart**
- X-Axis: `CalendarTable[Month Name]` (ordenar por Month Number)
- Y-Axis: `[AVG_QA Score]`
- Agregar línea de referencia constante: 85 (Analytics pane → Constant Line)
- Color línea: `#3498db`

**QA Score by Team (Barras horizontales)**
- Visual: **Bar Chart** (horizontal)
- Y-Axis: `qa_clean[Team]`
- X-Axis: `[AVG_QA Score]`
- Sort: Descending by Avg QA Score
- Agregar línea de referencia: 85
- Formato condicional de barras: usar `[COLOR_QA Score]`

**Critical Errors by Process (Barras verticales)**
- Visual: **Column Chart**
- X-Axis: `qa_clean[Process]`
- Y-Axis: `[RATE_Critical Error Rate %]`
- Agregar línea de referencia: 2 (target)
- Color barras: condicional por `[COLOR_Critical Error Rate]`

**Top/Bottom Agent Performance (Tabla)**
- Visual: **Table**
- Columnas: Agent, Team, Evaluations, Avg QA Score, Pass Rate, CSAT
- Aplicar formato condicional en QA Score: color de fondo basado en `[COLOR_QA Score]`

### Slicers (filtros)
Posición: panel lateral derecho o fila superior bajo el título.

| Slicer | Campo | Estilo |
|--------|-------|--------|
| Date | `CalendarTable[Date]` | Date range picker |
| Team | `qa_clean[Team]` | Lista vertical |
| Supervisor | `qa_clean[Supervisor]` | Dropdown |
| Process | `qa_clean[Process]` | Dropdown |

---

## Página 2 — QUALITY ANALYSIS

### Visuales

**QA Score by Team y Process (doble column chart)**
- Usar dos Column Charts lado a lado.
- Izquierda: X = Team, Y = `[AVG_QA Score]`
- Derecha: X = Process, Y = `[AVG_QA Score]`

**Critical Error Rate by Process**
- Visual: **Bar Chart** horizontal
- Ordenar descendente por Critical Error Rate
- Color condicional: verde si < 2%, rojo si >= 2%

**Error Distribution**
- Visual: **Clustered Bar Chart** o **Donut Chart**
- Campo: `qa_clean[QA_Category]`
- Valores: `[KPI_Total Evaluations]`
- Colores manuales:
  - Excellent: `#2ecc71`
  - Good: `#3498db`
  - Meets Target: `#f39c12`
  - Below Target: `#e74c3c`

**CSAT Trend**
- Visual: **Line Chart**
- X: Mes, Y: `[AVG_CSAT]`
- Línea de referencia: 4.2
- Color: `#f39c12`

**Resolution Time Trend**
- Visual: **Line Chart**
- X: Mes, Y: `[AVG_Resolution Time (Min)]`
- Sin línea de target fija (se analiza tendencia)
- Color: `#9b59b6`

**QA Category Distribution**
- Visual: **Donut Chart**
- Leyenda: `qa_clean[QA_Category]`
- Valores: `[KPI_Total Evaluations]`

---

## Página 3 — AGENT PERFORMANCE

### Tabla principal de agentes

**Crear Matrix o Table visual** con estas columnas:

| Campo | Medida/Columna | Formato |
|-------|----------------|---------|
| Agent | `qa_clean[Agent]` | Texto |
| Team | `qa_clean[Team]` | Texto |
| Supervisor | `qa_clean[Supervisor]` | Texto |
| Evaluations | `[KPI_Total Evaluations]` | `#,##0` |
| QA Score | `[AVG_QA Score]` | `0.00` |
| Pass Rate | `[RATE_Pass Rate %]` | `0.00"%"` |
| CSAT | `[AVG_CSAT]` | `0.00` |
| Errors | `[AVG_Errors per Evaluation]` | `0.00` |
| Critical Errors | `[CNT_Critical Errors]` | `#,##0` |
| Resolution Time | `[AVG_Resolution Time (Min)]` | `0.0` |

### Conditional Formatting en la tabla

Para **QA Score**:
- Format → Conditional formatting → Background color
- Rules:
  - Value >= 95 → `#2ecc71` (verde)
  - Value >= 85 AND < 95 → `#f39c12` (amarillo)
  - Value < 85 → `#e74c3c` (rojo)

Para **Critical Errors**:
- Rules:
  - Value = 0 → `#2ecc71`
  - Value > 0 → `#e74c3c`

### Filtros de Top / Bottom agents

1. Agregar un **Slicer** de `qa_clean[Agent]`.
2. Agregar un **Top N filter** en el visual de tabla:
   - Visual level filter → Agent → Top N → Top 10 → by `[AVG_QA Score]`
3. Duplicar el visual y cambiar a Bottom 10.

### Ranking de agentes

Agregar columna calculada en Power Query o DAX:

```dax
[Rank QA Score] =
RANKX(
    ALL( qa_clean[Agent] ),
    [AVG_QA Score],
    ,
    DESC,
    Dense
)
```

> **Nota:** Este ranking incluye todos los agentes. Para un ranking correcto
> que excluya agentes con pocas evaluaciones, filtra primero por evaluaciones >= 30
> usando un slicer o filtro de página.

---

## Buenas prácticas de diseño visual

### Jerarquía visual
1. **Título de página** — más grande, parte superior
2. **KPI Cards** — primera fila, números grandes
3. **Gráficos principales** — cuerpo central, tamaño medio
4. **Tablas de detalle** — parte inferior, tamaño menor

### Paleta de colores
```
Verde   #2ecc71  →  On Target / Positivo
Amarillo #f39c12 →  Atención / Cerca del límite
Rojo    #e74c3c  →  Below Target / Riesgo
Azul    #3498db  →  Referencia / Neutral
Gris    #95a5a6  →  Fondos / Labels secundarios
Oscuro  #2c3e50  →  Títulos / Texto principal
```

### Evitar
- ❌ Gráficos 3D (distorsionan la perspectiva)
- ❌ Más de 8 visuales por página (sobrecarga cognitiva)
- ❌ Colores sin significado consistente
- ❌ Decimales excesivos (2 decimales máximo)
- ❌ Títulos genéricos como "Chart 1" o "Visual"

### Aplicar
- ✅ Alineación en grilla (usar guías de alineación)
- ✅ Tamaños de fuente consistentes (8–14pt)
- ✅ Espacio en blanco entre visuales
- ✅ Subtítulos descriptivos en cada visual
- ✅ Leyenda solo cuando hay múltiples series

---

## Publicación del dashboard

1. **Power BI Desktop** → **Publish** → selecciona tu workspace.
2. En **Power BI Service** → Configura el **Scheduled Refresh** si conectas a una fuente dinámica.
3. Para compartir: clic en **Share** → ingresa emails o crea un link.
4. Para embed en SharePoint/Teams: **File → Embed report → SharePoint Online**.


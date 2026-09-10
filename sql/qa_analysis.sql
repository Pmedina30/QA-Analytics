-- ============================================================
-- QA ANALYTICS — SQL PORTFOLIO
-- Database: qa_evaluations.db (SQLite)
-- Author: Pedro Medina | Data Analyst Portfolio
-- Date: 2026
-- ============================================================
-- Este archivo contiene 15+ queries SQL que demuestran:
--   * Agregaciones y GROUP BY
--   * CTEs (Common Table Expressions)
--   * Window Functions (RANK, ROW_NUMBER, LAG, LEAD, AVG OVER)
--   * Subqueries correlacionados
--   * CASE WHEN para lógica condicional
--   * JOINs (self-join simulado)
--   * Filtros complejos y HAVING
-- ============================================================


-- ─────────────────────────────────────────────────────────────
-- QUERY 01: KPI Overview — Resumen ejecutivo global
-- Propósito: Vista rápida de todos los KPIs en una sola query
-- Técnica: Agregaciones múltiples, CAST, ROUND
-- ─────────────────────────────────────────────────────────────
SELECT
    COUNT(*)                                                        AS Total_Evaluations,
    ROUND(AVG(Evaluation_Score), 2)                                 AS Avg_QA_Score,
    ROUND(100.0 * SUM(CASE WHEN Status = 'Pass' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                            AS Pass_Rate_Pct,
    ROUND(100.0 * SUM(CASE WHEN Status = 'Fail' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                            AS Fail_Rate_Pct,
    ROUND(100.0 * SUM(CASE WHEN Critical_Error = 'Yes' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                            AS Critical_Error_Rate_Pct,
    ROUND(AVG(Customer_Satisfaction), 2)                            AS Avg_CSAT,
    ROUND(AVG(Resolution_Time_Min), 2)                              AS Avg_Resolution_Time_Min,
    ROUND(AVG(Errors), 2)                                           AS Avg_Errors_Per_Eval,
    MIN(Date)                                                       AS Period_Start,
    MAX(Date)                                                       AS Period_End
FROM evaluations
WHERE data_valid = 1;


-- ─────────────────────────────────────────────────────────────
-- QUERY 02: Team Performance Dashboard
-- Propósito: KPIs por equipo para identificar el mejor/peor
-- Técnica: GROUP BY, múltiples agregaciones, CASE WHEN, ORDER BY
-- ─────────────────────────────────────────────────────────────
SELECT
    Team,
    COUNT(*)                                                        AS Evaluations,
    ROUND(AVG(Evaluation_Score), 2)                                 AS Avg_QA_Score,
    ROUND(100.0 * SUM(CASE WHEN Status = 'Pass' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                            AS Pass_Rate_Pct,
    ROUND(100.0 * SUM(CASE WHEN Critical_Error = 'Yes' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                            AS Critical_Error_Rate_Pct,
    ROUND(AVG(Customer_Satisfaction), 2)                            AS Avg_CSAT,
    ROUND(AVG(Resolution_Time_Min), 2)                              AS Avg_Resolution_Min,
    CASE
        WHEN AVG(Evaluation_Score) >= 90 THEN 'Excellent'
        WHEN AVG(Evaluation_Score) >= 85 THEN 'On Target'
        WHEN AVG(Evaluation_Score) >= 80 THEN 'Needs Improvement'
        ELSE 'Critical'
    END                                                             AS Performance_Level
FROM evaluations
WHERE data_valid = 1
GROUP BY Team
ORDER BY Avg_QA_Score DESC;


-- ─────────────────────────────────────────────────────────────
-- QUERY 03: Process Risk Analysis
-- Propósito: Identificar procesos con mayor riesgo operacional
-- Técnica: HAVING para filtrar grupos, múltiples métricas de riesgo
-- ─────────────────────────────────────────────────────────────
SELECT
    Process,
    COUNT(*)                                                        AS Total_Evaluations,
    ROUND(AVG(Evaluation_Score), 2)                                 AS Avg_QA_Score,
    SUM(Errors)                                                     AS Total_Errors,
    ROUND(AVG(Errors), 2)                                           AS Avg_Errors,
    SUM(CASE WHEN Critical_Error = 'Yes' THEN 1 ELSE 0 END)         AS Total_Critical_Errors,
    ROUND(100.0 * SUM(CASE WHEN Critical_Error = 'Yes' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                            AS Critical_Error_Rate_Pct,
    ROUND(AVG(Customer_Satisfaction), 2)                            AS Avg_CSAT,
    ROUND(AVG(Resolution_Time_Min), 2)                              AS Avg_Resolution_Min,
    CASE
        WHEN 100.0 * SUM(CASE WHEN Critical_Error = 'Yes' THEN 1 ELSE 0 END)
             / COUNT(*) >= 3  THEN 'HIGH RISK'
        WHEN 100.0 * SUM(CASE WHEN Critical_Error = 'Yes' THEN 1 ELSE 0 END)
             / COUNT(*) >= 2  THEN 'MEDIUM RISK'
        ELSE 'LOW RISK'
    END                                                             AS Risk_Level
FROM evaluations
WHERE data_valid = 1
GROUP BY Process
ORDER BY Critical_Error_Rate_Pct DESC;


-- ─────────────────────────────────────────────────────────────
-- QUERY 04: Agent Ranking with Window Functions
-- Propósito: Rankear agentes por QA Score usando RANK()
-- Técnica: CTE + Window Functions (RANK, AVG OVER, COUNT OVER)
-- ─────────────────────────────────────────────────────────────
WITH AgentStats AS (
    SELECT
        Agent,
        Team,
        Supervisor,
        COUNT(*)                                                    AS Evaluations,
        ROUND(AVG(Evaluation_Score), 2)                             AS Avg_QA_Score,
        ROUND(100.0 * SUM(CASE WHEN Status = 'Pass' THEN 1 ELSE 0 END)
              / COUNT(*), 2)                                        AS Pass_Rate,
        ROUND(AVG(Customer_Satisfaction), 2)                        AS Avg_CSAT,
        ROUND(100.0 * SUM(CASE WHEN Critical_Error = 'Yes' THEN 1 ELSE 0 END)
              / COUNT(*), 2)                                        AS Critical_Error_Rate
    FROM evaluations
    WHERE data_valid = 1
    GROUP BY Agent, Team, Supervisor
    HAVING Evaluations >= 30   -- Mínimo estadístico para ranking confiable
)
SELECT
    Agent,
    Team,
    Supervisor,
    Evaluations,
    Avg_QA_Score,
    Pass_Rate,
    Avg_CSAT,
    Critical_Error_Rate,
    RANK() OVER (ORDER BY Avg_QA_Score DESC)                        AS QA_Rank,
    RANK() OVER (PARTITION BY Team ORDER BY Avg_QA_Score DESC)      AS Team_Rank,
    ROUND(AVG(Avg_QA_Score) OVER (), 2)                             AS Global_Avg_QA,
    ROUND(Avg_QA_Score - AVG(Avg_QA_Score) OVER (), 2)             AS Deviation_From_Global_Avg,
    CASE
        WHEN Avg_QA_Score >= 95 THEN 'Excellent'
        WHEN Avg_QA_Score >= 90 THEN 'Good'
        WHEN Avg_QA_Score >= 85 THEN 'Meets Target'
        ELSE 'Below Target'
    END                                                             AS QA_Category
FROM AgentStats
ORDER BY Avg_QA_Score DESC;


-- ─────────────────────────────────────────────────────────────
-- QUERY 05: Top 10 & Bottom 10 Agents
-- Propósito: Extraer extremos para coaching y reconocimiento
-- Técnica: CTE + UNION ALL + ROW_NUMBER + LIMIT
-- ─────────────────────────────────────────────────────────────
WITH AgentAvg AS (
    SELECT
        Agent,
        Team,
        COUNT(*)                        AS Evaluations,
        ROUND(AVG(Evaluation_Score), 2) AS Avg_QA_Score,
        ROUND(AVG(Customer_Satisfaction), 2) AS Avg_CSAT
    FROM evaluations
    WHERE data_valid = 1
    GROUP BY Agent, Team
    HAVING Evaluations >= 30
),
Ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (ORDER BY Avg_QA_Score DESC) AS Top_Rank,
        ROW_NUMBER() OVER (ORDER BY Avg_QA_Score ASC)  AS Bottom_Rank
    FROM AgentAvg
)
SELECT Agent, Team, Evaluations, Avg_QA_Score, Avg_CSAT,
       'TOP 10' AS Category, Top_Rank AS Rank
FROM Ranked WHERE Top_Rank <= 10

UNION ALL

SELECT Agent, Team, Evaluations, Avg_QA_Score, Avg_CSAT,
       'BOTTOM 10' AS Category, Bottom_Rank AS Rank
FROM Ranked WHERE Bottom_Rank <= 10
ORDER BY Category, Rank;


-- ─────────────────────────────────────────────────────────────
-- QUERY 06: Monthly Trend with MoM Change (LAG Window Function)
-- Propósito: Analizar tendencia mensual y cambio mes a mes
-- Técnica: strftime() para fechas, LAG() para MoM comparison
-- ─────────────────────────────────────────────────────────────
WITH MonthlyKPIs AS (
    SELECT
        strftime('%Y', Date)                                        AS Year,
        strftime('%m', Date)                                        AS Month_Num,
        CASE strftime('%m', Date)
            WHEN '01' THEN 'January'   WHEN '02' THEN 'February'
            WHEN '03' THEN 'March'     WHEN '04' THEN 'April'
            WHEN '05' THEN 'May'       WHEN '06' THEN 'June'
            WHEN '07' THEN 'July'      WHEN '08' THEN 'August'
            WHEN '09' THEN 'September' WHEN '10' THEN 'October'
            WHEN '11' THEN 'November'  WHEN '12' THEN 'December'
        END                                                         AS Month_Name,
        COUNT(*)                                                    AS Evaluations,
        ROUND(AVG(Evaluation_Score), 2)                             AS Avg_QA_Score,
        ROUND(100.0 * SUM(CASE WHEN Status = 'Pass' THEN 1 ELSE 0 END)
              / COUNT(*), 2)                                        AS Pass_Rate,
        ROUND(100.0 * SUM(CASE WHEN Critical_Error = 'Yes' THEN 1 ELSE 0 END)
              / COUNT(*), 2)                                        AS Critical_Error_Rate,
        ROUND(AVG(Customer_Satisfaction), 2)                        AS Avg_CSAT,
        ROUND(AVG(Resolution_Time_Min), 2)                          AS Avg_Resolution_Min
    FROM evaluations
    WHERE data_valid = 1
    GROUP BY Year, Month_Num
)
SELECT
    Year, Month_Name, Evaluations,
    Avg_QA_Score,
    LAG(Avg_QA_Score) OVER (ORDER BY Year, Month_Num)              AS Prev_Month_QA,
    ROUND(Avg_QA_Score -
          LAG(Avg_QA_Score) OVER (ORDER BY Year, Month_Num), 2)    AS QA_MoM_Change,
    Pass_Rate,
    Critical_Error_Rate,
    Avg_CSAT,
    LAG(Avg_CSAT) OVER (ORDER BY Year, Month_Num)                  AS Prev_Month_CSAT,
    ROUND(Avg_CSAT -
          LAG(Avg_CSAT) OVER (ORDER BY Year, Month_Num), 2)        AS CSAT_MoM_Change,
    Avg_Resolution_Min
FROM MonthlyKPIs
ORDER BY Year, Month_Num;


-- ─────────────────────────────────────────────────────────────
-- QUERY 07: Agents Consistently Below Target
-- Propósito: Detectar agentes que sistemáticamente fallan
-- Técnica: CTE anidado + subquery + HAVING
-- ─────────────────────────────────────────────────────────────
WITH AgentMonthly AS (
    SELECT
        Agent,
        Team,
        strftime('%Y-%m', Date)         AS Month,
        ROUND(AVG(Evaluation_Score), 2) AS Monthly_QA_Score,
        COUNT(*)                        AS Monthly_Evals,
        CASE WHEN AVG(Evaluation_Score) < 85 THEN 1 ELSE 0 END AS Below_Target_Month
    FROM evaluations
    WHERE data_valid = 1
    GROUP BY Agent, Team, Month
),
AgentConsistency AS (
    SELECT
        Agent,
        Team,
        COUNT(Month)                    AS Months_Active,
        SUM(Below_Target_Month)         AS Months_Below_Target,
        ROUND(AVG(Monthly_QA_Score), 2) AS Overall_Avg_QA,
        SUM(Monthly_Evals)              AS Total_Evaluations
    FROM AgentMonthly
    GROUP BY Agent, Team
    HAVING Total_Evaluations >= 30
)
SELECT
    Agent,
    Team,
    Months_Active,
    Months_Below_Target,
    ROUND(100.0 * Months_Below_Target / Months_Active, 1) AS Pct_Months_Below_Target,
    Overall_Avg_QA,
    Total_Evaluations
FROM AgentConsistency
WHERE Months_Below_Target >= 2    -- Al menos 2 meses bajo el target
ORDER BY Months_Below_Target DESC, Overall_Avg_QA ASC;


-- ─────────────────────────────────────────────────────────────
-- QUERY 08: Supervisor Accountability Report
-- Propósito: KPIs de los equipos de cada supervisor
-- Técnica: GROUP BY, condicionales, conteo de agentes únicos
-- ─────────────────────────────────────────────────────────────
SELECT
    Supervisor,
    COUNT(DISTINCT Agent)                                           AS Agents_Under_Supervision,
    COUNT(*)                                                        AS Total_Evaluations,
    ROUND(AVG(Evaluation_Score), 2)                                 AS Avg_QA_Score,
    ROUND(100.0 * SUM(CASE WHEN Status = 'Pass' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                            AS Pass_Rate,
    ROUND(100.0 * SUM(CASE WHEN Critical_Error = 'Yes' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                            AS Critical_Error_Rate,
    ROUND(AVG(Customer_Satisfaction), 2)                            AS Avg_CSAT,
    SUM(CASE WHEN Evaluation_Score < 85 THEN 1 ELSE 0 END)          AS Evals_Below_Target,
    ROUND(100.0 * SUM(CASE WHEN Evaluation_Score < 85 THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                            AS Pct_Below_Target
FROM evaluations
WHERE data_valid = 1
  AND Supervisor != 'Unknown'
GROUP BY Supervisor
ORDER BY Avg_QA_Score DESC;


-- ─────────────────────────────────────────────────────────────
-- QUERY 09: QA Score Distribution (Histogram buckets)
-- Propósito: Ver cómo se distribuyen los scores (no solo el promedio)
-- Técnica: CASE WHEN para bucketing + COUNT + porcentaje
-- ─────────────────────────────────────────────────────────────
SELECT
    CASE
        WHEN Evaluation_Score >= 95 THEN '95-100 (Excellent)'
        WHEN Evaluation_Score >= 90 THEN '90-94  (Good)'
        WHEN Evaluation_Score >= 85 THEN '85-89  (Meets Target)'
        WHEN Evaluation_Score >= 80 THEN '80-84  (Near Target)'
        WHEN Evaluation_Score >= 75 THEN '75-79  (Needs Improvement)'
        ELSE                              '< 75   (Critical)'
    END                                                             AS Score_Bucket,
    COUNT(*)                                                        AS Evaluations,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)             AS Percentage
FROM evaluations
WHERE data_valid = 1
GROUP BY Score_Bucket
ORDER BY MIN(Evaluation_Score) DESC;


-- ─────────────────────────────────────────────────────────────
-- QUERY 10: Critical Errors Deep Dive
-- Propósito: Análisis detallado de evaluaciones con error crítico
-- Técnica: Subquery en WHERE, GROUP BY múltiple
-- ─────────────────────────────────────────────────────────────
SELECT
    Team,
    Process,
    COUNT(*)                            AS Critical_Error_Evaluations,
    ROUND(AVG(Evaluation_Score), 2)     AS Avg_QA_Score_On_Critical,
    ROUND(AVG(Customer_Satisfaction), 2) AS Avg_CSAT_On_Critical,
    ROUND(AVG(Resolution_Time_Min), 2)  AS Avg_Resolution_On_Critical,
    ROUND(AVG(Errors), 2)               AS Avg_Errors_On_Critical
FROM evaluations
WHERE data_valid = 1
  AND Critical_Error = 'Yes'
GROUP BY Team, Process
ORDER BY Critical_Error_Evaluations DESC;


-- ─────────────────────────────────────────────────────────────
-- QUERY 11: Day-of-Week Performance Pattern
-- Propósito: Detectar si hay días con peor desempeño
-- Técnica: strftime() para extraer día de la semana
-- ─────────────────────────────────────────────────────────────
SELECT
    CASE strftime('%w', Date)
        WHEN '0' THEN '1-Sunday'    WHEN '1' THEN '2-Monday'
        WHEN '2' THEN '3-Tuesday'   WHEN '3' THEN '4-Wednesday'
        WHEN '4' THEN '5-Thursday'  WHEN '5' THEN '6-Friday'
        WHEN '6' THEN '7-Saturday'
    END                                                             AS Day_of_Week,
    COUNT(*)                                                        AS Evaluations,
    ROUND(AVG(Evaluation_Score), 2)                                 AS Avg_QA_Score,
    ROUND(100.0 * SUM(CASE WHEN Critical_Error = 'Yes' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                            AS Critical_Error_Rate,
    ROUND(AVG(Customer_Satisfaction), 2)                            AS Avg_CSAT
FROM evaluations
WHERE data_valid = 1
GROUP BY strftime('%w', Date)
ORDER BY strftime('%w', Date);


-- ─────────────────────────────────────────────────────────────
-- QUERY 12: Resolution Time Percentiles
-- Propósito: Entender la distribución real del tiempo de resolución
-- Técnica: NTILE() window function para cuartiles
-- ─────────────────────────────────────────────────────────────
WITH Percentiles AS (
    SELECT
        Resolution_Time_Min,
        NTILE(4) OVER (ORDER BY Resolution_Time_Min)   AS Quartile,
        NTILE(10) OVER (ORDER BY Resolution_Time_Min)  AS Decile
    FROM evaluations
    WHERE data_valid = 1
)
SELECT
    Quartile,
    COUNT(*)                                AS Evaluations,
    ROUND(MIN(Resolution_Time_Min), 1)      AS Min_Min,
    ROUND(AVG(Resolution_Time_Min), 1)      AS Avg_Min,
    ROUND(MAX(Resolution_Time_Min), 1)      AS Max_Min
FROM Percentiles
GROUP BY Quartile
ORDER BY Quartile;


-- ─────────────────────────────────────────────────────────────
-- QUERY 13: CSAT vs QA Score Correlation Bands
-- Propósito: Analizar si agentes con mayor QA Score tienen mejor CSAT
-- Técnica: CTE + CASE bucketing + comparación de grupos
-- ─────────────────────────────────────────────────────────────
WITH QABands AS (
    SELECT
        CASE
            WHEN Evaluation_Score >= 95 THEN 'A: 95-100'
            WHEN Evaluation_Score >= 90 THEN 'B: 90-94'
            WHEN Evaluation_Score >= 85 THEN 'C: 85-89'
            WHEN Evaluation_Score >= 80 THEN 'D: 80-84'
            ELSE                              'E: <80'
        END                                         AS QA_Band,
        Customer_Satisfaction,
        Resolution_Time_Min
    FROM evaluations
    WHERE data_valid = 1
)
SELECT
    QA_Band,
    COUNT(*)                                        AS Evaluations,
    ROUND(AVG(Customer_Satisfaction), 3)            AS Avg_CSAT,
    ROUND(MIN(Customer_Satisfaction), 1)            AS Min_CSAT,
    ROUND(MAX(Customer_Satisfaction), 1)            AS Max_CSAT,
    ROUND(AVG(Resolution_Time_Min), 2)              AS Avg_Resolution_Min
FROM QABands
GROUP BY QA_Band
ORDER BY QA_Band;


-- ─────────────────────────────────────────────────────────────
-- QUERY 14: Running Total & Cumulative Pass Rate
-- Propósito: Mostrar acumulados progresivos por mes
-- Técnica: SUM OVER (ORDER BY) para running totals
-- ─────────────────────────────────────────────────────────────
WITH Monthly AS (
    SELECT
        strftime('%Y-%m', Date)         AS YearMonth,
        COUNT(*)                        AS Monthly_Evals,
        SUM(CASE WHEN Status='Pass' THEN 1 ELSE 0 END) AS Monthly_Pass
    FROM evaluations
    WHERE data_valid = 1
    GROUP BY YearMonth
)
SELECT
    YearMonth,
    Monthly_Evals,
    Monthly_Pass,
    SUM(Monthly_Evals) OVER (ORDER BY YearMonth)  AS Cumulative_Evaluations,
    SUM(Monthly_Pass)  OVER (ORDER BY YearMonth)  AS Cumulative_Pass,
    ROUND(100.0 * SUM(Monthly_Pass) OVER (ORDER BY YearMonth)
               / SUM(Monthly_Evals) OVER (ORDER BY YearMonth), 2) AS Cumulative_Pass_Rate_Pct
FROM Monthly
ORDER BY YearMonth;


-- ─────────────────────────────────────────────────────────────
-- QUERY 15: Agent Improvement Detection (LEAD/LAG)
-- Propósito: Detectar agentes que mejoran o empeoran mes a mes
-- Técnica: CTE + LAG para comparar períodos consecutivos del agente
-- ─────────────────────────────────────────────────────────────
WITH AgentMonthly AS (
    SELECT
        Agent,
        Team,
        strftime('%Y-%m', Date)         AS Period,
        COUNT(*)                        AS Evals,
        ROUND(AVG(Evaluation_Score), 2) AS Avg_QA
    FROM evaluations
    WHERE data_valid = 1
    GROUP BY Agent, Team, Period
    HAVING Evals >= 5
),
WithLag AS (
    SELECT
        Agent, Team, Period, Evals, Avg_QA,
        LAG(Avg_QA) OVER (PARTITION BY Agent ORDER BY Period) AS Prev_QA,
        LEAD(Avg_QA) OVER (PARTITION BY Agent ORDER BY Period) AS Next_QA
    FROM AgentMonthly
)
SELECT
    Agent,
    Team,
    Period,
    Avg_QA,
    Prev_QA,
    ROUND(Avg_QA - Prev_QA, 2)                     AS MoM_Change,
    CASE
        WHEN Prev_QA IS NULL        THEN 'First Period'
        WHEN Avg_QA - Prev_QA > 2  THEN 'Improving'
        WHEN Avg_QA - Prev_QA < -2 THEN 'Declining'
        ELSE 'Stable'
    END                                             AS Trend
FROM WithLag
WHERE Prev_QA IS NOT NULL
ORDER BY Agent, Period;

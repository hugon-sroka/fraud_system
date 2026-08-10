-- =============================================================
-- MARTS: rpt_risk_tier_summary
-- Cel: Pre-agregowana tabela dla wykresów kołowych (Pie/Donut).
--      Tylko 4 wiersze — błyskawiczne zapytania w Looker Studio.
-- =============================================================

WITH daily AS (
    SELECT *
    FROM {{ ref('rpt_daily_fraud_summary') }}
)

SELECT
    'CRITICAL' AS risk_tier,
    SUM(critical_risk_count) AS transaction_count,
    1 AS sort_order
FROM daily

UNION ALL

SELECT
    'HIGH' AS risk_tier,
    SUM(high_risk_count) AS transaction_count,
    2 AS sort_order
FROM daily

UNION ALL

SELECT
    'MEDIUM' AS risk_tier,
    SUM(medium_risk_count) AS transaction_count,
    3 AS sort_order
FROM daily

UNION ALL

SELECT
    'LOW' AS risk_tier,
    SUM(low_risk_count) AS transaction_count,
    4 AS sort_order
FROM daily

ORDER BY sort_order

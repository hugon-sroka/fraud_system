-- =============================================================
-- MARTS: rpt_hourly_velocity_heatmaps
-- Cel: Widok dla BI generujący dane do map ciepła (heatmap)
--      według dnia tygodnia i godziny transakcji.
-- =============================================================

WITH fct AS (
    SELECT *
    FROM {{ ref('fct_transactions') }}
)

SELECT
    EXTRACT(DAYOFWEEK FROM transaction_ts) AS day_of_week,
    FORMAT_TIMESTAMP('%A', transaction_ts) AS day_name,
    EXTRACT(HOUR FROM transaction_ts) AS hour_of_day,
    COUNT(*) AS total_transactions,
    ROUND(SUM(amount_usd), 2) AS total_volume_usd,
    COUNTIF(requires_agent_investigation) AS flagged_alerts_count,
    ROUND(AVG(risk_score), 2) AS avg_risk_score
FROM fct
GROUP BY 1, 2, 3
ORDER BY day_of_week ASC, hour_of_day ASC

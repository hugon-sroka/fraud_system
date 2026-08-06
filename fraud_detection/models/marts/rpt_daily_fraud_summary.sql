-- =============================================================
-- MARTS: rpt_daily_fraud_summary
-- Cel: Widok raportowy dla BI (dzienne podsumowanie wolumenu,
--      liczby alertów i dystrybucji poziomów ryzyka).
-- =============================================================

WITH fct AS (
    SELECT *
    FROM {{ ref('fct_transactions') }}
)

SELECT
    DATE(transaction_ts) AS transaction_date,
    COUNT(*) AS total_transactions,
    ROUND(SUM(amount_usd), 2) AS total_volume_usd,
    ROUND(SUM(IF(status = 'accepted', amount_usd, 0)), 2) AS accepted_volume_usd,
    ROUND(SUM(IF(status = 'rejected', amount_usd, 0)), 2) AS rejected_volume_usd,
    
    COUNTIF(requires_agent_investigation) AS flagged_alerts_count,
    ROUND(SUM(IF(requires_agent_investigation, amount_usd, 0)), 2) AS flagged_volume_usd,
    ROUND(AVG(risk_score), 2) AS avg_risk_score,
    
    COUNTIF(risk_tier = 'CRITICAL') AS critical_risk_count,
    COUNTIF(risk_tier = 'HIGH') AS high_risk_count,
    COUNTIF(risk_tier = 'MEDIUM') AS medium_risk_count,
    COUNTIF(risk_tier = 'LOW') AS low_risk_count

FROM fct
GROUP BY DATE(transaction_ts)
ORDER BY transaction_date DESC

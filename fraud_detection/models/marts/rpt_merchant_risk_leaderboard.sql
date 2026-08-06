-- =============================================================
-- MARTS: rpt_merchant_risk_leaderboard
-- Cel: Widok raportowy dla BI przedstawiający ranking merchantów
--      pod kątem poziomu ryzyka i wskaźnika nadużyć.
-- =============================================================

WITH fct AS (
    SELECT *
    FROM {{ ref('fct_transactions') }}
),

merchant_agg AS (
    SELECT
        merchant_id,
        MAX(merchant_name) AS merchant_name,
        MAX(merchant_country) AS merchant_country,
        COUNT(*) AS total_transactions,
        ROUND(SUM(amount_usd), 2) AS total_volume_usd,
        COUNTIF(requires_agent_investigation) AS flagged_transactions_count,
        ROUND(SUM(IF(requires_agent_investigation, amount_usd, 0)), 2) AS flagged_volume_usd,
        ROUND(SAFE_DIVIDE(COUNTIF(requires_agent_investigation), COUNT(*)) * 100, 2) AS fraud_rate_pct,
        ROUND(AVG(risk_score), 2) AS avg_merchant_risk_score
    FROM fct
    GROUP BY merchant_id
)

SELECT
    *,
    CASE
        WHEN fraud_rate_pct >= 25.0 OR avg_merchant_risk_score >= 50 THEN 'CRITICAL_RISK'
        WHEN fraud_rate_pct >= 10.0 OR avg_merchant_risk_score >= 30 THEN 'HIGH_RISK'
        WHEN fraud_rate_pct >= 3.0 THEN 'ELEVATED_RISK'
        ELSE 'LOW_RISK'
    END AS merchant_risk_category
FROM merchant_agg
ORDER BY flagged_volume_usd DESC, fraud_rate_pct DESC

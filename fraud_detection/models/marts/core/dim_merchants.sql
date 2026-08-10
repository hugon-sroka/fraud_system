-- =============================================================
-- MARTS: dim_merchants
-- Cel: Wymiar merchantów zawierający wskaźniki wolumenu i poziom ryzyka.
-- =============================================================

WITH fct AS (
    SELECT *
    FROM {{ ref('fct_transactions') }}
)

SELECT
    merchant_id,
    MAX(merchant_name) AS merchant_name,
    MAX(merchant_country) AS merchant_country,
    COUNT(*) AS total_transactions,
    COUNT(DISTINCT account_id) AS total_unique_customers,
    ROUND(SUM(amount_usd), 2) AS total_volume_usd,
    ROUND(AVG(amount_usd), 2) AS avg_transaction_amount_usd,
    COUNTIF(requires_agent_investigation) AS total_flagged_alerts,
    ROUND(SAFE_DIVIDE(COUNTIF(requires_agent_investigation), COUNT(*)) * 100, 2) AS fraud_flag_rate_pct
FROM fct
GROUP BY merchant_id

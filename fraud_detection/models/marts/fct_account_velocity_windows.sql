-- =============================================================
-- MARTS: fct_account_velocity_windows
-- Cel: Tabela faktów agregująca dzienne maksima aktywności i impulsy
--      velocity per konto (szczytowe okna 10m i 1h).
-- =============================================================

WITH fct AS (
    SELECT *
    FROM {{ ref('fct_transactions') }}
)

SELECT
    DATE(transaction_ts) AS summary_date,
    account_id,
    COUNT(*) AS total_daily_transactions,
    ROUND(SUM(amount_usd), 2) AS total_daily_volume_usd,
    MAX(velocity_10m_count) AS peak_10m_txn_count,
    ROUND(MAX(velocity_1h_amount), 2) AS peak_1h_volume_usd,
    ROUND(MAX(z_score), 2) AS max_z_score,
    COUNTIF(requires_agent_investigation) AS total_alerts_triggered,
    MAX(risk_score) AS max_daily_risk_score
FROM fct
GROUP BY DATE(transaction_ts), account_id

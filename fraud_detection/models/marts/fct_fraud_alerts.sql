-- =============================================================
-- MARTS: fct_fraud_alerts
-- Cel: Kolejka alertów dla Agentic Fraud Analyst Engine.
--      Zawiera tylko transakcje z poziomem ryzyka HIGH i CRITICAL.
-- =============================================================

WITH fct AS (
    SELECT *
    FROM {{ ref('fct_transactions') }}
)

SELECT
    transaction_id,
    account_id,
    card_id,
    merchant_id,
    merchant_name,
    merchant_country,
    payment_type,
    amount_usd,
    transaction_ts,
    velocity_10m_count,
    velocity_1h_count,
    z_score,
    signal_velocity_10m_spike,
    signal_high_zscore,
    signal_structuring,
    signal_card_testing,
    signal_new_merchant_large_amount,
    risk_score,
    risk_tier,
    requires_agent_investigation,
    CURRENT_TIMESTAMP() AS alert_created_at
FROM fct
WHERE requires_agent_investigation = TRUE
ORDER BY risk_score DESC, transaction_ts DESC

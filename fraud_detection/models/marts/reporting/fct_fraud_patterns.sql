-- =============================================================
-- MARTS: fct_fraud_patterns
-- Cel: Tabela analityczna przedstawiająca statystyki incydentów
--      według poszczególnych wektorów ataków (patterns).
-- =============================================================

WITH signals AS (
    SELECT *
    FROM {{ ref('int_fraud_signals') }}
),

unpivoted_patterns AS (
    -- Structuring pattern
    SELECT
        'STRUCTURING' AS pattern_name,
        transaction_id,
        account_id,
        merchant_id,
        amount_usd,
        transaction_ts
    FROM signals
    WHERE signal_structuring

    UNION ALL

    -- Card Testing pattern
    SELECT
        'CARD_TESTING' AS pattern_name,
        transaction_id,
        account_id,
        merchant_id,
        amount_usd,
        transaction_ts
    FROM signals
    WHERE signal_card_testing

    UNION ALL

    -- Velocity Spike pattern
    SELECT
        'VELOCITY_SPIKE' AS pattern_name,
        transaction_id,
        account_id,
        merchant_id,
        amount_usd,
        transaction_ts
    FROM signals
    WHERE signal_velocity_10m_spike

    UNION ALL

    -- High Spend Deviation pattern
    SELECT
        'SPEND_DEVIATION' AS pattern_name,
        transaction_id,
        account_id,
        merchant_id,
        amount_usd,
        transaction_ts
    FROM signals
    WHERE signal_high_zscore
)

SELECT
    pattern_name,
    COUNT(*) AS total_incidents_count,
    COUNT(DISTINCT account_id) AS affected_accounts_count,
    COUNT(DISTINCT merchant_id) AS affected_merchants_count,
    ROUND(SUM(amount_usd), 2) AS total_volume_at_risk_usd,
    ROUND(AVG(amount_usd), 2) AS avg_incident_amount_usd,
    MIN(transaction_ts) AS first_detected_ts,
    MAX(transaction_ts) AS last_detected_ts
FROM unpivoted_patterns
GROUP BY pattern_name

-- =============================================================
-- MARTS: fct_transactions
-- Cel: Główna tabela faktów transakcji zawierająca obliczony
--      łączny Risk Score (0-100) oraz Risk Tier.
-- =============================================================

WITH signals AS (
    SELECT *
    FROM {{ ref('int_fraud_signals') }}
),

risk_scored AS (
    SELECT
        *,

        -- Obliczenie ważonego wskaźnika ryzyka (zabezpieczone próg 100)
        LEAST(
            100,
            (IF(signal_velocity_10m_spike, 35, 0) +
             IF(signal_high_zscore, 25, 0) +
             IF(signal_structuring, 40, 0) +
             IF(signal_card_testing, 30, 0) +
             IF(signal_new_merchant_large_amount, 20, 0))
        ) AS risk_score

    FROM signals
),

risk_tiered AS (
    SELECT
        *,

        CASE
            WHEN risk_score >= 60 THEN 'CRITICAL'
            WHEN risk_score >= 30 THEN 'HIGH'
            WHEN risk_score >= 15 THEN 'MEDIUM'
            ELSE 'LOW'
        END AS risk_tier,

        (risk_score >= 30) AS requires_agent_investigation

    FROM risk_scored
)

SELECT * FROM risk_tiered

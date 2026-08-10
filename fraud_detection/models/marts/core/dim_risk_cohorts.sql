-- =============================================================
-- MARTS: dim_risk_cohorts
-- Cel: Wymiar segmentacji kont klientów (risk cohorting)
--      klasyfikujący użytkowników do odpowiednich grup ryzyka.
-- =============================================================

WITH account_summary AS (
    SELECT
        account_id,
        total_transactions,
        total_spend_usd,
        avg_spend_usd,
        high_risk_transactions,
        max_risk_score_seen,
        first_seen_ts,
        last_seen_ts
    FROM {{ ref('dim_accounts') }}
)

SELECT
    account_id,
    total_transactions,
    total_spend_usd,
    avg_spend_usd,
    high_risk_transactions,
    max_risk_score_seen,
    
    CASE
        WHEN high_risk_transactions >= 2 THEN 'HIGH_RISK_REPEATER'
        WHEN high_risk_transactions = 1 OR max_risk_score_seen >= 40 THEN 'ELEVATED_RISK'
        WHEN total_spend_usd >= 5000.0 AND high_risk_transactions = 0 THEN 'TRUSTED_HIGH_VOLUME'
        ELSE 'STANDARD_CLEAN'
    END AS risk_cohort,

    first_seen_ts,
    last_seen_ts

FROM account_summary

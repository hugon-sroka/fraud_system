-- =============================================================
-- MARTS: dim_accounts
-- Cel: Wymiar kont klienta zawierający profil historyczny i wskaźniki ryzyka.
-- =============================================================

WITH fct AS (
    SELECT *
    FROM {{ ref('fct_transactions') }}
)

SELECT
    account_id,
    COUNT(*) AS total_transactions,
    COUNTIF(status = 'accepted') AS accepted_transactions,
    COUNTIF(status = 'rejected') AS rejected_transactions,
    COUNTIF(requires_agent_investigation) AS high_risk_transactions,
    ROUND(SUM(amount_usd), 2) AS total_spend_usd,
    ROUND(AVG(amount_usd), 2) AS avg_spend_usd,
    MAX(risk_score) AS max_risk_score_seen,
    MIN(transaction_ts) AS first_seen_ts,
    MAX(transaction_ts) AS last_seen_ts
FROM fct
GROUP BY account_id

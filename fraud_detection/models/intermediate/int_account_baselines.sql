-- =============================================================
-- INTERMEDIATE: int_account_baselines
-- Cel: Oblicza statystyki historyczne per konto dla wyznaczania
--      Z-Score (średnia kwota, odchylenie standardowe) oraz
--      bazowe profile zachowań.
-- =============================================================

WITH stg AS (
    SELECT *
    FROM {{ ref('stg_transactions') }}
    WHERE _is_valid = TRUE
),

account_stats AS (
    SELECT
        account_id,
        COUNT(*) AS total_historical_transactions,
        ROUND(AVG(amount_usd), 2) AS avg_transaction_amount,
        -- Zachowaj odchylenie standardowe (minimum 1.0 dla uniknięcia dzielenia przez 0)
        COALESCE(ROUND(STDDEV_SAMP(amount_usd), 2), 10.0) AS stddev_transaction_amount,
        MIN(amount_usd) AS min_transaction_amount,
        MAX(amount_usd) AS max_transaction_amount,
        MIN(transaction_ts) AS first_transaction_ts,
        MAX(transaction_ts) AS last_transaction_ts
    FROM stg
    GROUP BY account_id
)

SELECT * FROM account_stats

-- =============================================================
-- INTERMEDIATE: int_fraud_signals
-- Cel: Łączy dane stg, velocity oraz baselines w celu wyznaczenia
--      poszczególnych flag sygnałów fraudowych.
-- =============================================================

WITH stg AS (
    SELECT *
    FROM {{ ref('stg_transactions') }}
    WHERE _is_valid = TRUE
),

velocity AS (
    SELECT *
    FROM {{ ref('int_transaction_velocity') }}
),

baselines AS (
    SELECT *
    FROM {{ ref('int_account_baselines') }}
),

merchant_visits AS (
    SELECT
        transaction_id,
        (ROW_NUMBER() OVER (
            PARTITION BY account_id, merchant_id
            ORDER BY transaction_ts, transaction_id
        ) = 1) AS is_first_merchant_visit
    FROM stg
),

combined AS (
    SELECT
        s.transaction_id,
        s.account_id,
        s.card_id,
        s.merchant_id,
        s.merchant_name,
        s.merchant_country,
        s.payment_type,
        s.amount_usd,
        s.status,
        s.transaction_ts,

        -- Velocity metrics
        v.velocity_10m_count,
        v.velocity_10m_amount,
        v.velocity_1h_count,
        v.velocity_1h_amount,
        v.velocity_24h_count,
        v.velocity_24h_amount,
        v.structuring_1h_count,

        -- Baseline metrics
        b.avg_transaction_amount,
        b.stddev_transaction_amount,

        -- First visit flag
        m.is_first_merchant_visit,

        -- Z-Score calculation
        ROUND(
            SAFE_DIVIDE(
                (s.amount_usd - b.avg_transaction_amount),
                IF(b.stddev_transaction_amount = 0, 10.0, b.stddev_transaction_amount)
            ), 2
        ) AS z_score

    FROM stg s
    LEFT JOIN velocity v ON s.transaction_id = v.transaction_id
    LEFT JOIN baselines b ON s.account_id = b.account_id
    LEFT JOIN merchant_visits m ON s.transaction_id = m.transaction_id
),

signals_evaluated AS (
    SELECT
        *,

        -- Sygnał 1: High Velocity (>= 5 transakcji w 10m)
        (velocity_10m_count >= 5) AS signal_velocity_10m_spike,

        -- Sygnał 2: High Z-Score (odchylenie >= 3.0 od średniej konta)
        (z_score >= 3.0) AS signal_high_zscore,

        -- Sygnał 3: Structuring (>= 3 transakcje między $9k a $9.9k w 1h)
        (structuring_1h_count >= 3) AS signal_structuring,

        -- Sygnał 4: Card Testing (mała kwota <= $5 przy podwyższonym velocity)
        (amount_usd <= 5.0 AND velocity_10m_count >= 3) AS signal_card_testing,

        -- Sygnał 5: High-Value New Merchant (nowy merchant + kwota >= $500)
        (is_first_merchant_visit AND amount_usd >= 500.0) AS signal_new_merchant_large_amount

    FROM combined
)

SELECT * FROM signals_evaluated

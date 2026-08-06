-- =============================================================
-- INTERMEDIATE: int_transaction_velocity
-- Cel: Oblicza kroczące agregacje czasowe (velocity) per konto:
--      - 10 minut (wykrywanie ataku / card testing)
--      - 1 godzina (wykrywanie strukturacji i nagłego skoku aktywności)
--      - 24 godziny (dzienny profil aktywności)
-- =============================================================

WITH stg AS (
    SELECT *
    FROM {{ ref('stg_transactions') }}
    WHERE _is_valid = TRUE
),

velocity_calculated AS (
    SELECT
        transaction_id,
        account_id,
        merchant_id,
        transaction_ts,
        amount_usd,
        status,

        -- =====================================================
        -- 10-MINUTOWE VELOCITY (600 sekund)
        -- =====================================================
        COUNT(*) OVER (
            PARTITION BY account_id
            ORDER BY UNIX_SECONDS(transaction_ts)
            RANGE BETWEEN 600 PRECEDING AND CURRENT ROW
        ) AS velocity_10m_count,

        COALESCE(SUM(amount_usd) OVER (
            PARTITION BY account_id
            ORDER BY UNIX_SECONDS(transaction_ts)
            RANGE BETWEEN 600 PRECEDING AND CURRENT ROW
        ), 0.0) AS velocity_10m_amount,

        -- =====================================================
        -- 1-GODZINNE VELOCITY (3600 sekund)
        -- =====================================================
        COUNT(*) OVER (
            PARTITION BY account_id
            ORDER BY UNIX_SECONDS(transaction_ts)
            RANGE BETWEEN 3600 PRECEDING AND CURRENT ROW
        ) AS velocity_1h_count,

        COALESCE(SUM(amount_usd) OVER (
            PARTITION BY account_id
            ORDER BY UNIX_SECONDS(transaction_ts)
            RANGE BETWEEN 3600 PRECEDING AND CURRENT ROW
        ), 0.0) AS velocity_1h_amount,

        -- =====================================================
        -- 24-GODZINNE VELOCITY (86400 sekund)
        -- =====================================================
        COUNT(*) OVER (
            PARTITION BY account_id
            ORDER BY UNIX_SECONDS(transaction_ts)
            RANGE BETWEEN 86400 PRECEDING AND CURRENT ROW
        ) AS velocity_24h_count,

        COALESCE(SUM(amount_usd) OVER (
            PARTITION BY account_id
            ORDER BY UNIX_SECONDS(transaction_ts)
            RANGE BETWEEN 86400 PRECEDING AND CURRENT ROW
        ), 0.0) AS velocity_24h_amount,

        -- =====================================================
        -- STRUKTARYZACJA (9,000 USD - 9,999 USD w ciągu 1 godziny)
        -- =====================================================
        COUNTIF(amount_usd BETWEEN 9000 AND 9999) OVER (
            PARTITION BY account_id
            ORDER BY UNIX_SECONDS(transaction_ts)
            RANGE BETWEEN 3600 PRECEDING AND CURRENT ROW
        ) AS structuring_1h_count

    FROM stg
)

SELECT * FROM velocity_calculated

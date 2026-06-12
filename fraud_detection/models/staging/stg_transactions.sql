-- =============================================================
-- STAGING: stg_transactions
-- Źródło:  raw.transactions (landing zone)
-- Cel:     Oczyszczenie i standaryzacja surowych danych
--          Nie usuwa rekordów — flaguje problemy kolumną _is_valid
--          Audit trail musi być kompletny
-- =============================================================

WITH source AS (
    -- Pobieramy surowe dane ze źródła
    SELECT * FROM {{ source('fraud_detection', 'transactions') }}
),

cleaned AS (
    SELECT
        -- =====================================================
        -- IDENTYFIKATORY — trim whitespace, uppercase
        -- =====================================================
        TRIM(transaction_id)                    AS transaction_id,
        TRIM(account_id)                        AS account_id,
        TRIM(card_id)                           AS card_id,
        UPPER(TRIM(card_type))                  AS card_type,
        TRIM(card_expiry_date)                  AS card_expiry_date,
        TRIM(merchant_id)                       AS merchant_id,
        TRIM(merchant_name)                     AS merchant_name,

        -- =====================================================
        -- GEOGRAFIA — standaryzacja kodów krajów i stanów
        -- =====================================================
        TRIM(merchant_city)                     AS merchant_city,
        UPPER(TRIM(merchant_state))             AS merchant_state,
        UPPER(TRIM(merchant_country))           AS merchant_country,
        TRIM(merchant_zip)                      AS merchant_zip,

        -- =====================================================
        -- PŁATNOŚĆ — uppercase typ płatności
        -- =====================================================
        UPPER(TRIM(payment_type))               AS payment_type,

        -- =====================================================
        -- KWOTY — zaokrąglenie do 2 miejsc po przecinku
        -- =====================================================
        ROUND(original_amount, 2)               AS original_amount,
        UPPER(TRIM(original_currency))          AS original_currency,
        ROUND(amount_usd, 2)                    AS amount_usd,
        ROUND(balance_after, 2)                 AS balance_after,

        -- =====================================================
        -- STATUSY — lowercase dla spójności
        -- =====================================================
        LOWER(TRIM(status))                     AS status,

        -- =====================================================
        -- TIMESTAMPS
        -- =====================================================
        transaction_ts,
        uploaded_at,

        -- =====================================================
        -- WALIDACJA — flagujemy problemy zamiast usuwać rekordy
        -- Każda reguła walidacji jako osobna kolumna boolean
        -- =====================================================

        -- Krytyczne pola nie mogą być NULL
        (transaction_id IS NULL)                AS _flag_null_transaction_id,
        (account_id IS NULL)                    AS _flag_null_account_id,
        (original_amount IS NULL)               AS _flag_null_amount,
        (transaction_ts IS NULL)                AS _flag_null_timestamp,

        -- Kwota nie może być ujemna lub zerowa
        (original_amount <= 0)                  AS _flag_negative_amount,

        -- Transakcja nie może być z przyszłości
        (transaction_ts > CURRENT_TIMESTAMP())  AS _flag_future_timestamp,

        -- Typ płatności musi być jednym z dozwolonych
        (UPPER(TRIM(payment_type)) NOT IN ('S', 'V', 'D', 'K', 'B'))
                                                AS _flag_invalid_payment_type,

        -- Status musi być accepted lub rejected
        (LOWER(TRIM(status)) NOT IN ('accepted', 'rejected'))
                                                AS _flag_invalid_status,

        -- Karta po terminie ważności
        -- card_expiry_date format: YYYY-MM
        (SAFE.PARSE_DATE('%Y-%m', card_expiry_date) < DATE_TRUNC(CURRENT_DATE(), MONTH))
                                                AS _flag_expired_card,

        -- Metadane stagingu
        CURRENT_TIMESTAMP()                     AS _staged_at,

    FROM source
),

-- Łączny flag czy rekord jest valid
final AS (
    SELECT
        *,

        -- Rekord jest invalid jeśli którakolwiek flaga jest True
        NOT (
            _flag_null_transaction_id
            OR _flag_null_account_id
            OR _flag_null_amount
            OR _flag_null_timestamp
            OR _flag_negative_amount
            OR _flag_future_timestamp
            OR _flag_invalid_payment_type
            OR _flag_invalid_status
        ) AS _is_valid

    FROM cleaned
)

SELECT * FROM final

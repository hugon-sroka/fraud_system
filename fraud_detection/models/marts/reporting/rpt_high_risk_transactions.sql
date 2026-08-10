-- =============================================================
-- MARTS: rpt_high_risk_transactions
-- Cel: Wszystkie transakcje HIGH i CRITICAL z pełnym detalem.
--      Idealny do drill-down i analizy podejrzanych przypadków.
--      Mały rozmiar (~2-5k wierszy) = błyskawiczne zapytania.
-- =============================================================

{{ config(
    materialized='table',
    partition_by={
      "field": "transaction_ts",
      "data_type": "timestamp",
      "granularity": "day"
    },
    cluster_by=["risk_tier", "account_id"]
) }}

SELECT
    transaction_id,
    account_id,
    merchant_id,
    merchant_name,
    merchant_country,
    payment_type,
    amount_usd,
    status,
    transaction_ts,
    DATE(transaction_ts) AS transaction_date,
    velocity_10m_count,
    velocity_1h_count,
    z_score,
    signal_velocity_10m_spike,
    signal_high_zscore,
    signal_structuring,
    signal_card_testing,
    signal_new_merchant_large_amount,
    risk_score,
    risk_tier
FROM {{ ref('fct_transactions') }}
WHERE risk_tier IN ('HIGH', 'CRITICAL')

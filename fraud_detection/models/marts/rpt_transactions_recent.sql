-- =============================================================
-- MARTS: rpt_transactions_recent
-- Cel: Transakcje z ostatnich 30 dni z pełnym detalem.
--      Wystarczająco mały dla Looker Studio (~40k wierszy),
--      wystarczająco szczegółowy do analizy drill-down.
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
    risk_tier,
    requires_agent_investigation
FROM {{ ref('fct_transactions') }}
WHERE transaction_ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)

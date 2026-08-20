DECLARE start_date     DATE  DEFAULT '2026-05-10';
DECLARE end_date       DATE  DEFAULT '2026-06-08';
DECLARE rows_per_batch INT64 DEFAULT 20000;

INSERT INTO `fraud-sytem.fraud_detection.transactions`
  (transaction_id, account_id, transaction_ts, uploaded_at, amount, merchant_id)
WITH r AS (
  SELECT
    load_date,
    RAND() < 0.02                            AS is_late,
    CAST(1 + FLOOR(RAND() * 14) AS INT64)    AS late_days,
    CAST(FLOOR(RAND() * 86400) AS INT64)     AS event_sec,
    CAST(FLOOR(RAND() * 86400) AS INT64)     AS load_sec,
    CAST(5 + FLOOR(RAND() * 295) AS INT64)   AS ingest_lag_sec,
    CAST(FLOOR(RAND() * 50000) AS INT64)     AS acc_n,
    CAST(FLOOR(RAND() * 2000)  AS INT64)     AS mer_n,
    ROUND(RAND() * 5000, 2)                  AS amount
  FROM UNNEST(GENERATE_DATE_ARRAY(start_date, end_date)) AS load_date
  CROSS JOIN UNNEST(GENERATE_ARRAY(1, rows_per_batch))
),
e AS (
  SELECT r.*,
    CASE WHEN is_late
      THEN TIMESTAMP_ADD(
             TIMESTAMP(DATE_SUB(load_date, INTERVAL late_days DAY)),
             INTERVAL event_sec SECOND)
      ELSE TIMESTAMP_ADD(TIMESTAMP(load_date), INTERVAL event_sec SECOND)
    END AS event_ts
  FROM r
)
SELECT
  GENERATE_UUID(),
  CONCAT('ACC', LPAD(CAST(acc_n AS STRING), 6, '0')),
  event_ts,
  CASE WHEN is_late
    THEN TIMESTAMP_ADD(TIMESTAMP(load_date), INTERVAL load_sec SECOND)
    ELSE TIMESTAMP_ADD(event_ts, INTERVAL ingest_lag_sec SECOND)
  END,
  amount,
  CONCAT('MER', LPAD(CAST(mer_n AS STRING), 5, '0'))
FROM e;
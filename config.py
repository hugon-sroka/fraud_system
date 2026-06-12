# =============================================================
# BIGQUERY
# =============================================================
GCP_PROJECT = "fraud-sytem"
BQ_DATASET  = "fraud_detection"

# =============================================================
# FRAUD RULES THRESHOLDS
# =============================================================
VELOCITY_THRESHOLD       = 5      # max transakcji w 10 minut
ZSCORE_THRESHOLD         = 3.0    # odchylenia od średniej konta
STRUCTURING_MIN_COUNT    = 3      # min transakcji przy strukturyzacji
STRUCTURING_AMOUNT_MIN   = 9000   # dolny próg kwoty strukturyzacji
STRUCTURING_AMOUNT_MAX   = 9999   # górny próg kwoty strukturyzacji
NEW_MERCHANT_MIN_AMOUNT  = 500    # min kwota u nowego sprzedawcy

# =============================================================
# SCORING
# =============================================================
SOFT_BLOCK_SCORE = 30   # dodatkowa weryfikacja
HARD_BLOCK_SCORE = 60   # automatyczne zablokowanie

# =============================================================
# AGENT
# =============================================================
ALERT_WEBHOOK   = "https://your-webhook-url/alerts"
AGENT_MAX_ITER  = 10    # zabezpieczenie przed nieskończoną pętlą
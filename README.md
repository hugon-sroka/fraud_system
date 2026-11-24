# # 🛡️ Fraud Detection Pipeline (dbt + BigQuery + Python)

A fraud detection project built on synthetic transaction data: dbt models on Google BigQuery
compute fraud signals, and a Python rules engine turns them into decisions
(ALLOW / CHALLENGE_2FA / BLOCK_CARD), orchestrated with Airflow.

---

## 🏗️ System Architecture

```
[ Synthetic Generator ] ---> ( Raw Transactions in BigQuery )
                                        |
                                        v
                            [ dbt Transformation Pipeline ]
                            ├── staging: stg_transactions (cleaning & validation flags)
                            ├── intermediate: velocity metrics, z-scores, fraud signals
                            └── marts: fct_transactions, dim_accounts, fct_fraud_alerts
                                        |
                  +---------------------+---------------------+
                  |                                           |
                  v                                           v
    [ BI Dashboards ]                             [ Rules Engine (Python) ]
  (Looker Studio / PowerBI)                       ├── 5 fraud signals from dbt
                                                  └── Decision: ALLOW / CHALLENGE_2FA / BLOCK_CARD
                                                              |
                                                              v
                                                [ Airflow DAG + JSON audit log ]
```

---

## 🚀 Key Components

1. **Synthetic Data Generator** (`data_generation/ generate_transactions.py`):
   - Simulates 1,000 customer accounts across 12 months.
   - Embeds 10 realistic fraud patterns: velocity spikes, structuring ($9k–$9.9k), Z-score deviations, merchant anomalies, expired card usage, and geographic jumps.

2. **dbt Transformation Pipeline** (`fraud_detection/`):
   - **Staging**: Data cleansing, schema standardization, audit tags, non-destructive validation flags.
   - **Intermediate**: Windowed aggregate metrics (10-min, 1-hr, 24-hr velocity), account baseline spending ($\mu$, $\sigma$), anomaly signal flagging.
   - **Marts**: Star schema (`fct_transactions`, `dim_accounts`, `dim_merchants`) with risk scoring ($0–100$) and high-risk alert queue (`fct_fraud_alerts`).

3. **Rules Engine** (`rules/`, `agent/`, `services/`):
   - Evaluates 5 signals from dbt: velocity (10 min), z-score, structuring, card testing, high-value new merchant.
   - Critical patterns (structuring, card testing) or 2+ signals → BLOCK_CARD; one signal → CHALLENGE_2FA.
   - Every decision is saved to a JSON audit log with the rules that triggered it.

**Roadmap:** LLM-assisted investigation of borderline alerts, decision log in BigQuery, account takeover rule based on login events.

4. **Pipeline Orchestration** (`dags/` / `main.py`):
   - **Apache Airflow DAG**: Production orchestration managing data load → dbt run → dbt test → agent resolution batch execution.
   - **CLI Orchestrator**: Fast local developer execution runner.

---

## 📁 Repository Structure

```
fraud_system/
├── config.py                 # Central configuration & fraud thresholds
├── main.py                   # Local orchestrator entry point
├── requirements.txt          # Python dependencies
├── data_generation/          # Synthetic transaction generator script
├── fraud_detection/          # dbt project (staging, intermediate, marts)
│   ├── dbt_project.yml
│   └── models/
│       ├── staging/
│       ├── intermediate/
│       └── marts/
├── agent/                    # LLM Agentic investigation engine
├── rules/                    # Deterministic fraud rule definitions
├── services/                 # BigQuery connector & notification dispatchers
└── schemas/                  # Pydantic data models & contracts
```

---

## 🛠️ Getting Started

### Prerequisites
- Python 3.10+
- Google Cloud Platform account with BigQuery enabled
- `dbt-bigquery` installed

### Quick Start
```bash
# Activate virtual environment
source newvenv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run synthetic data generation
python data_generation/generate_transactions.py --output data_generation/transactions.csv

# Run dbt transformations
cd fraud_detection
dbt run
dbt test
```

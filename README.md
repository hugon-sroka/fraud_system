# 🛡️ End-to-End Agentic Fraud Detection & Data Platform

An enterprise-grade fraud detection platform combining synthetic transaction generation, **dbt** data modeling on **Google BigQuery**, and an **Autonomous Agentic Fraud Resolution Engine**.

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
    [ BI Dashboards ]                             [ Agentic Fraud Analyst ]
  (Looker Studio / PowerBI)                       ├── Rules Engine (Thresholds)
                                                  ├── LLM Contextual Investigation
                                                  └── Automated Actions (Block, 2FA, Escalation)
                                                              |
                                                              v
                                                [ Orchestrator & Audit Trail ]
                                                (Airflow DAG / FastAPI / BigQuery Logs)
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

3. **Autonomous Agentic Resolution Engine** (`agent/`, `rules/`, `services/`):
   - **Deterministic Rules Engine**: Rapid scoring against configured thresholds (`config.py`).
   - **Agent Analyst**: Multi-step AI investigation examining customer historical patterns, location continuity, and merchant risk to prevent false positives.
   - **Action Dispatcher**: Triggers automated block/allow decisions, updates BigQuery resolution logs, and posts webhook alerts.

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

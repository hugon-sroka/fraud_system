"""
=============================================================
APACHE AIRFLOW DAG: End-to-End Fraud Detection Pipeline
=============================================================
Orchestrates:
  1. Synthetic Data Generation / Ingestion
  2. dbt Staging, Intermediate & Mart Transformations
  3. dbt Data Quality Tests
  4. Autonomous Agentic Fraud Analyst Resolution
=============================================================
"""

from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import TaskGroup

# Default DAG configuration & SLA retry policies
default_args = {
    "owner": "fraud_data_engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}

# Base project path inside WSL / server
PROJECT_DIR = str(Path(__file__).resolve().parent.parent)

with DAG(
    dag_id="fraud_detection_end_to_end_pipeline",
    default_args=default_args,
    description="End-to-End BigQuery dbt pipeline + Agentic Fraud Analyst Engine",
    schedule="@hourly",  # Runs hourly in production
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["fraud_detection", "dbt", "bigquery", "agentic_ai"],
) as dag:

    # -------------------------------------------------------------
    # TASK GROUP 1: Ingestion & Data Generation
    # -------------------------------------------------------------
    with TaskGroup("data_ingestion_group", tooltip="Ingests raw transactions into BigQuery landing zone") as ingestion_group:
        ingest_transactions = BashOperator(
            task_id="generate_raw_transactions",
            bash_command=f"cd {PROJECT_DIR} && source newvenv/bin/activate && python data_generation/generate_transactions.py --output data_generation/transactions.csv",
        )

    # -------------------------------------------------------------
    # TASK GROUP 2: dbt Transformation Pipeline
    # -------------------------------------------------------------
    with TaskGroup("dbt_transformations_group", tooltip="Runs dbt models from staging to analytical marts") as dbt_group:
        dbt_staging = BashOperator(
            task_id="dbt_run_staging",
            bash_command=f"cd {PROJECT_DIR}/fraud_detection && dbt run --select staging",
        )

        dbt_intermediate_marts = BashOperator(
            task_id="dbt_run_intermediate_marts",
            bash_command=f"cd {PROJECT_DIR}/fraud_detection && dbt run --select intermediate marts",
        )

        dbt_test = BashOperator(
            task_id="dbt_test_quality_checks",
            bash_command=f"cd {PROJECT_DIR}/fraud_detection && dbt test",
        )

        dbt_staging >> dbt_intermediate_marts >> dbt_test

    # -------------------------------------------------------------
    # TASK GROUP 3: Agentic Fraud Resolution
    # -------------------------------------------------------------
    with TaskGroup("agent_resolution_group", tooltip="Executes AI Fraud Analyst agent on high-risk alerts") as agent_group:
        run_agent_analyst = BashOperator(
            task_id="execute_fraud_agent_investigation",
            bash_command=f"cd {PROJECT_DIR} && source newvenv/bin/activate && python main.py --limit 20",
        )

    # -------------------------------------------------------------
    # PIPELINE DEPENDENCY GRAPH
    # -------------------------------------------------------------
    ingestion_group >> dbt_group >> agent_group

#!/usr/bin/env python3
"""
=============================================================
FRAUD DETECTION & AGENTIC RESOLUTION ORCHESTRATOR
=============================================================
Uruchomienie:
    python main.py
    python main.py --limit 10
=============================================================
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agent.analyst import FraudAnalystAgent
from services.alert_service import load_mock_alerts

console = Console()


def run_agentic_pipeline(alert_limit: int = 5):
    console.print(
        Panel.fit(
            "[bold cyan]🛡️ Sentinel Fraud Detection & Agentic Resolution Engine[/bold cyan]\n"
            "[dim]dbt Transformation Pipeline + Autonomous AI Fraud Analyst[/dim]",
            border_style="cyan",
        )
    )

    console.print("[bold yellow]Step 1: Fetching pending high-risk fraud alerts...[/bold yellow]")
    alerts = load_mock_alerts(limit=alert_limit)
    console.print(f"Loaded [bold green]{len(alerts)}[/bold green] alerts from alert queue.\n")

    agent = FraudAnalystAgent(agent_name="Sentinel-Alpha")

    table = Table(title="🤖 Agentic Fraud Resolution Results", show_header=True, header_style="bold magenta")
    table.add_column("Txn ID", style="dim")
    table.add_column("Account", style="cyan")
    table.add_column("Amount (USD)", justify="right")
    table.add_column("Risk Score", justify="center")
    table.add_column("Risk Tier", justify="center")
    table.add_column("Decision", justify="center")
    table.add_column("Applied Rules")

    resolutions = []

    for alert in alerts:
        resolution = agent.investigate(alert)
        resolutions.append(resolution.model_dump())

        # Styling decisions
        if resolution.decision.value == "BLOCK_CARD":
            dec_style = "[bold red]⛔ BLOCK_CARD[/bold red]"
        elif resolution.decision.value == "CHALLENGE_2FA":
            dec_style = "[bold yellow]🔑 CHALLENGE_2FA[/bold yellow]"
        else:
            dec_style = "[bold green]✅ ALLOW[/bold green]"

        table.add_row(
            alert.transaction_id,
            alert.account_id,
            f"${alert.amount_usd:,.2f}",
            f"{alert.risk_score:.0f}",
            f"[bold]{alert.risk_tier.value}[/bold]",
            dec_style,
            ", ".join(resolution.applied_rules) if resolution.applied_rules else "[dim]None[/dim]",
        )

    console.print(table)

    # Save audit trail log
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "agent_resolutions.json"

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(resolutions, f, indent=2)

    console.print(f"\n[bold green]✅ Audit resolutions successfully saved to {log_file}[/bold green]")


def main():
    parser = argparse.ArgumentParser(description="Sentinel Fraud Detection Agent CLI")
    parser.add_argument("--limit", type=int, default=5, help="Max alerts to process")
    args = parser.parse_args()

    run_agentic_pipeline(alert_limit=args.limit)


if __name__ == "__main__":
    main()

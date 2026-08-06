#!/usr/bin/env python3
"""
=============================================================
FRAUD DETECTION & EVALUATION RUNNER
=============================================================
How to run:
    python main.py
=============================================================
"""

import json
from dataclasses import asdict
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from rules.engine import evaluate_fraud
from services.alert_service import get_pending_alerts

console = Console()


def main():
    # Banner
    console.print(
        Panel.fit(
            "[bold cyan]🛡️ Sentinel Fraud Detection System[/bold cyan]\n"
            "[dim]dbt Pipeline + Rule Evaluation Engine[/dim]",
            border_style="cyan",
        )
    )

    # Step 1: Load alerts
    console.print("[bold yellow]Step 1: Loading pending fraud alerts...[/bold yellow]")
    alerts = get_pending_alerts(limit=5)
    console.print(f"Loaded [bold green]{len(alerts)}[/bold green] alerts to evaluate.\n")

    # Step 2: Build terminal table
    table = Table(title="Fraud Evaluation Results", show_header=True, header_style="bold magenta")
    table.add_column("Txn ID", style="dim")
    table.add_column("Account", style="cyan")
    table.add_column("Amount", justify="right")
    table.add_column("Decision", justify="center")
    table.add_column("Triggered Rules")

    results_to_save = []

    # Step 3: Evaluate each alert
    for alert in alerts:
        decision = evaluate_fraud(alert)
        results_to_save.append(asdict(decision))

        # Format decision color
        if decision.decision == "BLOCK_CARD":
            dec_text = "[bold red]⛔ BLOCK_CARD[/bold red]"
        elif decision.decision == "CHALLENGE_2FA":
            dec_text = "[bold yellow]🔑 CHALLENGE_2FA[/bold yellow]"
        else:
            dec_text = "[bold green]✅ ALLOW[/bold green]"

        rules_str = ", ".join(decision.applied_rules) if decision.applied_rules else "[dim]None[/dim]"

        table.add_row(
            alert.transaction_id,
            alert.account_id,
            f"${alert.amount_usd:,.2f}",
            dec_text,
            rules_str,
        )

    # Print table to terminal
    console.print(table)

    # Step 4: Save JSON audit log
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "agent_resolutions.json"

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(results_to_save, f, indent=2)

    console.print(f"\n[bold green]✅ Saved evaluation log to {log_file}[/bold green]")


if __name__ == "__main__":
    main()

"""
Alert Service: Reads alerts from generated CSV or provides mock test alerts.
"""

import csv
from pathlib import Path
from typing import List
from schemas.alert import FraudAlert


def get_pending_alerts(limit: int = 5) -> List[FraudAlert]:
    """
    Reads alerts from generated CSV data.
    If CSV doesn't exist, returns fallback test alerts.
    """
    csv_path = Path("data_generation/transactions.csv")
    
    if not csv_path.exists():
        # Built-in fallback alerts for quick testing
        return [
            FraudAlert(
                transaction_id="TXN-101",
                account_id="ACC-8841",
                amount_usd=9450.00,
                transaction_ts="2026-08-06 12:00:00",
                velocity_10m_count=6,
                z_score=4.2,
                signal_velocity_10m_spike=True,
                signal_high_zscore=True,
                signal_structuring=True,
                risk_score=85.0,
                risk_tier="CRITICAL",
            ),
            FraudAlert(
                transaction_id="TXN-102",
                account_id="ACC-1204",
                amount_usd=3.50,
                transaction_ts="2026-08-06 12:05:00",
                velocity_10m_count=5,
                z_score=0.3,
                signal_velocity_10m_spike=True,
                signal_card_testing=True,
                risk_score=65.0,
                risk_tier="CRITICAL",
            ),
            FraudAlert(
                transaction_id="TXN-103",
                account_id="ACC-3312",
                amount_usd=1200.00,
                transaction_ts="2026-08-06 12:10:00",
                velocity_10m_count=1,
                z_score=3.1,
                signal_high_zscore=True,
                risk_score=45.0,
                risk_tier="HIGH",
            ),
        ]

    # Read from CSV file
    alerts = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            if len(alerts) >= limit:
                break
            
            # Map CSV row to FraudAlert object
            alerts.append(
                FraudAlert(
                    transaction_id=row.get("transaction_id", f"TXN-{idx}"),
                    account_id=row.get("account_id", f"ACC-{idx}"),
                    amount_usd=float(row.get("original_amount", 100.0)),
                    transaction_ts=row.get("transaction_ts", "2026-08-06 12:00:00"),
                    velocity_10m_count=2,
                    z_score=1.5,
                    risk_score=35.0,
                    risk_tier="HIGH",
                )
            )

    return alerts

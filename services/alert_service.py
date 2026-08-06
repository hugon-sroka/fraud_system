from __future__ import annotations

import csv
from pathlib import Path
from typing import List
from schemas.alert import FraudAlert, RiskTier
import config


def load_mock_alerts(csv_path: str | Path = "data_generation/transactions.csv", limit: int = 20) -> List[FraudAlert]:
    """
    Loads mock alerts from local generated CSV if BigQuery connection is not active.
    """
    alerts: List[FraudAlert] = []
    path = Path(csv_path)
    
    if not path.exists():
        # Fallback inline synthetic alerts if CSV does not exist yet
        return [
            FraudAlert(
                transaction_id="TXN-MOCK-001",
                account_id="ACC-8841",
                amount_usd=9450.00,
                transaction_ts="2026-08-06T12:00:00Z",
                velocity_10m_count=6,
                velocity_1h_count=8,
                z_score=4.2,
                signal_velocity_10m_spike=True,
                signal_high_zscore=True,
                signal_structuring=True,
                signal_card_testing=False,
                signal_new_merchant_large_amount=False,
                risk_score=85.0,
                risk_tier=RiskTier.CRITICAL,
                requires_agent_investigation=True,
            ),
            FraudAlert(
                transaction_id="TXN-MOCK-002",
                account_id="ACC-1204",
                amount_usd=3.50,
                transaction_ts="2026-08-06T12:05:00Z",
                velocity_10m_count=5,
                velocity_1h_count=5,
                z_score=0.3,
                signal_velocity_10m_spike=True,
                signal_high_zscore=False,
                signal_structuring=False,
                signal_card_testing=True,
                signal_new_merchant_large_amount=False,
                risk_score=65.0,
                risk_tier=RiskTier.CRITICAL,
                requires_agent_investigation=True,
            ),
            FraudAlert(
                transaction_id="TXN-MOCK-003",
                account_id="ACC-3312",
                amount_usd=1200.00,
                transaction_ts="2026-08-06T12:10:00Z",
                velocity_10m_count=1,
                velocity_1h_count=2,
                z_score=3.1,
                signal_velocity_10m_spike=False,
                signal_high_zscore=True,
                signal_structuring=False,
                signal_card_testing=False,
                signal_new_merchant_large_amount=True,
                risk_score=45.0,
                risk_tier=RiskTier.HIGH,
                requires_agent_investigation=True,
            )
        ]

    # Load from CSV if present
    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            if idx >= limit:
                break
            amount = float(row.get("amount_usd", row.get("original_amount", 100.0)))
            alerts.append(
                FraudAlert(
                    transaction_id=row.get("transaction_id", f"TXN-{idx}"),
                    account_id=row.get("account_id", f"ACC-{idx}"),
                    amount_usd=amount,
                    transaction_ts=row.get("transaction_ts", "2026-08-06T12:00:00Z"),
                    velocity_10m_count=2,
                    z_score=1.5,
                    risk_score=35.0,
                    risk_tier=RiskTier.HIGH,
                    requires_agent_investigation=True,
                )
            )

    return alerts

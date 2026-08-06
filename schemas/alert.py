"""
Simple data structures for fraud alerts and evaluation decisions.
Uses standard Python dataclasses for maximum readability.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class FraudAlert:
    transaction_id: str
    account_id: str
    amount_usd: float
    transaction_ts: str
    velocity_10m_count: int = 0
    velocity_1h_count: int = 0
    z_score: float = 0.0
    signal_velocity_10m_spike: bool = False
    signal_high_zscore: bool = False
    signal_structuring: bool = False
    signal_card_testing: bool = False
    signal_new_merchant_large_amount: bool = False
    risk_score: float = 0.0
    risk_tier: str = "LOW"


@dataclass
class FraudDecision:
    transaction_id: str
    account_id: str
    decision: str           # "BLOCK_CARD", "CHALLENGE_2FA", or "ALLOW"
    applied_rules: List[str] # List of triggered rule names
    reason: str             # Short explanation

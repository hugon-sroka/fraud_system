from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DecisionType(str, Enum):
    ALLOW = "ALLOW"
    CHALLENGE_2FA = "CHALLENGE_2FA"
    BLOCK_CARD = "BLOCK_CARD"
    ESCALATE_HUMAN = "ESCALATE_HUMAN"


class RiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FraudAlert(BaseModel):
    transaction_id: str
    account_id: str
    card_id: Optional[str] = None
    merchant_id: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_country: Optional[str] = "US"
    payment_type: Optional[str] = "S"
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
    risk_tier: RiskTier = RiskTier.LOW
    requires_agent_investigation: bool = False


class AgentResolution(BaseModel):
    transaction_id: str
    account_id: str
    decision: DecisionType
    confidence_score: float = Field(ge=0.0, le=1.0)
    rationale: str
    applied_rules: List[str] = Field(default_factory=list)
    risk_score: float
    risk_tier: RiskTier
    resolved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

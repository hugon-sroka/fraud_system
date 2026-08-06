from __future__ import annotations

from typing import List, Tuple
from schemas.alert import FraudAlert, DecisionType
import config


class RuleEvaluationResult:
    def __init__(
        self,
        suggested_decision: DecisionType,
        confidence: float,
        triggered_rules: List[str],
        reasoning: str,
    ):
        self.suggested_decision = suggested_decision
        self.confidence = confidence
        self.triggered_rules = triggered_rules
        self.reasoning = reasoning


def evaluate_rules(alert: FraudAlert) -> RuleEvaluationResult:
    triggered_rules: List[str] = []
    
    # 1. Structuring Detection Rule (AML evasion)
    if alert.signal_structuring:
        triggered_rules.append("RULE_STRUCTURING_BURST")
        
    # 2. Card Testing Attack Rule (Micro transactions in rapid burst)
    if alert.signal_card_testing:
        triggered_rules.append("RULE_CARD_TESTING_BURST")
        
    # 3. High Velocity Rule
    if alert.signal_velocity_10m_spike or alert.velocity_10m_count >= config.VELOCITY_THRESHOLD:
        triggered_rules.append("RULE_VELOCITY_10M_SPIKE")
        
    # 4. Extreme Z-Score Rule
    if alert.signal_high_zscore or alert.z_score >= config.ZSCORE_THRESHOLD:
        triggered_rules.append("RULE_EXTREME_SPEND_DEVIATION")
        
    # 5. New Merchant High-Value Rule
    if alert.signal_new_merchant_large_amount:
        triggered_rules.append("RULE_UNFAMILIAR_MERCHANT_HIGH_VALUE")
        
    # Decision Matrix based on Rule Combinations
    if "RULE_STRUCTURING_BURST" in triggered_rules or "RULE_CARD_TESTING_BURST" in triggered_rules:
        return RuleEvaluationResult(
            suggested_decision=DecisionType.BLOCK_CARD,
            confidence=0.95,
            triggered_rules=triggered_rules,
            reasoning="Critical fraud patterns detected (Structuring or Card Testing Attack). Immediate block recommended.",
        )
        
    if len(triggered_rules) >= 2:
        return RuleEvaluationResult(
            suggested_decision=DecisionType.BLOCK_CARD,
            confidence=0.88,
            triggered_rules=triggered_rules,
            reasoning=f"Multiple risk indicators triggered ({', '.join(triggered_rules)}). Card block recommended.",
        )
        
    if len(triggered_rules) == 1:
        return RuleEvaluationResult(
            suggested_decision=DecisionType.CHALLENGE_2FA,
            confidence=0.75,
            triggered_rules=triggered_rules,
            reasoning=f"Single elevated risk indicator ({triggered_rules[0]}). Step-up 2FA authentication recommended.",
        )
        
    # Default fallback for low-risk alerts
    return RuleEvaluationResult(
        suggested_decision=DecisionType.ALLOW,
        confidence=0.90,
        triggered_rules=[],
        reasoning="No high-risk fraud rules triggered. Safe to authorize.",
    )

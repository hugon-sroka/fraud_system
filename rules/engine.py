"""
Simple Rule Engine: Evaluates a transaction alert against 4 clear rules.
Returns a FraudDecision object containing the verdict and triggered rules.
"""

from schemas.alert import FraudAlert, FraudDecision


def evaluate_fraud(alert: FraudAlert) -> FraudDecision:
    """
    Evaluates risk signals on a transaction alert and decides an action:
      - BLOCK_CARD    : Immediate block for dangerous patterns (Structuring / Card Testing).
      - CHALLENGE_2FA : Step-up verification for suspicious velocity or spend deviation.
      - ALLOW         : Normal transaction.
    """
    triggered_rules = []

    # Rule 1: Structuring (AML Evasion - splitting payments under $10k threshold)
    if alert.signal_structuring:
        triggered_rules.append("RULE_STRUCTURING_BURST")

    # Rule 2: Card Testing (Bot testing stolen card with micro payments <= $5)
    if alert.signal_card_testing:
        triggered_rules.append("RULE_CARD_TESTING_BURST")

    # Rule 3: High Velocity (5+ transactions in 10 minutes)
    if alert.signal_velocity_10m_spike or alert.velocity_10m_count >= 5:
        triggered_rules.append("RULE_HIGH_VELOCITY_10M")

    # Rule 4: High Z-Score (Transaction amount is 3+ standard deviations above account avg)
    if alert.signal_high_zscore or alert.z_score >= 3.0:
        triggered_rules.append("RULE_HIGH_SPEND_DEVIATION")

    # --- DECISION LOGIC ---

    # Critical patterns -> Immediate Block
    if "RULE_STRUCTURING_BURST" in triggered_rules or "RULE_CARD_TESTING_BURST" in triggered_rules:
        return FraudDecision(
            transaction_id=alert.transaction_id,
            account_id=alert.account_id,
            decision="BLOCK_CARD",
            applied_rules=triggered_rules,
            reason="Dangerous fraud pattern detected (Structuring or Card Testing). Card blocked.",
        )

    # Multiple suspicious rules -> Block
    if len(triggered_rules) >= 2:
        return FraudDecision(
            transaction_id=alert.transaction_id,
            account_id=alert.account_id,
            decision="BLOCK_CARD",
            applied_rules=triggered_rules,
            reason=f"Multiple risk rules triggered: {', '.join(triggered_rules)}. Card blocked.",
        )

    # Single suspicious rule -> 2FA Challenge
    if len(triggered_rules) == 1:
        return FraudDecision(
            transaction_id=alert.transaction_id,
            account_id=alert.account_id,
            decision="CHALLENGE_2FA",
            applied_rules=triggered_rules,
            reason=f"Elevated risk indicator ({triggered_rules[0]}). Sent 2FA prompt.",
        )

    # Clean transaction -> Allow
    return FraudDecision(
        transaction_id=alert.transaction_id,
        account_id=alert.account_id,
        decision="ALLOW",
        applied_rules=[],
        reason="No risk rules triggered. Transaction approved.",
    )

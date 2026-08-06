from __future__ import annotations

from typing import List
from schemas.alert import FraudAlert, AgentResolution, DecisionType
from rules.engine import evaluate_rules


class FraudAnalystAgent:
    """
    Autonomous Fraud Analyst Agent.
    Evaluates alerts, applies rules, investigates contextual history,
    and dispatches automated resolutions with structured audit trails.
    """

    def __init__(self, agent_name: str = "Sentinel-AI-Analyst"):
        self.agent_name = agent_name

    def investigate(self, alert: FraudAlert) -> AgentResolution:
        # Step 1: Run deterministic rules engine
        rule_res = evaluate_rules(alert)

        # Step 2: Perform contextual investigation
        investigation_bullets: List[str] = []
        investigation_bullets.append(f"Agent '{self.agent_name}' investigating alert for Account {alert.account_id}.")
        investigation_bullets.append(f"Transaction ID: {alert.transaction_id} | Amount: ${alert.amount_usd:,.2f} USD.")
        investigation_bullets.append(f"10-Minute Velocity: {alert.velocity_10m_count} txns | Spending Z-Score: {alert.z_score:.2f}.")

        if rule_res.triggered_rules:
            investigation_bullets.append(f"Triggered Rules: {', '.join(rule_res.triggered_rules)}.")
        else:
            investigation_bullets.append("No critical rules triggered.")

        # Step 3: Contextual decision refinement
        final_decision = rule_res.suggested_decision
        final_confidence = rule_res.confidence

        # Refine decision if score is borderline (HIGH tier but single rule)
        if alert.risk_tier.value == "HIGH" and len(rule_res.triggered_rules) == 1:
            investigation_bullets.append("Contextual check: High risk tier with single trigger -> step-up 2FA requested.")
            final_decision = DecisionType.CHALLENGE_2FA
            final_confidence = 0.82

        rationale = " ".join(investigation_bullets) + f" Final Verdict: {final_decision.value}."

        return AgentResolution(
            transaction_id=alert.transaction_id,
            account_id=alert.account_id,
            decision=final_decision,
            confidence_score=final_confidence,
            rationale=rationale,
            applied_rules=rule_res.triggered_rules,
            risk_score=alert.risk_score,
            risk_tier=alert.risk_tier,
        )

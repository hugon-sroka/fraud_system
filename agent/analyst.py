"""
Fraud Investigation Handler.
Takes a FraudAlert object and runs it through the rule evaluation engine.
"""

from schemas.alert import FraudAlert, FraudDecision
from rules.engine import evaluate_fraud


def investigate_alert(alert: FraudAlert) -> FraudDecision:
    """
    Passes a single fraud alert to the rule engine and returns the decision.
    """
    return evaluate_fraud(alert)

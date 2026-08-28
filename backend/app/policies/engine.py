from enum import Enum

class PolicyDecision(Enum):
    ALLOW = "ALLOW"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCK = "BLOCK"

def evaluate_transaction_policy(amount: int, policy: dict) -> PolicyDecision:
    """
    Evaluates whether a transaction is allowed autonomously based on merchant policy.
    amount: in minor units (paise)
    policy: merchant policy configuration
    """
    if policy.get("max_autonomous_amount") and amount > policy["max_autonomous_amount"]:
        return PolicyDecision.REVIEW_REQUIRED
    
    # Other policy evaluations...
    
    return PolicyDecision.ALLOW

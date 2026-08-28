import uuid
import pytest
from app.models.merchant import User, Merchant
from app.models.policy import Policy
from app.services.policy_service import PolicyService
from app.core.constants import AuthorizationStatus


def test_policy_deterministic_rules(db_session):
    user_m = User(email="merchant_pol@test.com", password_hash="hash", role="MERCHANT")
    db_session.add(user_m)
    db_session.flush()
    merchant = Merchant(user_id=user_m.id, name="Policy Store")
    db_session.add(merchant)
    db_session.flush()

    # Policy: max autonomous = ₹5,000 (500000 paise), review above = ₹2,000 (200000 paise), blocked category = 'gambling'
    policy = Policy(
        merchant_id=merchant.id,
        max_autonomous_amount=500000,
        daily_autonomous_limit=5000000,
        require_approval_above=200000,
        blocked_categories=["gambling", "restricted"],
        is_ai_enabled=True,
    )
    db_session.add(policy)
    db_session.commit()

    service = PolicyService(db_session)

    # 1. Normal purchase under approval limit -> APPROVED
    status, reason = service.evaluate_transaction(
        merchant_id=merchant.id,
        amount=150000,  # ₹1,500
        categories=["electronics"],
        is_ai_agent=True,
    )
    assert status == AuthorizationStatus.APPROVED

    # 2. Purchase above review limit but below max autonomous limit -> REVIEW_REQUIRED
    status, reason = service.evaluate_transaction(
        merchant_id=merchant.id,
        amount=350000,  # ₹3,500
        categories=["electronics"],
        is_ai_agent=True,
    )
    assert status == AuthorizationStatus.REVIEW_REQUIRED

    # 3. Purchase exceeding max autonomous limit -> BLOCKED
    status, reason = service.evaluate_transaction(
        merchant_id=merchant.id,
        amount=700000,  # ₹7,000
        categories=["electronics"],
        is_ai_agent=True,
    )
    assert status == AuthorizationStatus.BLOCKED

    # 4. Purchase in blocked category -> BLOCKED
    status, reason = service.evaluate_transaction(
        merchant_id=merchant.id,
        amount=50000,  # ₹500
        categories=["gambling"],
        is_ai_agent=True,
    )
    assert status == AuthorizationStatus.BLOCKED

    # 5. When AI is disabled -> BLOCKED
    policy.is_ai_enabled = False
    db_session.commit()
    status, reason = service.evaluate_transaction(
        merchant_id=merchant.id,
        amount=10000,
        categories=["electronics"],
        is_ai_agent=True,
    )
    assert status == AuthorizationStatus.BLOCKED

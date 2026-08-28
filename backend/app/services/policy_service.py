import uuid
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models.policy import Policy
from app.repositories.policy_repository import PolicyRepository
from app.schemas.policy.requests import PolicyUpdate
from app.core.constants import AuthorizationStatus, ActorType, AuditEventType
from app.core.exceptions import NotFoundError
from app.services.audit_service import AuditService


class PolicyService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PolicyRepository(db)
        self.audit_service = AuditService(db)

    def get_merchant_policy(self, merchant_id: uuid.UUID) -> Policy:
        policy = self.repo.get_by_merchant_id(merchant_id)
        if not policy:
            # Create default policy if none exists
            policy = self.repo.create_or_update(
                {
                    "max_autonomous_amount": 500000,
                    "daily_autonomous_limit": 5000000,
                    "require_approval_above": 500000,
                    "blocked_categories": [],
                    "is_ai_enabled": True,
                },
                merchant_id=merchant_id,
            )
        return policy

    def update_merchant_policy(self, merchant_id: uuid.UUID, req: PolicyUpdate) -> Policy:
        policy_data = {
            "max_autonomous_amount": req.max_autonomous_amount,
            "daily_autonomous_limit": req.daily_autonomous_limit,
            "require_approval_above": req.require_approval_above,
            "blocked_categories": req.blocked_categories,
            "is_ai_enabled": req.is_ai_enabled,
        }
        policy = self.repo.create_or_update(policy_data, merchant_id=merchant_id)

        self.audit_service.log_event(
            event_type=AuditEventType.POLICY_UPDATED.value,
            actor_type=ActorType.MERCHANT.value,
            entity_type="policy",
            merchant_id=merchant_id,
            entity_id=policy.id,
            event_data=policy_data,
        )
        return policy

    def evaluate_transaction(
        self,
        merchant_id: uuid.UUID,
        amount: int,
        categories: list[str],
        is_ai_agent: bool = True,
    ) -> Tuple[AuthorizationStatus, str]:
        """
        Deterministic policy evaluation engine.
        Returns (AuthorizationStatus, reason).
        """
        policy = self.get_merchant_policy(merchant_id)

        if is_ai_agent and not policy.is_ai_enabled:
            return AuthorizationStatus.BLOCKED, "AI commerce transactions are disabled for this merchant."

        # Check blocked categories
        for cat in categories:
            if cat.lower() in [b.lower() for b in policy.blocked_categories]:
                return (
                    AuthorizationStatus.BLOCKED,
                    f"Category '{cat}' is blocked by merchant governance policy.",
                )

        # Check max autonomous transaction limit
        if amount > policy.max_autonomous_amount:
            return (
                AuthorizationStatus.BLOCKED,
                f"Amount ₹{amount / 100:.2f} exceeds merchant maximum autonomous transaction limit of ₹{policy.max_autonomous_amount / 100:.2f}.",
            )

        # Check approval requirement threshold
        if amount > policy.require_approval_above:
            return (
                AuthorizationStatus.REVIEW_REQUIRED,
                f"Amount ₹{amount / 100:.2f} requires merchant approval (threshold: ₹{policy.require_approval_above / 100:.2f}).",
            )

        return AuthorizationStatus.APPROVED, "Transaction conforms to merchant governance policy."

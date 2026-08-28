import uuid
from sqlalchemy.orm import Session
from app.models.authorization import Authorization
from app.models.quote import Quote
from app.repositories.authorization_repository import AuthorizationRepository
from app.repositories.quote_repository import QuoteRepository
from app.repositories.cart_repository import CartRepository
from app.services.quote_service import QuoteService
from app.services.policy_service import PolicyService
from app.services.audit_service import AuditService
from app.core.exceptions import NotFoundError, ForbiddenError, QuoteExpiredError, PolicyViolationError
from app.core.constants import AuthorizationStatus, ActorType, AuditEventType


class AuthorizationService:
    def __init__(self, db: Session):
        self.db = db
        self.auth_repo = AuthorizationRepository(db)
        self.quote_repo = QuoteRepository(db)
        self.cart_repo = CartRepository(db)
        self.quote_service = QuoteService(db)
        self.policy_service = PolicyService(db)
        self.audit_service = AuditService(db)

    def authorize_quote(self, quote_id: uuid.UUID, customer_id: uuid.UUID) -> Authorization:
        is_valid, is_expired, quote = self.quote_service.validate_quote(quote_id)
        if is_expired:
            raise QuoteExpiredError()

        cart = self.cart_repo.get_by_id(quote.cart_id)
        if not cart:
            raise NotFoundError("Cart", quote.cart_id)
        if cart.customer_id != customer_id:
            raise ForbiddenError("You do not own this cart.")

        # Extract categories from snapshot
        categories = [item.get("category", "") for item in quote.line_items_snapshot if "category" in item]

        # Evaluate merchant policy
        policy_decision, reason = self.policy_service.evaluate_transaction(
            merchant_id=cart.merchant_id,
            amount=quote.total,
            categories=categories,
            is_ai_agent=True,
        )

        authorization = Authorization(
            customer_id=customer_id,
            quote_id=quote.id,
            amount=quote.total,
            currency=quote.currency,
            status=policy_decision.value,
        )
        created_auth = self.auth_repo.create(authorization)

        # Log audit event
        event_type = (
            AuditEventType.AUTHORIZATION_APPROVED.value
            if policy_decision == AuthorizationStatus.APPROVED
            else AuditEventType.AUTHORIZATION_BLOCKED.value
            if policy_decision == AuthorizationStatus.BLOCKED
            else AuditEventType.AUTHORIZATION_REVIEW_REQUIRED.value
        )
        self.audit_service.log_event(
            event_type=event_type,
            actor_type=ActorType.SYSTEM.value,
            entity_type="authorization",
            actor_id=customer_id,
            merchant_id=cart.merchant_id,
            entity_id=created_auth.id,
            event_data={"status": created_auth.status, "amount": quote.total, "reason": reason},
        )

        if policy_decision == AuthorizationStatus.BLOCKED:
            raise PolicyViolationError(f"Transaction blocked: {reason}", reason_code="POLICY_BLOCKED")

        return created_auth

    def get_authorization_by_id(self, authorization_id: uuid.UUID) -> Authorization:
        auth = self.auth_repo.get_by_id(authorization_id)
        if not auth:
            raise NotFoundError("Authorization", authorization_id)
        return auth

import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.models.order import Order
from app.repositories.order_repository import OrderRepository
from app.repositories.authorization_repository import AuthorizationRepository
from app.repositories.quote_repository import QuoteRepository
from app.repositories.cart_repository import CartRepository
from app.integrations.razorpay.orders import RazorpayOrdersAdapter
from app.core.exceptions import (
    NotFoundError,
    ForbiddenError,
    ValidationError,
    QuoteExpiredError,
    IdempotencyConflictError,
)
from app.core.constants import AuthorizationStatus, OrderStatus, ActorType, AuditEventType
from app.services.quote_service import QuoteService
from app.services.audit_service import AuditService


class CheckoutService:
    def __init__(self, db: Session, razorpay_orders: Optional[RazorpayOrdersAdapter] = None):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.auth_repo = AuthorizationRepository(db)
        self.quote_repo = QuoteRepository(db)
        self.cart_repo = CartRepository(db)
        self.quote_service = QuoteService(db)
        self.razorpay_orders = razorpay_orders or RazorpayOrdersAdapter()
        self.audit_service = AuditService(db)

    def create_checkout_order(
        self,
        quote_id: uuid.UUID,
        authorization_id: uuid.UUID,
        customer_id: uuid.UUID,
    ) -> Order:
        # Check if an order already exists for this authorization (Idempotency)
        existing_order = self.order_repo.get_by_authorization_id(authorization_id)
        if existing_order:
            return existing_order

        # Verify Authorization
        authorization = self.auth_repo.get_by_id(authorization_id)
        if not authorization:
            raise NotFoundError("Authorization", authorization_id)
        if authorization.customer_id != customer_id:
            raise ForbiddenError("You do not own this authorization.")
        if authorization.status != AuthorizationStatus.APPROVED.value:
            raise ValidationError(
                f"Cannot create order for authorization with status '{authorization.status}'. Must be APPROVED."
            )
        if authorization.quote_id != quote_id:
            raise ValidationError("Authorization does not match the provided quote.")

        # Verify Quote Freshness & Invariant
        is_valid, is_expired, quote = self.quote_service.validate_quote(quote_id)
        if is_expired:
            raise QuoteExpiredError()

        # Authoritative Amount Invariant Check
        if authorization.amount != quote.total:
            raise ValidationError("Authorization amount does not match authoritative quote total.")

        cart = self.cart_repo.get_by_id(quote.cart_id)
        if not cart:
            raise NotFoundError("Cart", quote.cart_id)

        receipt = f"rcpt_{str(authorization.id)[:8]}_{str(uuid.uuid4())[:8]}"

        # Create External Razorpay Order
        razorpay_resp = self.razorpay_orders.create_order(
            amount=quote.total,
            currency=quote.currency,
            receipt=receipt,
            notes={
                "authorization_id": str(authorization.id),
                "customer_id": str(customer_id),
                "merchant_id": str(cart.merchant_id),
            },
        )
        razorpay_order_id = razorpay_resp["id"]

        order = Order(
            merchant_id=cart.merchant_id,
            customer_id=customer_id,
            cart_id=cart.id,
            authorization_id=authorization.id,
            razorpay_order_id=razorpay_order_id,
            amount=quote.total,
            currency=quote.currency,
            status=OrderStatus.CREATED.value,
            receipt=receipt,
        )

        # Database-level unique constraint on authorization_id guarantees idempotency
        created_order = self.order_repo.create(order)

        self.audit_service.log_event(
            event_type=AuditEventType.ORDER_CREATED.value,
            actor_type=ActorType.CUSTOMER.value,
            entity_type="order",
            actor_id=customer_id,
            merchant_id=cart.merchant_id,
            entity_id=created_order.id,
            event_data={
                "razorpay_order_id": razorpay_order_id,
                "amount": quote.total,
                "receipt": receipt,
            },
        )

        return created_order

    def get_order_by_id(self, order_id: uuid.UUID) -> Order:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundError("Order", order_id)
        return order

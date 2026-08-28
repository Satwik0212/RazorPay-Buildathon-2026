import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.quote import Quote
from app.models.cart import Cart
from app.repositories.quote_repository import QuoteRepository
from app.repositories.cart_repository import CartRepository
from app.repositories.product_repository import ProductRepository
from app.core.config import settings
from app.core.exceptions import NotFoundError, ForbiddenError, ValidationError, QuoteExpiredError
from app.core.constants import ActorType, AuditEventType
from app.security.idempotency import generate_quote_hash
from app.services.audit_service import AuditService


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class QuoteService:
    def __init__(self, db: Session):
        self.db = db
        self.quote_repo = QuoteRepository(db)
        self.cart_repo = CartRepository(db)
        self.product_repo = ProductRepository(db)
        self.audit_service = AuditService(db)

    def create_quote(self, cart_id: uuid.UUID, customer_id: uuid.UUID) -> Quote:
        cart = self.cart_repo.get_by_id(cart_id)
        if not cart:
            raise NotFoundError("Cart", cart_id)
        if cart.customer_id != customer_id:
            raise ForbiddenError("You do not own this cart.")
        if not cart.items:
            raise ValidationError("Cannot create a quote for an empty cart.")

        subtotal = 0
        line_items_snapshot: List[Dict[str, Any]] = []
        currency = settings.DEFAULT_CURRENCY

        # Authoritative price resolution from database product records
        for item in cart.items:
            product = self.product_repo.get_by_id(item.product_id)
            if not product or not product.is_active:
                raise ValidationError(f"Product '{item.product_id}' is no longer available.")
            if product.inventory and product.inventory.available_quantity < item.quantity:
                raise ValidationError(
                    f"Product '{product.name}' has insufficient stock (available: {product.inventory.available_quantity})."
                )

            item_subtotal = product.price * item.quantity
            subtotal += item_subtotal
            currency = product.currency

            line_items_snapshot.append({
                "product_id": str(product.id),
                "name": product.name,
                "category": product.category,
                "unit_price": product.price,
                "quantity": item.quantity,
                "currency": product.currency,
                "subtotal": item_subtotal,
            })

        discount = 0
        shipping = 0
        tax = 0
        total = subtotal - discount + shipping + tax

        # Invariant check
        if total < 0:
            total = 0

        quote_hash = generate_quote_hash(
            cart_id=str(cart_id),
            items=line_items_snapshot,
            subtotal=subtotal,
            discount=discount,
            shipping=shipping,
            tax=tax,
            total=total,
        )

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.DEFAULT_QUOTE_EXPIRY_SECONDS)

        quote = Quote(
            cart_id=cart_id,
            subtotal=subtotal,
            discount=discount,
            shipping=shipping,
            tax=tax,
            total=total,
            currency=currency,
            quote_hash=quote_hash,
            expires_at=expires_at,
            line_items_snapshot=line_items_snapshot,
        )
        created_quote = self.quote_repo.create(quote)

        self.audit_service.log_event(
            event_type=AuditEventType.QUOTE_CREATED.value,
            actor_type=ActorType.SYSTEM.value,
            entity_type="quote",
            actor_id=customer_id,
            merchant_id=cart.merchant_id,
            entity_id=created_quote.id,
            event_data={
                "cart_id": str(cart_id),
                "total": total,
                "currency": currency,
                "expires_at": expires_at.isoformat(),
            },
        )

        return created_quote

    def get_quote_by_id(self, quote_id: uuid.UUID) -> Quote:
        quote = self.quote_repo.get_by_id(quote_id)
        if not quote:
            raise NotFoundError("Quote", quote_id)
        return quote

    def validate_quote(self, quote_id: uuid.UUID) -> Tuple[bool, bool, Quote]:
        quote = self.get_quote_by_id(quote_id)
        is_expired = datetime.now(timezone.utc) >= to_utc(quote.expires_at)
        is_valid = not is_expired

        return is_valid, is_expired, quote

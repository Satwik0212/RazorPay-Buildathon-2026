import json
import uuid
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.webhook_event import WebhookEvent
from app.models.payment import Payment
from app.models.order import Order
from app.repositories.webhook_repository import WebhookRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.cart_repository import CartRepository
from app.security.webhook_verification import validate_webhook_signature_or_raise
from app.core.exceptions import WebhookSignatureError, ValidationError
from app.core.constants import PaymentStatus, OrderStatus, ActorType, AuditEventType
from app.core.logging import logger
from app.services.audit_service import AuditService


class WebhookService:
    def __init__(self, db: Session):
        self.db = db
        self.webhook_repo = WebhookRepository(db)
        self.payment_repo = PaymentRepository(db)
        self.order_repo = OrderRepository(db)
        self.product_repo = ProductRepository(db)
        self.cart_repo = CartRepository(db)
        self.audit_service = AuditService(db)

    def process_razorpay_webhook(
        self,
        raw_body: bytes,
        signature: str,
    ) -> Tuple[bool, str, str]:
        """
        Idempotent and cryptographically verified webhook processing.
        Returns: (is_duplicate: bool, event_id: str, message: str)
        """
        # 1. Cryptographic signature verification over raw body
        validate_webhook_signature_or_raise(raw_body=raw_body, signature=signature)

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception as exc:
            raise ValidationError(f"Invalid JSON in webhook body: {exc}") from exc

        event_type = payload.get("event", "unknown")
        # In Razorpay webhooks, payload may have an event id, or we derive one from event + payment id
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_entity = payload.get("payload", {}).get("order", {}).get("entity", {})

        razorpay_payment_id = payment_entity.get("id")
        razorpay_order_id = payment_entity.get("order_id") or order_entity.get("id")

        # Unique event identifier (using payload id or composite event key)
        event_id = payload.get("id") or f"{event_type}_{razorpay_payment_id or razorpay_order_id}_{payload.get('created_at', '')}"

        # 2. Idempotency Check
        existing_event = self.webhook_repo.get_by_event_id(event_id)
        if existing_event:
            logger.info(f"[WEBHOOK IDEMPOTENCY] Duplicate event '{event_id}' skipped.")
            return True, event_id, "Event already processed (idempotent)."

        # Record incoming event
        webhook_record = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            payload=payload,
            signature_verified=True,
            processed=False,
        )
        self.webhook_repo.create(webhook_record)

        # 3. Process Event Business Logic
        try:
            if event_type in ("payment.captured", "payment.authorized", "order.paid"):
                self._handle_payment_success(payment_entity, razorpay_order_id, razorpay_payment_id)
            elif event_type == "payment.failed":
                self._handle_payment_failure(payment_entity, razorpay_order_id, razorpay_payment_id)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")

            self.webhook_repo.mark_processed(event_id)
            
            self.audit_service.log_event(
                event_type=AuditEventType.WEBHOOK_PROCESSED.value,
                actor_type=ActorType.WEBHOOK.value,
                entity_type="webhook_event",
                entity_id=webhook_record.id,
                event_data={"event_type": event_type, "event_id": event_id},
            )
            return False, event_id, "Webhook processed successfully."

        except Exception as exc:
            logger.error(f"Error processing webhook event {event_id}: {exc}")
            self.webhook_repo.mark_processed(event_id, error=str(exc))
            raise

    def _handle_payment_success(
        self,
        payment_entity: Dict[str, Any],
        razorpay_order_id: str,
        razorpay_payment_id: str,
    ) -> None:
        if not razorpay_order_id:
            logger.warning("Payment success webhook received without order_id.")
            return

        order = self.order_repo.get_by_razorpay_order_id(razorpay_order_id)
        if not order:
            logger.warning(f"No local order found for Razorpay order {razorpay_order_id}")
            return

        payment_amount = payment_entity.get("amount", order.amount)
        # Validate payment amount against order amount
        if payment_amount != order.amount:
            logger.error(
                f"Amount mismatch in webhook for order {order.id}: expected {order.amount}, got {payment_amount}"
            )
            order.status = OrderStatus.REVIEW_REQUIRED.value
            self.order_repo.update_status(order.id, OrderStatus.REVIEW_REQUIRED.value)
            return

        if order.status == OrderStatus.PAID.value:
            logger.info(f"Order {order.id} is already PAID. Skipping duplicate processing.")
            return

        # ATOMIC INVENTORY DECREMENT
        cart = self.cart_repo.get_by_id(order.cart_id)
        if cart and cart.items:
            item_quantities = {}
            for item in cart.items:
                item_quantities[item.product_id] = item_quantities.get(item.product_id, 0) + item.quantity
            
            try:
                with self.db.begin_nested():
                    for product_id, quantity in item_quantities.items():
                        success = self.product_repo.decrement_inventory(product_id, quantity)
                        if not success:
                            raise ValueError(f"Insufficient inventory for product {product_id}")
            except ValueError as exc:
                logger.error(f"Order {order.id} failed inventory decrement: {exc}")
                order.status = OrderStatus.REVIEW_REQUIRED.value
                self.order_repo.update_status(order.id, OrderStatus.REVIEW_REQUIRED.value)
                
                self.audit_service.log_event(
                    event_type=AuditEventType.WEBHOOK_FAILED.value,
                    actor_type=ActorType.WEBHOOK.value,
                    entity_type="order",
                    merchant_id=order.merchant_id,
                    entity_id=order.id,
                    event_data={
                        "razorpay_payment_id": razorpay_payment_id,
                        "reason": str(exc),
                    },
                )
                return

        # Check or create payment record
        existing_payment = self.payment_repo.get_by_razorpay_payment_id(razorpay_payment_id)
        if not existing_payment:
            payment = Payment(
                order_id=order.id,
                razorpay_payment_id=razorpay_payment_id,
                status=PaymentStatus.CAPTURED.value,
                method=payment_entity.get("method", "card"),
                amount=payment_amount,
                currency=payment_entity.get("currency", order.currency),
            )
            self.payment_repo.create(payment)
        else:
            existing_payment.status = PaymentStatus.CAPTURED.value
            self.payment_repo.update(existing_payment)

        # Transition Order state to PAID
        order.status = OrderStatus.PAID.value
        self.order_repo.update_status(order.id, OrderStatus.PAID.value)

        self.audit_service.log_event(
            event_type=AuditEventType.PAYMENT_CAPTURED.value,
            actor_type=ActorType.WEBHOOK.value,
            entity_type="order",
            merchant_id=order.merchant_id,
            entity_id=order.id,
            event_data={
                "razorpay_payment_id": razorpay_payment_id,
                "amount": payment_amount,
                "status": "PAID",
            },
        )

    def _handle_payment_failure(
        self,
        payment_entity: Dict[str, Any],
        razorpay_order_id: str,
        razorpay_payment_id: str,
    ) -> None:
        if not razorpay_order_id:
            return

        order = self.order_repo.get_by_razorpay_order_id(razorpay_order_id)
        if not order:
            return

        if order.status == OrderStatus.PAID.value:
            logger.info(f"Order {order.id} is already PAID. Ignoring payment.failed webhook.")
            return

        error_code = payment_entity.get("error_code")
        error_description = payment_entity.get("error_description")

        if razorpay_payment_id:
            existing_payment = self.payment_repo.get_by_razorpay_payment_id(razorpay_payment_id)
            if not existing_payment:
                payment = Payment(
                    order_id=order.id,
                    razorpay_payment_id=razorpay_payment_id,
                    status=PaymentStatus.FAILED.value,
                    method=payment_entity.get("method"),
                    amount=payment_entity.get("amount", order.amount),
                    currency=payment_entity.get("currency", order.currency),
                    error_code=error_code,
                    error_reason=error_description,
                )
                self.payment_repo.create(payment)

        self.order_repo.update_status(order.id, OrderStatus.FAILED.value)

        self.audit_service.log_event(
            event_type=AuditEventType.PAYMENT_FAILED.value,
            actor_type=ActorType.WEBHOOK.value,
            entity_type="order",
            merchant_id=order.merchant_id,
            entity_id=order.id,
            event_data={
                "razorpay_payment_id": razorpay_payment_id,
                "error_code": error_code,
                "error_reason": error_description,
            },
        )

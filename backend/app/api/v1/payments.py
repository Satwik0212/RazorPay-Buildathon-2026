import uuid
import hmac
import hashlib
from fastapi import APIRouter, Depends, status as http_status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.config import settings
from app.core.constants import UserRole, OrderStatus, PaymentStatus, CartStatus, AuditEventType, ActorType
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.schemas.payment.responses import PaymentResponse, PaymentStatusResponse
from app.services.payment_service import PaymentService
from app.services.audit_service import AuditService
from app.security.authentication import get_current_user
from app.models.merchant import User
from app.models.payment import Payment
from app.repositories.order_repository import OrderRepository
from app.repositories.cart_repository import CartRepository

router = APIRouter(tags=["Payments"])


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentVerifyResponse(BaseModel):
    success: bool
    order_id: uuid.UUID
    payment_id: str
    message: str


def _verify_order_ownership(order, current_user: User):
    if current_user.role == UserRole.ADMIN.value:
        return
    if current_user.role == UserRole.MERCHANT.value and current_user.merchant and order.merchant_id == current_user.merchant.id:
        return
    if current_user.role == UserRole.CUSTOMER.value and current_user.customer and order.customer_id == current_user.customer.id:
        return
    raise ForbiddenError("You do not have permission to view this payment information.")


@router.post("/payments/verify", response_model=PaymentVerifyResponse, status_code=http_status.HTTP_200_OK)
def verify_payment(
    req: PaymentVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    P0-3: Synchronous Razorpay payment verification.
    Validates HMAC-SHA256 signature, transitions order to PAID,
    creates a Payment record, marks cart COMPLETED, decrements inventory,
    and emits an audit event.
    """
    # 1. Verify HMAC-SHA256 signature
    payload = f"{req.razorpay_order_id}|{req.razorpay_payment_id}"
    expected_sig = hmac.new(
        key=settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_sig, req.razorpay_signature):
        raise ValidationError("Invalid Razorpay payment signature. Payment verification failed.")

    # 2. Find the order
    order_repo = OrderRepository(db)
    order = order_repo.get_by_razorpay_order_id(req.razorpay_order_id)
    if not order:
        raise NotFoundError("Order", req.razorpay_order_id)

    # 3. Authorization check
    _verify_order_ownership(order, current_user)

    # 4. Idempotency: already verified
    if order.status == OrderStatus.PAID.value:
        return PaymentVerifyResponse(
            success=True,
            order_id=order.id,
            payment_id=req.razorpay_payment_id,
            message="Payment already verified.",
        )

    # 5. Transition order to PAID
    order.status = OrderStatus.PAID.value

    # 6. Create Payment record
    payment = Payment(
        order_id=order.id,
        razorpay_payment_id=req.razorpay_payment_id,
        status=PaymentStatus.CAPTURED.value,
        amount=order.amount,
        currency=order.currency,
    )
    db.add(payment)

    # 7. P0-4: Mark cart as COMPLETED so a fresh cart is created on next purchase
    cart_repo = CartRepository(db)
    cart = cart_repo.get_by_id(order.cart_id)
    if cart:
        cart.status = CartStatus.COMPLETED.value

    # 8. Atomically decrement inventory for each cart item
    if cart and cart.items:
        for item in cart.items:
            if item.product and hasattr(item.product, "inventory") and item.product.inventory:
                inv = item.product.inventory
                inv.available_quantity = max(0, inv.available_quantity - item.quantity)
                if inv.available_quantity == 0:
                    item.product.is_active = False

    # 9. Emit audit event
    audit_service = AuditService(db)
    audit_service.log_event(
        event_type=AuditEventType.PAYMENT_CAPTURED.value if hasattr(AuditEventType, "PAYMENT_CAPTURED") else "PAYMENT_CAPTURED",
        actor_type=ActorType.CUSTOMER.value,
        entity_type="order",
        actor_id=current_user.id,
        merchant_id=order.merchant_id,
        entity_id=order.id,
        event_data={
            "razorpay_order_id": req.razorpay_order_id,
            "razorpay_payment_id": req.razorpay_payment_id,
            "amount": order.amount,
            "verification": "HMAC_SHA256_VERIFIED",
        },
    )

    db.commit()

    return PaymentVerifyResponse(
        success=True,
        order_id=order.id,
        payment_id=req.razorpay_payment_id,
        message="Payment verified and order confirmed.",
    )


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PaymentService(db)
    payment = service.get_payment_by_id(payment_id)
    _verify_order_ownership(payment.order, current_user)
    return payment

@router.get("/orders/{order_id}/payment-status", response_model=PaymentStatusResponse)
def get_order_payment_status(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PaymentService(db)
    order = service.order_repo.get_by_id(order_id)
    if not order:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Order", order_id)

    _verify_order_ownership(order, current_user)
    return service.get_order_payment_status(order_id)

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.payment.responses import PaymentResponse, PaymentStatusResponse
from app.services.payment_service import PaymentService

from app.security.authentication import get_current_user
from app.models.merchant import User
from app.core.constants import UserRole
from app.core.exceptions import ForbiddenError

router = APIRouter(tags=["Payments"])

def _verify_order_ownership(order, current_user: User):
    if current_user.role == UserRole.ADMIN.value:
        return
    if current_user.role == UserRole.MERCHANT.value and current_user.merchant and order.merchant_id == current_user.merchant.id:
        return
    if current_user.role == UserRole.CUSTOMER.value and current_user.customer and order.customer_id == current_user.customer.id:
        return
    raise ForbiddenError("You do not have permission to view this payment information.")

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
    # PaymentService.get_order_payment_status returns a dict, but we need the order to verify ownership.
    # We can fetch the order via order_repo directly, or add order to the returned dict.
    # Actually, PaymentService has order_repo.
    order = service.order_repo.get_by_id(order_id)
    if not order:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Order", order_id)
    
    _verify_order_ownership(order, current_user)
    return service.get_order_payment_status(order_id)

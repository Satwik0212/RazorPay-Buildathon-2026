import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.schemas.checkout.requests import CheckoutOrderCreate
from app.schemas.checkout.responses import CheckoutOrderResponse
from app.schemas.payment.responses import PaymentResponse
from app.services.checkout_service import CheckoutService
from app.services.payment_service import PaymentService
from app.security.authentication import get_current_customer
from app.models.customer import Customer

router = APIRouter(prefix="/checkout", tags=["Checkout"])


@router.post("/orders", response_model=CheckoutOrderResponse, status_code=status.HTTP_201_CREATED)
def create_checkout_order(
    req: CheckoutOrderCreate,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    service = CheckoutService(db)
    order = service.create_checkout_order(
        quote_id=req.quote_id,
        authorization_id=req.authorization_id,
        customer_id=current_customer.id,
    )
    return CheckoutOrderResponse(
        order_id=order.id,
        merchant_id=order.merchant_id,
        customer_id=order.customer_id,
        cart_id=order.cart_id,
        authorization_id=order.authorization_id,
        razorpay_order_id=order.razorpay_order_id,
        amount=order.amount,
        currency=order.currency,
        status=order.status,
        receipt=order.receipt,
        razorpay_key_id=settings.RAZORPAY_KEY_ID,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.get("/orders/{order_id}", response_model=CheckoutOrderResponse)
def get_checkout_order(order_id: uuid.UUID, db: Session = Depends(get_db)):
    service = CheckoutService(db)
    order = service.get_order_by_id(order_id)
    return CheckoutOrderResponse(
        order_id=order.id,
        merchant_id=order.merchant_id,
        customer_id=order.customer_id,
        cart_id=order.cart_id,
        authorization_id=order.authorization_id,
        razorpay_order_id=order.razorpay_order_id,
        amount=order.amount,
        currency=order.currency,
        status=order.status,
        receipt=order.receipt,
        razorpay_key_id=settings.RAZORPAY_KEY_ID,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.get("/orders/{order_id}/payments", response_model=List[PaymentResponse])
def get_order_payments(order_id: uuid.UUID, db: Session = Depends(get_db)):
    service = PaymentService(db)
    payments = service.get_payments_for_order(order_id)
    return [PaymentResponse.model_validate(p) for p in payments]

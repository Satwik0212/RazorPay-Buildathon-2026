import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.payment.responses import PaymentResponse, PaymentStatusResponse
from app.services.payment_service import PaymentService

router = APIRouter(tags=["Payments"])


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: uuid.UUID, db: Session = Depends(get_db)):
    service = PaymentService(db)
    return service.get_payment_by_id(payment_id)


@router.get("/orders/{order_id}/payment-status", response_model=PaymentStatusResponse)
def get_order_payment_status(order_id: uuid.UUID, db: Session = Depends(get_db)):
    service = PaymentService(db)
    return service.get_order_payment_status(order_id)

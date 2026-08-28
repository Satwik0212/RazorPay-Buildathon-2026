import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.payment import Payment
from app.models.order import Order
from app.repositories.payment_repository import PaymentRepository
from app.repositories.order_repository import OrderRepository
from app.core.exceptions import NotFoundError
from app.core.constants import PaymentStatus, OrderStatus


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.order_repo = OrderRepository(db)

    def get_payment_by_id(self, payment_id: uuid.UUID) -> Payment:
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundError("Payment", payment_id)
        return payment

    def get_payments_for_order(self, order_id: uuid.UUID) -> List[Payment]:
        return self.payment_repo.get_by_order_id(order_id)

    def get_order_payment_status(self, order_id: uuid.UUID) -> dict:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundError("Order", order_id)

        payments = self.get_payments_for_order(order_id)
        latest_payment = payments[0] if payments else None

        return {
            "order_id": order.id,
            "status": order.status,
            "payment_id": latest_payment.id if latest_payment else None,
            "razorpay_payment_id": latest_payment.razorpay_payment_id if latest_payment else None,
            "amount": order.amount,
            "currency": order.currency,
        }

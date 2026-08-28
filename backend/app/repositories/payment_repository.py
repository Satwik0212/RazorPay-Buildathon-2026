import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.payment import Payment


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, payment_id: uuid.UUID) -> Optional[Payment]:
        return self.db.get(Payment, payment_id)

    def get_by_razorpay_payment_id(self, razorpay_payment_id: str) -> Optional[Payment]:
        stmt = select(Payment).where(Payment.razorpay_payment_id == razorpay_payment_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_order_id(self, order_id: uuid.UUID) -> List[Payment]:
        stmt = select(Payment).where(Payment.order_id == order_id).order_by(Payment.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def create(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def update(self, payment: Payment) -> Payment:
        self.db.commit()
        self.db.refresh(payment)
        return payment

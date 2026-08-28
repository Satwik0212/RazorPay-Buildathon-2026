import uuid
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.models.order import Order
from app.core.exceptions import IdempotencyConflictError


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, order_id: uuid.UUID) -> Optional[Order]:
        stmt = (
            select(Order)
            .options(joinedload(Order.payments))
            .where(Order.id == order_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_by_authorization_id(self, authorization_id: uuid.UUID) -> Optional[Order]:
        stmt = (
            select(Order)
            .options(joinedload(Order.payments))
            .where(Order.authorization_id == authorization_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_by_razorpay_order_id(self, razorpay_order_id: str) -> Optional[Order]:
        stmt = (
            select(Order)
            .options(joinedload(Order.payments))
            .where(Order.razorpay_order_id == razorpay_order_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def create(self, order: Order) -> Order:
        try:
            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)
            return order
        except IntegrityError as exc:
            self.db.rollback()
            # If an order with this authorization_id or razorpay_order_id already exists, raise IdempotencyConflictError
            existing = self.get_by_authorization_id(order.authorization_id)
            if existing:
                raise IdempotencyConflictError(
                    f"An order already exists for authorization {order.authorization_id}.",
                    details={"existing_order_id": str(existing.id), "razorpay_order_id": existing.razorpay_order_id},
                ) from exc
            raise

    def update_status(self, order_id: uuid.UUID, status: str) -> Optional[Order]:
        order = self.get_by_id(order_id)
        if order:
            order.status = status
            self.db.commit()
            self.db.refresh(order)
        return order

    def list_merchant_orders(self, merchant_id: uuid.UUID, limit: int = 50, offset: int = 0) -> List[Order]:
        stmt = (
            select(Order)
            .options(joinedload(Order.payments))
            .where(Order.merchant_id == merchant_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).unique().scalars().all())

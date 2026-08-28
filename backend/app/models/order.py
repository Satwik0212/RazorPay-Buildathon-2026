import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, BigInteger, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import ModelBase
from app.core.constants import OrderStatus

if TYPE_CHECKING:
    from app.models.merchant import Merchant
    from app.models.customer import Customer
    from app.models.authorization import Authorization
    from app.models.payment import Payment


class Order(ModelBase):
    __tablename__ = "orders"

    merchant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), index=True, nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), index=True, nullable=False)
    cart_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("carts.id", ondelete="CASCADE"), index=True, nullable=False)
    # Database-level uniqueness on authorization_id ensures strict idempotency against duplicate order creation
    authorization_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("authorizations.id", ondelete="RESTRICT"), unique=True, index=True, nullable=False)
    razorpay_order_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=OrderStatus.CREATED.value, index=True, nullable=False)
    receipt: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="orders")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")
    authorization: Mapped["Authorization"] = relationship("Authorization", back_populates="order")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="order", cascade="all, delete-orphan")

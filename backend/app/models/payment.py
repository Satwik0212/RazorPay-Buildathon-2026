import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, BigInteger, Text, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import ModelBase
from app.core.constants import PaymentStatus

if TYPE_CHECKING:
    from app.models.order import Order


class Payment(ModelBase):
    __tablename__ = "payments"

    order_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    razorpay_payment_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=PaymentStatus.CREATED.value, index=True, nullable=False)
    method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="payments")

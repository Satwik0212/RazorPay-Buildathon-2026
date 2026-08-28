import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, BigInteger, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import ModelBase
from app.core.constants import AuthorizationStatus

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.quote import Quote
    from app.models.order import Order


class Authorization(ModelBase):
    __tablename__ = "authorizations"

    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), index=True, nullable=False)
    quote_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("quotes.id", ondelete="CASCADE"), index=True, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=AuthorizationStatus.PENDING.value, nullable=False)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="authorizations")
    quote: Mapped["Quote"] = relationship("Quote", back_populates="authorizations")
    order: Mapped[Optional["Order"]] = relationship("Order", back_populates="authorization", uselist=False)

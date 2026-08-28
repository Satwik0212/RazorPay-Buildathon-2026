import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import ModelBase
from app.core.constants import CartStatus

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.cart_item import CartItem
    from app.models.quote import Quote


class Cart(ModelBase):
    __tablename__ = "carts"

    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), index=True, nullable=False)
    merchant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=CartStatus.ACTIVE.value, nullable=False)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="carts")
    items: Mapped[List["CartItem"]] = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    quotes: Mapped[List["Quote"]] = relationship("Quote", back_populates="cart", cascade="all, delete-orphan")

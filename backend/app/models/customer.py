import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import ModelBase

if TYPE_CHECKING:
    from app.models.merchant import User
    from app.models.cart import Cart
    from app.models.order import Order
    from app.models.authorization import Authorization


class Customer(ModelBase):
    __tablename__ = "customers"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="customer")
    carts: Mapped[List["Cart"]] = relationship("Cart", back_populates="customer", cascade="all, delete-orphan")
    authorizations: Mapped[List["Authorization"]] = relationship("Authorization", back_populates="customer")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="customer")

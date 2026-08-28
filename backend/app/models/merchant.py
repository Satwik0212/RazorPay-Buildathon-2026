import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, Text, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import ModelBase
from app.core.constants import UserRole

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.product import Product
    from app.models.policy import Policy
    from app.models.order import Order


class User(ModelBase):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default=UserRole.CUSTOMER.value, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    merchant: Mapped[Optional["Merchant"]] = relationship("Merchant", back_populates="user", uselist=False, cascade="all, delete-orphan")
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Merchant(ModelBase):
    __tablename__ = "merchants"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="merchant")
    products: Mapped[List["Product"]] = relationship("Product", back_populates="merchant", cascade="all, delete-orphan")
    policy: Mapped[Optional["Policy"]] = relationship("Policy", back_populates="merchant", uselist=False, cascade="all, delete-orphan")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="merchant")

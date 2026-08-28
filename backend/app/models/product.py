import uuid
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, Boolean, Text, BigInteger, Integer, ForeignKey, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import ModelBase

if TYPE_CHECKING:
    from app.models.merchant import Merchant


class Product(ModelBase):
    __tablename__ = "products"

    merchant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    price: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Minor units (e.g. paise)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    product_metadata: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="products")
    inventory: Mapped[Optional["Inventory"]] = relationship("Inventory", back_populates="product", uselist=False, cascade="all, delete-orphan")


class Inventory(ModelBase):
    __tablename__ = "inventory"

    product_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), unique=True, nullable=False)
    available_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="inventory")

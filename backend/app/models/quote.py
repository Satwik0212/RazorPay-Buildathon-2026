import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, BigInteger, DateTime, ForeignKey, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import ModelBase

if TYPE_CHECKING:
    from app.models.cart import Cart
    from app.models.authorization import Authorization


class Quote(ModelBase):
    __tablename__ = "quotes"

    cart_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("carts.id", ondelete="CASCADE"), index=True, nullable=False)
    subtotal: Mapped[int] = mapped_column(BigInteger, nullable=False)
    discount: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    shipping: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    tax: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    quote_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    line_items_snapshot: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    cart: Mapped["Cart"] = relationship("Cart", back_populates="quotes")
    authorizations: Mapped[List["Authorization"]] = relationship("Authorization", back_populates="quote", cascade="all, delete-orphan")

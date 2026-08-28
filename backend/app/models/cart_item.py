import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Integer, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import ModelBase

if TYPE_CHECKING:
    from app.models.cart import Cart
    from app.models.product import Product


class CartItem(ModelBase):
    __tablename__ = "cart_items"

    cart_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("carts.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    cart: Mapped["Cart"] = relationship("Cart", back_populates="items")
    product: Mapped["Product"] = relationship("Product")

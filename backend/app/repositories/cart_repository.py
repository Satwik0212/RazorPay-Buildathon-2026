import uuid
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product


class CartRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, cart_id: uuid.UUID) -> Optional[Cart]:
        stmt = (
            select(Cart)
            .options(
                joinedload(Cart.items).joinedload(CartItem.product).joinedload(Product.inventory)
            )
            .where(Cart.id == cart_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_active_cart_for_customer(self, customer_id: uuid.UUID, merchant_id: uuid.UUID) -> Optional[Cart]:
        stmt = (
            select(Cart)
            .options(
                joinedload(Cart.items).joinedload(CartItem.product).joinedload(Product.inventory)
            )
            .where(
                Cart.customer_id == customer_id,
                Cart.merchant_id == merchant_id,
                Cart.status == "ACTIVE",
            )
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def create_cart(self, cart: Cart) -> Cart:
        self.db.add(cart)
        self.db.commit()
        return self.get_by_id(cart.id)

    def add_or_update_item(self, cart_id: uuid.UUID, product_id: uuid.UUID, quantity: int) -> CartItem:
        stmt = select(CartItem).where(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
        item = self.db.execute(stmt).scalar_one_or_none()
        if item:
            item.quantity += quantity
        else:
            item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity)
            self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_item_quantity(self, item_id: uuid.UUID, quantity: int) -> Optional[CartItem]:
        item = self.db.get(CartItem, item_id)
        if item:
            item.quantity = quantity
            self.db.commit()
            self.db.refresh(item)
        return item

    def remove_item(self, item_id: uuid.UUID) -> bool:
        item = self.db.get(CartItem, item_id)
        if item:
            self.db.delete(item)
            self.db.commit()
            return True
        return False

    def update_status(self, cart_id: uuid.UUID, status: str) -> Optional[Cart]:
        cart = self.get_by_id(cart_id)
        if cart:
            cart.status = status
            self.db.commit()
            self.db.refresh(cart)
        return cart

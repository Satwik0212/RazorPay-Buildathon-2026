import uuid
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.repositories.cart_repository import CartRepository
from app.repositories.product_repository import ProductRepository
from app.core.exceptions import NotFoundError, ForbiddenError, ValidationError, InsufficientInventoryError
from app.core.constants import ActorType, AuditEventType, CartStatus
from app.services.audit_service import AuditService


class CartService:
    def __init__(self, db: Session):
        self.db = db
        self.cart_repo = CartRepository(db)
        self.product_repo = ProductRepository(db)
        self.audit_service = AuditService(db)

    def create_or_get_cart(self, customer_id: uuid.UUID, merchant_id: uuid.UUID) -> Cart:
        cart = self.cart_repo.get_active_cart_for_customer(customer_id, merchant_id)
        if not cart:
            cart = Cart(customer_id=customer_id, merchant_id=merchant_id, status=CartStatus.ACTIVE.value)
            cart = self.cart_repo.create_cart(cart)
            self.audit_service.log_event(
                event_type=AuditEventType.CART_CREATED.value,
                actor_type=ActorType.CUSTOMER.value,
                entity_type="cart",
                actor_id=customer_id,
                merchant_id=merchant_id,
                entity_id=cart.id,
            )
        return cart

    def get_cart_for_customer(self, cart_id: uuid.UUID, customer_id: uuid.UUID) -> Cart:
        cart = self.cart_repo.get_by_id(cart_id)
        if not cart:
            raise NotFoundError("Cart", cart_id)
        if cart.customer_id != customer_id:
            raise ForbiddenError("You do not own this cart.")
        return cart

    def add_item_to_cart(self, cart_id: uuid.UUID, customer_id: uuid.UUID, product_id: uuid.UUID, quantity: int) -> Cart:
        cart = self.get_cart_for_customer(cart_id, customer_id)
        if cart.status != CartStatus.ACTIVE.value:
            raise ValidationError(f"Cannot add items to cart with status '{cart.status}'.")

        product = self.product_repo.get_by_id(product_id)
        if not product or not product.is_active:
            raise ValidationError(f"Product {product_id} is not available.")
        if product.merchant_id != cart.merchant_id:
            raise ValidationError("Cannot add products from a different merchant to this cart.")

        # Inventory check
        if product.inventory and product.inventory.available_quantity < quantity:
            raise InsufficientInventoryError(product_id, quantity, product.inventory.available_quantity)

        self.cart_repo.add_or_update_item(cart_id=cart_id, product_id=product_id, quantity=quantity)

        self.audit_service.log_event(
            event_type=AuditEventType.CART_ITEM_ADDED.value,
            actor_type=ActorType.CUSTOMER.value,
            entity_type="cart_item",
            actor_id=customer_id,
            merchant_id=cart.merchant_id,
            entity_id=cart.id,
            event_data={"product_id": str(product_id), "quantity": quantity},
        )
        return self.cart_repo.get_by_id(cart_id)

    def update_item_quantity(self, cart_id: uuid.UUID, customer_id: uuid.UUID, item_id: uuid.UUID, quantity: int) -> Cart:
        cart = self.get_cart_for_customer(cart_id, customer_id)
        item = next((i for i in cart.items if i.id == item_id), None)
        if not item:
            raise NotFoundError("CartItem", item_id)

        product = item.product
        if product and product.inventory and product.inventory.available_quantity < quantity:
            raise InsufficientInventoryError(product.id, quantity, product.inventory.available_quantity)

        self.cart_repo.update_item_quantity(item_id, quantity)
        return self.cart_repo.get_by_id(cart_id)

    def remove_item_from_cart(self, cart_id: uuid.UUID, customer_id: uuid.UUID, item_id: uuid.UUID) -> Cart:
        cart = self.get_cart_for_customer(cart_id, customer_id)
        self.cart_repo.remove_item(item_id)
        return self.cart_repo.get_by_id(cart_id)

    def validate_cart(self, cart_id: uuid.UUID, customer_id: uuid.UUID) -> Tuple[bool, List[str]]:
        cart = self.get_cart_for_customer(cart_id, customer_id)
        issues = []
        if not cart.items:
            issues.append("Cart is empty.")

        for item in cart.items:
            if not item.product or not item.product.is_active:
                issues.append(f"Product '{item.product_id}' is no longer active.")
            elif item.product.inventory and item.product.inventory.available_quantity < item.quantity:
                issues.append(
                    f"Product '{item.product.name}' has only {item.product.inventory.available_quantity} units available (requested: {item.quantity})."
                )

        return len(issues) == 0, issues

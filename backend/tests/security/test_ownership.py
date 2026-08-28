import uuid
import pytest
from app.models.merchant import User, Merchant
from app.models.customer import Customer
from app.models.product import Product, Inventory
from app.models.cart import Cart
from app.services.cart_service import CartService
from app.services.product_service import ProductService
from app.schemas.product.requests import ProductUpdate
from app.core.exceptions import ForbiddenError


def test_merchant_and_customer_ownership_isolation(db_session):
    # Merchants A & B
    u_m1 = User(email="m1_own@test.com", password_hash="h", role="MERCHANT")
    u_m2 = User(email="m2_own@test.com", password_hash="h", role="MERCHANT")
    db_session.add_all([u_m1, u_m2])
    db_session.flush()

    m1 = Merchant(user_id=u_m1.id, name="Store 1")
    m2 = Merchant(user_id=u_m2.id, name="Store 2")
    db_session.add_all([m1, m2])
    db_session.flush()

    # Product belonging to Merchant 1
    p1 = Product(merchant_id=m1.id, name="M1 Product", price=1000, category="c", is_active=True)
    db_session.add(p1)
    db_session.flush()
    db_session.add(Inventory(product_id=p1.id, available_quantity=10))

    # Customers A & B
    u_c1 = User(email="c1_own@test.com", password_hash="h", role="CUSTOMER")
    u_c2 = User(email="c2_own@test.com", password_hash="h", role="CUSTOMER")
    db_session.add_all([u_c1, u_c2])
    db_session.flush()

    c1 = Customer(user_id=u_c1.id)
    c2 = Customer(user_id=u_c2.id)
    db_session.add_all([c1, c2])
    db_session.flush()

    cart1 = Cart(customer_id=c1.id, merchant_id=m1.id, status="ACTIVE")
    db_session.add(cart1)
    db_session.commit()

    # 1. Merchant 2 attempting to modify Merchant 1's product -> ForbiddenError
    product_service = ProductService(db_session)
    with pytest.raises(ForbiddenError):
        product_service.update_product(p1.id, merchant_id=m2.id, req=ProductUpdate(price=500))

    # 2. Customer 2 attempting to access Customer 1's cart -> ForbiddenError
    cart_service = CartService(db_session)
    with pytest.raises(ForbiddenError):
        cart_service.get_cart_for_customer(cart_id=cart1.id, customer_id=c2.id)

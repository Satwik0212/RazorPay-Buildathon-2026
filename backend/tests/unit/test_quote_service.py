import uuid
from datetime import datetime, timedelta, timezone
import pytest
from app.models.merchant import User, Merchant
from app.models.customer import Customer
from app.models.product import Product, Inventory
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.services.quote_service import QuoteService, to_utc
from app.core.exceptions import ValidationError, QuoteExpiredError


def test_quote_calculation_minor_units_and_invariants(db_session):
    # Setup Merchant and Customer
    user_m = User(email="merchant_quote@test.com", password_hash="hash", role="MERCHANT")
    db_session.add(user_m)
    db_session.flush()
    merchant = Merchant(user_id=user_m.id, name="Audio Store")
    db_session.add(merchant)

    user_c = User(email="cust_quote@test.com", password_hash="hash", role="CUSTOMER")
    db_session.add(user_c)
    db_session.flush()
    customer = Customer(user_id=user_c.id)
    db_session.add(customer)
    db_session.flush()

    # Product 1: ₹4,999.00 -> 499900 paise
    p1 = Product(
        merchant_id=merchant.id,
        name="ANC Headphones",
        price=499900,
        currency="INR",
        category="headphones",
        is_active=True,
    )
    db_session.add(p1)
    db_session.flush()
    db_session.add(Inventory(product_id=p1.id, available_quantity=10, reserved_quantity=0))

    # Product 2: ₹299.00 -> 29900 paise
    p2 = Product(
        merchant_id=merchant.id,
        name="Audio Cable",
        price=29900,
        currency="INR",
        category="accessories",
        is_active=True,
    )
    db_session.add(p2)
    db_session.flush()
    db_session.add(Inventory(product_id=p2.id, available_quantity=5, reserved_quantity=0))

    # Create Cart: 1x Headphones + 2x Cables
    cart = Cart(customer_id=customer.id, merchant_id=merchant.id, status="ACTIVE")
    db_session.add(cart)
    db_session.flush()
    db_session.add(CartItem(cart_id=cart.id, product_id=p1.id, quantity=1))
    db_session.add(CartItem(cart_id=cart.id, product_id=p2.id, quantity=2))
    db_session.commit()

    # Calculate Quote
    service = QuoteService(db_session)
    quote = service.create_quote(cart_id=cart.id, customer_id=customer.id)

    # Expected: 499900*1 + 29900*2 = 499900 + 59800 = 559700 paise (₹5,597.00)
    assert quote.subtotal == 559700
    assert quote.discount == 0
    assert quote.shipping == 0
    assert quote.tax == 0
    assert quote.total == 559700
    assert quote.currency == "INR"
    assert len(quote.line_items_snapshot) == 2
    assert quote.quote_hash is not None
    assert to_utc(quote.expires_at) > datetime.now(timezone.utc)


def test_quote_expiration_validation(db_session):
    user_m = User(email="m2@test.com", password_hash="hash", role="MERCHANT")
    db_session.add(user_m)
    db_session.flush()
    merchant = Merchant(user_id=user_m.id, name="Store 2")
    db_session.add(merchant)

    user_c = User(email="c2@test.com", password_hash="hash", role="CUSTOMER")
    db_session.add(user_c)
    db_session.flush()
    customer = Customer(user_id=user_c.id)
    db_session.add(customer)
    db_session.flush()

    p = Product(merchant_id=merchant.id, name="P1", price=10000, category="cat", is_active=True)
    db_session.add(p)
    db_session.flush()
    db_session.add(Inventory(product_id=p.id, available_quantity=10))

    cart = Cart(customer_id=customer.id, merchant_id=merchant.id, status="ACTIVE")
    db_session.add(cart)
    db_session.flush()
    db_session.add(CartItem(cart_id=cart.id, product_id=p.id, quantity=1))
    db_session.commit()

    service = QuoteService(db_session)
    quote = service.create_quote(cart_id=cart.id, customer_id=customer.id)

    # Manually expire the quote in DB
    quote.expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    db_session.commit()

    is_valid, is_expired, q = service.validate_quote(quote.id)
    assert is_valid is False
    assert is_expired is True

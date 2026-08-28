import uuid
import pytest
from app.models.merchant import User, Merchant
from app.models.customer import Customer
from app.models.product import Product, Inventory
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.quote import Quote
from app.models.authorization import Authorization
from app.services.checkout_service import CheckoutService
from app.services.quote_service import QuoteService
from app.core.exceptions import ValidationError


def test_amount_tampering_prevention(db_session):
    # Setup
    user_m = User(email="tamper_m@test.com", password_hash="hash", role="MERCHANT")
    db_session.add(user_m)
    db_session.flush()
    merchant = Merchant(user_id=user_m.id, name="Tamper Store")
    db_session.add(merchant)

    user_c = User(email="tamper_c@test.com", password_hash="hash", role="CUSTOMER")
    db_session.add(user_c)
    db_session.flush()
    customer = Customer(user_id=user_c.id)
    db_session.add(customer)
    db_session.flush()

    # Authoritative Product Price: ₹4,999.00 (499900 paise)
    product = Product(
        merchant_id=merchant.id,
        name="Real Product",
        price=499900,
        currency="INR",
        category="electronics",
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()
    db_session.add(Inventory(product_id=product.id, available_quantity=10))

    cart = Cart(customer_id=customer.id, merchant_id=merchant.id, status="ACTIVE")
    db_session.add(cart)
    db_session.flush()
    db_session.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=1))
    db_session.commit()

    # 1. Quote Service: Client does not supply amount, server calculates from DB
    quote_service = QuoteService(db_session)
    quote = quote_service.create_quote(cart_id=cart.id, customer_id=customer.id)
    assert quote.total == 499900

    # 2. Tampered Authorization: Attempting to create an authorization for ₹1 (100 paise)
    tampered_auth = Authorization(
        customer_id=customer.id,
        quote_id=quote.id,
        amount=100,  # TAMPERED AMOUNT
        currency="INR",
        status="APPROVED",
    )
    db_session.add(tampered_auth)
    db_session.commit()

    # 3. Checkout Service must reject tampered authorization
    checkout_service = CheckoutService(db_session)
    with pytest.raises(ValidationError) as exc:
        checkout_service.create_checkout_order(
            quote_id=quote.id,
            authorization_id=tampered_auth.id,
            customer_id=customer.id,
        )
    assert "Authorization amount does not match authoritative quote total" in str(exc.value)

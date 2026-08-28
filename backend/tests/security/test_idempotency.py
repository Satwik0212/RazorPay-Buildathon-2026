import uuid
from datetime import datetime, timedelta, timezone
import pytest
from app.models.merchant import User, Merchant
from app.models.customer import Customer
from app.models.product import Product, Inventory
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.quote import Quote
from app.models.authorization import Authorization
from app.models.order import Order
from app.services.checkout_service import CheckoutService
from app.integrations.razorpay.orders import RazorpayOrdersAdapter
from app.integrations.razorpay.client import RazorpayClient
from app.core.exceptions import IdempotencyConflictError, ValidationError


def test_order_creation_database_level_idempotency(db_session):
    # Setup Merchant, Customer, Product, Cart, Quote, Authorization
    user_m = User(email="idem_m@test.com", password_hash="hash", role="MERCHANT")
    db_session.add(user_m)
    db_session.flush()
    merchant = Merchant(user_id=user_m.id, name="Idem Store")
    db_session.add(merchant)

    user_c = User(email="idem_c@test.com", password_hash="hash", role="CUSTOMER")
    db_session.add(user_c)
    db_session.flush()
    customer = Customer(user_id=user_c.id)
    db_session.add(customer)
    db_session.flush()

    cart = Cart(customer_id=customer.id, merchant_id=merchant.id, status="ACTIVE")
    db_session.add(cart)
    db_session.flush()

    quote = Quote(
        cart_id=cart.id,
        subtotal=49900,
        discount=0,
        shipping=0,
        tax=0,
        total=49900,
        currency="INR",
        quote_hash="hash123",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        line_items_snapshot=[],
    )
    db_session.add(quote)
    db_session.flush()

    authorization = Authorization(
        customer_id=customer.id,
        quote_id=quote.id,
        amount=49900,
        currency="INR",
        status="APPROVED",
    )
    db_session.add(authorization)
    db_session.commit()

    # Checkout Service with Mock Razorpay Client
    mock_client = RazorpayClient(is_mock=True)
    orders_adapter = RazorpayOrdersAdapter(client=mock_client)
    checkout_service = CheckoutService(db_session, razorpay_orders=orders_adapter)

    # First call: creates order successfully
    order1 = checkout_service.create_checkout_order(
        quote_id=quote.id,
        authorization_id=authorization.id,
        customer_id=customer.id,
    )
    assert order1 is not None
    assert order1.amount == 49900
    assert order1.authorization_id == authorization.id

    # Second call (concurrent retry / duplicate submission): returns the existing order safely without duplicate external call
    order2 = checkout_service.create_checkout_order(
        quote_id=quote.id,
        authorization_id=authorization.id,
        customer_id=customer.id,
    )
    assert order2.id == order1.id
    assert order2.razorpay_order_id == order1.razorpay_order_id

    # Direct database insertion test verifying the UNIQUE constraint on authorization_id
    duplicate_direct_order = Order(
        merchant_id=merchant.id,
        customer_id=customer.id,
        cart_id=cart.id,
        authorization_id=authorization.id,  # Duplicate authorization_id
        razorpay_order_id="order_duplicate_direct",
        amount=49900,
        currency="INR",
        status="CREATED",
        receipt="rcpt_duplicate",
    )
    from app.repositories.order_repository import OrderRepository
    order_repo = OrderRepository(db_session)
    with pytest.raises(IdempotencyConflictError):
        order_repo.create(duplicate_direct_order)

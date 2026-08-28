import hmac
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from app.models.merchant import User, Merchant
from app.models.customer import Customer
from app.models.cart import Cart
from app.models.quote import Quote
from app.models.authorization import Authorization
from app.models.order import Order
from app.models.payment import Payment
from app.services.webhook_service import WebhookService
from app.core.config import settings
from app.core.constants import OrderStatus, PaymentStatus


def test_webhook_event_idempotency_and_replay_protection(db_session):
    # Setup
    user_m = User(email="m_wh@test.com", password_hash="h", role="MERCHANT")
    user_c = User(email="c_wh@test.com", password_hash="h", role="CUSTOMER")
    db_session.add_all([user_m, user_c])
    db_session.flush()

    merchant = Merchant(user_id=user_m.id, name="WH Store")
    customer = Customer(user_id=user_c.id)
    db_session.add_all([merchant, customer])
    db_session.flush()

    cart = Cart(customer_id=customer.id, merchant_id=merchant.id, status="ACTIVE")
    db_session.add(cart)
    db_session.flush()

    quote = Quote(
        cart_id=cart.id,
        subtotal=100000,
        discount=0,
        shipping=0,
        tax=0,
        total=100000,
        currency="INR",
        quote_hash="h",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        line_items_snapshot=[],
    )
    db_session.add(quote)
    db_session.flush()

    authorization = Authorization(
        customer_id=customer.id,
        quote_id=quote.id,
        amount=100000,
        currency="INR",
        status="APPROVED",
    )
    db_session.add(authorization)
    db_session.flush()

    order = Order(
        merchant_id=merchant.id,
        customer_id=customer.id,
        cart_id=cart.id,
        authorization_id=authorization.id,
        razorpay_order_id="order_rzp_webhook_test_123",
        amount=100000,
        currency="INR",
        status=OrderStatus.CREATED.value,
        receipt="rcpt_wh_123",
    )
    db_session.add(order)
    db_session.commit()

    webhook_payload = {
        "id": "evt_unique_12345",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_999",
                    "order_id": "order_rzp_webhook_test_123",
                    "amount": 100000,
                    "currency": "INR",
                    "status": "captured",
                    "method": "upi",
                }
            }
        },
    }
    raw_body = json.dumps(webhook_payload).encode("utf-8")
    signature = hmac.new(
        key=settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    service = WebhookService(db_session)

    # 1. First webhook processing
    is_dup1, event_id1, msg1 = service.process_razorpay_webhook(raw_body=raw_body, signature=signature)
    assert is_dup1 is False
    assert event_id1 == "evt_unique_12345"

    # Verify Order transitioned to PAID
    db_session.refresh(order)
    assert order.status == OrderStatus.PAID.value

    # 2. Second webhook processing (REPLAY / DUPLICATE)
    is_dup2, event_id2, msg2 = service.process_razorpay_webhook(raw_body=raw_body, signature=signature)
    assert is_dup2 is True
    assert event_id2 == "evt_unique_12345"
    assert "already processed" in msg2

    # Verify order state remains unchanged and no duplicate payment records
    from app.repositories.payment_repository import PaymentRepository
    payments = PaymentRepository(db_session).get_by_order_id(order.id)
    assert len(payments) == 1
    assert payments[0].status == PaymentStatus.CAPTURED.value

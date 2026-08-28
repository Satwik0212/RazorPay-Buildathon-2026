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
from app.services.webhook_service import WebhookService
from app.services.payment_service import PaymentService
from app.core.config import settings
from app.core.constants import OrderStatus, PaymentStatus


def test_payment_failure_state_machine(db_session):
    user_m = User(email="m_pf@test.com", password_hash="h", role="MERCHANT")
    user_c = User(email="c_pf@test.com", password_hash="h", role="CUSTOMER")
    db_session.add_all([user_m, user_c])
    db_session.flush()

    merchant = Merchant(user_id=user_m.id, name="Fail Store")
    customer = Customer(user_id=user_c.id)
    db_session.add_all([merchant, customer])
    db_session.flush()

    cart = Cart(customer_id=customer.id, merchant_id=merchant.id, status="ACTIVE")
    db_session.add(cart)
    db_session.flush()

    quote = Quote(
        cart_id=cart.id,
        subtotal=200000,
        discount=0,
        shipping=0,
        tax=0,
        total=200000,
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
        amount=200000,
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
        razorpay_order_id="order_rzp_fail_test",
        amount=200000,
        currency="INR",
        status=OrderStatus.CREATED.value,
        receipt="rcpt_fail_1",
    )
    db_session.add(order)
    db_session.commit()

    webhook_payload = {
        "id": "evt_fail_123",
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_failed_999",
                    "order_id": "order_rzp_fail_test",
                    "amount": 200000,
                    "currency": "INR",
                    "status": "failed",
                    "method": "netbanking",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Payment was cancelled by user.",
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
    service.process_razorpay_webhook(raw_body=raw_body, signature=signature)

    db_session.refresh(order)
    assert order.status == OrderStatus.FAILED.value

    payment_service = PaymentService(db_session)
    status_info = payment_service.get_order_payment_status(order.id)
    assert status_info["status"] == OrderStatus.FAILED.value
    assert status_info["razorpay_payment_id"] == "pay_failed_999"
def test_illegal_state_transition_paid_to_failed(db_session):
    user_m = User(email="m_ill@test.com", password_hash="h", role="MERCHANT")
    user_c = User(email="c_ill@test.com", password_hash="h", role="CUSTOMER")
    db_session.add_all([user_m, user_c])
    db_session.flush()

    merchant = Merchant(user_id=user_m.id, name="Illegal Store")
    customer = Customer(user_id=user_c.id)
    db_session.add_all([merchant, customer])
    db_session.flush()

    cart = Cart(customer_id=customer.id, merchant_id=merchant.id, status="ACTIVE")
    db_session.add(cart)
    db_session.flush()

    order = Order(
        merchant_id=merchant.id,
        customer_id=customer.id,
        cart_id=cart.id,
        authorization_id=uuid.uuid4(),
        razorpay_order_id="order_rzp_illegal_test",
        amount=200000,
        currency="INR",
        status=OrderStatus.PAID.value,
        receipt="rcpt_ill_1",
    )
    db_session.add(order)
    db_session.commit()

    webhook_payload = {
        "id": "evt_ill_123",
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_failed_999",
                    "order_id": "order_rzp_illegal_test",
                    "amount": 200000,
                    "currency": "INR",
                    "status": "failed",
                    "method": "netbanking",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Payment was cancelled by user.",
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
    service.process_razorpay_webhook(raw_body=raw_body, signature=signature)

    db_session.refresh(order)
    assert order.status == OrderStatus.PAID.value, "Order was illegally transitioned from PAID to FAILED!"


import hmac
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
import pytest

from app.models.merchant import User, Merchant
from app.models.customer import Customer
from app.models.product import Product, Inventory
from app.models.cart import Cart
from app.models.quote import Quote
from app.models.authorization import Authorization
from app.models.order import Order
from app.models.payment import Payment
from app.security.authentication import create_access_token
from app.core.config import settings
from app.core.constants import OrderStatus, PaymentStatus, CartStatus
from app.repositories.payment_repository import PaymentRepository


# ==============================================================================
# TRACK G: PAYMENT FAILURE QA
# ==============================================================================

def test_track_g_invalid_payment_signature_verification(db_session, client):
    """
    Track G: Send invalid signature to /api/v1/payments/verify.
    Assert rejected with HTTP 400 Bad Request.
    NOTE: Current implementation raises ValidationError which maps to HTTP 422 instead of HTTP 400.
    """
    u_c = User(email=f"cust_{uuid.uuid4().hex[:6]}@test.com", password_hash="h", role="CUSTOMER")
    u_m = User(email=f"merch_{uuid.uuid4().hex[:6]}@test.com", password_hash="h", role="MERCHANT")
    db_session.add_all([u_c, u_m])
    db_session.flush()

    merch = Merchant(user_id=u_m.id, name="Store Sig Test")
    cust = Customer(user_id=u_c.id)
    db_session.add_all([merch, cust])
    db_session.flush()

    cart = Cart(customer_id=cust.id, merchant_id=merch.id, status=CartStatus.ACTIVE.value)
    db_session.add(cart)
    db_session.flush()

    order = Order(
        merchant_id=merch.id,
        customer_id=cust.id,
        cart_id=cart.id,
        authorization_id=uuid.uuid4(),
        razorpay_order_id=f"order_sig_{uuid.uuid4().hex[:8]}",
        amount=150000,
        currency="INR",
        status=OrderStatus.CREATED.value,
        receipt="rcpt_sig_test",
    )
    db_session.add(order)
    db_session.commit()

    token = create_access_token(user_id=u_c.id, role="CUSTOMER")

    # Send invalid signature
    payload = {
        "razorpay_order_id": order.razorpay_order_id,
        "razorpay_payment_id": "pay_fake_invalid_sig",
        "razorpay_signature": "completely_bogus_signature_hex",
    }

    res = client.post(
        "/api/v1/payments/verify",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    # We record empirical observation: does it return 400 as required or 422?
    assert res.status_code == 400, f"Expected 400 Bad Request for invalid signature, got {res.status_code}: {res.text}"


def test_track_g_payment_failed_webhook(db_session, client):
    """
    Track G: Send payment.failed webhook -> assert order transitions to FAILED.
    """
    u_c = User(email=f"c_fail_{uuid.uuid4().hex[:6]}@test.com", password_hash="h", role="CUSTOMER")
    u_m = User(email=f"m_fail_{uuid.uuid4().hex[:6]}@test.com", password_hash="h", role="MERCHANT")
    db_session.add_all([u_c, u_m])
    db_session.flush()

    merch = Merchant(user_id=u_m.id, name="Store Fail Webhook")
    cust = Customer(user_id=u_c.id)
    db_session.add_all([merch, cust])
    db_session.flush()

    cart = Cart(customer_id=cust.id, merchant_id=merch.id, status=CartStatus.ACTIVE.value)
    db_session.add(cart)
    db_session.flush()

    order = Order(
        merchant_id=merch.id,
        customer_id=cust.id,
        cart_id=cart.id,
        authorization_id=uuid.uuid4(),
        razorpay_order_id=f"order_fail_{uuid.uuid4().hex[:8]}",
        amount=50000,
        currency="INR",
        status=OrderStatus.CREATED.value,
        receipt="rcpt_fail_webhook",
    )
    db_session.add(order)
    db_session.commit()

    webhook_payload = {
        "id": f"evt_fail_{uuid.uuid4().hex[:8]}",
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_failed_{uuid.uuid4().hex[:8]}",
                    "order_id": order.razorpay_order_id,
                    "amount": 50000,
                    "currency": "INR",
                    "status": "failed",
                    "method": "card",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Payment was cancelled or card declined.",
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

    res = client.post(
        "/api/v1/webhooks/razorpay",
        headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"},
        content=raw_body,
    )
    assert res.status_code == 200, f"Webhook failed: {res.text}"

    db_session.refresh(order)
    assert order.status == OrderStatus.FAILED.value, f"Expected order status FAILED, got {order.status}"


# ==============================================================================
# TRACK H: WEBHOOK & IDEMPOTENCY QA
# ==============================================================================

def test_track_h_duplicate_webhook_delivery_and_inventory_idempotency(db_session, client):
    """
    Track H: Webhook & Idempotency QA.
    - Post identical payment.captured event twice with valid HMAC-SHA256 signature.
    - Assert first call captures payment and decrements inventory;
    - Assert second call returns HTTP 200 with idempotent notice without duplicate side effects or inventory double-decrement.
    """
    u_c = User(email=f"c_dup_{uuid.uuid4().hex[:6]}@test.com", password_hash="h", role="CUSTOMER")
    u_m = User(email=f"m_dup_{uuid.uuid4().hex[:6]}@test.com", password_hash="h", role="MERCHANT")
    db_session.add_all([u_c, u_m])
    db_session.flush()

    merch = Merchant(user_id=u_m.id, name="Store Dup Webhook")
    cust = Customer(user_id=u_c.id)
    db_session.add_all([merch, cust])
    db_session.flush()

    # Product with initial inventory of 15
    prod = Product(merchant_id=merch.id, name="Idempotent Item", price=2500, category="gadgets", is_active=True)
    db_session.add(prod)
    db_session.flush()
    inv = Inventory(product_id=prod.id, available_quantity=15)
    db_session.add(inv)
    db_session.flush()

    cart = Cart(customer_id=cust.id, merchant_id=merch.id, status=CartStatus.ACTIVE.value)
    db_session.add(cart)
    db_session.flush()

    purchased_qty = 3
    line_snapshot = [
        {
            "product_id": str(prod.id),
            "name": prod.name,
            "unit_price": prod.price,
            "quantity": purchased_qty,
            "total": prod.price * purchased_qty,
        }
    ]

    quote = Quote(
        cart_id=cart.id,
        subtotal=prod.price * purchased_qty,
        discount=0,
        shipping=0,
        tax=0,
        total=prod.price * purchased_qty,
        currency="INR",
        quote_hash="quote_hash_test",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        line_items_snapshot=line_snapshot,
    )
    db_session.add(quote)
    db_session.flush()

    authorization = Authorization(
        customer_id=cust.id,
        quote_id=quote.id,
        amount=prod.price * purchased_qty,
        currency="INR",
        status="APPROVED",
    )
    db_session.add(authorization)
    db_session.flush()

    razorpay_order_id = f"order_dup_{uuid.uuid4().hex[:8]}"
    order = Order(
        merchant_id=merch.id,
        customer_id=cust.id,
        cart_id=cart.id,
        authorization_id=authorization.id,
        razorpay_order_id=razorpay_order_id,
        amount=prod.price * purchased_qty,
        currency="INR",
        status=OrderStatus.CREATED.value,
        receipt="rcpt_dup_123",
    )
    db_session.add(order)
    db_session.commit()

    razorpay_payment_id = f"pay_dup_{uuid.uuid4().hex[:8]}"
    event_id = f"evt_dup_{uuid.uuid4().hex[:8]}"
    webhook_payload = {
        "id": event_id,
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": razorpay_payment_id,
                    "order_id": razorpay_order_id,
                    "amount": prod.price * purchased_qty,
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

    # FIRST CALL
    res1 = client.post(
        "/api/v1/webhooks/razorpay",
        headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"},
        content=raw_body,
    )
    assert res1.status_code == 200, f"First webhook call failed: {res1.text}"
    body1 = res1.json()
    assert body1["duplicate"] is False, f"Expected duplicate=False, got {body1}"

    # Verify side effects after first call
    db_session.refresh(order)
    db_session.refresh(inv)
    assert order.status == OrderStatus.PAID.value, f"Order status is {order.status}"
    assert inv.available_quantity == 15 - purchased_qty, f"Inventory was {inv.available_quantity}, expected {15 - purchased_qty}"

    payments = PaymentRepository(db_session).get_by_order_id(order.id)
    assert len(payments) == 1, f"Expected 1 payment record, found {len(payments)}"
    assert payments[0].status == PaymentStatus.CAPTURED.value

    # SECOND CALL (DUPLICATE)
    res2 = client.post(
        "/api/v1/webhooks/razorpay",
        headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"},
        content=raw_body,
    )
    assert res2.status_code == 200, f"Second webhook call failed: {res2.text}"
    body2 = res2.json()
    assert body2["duplicate"] is True, f"Expected duplicate=True, got {body2}"
    assert "already processed" in body2["message"].lower() or "idempotent" in body2["message"].lower()

    # Verify no second decrement and no duplicate payment records
    db_session.refresh(order)
    db_session.refresh(inv)
    assert order.status == OrderStatus.PAID.value
    assert inv.available_quantity == 15 - purchased_qty, f"Inventory double decremented! Current: {inv.available_quantity}"
    payments_after = PaymentRepository(db_session).get_by_order_id(order.id)
    assert len(payments_after) == 1, f"Duplicate payment record created! Found {len(payments_after)}"


def test_track_h_duplicate_webhook_delivery_for_payment_failed(db_session, client):
    """
    Track H: Duplicate delivery of payment.failed webhook.
    Assert second call returns HTTP 200 with duplicate=True.
    """
    u_c = User(email=f"c_dup_f_{uuid.uuid4().hex[:6]}@test.com", password_hash="h", role="CUSTOMER")
    u_m = User(email=f"m_dup_f_{uuid.uuid4().hex[:6]}@test.com", password_hash="h", role="MERCHANT")
    db_session.add_all([u_c, u_m])
    db_session.flush()

    merch = Merchant(user_id=u_m.id, name="Store Dup Fail")
    cust = Customer(user_id=u_c.id)
    db_session.add_all([merch, cust])
    db_session.flush()

    cart = Cart(customer_id=cust.id, merchant_id=merch.id, status=CartStatus.ACTIVE.value)
    db_session.add(cart)
    db_session.flush()

    order = Order(
        merchant_id=merch.id,
        customer_id=cust.id,
        cart_id=cart.id,
        authorization_id=uuid.uuid4(),
        razorpay_order_id=f"order_dup_f_{uuid.uuid4().hex[:8]}",
        amount=10000,
        currency="INR",
        status=OrderStatus.CREATED.value,
        receipt="rcpt_dup_f",
    )
    db_session.add(order)
    db_session.commit()

    event_id = f"evt_dup_fail_{uuid.uuid4().hex[:8]}"
    webhook_payload = {
        "id": event_id,
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_dup_f_{uuid.uuid4().hex[:8]}",
                    "order_id": order.razorpay_order_id,
                    "amount": 10000,
                    "currency": "INR",
                    "status": "failed",
                    "method": "card",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Card was declined.",
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

    # Call 1
    res1 = client.post(
        "/api/v1/webhooks/razorpay",
        headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"},
        content=raw_body,
    )
    assert res1.status_code == 200
    assert res1.json()["duplicate"] is False

    # Call 2 (Replay)
    res2 = client.post(
        "/api/v1/webhooks/razorpay",
        headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"},
        content=raw_body,
    )
    assert res2.status_code == 200
    assert res2.json()["duplicate"] is True


def test_track_h_illegal_state_transition_paid_to_failed(db_session, client):
    """
    Track H: Send payment.failed webhook for an order already in PAID state ->
    assert order remains PAID and illegal transition is rejected.
    """
    u_c = User(email=f"c_ill_{uuid.uuid4().hex[:6]}@test.com", password_hash="h", role="CUSTOMER")
    u_m = User(email=f"m_ill_{uuid.uuid4().hex[:6]}@test.com", password_hash="h", role="MERCHANT")
    db_session.add_all([u_c, u_m])
    db_session.flush()

    merch = Merchant(user_id=u_m.id, name="Store Illegal Trans")
    cust = Customer(user_id=u_c.id)
    db_session.add_all([merch, cust])
    db_session.flush()

    cart = Cart(customer_id=cust.id, merchant_id=merch.id, status=CartStatus.ACTIVE.value)
    db_session.add(cart)
    db_session.flush()

    order = Order(
        merchant_id=merch.id,
        customer_id=cust.id,
        cart_id=cart.id,
        authorization_id=uuid.uuid4(),
        razorpay_order_id=f"order_ill_{uuid.uuid4().hex[:8]}",
        amount=10000,
        currency="INR",
        status=OrderStatus.PAID.value,  # Already PAID!
        receipt="rcpt_ill_paid",
    )
    db_session.add(order)
    db_session.commit()

    webhook_payload = {
        "id": f"evt_ill_{uuid.uuid4().hex[:8]}",
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_ill_{uuid.uuid4().hex[:8]}",
                    "order_id": order.razorpay_order_id,
                    "amount": 10000,
                    "currency": "INR",
                    "status": "failed",
                    "method": "netbanking",
                    "error_code": "USER_DROPPED",
                    "error_description": "User cancelled after success.",
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

    res = client.post(
        "/api/v1/webhooks/razorpay",
        headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"},
        content=raw_body,
    )
    assert res.status_code == 200

    db_session.refresh(order)
    assert order.status == OrderStatus.PAID.value, f"Illegal transition allowed! Order status became {order.status}"


def test_track_h_invalid_webhook_signature(client):
    """
    Track H: Test invalid or forged webhook signature.
    Assert rejected with HTTP 400 Bad Request.
    """
    raw_body = json.dumps({"event": "payment.captured", "id": "evt_forged_1"}).encode("utf-8")

    # 1. Tampered signature
    res_bad_sig = client.post(
        "/api/v1/webhooks/razorpay",
        headers={"X-Razorpay-Signature": "bad_hex_digest_value", "Content-Type": "application/json"},
        content=raw_body,
    )
    assert res_bad_sig.status_code == 400, f"Expected 400 for forged webhook signature, got {res_bad_sig.status_code}"

    # 2. Missing signature header
    res_no_sig = client.post(
        "/api/v1/webhooks/razorpay",
        headers={"Content-Type": "application/json"},
        content=raw_body,
    )
    assert res_no_sig.status_code == 400, f"Expected 400 for missing webhook signature header, got {res_no_sig.status_code}"


# ==============================================================================
# TRACKS O & P: SECURITY & ISOLATION QA
# ==============================================================================

def test_tracks_o_p_customer_isolation(db_session, client):
    """
    Tracks O & P: Test Customer A attempting to access Customer B's cart, quote, or order ->
    assert HTTP 403 Forbidden.
    """
    u_c1 = User(email=f"c1_iso_{uuid.uuid4().hex[:6]}@test.com", password_hash="h", role="CUSTOMER")
    u_c2 = User(email=f"c2_iso_{uuid.uuid4().hex[:6]}@test.com", password_hash="h", role="CUSTOMER")
    u_m = User(email=f"m_iso_{uuid.uuid4().hex[:6]}@test.com", password_hash="h", role="MERCHANT")
    db_session.add_all([u_c1, u_c2, u_m])
    db_session.flush()

    merch = Merchant(user_id=u_m.id, name="Iso Store")
    c1 = Customer(user_id=u_c1.id)
    c2 = Customer(user_id=u_c2.id)
    db_session.add_all([merch, c1, c2])
    db_session.flush()

    # Customer B's Cart, Quote, Order
    cart_b = Cart(customer_id=c2.id, merchant_id=merch.id, status=CartStatus.ACTIVE.value)
    db_session.add(cart_b)
    db_session.flush()

    quote_b = Quote(
        cart_id=cart_b.id,
        subtotal=1000,
        discount=0,
        shipping=0,
        tax=0,
        total=1000,
        currency="INR",
        quote_hash="quote_b_hash",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        line_items_snapshot=[],
    )
    db_session.add(quote_b)
    db_session.flush()

    order_b = Order(
        merchant_id=merch.id,
        customer_id=c2.id,
        cart_id=cart_b.id,
        authorization_id=uuid.uuid4(),
        razorpay_order_id=f"order_b_{uuid.uuid4().hex[:8]}",
        amount=1000,
        currency="INR",
        status=OrderStatus.CREATED.value,
        receipt="rcpt_b",
    )
    db_session.add(order_b)
    db_session.commit()

    token_a = create_access_token(user_id=u_c1.id, role="CUSTOMER")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 1. Customer A accessing Customer B's cart
    res_cart = client.get(f"/api/v1/carts/{cart_b.id}", headers=headers_a)
    assert res_cart.status_code == 403, f"Expected 403 for Customer B's cart, got {res_cart.status_code}: {res_cart.text}"

    # 2. Customer A accessing Customer B's quote
    res_quote = client.get(f"/api/v1/quotes/{quote_b.id}", headers=headers_a)
    assert res_quote.status_code == 403, f"Expected 403 for Customer B's quote, got {res_quote.status_code}: {res_quote.text}"

    # 3. Customer A accessing Customer B's order
    res_order = client.get(f"/api/v1/checkout/orders/{order_b.id}", headers=headers_a)
    assert res_order.status_code == 403, f"Expected 403 for Customer B's order, got {res_order.status_code}: {res_order.text}"

    # 4. Customer A accessing Customer B's order payments
    res_order_pay = client.get(f"/api/v1/checkout/orders/{order_b.id}/payments", headers=headers_a)
    assert res_order_pay.status_code == 403, f"Expected 403 for Customer B's order payments, got {res_order_pay.status_code}: {res_order_pay.text}"

    # 5. Customer A accessing Customer B's order payment status
    res_order_stat = client.get(f"/api/v1/orders/{order_b.id}/payment-status", headers=headers_a)
    assert res_order_stat.status_code == 403, f"Expected 403 for Customer B's order payment-status, got {res_order_stat.status_code}: {res_order_stat.text}"


def test_tracks_o_p_merchant_isolation(db_session, client):
    """
    Tracks O & P: Test Merchant A attempting to view or alter Merchant B's products or policy ->
    assert HTTP 403 Forbidden.
    """
    u_m1 = User(email=f"m1_iso_{uuid.uuid4().hex[:6]}@test.com", password_hash="h", role="MERCHANT")
    u_m2 = User(email=f"m2_iso_{uuid.uuid4().hex[:6]}@test.com", password_hash="h", role="MERCHANT")
    db_session.add_all([u_m1, u_m2])
    db_session.flush()

    m1 = Merchant(user_id=u_m1.id, name="Store A")
    m2 = Merchant(user_id=u_m2.id, name="Store B")
    db_session.add_all([m1, m2])
    db_session.flush()

    prod_b = Product(merchant_id=m2.id, name="Merchant B Product", price=5000, category="tech", is_active=True)
    db_session.add(prod_b)
    db_session.flush()
    db_session.add(Inventory(product_id=prod_b.id, available_quantity=10))
    db_session.commit()

    token_m1 = create_access_token(user_id=u_m1.id, role="MERCHANT")
    headers_m1 = {"Authorization": f"Bearer {token_m1}"}

    # 1. Merchant A viewing Merchant B's product
    res_view = client.get(f"/api/v1/products/{prod_b.id}", headers=headers_m1)
    assert res_view.status_code == 403, f"Expected 403 for Merchant B's product view, got {res_view.status_code}: {res_view.text}"

    # 2. Merchant A altering Merchant B's product
    res_alter = client.patch(f"/api/v1/products/{prod_b.id}", headers=headers_m1, json={"price": 100})
    assert res_alter.status_code == 403, f"Expected 403 for Merchant B's product patch, got {res_alter.status_code}: {res_alter.text}"

    # 3. Merchant A altering Merchant B's inventory
    res_inv = client.patch(f"/api/v1/products/{prod_b.id}/inventory", headers=headers_m1, json={"available_quantity": 0})
    assert res_inv.status_code == 403, f"Expected 403 for Merchant B's inventory patch, got {res_inv.status_code}: {res_inv.text}"

    # 4. Merchant A deleting Merchant B's product
    res_del = client.delete(f"/api/v1/products/{prod_b.id}", headers=headers_m1)
    assert res_del.status_code == 403, f"Expected 403 for Merchant B's product delete, got {res_del.status_code}: {res_del.text}"


def test_tracks_o_p_unauthenticated_requests(client):
    """
    Tracks O & P: Test unauthenticated requests to protected endpoints ->
    assert HTTP 401 Unauthorized.
    """
    dummy_id = str(uuid.uuid4())

    protected_endpoints = [
        ("POST", "/api/v1/payments/verify", {"razorpay_order_id": "ord_1", "razorpay_payment_id": "pay_1", "razorpay_signature": "sig"}),
        ("GET", f"/api/v1/carts/{dummy_id}", None),
        ("GET", f"/api/v1/quotes/{dummy_id}", None),
        ("GET", f"/api/v1/checkout/orders/{dummy_id}", None),
        ("GET", f"/api/v1/products/{dummy_id}", None),
        ("GET", "/api/v1/merchant/policy", None),
        ("PUT", "/api/v1/merchant/policy", {"max_autonomous_amount": 1000}),
        ("POST", "/api/v1/merchant/policy/check", {"amount": 100}),
    ]

    for method, endpoint, body in protected_endpoints:
        if method == "GET":
            res = client.get(endpoint)
        elif method == "POST":
            res = client.post(endpoint, json=body or {})
        elif method == "PUT":
            res = client.put(endpoint, json=body or {})
        elif method == "PATCH":
            res = client.patch(endpoint, json=body or {})
        else:
            raise ValueError(f"Unknown method {method}")

        assert res.status_code == 401, f"Expected 401 for unauthenticated {method} {endpoint}, got {res.status_code}: {res.text}"

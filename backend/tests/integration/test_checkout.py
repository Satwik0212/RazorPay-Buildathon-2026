import hmac
import hashlib
import json
import pytest
from app.core.config import settings


def test_end_to_end_checkout_and_webhook_flow(client):
    # 1. Register Merchant
    m_reg = client.post(
        "/api/v1/auth/register",
        json={"email": "e2e_merchant@test.com", "password": "password12345", "role": "MERCHANT"},
    ).json()
    m_token = m_reg["access_token"]
    merchant_id = m_reg["user"]["merchant_id"]

    # 2. Create Product (₹4,999.00 = 499900 paise)
    prod_resp = client.post(
        "/api/v1/products",
        json={
            "name": "E2E Headphones",
            "description": "Premium wireless headphones",
            "category": "headphones",
            "price": 499900,
            "currency": "INR",
            "initial_quantity": 25,
        },
        headers={"Authorization": f"Bearer {m_token}"},
    )
    assert prod_resp.status_code == 201
    product_id = prod_resp.json()["id"]

    # 3. Register Customer
    c_reg = client.post(
        "/api/v1/auth/register",
        json={"email": "e2e_buyer@test.com", "password": "password12345", "role": "CUSTOMER"},
    ).json()
    c_token = c_reg["access_token"]

    # 4. Create Cart
    cart_resp = client.post(
        "/api/v1/carts",
        json={"merchant_id": merchant_id},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert cart_resp.status_code == 201
    cart_id = cart_resp.json()["id"]

    # 5. Add Item to Cart
    add_item_resp = client.post(
        f"/api/v1/carts/{cart_id}/items",
        json={"product_id": product_id, "quantity": 1},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert add_item_resp.status_code == 201

    # 6. Create Quote (Authoritative server-side calculation)
    quote_resp = client.post(
        "/api/v1/quotes",
        json={"cart_id": cart_id},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert quote_resp.status_code == 201
    quote_data = quote_resp.json()
    assert quote_data["total"] == 499900
    quote_id = quote_data["quote_id"]

    # 7. Authorize Quote
    auth_resp = client.post(
        "/api/v1/authorizations",
        json={"quote_id": quote_id},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert auth_resp.status_code == 201
    auth_data = auth_resp.json()
    assert auth_data["status"] == "APPROVED"
    authorization_id = auth_data["authorization_id"]

    # 8. Create Checkout Order
    checkout_resp = client.post(
        "/api/v1/checkout/orders",
        json={"quote_id": quote_id, "authorization_id": authorization_id},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert checkout_resp.status_code == 201
    order_data = checkout_resp.json()
    assert order_data["amount"] == 499900
    assert order_data["status"] == "CREATED"
    order_id = order_data["order_id"]
    rzp_order_id = order_data["razorpay_order_id"]

    # 9. Deliver Verified Razorpay Webhook Callback
    webhook_payload = {
        "id": f"evt_e2e_{order_id}",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_rzp_e2e_{order_id}",
                    "order_id": rzp_order_id,
                    "amount": 499900,
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

    wh_resp = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"},
    )
    assert wh_resp.status_code == 200
    assert wh_resp.json()["status"] == "success"

    # 10. Query Payment Status
    status_resp = client.get(
        f"/api/v1/orders/{order_id}/payment-status",
        headers={"Authorization": f"Bearer {c_token}"}
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "PAID"
    assert status_resp.json()["amount"] == 499900

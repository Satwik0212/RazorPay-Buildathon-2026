import pytest
import uuid
import json
import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from app.models.merchant import User, Merchant
from app.models.customer import Customer
from app.models.product import Product, Inventory
from app.models.order import Order
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.authorization import Authorization
from app.models.quote import Quote
from app.core.constants import OrderStatus, AuthorizationStatus
from app.core.config import settings
from app.services.webhook_service import WebhookService

def generate_signature(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

def test_inventory_decrement_safety(db_session):
    user_m = User(email=f"m_{uuid.uuid4()}@test.com", password_hash="hash", role="MERCHANT")
    user_c = User(email=f"c_{uuid.uuid4()}@test.com", password_hash="hash", role="CUSTOMER")
    db_session.add_all([user_m, user_c])
    db_session.commit()

    merchant = Merchant(user_id=user_m.id, name="Store")
    customer = Customer(user_id=user_c.id)
    db_session.add_all([merchant, customer])
    db_session.commit()

    product = Product(merchant_id=merchant.id, name="Test Item", category="electronics", price=1000, currency="INR")
    db_session.add(product)
    db_session.commit()

    inventory = Inventory(product_id=product.id, available_quantity=10, reserved_quantity=0)
    db_session.add(inventory)
    db_session.commit()

    cart = Cart(merchant_id=merchant.id, customer_id=customer.id)
    db_session.add(cart)
    db_session.commit()
    
    cart_item = CartItem(cart_id=cart.id, product_id=product.id, quantity=3)
    db_session.add(cart_item)
    db_session.commit()

    quote = Quote(
        cart_id=cart.id, subtotal=3000, discount=0, shipping=0, tax=0,
        total=3000, currency="INR", quote_hash="h",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        line_items_snapshot=[{
            "product_id": str(product.id),
            "quantity": 3
        }]
    )
    db_session.add(quote)
    db_session.commit()

    auth = Authorization(
        customer_id=customer.id, quote_id=quote.id,
        amount=3000, currency="INR", status=AuthorizationStatus.APPROVED.value
    )
    db_session.add(auth)
    db_session.commit()

    razorpay_order_id = f"order_{uuid.uuid4()}"
    order = Order(
        merchant_id=merchant.id, customer_id=customer.id, cart_id=cart.id,
        authorization_id=auth.id, razorpay_order_id=razorpay_order_id,
        amount=3000, currency="INR", status=OrderStatus.CREATED.value, receipt="rcpt_1"
    )
    db_session.add(order)
    db_session.commit()

    webhook_service = WebhookService(db_session)

    payload1 = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_{uuid.uuid4()}",
                    "order_id": razorpay_order_id,
                    "amount": 3000,
                    "currency": "INR",
                    "status": "captured"
                }
            }
        }
    }
    raw_body1 = json.dumps(payload1).encode("utf-8")
    sig1 = generate_signature(raw_body1, settings.RAZORPAY_WEBHOOK_SECRET)
    
    webhook_service.process_razorpay_webhook(raw_body1, sig1)
    db_session.refresh(inventory)
    db_session.refresh(order)
    assert order.status == OrderStatus.PAID.value
    assert inventory.available_quantity == 7  

    webhook_service.process_razorpay_webhook(raw_body1, sig1)
    db_session.refresh(inventory)
    assert inventory.available_quantity == 7 

    cart2 = Cart(merchant_id=merchant.id, customer_id=customer.id)
    db_session.add(cart2)
    db_session.commit()
    cart_item2 = CartItem(cart_id=cart2.id, product_id=product.id, quantity=8)
    db_session.add(cart_item2)
    db_session.commit()
    
    quote2 = Quote(
        cart_id=cart2.id, subtotal=8000, discount=0, shipping=0, tax=0,
        total=8000, currency="INR", quote_hash="h2",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        line_items_snapshot=[{
            "product_id": str(product.id),
            "quantity": 8
        }]
    )
    db_session.add(quote2)
    db_session.commit()

    auth2 = Authorization(
        customer_id=customer.id, quote_id=quote2.id,
        amount=8000, currency="INR", status=AuthorizationStatus.APPROVED.value
    )
    db_session.add(auth2)
    db_session.commit()

    rzp_order2 = f"order_{uuid.uuid4()}"
    order2 = Order(
        merchant_id=merchant.id, customer_id=customer.id, cart_id=cart2.id,
        authorization_id=auth2.id, razorpay_order_id=rzp_order2,
        amount=8000, currency="INR", status=OrderStatus.CREATED.value, receipt="rcpt_2"
    )
    db_session.add(order2)
    db_session.commit()

    payload2 = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_{uuid.uuid4()}",
                    "order_id": rzp_order2,
                    "amount": 8000,
                    "currency": "INR",
                    "status": "captured"
                }
            }
        }
    }
    raw_body2 = json.dumps(payload2).encode("utf-8")
    sig2 = generate_signature(raw_body2, settings.RAZORPAY_WEBHOOK_SECRET)
    
    webhook_service.process_razorpay_webhook(raw_body2, sig2)
    db_session.refresh(inventory)
    db_session.refresh(order2)
    
    assert order2.status == OrderStatus.REVIEW_REQUIRED.value
    assert inventory.available_quantity == 7  

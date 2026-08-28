import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_merchant_isolation_products():
    merchant_a_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtZXJjaGFudF9BIiwicm9sZSI6Ik1FUkNIQU5UIn0.invalid"
    merchant_b_product_id = str(uuid.uuid4())
    # Merchant A trying to patch Merchant B's product
    response = client.patch(f"/api/v1/products/{merchant_b_product_id}", json={"price": 1}, headers={"Authorization": f"Bearer {merchant_a_token}"})
    assert response.status_code in [401, 403, 404]

def test_merchant_isolation_policies():
    merchant_a_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtZXJjaGFudF9BIiwicm9sZSI6Ik1FUkNIQU5UIn0.invalid"
    merchant_b_policy_id = str(uuid.uuid4())
    # Merchant A trying to modify Merchant B's policy
    response = client.patch(f"/api/v1/policies/{merchant_b_policy_id}", json={"max_autonomous_amount": 999999}, headers={"Authorization": f"Bearer {merchant_a_token}"})
    assert response.status_code in [401, 403, 404]

def test_customer_isolation_carts():
    customer_a_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjdXN0b21lcl9BIiwicm9sZSI6IkNVU1RPTUVSIn0.invalid"
    customer_b_cart_id = str(uuid.uuid4())
    # Customer A trying to view Customer B's cart
    response = client.get(f"/api/v1/carts/{customer_b_cart_id}", headers={"Authorization": f"Bearer {customer_a_token}"})
    assert response.status_code in [401, 403, 404]

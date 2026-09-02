import uuid
import pytest
from app.main import app
from app.api.v1.buyer.upsell import router as upsell_router

app.include_router(upsell_router, prefix="/api/v1")

def test_upsell_only_shows_merchant_products(client, db_session):
    # Register Merchant A and create products
    unique_email_a = f"merchant_a_{uuid.uuid4().hex[:8]}@example.com"
    reg_a = client.post("/api/v1/auth/register", json={"email": unique_email_a, "password": "Password123!", "role": "MERCHANT"})
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    client.post("/api/v1/products", json={
        "name": "Merchant A Product 1",
        "description": "Desc",
        "category": "shoes",
        "price": 100000,
        "currency": "INR",
        "metadata": {}
    }, headers=headers_a)

    prod_a_res = client.post("/api/v1/products", json={
        "name": "Merchant A Product 2",
        "description": "Desc",
        "category": "shoes",
        "price": 150000,
        "currency": "INR",
        "metadata": {}
    }, headers=headers_a)
    prod_a_id = prod_a_res.json()["id"]

    # Register Merchant B and create products
    unique_email_b = f"merchant_b_{uuid.uuid4().hex[:8]}@example.com"
    reg_b = client.post("/api/v1/auth/register", json={"email": unique_email_b, "password": "Password123!", "role": "MERCHANT"})
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    client.post("/api/v1/products", json={
        "name": "Merchant B Product 1",
        "description": "Desc",
        "category": "shoes",
        "price": 200000,
        "currency": "INR",
        "metadata": {}
    }, headers=headers_b)

    # Test GET suggestions for prod A
    res = client.get(f"/api/v1/buyer/products/{prod_a_id}/suggestions")
    assert res.status_code == 200
    data = res.json()
    assert len(data["upsell"]) == 0
    assert len(data["cross_sell"]) == 0 

    # Add a cross sell product to A
    client.post("/api/v1/products", json={
        "name": "Merchant A Accessory",
        "description": "Desc",
        "category": "accessories",
        "price": 20000,
        "currency": "INR",
        "metadata": {}
    }, headers=headers_a)

    res2 = client.get(f"/api/v1/buyer/products/{prod_a_id}/suggestions")
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2["cross_sell"]) == 1
    assert data2["cross_sell"][0]["name"] == "Merchant A Accessory"
    # Should not include Merchant B's products
    for u in data2["upsell"] + data2["cross_sell"]:
        assert "Merchant B" not in u["name"]

def test_upsell_cart_suggestions(client, db_session):
    # Setup Merchant and Customer
    unique_email_a = f"merchant_{uuid.uuid4().hex[:8]}@example.com"
    reg_a = client.post("/api/v1/auth/register", json={"email": unique_email_a, "password": "Password123!", "role": "MERCHANT"})
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    merch_id = client.get("/api/v1/merchants/me", headers=headers_a).json()["id"]

    customer_email = f"customer_{uuid.uuid4().hex[:8]}@example.com"
    reg_c = client.post("/api/v1/auth/register", json={"email": customer_email, "password": "Password123!", "role": "CUSTOMER"})
    token_c = reg_c.json()["access_token"]
    headers_c = {"Authorization": f"Bearer {token_c}"}

    # Create Products
    p1 = client.post("/api/v1/products", json={"name": "P1", "category": "electronics", "price": 100000, "currency": "INR", "metadata": {}}, headers=headers_a).json()
    p2 = client.post("/api/v1/products", json={"name": "P2 Upsell", "category": "electronics", "price": 150000, "currency": "INR", "metadata": {}}, headers=headers_a).json()
    p3 = client.post("/api/v1/products", json={"name": "P3 Cross", "category": "cases", "price": 20000, "currency": "INR", "metadata": {}}, headers=headers_a).json()

    # Deactivate product and out of stock product
    p4_inactive = client.post("/api/v1/products", json={"name": "P4 Inactive", "category": "cases", "price": 25000, "currency": "INR", "metadata": {}}, headers=headers_a).json()
    client.delete(f"/api/v1/products/{p4_inactive['id']}", headers=headers_a)

    p5_oos = client.post("/api/v1/products", json={"name": "P5 OOS", "category": "electronics", "price": 200000, "currency": "INR", "metadata": {}}, headers=headers_a).json()
    client.patch(f"/api/v1/products/{p5_oos['id']}/inventory", json={"available_quantity": 0}, headers=headers_a)

    # Create Cart
    cart_res = client.post("/api/v1/carts", json={"merchant_id": merch_id}, headers=headers_c)
    cart_id = cart_res.json()["id"]

    # Add item to cart
    client.post(f"/api/v1/carts/{cart_id}/items", json={"product_id": p1["id"], "quantity": 1}, headers=headers_c)

    # Fetch upsell suggestions
    res = client.post(f"/api/v1/buyer/cart/{cart_id}/upsell-suggestions", json={"limit": 5}, headers=headers_c)
    assert res.status_code == 200
    data = res.json()
    
    assert data["data_source"] == "DETERMINISTIC_CATALOGUE_SCORING"
    assert len(data["anchor_product_ids"]) == 1
    assert data["anchor_product_ids"][0] == p1["id"]

    # Upsell should have P2
    assert len(data["upsell"]) == 1
    assert data["upsell"][0]["name"] == "P2 Upsell"

    # Cross-sell should have P3
    assert len(data["cross_sell"]) == 1
    assert data["cross_sell"][0]["name"] == "P3 Cross"

    # Exclude logic check: Add P3 to cart, it should disappear from cross-sell
    client.post(f"/api/v1/carts/{cart_id}/items", json={"product_id": p3["id"], "quantity": 1}, headers=headers_c)
    res2 = client.post(f"/api/v1/buyer/cart/{cart_id}/upsell-suggestions", json={"limit": 5}, headers=headers_c)
    assert len(res2.json()["cross_sell"]) == 0

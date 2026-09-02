import uuid
import pytest


def test_catalogue_search_and_intent_integration(client):
    # 1. Register merchant user
    unique_email = f"merchant_cat_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": "Password123!", "role": "MERCHANT"}
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get merchant profile
    merchant_res = client.get("/api/v1/merchants/me", headers=headers)
    assert merchant_res.status_code == 200

    # 3. Add products to catalogue
    client.post(
        "/api/v1/products",
        json={
            "name": "Sony WH-1000XM5 ANC Headphones",
            "description": "Industry leading wireless noise cancelling headphones with 30hr battery",
            "category": "headphones",
            "price": 2499900,
            "currency": "INR",
            "metadata": {"anc": True, "wireless": True, "battery_hours": 30, "rating": 4.9}
        },
        headers=headers
    )
    client.post(
        "/api/v1/products",
        json={
            "name": "boAt Rockerz 450",
            "description": "Affordable on-ear bluetooth wireless headphones",
            "category": "headphones",
            "price": 149900,
            "currency": "INR",
            "metadata": {"wireless": True, "rating": 4.2}
        },
        headers=headers
    )

    # 4. Parse natural language intent for budget headphones
    intent_res = client.post(
        "/api/v1/buyer/intents",
        json={"text": "I need cheap wireless headphones under ₹2,000"}
    )
    assert intent_res.status_code == 200
    intent_data = intent_res.json()["intent"]
    assert intent_data["category"] == "headphones"
    assert intent_data["max_budget"] == 200000

    # 5. Search catalogue using the structured intent
    search_res = client.post(
        "/api/v1/catalogue/search",
        json={
            "category": intent_data["category"],
            "max_budget": intent_data["max_budget"],
            "requirements": intent_data["requirements"],
            "preferences": intent_data["preferences"],
        }
    )
    assert search_res.status_code == 200
    search_results = search_res.json()["results"]
    assert len(search_results) > 0
    # boAt Rockerz is under ₹2,000, so it should rank top
    assert search_results[0]["name"] == "boAt Rockerz 450"
    assert "budget_compliant" in search_results[0]["matched_constraints"]


def test_merchant_read_isolation_and_soft_delete(client):
    # Register merchant A
    merchant_a = client.post("/api/v1/auth/register", json={"email": f"a_{uuid.uuid4().hex[:8]}@example.com", "password": "Password123!", "role": "MERCHANT"}).json()
    headers_a = {"Authorization": f"Bearer {merchant_a['access_token']}"}

    # Register merchant B
    merchant_b = client.post("/api/v1/auth/register", json={"email": f"b_{uuid.uuid4().hex[:8]}@example.com", "password": "Password123!", "role": "MERCHANT"}).json()
    headers_b = {"Authorization": f"Bearer {merchant_b['access_token']}"}

    # Merchant A creates a product
    prod_a = client.post("/api/v1/products", json={"name": "Product A", "category": "cat", "price": 100, "currency": "INR", "metadata": {}}, headers=headers_a).json()

    # Merchant B creates a product
    prod_b = client.post("/api/v1/products", json={"name": "Product B", "category": "cat", "price": 200, "currency": "INR", "metadata": {}}, headers=headers_b).json()

    # GET /products as Merchant A should only return Product A
    res_a = client.get("/api/v1/products", headers=headers_a).json()
    assert len(res_a["items"]) == 1
    assert res_a["items"][0]["id"] == prod_a["id"]

    # GET /products as Merchant B should only return Product B
    res_b = client.get("/api/v1/products", headers=headers_b).json()
    assert len(res_b["items"]) == 1
    assert res_b["items"][0]["id"] == prod_b["id"]

    # GET /products/{id} as Merchant B for Product A should fail
    get_fail = client.get(f"/api/v1/products/{prod_a['id']}", headers=headers_b)
    assert get_fail.status_code == 403

    # Soft Delete Product A
    client.delete(f"/api/v1/products/{prod_a['id']}", headers=headers_a)

    # GET /products as Merchant A with is_active=True (default) should be empty
    res_a_active = client.get("/api/v1/products", headers=headers_a).json()
    assert len(res_a_active["items"]) == 0

    # GET /products as Merchant A with is_active=False should return Product A
    res_a_inactive = client.get("/api/v1/products?is_active=false", headers=headers_a).json()
    assert len(res_a_inactive["items"]) == 1
    assert res_a_inactive["items"][0]["id"] == prod_a["id"]
    assert res_a_inactive["items"][0]["is_active"] is False

    # Reactivate Product A
    client.patch(f"/api/v1/products/{prod_a['id']}/reactivate", headers=headers_a)
    res_a_reactivated = client.get(f"/api/v1/products/{prod_a['id']}", headers=headers_a).json()
    assert res_a_reactivated["is_active"] is True


def test_inventory_update(client):
    merchant = client.post("/api/v1/auth/register", json={"email": f"inv_{uuid.uuid4().hex[:8]}@example.com", "password": "Password123!", "role": "MERCHANT"}).json()
    headers = {"Authorization": f"Bearer {merchant['access_token']}"}

    prod = client.post("/api/v1/products", json={"name": "Inv Prod", "category": "cat", "price": 100, "currency": "INR", "metadata": {}, "initial_quantity": 10}, headers=headers).json()
    
    # Check initial inventory
    inv = client.get(f"/api/v1/products/{prod['id']}/inventory", headers=headers).json()
    assert inv["available_quantity"] == 10

    # Update inventory
    upd = client.patch(f"/api/v1/products/{prod['id']}/inventory", json={"available_quantity": 50}, headers=headers).json()
    assert upd["available_quantity"] == 50

    # Merchant B cannot update Merchant A's inventory
    merchant_b = client.post("/api/v1/auth/register", json={"email": f"b_{uuid.uuid4().hex[:8]}@example.com", "password": "Password123!", "role": "MERCHANT"}).json()
    headers_b = {"Authorization": f"Bearer {merchant_b['access_token']}"}
    
    fail = client.patch(f"/api/v1/products/{prod['id']}/inventory", json={"available_quantity": 100}, headers=headers_b)
    assert fail.status_code == 403

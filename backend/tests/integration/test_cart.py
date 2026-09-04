import uuid
import pytest
from tests.helpers import create_test_merchant


def register_test_customer(client, email="cart_customer@test.com", password="password12345"):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": "CUSTOMER"},
    )
    assert resp.status_code == 201
    data = resp.json()
    return data["access_token"], data["user"]["customer_id"]


def create_merchant_product(client, merchant_token, name="Test Product", price=199900, quantity=10):
    resp = client.post(
        "/api/v1/products",
        json={
            "name": name,
            "description": f"Description for {name}",
            "category": "electronics",
            "price": price,
            "currency": "INR",
            "initial_quantity": quantity,
        },
        headers={"Authorization": f"Bearer {merchant_token}"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def test_cart_creation_and_idempotency(client, db_session):
    # Setup merchant
    m_reg = create_test_merchant(db_session, "cart_merchant_1@test.com").json()
    m_token = m_reg["access_token"]
    merchant_id = m_reg["user"]["merchant_id"]

    # Setup customer
    c_token, customer_id = register_test_customer(client, "customer_cart_1@test.com")

    # Unauthenticated attempt should fail with 401
    unauth_resp = client.post("/api/v1/carts", json={"merchant_id": merchant_id})
    assert unauth_resp.status_code == 401

    # Authenticated cart creation
    cart_resp = client.post(
        "/api/v1/carts",
        json={"merchant_id": merchant_id},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert cart_resp.status_code == 201
    cart_data = cart_resp.json()
    cart_id = cart_data["id"]
    assert cart_data["status"] == "ACTIVE"
    assert cart_data["customer_id"] == customer_id
    assert cart_data["merchant_id"] == merchant_id
    assert cart_data["items"] == []

    # Calling create_cart again for the same merchant returns the existing active cart
    cart_resp_2 = client.post(
        "/api/v1/carts",
        json={"merchant_id": merchant_id},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert cart_resp_2.status_code == 201
    assert cart_resp_2.json()["id"] == cart_id

    # Retrieve cart via GET /api/v1/carts/{cart_id}
    get_resp = client.get(
        f"/api/v1/carts/{cart_id}",
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == cart_id


def test_add_in_stock_item_to_cart(client, db_session):
    # Merchant setup
    m_reg = create_test_merchant(db_session, "cart_merchant_2@test.com").json()
    m_token = m_reg["access_token"]
    merchant_id = m_reg["user"]["merchant_id"]

    # In-stock product (15 in stock)
    product_id = create_merchant_product(client, m_token, name="Noise Canceling Headphones", price=249900, quantity=15)

    # Customer & Cart setup
    c_token, _ = register_test_customer(client, "customer_cart_2@test.com")
    cart_resp = client.post(
        "/api/v1/carts",
        json={"merchant_id": merchant_id},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    cart_id = cart_resp.json()["id"]

    # Add 2 units of in-stock item
    add_resp = client.post(
        f"/api/v1/carts/{cart_id}/items",
        json={"product_id": product_id, "quantity": 2},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert add_resp.status_code == 201
    cart_data = add_resp.json()
    assert len(cart_data["items"]) == 1
    item = cart_data["items"][0]
    assert item["product_id"] == product_id
    assert item["quantity"] == 2
    assert item["product"]["price"] == 249900


def test_add_out_of_stock_item_rejected_with_insufficient_inventory(client, db_session):
    # Merchant setup
    m_reg = create_test_merchant(db_session, "cart_merchant_3@test.com").json()
    m_token = m_reg["access_token"]
    merchant_id = m_reg["user"]["merchant_id"]

    # Out of stock product (0 in stock)
    oos_product_id = create_merchant_product(client, m_token, name="Sold Out Keyboard", price=59900, quantity=0)

    # Limited stock product (2 in stock)
    limited_product_id = create_merchant_product(client, m_token, name="Limited Mouse", price=19900, quantity=2)

    # Customer & Cart setup
    c_token, _ = register_test_customer(client, "customer_cart_3@test.com")
    cart_resp = client.post(
        "/api/v1/carts",
        json={"merchant_id": merchant_id},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    cart_id = cart_resp.json()["id"]

    # Attempt to add 0-stock product
    add_oos_resp = client.post(
        f"/api/v1/carts/{cart_id}/items",
        json={"product_id": oos_product_id, "quantity": 1},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert add_oos_resp.status_code == 400
    oos_err = add_oos_resp.json()["error"]
    assert oos_err["code"] == "INSUFFICIENT_INVENTORY"
    assert oos_err["details"]["product_id"] == oos_product_id
    assert oos_err["details"]["requested"] == 1
    assert oos_err["details"]["available"] == 0

    # Attempt to add 3 units when only 2 available
    add_exceed_resp = client.post(
        f"/api/v1/carts/{cart_id}/items",
        json={"product_id": limited_product_id, "quantity": 3},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert add_exceed_resp.status_code == 400
    exceed_err = add_exceed_resp.json()["error"]
    assert exceed_err["code"] == "INSUFFICIENT_INVENTORY"
    assert exceed_err["details"]["product_id"] == limited_product_id
    assert exceed_err["details"]["requested"] == 3
    assert exceed_err["details"]["available"] == 2


def test_update_item_quantity_patch(client, db_session):
    # Merchant setup
    m_reg = create_test_merchant(db_session, "cart_merchant_4@test.com").json()
    m_token = m_reg["access_token"]
    merchant_id = m_reg["user"]["merchant_id"]

    # Product with stock = 10
    product_id = create_merchant_product(client, m_token, name="Smart Watch", price=129900, quantity=10)

    # Customer & Cart setup
    c_token, _ = register_test_customer(client, "customer_cart_4@test.com")
    cart_resp = client.post(
        "/api/v1/carts",
        json={"merchant_id": merchant_id},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    cart_id = cart_resp.json()["id"]

    # Add 1 unit
    add_resp = client.post(
        f"/api/v1/carts/{cart_id}/items",
        json={"product_id": product_id, "quantity": 1},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert add_resp.status_code == 201
    item_id = add_resp.json()["items"][0]["id"]

    # Update quantity to 4 via PATCH
    patch_resp = client.patch(
        f"/api/v1/carts/{cart_id}/items/{item_id}",
        json={"quantity": 4},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert patch_resp.status_code == 200
    updated_cart = patch_resp.json()
    assert updated_cart["items"][0]["quantity"] == 4

    # Update quantity exceeding inventory (15 > 10) should fail with 400
    patch_fail_resp = client.patch(
        f"/api/v1/carts/{cart_id}/items/{item_id}",
        json={"quantity": 15},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert patch_fail_resp.status_code == 400
    assert patch_fail_resp.json()["error"]["code"] == "INSUFFICIENT_INVENTORY"


def test_remove_item_delete(client, db_session):
    # Merchant setup
    m_reg = create_test_merchant(db_session, "cart_merchant_5@test.com").json()
    m_token = m_reg["access_token"]
    merchant_id = m_reg["user"]["merchant_id"]

    # Two products
    prod_1 = create_merchant_product(client, m_token, name="USB Cable", price=49900, quantity=20)
    prod_2 = create_merchant_product(client, m_token, name="Power Adapter", price=99900, quantity=20)

    # Customer & Cart setup
    c_token, _ = register_test_customer(client, "customer_cart_5@test.com")
    cart_resp = client.post(
        "/api/v1/carts",
        json={"merchant_id": merchant_id},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    cart_id = cart_resp.json()["id"]

    # Add both items
    client.post(
        f"/api/v1/carts/{cart_id}/items",
        json={"product_id": prod_1, "quantity": 1},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    add_2_resp = client.post(
        f"/api/v1/carts/{cart_id}/items",
        json={"product_id": prod_2, "quantity": 2},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    cart_items = add_2_resp.json()["items"]
    assert len(cart_items) == 2

    item_to_remove = next(i for i in cart_items if i["product_id"] == prod_1)
    item_to_keep = next(i for i in cart_items if i["product_id"] == prod_2)

    # DELETE the item
    del_resp = client.delete(
        f"/api/v1/carts/{cart_id}/items/{item_to_remove['id']}",
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert del_resp.status_code == 200
    remaining_items = del_resp.json()["items"]
    assert len(remaining_items) == 1
    assert remaining_items[0]["id"] == item_to_keep["id"]
    assert remaining_items[0]["product_id"] == prod_2


def test_single_merchant_cart_constraint_validation(client, db_session):
    # Setup Merchant A
    m_a_reg = create_test_merchant(db_session, "merchant_a@test.com").json()
    m_a_token = m_a_reg["access_token"]
    merchant_a_id = m_a_reg["user"]["merchant_id"]
    prod_a_id = create_merchant_product(client, m_a_token, name="Merchant A Product", price=100000, quantity=10)

    # Setup Merchant B
    m_b_reg = create_test_merchant(db_session, "merchant_b@test.com").json()
    m_b_token = m_b_reg["access_token"]
    merchant_b_id = m_b_reg["user"]["merchant_id"]
    prod_b_id = create_merchant_product(client, m_b_token, name="Merchant B Product", price=200000, quantity=10)

    # Customer creates cart for Merchant A
    c_token, _ = register_test_customer(client, "customer_cross_merchant@test.com")
    cart_resp = client.post(
        "/api/v1/carts",
        json={"merchant_id": merchant_a_id},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    cart_id = cart_resp.json()["id"]

    # Add product A to cart A succeeds
    add_a_resp = client.post(
        f"/api/v1/carts/{cart_id}/items",
        json={"product_id": prod_a_id, "quantity": 1},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert add_a_resp.status_code == 201

    # Attempt to add product B (from Merchant B) into Cart A (Merchant A)
    add_b_resp = client.post(
        f"/api/v1/carts/{cart_id}/items",
        json={"product_id": prod_b_id, "quantity": 1},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert add_b_resp.status_code == 422
    err_data = add_b_resp.json()["error"]
    assert err_data["code"] == "VALIDATION_ERROR"
    assert "Cannot add products from a different merchant" in err_data["message"]


def test_cart_customer_isolation(client, db_session):
    # Setup merchant and product
    m_reg = create_test_merchant(db_session, "isolation_merchant@test.com").json()
    m_token = m_reg["access_token"]
    merchant_id = m_reg["user"]["merchant_id"]
    prod_id = create_merchant_product(client, m_token, name="Isolation Item", price=50000, quantity=10)

    # Customer 1 creates cart & adds item
    c1_token, _ = register_test_customer(client, "customer_1_iso@test.com")
    cart_resp = client.post(
        "/api/v1/carts",
        json={"merchant_id": merchant_id},
        headers={"Authorization": f"Bearer {c1_token}"},
    )
    cart_id = cart_resp.json()["id"]
    add_resp = client.post(
        f"/api/v1/carts/{cart_id}/items",
        json={"product_id": prod_id, "quantity": 1},
        headers={"Authorization": f"Bearer {c1_token}"},
    )
    item_id = add_resp.json()["items"][0]["id"]

    # Customer 2 registers
    c2_token, _ = register_test_customer(client, "customer_2_iso@test.com")

    # Customer 2 attempts to GET Customer 1's cart -> 403 Forbidden
    get_resp = client.get(
        f"/api/v1/carts/{cart_id}",
        headers={"Authorization": f"Bearer {c2_token}"},
    )
    assert get_resp.status_code == 403
    assert get_resp.json()["error"]["code"] == "FORBIDDEN"

    # Customer 2 attempts to add item to Customer 1's cart -> 403 Forbidden
    add_attempt = client.post(
        f"/api/v1/carts/{cart_id}/items",
        json={"product_id": prod_id, "quantity": 1},
        headers={"Authorization": f"Bearer {c2_token}"},
    )
    assert add_attempt.status_code == 403

    # Customer 2 attempts to update item in Customer 1's cart -> 403 Forbidden
    patch_attempt = client.patch(
        f"/api/v1/carts/{cart_id}/items/{item_id}",
        json={"quantity": 3},
        headers={"Authorization": f"Bearer {c2_token}"},
    )
    assert patch_attempt.status_code == 403

    # Customer 2 attempts to delete item in Customer 1's cart -> 403 Forbidden
    del_attempt = client.delete(
        f"/api/v1/carts/{cart_id}/items/{item_id}",
        headers={"Authorization": f"Bearer {c2_token}"},
    )
    assert del_attempt.status_code == 403

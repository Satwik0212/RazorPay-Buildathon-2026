from tests.helpers import create_test_merchant
import uuid
import pytest
from httpx import AsyncClient

def test_analytics_overview_and_isolation(client, db_session):
    # 1. Register Primary Merchant
    email1 = f"merchant1_{uuid.uuid4().hex[:8]}@example.com"
    reg1 = create_test_merchant(db_session, email1, "Password123!")
    token1 = reg1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # 2. Add products for primary merchant
    client.post("/api/v1/products", json={"name": "Prod1", "price": 100, "currency": "INR", "category": "cat1"}, headers=headers1)
    client.post("/api/v1/products", json={"name": "Prod2", "price": 200, "currency": "INR", "category": "cat2"}, headers=headers1)
    # Put some inventory
    # ProductCreate defaults to 10 initial inventory, so 2 products = 20 inventory
    prods = client.get("/api/v1/products", headers=headers1).json()["items"]

    # 3. Register Secondary Merchant
    email2 = f"merchant2_{uuid.uuid4().hex[:8]}@example.com"
    reg2 = create_test_merchant(db_session, email2, "Password123!")
    token2 = reg2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # 4. Fetch overview for Primary Merchant
    res1 = client.get("/api/v1/analytics/overview", headers=headers1)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["total_products"] == 2
    assert data1["active_products"] == 2
    assert data1["total_inventory"] == 20
    assert data1["total_categories"] == 2
    assert data1["total_personas"] >= 5
    assert data1["total_recommendations"] == 0

    # 5. Fetch overview for Secondary Merchant
    res2 = client.get("/api/v1/analytics/overview", headers=headers2)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total_products"] == 0
    assert data2["active_products"] == 0
    assert data2["total_inventory"] == 0
    assert data2["total_categories"] == 0
    assert data2["total_personas"] >= 5
    assert data2["total_recommendations"] == 0

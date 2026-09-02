from tests.helpers import create_test_merchant
import uuid
from app.main import app


def test_api_buyer_intent_multiple_inputs(client, db_session):
    # 1. Budget query
    res1 = client.post("/api/v1/buyer/intents", json={"text": "I need a cheap laptop under 50000"})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["intent"]["category"] == "laptop"
    assert data1["intent"]["max_budget"] == 5000000

    # 2. Premium headphones query
    res2 = client.post("/api/v1/buyer/intents", json={"text": "I need ANC headphones under 15k with next day delivery"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["intent"]["category"] == "headphones"
    assert data2["intent"]["max_budget"] == 1500000
    assert "ANC" in data2["intent"]["requirements"]
    assert data2["intent"]["delivery_deadline_days"] == 1

    # Verify results are genuinely different
    assert data1["intent"]["category"] != data2["intent"]["category"]
    assert data1["intent"]["max_budget"] != data2["intent"]["max_budget"]


def test_api_buyer_personas_list_and_create(client, db_session):
    # List personas
    res = client.get("/api/v1/buyer-personas")
    assert res.status_code == 200
    personas = res.json()
    assert len(personas) >= 5
    persona_names = [p["name"] for p in personas]
    assert "Budget Conscious Buyer" in persona_names
    assert "Speed First Buyer" in persona_names

    # Create custom persona
    custom_id = str(uuid.uuid4())
    create_res = client.post(
        "/api/v1/buyer-personas",
        json={
            "name": f"Gamer Buyer {custom_id[:6]}",
            "description": "Needs top tier specs",
            "budget_min": 100000,
            "budget_max": 2500000,
            "priorities": ["performance", "gpu"],
            "urgency": "HIGH",
            "weights": {"quality": 0.50, "metadata": 0.30, "price": 0.10, "delivery": 0.10},
        }
    )
    assert create_res.status_code == 201
    assert create_res.json()["name"] == f"Gamer Buyer {custom_id[:6]}"


def test_api_what_if_analysis(client, db_session):
    # 1. Register merchant to get auth token
    unique_email = f"whatif_{uuid.uuid4().hex[:8]}@test.com"
    m_reg = create_test_merchant(db_session, unique_email, "password12345")
    assert m_reg.status_code == 201
    m_token = m_reg.json()["access_token"]
    merchant_id = m_reg.json()["user"]["merchant_id"]
    headers = {"Authorization": f"Bearer {m_token}"}

    # 2. Verify empty catalogue rejects What-If simulation without fabricating products
    empty_res = client.post(
        "/api/v1/optimization/what-if",
        json={
            "merchant_id": merchant_id,
            "hypothesis": "Test hypothesis on empty catalogue",
            "modifications": {"delivery_days": 2}
        },
        headers=headers
    )
    assert empty_res.status_code == 422
    assert "empty" in empty_res.json()["error"]["message"].lower()

    # 3. Add a real product for the merchant
    prod_res = client.post(
        "/api/v1/products",
        json={
            "name": "Real Test Headphones",
            "description": "Real headphones for what-if test",
            "category": "headphones",
            "price": 299900,
            "currency": "INR",
            "metadata": {"delivery_days": 5, "return_days": 7}
        },
        headers=headers
    )
    assert prod_res.status_code == 201

    # 4. Verify What-If simulation succeeds for merchant with real products
    res = client.post(
        "/api/v1/optimization/what-if",
        json={
            "merchant_id": merchant_id,
            "hypothesis": "Reducing delivery time from 5 days to 2 days increases buyer match rate",
            "modifications": {
                "delivery_days": 2,
                "metadata": {"has_discount": True}
            }
        },
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["hypothesis"] == "Reducing delivery time from 5 days to 2 days increases buyer match rate"
    assert "baseline_metrics" in data
    assert "simulated_metrics" in data
    assert "delta_percentage" in data
    assert data["baseline_metrics"]["metric_type"] == "SIMULATED RESULT"

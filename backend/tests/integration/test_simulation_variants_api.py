from tests.helpers import create_test_merchant
import pytest
import uuid
from fastapi.testclient import TestClient

def test_multi_scenario_simulation_produces_variation(client, db_session):
    """Verify running multiple scenarios for one persona does not simply return identical scenario inputs/results."""
    # 1. Register a merchant
    unique_email = f"merchant_{uuid.uuid4().hex[:8]}@example.com"
    reg = create_test_merchant(db_session, unique_email, "Password123!")
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Add some diverse products so variation is possible
    client.post("/api/v1/products", json={"name": "Cheap watch", "category": "test", "price": 400000, "currency": "INR", "metadata": {"delivery_days": 1}}, headers=headers)
    client.post("/api/v1/products", json={"name": "Expensive watch", "category": "test", "price": 4000000, "currency": "INR", "metadata": {"delivery_days": 5}}, headers=headers)
    client.post("/api/v1/products", json={"name": "Premium spec watch", "category": "test", "price": 2000000, "currency": "INR", "metadata": {"delivery_days": 3, "specifications": "yes", "warranty": "yes"}}, headers=headers)

    # 3. Run simulation with FEATURE persona and count=5
    sim_res = client.post("/api/v1/optimization/simulations", json={
        "scenario_count": 5,
        "buyer_profiles": ["FEATURE"]
    }, headers=headers)
    
    assert sim_res.status_code == 200
    data = sim_res.json()
    assert data["scenario_count"] == 5
    results = data["results"]
    assert len(results) == 5
    
    # Verify persona_name includes variant tags
    persona_names = [r["persona_name"] for r in results]
    assert "FEATURE:feature_budget_low" in persona_names
    assert "FEATURE:feature_budget_mid" in persona_names
    
    # Check that not all selected products/scores are identical
    selected_ids = set(r["selected_product_id"] for r in results if r["selected_product_id"])
    scores = set(r["score"] for r in results)
    
    # In a catalogue with 3 varied products, 5 varying intents should result in >1 distinct product or score
    assert len(selected_ids) > 1 or len(scores) > 1

def test_explicit_intent_overrides_but_count_still_runs(client, db_session):
    """Verify that explicit intent remains respected and exactly scenario_count results are returned."""
    # 1. Register a merchant
    unique_email = f"merchant_{uuid.uuid4().hex[:8]}@example.com"
    reg = create_test_merchant(db_session, unique_email, "Password123!")
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Run simulation with explicit intent
    sim_res = client.post("/api/v1/optimization/simulations", json={
        "scenario_count": 3,
        "buyer_profiles": ["BUDGET"],
        "intent": {
            "max_budget": 123456,
            "requirements": ["explicit_req"]
        }
    }, headers=headers)
    
    assert sim_res.status_code == 200
    data = sim_res.json()
    assert data["scenario_count"] == 3
    results = data["results"]
    assert len(results) == 3
    
    # Verify persona names use explicit tag
    for i, r in enumerate(results):
        assert r["persona_name"] == f"BUDGET:explicit_{i + 1}"

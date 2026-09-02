from tests.helpers import create_test_merchant
import uuid
import pytest

def test_catalogue_mutation_changes_simulation_outcomes(client, db_session):
    # 1. Register merchant user
    unique_email = f"merchant_sim_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = create_test_merchant(db_session, unique_email, "Password123!")
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    merchant_id = client.get("/api/v1/merchants/me", headers=headers).json()["id"]

    # 2. Create a product with poor metrics
    p1_res = client.post(
        "/api/v1/products",
        json={
            "name": "Standard Delivery Headphones",
            "description": "Takes a long time to deliver and no returns.",
            "category": "headphones",
            "price": 500000, # 5000 INR
            "currency": "INR",
            "metadata": {"delivery_days": 10, "return_days": 0, "rating": 3.0}
        },
        headers=headers
    )
    assert p1_res.status_code == 201
    product_id = p1_res.json()["id"]

    # 3. Run baseline simulation for SPEED persona
    sim_baseline = client.post(
        "/api/v1/optimization/simulations",
        json={
            "merchant_id": merchant_id,
            "scenario_count": 1,
            "buyer_profiles": ["SPEED"],
        },
        headers=headers
    )
    assert sim_baseline.status_code == 200
    baseline_results = sim_baseline.json()["results"]
    assert len(baseline_results) == 1
    baseline_score = baseline_results[0]["score"]
    
    # Assert there is friction about delivery days for SPEED buyer
    assert any(f["reason"] in ("DELIVERY_UNCLEAR", "MISSING_FEATURE", "DELIVERY_TOO_SLOW", "DELIVERY_UNKNOWN") for f in baseline_results[0]["frictions"])

    # 4. Mutate the catalogue to fix the friction (improving delivery)
    update_res = client.patch(
        f"/api/v1/products/{product_id}",
        json={
            "description": "Fast delivery headphones with quick shipping.",
            "metadata": {"delivery_days": 1, "return_days": 30, "rating": 4.5, "fast_delivery": True}
        },
        headers=headers
    )
    assert update_res.status_code == 200

    # 5. Run simulation again
    sim_mutated = client.post(
        "/api/v1/optimization/simulations",
        json={
            "merchant_id": merchant_id,
            "scenario_count": 1,
            "buyer_profiles": ["SPEED"],
        },
        headers=headers
    )
    assert sim_mutated.status_code == 200
    mutated_results = sim_mutated.json()["results"]
    assert len(mutated_results) == 1
    mutated_score = mutated_results[0]["score"]

    # Assert friction is gone
    assert not any(f["reason"] == "DELIVERY_UNCLEAR" for f in mutated_results[0]["frictions"])

    # Assert outcome changed and improved
    assert mutated_score > baseline_score

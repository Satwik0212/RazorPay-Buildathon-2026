import uuid
import pytest


def test_simulation_api_end_to_end(client):
    # 1. Register merchant user
    unique_email = f"merchant_sim_{uuid.uuid4().hex[:8]}@example.com"
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
    merchant_id = merchant_res.json()["id"]

    # 3. Create products in database
    p1_res = client.post(
        "/api/v1/products",
        json={
            "name": "Budget Wireless Earbuds",
            "description": "Standard wireless audio buds",
            "category": "headphones",
            "price": 199900,
            "currency": "INR",
            "metadata": {"delivery_days": 5, "rating": 4.1, "return_days": 7}
        },
        headers=headers
    )
    assert p1_res.status_code == 201

    p2_res = client.post(
        "/api/v1/products",
        json={
            "name": "Flagship Pro ANC Headphones",
            "description": "Ultra fast delivery noise cancelling headphones with 30-day returns",
            "category": "headphones",
            "price": 899900,
            "currency": "INR",
            "metadata": {"delivery_days": 1, "rating": 4.9, "warranty": True, "return_days": 30, "anc": True}
        },
        headers=headers
    )
    assert p2_res.status_code == 201

    # 4. Run multi-persona simulation
    sim_res = client.post(
        "/api/v1/optimization/simulations",
        json={
            "merchant_id": merchant_id,
            "scenario_count": 4,
            "buyer_profiles": ["BUDGET", "SPEED", "QUALITY", "BALANCED"],
        },
        headers=headers
    )
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["status"] == "COMPLETED"
    assert sim_data["scenario_count"] == 4
    assert len(sim_data["results"]) == 4
    assert "summary_metrics" in sim_data
    assert sim_data["summary_metrics"]["metric_type"] == "SIMULATED RESULT"

    # 5. Fetch explainable recommendations
    recs_res = client.get(
        "/api/v1/optimization/recommendations",
        headers=headers
    )
    assert recs_res.status_code == 200
    recs = recs_res.json()
    assert isinstance(recs, list)

    # 6. Run what-if optimization experiment
    what_if_res = client.post(
        "/api/v1/optimization/what-if",
        json={
            "merchant_id": merchant_id,
            "hypothesis": "Offering 1-day express delivery across all products improves speed-buyer matches",
            "modifications": {
                "delivery_days": 1,
                "metadata": {"express_shipping": True}
            }
        },
        headers=headers
    )
    assert what_if_res.status_code == 200
    what_if_data = what_if_res.json()
    assert "delta_percentage" in what_if_data
    assert what_if_data["baseline_metrics"]["metric_type"] == "SIMULATED RESULT"

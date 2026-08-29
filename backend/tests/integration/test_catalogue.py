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

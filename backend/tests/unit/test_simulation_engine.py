import pytest
from app.simulation.engine import simulation_engine


def test_simulation_engine_ranked_selection():
    merchant_id = "00000000-0000-0000-0000-000000000001"
    catalogue = [
        {
            "id": "p_cheap",
            "name": "Budget Laptop",
            "price": 3000000,
            "is_active": True,
            "product_metadata": {"delivery_days": 5, "rating": 3.8}
        },
        {
            "id": "p_fast_premium",
            "name": "Pro Gaming Laptop",
            "price": 7500000,
            "is_active": True,
            "product_metadata": {"delivery_days": 1, "rating": 4.9, "warranty": True, "return_days": 30}
        },
    ]

    # Speed buyer simulation
    speed_weights = {"delivery": 0.60, "quality": 0.20, "price": 0.20}
    res_speed = simulation_engine.run_simulation(
        merchant_id=merchant_id,
        persona_weights=speed_weights,
        intent={"max_budget": 8000000},
        catalogue=catalogue,
        persona_name="Speed Buyer"
    )

    assert res_speed["constraints_satisfied"] is True
    assert res_speed["selected_product_id"] == "p_fast_premium"
    assert res_speed["rankings"][0]["product_id"] == "p_fast_premium"
    assert res_speed["rankings"][1]["product_id"] == "p_cheap"

    # Budget buyer simulation with low budget
    budget_weights = {"price": 0.70, "delivery": 0.15, "quality": 0.15}
    res_budget = simulation_engine.run_simulation(
        merchant_id=merchant_id,
        persona_weights=budget_weights,
        intent={"max_budget": 4000000},
        catalogue=catalogue,
        persona_name="Budget Buyer"
    )

    assert res_budget["constraints_satisfied"] is True
    assert res_budget["selected_product_id"] == "p_cheap"


def test_simulation_engine_all_rejected_when_hard_constraints_fail():
    merchant_id = "00000000-0000-0000-0000-000000000001"
    catalogue = [
        {"id": "p1", "name": "Laptop 1", "price": 5000000, "is_active": True, "metadata": {}},
        {"id": "p2", "name": "Laptop 2", "price": 6000000, "is_active": True, "metadata": {}},
    ]

    # Buyer has max budget 2000000 (both laptops exceed)
    res = simulation_engine.run_simulation(
        merchant_id=merchant_id,
        persona_weights={"price": 0.5, "quality": 0.5},
        intent={"max_budget": 2000000},
        catalogue=catalogue,
        persona_name="Tight Budget Buyer"
    )

    assert res["constraints_satisfied"] is False
    assert res["selected_product_id"] is None
    assert "NO_MATCHING_PRODUCTS" in res["reason_codes"]
    assert len(res["frictions"]) >= 2
    assert all(f["reason"] == "PRICE_MISMATCH" for f in res["frictions"])

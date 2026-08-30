import pytest
import uuid
from app.simulation.scoring import ProductScorer
from app.simulation.friction import FrictionDetector, FrictionReason
from app.simulation.engine import simulation_engine
from app.services.optimization.what_if_service import what_if_service
from app.services.optimization.recommendation_service import recommendation_service


def test_identical_inputs_produce_identical_simulation():
    merchant_id = "00000000-0000-0000-0000-000000000001"
    persona = {"price": 0.5, "delivery": 0.5}
    intent = {"max_budget": 500000}
    catalogue = [
        {"id": "p_1", "name": "Prod 1", "price": 400000, "is_active": True, "metadata": {"delivery_days": 3}},
        {"id": "p_2", "name": "Prod 2", "price": 450000, "is_active": True, "metadata": {"delivery_days": 1}},
    ]

    result1 = simulation_engine.run_simulation(merchant_id, persona, intent, catalogue)
    result2 = simulation_engine.run_simulation(merchant_id, persona, intent, catalogue)

    assert result1["selected_product_id"] == result2["selected_product_id"]
    assert [r["product_id"] for r in result1["rankings"]] == [r["product_id"] for r in result2["rankings"]]
    assert [r["score"] for r in result1["rankings"]] == [r["score"] for r in result2["rankings"]]


def test_persona_scoring_different_priorities():
    # Price sensitive persona prefers cheap product
    budget_persona = {"price": 0.8, "delivery": 0.2}
    # Speed sensitive persona prefers fast delivery
    speed_persona = {"price": 0.1, "delivery": 0.9}

    cheap_slow_prod = {"id": "p_1", "price": 100000, "metadata": {"delivery_days": 7}}
    expensive_fast_prod = {"id": "p_2", "price": 800000, "metadata": {"delivery_days": 1}}

    # Budget score evaluation
    b_score1 = ProductScorer.calculate_score(cheap_slow_prod, budget_persona)
    b_score2 = ProductScorer.calculate_score(expensive_fast_prod, budget_persona)
    assert b_score1 > b_score2

    # Speed score evaluation
    s_score1 = ProductScorer.calculate_score(cheap_slow_prod, speed_persona)
    s_score2 = ProductScorer.calculate_score(expensive_fast_prod, speed_persona)
    assert s_score2 > s_score1


def test_budget_constraints_friction():
    intent = {"max_budget": 500000}
    over_budget_product = {"price": 600000, "is_active": True}
    in_budget_product = {"price": 450000, "is_active": True}

    frictions_over = FrictionDetector.detect_hard_constraints(over_budget_product, intent)
    assert FrictionReason.PRICE_MISMATCH in frictions_over

    frictions_in = FrictionDetector.detect_hard_constraints(in_budget_product, intent)
    assert FrictionReason.PRICE_MISMATCH not in frictions_in


def test_soft_friction_detection():
    speed_weights = {"delivery": 0.6, "price": 0.1}
    product_no_delivery = {"name": "Test Item", "description": "Good item with lots of details here", "metadata": {}}
    product_with_delivery = {"name": "Test Item", "description": "Good item with lots of details here", "metadata": {"delivery_days": 2}}

    soft_frictions_missing = FrictionDetector.detect_soft_friction(product_no_delivery, speed_weights)
    assert FrictionReason.DELIVERY_UNCLEAR in soft_frictions_missing

    soft_frictions_present = FrictionDetector.detect_soft_friction(product_with_delivery, speed_weights)
    assert FrictionReason.DELIVERY_UNCLEAR not in soft_frictions_present


def test_what_if_delta_calculation():
    merchant_id = "00000000-0000-0000-0000-000000000001"
    persona = {"price": 0.2, "delivery": 0.8}
    intent = {"max_budget": 1000000}

    original_catalogue = [
        {"id": "p_1", "name": "Prod 1", "price": 500000, "is_active": True, "metadata": {"delivery_days": 7}},
        {"id": "p_2", "name": "Prod 2", "price": 500000, "is_active": True, "metadata": {"delivery_days": 5}},
    ]

    modified_catalogue = [
        {"id": "p_1", "name": "Prod 1", "price": 500000, "is_active": True, "metadata": {"delivery_days": 1}},
        {"id": "p_2", "name": "Prod 2", "price": 500000, "is_active": True, "metadata": {"delivery_days": 5}},
    ]

    result = what_if_service.compare(merchant_id, persona, intent, original_catalogue, modified_catalogue)

    assert result["delta"]["outcome_changed"] is True
    assert result["delta"]["baseline_selected"] == "p_2"
    assert result["delta"]["proposed_selected"] == "p_1"
    assert result["delta"]["score_delta"] > 0


def test_recommendation_generation():
    merchant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    p1 = uuid.UUID("00000000-0000-0000-0000-000000000002")
    p2 = uuid.UUID("00000000-0000-0000-0000-000000000003")

    events = [
        {"product_id": str(p1), "reason": FrictionReason.DELIVERY_UNCLEAR.value, "count": 40},
        {"product_id": str(p2), "reason": FrictionReason.PRICE_MISMATCH.value, "count": 20},
    ]

    from unittest.mock import MagicMock
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    recs = recommendation_service.generate_recommendations(mock_db, merchant_id, events)
    assert len(recs) == 2

    assert recs[0].type == "DELIVERY_CLARITY"
    assert recs[0].action_data["friction_count"] == 40
    assert recs[0].product_id == p1

    assert recs[1].type == "PRICE_COMPETITIVENESS"
    assert recs[1].product_id == p2

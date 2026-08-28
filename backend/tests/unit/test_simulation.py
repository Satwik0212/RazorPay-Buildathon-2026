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
    intent = {"max_budget": 5000}
    catalogue = [
        {"id": "p_1", "price": 4000, "is_active": True, "metadata": {"delivery_days": 3}},
        {"id": "p_2", "price": 4500, "is_active": True, "metadata": {"delivery_days": 1}},
    ]
    
    result1 = simulation_engine.run_simulation(merchant_id, persona, intent, catalogue)
    result2 = simulation_engine.run_simulation(merchant_id, persona, intent, catalogue)
    
    assert result1.selected_product == result2.selected_product
    assert [r.product_id for r in result1.rankings] == [r.product_id for r in result2.rankings]
    assert [r.score for r in result1.rankings] == [r.score for r in result2.rankings]


def test_persona_scoring():
    persona = {"price": 0.8, "delivery": 0.2} 
    product1 = {"id": "p_1", "price": 1000, "metadata": {"delivery_days": 7}} 
    product2 = {"id": "p_2", "price": 500000, "metadata": {"delivery_days": 1}}
    
    score1 = ProductScorer.calculate_score(product1, persona)
    score2 = ProductScorer.calculate_score(product2, persona)
    
    assert score1 > score2


def test_budget_constraints_friction():
    intent = {"max_budget": 5000}
    product = {"price": 6000, "is_active": True}
    
    frictions = FrictionDetector.detect_hard_constraints(product, intent)
    assert FrictionReason.PRICE_MISMATCH in frictions


def test_what_if_delta_calculation():
    merchant_id = "00000000-0000-0000-0000-000000000001"
    persona = {"price": 0.5, "delivery": 0.5}
    intent = {"max_budget": 1000000}
    
    original_catalogue = [
        {"id": "p_1", "price": 500000, "is_active": True, "metadata": {"delivery_days": 7}},
        {"id": "p_2", "price": 500000, "is_active": True, "metadata": {"delivery_days": 6}},
    ]
    
    modified_catalogue = [
        {"id": "p_1", "price": 500000, "is_active": True, "metadata": {"delivery_days": 2}},
        {"id": "p_2", "price": 500000, "is_active": True, "metadata": {"delivery_days": 6}},
    ]
    
    result = what_if_service.compare(merchant_id, persona, intent, original_catalogue, modified_catalogue)
    
    assert result["delta"]["outcome_changed"] == True
    assert result["delta"]["baseline_selected"] == "p_2" 
    assert result["delta"]["proposed_selected"] == "p_1"


def test_recommendation_generation():
    events = [
        {"product_id": "00000000-0000-0000-0000-000000000002", "reason": FrictionReason.DELIVERY_UNCLEAR.value, "count": 40},
        {"product_id": "00000000-0000-0000-0000-000000000003", "reason": FrictionReason.PRICE_MISMATCH.value, "count": 20}
    ]
    
    recs = recommendation_service.generate_recommendations(uuid.UUID("00000000-0000-0000-0000-000000000001"), events)
    assert len(recs) == 2
    
    assert recs[0].type == "DELIVERY_CLARITY"
    assert recs[0].action_data["friction_count"] == 40
    
    assert recs[1].type == "PRICE_COMPETITIVENESS"

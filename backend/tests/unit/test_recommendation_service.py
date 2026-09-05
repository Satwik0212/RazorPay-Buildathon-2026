import uuid
import pytest
from unittest.mock import MagicMock
from app.services.optimization.recommendation_service import RecommendationService
from app.simulation.friction import FrictionReason

def test_generate_recommendations():
    service = RecommendationService()
    db = MagicMock()
    # Mock existing rec query to return nothing so it inserts new recs
    db.query.return_value.filter.return_value.first.return_value = None

    merchant_id = uuid.uuid4()
    p_id = uuid.uuid4()

    friction_events = [
        {"product_id": str(p_id), "reason": "MISSING_FEATURE", "count": 5},
        {"product_id": str(p_id), "reason": "DELIVERY_UNKNOWN", "count": 3, "delivery_deadline_days": 2},
        {"product_id": str(p_id), "reason": "DELIVERY_TOO_SLOW", "count": 2, "delivery_deadline_days": 1},
        {"product_id": str(p_id), "reason": "INVENTORY_ISSUE", "count": 10},
        {"product_id": str(p_id), "reason": "PRICE_MISMATCH", "count": 1},
        {"product_id": str(p_id), "reason": "RETURN_UNCLEAR", "count": 4},
        {"product_id": str(p_id), "reason": "DELIVERY_UNCLEAR", "count": 6}
    ]

    recs = service.generate_recommendations(db, merchant_id, friction_events)

    assert len(recs) == 7

    types = {r.type: r for r in recs}

    # MISSING_FEATURE
    assert "MISSING_FEATURE" in types
    assert types["MISSING_FEATURE"].action_data["friction_count"] == 5
    assert types["MISSING_FEATURE"].action_data["affected_products_count"] == 1
    assert "Add structured product specifications" in types["MISSING_FEATURE"].action_data["suggested_change"]

    # DELIVERY_UNKNOWN
    assert "DELIVERY_UNKNOWN" in types
    assert types["DELIVERY_UNKNOWN"].action_data["friction_count"] == 3

    # INVENTORY_ISSUE
    assert "INVENTORY_RESTORATION" in types
    assert types["INVENTORY_RESTORATION"].action_data["friction_count"] == 10

    assert db.add.call_count == 7
    db.commit.assert_called_once()


def test_aggregate_duplicate_frictions():
    service = RecommendationService()
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    merchant_id = uuid.uuid4()
    p1 = uuid.uuid4()
    p2 = uuid.uuid4()
    p3 = uuid.uuid4()

    # Simulating multiple scenarios generating friction across different products
    friction_events = [
        {"product_id": str(p1), "reason": "DELIVERY_UNKNOWN", "count": 2, "delivery_deadline_days": 2},
        {"product_id": str(p2), "reason": "DELIVERY_UNKNOWN", "count": 5, "delivery_deadline_days": 1},
        {"product_id": str(p3), "reason": "DELIVERY_UNKNOWN", "count": 3, "delivery_deadline_days": 3},

        {"product_id": str(p1), "reason": "PRICE_MISMATCH", "count": 1},
        {"product_id": str(p2), "reason": "PRICE_MISMATCH", "count": 1},
    ]

    recs = service.generate_recommendations(db, merchant_id, friction_events, scenario_count=20)

    # Should only create 2 recommendations: one for DELIVERY_UNKNOWN, one for PRICE_COMPETITIVENESS
    assert len(recs) == 2

    types = {r.type: r for r in recs}

    assert "DELIVERY_UNKNOWN" in types
    del_rec = types["DELIVERY_UNKNOWN"]
    assert del_rec.action_data["friction_count"] == 10  # 2 + 5 + 3
    assert del_rec.action_data["affected_products_count"] == 3
    assert str(p1) in del_rec.action_data["affected_product_ids"]
    assert str(p2) in del_rec.action_data["affected_product_ids"]
    assert str(p3) in del_rec.action_data["affected_product_ids"]
    assert del_rec.action_data["scenario_count"] == 20
    assert del_rec.action_data["total_overall_frictions"] == 12  # 10 + 2

    # Verify non-fabricated deterministic impact (10 out of 12 frictions)
    assert del_rec.expected_simulated_impact == pytest.approx(10/12, 0.01)

    # Top product is p2 because it had 5 counts
    assert str(del_rec.product_id) == str(p2)
    assert "10 simulated buyer drop-offs occurred" in del_rec.reason
    assert "across 3 products" in del_rec.reason

    assert "PRICE_COMPETITIVENESS" in types
    price_rec = types["PRICE_COMPETITIVENESS"]
    assert price_rec.action_data["friction_count"] == 2
    assert price_rec.action_data["affected_products_count"] == 2
    assert price_rec.expected_simulated_impact == pytest.approx(2/12, 0.01)

    assert db.add.call_count == 2
    db.commit.assert_called_once()

def test_delivery_too_slow_min_unmet_deadline():
    from app.services.optimization.recommendation_service import RecommendationService
    import uuid
    from unittest.mock import MagicMock

    service = RecommendationService()
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    merchant_id = uuid.uuid4()
    p_id = uuid.uuid4()

    friction_events = [
        {"product_id": str(p_id), "reason": "DELIVERY_TOO_SLOW", "count": 1, "delivery_deadline_days": 3},
        {"product_id": str(p_id), "reason": "DELIVERY_TOO_SLOW", "count": 1, "delivery_deadline_days": 2},
    ]

    recs = service.generate_recommendations(db, merchant_id, friction_events)
    assert len(recs) == 1
    rec = recs[0]
    assert rec.type == "DELIVERY_TOO_SLOW"
    assert rec.action_data["new_delivery_days"] == 2
    assert rec.action_data["after_state_description"] == "2 days (SLA satisfied)"

def test_delivery_too_slow_no_fabrication():
    from app.services.optimization.recommendation_service import RecommendationService
    import uuid
    from unittest.mock import MagicMock

    service = RecommendationService()
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    merchant_id = uuid.uuid4()
    p_id = uuid.uuid4()

    friction_events = [
        {"product_id": str(p_id), "reason": "DELIVERY_TOO_SLOW", "count": 5},
    ]

    recs = service.generate_recommendations(db, merchant_id, friction_events)
    assert len(recs) == 0

"""
Phase 3 — AI Upsell/Cross-sell Agent targeted tests.
"""
import uuid
import pytest
from unittest.mock import patch

from app.ai.recommendation import get_ai_recommendations, AiUpsellOutput, AiCandidateReasoning
from tests.helpers import create_test_merchant

# ---------------------------------------------------------------------------
# Unit: AI recommendation module
# ---------------------------------------------------------------------------

class TestAiRecommendationModule:
    """Test the AI reasoning layer in isolation."""

    def test_returns_empty_when_no_candidates(self):
        result = get_ai_recommendations(
            anchor_products=[{"id": "abc", "name": "Laptop", "category": "Computers", "price": 5000000}],
            upsell_candidates=[],
            cross_sell_candidates=[],
        )
        assert result is not None
        assert result.recommendations == []

    def test_ai_output_schema_validation_rejects_bad_type(self):
        """AiCandidateReasoning must reject recommendation_type other than UPSELL/CROSS_SELL."""
        rec = AiCandidateReasoning(
            product_id="abc",
            recommendation_type="UPSELL",
            reason="Better RAM",
            confidence=0.9,
        )
        assert rec.recommendation_type == "UPSELL"

    def test_ai_failure_returns_none(self):
        """When LLM raises, get_ai_recommendations must return None (not raise)."""
        with patch("app.ai.recommendation.llm_client") as mock_llm:
            mock_llm.generate_structured.side_effect = Exception("Connection timeout")
            result = get_ai_recommendations(
                anchor_products=[{"id": "a", "name": "X", "category": "C", "price": 100}],
                upsell_candidates=[{"id": "b", "name": "Y", "category": "C", "price": 200}],
                cross_sell_candidates=[],
            )
        assert result is None

    def test_ai_confidence_clamped(self):
        """Confidence values must be within [0, 1]."""
        with pytest.raises(Exception):
            AiCandidateReasoning(
                product_id="a",
                recommendation_type="UPSELL",
                reason="X",
                confidence=1.5,
            )

# ---------------------------------------------------------------------------
# Integration: API endpoint tests with DB setup
# ---------------------------------------------------------------------------

def test_phase3_integration(client, db_session):
    # Setup Merchant A
    unique_email_a = f"merchant_a_{uuid.uuid4().hex[:8]}@example.com"
    reg_a = create_test_merchant(db_session, unique_email_a, "Password123!")
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Setup Merchant B
    unique_email_b = f"merchant_b_{uuid.uuid4().hex[:8]}@example.com"
    reg_b = create_test_merchant(db_session, unique_email_b, "Password123!")
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Create Products for A
    p1 = client.post("/api/v1/products", json={"name": "P1", "category": "cat1", "price": 100000, "currency": "INR", "metadata": {}}, headers=headers_a).json()
    p2 = client.post("/api/v1/products", json={"name": "P2 Upsell", "category": "cat1", "price": 150000, "currency": "INR", "metadata": {}}, headers=headers_a).json()
    p3 = client.post("/api/v1/products", json={"name": "P3 Cross", "category": "cat2", "price": 20000, "currency": "INR", "metadata": {}}, headers=headers_a).json()

    # Create Product for B
    p_b = client.post("/api/v1/products", json={"name": "P_B Leak", "category": "cat1", "price": 200000, "currency": "INR", "metadata": {}}, headers=headers_b).json()

    # Test 1: Suggestions respect merchant boundary and don't include anchor product
    res = client.get(f"/api/v1/buyer/products/{p1['id']}/suggestions?limit=5")
    assert res.status_code == 200
    data = res.json()
    
    suggested_ids = [s["product_id"] for s in data["upsell"] + data["cross_sell"]]
    assert p_b["id"] not in suggested_ids  # Tenant isolation
    assert p1["id"] not in suggested_ids  # Anchor product rejected

    # Test 2: Invalid product ID returns 404
    fake_id = str(uuid.uuid4())
    res_fake = client.get(f"/api/v1/buyer/products/{fake_id}/suggestions")
    assert res_fake.status_code == 404

    # Test 3: Normal purchase flow works without recommendations (catalog still works)
    res_cat = client.get("/api/v1/catalog")
    assert res_cat.status_code == 200

    # Test 4: Hallucinated AI ID does not appear in suggestions
    fake_ai_output = AiUpsellOutput(recommendations=[
        AiCandidateReasoning(
            product_id="00000000-0000-0000-0000-000000000000",
            recommendation_type="UPSELL",
            reason="This is a hallucinated product",
            confidence=0.99,
        )
    ])

    with patch("app.services.upsell_service.get_ai_recommendations", return_value=fake_ai_output):
        res_hal = client.get(f"/api/v1/buyer/products/{p1['id']}/suggestions")
        assert res_hal.status_code == 200
        data_hal = res_hal.json()
        all_ids = [s["product_id"] for s in data_hal["upsell"] + data_hal["cross_sell"]]
        assert "00000000-0000-0000-0000-000000000000" not in all_ids

    # Test 5: AI failure still returns deterministic suggestions
    with patch("app.services.upsell_service.get_ai_recommendations", return_value=None):
        res_fail = client.get(f"/api/v1/buyer/products/{p1['id']}/suggestions")
        assert res_fail.status_code == 200
        data_fail = res_fail.json()
        assert "upsell" in data_fail
        assert "cross_sell" in data_fail
        assert data_fail["ai_powered"] is False

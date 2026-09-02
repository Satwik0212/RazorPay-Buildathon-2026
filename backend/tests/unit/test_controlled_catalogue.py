"""
Controlled mini-catalogue simulation tests.
Verifies that the simulation engine produces logically defensible results
with a known, small product catalogue where outcomes can be manually predicted.
"""
import pytest
from app.simulation.engine import simulation_engine
from app.api.v1.optimization.simulations import SCENARIO_VARIANTS, PERSONA_PROFILE_MAP


# Controlled mini-catalogue with deliberately varied attributes
MINI_CATALOGUE = [
    {
        "id": "prod_A", "name": "Budget Audio Cable",
        "description": "High quality braided audio cable with gold plated connectors and shielded wiring for superior sound quality",
        "category": "Audio", "price": 34900, "currency": "INR",
        "is_active": True, "available_quantity": 100,
        "product_metadata": {"delivery_days": 1, "rating": 4.5, "warranty": True, "return_days": 30, "discount_percent": 10},
    },
    {
        "id": "prod_B", "name": "Mid-Range Speaker",
        "description": "Wireless speaker",
        "category": "Audio", "price": 499900, "currency": "INR",
        "is_active": True, "available_quantity": 100,
        "product_metadata": {"delivery_days": 7},
    },
    {
        "id": "prod_C", "name": "Premium Headphones",
        "description": "Noise cancelling premium headphones with active noise cancellation, 40mm drivers, Bluetooth 5.3, and 30 hour battery life",
        "category": "Audio", "price": 2000000, "currency": "INR",
        "is_active": True, "available_quantity": 0,  # OUT OF STOCK
        "product_metadata": {"delivery_days": 1, "rating": 4.9, "warranty": True, "return_days": 30, "premium": True},
    },
    {
        "id": "prod_D", "name": "Pro Studio Monitor",
        "description": "Professional studio reference monitor with flat frequency response and premium build quality",
        "category": "Audio", "price": 1000000, "currency": "INR",
        "is_active": True, "available_quantity": 5,  # LOW STOCK
        "product_metadata": {"delivery_days": 2, "rating": 4.7, "warranty": True, "return_days": 14, "premium": True},
    },
]


class TestInventoryHardConstraint:
    """Verify that inventory=0 always produces INVENTORY_ISSUE and prevents selection."""

    def test_zero_stock_product_is_never_selected(self):
        """Product C (stock=0) must never be the selected product."""
        for persona in PERSONA_PROFILE_MAP:
            weights = PERSONA_PROFILE_MAP[persona]
            for variant in SCENARIO_VARIANTS[persona]:
                label, max_budget, requirements, deadline = variant
                intent = {"max_budget": max_budget, "requirements": requirements}
                if deadline:
                    intent["delivery_deadline_days"] = deadline

                res = simulation_engine.run_simulation(
                    "test_merchant", weights, intent, MINI_CATALOGUE, f"{persona}:{label}"
                )
                assert res["selected_product_id"] != "prod_C", \
                    f"{persona}:{label} selected zero-stock product C"

    def test_zero_stock_generates_inventory_issue_friction(self):
        """Product C should always generate INVENTORY_ISSUE friction."""
        res = simulation_engine.run_simulation(
            "test", PERSONA_PROFILE_MAP["FEATURE"],
            {"max_budget": 5000000}, MINI_CATALOGUE, "test"
        )
        prod_c_frictions = [f for f in res["frictions"] if f["product_id"] == "prod_C"]
        assert any(f["reason"] == "INVENTORY_ISSUE" for f in prod_c_frictions)

    def test_low_stock_product_can_be_selected(self):
        """Product D (stock=5) should be selectable when it's the best candidate."""
        # QUALITY persona with high budget — D should win over A due to quality weight
        res = simulation_engine.run_simulation(
            "test", PERSONA_PROFILE_MAP["QUALITY"],
            {"max_budget": 5000000}, MINI_CATALOGUE, "quality_test"
        )
        assert res["selected_product_id"] == "prod_D"


class TestBudgetHardConstraint:
    """Verify that budget filtering works correctly."""

    def test_product_above_budget_is_rejected(self):
        """Product B (₹4,999) should be rejected when budget is ₹3,000."""
        res = simulation_engine.run_simulation(
            "test", PERSONA_PROFILE_MAP["BUDGET"],
            {"max_budget": 300000}, MINI_CATALOGUE, "tight_budget"
        )
        prod_b_frictions = [f for f in res["frictions"] if f["product_id"] == "prod_B"]
        assert any(f["reason"] == "PRICE_MISMATCH" for f in prod_b_frictions)

    def test_product_within_budget_passes(self):
        """Product A (₹349) should pass when budget is ₹5,000."""
        res = simulation_engine.run_simulation(
            "test", PERSONA_PROFILE_MAP["BUDGET"],
            {"max_budget": 500000}, MINI_CATALOGUE, "moderate_budget"
        )
        # A should be in the candidates (passed hard constraints)
        passed_ids = [r["product_id"] for r in res["rankings"] if r.get("passed")]
        assert "prod_A" in passed_ids


class TestPersonaDifferentiation:
    """Verify that different personas select different products when the catalogue allows it."""

    def test_quality_prefers_high_quality_product(self):
        """QUALITY persona should select prod_D (highest quality score among in-stock)."""
        res = simulation_engine.run_simulation(
            "test", PERSONA_PROFILE_MAP["QUALITY"],
            {"max_budget": 5000000}, MINI_CATALOGUE, "quality_test"
        )
        assert res["selected_product_id"] == "prod_D"

    def test_speed_prefers_fast_delivery(self):
        """SPEED persona should prefer prod_A (1-day delivery)."""
        res = simulation_engine.run_simulation(
            "test", PERSONA_PROFILE_MAP["SPEED"],
            {"max_budget": 5000000, "delivery_deadline_days": 1}, MINI_CATALOGUE, "speed_test"
        )
        assert res["selected_product_id"] == "prod_A"


class TestDeterminism:
    """Verify that identical inputs always produce identical outputs."""

    def test_repeated_runs_produce_identical_results(self):
        """Running the same simulation 5 times should produce byte-identical results."""
        results = []
        for _ in range(5):
            res = simulation_engine.run_simulation(
                "determinism_test", PERSONA_PROFILE_MAP["FEATURE"],
                {"max_budget": 1500000}, MINI_CATALOGUE, "determinism"
            )
            results.append((res["selected_product_id"], res["score"], len(res["frictions"])))

        assert all(r == results[0] for r in results)

    def test_all_variants_produce_same_result_on_repeat(self):
        """Each variant should produce the same result when run twice."""
        for persona in PERSONA_PROFILE_MAP:
            weights = PERSONA_PROFILE_MAP[persona]
            for variant in SCENARIO_VARIANTS[persona]:
                label, max_budget, requirements, deadline = variant
                intent = {"max_budget": max_budget, "requirements": requirements}
                if deadline:
                    intent["delivery_deadline_days"] = deadline

                r1 = simulation_engine.run_simulation("test", weights, intent, MINI_CATALOGUE, label)
                r2 = simulation_engine.run_simulation("test", weights, intent, MINI_CATALOGUE, label)
                assert r1["selected_product_id"] == r2["selected_product_id"], \
                    f"{persona}:{label} not deterministic"
                assert r1["score"] == r2["score"]


class TestFrictionAggregation:
    """Verify friction counting math."""

    def test_friction_count_matches_products_evaluated(self):
        """Total friction signals should be traceable to individual product evaluations."""
        res = simulation_engine.run_simulation(
            "test", PERSONA_PROFILE_MAP["FEATURE"],
            {"max_budget": 5000000}, MINI_CATALOGUE, "friction_test"
        )
        # Each friction should have a product_id
        for f in res["frictions"]:
            assert "product_id" in f
            assert f["product_id"] in ["prod_A", "prod_B", "prod_C", "prod_D"]

    def test_zero_stock_product_counted_once_per_run(self):
        """Product C should generate exactly 1 INVENTORY_ISSUE per simulation run."""
        res = simulation_engine.run_simulation(
            "test", PERSONA_PROFILE_MAP["FEATURE"],
            {"max_budget": 5000000}, MINI_CATALOGUE, "count_test"
        )
        inv_issues_for_c = [f for f in res["frictions"]
                           if f["product_id"] == "prod_C" and f["reason"] == "INVENTORY_ISSUE"]
        assert len(inv_issues_for_c) == 1


class TestScenarioVariantSemantics:
    """Verify that variant labels match their actual constraints."""

    def test_feature_budget_ordering(self):
        """feature_budget_low < feature_budget_mid < feature_budget_high."""
        f_variants = SCENARIO_VARIANTS["FEATURE"]
        low = next(v for v in f_variants if v[0] == "feature_budget_low")
        mid = next(v for v in f_variants if v[0] == "feature_budget_mid")
        high = next(v for v in f_variants if v[0] == "feature_budget_high")
        assert low[1] < mid[1] < high[1]

    def test_all_personas_have_five_variants(self):
        """Each persona should have exactly 5 scenario variants."""
        for persona in ["FEATURE", "BUDGET", "SPEED", "QUALITY", "BALANCED"]:
            assert len(SCENARIO_VARIANTS[persona]) == 5

    def test_speed_variants_all_have_deadlines(self):
        """All SPEED variants should have delivery deadline constraints."""
        for variant in SCENARIO_VARIANTS["SPEED"]:
            label, _, _, deadline = variant
            assert deadline is not None, f"SPEED variant {label} missing delivery deadline"

    def test_no_duplicate_variants_within_persona(self):
        """No two variants within a persona should have identical constraints."""
        for persona, variants in SCENARIO_VARIANTS.items():
            intents = set()
            for v in variants:
                key = (v[1], tuple(v[2]), v[3])
                assert key not in intents, f"{persona} has duplicate variant: {v[0]}"
                intents.add(key)

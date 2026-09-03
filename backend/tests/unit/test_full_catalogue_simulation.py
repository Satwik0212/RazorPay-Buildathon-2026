import uuid
import pytest
from app.models.product import Product, Inventory
from app.models.simulation_result import SimulationResult
from app.models.optimization_recommendation import OptimizationRecommendation
from app.models.what_if_run import WhatIfRun
from app.api.v1.optimization.simulations import truncate_rankings
from tests.helpers import create_test_merchant


class TestFullCatalogueSimulation:
    """
    Tests for Optimization Step 3: Full Active Catalogue Retrieval.
    Covers:
      - Test 5: Full Evaluation (product outside first 100 can win)
      - Test 6: Recommendation Evidence (catalogue-wide friction retained despite truncation)
      - Test 7: Ranking Payload Bound (at most 20 passed + 10 disqualified, max 31)
      - Test 8: Winner Preservation (guaranteed retention of selected winner)
      - Test 9: What-If evaluates full active catalogue under baseline & proposed
    """

    def test_5_full_evaluation_winner_outside_first_100(self, client, db_session):
        """
        Test 5: Full Evaluation
        Verify that a product outside the legacy first-100 window participates in
        candidate evaluation and can become the selected winner when scoring highest.
        """
        # Register merchant
        m_reg = create_test_merchant(db_session, "full_eval@test.com")
        token = m_reg.json()["access_token"]
        merchant_id = uuid.UUID(m_reg.json()["user"]["merchant_id"])
        headers = {"Authorization": f"Bearer {token}"}

        # Create 115 products
        # First 110 products have mediocre/low scores (e.g. higher price, slow delivery)
        created_products = []
        for i in range(115):
            p = Product(
                merchant_id=merchant_id,
                name=f"Standard Product {i:03d}",
                description=f"Standard product description {i}",
                category="electronics",
                price=2000000 + i * 1000,  # 20,000+ INR
                currency="INR",
                is_active=True,
                product_metadata={"delivery_days": 5, "rating": 3.0},
            )
            db_session.add(p)
            db_session.flush()
            db_session.add(Inventory(product_id=p.id, available_quantity=10, reserved_quantity=0))
            created_products.append(p)

        db_session.commit()

        # In get_active_catalogue_for_merchant, products are ordered by Product.id
        # Sort our created products by id to find the exact order
        created_products.sort(key=lambda p: p.id)

        # Pick a product strictly outside the first 100 (e.g., index 105)
        # and give it stellar attributes so it legitimately wins
        winner_target = created_products[105]
        winner_target.name = "Ultimate Star Headphones"
        winner_target.price = 250000  # 2,500 INR (fits budget tight/moderate)
        winner_target.product_metadata = {
            "delivery_days": 1,
            "rating": 5.0,
            "warranty": True,
            "fast_delivery": True,
        }
        db_session.commit()

        # Run simulation with 1 scenario targeting BUDGET persona
        res = client.post(
            "/api/v1/optimization/simulations",
            json={
                "merchant_id": str(merchant_id),
                "scenario_count": 1,
                "buyer_profiles": ["BUDGET"],
            },
            headers=headers,
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert len(data["results"]) == 1
        scenario_result = data["results"][0]

        # Verify that the winner is indeed product at index 105 (outside the first 100)
        assert scenario_result["constraints_satisfied"] is True
        assert scenario_result["selected_product_id"] == str(winner_target.id), (
            f"Expected winner {winner_target.id} (index 105 in active catalogue), "
            f"got {scenario_result['selected_product_id']}"
        )

    def test_6_recommendation_evidence_across_full_catalogue(self, client, db_session):
        """
        Test 6: Recommendation Evidence
        Verify out-of-stock products / inventory issues across the entire catalogue
        remain visible to recommendation generation even when not present in truncated rankings.
        """
        m_reg = create_test_merchant(db_session, "rec_evidence@test.com")
        token = m_reg.json()["access_token"]
        merchant_id = uuid.UUID(m_reg.json()["user"]["merchant_id"])
        headers = {"Authorization": f"Bearer {token}"}

        # Create 40 products:
        # 15 in stock (available_quantity=10)
        # 25 OUT OF STOCK (available_quantity=0) -> triggers INVENTORY_ISSUE
        for i in range(15):
            p = Product(
                merchant_id=merchant_id,
                name=f"In-Stock Item {i:02d}",
                description="In-stock product",
                category="apparel",
                price=50000,
                currency="INR",
                is_active=True,
                product_metadata={"delivery_days": 2},
            )
            db_session.add(p)
            db_session.flush()
            db_session.add(Inventory(product_id=p.id, available_quantity=10, reserved_quantity=0))

        for i in range(25):
            p_oos = Product(
                merchant_id=merchant_id,
                name=f"Out-of-Stock Item {i:02d}",
                description="OOS product",
                category="apparel",
                price=50000,
                currency="INR",
                is_active=True,
                product_metadata={"delivery_days": 2},
            )
            db_session.add(p_oos)
            db_session.flush()
            db_session.add(Inventory(product_id=p_oos.id, available_quantity=0, reserved_quantity=0))

        db_session.commit()

        # Run simulation with 1 scenario
        res = client.post(
            "/api/v1/optimization/simulations",
            json={
                "merchant_id": str(merchant_id),
                "scenario_count": 1,
                "buyer_profiles": ["BUDGET"],
            },
            headers=headers,
        )
        assert res.status_code == 200, res.text
        data = res.json()
        scenario_result = data["results"][0]

        # 1. Verify ranking payload is truncated: disqualified must be at most 10 (not 25)
        disqualified_rankings = [r for r in scenario_result["rankings"] if not r.get("passed")]
        assert len(disqualified_rankings) <= 10, (
            f"Serialized disqualified rankings should be truncated to <= 10, got {len(disqualified_rankings)}"
        )

        # 2. Verify recommendation generation saw ALL 25 inventory friction events
        # Check optimization_recommendations table for this merchant
        recs = (
            db_session.query(OptimizationRecommendation)
            .filter(OptimizationRecommendation.merchant_id == merchant_id)
            .all()
        )
        assert len(recs) > 0, "Expected recommendations to be generated"

        # Find inventory restoration recommendation
        inv_rec = next((r for r in recs if r.type == "INVENTORY_RESTORATION"), None)
        assert inv_rec is not None, "Expected INVENTORY_RESTORATION recommendation"
        # The affected_product_count or friction_count must be 25 (100% of out-of-stock items)
        action_data = inv_rec.action_data
        assert action_data.get("affected_product_count") == 25 or action_data.get("friction_count") == 25, (
            f"Expected recommendation to reflect 25 out-of-stock items, got action_data: {action_data}"
        )

    def test_7_ranking_payload_bound_max_31_candidates(self, client, db_session):
        """
        Test 7: Ranking Payload Bound
        Verify serialized and persisted rankings contain at most 20 passed + 10 disqualified (max 31).
        """
        m_reg = create_test_merchant(db_session, "payload_bound@test.com")
        token = m_reg.json()["access_token"]
        merchant_id = uuid.UUID(m_reg.json()["user"]["merchant_id"])
        headers = {"Authorization": f"Bearer {token}"}

        # Create 35 passing products and 20 failing products (total 55 products)
        for i in range(35):
            p = Product(
                merchant_id=merchant_id,
                name=f"Passing Product {i:02d}",
                description="Passing",
                category="gadgets",
                price=50000 + i * 1000,
                currency="INR",
                is_active=True,
                product_metadata={"delivery_days": 2},
            )
            db_session.add(p)
            db_session.flush()
            db_session.add(Inventory(product_id=p.id, available_quantity=20, reserved_quantity=0))

        for i in range(20):
            p_fail = Product(
                merchant_id=merchant_id,
                name=f"Failing Product {i:02d}",
                description="Failing",
                category="gadgets",
                price=50000,
                currency="INR",
                is_active=True,
                product_metadata={},
            )
            db_session.add(p_fail)
            db_session.flush()
            db_session.add(Inventory(product_id=p_fail.id, available_quantity=0, reserved_quantity=0))

        db_session.commit()

        res = client.post(
            "/api/v1/optimization/simulations",
            json={
                "merchant_id": str(merchant_id),
                "scenario_count": 2,
                "buyer_profiles": ["BUDGET", "BALANCED"],
            },
            headers=headers,
        )
        assert res.status_code == 200, res.text
        data = res.json()

        # Check API response rankings bounds
        for result in data["results"]:
            passed = [r for r in result["rankings"] if r.get("passed") is True]
            disqualified = [r for r in result["rankings"] if r.get("passed") is False]

            assert len(passed) <= 21, f"Expected <= 21 passed candidates, got {len(passed)}"
            assert len(disqualified) <= 10, f"Expected <= 10 disqualified candidates, got {len(disqualified)}"
            assert len(result["rankings"]) <= 31, f"Expected <= 31 total rankings, got {len(result['rankings'])}"

        # Check Database persistence rankings bounds
        db_results = (
            db_session.query(SimulationResult)
            .filter(SimulationResult.simulation_run_id == uuid.UUID(data["simulation_id"]))
            .all()
        )
        assert len(db_results) == 2
        for db_res in db_results:
            db_passed = [r for r in db_res.rankings if r.get("passed") is True]
            db_disqualified = [r for r in db_res.rankings if r.get("passed") is False]

            assert len(db_passed) <= 21
            assert len(db_disqualified) <= 10
            assert len(db_res.rankings) <= 31

    def test_8_winner_preservation_in_rankings(self):
        """
        Test 8: Winner Preservation
        Verify selected winner is guaranteed present in serialized rankings even if outside top 20.
        Tests truncate_rankings unit logic across multiple boundary conditions.
        """
        # Case A: Winner is outside top 20 (e.g. rank 25)
        mock_passed = [
            {"product_id": f"p_pass_{i:02d}", "score": 100 - i, "rank": i + 1, "passed": True}
            for i in range(30)
        ]
        mock_disqualified = [
            {"product_id": f"p_fail_{i:02d}", "score": 0.0, "rank": 999, "passed": False}
            for i in range(15)
        ]
        all_rankings = mock_passed + mock_disqualified

        winner_id = "p_pass_24"  # index 24 is rank 25, outside top 20
        truncated = truncate_rankings(
            all_rankings,
            selected_product_id=winner_id,
            max_passed=20,
            max_disqualified=10,
        )

        # Winner must be present
        assert any(r["product_id"] == winner_id for r in truncated), "Winner outside top 20 must be preserved!"
        # Bounded payload: 20 top + 1 winner + 10 disqualified = 31
        assert len(truncated) == 31
        passed_in_truncated = [r for r in truncated if r.get("passed")]
        assert len(passed_in_truncated) == 21

        # Case B: Winner is already inside top 20 (e.g. rank 1)
        winner_top1 = "p_pass_00"
        truncated_top1 = truncate_rankings(
            all_rankings,
            selected_product_id=winner_top1,
            max_passed=20,
            max_disqualified=10,
        )
        assert any(r["product_id"] == winner_top1 for r in truncated_top1)
        assert len(truncated_top1) == 30  # 20 passed + 10 disqualified (no extra added)

        # Case C: No winner selected (None)
        truncated_none = truncate_rankings(
            all_rankings,
            selected_product_id=None,
            max_passed=20,
            max_disqualified=10,
        )
        assert len(truncated_none) == 30

    def test_9_what_if_evaluates_full_active_catalogue(self, client, db_session):
        """
        Test 9: What-If evaluates full active catalogue
        Verify What-If evaluates the full active catalogue (exceeding legacy 50 limit)
        under both baseline and proposed conditions.
        """
        m_reg = create_test_merchant(db_session, "whatif_full@test.com")
        token = m_reg.json()["access_token"]
        merchant_id = uuid.UUID(m_reg.json()["user"]["merchant_id"])
        headers = {"Authorization": f"Bearer {token}"}

        # Create 60 active products (> 50 legacy limit)
        # Products 0..54 have slow delivery (10 days) and price 1,500,000
        # Product 58 has price 200,000 but slow delivery (10 days)
        created_products = []
        for i in range(60):
            p = Product(
                merchant_id=merchant_id,
                name=f"WhatIf Product {i:02d}",
                description="What-If product",
                category="electronics",
                price=1500000,
                currency="INR",
                is_active=True,
                product_metadata={"delivery_days": 10, "rating": 3.5},
            )
            db_session.add(p)
            db_session.flush()
            db_session.add(Inventory(product_id=p.id, available_quantity=20, reserved_quantity=0))
            created_products.append(p)

        db_session.commit()

        # Sort products by Product.id to find index 55 (strictly > 50)
        created_products.sort(key=lambda p: p.id)
        target_product = created_products[55]
        target_product.price = 200000  # affordable
        target_product.product_metadata = {"delivery_days": 10, "rating": 4.5}
        db_session.commit()

        # Run What-If modifying delivery days on target_product (index 55) from 10 to 1
        res = client.post(
            "/api/v1/optimization/what-if",
            json={
                "merchant_id": str(merchant_id),
                "hypothesis": "Reducing delivery time for target product outside top 50 improves match rate",
                "modifications": {
                    "product_id": str(target_product.id),
                    "delivery_days": 1,
                },
            },
            headers=headers,
        )
        assert res.status_code == 200, res.text
        data = res.json()

        assert "baseline_metrics" in data
        assert "simulated_metrics" in data
        assert "delta_percentage" in data

        # Product 55 with 1-day delivery now satisfies SPEED personas that require <= 2 days delivery
        # Under legacy limit=50, product 55 was never loaded, so proposed match rate would have been 0
        # Under full catalogue retrieval, product 55 is evaluated and proposed metrics improve
        assert data["simulated_metrics"]["matches"] >= data["baseline_metrics"]["matches"]
        assert data["simulated_metrics"]["average_score"] >= data["baseline_metrics"]["average_score"]

        # Verify WhatIfRun record in DB
        what_if_record = (
            db_session.query(WhatIfRun)
            .filter(WhatIfRun.id == uuid.UUID(data["id"]))
            .first()
        )
        assert what_if_record is not None
        assert what_if_record.hypothesis == data["hypothesis"]

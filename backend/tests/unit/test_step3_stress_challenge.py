import copy
import os
import uuid
from typing import List, Dict, Any
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.product import Product, Inventory
from app.models.merchant import Merchant
from app.models.simulation_run import SimulationRun
from app.models.simulation_result import SimulationResult
from app.models.buyer_persona import BuyerPersona
from app.repositories.product_repository import ProductRepository
from app.services.product_service import ProductService
from app.simulation.engine import simulation_engine
from app.simulation.friction import FrictionDetector, FrictionReason
from app.api.v1.optimization.simulations import truncate_rankings
from app.services.optimization.what_if_service import what_if_service
from tests.helpers import create_test_merchant


class TestStep3StressChallenge:
    """
    Challenger Empirical Stress Verification Suite for Step 3:
    Full Active Catalogue Retrieval.

    Edge Case A: Empty catalogue (merchant with 0 active products).
    Edge Case B: Winner outside top 20 (ranks 500 and 1500) preserved in truncate_rankings.
    Edge Case C: Inventory signal differentiation (0 -> INVENTORY_ISSUE, >0 -> pass, None -> pre-Step 3 contract).
    Edge Case D: Determinism verification across 2,977 active products (3 consecutive runs).
    """

    # -------------------------------------------------------------------------
    # EDGE CASE A: Empty Catalogue
    # -------------------------------------------------------------------------

    def test_edge_case_a1_simulation_endpoint_empty_catalogue(self, client, db_session):
        """
        Verify that POST /api/v1/optimization/simulations completes gracefully
        when a merchant has 0 active products.
        """
        # Register a brand new merchant with zero products
        m_reg = create_test_merchant(db_session, "empty_sim@test.com")
        token = m_reg.json()["access_token"]
        merchant_id = uuid.UUID(m_reg.json()["user"]["merchant_id"])
        headers = {"Authorization": f"Bearer {token}"}

        res = client.post(
            "/api/v1/optimization/simulations",
            json={
                "merchant_id": str(merchant_id),
                "scenario_count": 3,
                "buyer_profiles": ["BUDGET", "SPEED"],
            },
            headers=headers,
        )

        assert res.status_code == 200, f"Expected 200 OK on empty catalogue, got {res.status_code}: {res.text}"
        data = res.json()

        assert data["status"] == "COMPLETED"
        assert data["scenario_count"] == 3

        # Summary metrics validation
        metrics = data["summary_metrics"]
        assert metrics["buyers_simulated"] == 3
        assert metrics["successful_matches"] == 0
        assert metrics["failed_matches"] == 3
        assert metrics["constraint_satisfaction_rate"] == 0.0
        assert metrics["average_score"] == 0.0
        assert metrics["friction_distribution"] == {}

        # Scenario results validation
        assert len(data["results"]) == 3
        for result in data["results"]:
            assert result["selected_product_id"] is None
            assert result["score"] == 0.0
            assert result["constraints_satisfied"] is False
            assert "NO_MATCHING_PRODUCTS" in result["reason_codes"]
            assert result["rankings"] == []
            assert result["frictions"] == []

        # Persistence verification: SimulationRun and SimulationResult saved cleanly
        sim_run = db_session.query(SimulationRun).filter(SimulationRun.id == uuid.UUID(data["simulation_id"])).first()
        assert sim_run is not None
        assert sim_run.scenario_count == 3
        assert len(sim_run.results) == 3
        for r in sim_run.results:
            assert r.selected_product_id is None
            assert r.rankings == []
            assert r.constraints_satisfied is False

    def test_edge_case_a2_simulation_endpoint_all_inactive_products(self, client, db_session):
        """
        Verify that a merchant whose catalogue contains ONLY inactive products (is_active=False)
        is treated as having 0 active candidates and completes gracefully.
        """
        m_reg = create_test_merchant(db_session, "all_inactive@test.com")
        token = m_reg.json()["access_token"]
        merchant_id = uuid.UUID(m_reg.json()["user"]["merchant_id"])
        headers = {"Authorization": f"Bearer {token}"}

        # Create 5 inactive products
        for i in range(5):
            p = Product(
                merchant_id=merchant_id,
                name=f"Inactive Product {i}",
                description="Deactivated",
                category="electronics",
                price=10000,
                currency="INR",
                is_active=False,
            )
            db_session.add(p)
            db_session.flush()
            db_session.add(Inventory(product_id=p.id, available_quantity=50))
        db_session.commit()

        # Repository retrieval must return 0
        repo_cat = ProductRepository(db_session).get_active_catalogue_for_merchant(merchant_id)
        assert len(repo_cat) == 0

        # Endpoint must succeed gracefully with 0 matches
        res = client.post(
            "/api/v1/optimization/simulations",
            json={
                "merchant_id": str(merchant_id),
                "scenario_count": 2,
            },
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["summary_metrics"]["successful_matches"] == 0
        assert data["summary_metrics"]["failed_matches"] == 2
        for r in data["results"]:
            assert r["selected_product_id"] is None
            assert r["rankings"] == []

    def test_edge_case_a3_what_if_endpoint_empty_catalogue(self, client, db_session):
        """
        Verify that POST /api/v1/optimization/what-if rejects empty catalogues
        with a structured HTTP 422 ValidationError rather than an unhandled 500 error.
        """
        m_reg = create_test_merchant(db_session, "empty_whatif@test.com")
        token = m_reg.json()["access_token"]
        merchant_id = uuid.UUID(m_reg.json()["user"]["merchant_id"])
        headers = {"Authorization": f"Bearer {token}"}

        res = client.post(
            "/api/v1/optimization/what-if",
            json={
                "hypothesis": "Test with empty catalogue",
                "modifications": {"price": 5000},
            },
            headers=headers,
        )

        assert res.status_code == 422, f"Expected 422 Unprocessable Entity, got {res.status_code}: {res.text}"
        data = res.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "Merchant catalogue is empty" in data["error"]["message"]

    def test_edge_case_a4_what_if_service_empty_catalogue_graceful(self, db_session):
        """
        Verify that WhatIfService.run_what_if handles an empty baseline catalogue directly
        without throwing exceptions, returning 0 matches and 0 score.
        """
        m_id = str(uuid.uuid4())
        db_personas = db_session.query(BuyerPersona).all()
        assert len(db_personas) > 0

        result = what_if_service.run_what_if(
            merchant_id=m_id,
            hypothesis="Empty catalogue direct service test",
            baseline_catalogue=[],
            modifications={"price": 1000},
            db_personas=db_personas,
        )

        assert result["baseline_metrics"]["matches"] == 0
        assert result["baseline_metrics"]["average_score"] == 0.0
        assert result["simulated_metrics"]["matches"] == 0
        assert result["simulated_metrics"]["average_score"] == 0.0
        assert result["delta_percentage"] == 0.0

    # -------------------------------------------------------------------------
    # EDGE CASE B: Winner Outside Top 20 (Ranks 500 & 1500)
    # -------------------------------------------------------------------------

    def test_edge_case_b1_truncate_rankings_winner_at_rank_500(self):
        """
        In a candidate pool of 2,977 evaluated products, verify that when the winner
        is at rank 500 (index 499), truncate_rankings appends this winner,
        maintains len(rankings) <= 31, and preserves the winner's visibility.
        """
        total_candidates = 2977
        passed_count = 2400
        disqualified_count = total_candidates - passed_count  # 577

        # Generate 2,400 passed candidates
        mock_passed = [
            {
                "product_id": f"prod_pass_{i:04d}",
                "product_name": f"Passed Product {i}",
                "score": round(100.0 - (i * 0.03), 4),
                "rank": i + 1,
                "frictions": [],
                "passed": True,
            }
            for i in range(passed_count)
        ]

        # Generate 577 disqualified candidates
        mock_disqualified = [
            {
                "product_id": f"prod_fail_{i:04d}",
                "product_name": f"Failed Product {i}",
                "score": 0.0,
                "rank": 999,
                "frictions": ["INVENTORY_ISSUE"],
                "passed": False,
            }
            for i in range(disqualified_count)
        ]

        all_rankings = mock_passed + mock_disqualified
        assert len(all_rankings) == 2977

        # Selected winner is at rank 500 (index 499)
        winner_index = 499
        winner_id = mock_passed[winner_index]["product_id"]
        assert mock_passed[winner_index]["rank"] == 500

        truncated = truncate_rankings(
            rankings=all_rankings,
            selected_product_id=winner_id,
            max_passed=20,
            max_disqualified=10,
        )

        # 1. Verification of maximum payload bound
        assert len(truncated) <= 31, f"Expected <= 31 candidates, got {len(truncated)}"
        assert len(truncated) == 31, f"Expected exactly 31 (20 + 1 winner + 10 fail), got {len(truncated)}"

        # 2. Winner visibility preservation
        winner_entries = [r for r in truncated if r["product_id"] == winner_id]
        assert len(winner_entries) == 1, "Winner at rank 500 must be present exactly once in truncated rankings"
        assert winner_entries[0]["rank"] == 500
        assert winner_entries[0]["passed"] is True

        # 3. Passed and disqualified counts
        passed_in_trunc = [r for r in truncated if r["passed"] is True]
        disqualified_in_trunc = [r for r in truncated if r["passed"] is False]
        assert len(passed_in_trunc) == 21  # 20 top + 1 appended winner
        assert len(disqualified_in_trunc) == 10  # max_disqualified = 10

        # Top 20 passed must be ranks 1..20
        for idx in range(20):
            assert passed_in_trunc[idx]["rank"] == idx + 1
        # 21st must be rank 500
        assert passed_in_trunc[20]["rank"] == 500

    def test_edge_case_b2_truncate_rankings_winner_at_rank_1500(self):
        """
        In a candidate pool of 2,977 evaluated products, verify that when the winner
        is at rank 1500 (index 1499), truncate_rankings appends this winner,
        maintains len(rankings) <= 31, and preserves the winner's visibility.
        """
        total_candidates = 2977
        passed_count = 2000
        disqualified_count = total_candidates - passed_count  # 977

        mock_passed = [
            {
                "product_id": f"prod_pass_{i:04d}",
                "product_name": f"Passed Product {i}",
                "score": round(100.0 - (i * 0.04), 4),
                "rank": i + 1,
                "frictions": [],
                "passed": True,
            }
            for i in range(passed_count)
        ]

        mock_disqualified = [
            {
                "product_id": f"prod_fail_{i:04d}",
                "product_name": f"Failed Product {i}",
                "score": 0.0,
                "rank": 999,
                "frictions": ["DELIVERY_TOO_SLOW"],
                "passed": False,
            }
            for i in range(disqualified_count)
        ]

        all_rankings = mock_passed + mock_disqualified
        assert len(all_rankings) == 2977

        # Selected winner is at rank 1500 (index 1499)
        winner_index = 1499
        winner_id = mock_passed[winner_index]["product_id"]
        assert mock_passed[winner_index]["rank"] == 1500

        truncated = truncate_rankings(
            rankings=all_rankings,
            selected_product_id=winner_id,
            max_passed=20,
            max_disqualified=10,
        )

        assert len(truncated) <= 31
        assert len(truncated) == 31

        winner_entries = [r for r in truncated if r["product_id"] == winner_id]
        assert len(winner_entries) == 1
        assert winner_entries[0]["rank"] == 1500
        assert winner_entries[0]["passed"] is True

        passed_in_trunc = [r for r in truncated if r["passed"] is True]
        assert len(passed_in_trunc) == 21
        assert passed_in_trunc[20]["product_id"] == winner_id

    def test_edge_case_b3_winner_already_in_top_20_no_duplicate(self):
        """
        Verify that when the selected winner is inside top 20 (e.g. rank 1 or rank 12),
        it is NOT duplicated and total rankings is exactly 30 (<= 31).
        """
        mock_passed = [
            {"product_id": f"p_{i}", "rank": i + 1, "passed": True, "score": 10.0 - i * 0.1}
            for i in range(100)
        ]
        mock_disqualified = [
            {"product_id": f"d_{i}", "rank": 999, "passed": False, "score": 0.0}
            for i in range(50)
        ]
        all_rankings = mock_passed + mock_disqualified

        # Winner is rank 5
        winner_id = "p_4"
        truncated = truncate_rankings(
            all_rankings,
            selected_product_id=winner_id,
            max_passed=20,
            max_disqualified=10,
        )

        # 20 passed + 10 disqualified = 30 (not 31)
        assert len(truncated) == 30
        winner_occurrences = [r for r in truncated if r["product_id"] == winner_id]
        assert len(winner_occurrences) == 1

    # -------------------------------------------------------------------------
    # EDGE CASE C: Inventory Signal Differentiation
    # -------------------------------------------------------------------------

    def test_edge_case_c1_friction_detector_inventory_signals(self):
        """
        Verify FrictionDetector.detect_hard_constraints distinguishes:
        - stock == 0 -> INVENTORY_ISSUE
        - stock < 0 -> INVENTORY_ISSUE
        - stock > 0 -> passes (no INVENTORY_ISSUE)
        - stock is None -> passes (no INVENTORY_ISSUE, preserving pre-Step 3 contract)
        """
        intent = {"max_budget": 100000}

        # Case 1: Stock == 0
        p_zero = {"id": "p0", "name": "Zero Stock", "price": 5000, "is_active": True, "available_quantity": 0}
        frictions_zero = FrictionDetector.detect_hard_constraints(p_zero, intent)
        assert FrictionReason.INVENTORY_ISSUE in frictions_zero

        # Case 2: Stock < 0 (negative)
        p_neg = {"id": "p_neg", "name": "Negative Stock", "price": 5000, "is_active": True, "available_quantity": -3}
        frictions_neg = FrictionDetector.detect_hard_constraints(p_neg, intent)
        assert FrictionReason.INVENTORY_ISSUE in frictions_neg

        # Case 3: Stock > 0 (positive)
        p_pos = {"id": "p_pos", "name": "Positive Stock", "price": 5000, "is_active": True, "available_quantity": 10}
        frictions_pos = FrictionDetector.detect_hard_constraints(p_pos, intent)
        assert FrictionReason.INVENTORY_ISSUE not in frictions_pos

        # Case 4: Stock is None (missing inventory record)
        p_none = {"id": "p_none", "name": "None Stock", "price": 5000, "is_active": True, "available_quantity": None}
        frictions_none = FrictionDetector.detect_hard_constraints(p_none, intent)
        assert FrictionReason.INVENTORY_ISSUE not in frictions_none, (
            "Missing inventory row (None) must NOT trigger INVENTORY_ISSUE under pre-Step 3 contract"
        )

        # Case 5: Product is_active == False
        p_inactive = {"id": "p_inact", "name": "Inactive", "price": 5000, "is_active": False, "available_quantity": 10}
        frictions_inactive = FrictionDetector.detect_hard_constraints(p_inactive, intent)
        assert FrictionReason.INVENTORY_ISSUE in frictions_inactive

    def test_edge_case_c2_simulation_engine_evaluates_three_inventory_states(self):
        """
        Verify SimulationEngine handles a mixed catalogue containing:
        - Product A: available_quantity = 0 (rejected with INVENTORY_ISSUE)
        - Product B: available_quantity = 10 (evaluated and scored)
        - Product C: available_quantity = None (evaluated and scored according to pre-Step 3 contract)
        """
        catalogue = [
            {
                "id": str(uuid.uuid4()),
                "name": "Zero Stock Item",
                "price": 1000,
                "is_active": True,
                "available_quantity": 0,
                "product_metadata": {"delivery_days": 2},
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Positive Stock Item",
                "price": 3000,
                "is_active": True,
                "available_quantity": 10,
                "product_metadata": {"delivery_days": 2},
            },
            {
                "id": str(uuid.uuid4()),
                "name": "None Stock Item",
                "price": 2000,
                "is_active": True,
                "available_quantity": None,
                "product_metadata": {"delivery_days": 2},
            },
        ]

        intent = {"max_budget": 5000}
        persona_weights = {"price": 0.8, "delivery": 0.2}

        sim_out = simulation_engine.run_simulation(
            merchant_id=str(uuid.uuid4()),
            persona_weights=persona_weights,
            intent=intent,
            catalogue=catalogue,
        )

        # 1. Zero stock item must be disqualified with INVENTORY_ISSUE
        p0_id = catalogue[0]["id"]
        p0_rankings = [r for r in sim_out["rankings"] if r["product_id"] == p0_id]
        assert len(p0_rankings) == 1
        assert p0_rankings[0]["passed"] is False
        assert "INVENTORY_ISSUE" in p0_rankings[0]["frictions"]

        # 2. Positive stock item must pass
        p_pos_id = catalogue[1]["id"]
        p_pos_rankings = [r for r in sim_out["rankings"] if r["product_id"] == p_pos_id]
        assert len(p_pos_rankings) == 1
        assert p_pos_rankings[0]["passed"] is True

        # 3. None stock item must pass
        p_none_id = catalogue[2]["id"]
        p_none_rankings = [r for r in sim_out["rankings"] if r["product_id"] == p_none_id]
        assert len(p_none_rankings) == 1
        assert p_none_rankings[0]["passed"] is True

        # 4. Winner selection: None stock item has lower price (2000 vs 3000) so under budget persona
        # it scores higher and becomes the legitimate winner!
        assert sim_out["selected_product_id"] == p_none_id
        assert sim_out["constraints_satisfied"] is True

    def test_edge_case_c3_db_repository_truthful_inventory_mapping(self, db_session):
        """
        Verify that ProductRepository.get_active_catalogue_for_merchant truthfully maps:
        - Product with Inventory(available_quantity=0) -> available_quantity == 0
        - Product with Inventory(available_quantity=25) -> available_quantity == 25
        - Product with NO Inventory row -> available_quantity is None (no fabricated 10!)
        """
        m_reg = create_test_merchant(db_session, "inv_truth@test.com")
        merchant_id = uuid.UUID(m_reg.json()["user"]["merchant_id"])

        p_oos = Product(
            merchant_id=merchant_id,
            name="OOS Product",
            category="general",
            price=1000,
            currency="INR",
            is_active=True,
        )
        p_in_stock = Product(
            merchant_id=merchant_id,
            name="In Stock Product",
            category="general",
            price=2000,
            currency="INR",
            is_active=True,
        )
        p_no_inv = Product(
            merchant_id=merchant_id,
            name="No Inventory Row Product",
            category="general",
            price=3000,
            currency="INR",
            is_active=True,
        )

        db_session.add_all([p_oos, p_in_stock, p_no_inv])
        db_session.flush()

        # Add Inventory row ONLY for p_oos and p_in_stock; leave p_no_inv without Inventory row
        db_session.add(Inventory(product_id=p_oos.id, available_quantity=0, reserved_quantity=0))
        db_session.add(Inventory(product_id=p_in_stock.id, available_quantity=25, reserved_quantity=0))
        db_session.commit()

        # Retrieve through ProductRepository
        repo = ProductRepository(db_session)
        catalogue = repo.get_active_catalogue_for_merchant(merchant_id)

        assert len(catalogue) == 3

        cat_by_id = {c["id"]: c for c in catalogue}

        # Verify truthful inventory
        assert cat_by_id[p_oos.id]["available_quantity"] == 0
        assert cat_by_id[p_in_stock.id]["available_quantity"] == 25
        assert cat_by_id[p_no_inv.id]["available_quantity"] is None, (
            f"Expected available_quantity to be None for missing inventory row, got {cat_by_id[p_no_inv.id]['available_quantity']}"
        )

    # -------------------------------------------------------------------------
    # EDGE CASE D: Determinism Verification
    # -------------------------------------------------------------------------

    def test_edge_case_d1_determinism_across_2977_products_with_score_ties(self):
        """
        Synthesize 2,977 active products with identical prices, delivery days, and scores
        to trigger score ties across large clusters.
        Execute simulation 3 consecutive times with identical inputs.
        Assert that scores, tie-breaking ordering, winner product ID, and truncated rankings
        are 100% bit-for-bit identical across all 3 runs.
        """
        # Generate 2,977 candidates with deterministic UUIDs
        candidates = []
        for i in range(2977):
            # Deterministic UUID based on index
            p_uuid = str(uuid.UUID(int=i + 1))
            # Create clusters of identical scores to stress deterministic tie-breaking
            cluster_id = i % 10
            candidates.append({
                "id": p_uuid,
                "name": f"Candidate Product {i:04d}",
                "description": f"Cluster {cluster_id} product",
                "category": "electronics",
                "price": 10000 + cluster_id * 500,  # identical within cluster
                "currency": "INR",
                "is_active": True,
                "available_quantity": 10,
                "product_metadata": {
                    "delivery_days": 2 + (cluster_id % 3),
                    "rating": 4.0,
                },
            })

        merchant_id = str(uuid.uuid4())
        persona_weights = {"price": 0.4, "delivery": 0.3, "rating": 0.3}
        intent = {"max_budget": 50000, "delivery_deadline_days": 5}

        # Run 1
        out1 = simulation_engine.run_simulation(
            merchant_id=merchant_id,
            persona_weights=persona_weights,
            intent=intent,
            catalogue=candidates,
            persona_name="DETERMINISM_TESTER",
        )
        trunc1 = truncate_rankings(out1["rankings"], out1["selected_product_id"])

        # Run 2
        out2 = simulation_engine.run_simulation(
            merchant_id=merchant_id,
            persona_weights=persona_weights,
            intent=intent,
            catalogue=candidates,
            persona_name="DETERMINISM_TESTER",
        )
        trunc2 = truncate_rankings(out2["rankings"], out2["selected_product_id"])

        # Run 3
        out3 = simulation_engine.run_simulation(
            merchant_id=merchant_id,
            persona_weights=persona_weights,
            intent=intent,
            catalogue=candidates,
            persona_name="DETERMINISM_TESTER",
        )
        trunc3 = truncate_rankings(out3["rankings"], out3["selected_product_id"])

        # Assert selected winner is 100% bit-for-bit identical
        assert out1["selected_product_id"] == out2["selected_product_id"] == out3["selected_product_id"]
        assert out1["score"] == out2["score"] == out3["score"]
        assert out1["reason_codes"] == out2["reason_codes"] == out3["reason_codes"]
        assert out1["constraints_satisfied"] == out2["constraints_satisfied"] == out3["constraints_satisfied"]

        # Assert full 2,977 rankings list is bit-for-bit identical
        assert len(out1["rankings"]) == len(out2["rankings"]) == len(out3["rankings"]) == 2977
        for idx in range(2977):
            r1, r2, r3 = out1["rankings"][idx], out2["rankings"][idx], out3["rankings"][idx]
            assert r1["product_id"] == r2["product_id"] == r3["product_id"]
            assert r1["score"] == r2["score"] == r3["score"]
            assert r1["rank"] == r2["rank"] == r3["rank"]
            assert r1["passed"] == r2["passed"] == r3["passed"]
            assert r1["frictions"] == r2["frictions"] == r3["frictions"]

        # Assert truncated rankings are 100% bit-for-bit identical
        assert len(trunc1) == len(trunc2) == len(trunc3)
        for idx in range(len(trunc1)):
            assert trunc1[idx] == trunc2[idx] == trunc3[idx]

    def test_edge_case_d2_determinism_live_merchant_catalogue(self):
        """
        Connects to the active development database (razorpay_buildathon.db),
        retrieves all 2,977 active products for 'Apex Audio & Tech',
        and executes simulation 3 consecutive times with identical buyer configuration.
        Asserts 100% bit-for-bit identical scores, tie-breaks, rankings, and winner.
        """
        # Look for the local SQLite database that contains Apex Audio & Tech
        test_dir = os.path.dirname(os.path.abspath(__file__))
        candidate_paths = [
            os.path.abspath("razorpay_buildathon.db"),
            os.path.abspath(os.path.join(test_dir, "..", "..", "razorpay_buildathon.db")),
            os.path.abspath("backend/razorpay_buildathon.db"),
            os.path.abspath(os.path.join(test_dir, "..", "razorpay_buildathon.db")),
        ]
        db_path = None
        for p in candidate_paths:
            if os.path.exists(p):
                eng = create_engine(f"sqlite:///{p}")
                try:
                    with eng.connect() as conn:
                        from sqlalchemy import text
                        res = conn.execute(text("SELECT id FROM merchants WHERE name = 'Apex Audio & Tech'")).fetchone()
                        if res:
                            db_path = p
                            break
                except Exception:
                    pass
                finally:
                    eng.dispose()

        if not db_path:
            pytest.skip("Live database with 'Apex Audio & Tech' not found; skipping live merchant test.")

        engine = create_engine(f"sqlite:///{db_path}")
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            merchant = session.query(Merchant).filter(Merchant.name == "Apex Audio & Tech").first()
            assert merchant is not None, "Expected merchant 'Apex Audio & Tech' to exist"

            srv = ProductService(session)
            cat = srv.get_active_catalogue(merchant.id)
            assert len(cat) == 2977, f"Expected 2977 active products, got {len(cat)}"

            persona_weights = {"price": 0.35, "delivery": 0.35, "rating": 0.30}
            intent = {"max_budget": 200000, "delivery_deadline_days": 4}

            runs = []
            truncated_runs = []
            for run_num in range(3):
                out = simulation_engine.run_simulation(
                    merchant_id=str(merchant.id),
                    persona_weights=persona_weights,
                    intent=intent,
                    catalogue=cat,
                    persona_name="LIVE_MERCHANT_DETERMINISM",
                )
                trunc = truncate_rankings(out["rankings"], out["selected_product_id"])
                runs.append(out)
                truncated_runs.append(trunc)

            # Compare runs 0, 1, 2
            run0, run1, run2 = runs[0], runs[1], runs[2]
            assert run0["selected_product_id"] == run1["selected_product_id"] == run2["selected_product_id"]
            assert run0["score"] == run1["score"] == run2["score"]
            assert run0["reason_codes"] == run1["reason_codes"] == run2["reason_codes"]

            # Verify all 2,977 candidate rankings match bit-for-bit
            for i in range(2977):
                r0, r1, r2 = run0["rankings"][i], run1["rankings"][i], run2["rankings"][i]
                assert r0["product_id"] == r1["product_id"] == r2["product_id"]
                assert r0["score"] == r1["score"] == r2["score"]
                assert r0["rank"] == r1["rank"] == r2["rank"]
                assert r0["passed"] == r1["passed"] == r2["passed"]

            # Verify truncated rankings match bit-for-bit
            assert truncated_runs[0] == truncated_runs[1] == truncated_runs[2]
            assert len(truncated_runs[0]) <= 31

        finally:
            session.close()
            engine.dispose()

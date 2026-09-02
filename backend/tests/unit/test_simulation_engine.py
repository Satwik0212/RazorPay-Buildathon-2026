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
    assert "Dominant reason: PRICE_MISMATCH" in res["explanation"]
    assert len(res["frictions"]) >= 2
    assert all(f["reason"] == "PRICE_MISMATCH" for f in res["frictions"])


# Step 2: Deterministic Ordering & Permutation Invariance Tests

def test_equal_scores_deterministic_tie_breaking_by_product_id():
    """
    Step 2 - Requirement C:
    Given candidates with exactly equal scores, verify product_id determines
    the exact same ordering regardless of input candidate order.
    """
    import random
    merchant_id = "00000000-0000-0000-0000-000000000001"
    weights = {"price": 0.5, "delivery": 0.5}
    intent = {"max_budget": 500000}

    # 4 candidates with identical attributes and identical scores
    candidates = [
        {"id": "prod_z", "name": "Zebra Prod", "price": 200000, "is_active": True, "metadata": {"delivery_days": 2}},
        {"id": "prod_a", "name": "Apple Prod", "price": 200000, "is_active": True, "metadata": {"delivery_days": 2}},
        {"id": "prod_m", "name": "Mango Prod", "price": 200000, "is_active": True, "metadata": {"delivery_days": 2}},
        {"id": "prod_b", "name": "Banana Prod", "price": 200000, "is_active": True, "metadata": {"delivery_days": 2}},
    ]

    expected_ordered_ids = ["prod_a", "prod_b", "prod_m", "prod_z"]

    # Test distinct permutations
    test_permutations = [
        candidates,  # [z, a, m, b]
        list(reversed(candidates)),  # [b, m, a, z]
        [candidates[2], candidates[0], candidates[3], candidates[1]],  # [m, z, b, a]
        [candidates[1], candidates[3], candidates[2], candidates[0]],  # [a, b, m, z]
    ]

    for order_idx, perm in enumerate(test_permutations):
        res = simulation_engine.run_simulation(
            merchant_id=merchant_id,
            persona_weights=weights,
            intent=intent,
            catalogue=perm,
            persona_name="Balanced Buyer"
        )
        ranked_ids = [r["product_id"] for r in res["rankings"]]
        scores = [r["score"] for r in res["rankings"]]

        # All scores must be equal
        assert len(set(scores)) == 1, f"Expected all scores to be equal, got {scores}"
        # Ranking order must strictly match lexicographical product_id tie-breaker
        assert ranked_ids == expected_ordered_ids, (
            f"Permutation {order_idx} failed deterministic ordering: {ranked_ids} vs {expected_ordered_ids}"
        )
        assert res["selected_product_id"] == "prod_a"


def test_ranking_permutation_invariance_100_runs():
    """
    Step 2 - Requirement D:
    Shuffle the same candidate set repeatedly across 100 randomized permutations
    and verify the final ranking list is 100% identical on every execution.
    """
    import random
    merchant_id = "00000000-0000-0000-0000-000000000001"
    weights = {"price": 0.4, "delivery": 0.3, "quality": 0.3}
    intent = {"max_budget": 1000000}

    # Diverse catalogue with distinct scores and intentional tie clusters
    catalogue = [
        {"id": "p_01_tie_a", "name": "Item 1", "price": 300000, "is_active": True, "metadata": {"delivery_days": 2, "rating": 4.5}},
        {"id": "p_02_tie_b", "name": "Item 2", "price": 300000, "is_active": True, "metadata": {"delivery_days": 2, "rating": 4.5}},
        {"id": "p_03_high",  "name": "Item 3", "price": 100000, "is_active": True, "metadata": {"delivery_days": 1, "rating": 5.0, "warranty": True}},
        {"id": "p_04_low",   "name": "Item 4", "price": 800000, "is_active": True, "metadata": {"delivery_days": 7, "rating": 2.0}},
        {"id": "p_05_mid",   "name": "Item 5", "price": 400000, "is_active": True, "metadata": {"delivery_days": 3, "rating": 4.0}},
        {"id": "p_06_tie_c", "name": "Item 6", "price": 300000, "is_active": True, "metadata": {"delivery_days": 2, "rating": 4.5}},
        {"id": "p_07_mid2",  "name": "Item 7", "price": 450000, "is_active": True, "metadata": {"delivery_days": 2, "rating": 4.2}},
        {"id": "p_08_hard_fail", "name": "Item 8", "price": 1500000, "is_active": True, "metadata": {}},  # exceeds max_budget
    ]

    baseline_res = simulation_engine.run_simulation(
        merchant_id=merchant_id,
        persona_weights=weights,
        intent=intent,
        catalogue=catalogue,
        persona_name="Test Persona"
    )

    baseline_ranking_ids = [r["product_id"] for r in baseline_res["rankings"]]
    baseline_ranking_scores = [r["score"] for r in baseline_res["rankings"]]
    baseline_selected_id = baseline_res["selected_product_id"]

    rng = random.Random(42)
    for trial in range(100):
        shuffled = catalogue.copy()
        rng.shuffle(shuffled)

        res = simulation_engine.run_simulation(
            merchant_id=merchant_id,
            persona_weights=weights,
            intent=intent,
            catalogue=shuffled,
            persona_name="Test Persona"
        )

        trial_ranking_ids = [r["product_id"] for r in res["rankings"]]
        trial_ranking_scores = [r["score"] for r in res["rankings"]]

        assert trial_ranking_ids == baseline_ranking_ids, (
            f"Trial {trial}: ranking order diverged under permutation!\n"
            f"Expected: {baseline_ranking_ids}\nGot: {trial_ranking_ids}"
        )
        assert trial_ranking_scores == baseline_ranking_scores, (
            f"Trial {trial}: scores diverged under permutation!"
        )
        assert res["selected_product_id"] == baseline_selected_id, (
            f"Trial {trial}: selected product diverged!"
        )


def test_genuine_higher_score_ranks_above_lower_regardless_of_product_id():
    """
    Step 2 - Requirement E:
    Verify a candidate with a genuinely higher score still ranks above
    a lower-score candidate regardless of product_id (lexicographical product_id
    tie-breaker is strictly secondary and never inverts genuine score differences).
    """
    merchant_id = "00000000-0000-0000-0000-000000000001"
    weights = {"price": 0.8, "delivery": 0.2}
    intent = {"max_budget": 1000000}

    # Product A has alphabetically lowest ID ("000_low_score") but high price (low score)
    prod_low_score = {
        "id": "000_low_score",
        "name": "Overpriced Product",
        "price": 900000,
        "is_active": True,
        "metadata": {"delivery_days": 7}
    }
    # Product Z has alphabetically highest ID ("zzz_high_score") but low price (high score)
    prod_high_score = {
        "id": "zzz_high_score",
        "name": "Bargain Product",
        "price": 100000,
        "is_active": True,
        "metadata": {"delivery_days": 1}
    }

    # Case 1: Input catalogue with low score first
    res1 = simulation_engine.run_simulation(
        merchant_id=merchant_id,
        persona_weights=weights,
        intent=intent,
        catalogue=[prod_low_score, prod_high_score],
        persona_name="Budget Persona"
    )
    assert res1["selected_product_id"] == "zzz_high_score"
    assert res1["rankings"][0]["product_id"] == "zzz_high_score"
    assert res1["rankings"][1]["product_id"] == "000_low_score"
    assert res1["rankings"][0]["score"] > res1["rankings"][1]["score"]

    # Case 2: Input catalogue with high score first
    res2 = simulation_engine.run_simulation(
        merchant_id=merchant_id,
        persona_weights=weights,
        intent=intent,
        catalogue=[prod_high_score, prod_low_score],
        persona_name="Budget Persona"
    )
    assert res2["selected_product_id"] == "zzz_high_score"
    assert res2["rankings"][0]["product_id"] == "zzz_high_score"
    assert res2["rankings"][1]["product_id"] == "000_low_score"

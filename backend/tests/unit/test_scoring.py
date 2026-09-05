import pytest
from app.simulation.scoring import ProductScorer


def test_scoring_bounded_and_reproducible():
    product = {
        "name": "Noise Cancelling Headphones",
        "description": "Premium over-ear ANC headset with long battery life.",
        "price": 499900,
        "product_metadata": {
            "delivery_days": 2,
            "rating": 4.8,
            "warranty": True,
            "return_days": 30,
            "has_discount": True,
            "anc": True
        }
    }
    weights = {"price": 0.25, "delivery": 0.25, "quality": 0.25, "returns": 0.15, "offers": 0.10}

    score1 = ProductScorer.calculate_score(product, weights, max_budget_minor=600000)
    score2 = ProductScorer.calculate_score(product, weights, max_budget_minor=600000)

    # Identical score (reproducibility)
    assert score1 == score2
    # Bounded within [0.0, 1.0]
    assert 0.0 <= score1 <= 1.0
    assert score1 > 0.70  # Excellent fit across all dimensions


def test_scoring_missing_attributes_handled_safely():
    # Bare minimum product dictionary
    bare_product = {"price": 100000}
    weights = {"price": 0.5, "delivery": 0.5}

    score = ProductScorer.calculate_score(bare_product, weights)
    assert 0.0 <= score <= 1.0


def test_scoring_weights_drive_differentiated_rankings():
    cheap_slow_item = {
        "id": "p1",
        "name": "Budget Earbuds",
        "description": "Simple earbuds",
        "price": 99900,
        "product_metadata": {"delivery_days": 7, "rating": 3.5, "return_days": 0}
    }
    expensive_fast_premium_item = {
        "id": "p2",
        "name": "Studio Pro Wireless",
        "description": "High end audio",
        "price": 899900,
        "product_metadata": {"delivery_days": 1, "rating": 4.9, "warranty": True, "return_days": 30}
    }

    # 1. Budget persona prioritizes price
    budget_weights = {"price": 0.70, "delivery": 0.10, "quality": 0.10, "returns": 0.10}
    score_p1_budget = ProductScorer.calculate_score(cheap_slow_item, budget_weights)
    score_p2_budget = ProductScorer.calculate_score(expensive_fast_premium_item, budget_weights)
    assert score_p1_budget > score_p2_budget

    # 2. Quality/Speed persona prioritizes fast delivery, high rating, and return policy
    quality_weights = {"quality": 0.40, "delivery": 0.40, "returns": 0.15, "price": 0.05}
    score_p1_quality = ProductScorer.calculate_score(cheap_slow_item, quality_weights)
    score_p2_quality = ProductScorer.calculate_score(expensive_fast_premium_item, quality_weights)
    assert score_p2_quality > score_p1_quality


# Step 2: Unquantized Score Precision & Strict Bounds Tests

def test_calculate_score_preserves_unquantized_precision():
    """
    Step 2 - Requirement A:
    Verify that calculate_score returns full floating-point precision
    and does NOT artificially quantize/round scores to 3 decimal places.
    """
    product = {
        "price": 10000,
        "description": "Short description",  # 17 chars -> desc_score = (17/500)*0.4 = 0.0136
        "metadata": {"product_rating": "4.8"}  # 1 key -> meta_score = (1/15)*0.6 = 0.04
    }
    weights = {"metadata": 1.0}
    score = ProductScorer.calculate_score(product, weights)

    # Exact mathematical score: 0.04 + 0.0136 = 0.0536
    assert score == pytest.approx(0.0536, abs=1e-6)
    # Confirm score is not quantized to 3 decimal places (0.054)
    assert score != 0.054
    assert score != round(score, 3)

    # Test with fractional budget savings creating repeating floating decimals
    product2 = {
        "price": 333333,
        "metadata": {"delivery_days": 3}
    }
    weights2 = {"price": 0.7, "delivery": 0.3}
    score2 = ProductScorer.calculate_score(product2, weights2, max_budget_minor=1000000)

    # Savings ratio: (1000000 - 333333) / 1000000 = 0.666667
    # price_score = 0.5 + 0.5 * 0.666667 = 0.8333335
    # delivery_score = 0.75
    # score = 0.7 * 0.8333335 + 0.3 * 0.75 = 0.58333345 + 0.225 = 0.80833345
    assert score2 != round(score2, 3)
    decimal_digits = len(str(score2).split(".")[1])
    assert decimal_digits > 3, f"Score {score2} unexpectedly quantized to <= 3 decimals"


def test_calculate_score_bounds_strict_enforcement():
    """
    Step 2 - Requirement B:
    Verify that scores strictly remain within [0.0, 1.0] across all
    boundary conditions, edge cases, and extreme inputs.
    """
    # 1. Perfect product with maximum possible attributes
    perfect_product = {
        "price": 0,
        "description": "A" * 600,
        "metadata": {
            f"key_{i}": f"val_{i}" for i in range(20)
        }
    }
    perfect_product["metadata"].update({
        "delivery_days": 0,
        "rating": 5.0,
        "warranty": True,
        "high_quality": True,
        "return_days": 45,
        "discount_percent": 80,
    })
    weights = {"price": 0.2, "delivery": 0.2, "quality": 0.2, "returns": 0.15, "offers": 0.15, "metadata": 0.1}
    max_score = ProductScorer.calculate_score(perfect_product, weights, max_budget_minor=1000000)
    assert 0.0 <= max_score <= 1.0
    assert max_score == pytest.approx(1.0, abs=1e-7)
    assert max_score > 0.999

    # 2. Extremely unfavorable product (massive price overflow, worst parameters)
    terrible_product = {
        "price": 999_999_999_999,
        "description": "",
        "metadata": {
            "delivery_days": 90,
            "rating": 0.0,
            "warranty": False,
            "return_days": 0,
            "discount_percent": 0
        }
    }
    min_score = ProductScorer.calculate_score(terrible_product, weights, max_budget_minor=1000)
    assert 0.0 <= min_score <= 1.0
    assert min_score >= 0.0

    # 3. Empty product and empty weights fallback
    fallback_score = ProductScorer.calculate_score({}, {})
    assert 0.0 <= fallback_score <= 1.0

    # 4. Systematic check across extreme weights and budget combinations
    for budget in [None, 0, 1, 100000, 10000000]:
        for price in [0, 1000, 500000, 50000000]:
            prod = {"price": price, "metadata": {"delivery_days": 2, "rating": 4.5}}
            s = ProductScorer.calculate_score(prod, {"price": 1.0}, max_budget_minor=budget)
            assert 0.0 <= s <= 1.0, f"Score {s} out of bounds for price={price}, budget={budget}"


def test_calculate_score_with_breakdown():
    product = {
        "name": "Sony Wireless Headphones",
        "description": "High performance audio with ANC and long battery life.",
        "price": 499900,
        "product_metadata": {
            "delivery_days": 2,
            "rating": 4.6,
            "warranty": True,
            "return_days": 14,
            "discount_percent": 10,
        }
    }
    weights = {"price": 0.3, "delivery": 0.2, "quality": 0.2, "returns": 0.1, "offers": 0.1, "metadata": 0.1}

    score, breakdown = ProductScorer.calculate_score_with_breakdown(product, weights, max_budget_minor=600000)
    score_standalone = ProductScorer.calculate_score(product, weights, max_budget_minor=600000)

    # Identical score calculation
    assert score == score_standalone
    assert 0.0 <= score <= 1.0

    # Verify all 6 dimensions present and bounded
    expected_keys = {"price", "delivery", "quality", "returns", "offers", "metadata"}
    assert set(breakdown.keys()) == expected_keys
    for k, val in breakdown.items():
        assert 0.0 <= val <= 1.0, f"Breakdown key {k} had value {val} outside [0.0, 1.0]"

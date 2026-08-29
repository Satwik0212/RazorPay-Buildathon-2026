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

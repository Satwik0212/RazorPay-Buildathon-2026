import pytest
from app.simulation.friction import FrictionDetector, FrictionReason


def test_hard_constraint_price_mismatch():
    intent = {"max_budget": 50000}
    product_over = {"price": 60000, "is_active": True, "metadata": {}}
    product_under = {"price": 40000, "is_active": True, "metadata": {}}

    frictions_over = FrictionDetector.detect_hard_constraints(product_over, intent)
    assert FrictionReason.PRICE_MISMATCH in frictions_over

    frictions_under = FrictionDetector.detect_hard_constraints(product_under, intent)
    assert FrictionReason.PRICE_MISMATCH not in frictions_under


def test_hard_constraint_inventory_issue():
    intent = {"max_budget": 100000}
    inactive_product = {"price": 50000, "is_active": False, "metadata": {}}
    out_of_stock_product = {"price": 50000, "is_active": True, "available_quantity": 0, "metadata": {}}
    in_stock_product = {"price": 50000, "is_active": True, "available_quantity": 10, "metadata": {}}

    assert FrictionReason.INVENTORY_ISSUE in FrictionDetector.detect_hard_constraints(inactive_product, intent)
    assert FrictionReason.INVENTORY_ISSUE in FrictionDetector.detect_hard_constraints(out_of_stock_product, intent)
    assert FrictionReason.INVENTORY_ISSUE not in FrictionDetector.detect_hard_constraints(in_stock_product, intent)


def test_hard_constraint_missing_feature():
    intent = {"requirements": ["ANC", "wireless"]}
    product_with_features = {
        "name": "Wireless Noise Cancelling Headphones",
        "description": "Premium wireless ANC headset",
        "price": 50000,
        "is_active": True,
        "product_metadata": {"anc": "true", "wireless": "true"}
    }
    product_without_features = {
        "name": "Basic Wired Earbuds",
        "description": "Standard 3.5mm earbuds",
        "price": 20000,
        "is_active": True,
        "product_metadata": {}
    }

    assert FrictionDetector.detect_hard_constraints(product_with_features, intent) == []
    frictions = FrictionDetector.detect_hard_constraints(product_without_features, intent)
    assert FrictionReason.MISSING_FEATURE in frictions


def test_hard_constraint_delivery_deadline():
    intent = {"delivery_deadline_days": 2}
    slow_product = {"price": 50000, "is_active": True, "metadata": {"delivery_days": 5}}
    fast_product = {"price": 50000, "is_active": True, "metadata": {"delivery_days": 1}}

    assert FrictionReason.DELIVERY_UNCLEAR in FrictionDetector.detect_hard_constraints(slow_product, intent)
    assert FrictionReason.DELIVERY_UNCLEAR not in FrictionDetector.detect_hard_constraints(fast_product, intent)


def test_soft_friction_speed_persona_missing_delivery():
    speed_weights = {"delivery": 0.50, "price": 0.10}
    product_without_delivery = {"description": "Full product description with many details here.", "metadata": {}}
    product_with_delivery = {"description": "Full product description with many details here.", "metadata": {"delivery_days": 2}}

    frictions = FrictionDetector.detect_soft_friction(product_without_delivery, speed_weights)
    assert FrictionReason.DELIVERY_UNCLEAR in frictions

    frictions_ok = FrictionDetector.detect_soft_friction(product_with_delivery, speed_weights)
    assert FrictionReason.DELIVERY_UNCLEAR not in frictions_ok


def test_soft_friction_quality_persona_missing_return():
    quality_weights = {"quality": 0.40, "returns": 0.20}
    product_without_returns = {"description": "High end audio headphones with premium build", "metadata": {}}
    product_with_returns = {"description": "High end audio headphones with premium build", "metadata": {"return_days": 14}}

    frictions = FrictionDetector.detect_soft_friction(product_without_returns, quality_weights)
    assert FrictionReason.RETURN_UNCLEAR in frictions

    frictions_ok = FrictionDetector.detect_soft_friction(product_with_returns, quality_weights)
    assert FrictionReason.RETURN_UNCLEAR not in frictions_ok


def test_soft_friction_insufficient_product_information():
    feature_weights = {"metadata": 0.40, "quality": 0.20}
    sparse_product = {"description": "Short", "metadata": {}}
    rich_product = {
        "description": "Comprehensive detailed description of the laptop with full specs.",
        "metadata": {"ram": "16GB", "ssd": "512GB", "screen": "15.6 inch"}
    }

    assert FrictionReason.INSUFFICIENT_PRODUCT_INFORMATION in FrictionDetector.detect_soft_friction(sparse_product, feature_weights)
    assert FrictionReason.INSUFFICIENT_PRODUCT_INFORMATION not in FrictionDetector.detect_soft_friction(rich_product, feature_weights)

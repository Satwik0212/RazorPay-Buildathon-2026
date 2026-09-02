import pytest
from app.simulation.normalization import MetadataNormalizer
from app.simulation.scoring import ProductScorer


# 1. Rating Normalization & Falsy 0.0 Tests

def test_rating_zero_is_recognized():
    product = {"metadata": {"rating": 0.0}}
    normalized = MetadataNormalizer.normalize(product)
    assert normalized.get("rating") == 0.0


def test_product_rating_zero_is_recognized():
    product = {"metadata": {"product_rating": 0}}
    normalized = MetadataNormalizer.normalize(product)
    assert normalized.get("rating") == 0.0


def test_overall_rating_zero_is_recognized():
    product = {"metadata": {"overall_rating": "0.0"}}
    normalized = MetadataNormalizer.normalize(product)
    assert normalized.get("rating") == 0.0


def test_rating_alias_precedence():
    product = {"metadata": {"rating": "4.5", "product_rating": "3.0", "overall_rating": "2.0"}}
    normalized = MetadataNormalizer.normalize(product)
    assert normalized.get("rating") == 4.5

    product2 = {"metadata": {"product_rating": "3.8", "overall_rating": "2.5"}}
    normalized2 = MetadataNormalizer.normalize(product2)
    assert normalized2.get("rating") == 3.8


def test_product_rating_numeric_string():
    product = {"metadata": {"product_rating": "4.8"}}
    normalized = MetadataNormalizer.normalize(product)
    assert normalized.get("rating") == 4.8


def test_rating_string_fraction_recognized():
    product = {"metadata": {"rating": "4.8/5.0"}}
    normalized = MetadataNormalizer.normalize(product)
    assert normalized.get("rating") == 4.8


def test_no_rating_available_falls_back_safely():
    product = {"metadata": {"rating": "No rating available"}}
    normalized = MetadataNormalizer.normalize(product)
    assert "rating" not in normalized


def test_malformed_rating_does_not_crash():
    product = {"metadata": {"product_rating": {"complex": "object"}}}
    normalized = MetadataNormalizer.normalize(product)
    assert "rating" not in normalized


# 2. Warranty Normalization Tests

@pytest.mark.parametrize("warranty_str", [
    "1 year",
    "2 years",
    "12 months",
    "24 months",
    "6 months",
    "30 days",
    "1 Year Manufacturer Warranty",
    "Domestic Warranty 2 Years",
    True,
    "true",
    "yes",
    "1",
])
def test_warranty_positive_recognized(warranty_str):
    product = {"metadata": {"warranty": warranty_str}}
    normalized = MetadataNormalizer.normalize(product)
    assert normalized.get("warranty") is True


@pytest.mark.parametrize("warranty_str", [
    False,
    "false",
    "no",
    "0",
    "none",
    "No warranty",
    "n/a",
    "without warranty",
])
def test_warranty_negative_recognized(warranty_str):
    product = {"metadata": {"warranty": warranty_str}}
    normalized = MetadataNormalizer.normalize(product)
    assert normalized.get("warranty") is False


def test_warranty_unparseable_remains_unknown():
    product = {"metadata": {"warranty": "unspecified random string 123"}}
    normalized = MetadataNormalizer.normalize(product)
    assert "warranty" not in normalized


def test_warranty_in_specifications_dict():
    product = {"metadata": {"specifications": {"warranty": "2 years"}}}
    normalized = MetadataNormalizer.normalize(product)
    assert normalized.get("warranty") is True


def test_warranty_in_specifications_list():
    product = {"metadata": {"specifications": [{"name": "Warranty Summary", "value": "1 Year Brand Warranty"}]}}
    normalized = MetadataNormalizer.normalize(product)
    assert normalized.get("warranty") is True


# 3. Delivery and Return Normalization Tests

def test_missing_delivery_remains_unknown():
    product = {"metadata": {"free_shipping": True}}
    normalized = MetadataNormalizer.normalize(product)
    assert "delivery_days" not in normalized


def test_invalid_delivery_falls_back_safely():
    product = {"metadata": {"delivery_days": "Unknown"}}
    normalized = MetadataNormalizer.normalize(product)
    assert "delivery_days" not in normalized


def test_missing_return_remains_unknown():
    product = {"metadata": {"random_policy": "yes"}}
    normalized = MetadataNormalizer.normalize(product)
    assert "return_days" not in normalized


def test_returnable_sets_return_policy():
    product = {"metadata": {"returnable": "True"}}
    normalized = MetadataNormalizer.normalize(product)
    assert normalized.get("return_policy") is True


# 4. Metadata Density Preservation in ProductScorer

def test_metadata_density_not_inflated_by_aliases():
    # A product with 1 raw metadata key ("product_rating")
    product = {
        "price": 10000,
        "description": "Short description",
        "metadata": {"product_rating": "4.8"}
    }
    # Persona placing 1.0 weight on metadata richness
    weights = {"metadata": 1.0}
    score = ProductScorer.calculate_score(product, weights)

    # Raw meta count is 1. meta_score = min(0.6, (1 / 15.0) * 0.6) = 0.04
    # desc_score = min(0.4, (17 / 500.0) * 0.4) = 0.0136
    # Total expected score = 0.04 + 0.0136 = 0.0536 (unquantized float precision in Step 2)
    assert score == pytest.approx(0.0536, abs=1e-5)

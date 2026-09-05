"""Unit tests for the normalizer."""
import pytest
from app.ingestion.normalizer import (
    normalize_price, normalize_inventory, normalize_category,
    normalize_images, normalize_specs, normalize_rating, normalize_text,
)


class TestNormalizePrice:
    def test_plain_integer(self):
        assert normalize_price("1999") == 199900

    def test_with_rupee_symbol(self):
        assert normalize_price("\u20b91999") == 199900

    def test_with_commas(self):
        assert normalize_price("1,999") == 199900

    def test_inr_prefix(self):
        assert normalize_price("INR 1999") == 199900

    def test_rs_prefix(self):
        assert normalize_price("Rs. 1999") == 199900

    def test_decimal(self):
        assert normalize_price("1999.50") == 199950

    def test_empty(self):
        assert normalize_price("") is None

    def test_zero(self):
        assert normalize_price("0") == 0

    def test_non_numeric(self):
        assert normalize_price("not a price") is None

    def test_negative(self):
        assert normalize_price("-100") is None


class TestNormalizeInventory:
    def test_plain_int(self):
        assert normalize_inventory("50") == 50

    def test_with_text(self):
        assert normalize_inventory("50 units") == 50

    def test_empty(self):
        assert normalize_inventory("") == 0

    def test_non_numeric(self):
        assert normalize_inventory("out of stock") == 0

    def test_zero(self):
        assert normalize_inventory("0") == 0


class TestNormalizeCategory:
    def test_flipkart_tree(self):
        raw = '["Mobiles & Accessories >> Smartphones >> Android Phones"]'
        top, hierarchy = normalize_category(raw)
        assert top == "Mobiles & Accessories"
        assert "Smartphones" in hierarchy

    def test_plain_hierarchy(self):
        top, hierarchy = normalize_category("Electronics > Computers > Laptops")
        assert top == "Electronics"

    def test_empty(self):
        top, hierarchy = normalize_category("")
        assert top == "Uncategorized"

    def test_plain_text(self):
        top, hierarchy = normalize_category("Electronics")
        assert top == "Electronics"


class TestNormalizeImages:
    def test_json_array(self):
        raw = '["http://img1.jpg", "http://img2.jpg"]'
        urls = normalize_images(raw)
        assert len(urls) == 2
        assert "http://img1.jpg" in urls

    def test_single_url(self):
        urls = normalize_images("http://example.com/img.jpg")
        assert urls == ["http://example.com/img.jpg"]

    def test_empty(self):
        assert normalize_images("") == []

    def test_invalid(self):
        assert normalize_images("not a url or json") == []


class TestNormalizeSpecs:
    def test_ruby_hash(self):
        raw = '{"product_specification"=>[{"key"=>"Brand", "value"=>"Apple"}, {"key"=>"Color", "value"=>"White"}]}'
        specs = normalize_specs(raw)
        assert specs["Brand"] == "Apple"
        assert specs["Color"] == "White"

    def test_empty_ruby_hash(self):
        raw = '{"product_specification"=>[]}'
        specs = normalize_specs(raw)
        assert specs == {}

    def test_empty_string(self):
        assert normalize_specs("") == {}

    def test_plain_json_dict(self):
        specs = normalize_specs('{"Color": "Blue", "Size": "Large"}')
        assert specs["Color"] == "Blue"

    def test_json_array_kv(self):
        raw = '[{"key": "Material", "value": "Steel"}]'
        specs = normalize_specs(raw)
        assert specs.get("Material") == "Steel"


class TestNormalizeRating:
    def test_valid(self):
        assert normalize_rating("4.5") == 4.5

    def test_integer(self):
        assert normalize_rating("5") == 5.0

    def test_empty(self):
        assert normalize_rating("") is None

    def test_out_of_range(self):
        assert normalize_rating("6.0") is None

    def test_text(self):
        assert normalize_rating("no rating") is None

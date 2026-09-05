"""Unit tests for schema detector and mapping validator."""
import pytest
from app.ingestion.schema_detector import detect_schema
from app.ingestion.mapping_validator import validate_mapping, mappings_to_field_dict


class TestSchemaDetector:
    def test_flipkart_canonical_detected(self):
        headers = [
            "uniq_id", "crawl_timestamp", "product_url", "product_name",
            "product_category_tree", "pid", "retail_price", "discounted_price",
            "image", "is_FK_Advantage_product", "description", "product_rating",
            "overall_rating", "brand", "product_specifications"
        ]
        schema = detect_schema(headers)
        assert schema.is_flipkart_canonical
        assert not schema.needs_ai_mapping
        assert "product_name" in schema.deterministic_mappings.values()
        assert "retail_price" in schema.deterministic_mappings.values()
        assert "discounted_price" in schema.deterministic_mappings.values()

    def test_known_alias_mapping(self):
        headers = ["name", "selling_price", "category", "brand"]
        schema = detect_schema(headers)
        assert schema.schema_type == "PARTIAL_DETERMINISTIC"
        assert schema.deterministic_mappings["name"] == "product_name"
        assert schema.deterministic_mappings["selling_price"] == "discounted_price"

    def test_unknown_schema(self):
        headers = ["col1", "col2", "col3"]
        schema = detect_schema(headers)
        assert schema.needs_ai_mapping
        assert schema.schema_type == "UNKNOWN"

    def test_case_insensitive_flipkart(self):
        headers = [
            "UNIQ_ID", "Product_Name", "product_category_tree", "retail_price",
            "discounted_price", "brand", "description"
        ]
        schema = detect_schema(headers)
        # Should still detect as PARTIAL_DETERMINISTIC at least
        assert schema.schema_type in ("FLIPKART_CANONICAL", "PARTIAL_DETERMINISTIC")


class TestMappingValidator:
    def test_valid_mapping(self):
        mappings = [
            {"source_column": "name", "target_field": "product_name", "confidence": 0.95, "reason": "test"},
            {"source_column": "price", "target_field": "discounted_price", "confidence": 0.90, "reason": "test"},
        ]
        valid, errors = validate_mapping(mappings, ["name", "price"])
        assert len(valid) == 2
        assert len(errors) == 0

    def test_blocks_platform_owned(self):
        mappings = [
            {"source_column": "mid", "target_field": "merchant_id", "confidence": 0.99, "reason": "test"},
            {"source_column": "name", "target_field": "product_name", "confidence": 0.95, "reason": "test"},
        ]
        valid, errors = validate_mapping(mappings, ["mid", "name"])
        assert all(m["target_field"] != "merchant_id" for m in valid)
        assert any("platform-owned" in e for e in errors)

    def test_rejects_unknown_canonical(self):
        mappings = [
            {"source_column": "col", "target_field": "nonexistent_field", "confidence": 0.9, "reason": "test"},
            {"source_column": "name", "target_field": "product_name", "confidence": 0.95, "reason": "test"},
        ]
        valid, errors = validate_mapping(mappings, ["col", "name"])
        assert not any(m["target_field"] == "nonexistent_field" for m in valid)

    def test_rejects_source_not_in_csv(self):
        mappings = [
            {"source_column": "ghost_col", "target_field": "product_name", "confidence": 0.9, "reason": "test"},
        ]
        valid, errors = validate_mapping(mappings, ["name", "price"])
        assert len(valid) == 0
        assert any("product_name" in e for e in errors)  # required field error

    def test_no_duplicate_source(self):
        mappings = [
            {"source_column": "name", "target_field": "product_name", "confidence": 0.9, "reason": "test"},
            {"source_column": "name", "target_field": "description", "confidence": 0.8, "reason": "test"},
        ]
        valid, errors = validate_mapping(mappings, ["name"])
        assert len(valid) == 1

    def test_confidence_levels(self):
        mappings = [
            {"source_column": "name", "target_field": "product_name", "confidence": 0.95, "reason": "test"},
            {"source_column": "price", "target_field": "discounted_price", "confidence": 0.80, "reason": "test"},
            {"source_column": "cat", "target_field": "category", "confidence": 0.60, "reason": "test"},
        ]
        valid, _ = validate_mapping(mappings, ["name", "price", "cat"])
        level_map = {m["target_field"]: m["confidence_level"] for m in valid}
        assert level_map["product_name"] == "HIGH"
        assert level_map["discounted_price"] == "MEDIUM"
        assert level_map["category"] == "LOW"

    def test_requires_product_name(self):
        mappings = [
            {"source_column": "price", "target_field": "discounted_price", "confidence": 0.95, "reason": "test"},
        ]
        valid, errors = validate_mapping(mappings, ["price"])
        assert any("product_name" in e or "Required" in e for e in errors)


class TestFlipkartCLICompatibility:
    """Verify that the existing parse_specs function still works via the refactored CLI."""
    def test_parse_specs_compatibility(self):
        from scripts.import_flipkart_data import parse_specs
        raw = '{"product_specification"=>[{"key"=>"Brand", "value"=>"Apple"}, {"key"=>"Color", "value"=>"White"}]}'
        res = parse_specs(raw)
        assert res["Brand"] == "Apple"
        assert res["Color"] == "White"

    def test_parse_specs_empty(self):
        from scripts.import_flipkart_data import parse_specs
        assert parse_specs("") == {}
        assert parse_specs('{"product_specification"=>[]}') == {}

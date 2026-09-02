import os
import csv
import pytest
import uuid
from unittest.mock import patch
from app.core.database import SessionLocal
from app.models.merchant import Merchant
from app.models.product import Product, Inventory
from scripts.import_flipkart_data import parse_specs

def test_parse_specs():
    raw = '{"product_specification"=>[{"key"=>"Brand", "value"=>"Apple"}, {"key"=>"Color", "value"=>"White"}, {"value"=>"Some feature"}]}'
    res = parse_specs(raw)
    assert res["Brand"] == "Apple"
    assert res["Color"] == "White"

def test_parse_specs_empty():
    assert parse_specs("") == {}
    assert parse_specs('{"product_specification"=>[]}') == {}

@pytest.fixture
def mock_csv_data(tmp_path):
    csv_file = tmp_path / "test_flipkart.csv"
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(['uniq_id', 'crawl_timestamp', 'product_url', 'product_name', 'product_category_tree', 'pid', 'retail_price', 'discounted_price', 'image', 'is_FK_Advantage_product', 'description', 'product_rating', 'overall_rating', 'brand', 'product_specifications'])
        # Valid product
        writer.writerow(['u1', '', '', 'Test Phone', '["Mobiles & Accessories >> Phones"]', '', '1000', '900', '["img1"]', '', 'A nice phone', '4.5', '5', 'Apple', '{"product_specification"=>[{"key"=>"Color", "value"=>"White"}]}'])
        # Duplicate product name
        writer.writerow(['u2', '', '', 'Test Phone', '["Mobiles & Accessories >> Phones"]', '', '1000', '900', '["img1"]', '', 'Another phone', '', '', '', ''])
        # Missing price
        writer.writerow(['u3', '', '', 'Free Phone', '["Mobiles & Accessories >> Phones"]', '', '', '', '', '', '', '', '', '', ''])
        # Ignored category
        writer.writerow(['u4', '', '', 'Test Shirt', '["Clothing >> Shirts"]', '', '500', '400', '', '', '', '', '', '', ''])
    return str(csv_file)

# We would need to mock the path in the script to point to mock_csv_data

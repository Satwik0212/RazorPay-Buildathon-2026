"""Unit tests for the CSV profiler."""
import pytest
from app.ingestion.profiler import profile_csv, CSVProfileError

VALID_CSV = b"""product_name,price,category,brand
Test Product,1000,Electronics,Apple
Another Product,2000,Computers,Samsung
"""

EMPTY_CSV = b""
NO_HEADER_CSV = b"\n\n\n"
LARGE_FIELD_CSV = b"product_name,price\n" + b"A" * 6000 + b",100\n"


def test_profile_valid_csv():
    profile = profile_csv(VALID_CSV)
    assert "product_name" in profile["headers"]
    assert "price" in profile["headers"]
    assert profile["row_count"] == 2
    assert len(profile["sample_rows"]) == 2
    assert profile["column_profiles"]["price"]["inferred_type"] == "numeric"
    assert profile["column_profiles"]["product_name"]["inferred_type"] == "text"


def test_profile_empty_csv():
    with pytest.raises(CSVProfileError, match="empty"):
        profile_csv(EMPTY_CSV)


def test_profile_no_data_rows():
    with pytest.raises(CSVProfileError):
        profile_csv(b"col1,col2\n")


def test_profile_bom_stripped():
    bom_csv = b"\xef\xbb\xbf" + VALID_CSV
    profile = profile_csv(bom_csv)
    assert "product_name" in profile["headers"]


def test_profile_field_truncation():
    profile = profile_csv(LARGE_FIELD_CSV)
    sample = profile["sample_rows"][0]
    assert sample["product_name"].endswith("...[truncated]")


def test_profile_file_too_large():
    large = b"col\n" + b"x" * (51 * 1024 * 1024)
    with pytest.raises(CSVProfileError, match="too large"):
        profile_csv(large)


def test_profile_column_types():
    csv_bytes = b"name,amount,data\nApple,1999.0,[1,2,3]\nSamsung,2500.00,{}\n"
    profile = profile_csv(csv_bytes)
    assert profile["column_profiles"]["amount"]["inferred_type"] == "numeric"
    assert profile["column_profiles"]["data"]["inferred_type"] == "json_or_list"
    assert profile["column_profiles"]["name"]["inferred_type"] == "text"

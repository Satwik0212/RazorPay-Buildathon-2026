"""
Deterministic Value Normalization Engine.

Transforms raw CSV cell values into canonical types expected by the Product model.
All transformations are deterministic — no LLM is involved.

Normalization rules documented per field type.
"""
import ast
import re
import json
from typing import Any, Dict, List, Optional, Tuple


class NormalizationError(Exception):
    pass


def normalize_price(raw: str) -> Optional[int]:
    """
    Converts price strings to integer paise (price in rupees * 100).

    Handles:
      ₹1,999  |  INR 1999  |  Rs. 1999  |  1,999.00  |  1999

    Returns None if value cannot be parsed.
    """
    if not raw or not raw.strip():
        return None
    cleaned = raw.strip()
    # Remove currency symbols, prefixes
    cleaned = re.sub(r"[\u20b9\$\u20ac\xa3]", "", cleaned)  # rupee, dollar, euro, pound
    cleaned = re.sub(r"(?i)^(inr|rs\.?|rupees?)", "", cleaned).strip()
    # Remove commas (thousands separator)
    cleaned = cleaned.replace(",", "")
    # Remove trailing/leading whitespace
    cleaned = cleaned.strip()
    if not cleaned:
        return None
    try:
        value = float(cleaned)
        if value < 0:
            return None  # Negative prices not allowed
        return int(round(value * 100))  # Convert to paise
    except ValueError:
        return None


def normalize_inventory(raw: str) -> int:
    """
    Converts inventory/quantity strings to non-negative integer.

    Handles:
      34  |  "34 units"  |  "34 pcs"  |  "34 pieces"

    Returns 0 if value cannot be parsed.
    """
    if not raw or not raw.strip():
        return 0
    # Extract leading integer
    match = re.match(r"^\s*(\d+)", raw.strip())
    if match:
        return int(match.group(1))
    return 0


def normalize_text(raw: str, max_length: Optional[int] = None) -> str:
    """
    Strips whitespace from text. Optionally truncates to max_length.
    DOES NOT rewrite or AI-enhance the text.
    """
    if not raw:
        return ""
    result = raw.strip()
    if max_length and len(result) > max_length:
        result = result[:max_length]
    return result


def normalize_category(raw: str) -> Tuple[str, str]:
    """
    Extracts the top-level category from a category string.
    Preserves the original hierarchy.

    For Flipkart format: '["Mobiles & Accessories >> Phones >> Smartphones"]'
    Returns: ("Mobiles & Accessories", original_hierarchy)

    For plain text: "Electronics > Smartphones"
    Returns: ("Electronics", "Electronics > Smartphones")
    """
    if not raw or not raw.strip():
        return ("Uncategorized", "")

    original = raw.strip()

    # Try Flipkart format: list of strings
    try:
        parsed = ast.literal_eval(original)
        if isinstance(parsed, list) and parsed:
            first = str(parsed[0])
            # Extract top-level: split on >> or >
            top = re.split(r"\s*>>\s*|\s*>\s*", first)[0].strip()
            return (top or "Uncategorized", first)
    except Exception:
        pass

    # Try plain hierarchy: "Category >> Sub >> Sub"
    parts = re.split(r"\s*>>\s*|\s*>\s*", original)
    top = parts[0].strip() if parts else "Uncategorized"
    return (top or "Uncategorized", original)


def normalize_images(raw: str) -> List[str]:
    """
    Converts image field to a list of URL strings.

    Handles:
      '["url1", "url2"]'  (JSON array string)
      'url1'              (single URL)

    Returns empty list if not parseable.
    """
    if not raw or not raw.strip():
        return []
    stripped = raw.strip()
    try:
        parsed = ast.literal_eval(stripped)
        if isinstance(parsed, list):
            return [str(u) for u in parsed if u]
        if isinstance(parsed, str):
            return [parsed] if parsed else []
    except Exception:
        pass
    # Single URL
    if stripped.startswith("http"):
        return [stripped]
    return []


def normalize_specs(raw: str) -> Dict[str, str]:
    """
    Parses product specifications.

    Handles two formats:
    1. Flipkart Ruby-hash style:
       '{"product_specification"=>[{"key"=>"Brand", "value"=>"Apple"}, ...]}'
    2. Plain JSON dict: '{"Brand": "Apple", "Color": "White"}'
    3. JSON array: '[{"key": "Brand", "value": "Apple"}]'

    Returns dict of key->value.
    Preserves raw value (with raw_specs key) if not parseable.
    """
    if not raw or raw.strip() == '{"product_specification"=>[]}' or not raw.strip():
        return {}

    results = {}

    # Try Flipkart Ruby-hash style
    ruby_matches = re.finditer(
        r'"key"\s*=>\s*"(.*?)",\s*"value"\s*=>\s*"(.*?)"', raw
    )
    for match in ruby_matches:
        key = match.group(1).strip()
        value = match.group(2).strip()
        if key:
            results[key] = value

    if results:
        return results

    # Try plain JSON
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return {str(k): str(v) for k, v in parsed.items()}
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    k = item.get("key") or item.get("name") or item.get("attribute")
                    v = item.get("value") or item.get("val")
                    if k and v:
                        results[str(k).strip()] = str(v).strip()
            if results:
                return results
    except Exception:
        pass

    # Cannot parse — preserve raw value with explicit marker
    return {"_raw_specifications": raw[:500]}


def normalize_rating(raw: str) -> Optional[float]:
    """
    Parses rating strings to float in 0-5 range.
    Returns None if not parseable.
    """
    if not raw or not raw.strip():
        return None
    try:
        val = float(raw.strip())
        if 0.0 <= val <= 5.0:
            return val
        return None  # Out of range
    except ValueError:
        return None


def normalize_row(
    row: Dict[str, str],
    field_mapping: Dict[str, str],  # source_column -> canonical_field
    default_inventory: int = 0,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Normalizes a single CSV row according to the field mapping.

    Returns:
        (normalized_values, row_errors)

    normalized_values keys match canonical field names.
    row_errors is a list of {field, error, original_value, severity} dicts.
    """
    normalized: Dict[str, Any] = {}
    errors: List[Dict[str, Any]] = []

    for source_col, canonical_field in field_mapping.items():
        raw_value = row.get(source_col, "") or ""

        if canonical_field == "product_name":
            val = normalize_text(raw_value, max_length=255)
            normalized["product_name"] = val

        elif canonical_field == "description":
            normalized["description"] = normalize_text(raw_value, max_length=5000)

        elif canonical_field == "category":
            top_cat, original_hierarchy = normalize_category(raw_value)
            normalized["category"] = top_cat
            normalized["category_hierarchy"] = original_hierarchy

        elif canonical_field == "brand":
            normalized["brand"] = normalize_text(raw_value, max_length=100)

        elif canonical_field == "retail_price":
            price = normalize_price(raw_value)
            normalized["retail_price"] = price  # May be None
            if price is None and raw_value.strip():
                errors.append({
                    "field": "retail_price",
                    "error": "Cannot parse retail price",
                    "original_value": raw_value[:100],
                    "severity": "WARNING"
                })

        elif canonical_field == "discounted_price":
            price = normalize_price(raw_value)
            normalized["discounted_price"] = price  # May be None
            if price is None and raw_value.strip():
                errors.append({
                    "field": "discounted_price",
                    "error": "Cannot parse discounted price",
                    "original_value": raw_value[:100],
                    "severity": "WARNING"
                })

        elif canonical_field == "product_rating":
            normalized["product_rating"] = normalize_rating(raw_value)

        elif canonical_field == "image":
            normalized["image_urls"] = normalize_images(raw_value)

        elif canonical_field == "product_specifications":
            normalized["specifications"] = normalize_specs(raw_value)

        elif canonical_field == "source_product_id":
            normalized["source_product_id"] = normalize_text(raw_value, max_length=200)

        elif canonical_field == "inventory":
            normalized["inventory"] = normalize_inventory(raw_value)

    # Default inventory if not mapped
    if "inventory" not in normalized:
        normalized["inventory"] = default_inventory

    return normalized, errors

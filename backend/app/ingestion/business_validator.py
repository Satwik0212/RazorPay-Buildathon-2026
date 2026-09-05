"""
Deterministic Business Validator for imported rows.
Backend enforces all rules. LLM never decides validation.
"""
from typing import Any, Dict, List


class RowValidationResult:
    def __init__(self, is_valid, errors):
        self.is_valid = is_valid
        self.errors = errors


def validate_row(row_index, normalized):
    errors = []

    name = normalized.get("product_name", "")
    if not name or not name.strip():
        errors.append({"row": row_index, "field": "product_name",
                       "error": "Product name is required", "original_value": name, "severity": "ERROR"})

    retail = normalized.get("retail_price")
    discounted = normalized.get("discounted_price")

    if retail is not None and retail < 0:
        errors.append({"row": row_index, "field": "retail_price",
                       "error": "Retail price cannot be negative", "original_value": retail, "severity": "ERROR"})
        retail = None

    if discounted is not None and discounted < 0:
        errors.append({"row": row_index, "field": "discounted_price",
                       "error": "Discounted price cannot be negative", "original_value": discounted, "severity": "ERROR"})
        discounted = None

    if retail is None and discounted is None:
        errors.append({"row": row_index, "field": "price",
                       "error": "At least one of retail_price or discounted_price required",
                       "original_value": None, "severity": "ERROR"})

    if retail is not None and discounted is not None and discounted > retail:
        errors.append({"row": row_index, "field": "discounted_price",
                       "error": f"Discounted price ({discounted/100:.2f}) exceeds retail price ({retail/100:.2f})",
                       "original_value": discounted, "severity": "ERROR"})

    inventory = normalized.get("inventory", 0)
    if isinstance(inventory, int) and inventory < 0:
        errors.append({"row": row_index, "field": "inventory",
                       "error": "Inventory cannot be negative", "original_value": inventory, "severity": "WARNING"})

    rating = normalized.get("product_rating")
    if rating is not None and not (0.0 <= rating <= 5.0):
        errors.append({"row": row_index, "field": "product_rating",
                       "error": f"Rating {rating} out of valid range 0-5",
                       "original_value": rating, "severity": "WARNING"})

    has_error = any(e["severity"] == "ERROR" for e in errors)
    return RowValidationResult(is_valid=not has_error, errors=errors)


def select_price(normalized):
    """Canonical price selection: discounted_price > retail_price."""
    discounted = normalized.get("discounted_price")
    retail = normalized.get("retail_price")
    if discounted is not None and discounted > 0:
        return discounted
    if retail is not None and retail > 0:
        return retail
    return 0

import hashlib
import json
from typing import Any, Dict


def generate_quote_hash(cart_id: str, items: list[dict], subtotal: int, discount: int, shipping: int, tax: int, total: int) -> str:
    """
    Computes a cryptographic digest representing the exact quote parameters.
    """
    data = {
        "cart_id": str(cart_id),
        "items": sorted(items, key=lambda x: str(x.get("product_id", ""))),
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "tax": tax,
        "total": total,
    }
    payload = json.dumps(data, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

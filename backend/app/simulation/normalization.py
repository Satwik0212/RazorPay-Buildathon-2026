import re
from typing import Dict, Any, Optional

class MetadataNormalizer:
    """
    Normalizes product metadata for the simulation and scoring pipeline.
    Handles legacy aliases, safe type casting, and fallback behavior.
    """

    @staticmethod
    def _normalize_warranty(raw_val: Any) -> Optional[bool]:
        if raw_val is None:
            return None
        if isinstance(raw_val, bool):
            return raw_val
        val_str = str(raw_val).strip().lower()
        if val_str in ['true', 'yes', '1']:
            return True
        if val_str in ['false', 'no', '0', 'none', 'no warranty', 'n/a']:
            return False
        # Match descriptive warranty periods or phrases
        if re.search(r'\b\d+\s*(?:year|yr|month|mth|day)s?\b', val_str) or 'warranty' in val_str:
            if any(neg in val_str for neg in ['no ', 'not ', 'without ']):
                return False
            return True
        return None

    @staticmethod
    def normalize(product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts and normalizes metadata from a product dictionary.
        Returns a new metadata dictionary with clean, expected keys.
        """
        raw_meta = product.get("product_metadata") or product.get("metadata") or {}
        normalized = dict(raw_meta)  # Shallow copy to preserve existing keys

        # 1. Normalize Rating (handling falsy 0 / 0.0 with explicit presence checks)
        rating_raw = None
        for key in ("rating", "product_rating", "overall_rating"):
            if key in raw_meta and raw_meta[key] is not None:
                rating_raw = raw_meta[key]
                break

        if rating_raw is not None:
            try:
                # Handle cases like "4.8/5.0", "4.8 / 5", or "4.8"
                rating_str = str(rating_raw).split('/')[0].strip()
                rating_val = float(rating_str)
                normalized["rating"] = rating_val
            except (ValueError, TypeError):
                normalized.pop("rating", None)
        else:
            normalized.pop("rating", None)

        # 2. Normalize Delivery Days
        if "delivery_days" in raw_meta and raw_meta["delivery_days"] is not None:
            try:
                normalized["delivery_days"] = float(str(raw_meta["delivery_days"]).strip())
            except (ValueError, TypeError):
                normalized.pop("delivery_days", None)
        else:
            normalized.pop("delivery_days", None)

        # 3. Normalize Return Days & Policy
        if "return_days" in raw_meta and raw_meta["return_days"] is not None:
            try:
                normalized["return_days"] = float(str(raw_meta["return_days"]).strip())
            except (ValueError, TypeError):
                normalized.pop("return_days", None)
        else:
            normalized.pop("return_days", None)

        # Ensure return_policy is set if returnable is true
        if "return_policy" not in normalized:
            returnable = raw_meta.get("returnable")
            if returnable is not None and str(returnable).lower() in ['true', 'yes', '1']:
                normalized["return_policy"] = True

        # 4. Normalize Warranty
        warranty_val = None
        if "warranty" in raw_meta and raw_meta["warranty"] is not None:
            warranty_val = MetadataNormalizer._normalize_warranty(raw_meta["warranty"])
        else:
            specs = raw_meta.get("specifications") or raw_meta.get("specs")
            if isinstance(specs, dict) and "warranty" in specs:
                warranty_val = MetadataNormalizer._normalize_warranty(specs.get("warranty"))
            elif isinstance(specs, list):
                for spec in specs:
                    if isinstance(spec, dict):
                        k = str(spec.get("name", "")).lower()
                        if "warranty" in k:
                            warranty_val = MetadataNormalizer._normalize_warranty(spec.get("value"))
                            break

        if warranty_val is not None:
            normalized["warranty"] = warranty_val
        else:
            normalized.pop("warranty", None)

        return normalized

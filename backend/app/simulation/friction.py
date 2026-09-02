from enum import Enum
from typing import List, Dict, Any, Optional


class FrictionReason(Enum):
    PRICE_MISMATCH = "PRICE_MISMATCH"
    MISSING_FEATURE = "MISSING_FEATURE"
    DELIVERY_UNCLEAR = "DELIVERY_UNCLEAR"
    DELIVERY_TOO_SLOW = "DELIVERY_TOO_SLOW"
    DELIVERY_UNKNOWN = "DELIVERY_UNKNOWN"
    RETURN_UNCLEAR = "RETURN_UNCLEAR"
    INSUFFICIENT_PRODUCT_INFORMATION = "INSUFFICIENT_PRODUCT_INFORMATION"
    NO_SUITABLE_PRODUCT = "NO_SUITABLE_PRODUCT"
    INVENTORY_ISSUE = "INVENTORY_ISSUE"

class FrictionDetector:
    """
    Evaluates where simulated buyers experience friction or rejection during evaluation.
    Distinguishes between hard rejection blockers and soft evaluation friction.
    """

    @staticmethod
    def detect_hard_constraints(
        product: Dict[str, Any],
        intent: Dict[str, Any]
    ) -> List[FrictionReason]:
        """
        Hard constraint filter: Identifies absolute disqualifying factors.
        """
        reasons: List[FrictionReason] = []
        price = product.get("price", 0)
        metadata = product.get("product_metadata") or product.get("metadata") or {}

        # 1. Budget hard limit check
        max_budget = intent.get("max_budget")
        if max_budget is not None and price > max_budget:
            reasons.append(FrictionReason.PRICE_MISMATCH)

        # 2. Inventory / Active availability check
        if product.get("is_active") is False:
            reasons.append(FrictionReason.INVENTORY_ISSUE)
        if product.get("available_quantity") is not None and product.get("available_quantity") <= 0:
            reasons.append(FrictionReason.INVENTORY_ISSUE)

        # 3. Explicit Required Features check
        product_text = f"{product.get('name', '')} {product.get('description', '')}".lower()
        for req in intent.get("requirements", []):
            req_clean = req.lower().replace("_", " ")
            
            # Check structured metadata first
            meta_val = metadata.get(req.lower())
            if meta_val is not None:
                if str(meta_val).lower() not in ["true", "yes", "1"]:
                    reasons.append(FrictionReason.MISSING_FEATURE)
                continue
                
            # Free text fallback
            if req_clean not in product_text:
                reasons.append(FrictionReason.MISSING_FEATURE)
                continue
                
            # Check for negative formulations in text
            negative_phrases = [
                f"no {req_clean}",
                f"without {req_clean}",
                f"{req_clean} not provided",
                f"does not include {req_clean}"
            ]
            if any(neg in product_text for neg in negative_phrases):
                reasons.append(FrictionReason.MISSING_FEATURE)

        # 4. Explicit Delivery Deadline check
        deadline_days = intent.get("delivery_deadline_days")
        if deadline_days is not None:
            delivery_days = metadata.get("delivery_days")
            if delivery_days is None:
                reasons.append(FrictionReason.DELIVERY_UNKNOWN)
            elif float(delivery_days) > float(deadline_days):
                reasons.append(FrictionReason.DELIVERY_TOO_SLOW)

        return list(set(reasons))

    @staticmethod
    def detect_soft_friction(
        product: Dict[str, Any],
        persona_weights: Dict[str, float]
    ) -> List[FrictionReason]:
        """
        Soft friction evaluation: Identifies attributes that reduce buyer confidence or score.
        """
        reasons: List[FrictionReason] = []
        metadata = product.get("product_metadata") or product.get("metadata") or {}
        w_delivery = persona_weights.get("delivery", persona_weights.get("speed", 0.0))
        w_returns = persona_weights.get("returns", persona_weights.get("return_policy", 0.0))
        w_metadata = persona_weights.get("metadata", persona_weights.get("specifications", 0.0))

        # Delivery information missing for speed-sensitive personas
        if w_delivery >= 0.20 and "delivery_days" not in metadata:
            reasons.append(FrictionReason.DELIVERY_UNCLEAR)

        # Return policy missing for return/quality sensitive personas
        if w_returns >= 0.10 and "return_days" not in metadata and "return_policy" not in metadata:
            reasons.append(FrictionReason.RETURN_UNCLEAR)

        # Incomplete product information
        desc = product.get("description") or ""
        if len(desc.strip()) < 15 or (w_metadata >= 0.20 and len(metadata) < 2):
            reasons.append(FrictionReason.INSUFFICIENT_PRODUCT_INFORMATION)

        return list(set(reasons))

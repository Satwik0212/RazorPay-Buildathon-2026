from enum import Enum
from typing import List, Dict, Any

class FrictionReason(Enum):
    PRICE_MISMATCH = "PRICE_MISMATCH"
    MISSING_FEATURE = "MISSING_FEATURE"
    DELIVERY_UNCLEAR = "DELIVERY_UNCLEAR"
    RETURN_UNCLEAR = "RETURN_UNCLEAR"
    INSUFFICIENT_PRODUCT_INFORMATION = "INSUFFICIENT_PRODUCT_INFORMATION"
    NO_SUITABLE_PRODUCT = "NO_SUITABLE_PRODUCT"
    INVENTORY_ISSUE = "INVENTORY_ISSUE"

class FrictionDetector:
    @staticmethod
    def detect_hard_constraints(product: Dict[str, Any], intent: Dict[str, Any]) -> List[FrictionReason]:
        reasons = []
        if intent.get("max_budget") and product.get("price", 0) > intent["max_budget"]:
            reasons.append(FrictionReason.PRICE_MISMATCH)
        
        # inventory issue if active is false or out of stock in some way
        if not product.get("is_active", True):
            reasons.append(FrictionReason.INVENTORY_ISSUE)
            
        for req in intent.get("requirements", []):
            metadata = product.get("metadata", {})
            # just a simple mock check
            if str(metadata.get(req.lower(), "")) != "true" and req.lower() not in str(metadata).lower():
                reasons.append(FrictionReason.MISSING_FEATURE)
                
        return reasons
        
    @staticmethod
    def detect_soft_friction(product: Dict[str, Any], persona_weights: Dict[str, float]) -> List[FrictionReason]:
        reasons = []
        metadata = product.get("metadata", {})
        
        if persona_weights.get("delivery", 0) > 0.2 and not metadata.get("delivery_days"):
            reasons.append(FrictionReason.DELIVERY_UNCLEAR)
            
        if persona_weights.get("returns", 0) > 0.1 and not metadata.get("return_policy"):
            reasons.append(FrictionReason.RETURN_UNCLEAR)
            
        if not product.get("description"):
            reasons.append(FrictionReason.INSUFFICIENT_PRODUCT_INFORMATION)
            
        return list(set(reasons))

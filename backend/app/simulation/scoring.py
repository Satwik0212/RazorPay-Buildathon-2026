from typing import Dict, Any

class ProductScorer:
    @staticmethod
    def calculate_score(product: Dict[str, Any], persona_weights: Dict[str, float]) -> float:
        """
        Deterministically calculate a product score based on persona weights.
        All normalized feature scores are mocked between 0.0 and 1.0.
        """
        price = product.get("price", 0)
        # Mock normalization: lower price is better. Max typical price = 1000000 minor units.
        price_score = max(0.0, 1.0 - (price / 1000000.0))
        
        metadata = product.get("metadata", {})
        
        # Lower delivery days = better
        delivery_days = float(metadata.get("delivery_days", 7))
        delivery_score = max(0.0, 1.0 - (delivery_days / 14.0))
        
        # Mock quality
        quality_score = 0.8 if metadata.get("high_quality") else 0.5
        
        # Higher return days = better
        return_days = float(metadata.get("return_days", 0))
        return_score = min(1.0, return_days / 30.0)
        
        # Has offer
        offer_score = 1.0 if metadata.get("has_offer") else 0.0
        
        # Metadata richness
        metadata_score = min(1.0, len(metadata) / 5.0)
        
        total = (
            price_score * persona_weights.get("price", 0.0) +
            delivery_score * persona_weights.get("delivery", 0.0) +
            quality_score * persona_weights.get("quality", 0.0) +
            return_score * persona_weights.get("returns", 0.0) +
            offer_score * persona_weights.get("offers", 0.0) +
            metadata_score * persona_weights.get("metadata", 0.0)
        )
        
        return round(total, 3)

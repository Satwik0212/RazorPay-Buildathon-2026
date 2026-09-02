from typing import Dict, Any, Optional


class ProductScorer:
    """
    Deterministic scoring engine for buyer simulations.
    Maps product commerce attributes to normalized feature values (0.0 to 1.0)
    and calculates preference-weighted scores based on synthetic buyer personas.
    """

    @staticmethod
    def calculate_score(
        product: Dict[str, Any],
        persona_weights: Dict[str, float],
        max_budget_minor: Optional[int] = None
    ) -> float:
        """
        Deterministically calculate a product score based on persona weights.
        All normalized feature scores are in range [0.0, 1.0].
        """
        from app.simulation.normalization import MetadataNormalizer
        metadata = MetadataNormalizer.normalize(product)
        price = product.get("price", 0)

        # Normalize weight keys early (handling aliases)
        w_price = persona_weights.get("price", 0.0)
        w_delivery = persona_weights.get("delivery", persona_weights.get("speed", 0.0))
        w_quality = persona_weights.get("quality", 0.0)
        w_returns = persona_weights.get("returns", persona_weights.get("return_policy", 0.0))
        w_offers = persona_weights.get("offers", persona_weights.get("discount", 0.0))
        w_metadata = persona_weights.get("metadata", persona_weights.get("specifications", persona_weights.get("stock", 0.0)))

        # Fallback if no specific weights given
        total_w = w_price + w_delivery + w_quality + w_returns + w_offers + w_metadata
        if total_w == 0:
            w_price = w_quality = w_delivery = 0.33
            total_w = 1.0

        # 1. Price Score: Lower price relative to benchmark / budget = higher score
        if max_budget_minor and max_budget_minor > 0:
            if price <= max_budget_minor:
                savings_ratio = (max_budget_minor - price) / max_budget_minor
                
                # If price is a dominant factor, reward maximum savings linearly
                if w_price >= 0.3:
                    price_score = 0.5 + (0.5 * min(max(savings_ratio, 0.0), 1.0))
                else:
                    # For non-budget personas, satisfying the budget provides a strong baseline
                    # score (0.8) and extreme savings offer only marginal improvement
                    price_score = 0.8 + (0.2 * min(max(savings_ratio, 0.0), 1.0))
            else:
                price_score = max(0.0, 0.5 - ((price - max_budget_minor) / max_budget_minor))
        else:
            # Benchmark normalization against standard minor unit scale
            price_score = max(0.1, 1.0 - (price / 2000000.0))

        # 2. Delivery / Speed Score
        delivery_days_raw = metadata.get("delivery_days")
        if delivery_days_raw is None:
            delivery_score = 0.30  # Unknown delivery receives a neutral penalty, not assumed good
        else:
            delivery_days = float(delivery_days_raw)
            if delivery_days <= 1:
                delivery_score = 1.0
            elif delivery_days <= 2:
                delivery_score = 0.90
            elif delivery_days <= 3:
                delivery_score = 0.75
            elif delivery_days <= 5:
                delivery_score = 0.55
            elif delivery_days <= 7:
                delivery_score = 0.40
            else:
                delivery_score = max(0.1, 1.0 - (delivery_days / 14.0))

        # 3. Quality & Brand Score
        rating_raw = metadata.get("rating")
        if rating_raw is None:
            rating_score = 0.35  # Neutral default (equivalent to 2.5 stars) instead of 4.0
        else:
            rating_score = min(max(float(rating_raw) / 5.0, 0.0), 1.0) * 0.7
            
        warranty_raw = metadata.get("warranty")
        if warranty_raw is None:
            has_warranty = 0.05  # Slight boost for possibility, but less than verified 0.2
        elif str(warranty_raw).lower() in ['true', 'yes', '1']:
            has_warranty = 0.2
        else:
            has_warranty = 0.0
            
        premium_raw = metadata.get("high_quality") or metadata.get("premium")
        if premium_raw is None:
            is_premium = 0.0
        elif str(premium_raw).lower() in ['true', 'yes', '1']:
            is_premium = 0.1
        else:
            is_premium = 0.0
            
        quality_score = min(1.0, rating_score + has_warranty + is_premium)

        # 4. Return Policy Score
        return_days_raw = metadata.get("return_days")
        if return_days_raw is None:
            if metadata.get("return_policy"):
                return_score = 0.50
            else:
                return_score = 0.20  # Neutral instead of pessimistic 0.10
        else:
            return_days = float(return_days_raw)
            if return_days >= 30:
                return_score = 1.0
            elif return_days >= 14:
                return_score = 0.85
            elif return_days >= 7:
                return_score = 0.60
            else:
                return_score = 0.10

        # 5. Offer & Discount Score
        discount_percent = float(metadata.get("discount_percent", 0))
        if discount_percent > 0:
            offer_score = min(1.0, 0.4 + (discount_percent / 50.0) * 0.6)
        elif metadata.get("has_offer") or metadata.get("has_discount"):
            offer_score = 0.75
        else:
            offer_score = 0.10

        # 6. Metadata & Feature Richness Score
        desc_length = len(product.get("description") or "")
        # Scale: 500 chars = 0.4 (max)
        desc_score = min(0.4, (desc_length / 500.0) * 0.4) 
        raw_meta = product.get("product_metadata") or product.get("metadata") or {}
        meta_count = len(raw_meta)
        # Scale: 15 keys = 0.6 (max)
        meta_score = min(0.6, (meta_count / 15.0) * 0.6)   
        metadata_score = desc_score + meta_score

        raw_score = (
            (price_score * w_price) +
            (delivery_score * w_delivery) +
            (quality_score * w_quality) +
            (return_score * w_returns) +
            (offer_score * w_offers) +
            (metadata_score * w_metadata)
        ) / total_w

        return round(min(max(raw_score, 0.0), 1.0), 3)

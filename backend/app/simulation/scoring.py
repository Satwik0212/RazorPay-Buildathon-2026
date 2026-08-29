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
        metadata = product.get("product_metadata") or product.get("metadata") or {}
        price = product.get("price", 0)

        # 1. Price Score: Lower price relative to benchmark / budget = higher score
        if max_budget_minor and max_budget_minor > 0:
            if price <= max_budget_minor:
                # Scaled between 0.5 and 1.0 based on savings
                savings_ratio = (max_budget_minor - price) / max_budget_minor
                price_score = 0.5 + (0.5 * min(max(savings_ratio, 0.0), 1.0))
            else:
                price_score = max(0.0, 0.5 - ((price - max_budget_minor) / max_budget_minor))
        else:
            # Benchmark normalization against standard minor unit scale
            price_score = max(0.1, 1.0 - (price / 2000000.0))

        # 2. Delivery / Speed Score
        delivery_days = float(metadata.get("delivery_days", 5))
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
        rating = float(metadata.get("rating", 4.0))
        rating_score = min(max(rating / 5.0, 0.0), 1.0)
        has_warranty = 0.2 if metadata.get("warranty") else 0.0
        is_premium = 0.1 if metadata.get("high_quality") or metadata.get("premium") else 0.0
        quality_score = min(1.0, (rating_score * 0.7) + has_warranty + is_premium)

        # 4. Return Policy Score
        return_days = float(metadata.get("return_days", 0))
        if return_days >= 30:
            return_score = 1.0
        elif return_days >= 14:
            return_score = 0.85
        elif return_days >= 7:
            return_score = 0.60
        elif metadata.get("return_policy"):
            return_score = 0.50
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
        desc_score = min(0.4, desc_length / 200.0)
        meta_count = len(metadata)
        meta_score = min(0.6, meta_count / 5.0)
        metadata_score = desc_score + meta_score

        # Normalize weight keys (handling aliases)
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

        raw_score = (
            (price_score * w_price) +
            (delivery_score * w_delivery) +
            (quality_score * w_quality) +
            (return_score * w_returns) +
            (offer_score * w_offers) +
            (metadata_score * w_metadata)
        ) / total_w

        return round(min(max(raw_score, 0.0), 1.0), 3)

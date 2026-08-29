import uuid
from typing import List, Dict, Any
from app.models.optimization_recommendation import OptimizationRecommendation
from app.simulation.friction import FrictionReason
from app.core.constants import RecommendationStatus


class RecommendationService:
    """
    Transforms observed simulation friction and drop-offs into actionable,
    structured merchant optimization recommendations.
    """

    def generate_recommendations(
        self,
        merchant_id: uuid.UUID,
        friction_events: List[Dict[str, Any]]
    ) -> List[OptimizationRecommendation]:
        """
        Maps observed friction occurrences to evidence-backed optimization recommendations.
        """
        recommendations: List[OptimizationRecommendation] = []
        
        # Group friction by (product_id, reason)
        friction_counts: Dict[tuple, int] = {}
        for event in friction_events:
            p_id = event.get("product_id")
            reason = event.get("reason")
            count = event.get("count", 1)
            key = (p_id, reason)
            friction_counts[key] = friction_counts.get(key, 0) + count

        for (p_id_str, reason), count in friction_counts.items():
            p_uuid = None
            if p_id_str:
                try:
                    p_uuid = uuid.UUID(p_id_str) if isinstance(p_id_str, str) else p_id_str
                except Exception:
                    p_uuid = None

            if reason == FrictionReason.DELIVERY_UNCLEAR.value or reason == "DELIVERY_UNCLEAR":
                recommendations.append(OptimizationRecommendation(
                    merchant_id=merchant_id,
                    product_id=p_uuid,
                    type="DELIVERY_CLARITY",
                    title="Add Explicit Delivery Timeline",
                    reason=f"{count} simulated speed-focused buyers abandoned due to missing or delayed delivery promises.",
                    action_data={
                        "suggested_change": "Configure 'delivery_days: 2' or express shipping in product metadata.",
                        "friction_count": count,
                        "friction_type": "DELIVERY_UNCLEAR",
                    },
                    expected_simulated_impact=0.22,
                    confidence=0.90,
                    status=RecommendationStatus.PROPOSED.value,
                ))

            elif reason == FrictionReason.PRICE_MISMATCH.value or reason == "PRICE_MISMATCH":
                recommendations.append(OptimizationRecommendation(
                    merchant_id=merchant_id,
                    product_id=p_uuid,
                    type="PRICE_COMPETITIVENESS",
                    title="Adjust Price or Add Promotional Discount",
                    reason=f"{count} simulated budget-conscious buyers rejected this item because price exceeded budget constraint.",
                    action_data={
                        "suggested_change": "Introduce a 5-10% promotional discount offer to capture budget buyer segment.",
                        "friction_count": count,
                        "friction_type": "PRICE_MISMATCH",
                    },
                    expected_simulated_impact=0.28,
                    confidence=0.85,
                    status=RecommendationStatus.PROPOSED.value,
                ))

            elif reason == FrictionReason.RETURN_UNCLEAR.value or reason == "RETURN_UNCLEAR":
                recommendations.append(OptimizationRecommendation(
                    merchant_id=merchant_id,
                    product_id=p_uuid,
                    type="RETURN_POLICY_CLARITY",
                    title="Clarify Return & Refund Policy",
                    reason=f"{count} quality-focused buyers hesitated due to unstated return terms.",
                    action_data={
                        "suggested_change": "Add explicit 'return_days: 14' or 'return_policy: full refund' in product metadata.",
                        "friction_count": count,
                        "friction_type": "RETURN_UNCLEAR",
                    },
                    expected_simulated_impact=0.15,
                    confidence=0.88,
                    status=RecommendationStatus.PROPOSED.value,
                ))

            elif reason == FrictionReason.INSUFFICIENT_PRODUCT_INFORMATION.value or reason == "INSUFFICIENT_PRODUCT_INFORMATION":
                recommendations.append(OptimizationRecommendation(
                    merchant_id=merchant_id,
                    product_id=p_uuid,
                    type="CATALOGUE_ENRICHMENT",
                    title="Enrich Product Specifications & Description",
                    reason=f"{count} feature-focused buyers skipped this product due to sparse specifications or brief description.",
                    action_data={
                        "suggested_change": "Expand product description and add structured technical attributes to metadata.",
                        "friction_count": count,
                        "friction_type": "INSUFFICIENT_PRODUCT_INFORMATION",
                    },
                    expected_simulated_impact=0.18,
                    confidence=0.92,
                    status=RecommendationStatus.PROPOSED.value,
                ))

            elif reason == FrictionReason.INVENTORY_ISSUE.value or reason == "INVENTORY_ISSUE":
                recommendations.append(OptimizationRecommendation(
                    merchant_id=merchant_id,
                    product_id=p_uuid,
                    type="INVENTORY_RESTORATION",
                    title="Restock or Reactivate Inactive Listing",
                    reason=f"{count} potential purchases were blocked due to out-of-stock inventory or deactivated listing.",
                    action_data={
                        "suggested_change": "Increase available inventory quantity and ensure active status is enabled.",
                        "friction_count": count,
                        "friction_type": "INVENTORY_ISSUE",
                    },
                    expected_simulated_impact=0.50,
                    confidence=0.99,
                    status=RecommendationStatus.PROPOSED.value,
                ))

        return recommendations


recommendation_service = RecommendationService()

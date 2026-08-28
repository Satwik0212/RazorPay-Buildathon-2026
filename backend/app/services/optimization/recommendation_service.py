from typing import List, Dict, Any
from app.models.optimization_recommendation import OptimizationRecommendation
from app.simulation.friction import FrictionReason
from app.core.constants import RecommendationStatus

class RecommendationService:
    def generate_recommendations(self, merchant_id: str, friction_events: List[Dict[str, Any]]) -> List[OptimizationRecommendation]:
        """
        Maps observed friction to actionable optimization recommendations.
        """
        recommendations = []
        
        for event in friction_events:
            reason = event.get("reason")
            product_id = event.get("product_id")
            count = event.get("count", 0)
            
            if reason == FrictionReason.DELIVERY_UNCLEAR.value:
                recommendations.append(OptimizationRecommendation(
                    merchant_id=merchant_id,
                    product_id=product_id,
                    type="DELIVERY_CLARITY",
                    title="Missing Delivery Information",
                    reason=f"{count} buyers experienced friction because delivery time is missing or unclear.",
                    action_data={"suggested_change": "Add explicit 'delivery_days' to product metadata.", "friction_count": count},
                    status=RecommendationStatus.PROPOSED.value
                ))
            elif reason == FrictionReason.PRICE_MISMATCH.value:
                recommendations.append(OptimizationRecommendation(
                    merchant_id=merchant_id,
                    product_id=product_id,
                    type="PRICE_COMPETITIVENESS",
                    title="Price Exceeds Buyer Budgets",
                    reason=f"{count} buyers filtered out this product due to price mismatch with budget constraints.",
                    action_data={"suggested_change": "Consider adding a discount offer or reducing the base price.", "friction_count": count},
                    status=RecommendationStatus.PROPOSED.value
                ))
            elif reason == FrictionReason.RETURN_UNCLEAR.value:
                recommendations.append(OptimizationRecommendation(
                    merchant_id=merchant_id,
                    product_id=product_id,
                    type="RETURN_POLICY_CLARITY",
                    title="Missing Return Policy",
                    reason=f"{count} buyers experienced friction because return policy is missing.",
                    action_data={"suggested_change": "Add 'return_days' or 'return_policy' to product metadata.", "friction_count": count},
                    status=RecommendationStatus.PROPOSED.value
                ))
                
        return recommendations

recommendation_service = RecommendationService()

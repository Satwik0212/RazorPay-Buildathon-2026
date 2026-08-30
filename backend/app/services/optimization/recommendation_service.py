import uuid
from typing import List, Dict, Any, Optional
from app.models.optimization_recommendation import OptimizationRecommendation
from app.simulation.friction import FrictionReason
from app.core.constants import RecommendationStatus


from sqlalchemy.orm import Session

class RecommendationService:
    """
    Transforms observed simulation friction and drop-offs into actionable,
    structured merchant optimization recommendations.
    """

    def generate_recommendations(
        self,
        db: Session,
        merchant_id: uuid.UUID,
        friction_events: List[Dict[str, Any]],
        simulation_run_id: Optional[uuid.UUID] = None
    ) -> List[OptimizationRecommendation]:
        """
        Maps observed friction occurrences to evidence-backed optimization recommendations.
        Persists them to the database.
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

            rec_type = None
            title = None
            rec_reason = None
            action_data = None
            impact = 0.0
            confidence = 0.0

            if reason == FrictionReason.DELIVERY_UNCLEAR.value or reason == "DELIVERY_UNCLEAR":
                rec_type = "DELIVERY_CLARITY"
                title = "Add Explicit Delivery Timeline"
                rec_reason = f"{count} simulated speed-focused buyers abandoned due to missing or delayed delivery promises."
                action_data = {
                    "suggested_change": "Configure 'delivery_days: 2' or express shipping in product metadata.",
                    "friction_count": count,
                    "friction_type": "DELIVERY_UNCLEAR",
                }
                impact = 0.22
                confidence = 0.90

            elif reason == FrictionReason.PRICE_MISMATCH.value or reason == "PRICE_MISMATCH":
                rec_type = "PRICE_COMPETITIVENESS"
                title = "Adjust Price or Add Promotional Discount"
                rec_reason = f"{count} simulated budget-conscious buyers rejected this item because price exceeded budget constraint."
                action_data = {
                    "suggested_change": "Introduce a 5-10% promotional discount offer to capture budget buyer segment.",
                    "friction_count": count,
                    "friction_type": "PRICE_MISMATCH",
                }
                impact = 0.28
                confidence = 0.85

            elif reason == FrictionReason.RETURN_UNCLEAR.value or reason == "RETURN_UNCLEAR":
                rec_type = "RETURN_POLICY_CLARITY"
                title = "Clarify Return & Refund Policy"
                rec_reason = f"{count} quality-focused buyers hesitated due to unstated return terms."
                action_data = {
                    "suggested_change": "Add explicit 'return_days: 14' or 'return_policy: full refund' in product metadata.",
                    "friction_count": count,
                    "friction_type": "RETURN_UNCLEAR",
                }
                impact = 0.15
                confidence = 0.88

            elif reason == FrictionReason.INSUFFICIENT_PRODUCT_INFORMATION.value or reason == "INSUFFICIENT_PRODUCT_INFORMATION":
                rec_type = "CATALOGUE_ENRICHMENT"
                title = "Enrich Product Specifications & Description"
                rec_reason = f"{count} feature-focused buyers skipped this product due to sparse specifications or brief description."
                action_data = {
                    "suggested_change": "Expand product description and add structured technical attributes to metadata.",
                    "friction_count": count,
                    "friction_type": "INSUFFICIENT_PRODUCT_INFORMATION",
                }
                impact = 0.18
                confidence = 0.92

            elif reason == FrictionReason.INVENTORY_ISSUE.value or reason == "INVENTORY_ISSUE":
                rec_type = "INVENTORY_RESTORATION"
                title = "Restock or Reactivate Inactive Listing"
                rec_reason = f"{count} potential purchases were blocked due to out-of-stock inventory or deactivated listing."
                action_data = {
                    "suggested_change": "Increase available inventory quantity and ensure active status is enabled.",
                    "friction_count": count,
                    "friction_type": "INVENTORY_ISSUE",
                }
                impact = 0.50
                confidence = 0.99

            if rec_type:
                # Check for existing PROPOSED recommendation of this type for this product
                existing_rec = db.query(OptimizationRecommendation).filter(
                    OptimizationRecommendation.merchant_id == merchant_id,
                    OptimizationRecommendation.product_id == p_uuid,
                    OptimizationRecommendation.type == rec_type,
                    OptimizationRecommendation.status == RecommendationStatus.PROPOSED.value
                ).first()

                if existing_rec:
                    # Update existing recommendation with new evidence
                    existing_rec.reason = rec_reason
                    existing_rec.action_data = action_data
                    existing_rec.simulation_run_id = simulation_run_id
                    existing_rec.confidence = confidence
                    existing_rec.expected_simulated_impact = impact
                    recommendations.append(existing_rec)
                else:
                    new_rec = OptimizationRecommendation(
                        merchant_id=merchant_id,
                        simulation_run_id=simulation_run_id,
                        product_id=p_uuid,
                        type=rec_type,
                        title=title,
                        reason=rec_reason,
                        action_data=action_data,
                        expected_simulated_impact=impact,
                        confidence=confidence,
                        status=RecommendationStatus.PROPOSED.value,
                    )
                    db.add(new_rec)
                    recommendations.append(new_rec)

        db.commit()
        return recommendations


recommendation_service = RecommendationService()

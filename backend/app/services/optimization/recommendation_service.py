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
    Aggregates friction events by issue type to produce a small, prioritized set of recommendations.
    """

    def generate_recommendations(
        self,
        db: Session,
        merchant_id: uuid.UUID,
        friction_events: List[Dict[str, Any]],
        simulation_run_id: Optional[uuid.UUID] = None,
        scenario_count: int = 0
    ) -> List[OptimizationRecommendation]:
        """
        Maps observed friction occurrences to evidence-backed optimization recommendations.
        Aggregates by friction reason across the merchant's catalogue.
        Persists them to the database.
        """
        recommendations: List[OptimizationRecommendation] = []

        # Group friction by reason
        reason_groups: Dict[str, List[Dict[str, Any]]] = {}
        for event in friction_events:
            reason = event.get("reason")
            if not reason:
                continue
            if reason not in reason_groups:
                reason_groups[reason] = []
            reason_groups[reason].append(event)

        total_overall_frictions = sum(e.get("count", 1) for e in friction_events)

        # Process each reason group
        for reason, events in reason_groups.items():
            total_frictions = sum(e.get("count", 1) for e in events)

            # Count affected products and find the most affected one
            product_counts: Dict[str, int] = {}
            for e in events:
                p_id = e.get("product_id")
                if p_id:
                    product_counts[p_id] = product_counts.get(p_id, 0) + e.get("count", 1)

            unique_product_count = len(product_counts)

            # Use the most affected product as the primary example for What-If simulations
            top_product_id_str = None
            if product_counts:
                top_product_id_str = max(product_counts.items(), key=lambda x: x[1])[0]

            top_product_uuid = None
            if top_product_id_str:
                try:
                    top_product_uuid = uuid.UUID(top_product_id_str) if isinstance(top_product_id_str, str) else top_product_id_str
                except Exception:
                    top_product_uuid = None

            affected_product_ids = list(product_counts.keys())

            rec_type = None
            title = None
            rec_reason = None
            action_data = None

            # Deterministic, empirical impact scoring rather than fabricated percentages
            impact = round(total_frictions / max(total_overall_frictions, 1), 3)
            # Confidence grows logarithmically with evidence volume up to 1.0
            confidence = round(min(total_frictions / 20.0, 1.0), 3)

            # Map reason to recommendation details
            if reason == FrictionReason.DELIVERY_UNCLEAR.value or reason == "DELIVERY_UNCLEAR":
                # For DELIVERY_UNCLEAR (soft friction), there might not be a strict deadline in intent,
                # but if there happens to be one (or from other events), we try to extract it.
                deadlines = [e.get("delivery_deadline_days") for e in events if e.get("delivery_deadline_days") is not None]

                # If there are no deadlines, preserve the existing sensible fallback rather than inventing
                min_deadline = min(deadlines) if deadlines else 2

                rec_type = "DELIVERY_CLARITY"
                title = "Add Explicit Delivery Timeline"
                rec_reason = f"{total_frictions} simulated speed-focused buyer drop-offs occurred due to missing or delayed delivery promises across {unique_product_count} products."
                action_data = {
                    "suggested_change": f"Configure 'delivery_days: {min_deadline}' or express shipping in product metadata.",
                    "friction_count": total_frictions,
                    "affected_products_count": unique_product_count,
                    "friction_type": "DELIVERY_UNCLEAR",
                    "affected_product_ids": affected_product_ids,
                    "total_overall_frictions": total_overall_frictions,
                    "scenario_count": scenario_count,
                    "new_delivery_days": min_deadline,
                    "before_state_description": f"Unknown or >{min_deadline} days",
                    "after_state_description": f"{min_deadline} day{'s' if min_deadline != 1 else ''}"
                }

            elif reason == "DELIVERY_UNKNOWN" or (hasattr(FrictionReason, "DELIVERY_UNKNOWN") and reason == FrictionReason.DELIVERY_UNKNOWN.value):
                # Calculate minimum required deadline from evidence
                deadlines = [e.get("delivery_deadline_days") for e in events if e.get("delivery_deadline_days") is not None]

                if not deadlines:
                    continue

                min_deadline = min(deadlines)

                rec_type = "DELIVERY_UNKNOWN"
                title = "Add Structured Delivery Days"
                rec_reason = f"{total_frictions} simulated buyer drop-offs occurred because delivery requirements could not be verified across {unique_product_count} products."
                action_data = {
                    "suggested_change": f"Add structured 'delivery_days: {min_deadline}' information to metadata.",
                    "friction_count": total_frictions,
                    "affected_products_count": unique_product_count,
                    "friction_type": "DELIVERY_UNKNOWN",
                    "affected_product_ids": affected_product_ids,
                    "total_overall_frictions": total_overall_frictions,
                    "scenario_count": scenario_count,
                    "new_delivery_days": min_deadline,
                    "before_state_description": "Unknown (no delivery_days in metadata)",
                    "after_state_description": f"{min_deadline} day{'s' if min_deadline != 1 else ''} (structured)"
                }

            elif reason == "DELIVERY_TOO_SLOW" or (hasattr(FrictionReason, "DELIVERY_TOO_SLOW") and reason == FrictionReason.DELIVERY_TOO_SLOW.value):
                # Calculate minimum required deadline from evidence
                deadlines = [e.get("delivery_deadline_days") for e in events if e.get("delivery_deadline_days") is not None]

                # If there are no relevant delivery failures with a deadline, do not invent a recommendation
                if not deadlines:
                    continue

                min_deadline = min(deadlines)

                rec_type = "DELIVERY_TOO_SLOW"
                title = "Reduce Delivery Time"
                rec_reason = f"{total_frictions} simulated buyer drop-offs occurred because delivery time exceeded strict deadlines across {unique_product_count} products."
                action_data = {
                    "suggested_change": f"Reduce delivery time to {min_deadline} day{'s' if min_deadline != 1 else ''} to satisfy strict SLA constraints.",
                    "friction_count": total_frictions,
                    "affected_products_count": unique_product_count,
                    "friction_type": "DELIVERY_TOO_SLOW",
                    "affected_product_ids": affected_product_ids,
                    "total_overall_frictions": total_overall_frictions,
                    "scenario_count": scenario_count,
                    "new_delivery_days": min_deadline,
                    "before_state_description": f">{min_deadline} day{'s' if min_deadline != 1 else ''} (current delivery exceeds buyer SLA)",
                    "after_state_description": f"{min_deadline} day{'s' if min_deadline != 1 else ''} (SLA satisfied)"
                }

            elif reason == FrictionReason.PRICE_MISMATCH.value or reason == "PRICE_MISMATCH":
                rec_type = "PRICE_COMPETITIVENESS"
                title = "Adjust Price or Add Promotional Discount"
                rec_reason = f"{total_frictions} simulated budget-conscious buyer drop-offs occurred because prices exceeded budget constraints across {unique_product_count} products."
                # P0-5 FIX: Include new_price so Apply handler can mutate the product.
                # Suggest a 10% price reduction as the concrete action.
                action_data = {
                    "suggested_change": "Apply a 10% price reduction to improve budget-conscious buyer match rates.",
                    "friction_count": total_frictions,
                    "affected_products_count": unique_product_count,
                    "friction_type": "PRICE_MISMATCH",
                    "affected_product_ids": affected_product_ids,
                    "total_overall_frictions": total_overall_frictions,
                    "scenario_count": scenario_count,
                    "price_reduction_percent": 10,
                    # new_price will be computed per-product at apply time from price_reduction_percent.
                    # We set a sentinel value of -1 to signal "compute 10% discount per product".
                    "new_price_mode": "percent_discount",
                    "new_price_discount_pct": 10,
                }

            elif reason == FrictionReason.RETURN_UNCLEAR.value or reason == "RETURN_UNCLEAR":
                rec_type = "RETURN_POLICY_CLARITY"
                title = "Clarify Return & Refund Policy"
                rec_reason = f"{total_frictions} simulated buyer drop-offs occurred due to unstated return terms across {unique_product_count} products."
                # P0-5 FIX: Include new_return_days so Apply handler can mutate the product.
                action_data = {
                    "suggested_change": "Add a structured 14-day return policy to product metadata.",
                    "friction_count": total_frictions,
                    "affected_products_count": unique_product_count,
                    "friction_type": "RETURN_UNCLEAR",
                    "affected_product_ids": affected_product_ids,
                    "total_overall_frictions": total_overall_frictions,
                    "scenario_count": scenario_count,
                    "new_return_days": 14,
                    "before_state_description": "Unknown / unstated",
                    "after_state_description": "14 days",
                }

            elif reason == FrictionReason.INSUFFICIENT_PRODUCT_INFORMATION.value or reason == "INSUFFICIENT_PRODUCT_INFORMATION":
                rec_type = "CATALOGUE_ENRICHMENT"
                title = "Enrich Product Specifications & Description"
                rec_reason = f"{total_frictions} simulated buyer drop-offs occurred due to sparse specifications or descriptions across {unique_product_count} products."
                action_data = {
                    "suggested_change": "Expand product descriptions and add structured technical attributes to metadata.",
                    "friction_count": total_frictions,
                    "affected_products_count": unique_product_count,
                    "friction_type": "INSUFFICIENT_PRODUCT_INFORMATION",
                    "affected_product_ids": affected_product_ids,
                    "total_overall_frictions": total_overall_frictions,
                    "scenario_count": scenario_count,
                }

            elif reason == FrictionReason.INVENTORY_ISSUE.value or reason == "INVENTORY_ISSUE":
                rec_type = "INVENTORY_RESTORATION"
                title = "Restock or Reactivate Inactive Listings"
                rec_reason = f"{total_frictions} simulated purchase blocks occurred due to out-of-stock inventory or deactivated listings across {unique_product_count} products."
                # P0-5 FIX: Include new_inventory_count so Apply handler can mutate the product.
                action_data = {
                    "suggested_change": "Restock to 50 units and reactivate listings rejected due to zero inventory.",
                    "friction_count": total_frictions,
                    "affected_products_count": unique_product_count,
                    "friction_type": "INVENTORY_ISSUE",
                    "affected_product_ids": affected_product_ids,
                    "total_overall_frictions": total_overall_frictions,
                    "scenario_count": scenario_count,
                    "new_inventory_count": 50,
                    "before_state_description": "0 / inactive",
                    "after_state_description": "50 units, active",
                }

            elif reason == FrictionReason.MISSING_FEATURE.value or reason == "MISSING_FEATURE":
                rec_type = "MISSING_FEATURE"
                title = "Add Missing Feature Specifications"
                rec_reason = f"{total_frictions} simulated buyer drop-offs occurred because a required feature was missing or explicitly excluded across {unique_product_count} products."
                action_data = {
                    "suggested_change": "Add structured product specifications for required features so AI buyers can verify the requirement.",
                    "friction_count": total_frictions,
                    "affected_products_count": unique_product_count,
                    "friction_type": "MISSING_FEATURE",
                    "affected_product_ids": affected_product_ids,
                    "total_overall_frictions": total_overall_frictions,
                    "scenario_count": scenario_count,
                }

            if rec_type:
                # Check for existing PROPOSED recommendation of this type
                # We aggregate by `type` at the merchant level rather than per-product
                existing_rec = db.query(OptimizationRecommendation).filter(
                    OptimizationRecommendation.merchant_id == merchant_id,
                    OptimizationRecommendation.type == rec_type,
                    OptimizationRecommendation.status == RecommendationStatus.PROPOSED.value
                ).first()

                if existing_rec:
                    # Update existing recommendation with aggregated evidence
                    existing_rec.reason = rec_reason
                    existing_rec.action_data = action_data
                    existing_rec.simulation_run_id = simulation_run_id
                    existing_rec.confidence = confidence
                    existing_rec.expected_simulated_impact = impact
                    # Update top_product_id if we have one, otherwise leave it (or update it)
                    if top_product_uuid:
                        existing_rec.product_id = top_product_uuid
                    recommendations.append(existing_rec)
                else:
                    new_rec = OptimizationRecommendation(
                        merchant_id=merchant_id,
                        simulation_run_id=simulation_run_id,
                        product_id=top_product_uuid,
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

        # Sort recommendations by impact and friction count (highest first)
        recommendations.sort(key=lambda r: (r.expected_simulated_impact, r.action_data.get("friction_count", 0)), reverse=True)
        return recommendations


recommendation_service = RecommendationService()

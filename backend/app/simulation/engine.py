import uuid
from typing import List, Dict, Any, Optional
from .scoring import ProductScorer
from .friction import FrictionDetector, FrictionReason


class SimulationEngine:
    """
    Core deterministic simulation orchestrator.
    Evaluates synthetic buyer personas against merchant catalogue data.
    """

    def run_simulation(
        self,
        merchant_id: str,
        persona_weights: Dict[str, float],
        intent: Dict[str, Any],
        catalogue: List[Dict[str, Any]],
        persona_name: str = "SYNTHETIC_BUYER"
    ) -> Dict[str, Any]:
        """
        Executes a single deterministic simulation.
        Flow:
          Catalogue -> Hard Constraint Filtering -> Persona Scoring -> Ranking -> Selection & Friction Explanation
        """
        candidates = []
        all_evaluated_rankings = []
        observed_frictions = []

        max_budget = intent.get("max_budget")

        for product in catalogue:
            p_id = str(product.get("id"))
            p_name = product.get("name", "Product")

            # 1. Hard constraint filter
            hard_friction = FrictionDetector.detect_hard_constraints(product, intent)
            if hard_friction:
                friction_names = [f.value for f in hard_friction]
                for fn in friction_names:
                    f_event = {
                        "product_id": p_id,
                        "product_name": p_name,
                        "type": "HARD_CONSTRAINT",
                        "reason": fn,
                    }
                    if intent.get("delivery_deadline_days") is not None:
                        f_event["delivery_deadline_days"] = intent.get("delivery_deadline_days")
                    observed_frictions.append(f_event)
                all_evaluated_rankings.append({
                    "product_id": p_id,
                    "product_name": p_name,
                    "score": 0.0,
                    "rank": 999,
                    "frictions": friction_names,
                    "passed": False,
                    "price": product.get("price"),
                    "category": product.get("category"),
                })
                continue

            # 2. Soft friction evaluation
            soft_friction = FrictionDetector.detect_soft_friction(product, persona_weights)
            soft_friction_names = [f.value for f in soft_friction]
            for fn in soft_friction_names:
                observed_frictions.append({
                    "product_id": p_id,
                    "product_name": p_name,
                    "type": "SOFT_FRICTION",
                    "reason": fn,
                })

            # 3. Preference-weighted score calculation
            score, breakdown = ProductScorer.calculate_score_with_breakdown(product, persona_weights, max_budget)

            candidates.append({
                "product_id": p_id,
                "product_name": p_name,
                "score": score,
                "score_breakdown": breakdown,
                "friction_reasons": soft_friction_names,
                "product": product,
            })

        # Sort candidates descending by score with deterministic tie-breaking
        candidates.sort(
            key=lambda x: (-x["score"], str(x["product_id"]))
        )

        rankings = []
        for i, c in enumerate(candidates):
            rankings.append({
                "product_id": c["product_id"],
                "product_name": c["product_name"],
                "score": c["score"],
                "rank": i + 1,
                "frictions": c["friction_reasons"],
                "passed": True,
                "price": c["product"].get("price"),
                "category": c["product"].get("category"),
                "score_breakdown": c.get("score_breakdown"),
            })

        # Append failed products at the end
        rankings.extend([r for r in all_evaluated_rankings if not r["passed"]])

        selected_product_id = None
        selected_score = 0.0
        selected_score_breakdown = None
        selected_product_name = None
        selected_product_price = None
        selected_product_category = None
        reason_codes = []
        explanation = ""
        constraints_satisfied = False

        if candidates:
            best = candidates[0]
            selected_product_id = best["product_id"]
            selected_score = best["score"]
            selected_score_breakdown = best.get("score_breakdown")
            selected_product_name = best["product_name"]
            selected_product_price = best["product"].get("price")
            selected_product_category = best["product"].get("category")
            constraints_satisfied = True

            # Reason codes
            reason_codes.append("CONSTRAINTS_SATISFIED")
            if best["score"] >= 0.75:
                reason_codes.append("HIGH_PERSONA_AFFINITY")
            if max_budget and best["product"].get("price", 0) <= max_budget:
                reason_codes.append("PRICE_FIT")

            explanation = (
                f"SIMULATED: Product '{best['product_name']}' selected by {persona_name} "
                f"with score {best['score']:.3f} (ranked #1 of {len(catalogue)} evaluated items)."
            )
        else:
            dominant_friction = "constraint friction"
            if all_evaluated_rankings:
                from collections import Counter
                all_frictions = []
                for r in all_evaluated_rankings:
                    all_frictions.extend(r.get("frictions", []))
                if all_frictions:
                    dominant_friction = Counter(all_frictions).most_common(1)[0][0]

            explanation = (
                f"SIMULATED: {persona_name} rejected all {len(catalogue)} products. "
                f"Dominant reason: {dominant_friction}."
            )
            reason_codes.append("NO_MATCHING_PRODUCTS")

        return {
            "simulation_id": str(uuid.uuid4()),
            "persona_name": persona_name,
            "selected_product_id": selected_product_id,
            "score": selected_score,
            "score_breakdown": selected_score_breakdown,
            "selected_product_name": selected_product_name,
            "selected_product_price": selected_product_price,
            "selected_product_category": selected_product_category,
            "constraints_satisfied": constraints_satisfied,
            "reason_codes": reason_codes,
            "frictions": observed_frictions,
            "rankings": rankings,
            "explanation": explanation,
        }


simulation_engine = SimulationEngine()

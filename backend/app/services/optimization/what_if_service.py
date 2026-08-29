import copy
from typing import Dict, Any, List, Optional
from app.simulation.engine import simulation_engine


class WhatIfService:
    """
    Simulates merchant "What-If" catalogue modifications in memory.
    Evaluates baseline catalogue versus proposed changes across multiple buyer personas
    without modifying database or financial records.
    """

    def compare(
        self,
        merchant_id: str,
        persona_weights: Dict[str, float],
        intent: Dict[str, Any],
        original_catalogue: List[Dict[str, Any]],
        modified_catalogue: List[Dict[str, Any]],
        persona_name: str = "SYNTHETIC_BUYER"
    ) -> Dict[str, Any]:
        """
        Direct comparison between original catalogue and modified catalogue for a specific intent/persona.
        """
        baseline_result = simulation_engine.run_simulation(
            merchant_id=merchant_id,
            persona_weights=persona_weights,
            intent=intent,
            catalogue=original_catalogue,
            persona_name=persona_name,
        )

        proposed_result = simulation_engine.run_simulation(
            merchant_id=merchant_id,
            persona_weights=persona_weights,
            intent=intent,
            catalogue=modified_catalogue,
            persona_name=persona_name,
        )

        baseline_selected = baseline_result.get("selected_product_id")
        proposed_selected = proposed_result.get("selected_product_id")

        delta_summary = {
            "baseline_selected": baseline_selected,
            "proposed_selected": proposed_selected,
            "outcome_changed": baseline_selected != proposed_selected,
            "score_delta": round(proposed_result.get("score", 0.0) - baseline_result.get("score", 0.0), 3),
            "note": "SIMULATED RESULT",
        }

        return {
            "baseline": baseline_result,
            "proposed": proposed_result,
            "delta": delta_summary,
        }

    def run_what_if(
        self,
        merchant_id: str,
        hypothesis: str,
        baseline_catalogue: List[Dict[str, Any]],
        modifications: Dict[str, Any],
        scenarios: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Executes comparative in-memory simulations for baseline vs modified catalogue state.
        """
        modified_catalogue = copy.deepcopy(baseline_catalogue)

        target_product_id = str(modifications.get("product_id", ""))
        price_override = modifications.get("price")
        delivery_days_override = modifications.get("delivery_days")
        return_days_override = modifications.get("return_days")
        metadata_overrides = modifications.get("metadata", {})

        # Apply in-memory modifications
        for p in modified_catalogue:
            if not target_product_id or str(p.get("id")) == target_product_id:
                if price_override is not None:
                    p["price"] = int(price_override)
                p_meta = p.get("product_metadata") or p.get("metadata") or {}
                if delivery_days_override is not None:
                    p_meta["delivery_days"] = delivery_days_override
                if return_days_override is not None:
                    p_meta["return_days"] = return_days_override
                for k, v in metadata_overrides.items():
                    p_meta[k] = v
                p["product_metadata"] = p_meta

        if not scenarios:
            scenarios = [
                {"name": "Budget Buyer", "weights": {"price": 0.50, "offers": 0.25, "delivery": 0.10, "quality": 0.10, "returns": 0.05}, "intent": {"max_budget": 500000}},
                {"name": "Speed Buyer", "weights": {"delivery": 0.55, "metadata": 0.20, "quality": 0.15, "price": 0.10}, "intent": {"delivery_deadline_days": 2}},
                {"name": "Quality Buyer", "weights": {"quality": 0.50, "metadata": 0.20, "returns": 0.15, "delivery": 0.10, "price": 0.05}, "intent": {}},
                {"name": "Feature Buyer", "weights": {"metadata": 0.50, "quality": 0.25, "price": 0.15, "delivery": 0.10}, "intent": {}},
                {"name": "Balanced Buyer", "weights": {"price": 0.25, "quality": 0.25, "delivery": 0.20, "returns": 0.15, "offers": 0.10, "metadata": 0.05}, "intent": {}},
            ]

        baseline_scores = []
        proposed_scores = []
        baseline_matches = 0
        proposed_matches = 0

        for sc in scenarios:
            b_res = simulation_engine.run_simulation(
                merchant_id=merchant_id,
                persona_weights=sc["weights"],
                intent=sc["intent"],
                catalogue=baseline_catalogue,
                persona_name=sc["name"],
            )
            p_res = simulation_engine.run_simulation(
                merchant_id=merchant_id,
                persona_weights=sc["weights"],
                intent=sc["intent"],
                catalogue=modified_catalogue,
                persona_name=sc["name"],
            )

            if b_res["constraints_satisfied"]:
                baseline_matches += 1
                baseline_scores.append(b_res["score"])
            else:
                baseline_scores.append(0.0)

            if p_res["constraints_satisfied"]:
                proposed_matches += 1
                proposed_scores.append(p_res["score"])
            else:
                proposed_scores.append(0.0)

        total_scenarios = len(scenarios)
        b_rate = round(baseline_matches / max(total_scenarios, 1), 3)
        p_rate = round(proposed_matches / max(total_scenarios, 1), 3)

        b_avg_score = round(sum(baseline_scores) / max(total_scenarios, 1), 3)
        p_avg_score = round(sum(proposed_scores) / max(total_scenarios, 1), 3)

        if b_avg_score > 0:
            delta_pct = round(((p_avg_score - b_avg_score) / b_avg_score) * 100.0, 1)
        elif p_avg_score > 0:
            delta_pct = 100.0
        else:
            delta_pct = 0.0

        return {
            "hypothesis": hypothesis,
            "modifications": modifications,
            "baseline_metrics": {
                "simulated_selection_rate": b_rate,
                "average_score": b_avg_score,
                "matches": baseline_matches,
                "total_scenarios": total_scenarios,
                "metric_type": "SIMULATED RESULT",
            },
            "simulated_metrics": {
                "simulated_selection_rate": p_rate,
                "average_score": p_avg_score,
                "matches": proposed_matches,
                "total_scenarios": total_scenarios,
                "metric_type": "SIMULATED RESULT",
            },
            "delta_percentage": delta_pct,
            "note": "SIMULATED RESULT: Evaluated in-memory. No production data modified.",
        }


what_if_service = WhatIfService()

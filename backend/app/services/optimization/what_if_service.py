from typing import Dict, Any, List
from app.simulation.engine import simulation_engine

class WhatIfService:
    def compare(
        self, 
        merchant_id: str, 
        persona_weights: Dict[str, float], 
        intent: Dict[str, Any], 
        original_catalogue: List[Dict[str, Any]], 
        modified_catalogue: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        
        # Run baseline
        baseline_result = simulation_engine.run_simulation(
            merchant_id=merchant_id,
            persona_weights=persona_weights,
            intent=intent,
            catalogue=original_catalogue
        )
        
        # Run proposed
        proposed_result = simulation_engine.run_simulation(
            merchant_id=merchant_id,
            persona_weights=persona_weights,
            intent=intent,
            catalogue=modified_catalogue
        )
        
        # Calculate Delta
        baseline_selected = baseline_result.selected_product
        proposed_selected = proposed_result.selected_product
        
        delta_summary = {
            "baseline_selected": baseline_selected,
            "proposed_selected": proposed_selected,
            "outcome_changed": baseline_selected != proposed_selected,
            "note": "SIMULATED RESULT"
        }
        
        return {
            "baseline": baseline_result.model_dump(),
            "proposed": proposed_result.model_dump(),
            "delta": delta_summary
        }

what_if_service = WhatIfService()

from typing import List, Dict, Any
import uuid
from .scoring import ProductScorer
from .friction import FrictionDetector
from app.schemas.optimization.simulations import SimulationResponse, SimulationRanking

class SimulationEngine:
    def run_simulation(
        self, 
        merchant_id: str, 
        persona_weights: Dict[str, float], 
        intent: Dict[str, Any], 
        catalogue: List[Dict[str, Any]]
    ) -> SimulationResponse:
        
        candidates = []
        rankings = []
        
        for product in catalogue:
            hard_friction = FrictionDetector.detect_hard_constraints(product, intent)
            if hard_friction:
                rankings.append(SimulationRanking(
                    product_id=str(product.get("id")),
                    score=0.0,
                    rank=999,
                    friction_reasons=[f.value for f in hard_friction]
                ))
                continue
                
            soft_friction = FrictionDetector.detect_soft_friction(product, persona_weights)
            score = ProductScorer.calculate_score(product, persona_weights)
            
            candidates.append({
                "product": product,
                "score": score,
                "friction": [f.value for f in soft_friction]
            })
            
        # Sort candidates descending by score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # Populate rankings for candidates
        for i, c in enumerate(candidates):
            rankings.append(SimulationRanking(
                product_id=str(c["product"].get("id")),
                score=c["score"],
                rank=i+1,
                friction_reasons=c["friction"]
            ))
            
        selected_product = None
        explanation = None
        
        if candidates:
            best = candidates[0]
            selected_product = str(best["product"].get("id"))
            
            # This is where LLM could generate a real explanation based on the facts
            explanation = f"Selected because it scored {best['score']}."
            
        return SimulationResponse(
            simulation_id=str(uuid.uuid4()),
            selected_product=selected_product,
            rankings=rankings,
            explanation=explanation,
            constraints_satisfied=bool(candidates)
        )

simulation_engine = SimulationEngine()

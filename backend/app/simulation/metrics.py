from typing import List, Dict, Any

class SimulationMetrics:
    @staticmethod
    def calculate_selection_metrics(scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate metrics such as selection_rate, rejection_rate, friction_distribution.
        """
        total = len(scenarios)
        if total == 0:
            return {
                "total_scenarios": 0,
                "selection_rate": 0.0,
                "rejection_rate": 0.0,
                "friction_distribution": {}
            }
            
        selected_count = sum(1 for s in scenarios if s.get("selected_product"))
        
        # friction distribution
        friction_dist = {}
        for s in scenarios:
            for f in s.get("frictions", []):
                friction_dist[f] = friction_dist.get(f, 0) + 1
                
        return {
            "total_scenarios": total,
            "selection_rate": selected_count / total,
            "rejection_rate": (total - selected_count) / total,
            "friction_distribution": friction_dist
        }

simulation_metrics = SimulationMetrics()

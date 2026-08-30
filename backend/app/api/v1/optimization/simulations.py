import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.optimization.simulation import (
    SimulationCreate,
    SimulationResponse,
    SimulationResultItem,
)
from app.services.product_service import ProductService
from app.simulation.engine import simulation_engine
from app.api.v1.buyer.personas import DEFAULT_PERSONAS, _custom_personas
from app.security.authentication import get_current_merchant
from app.models.merchant import Merchant

router = APIRouter(prefix="/optimization", tags=["Optimization & Simulation"])

PERSONA_PROFILE_MAP = {
    "BUDGET": {"price": 0.50, "offers": 0.25, "delivery": 0.10, "quality": 0.10, "returns": 0.05},
    "SPEED": {"delivery": 0.55, "metadata": 0.20, "quality": 0.15, "price": 0.10},
    "QUALITY": {"quality": 0.50, "metadata": 0.20, "returns": 0.15, "delivery": 0.10, "price": 0.05},
    "FEATURE": {"metadata": 0.50, "quality": 0.25, "price": 0.15, "delivery": 0.10},
    "BALANCED": {"price": 0.25, "quality": 0.25, "delivery": 0.20, "returns": 0.15, "offers": 0.10, "metadata": 0.05},
}


def _resolve_persona_weights(profile_name: str) -> Dict[str, float]:
    upper_name = profile_name.upper()
    if upper_name in PERSONA_PROFILE_MAP:
        return PERSONA_PROFILE_MAP[upper_name]

    # Search in default personas
    for p in DEFAULT_PERSONAS + _custom_personas:
        if profile_name.lower() in p["name"].lower():
            return p["weights"]

    return PERSONA_PROFILE_MAP["BALANCED"]


@router.post("/simulations", response_model=SimulationResponse, status_code=status.HTTP_200_OK)
def run_simulation(
    req: SimulationCreate,
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant)
):
    """
    Executes synchronous, deterministic buyer simulations against the merchant's catalogue.
    Evaluates real buyer personas, applies hard/soft constraints, and detects friction.
    """
    merchant_id = current_merchant.id
    product_service = ProductService(db)
    db_products, _ = product_service.list_products(merchant_id=merchant_id, limit=100)

    # Convert DB products to dictionary catalogue format
    catalogue: List[Dict[str, Any]] = []
    for p in db_products:
        inv_qty = p.inventory.available_quantity if hasattr(p, "inventory") and p.inventory else 10
        catalogue.append({
            "id": p.id,
            "name": p.name,
            "description": p.description or "",
            "category": p.category,
            "price": p.price,
            "currency": p.currency,
            "is_active": p.is_active,
            "product_metadata": p.product_metadata or {},
            "available_quantity": inv_qty,
        })

    profiles = req.buyer_profiles if req.buyer_profiles else ["BUDGET", "SPEED", "QUALITY", "BALANCED"]
    sim_id = uuid.uuid4()
    results: List[SimulationResultItem] = []
    friction_summary: Dict[str, int] = {}
    detailed_frictions: List[Dict[str, Any]] = []
    persona_success_count: Dict[str, int] = {}

    # Run simulation iterations
    for index in range(req.scenario_count):
        profile_name = profiles[index % len(profiles)]
        weights = _resolve_persona_weights(profile_name)

        if req.intent:
            intent_dict = req.intent.model_dump()
        else:
            # Construct standard scenario intent based on persona tendencies
            if "BUDGET" in profile_name.upper():
                intent_dict = {"max_budget": 500000, "requirements": []}
            elif "SPEED" in profile_name.upper():
                intent_dict = {"max_budget": 1000000, "delivery_deadline_days": 2, "requirements": ["fast_delivery"]}
            elif "QUALITY" in profile_name.upper():
                intent_dict = {"max_budget": 2000000, "requirements": ["warranty"]}
            else:
                intent_dict = {"max_budget": 1000000, "requirements": []}

        sim_output = simulation_engine.run_simulation(
            merchant_id=str(req.merchant_id or merchant_id),
            persona_weights=weights,
            intent=intent_dict,
            catalogue=catalogue,
            persona_name=profile_name,
        )

        selected_id = uuid.UUID(sim_output["selected_product_id"]) if sim_output["selected_product_id"] else None

        # Track friction summary
        for f in sim_output.get("frictions", []):
            reason_name = f.get("reason", "UNKNOWN")
            friction_summary[reason_name] = friction_summary.get(reason_name, 0) + 1
            detailed_frictions.append({
                "product_id": f.get("product_id"),
                "reason": reason_name,
                "count": 1
            })

        # Track persona success
        if sim_output["constraints_satisfied"]:
            persona_success_count[profile_name] = persona_success_count.get(profile_name, 0) + 1

        results.append(
            SimulationResultItem(
                persona_name=profile_name,
                selected_product_id=selected_id,
                score=sim_output["score"],
                constraints_satisfied=sim_output["constraints_satisfied"],
                reason_codes=sim_output["reason_codes"],
                frictions=sim_output["frictions"],
                rankings=sim_output["rankings"],
                explanation=sim_output["explanation"],
            )
        )

    # Compute comprehensive summary metrics
    total_simulated = len(results)
    successful_matches = sum(1 for r in results if r.constraints_satisfied and r.selected_product_id is not None)
    failed_matches = total_simulated - successful_matches
    satisfaction_rate = round(successful_matches / max(total_simulated, 1), 3)
    avg_score = round(sum(r.score for r in results) / max(total_simulated, 1), 3)

    # Persist the collected friction evidence as actionable recommendations
    if detailed_frictions:
        from app.services.optimization.recommendation_service import recommendation_service
        recommendation_service.generate_recommendations(db, merchant_id, detailed_frictions)

    return SimulationResponse(
        simulation_id=sim_id,
        merchant_id=merchant_id,
        status="COMPLETED",
        scenario_count=total_simulated,
        buyer_profiles=profiles,
        summary_metrics={
            "buyers_simulated": total_simulated,
            "successful_matches": successful_matches,
            "failed_matches": failed_matches,
            "constraint_satisfaction_rate": satisfaction_rate,
            "average_score": avg_score,
            "friction_distribution": friction_summary,
            "persona_success_rates": {
                p: round(persona_success_count.get(p, 0) / max(sum(1 for r in results if r.persona_name == p), 1), 2)
                for p in set(profiles)
            },
            "metric_type": "SIMULATED RESULT",
        },
        results=results,
        created_at=datetime.now(timezone.utc),
    )

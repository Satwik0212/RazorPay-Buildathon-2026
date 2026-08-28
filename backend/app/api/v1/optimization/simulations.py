import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.optimization.simulation import SimulationCreate, SimulationResponse, SimulationResultItem
from app.services.product_service import ProductService

router = APIRouter(prefix="/optimization", tags=["Optimization & Simulation"])


@router.post("/simulations", response_model=SimulationResponse, status_code=status.HTTP_200_OK)
def run_simulation(req: SimulationCreate, db: Session = Depends(get_db)):
    """
    Synchronous in-process simulation interface boundary.
    Sanji (AI agent) provides the detailed scoring engine.
    """
    product_service = ProductService(db)
    products, total = product_service.list_products(merchant_id=req.merchant_id, limit=req.scenario_count)

    sim_id = uuid.uuid4()
    results = []

    for index, p in enumerate(products):
        profile = req.buyer_profiles[index % len(req.buyer_profiles)] if req.buyer_profiles else "BUDGET"
        results.append(
            SimulationResultItem(
                persona_name=profile,
                selected_product_id=p.id,
                score=0.85,
                constraints_satisfied=True,
                reason_codes=["PRICE_MATCH", "IN_STOCK"],
                frictions=[],
                rankings=[{"product_id": str(p.id), "score": 0.85, "rank": 1}],
                explanation=f"SIMULATED: Product '{p.name}' matched {profile} buyer criteria.",
            )
        )

    return SimulationResponse(
        simulation_id=sim_id,
        merchant_id=req.merchant_id,
        status="COMPLETED",
        scenario_count=len(results),
        buyer_profiles=req.buyer_profiles,
        summary_metrics={
            "buyers_simulated": len(results),
            "successful_matches": len(results),
            "failed_matches": 0,
            "constraint_satisfaction_rate": 1.0 if results else 0.0,
        },
        results=results,
        created_at=datetime.now(timezone.utc),
    )

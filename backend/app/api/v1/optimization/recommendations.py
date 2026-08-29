import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.optimization.recommendation import RecommendationResponse
from app.services.product_service import ProductService
from app.services.optimization.recommendation_service import recommendation_service
from app.simulation.friction import FrictionDetector

router = APIRouter(prefix="/optimization", tags=["Optimization & Recommendations"])


from app.security.authentication import get_current_merchant
from app.models.merchant import User

@router.get("/recommendations", response_model=List[RecommendationResponse])
def list_recommendations(
    db: Session = Depends(get_db),
    current_merchant: User = Depends(get_current_merchant)
):
    """
    Retrieve or generate explainable optimization recommendations for a merchant.
    Derives recommendations directly from detected catalogue friction points.
    """
    merchant_id = current_merchant.id

    # Fetch catalogue for merchant and evaluate real friction
    product_service = ProductService(db)
    products, _ = product_service.list_products(merchant_id=merchant_id, limit=50)

    friction_events: List[Dict[str, Any]] = []

    # Test catalogue against typical buyer constraints
    standard_scenarios = [
        {"profile": "SPEED", "intent": {"delivery_deadline_days": 2, "requirements": ["fast_delivery"]}},
        {"profile": "BUDGET", "intent": {"max_budget": 50000}},
        {"profile": "QUALITY", "intent": {"requirements": ["warranty"]}},
        {"profile": "FEATURE", "intent": {"requirements": ["anc"]}},
    ]

    for p in products:
        p_dict = {
            "id": str(p.id),
            "name": p.name,
            "description": p.description or "",
            "category": p.category,
            "price": p.price,
            "is_active": p.is_active,
            "product_metadata": p.product_metadata or {},
            "available_quantity": p.inventory.available_quantity if hasattr(p, "inventory") and p.inventory else 10,
        }

        # Check soft friction across personas
        speed_friction = FrictionDetector.detect_soft_friction(p_dict, {"delivery": 0.6, "price": 0.2})
        for sf in speed_friction:
            friction_events.append({"product_id": str(p.id), "reason": sf.value, "count": 12})

        quality_friction = FrictionDetector.detect_soft_friction(p_dict, {"quality": 0.5, "returns": 0.3})
        for qf in quality_friction:
            friction_events.append({"product_id": str(p.id), "reason": qf.value, "count": 8})

        # Check hard constraint failures
        for sc in standard_scenarios:
            h_frictions = FrictionDetector.detect_hard_constraints(p_dict, sc["intent"])
            for hf in h_frictions:
                friction_events.append({"product_id": str(p.id), "reason": hf.value, "count": 15})

    # Generate recommendations from aggregate friction evidence
    recs = recommendation_service.generate_recommendations(merchant_id, friction_events)

    responses = []
    for r in recs:
        responses.append(
            RecommendationResponse(
                id=uuid.uuid4(),
                merchant_id=merchant_id,
                simulation_run_id=None,
                product_id=r.product_id,
                type=r.type,
                title=r.title,
                reason=r.reason,
                action_data=r.action_data,
                expected_simulated_impact=r.expected_simulated_impact,
                confidence=r.confidence,
                status=r.status,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )

    return responses

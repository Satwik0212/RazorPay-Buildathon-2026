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

from app.core.exceptions import NotFoundError
from app.schemas.optimization.recommendation import RecommendationResponse, RecommendationStatusUpdate
from app.security.authentication import get_current_merchant
from app.models.merchant import User
from app.models.optimization_recommendation import OptimizationRecommendation

@router.get("/recommendations", response_model=List[RecommendationResponse])
def list_recommendations(
    db: Session = Depends(get_db),
    current_merchant: User = Depends(get_current_merchant)
):
    """
    Retrieve explainable optimization recommendations for a merchant.
    Returns real, persisted recommendations generated from actual buyer simulation runs.
    Filters to only show recommendations associated with the merchant's most recent simulation run.
    """
    merchant_id = current_merchant.id

    # Find the latest simulation run for this merchant
    from app.models.simulation_run import SimulationRun
    latest_run = db.query(SimulationRun)\
        .filter(SimulationRun.merchant_id == merchant_id, SimulationRun.status == "COMPLETED")\
        .order_by(SimulationRun.created_at.desc())\
        .first()

    if not latest_run:
        return []

    from sqlalchemy import or_
    
    # Fetch real persisted recommendations tied to the latest run, 
    # plus any historical recommendations the merchant has already acted upon (APPLIED/REJECTED).
    recs = db.query(OptimizationRecommendation)\
        .filter(OptimizationRecommendation.merchant_id == merchant_id)\
        .filter(
            or_(
                OptimizationRecommendation.simulation_run_id == latest_run.id,
                OptimizationRecommendation.status != "PROPOSED"
            )
        )\
        .order_by(OptimizationRecommendation.expected_simulated_impact.desc(), OptimizationRecommendation.confidence.desc())\
        .limit(50).all()

    return recs

@router.patch("/recommendations/{recommendation_id}/status", response_model=RecommendationResponse)
def update_recommendation_status(
    recommendation_id: uuid.UUID,
    req: RecommendationStatusUpdate,
    db: Session = Depends(get_db),
    current_merchant: User = Depends(get_current_merchant)
):
    """
    Update the status of a recommendation (e.g. APPLIED, REJECTED).
    Restricted to the owning merchant.
    """
    merchant_id = current_merchant.id

    rec = db.query(OptimizationRecommendation).filter(
        OptimizationRecommendation.id == recommendation_id,
        OptimizationRecommendation.merchant_id == merchant_id
    ).first()

    if not rec:
        raise NotFoundError("Recommendation", recommendation_id)

    if rec.status == req.status:
        return rec

    rec.status = req.status
    
    if req.status == "APPLIED" and rec.action_data:
        from app.models.product import Product
        from app.models.audit_event import AuditEvent
        from sqlalchemy.orm.attributes import flag_modified
        
        affected_ids_str = rec.action_data.get("affected_product_ids", [])
        if not affected_ids_str and rec.product_id:
            affected_ids_str = [str(rec.product_id)]
            
        affected_ids = []
        for id_str in affected_ids_str:
            try:
                affected_ids.append(uuid.UUID(id_str) if isinstance(id_str, str) else id_str)
            except ValueError:
                pass
                
        if affected_ids:
            products = db.query(Product).filter(
                Product.id.in_(affected_ids),
                Product.merchant_id == merchant_id
            ).all()
            
            for product in products:
                before_state = {}
                after_state = {}
                action_performed = "APPLY_RECOMMENDATION"
                changed = False

                if "new_price" in rec.action_data:
                    before_state["price"] = product.price
                    if product.price != rec.action_data["new_price"]:
                        product.price = rec.action_data["new_price"]
                        changed = True
                    after_state["price"] = product.price
                elif rec.action_data.get("new_price_mode") == "percent_discount":
                    # Dynamically calculate the new price based on the discount percentage
                    pct = rec.action_data.get("new_price_discount_pct", 10)
                    new_price = int(product.price * (1 - (pct / 100.0)))
                    before_state["price"] = product.price
                    if product.price != new_price:
                        product.price = new_price
                        changed = True
                    after_state["price"] = product.price
                
                # Support both explicitly populated action_data (new recommendations) 
                # and fallback to recommendation type inference (for older recommendations in DB)
                has_delivery_action = "new_delivery_days" in rec.action_data
                is_delivery_rec = rec.type in ["DELIVERY_UNKNOWN", "DELIVERY_TOO_SLOW", "DELIVERY_CLARITY"]
                
                if has_delivery_action or is_delivery_rec or "new_return_days" in rec.action_data:
                    meta = dict(product.product_metadata or {})
                    if has_delivery_action or is_delivery_rec:
                        before_state["delivery_days"] = meta.get("delivery_days")
                        new_val = rec.action_data.get("new_delivery_days", 2) # fallback to 2
                        if meta.get("delivery_days") != new_val:
                            meta["delivery_days"] = new_val
                            changed = True
                        after_state["delivery_days"] = new_val
                        action_performed = "UPDATE_DELIVERY_DAYS"
                    if "new_return_days" in rec.action_data:
                        before_state["return_days"] = meta.get("return_days")
                        new_val = rec.action_data["new_return_days"]
                        if meta.get("return_days") != new_val:
                            meta["return_days"] = new_val
                            changed = True
                        after_state["return_days"] = new_val
                        
                    if changed:
                        product.product_metadata = meta
                        flag_modified(product, "product_metadata")
                    
                if "new_inventory_count" in rec.action_data:
                    before_state["inventory_count"] = product.inventory.available_quantity
                    new_val = rec.action_data["new_inventory_count"]
                    if product.inventory.available_quantity != new_val:
                        product.inventory.available_quantity = new_val
                        product.is_active = True
                        changed = True
                    after_state["inventory_count"] = product.inventory.available_quantity

                # Only record audit if something was actually changed (Idempotency)
                if changed:
                    audit = AuditEvent(
                        actor_type="MERCHANT",
                        actor_id=current_merchant.id,
                        merchant_id=current_merchant.id,
                        event_type="RECOMMENDATION_APPLIED",
                        entity_type="PRODUCT",
                        entity_id=product.id,
                        event_data={
                            "recommendation_id": str(rec.id),
                            "action_performed": action_performed,
                            "before_state": before_state,
                            "after_state": after_state,
                            "result": "SUCCESS"
                        }
                    )
                    db.add(audit)
    db.commit()
    db.refresh(rec)

    return rec

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
from app.models.optimization_recommendation import OptimizationRecommendation

@router.get("/recommendations", response_model=List[RecommendationResponse])
def list_recommendations(
    db: Session = Depends(get_db),
    current_merchant: User = Depends(get_current_merchant)
):
    """
    Retrieve explainable optimization recommendations for a merchant.
    Returns real, persisted recommendations generated from actual buyer simulation runs.
    """
    merchant_id = current_merchant.id

    # Fetch real persisted recommendations
    recs = db.query(OptimizationRecommendation)\
        .filter(OptimizationRecommendation.merchant_id == merchant_id)\
        .order_by(OptimizationRecommendation.confidence.desc())\
        .limit(50).all()

    return recs

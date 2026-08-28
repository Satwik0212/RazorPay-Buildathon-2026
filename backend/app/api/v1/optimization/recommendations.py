import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter
from app.schemas.optimization.recommendation import RecommendationResponse

router = APIRouter(prefix="/optimization", tags=["Optimization"])


@router.get("/recommendations", response_model=List[RecommendationResponse])
def list_recommendations(merchant_id: Optional[uuid.UUID] = None):
    return []

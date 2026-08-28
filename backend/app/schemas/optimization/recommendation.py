import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RecommendationResponse(BaseModel):
    id: uuid.UUID
    merchant_id: uuid.UUID
    simulation_run_id: Optional[uuid.UUID] = None
    product_id: Optional[uuid.UUID] = None
    type: str
    title: str
    reason: str
    action_data: Dict[str, Any] = {}
    expected_simulated_impact: float
    confidence: float
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

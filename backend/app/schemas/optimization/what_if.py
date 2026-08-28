import uuid
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class WhatIfRequest(BaseModel):
    merchant_id: uuid.UUID
    hypothesis: str = Field(min_length=3, max_length=500)
    modifications: Dict[str, Any] = Field(default_factory=dict)


class WhatIfResponse(BaseModel):
    id: uuid.UUID
    merchant_id: uuid.UUID
    hypothesis: str
    modifications: Dict[str, Any]
    baseline_metrics: Dict[str, Any]
    simulated_metrics: Dict[str, Any]
    delta_percentage: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

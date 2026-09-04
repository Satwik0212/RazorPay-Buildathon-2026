import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class WhatIfRequest(BaseModel):
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
    # Optional: present only when a specific product_id is in modifications.
    # Contains per-persona score/eligibility for the target product (not catalogue-wide).
    target_product_metrics: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

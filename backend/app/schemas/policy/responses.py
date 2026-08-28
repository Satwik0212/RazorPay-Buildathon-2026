import uuid
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PolicyResponse(BaseModel):
    id: uuid.UUID
    merchant_id: uuid.UUID
    max_autonomous_amount: int
    daily_autonomous_limit: int
    require_approval_above: int
    blocked_categories: List[str]
    is_ai_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PolicyCheckResponse(BaseModel):
    allowed: bool
    status: str  # APPROVED, REVIEW_REQUIRED, BLOCKED
    reason: str

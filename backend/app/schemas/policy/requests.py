import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class PolicyUpdate(BaseModel):
    max_autonomous_amount: int = Field(ge=0, description="Max amount allowed autonomously in minor units")
    daily_autonomous_limit: int = Field(ge=0, description="Daily spend cap in minor units")
    require_approval_above: int = Field(ge=0, description="Requires merchant approval if above this amount")
    blocked_categories: List[str] = Field(default_factory=list)
    is_ai_enabled: bool = True


class PolicyCheckRequest(BaseModel):
    merchant_id: uuid.UUID
    amount: int = Field(ge=0)
    category: Optional[str] = None

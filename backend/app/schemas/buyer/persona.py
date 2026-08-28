import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class BuyerPersonaCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=500)
    budget_min: int = Field(default=0, ge=0)
    budget_max: int = Field(default=1000000, ge=0)
    priorities: List[str] = Field(default_factory=list)
    urgency: str = Field(default="MEDIUM")
    weights: Dict[str, float] = Field(default_factory=dict)


class BuyerPersonaResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    budget_min: int
    budget_max: int
    priorities: List[str]
    urgency: str
    weights: Dict[str, float]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

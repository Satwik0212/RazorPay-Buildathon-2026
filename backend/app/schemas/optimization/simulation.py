import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.buyer.intent import StructuredIntent


class SimulationCreate(BaseModel):
    merchant_id: Optional[uuid.UUID] = None
    scenario_count: int = Field(default=10, ge=1, le=100)
    buyer_profiles: List[str] = Field(default_factory=lambda: ["BUDGET", "QUALITY", "SPEED"])
    intent: Optional[StructuredIntent] = None


class SimulationResultItem(BaseModel):
    persona_name: str
    selected_product_id: Optional[uuid.UUID] = None
    score: float
    constraints_satisfied: bool
    reason_codes: List[str] = []
    frictions: List[Dict[str, Any]] = []
    rankings: List[Dict[str, Any]] = []
    explanation: str = ""

    model_config = ConfigDict(from_attributes=True)


class SimulationResponse(BaseModel):
    simulation_id: uuid.UUID
    merchant_id: uuid.UUID
    status: str
    scenario_count: int
    buyer_profiles: List[str]
    summary_metrics: Dict[str, Any] = {}
    results: List[SimulationResultItem] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

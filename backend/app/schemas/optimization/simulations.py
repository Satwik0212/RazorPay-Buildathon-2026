from pydantic import BaseModel
from typing import List, Optional, Dict
from app.schemas.buyer.intent import BuyerIntent

class SimulationRanking(BaseModel):
    product_id: str
    score: float
    rank: int
    friction_reasons: Optional[List[str]] = None

class SimulationRequest(BaseModel):
    merchant_id: str
    persona_id: str
    intent: BuyerIntent

class SimulationResponse(BaseModel):
    simulation_id: str
    selected_product: Optional[str]
    rankings: List[SimulationRanking]
    explanation: Optional[str]
    constraints_satisfied: bool

class BatchSimulationRequest(BaseModel):
    merchant_id: str
    product_ids: List[str]
    persona_ids: List[str]
    scenario_count: int

class ProductSimulationResult(BaseModel):
    selected: int
    rejected: int
    selection_rate: float

class BatchSimulationResponse(BaseModel):
    run_id: str
    scenario_count: int
    results: Dict[str, ProductSimulationResult]

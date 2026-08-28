from pydantic import BaseModel
from typing import Dict, Any

class SyntheticBuyer(BaseModel):
    """
    Represents one synthetic buyer in a simulation scenario.
    """
    persona_id: str
    persona_weights: Dict[str, float]
    budget_minor: int
    intent: Dict[str, Any]

from pydantic import BaseModel
from typing import List, Dict, Any
from .buyer import SyntheticBuyer

class SimulationScenario(BaseModel):
    """
    Represents a full simulation configuration.
    """
    merchant_id: str
    catalogue: List[Dict[str, Any]]
    buyers: List[SyntheticBuyer]

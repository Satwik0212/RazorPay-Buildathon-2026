import uuid
from typing import List, Optional
from pydantic import BaseModel


class UpsellSuggestion(BaseModel):
    product_id: uuid.UUID
    name: str
    price: int
    category: str
    score: float
    explanation: Optional[str] = None


class UpsellResponse(BaseModel):
    upsell: List[UpsellSuggestion]
    cross_sell: List[UpsellSuggestion]
    anchor_product_ids: List[uuid.UUID]
    data_source: str = "DETERMINISTIC_CATALOGUE_SCORING"

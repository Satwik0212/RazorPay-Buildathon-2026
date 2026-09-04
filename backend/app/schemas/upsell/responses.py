import uuid
from typing import List, Optional, Literal
from pydantic import BaseModel


class UpsellSuggestion(BaseModel):
    product_id: uuid.UUID
    name: str
    price: int
    category: str
    score: float
    explanation: Optional[str] = None
    recommendation_type: Literal["UPSELL", "CROSS_SELL"] = "UPSELL"
    ai_confidence: Optional[float] = None


class UpsellResponse(BaseModel):
    upsell: List[UpsellSuggestion]
    cross_sell: List[UpsellSuggestion]
    anchor_product_ids: List[uuid.UUID]
    data_source: str = "DETERMINISTIC_CATALOGUE_SCORING"
    ai_powered: bool = False

import uuid
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class QuoteResponse(BaseModel):
    quote_id: uuid.UUID
    cart_id: uuid.UUID
    subtotal: int
    discount: int
    shipping: int
    tax: int
    total: int
    currency: str
    quote_hash: str
    expires_at: datetime
    created_at: datetime
    line_items_snapshot: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)


class QuoteValidationResponse(BaseModel):
    valid: bool
    expired: bool
    amount: int
    currency: str

import uuid
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.product.responses import ProductResponse


class CartItemResponse(BaseModel):
    id: uuid.UUID
    cart_id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    product: Optional[ProductResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    merchant_id: uuid.UUID
    status: str
    items: List[CartItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartValidationResponse(BaseModel):
    valid: bool
    issues: List[str] = []

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class InventoryResponse(BaseModel):
    product_id: uuid.UUID
    available_quantity: int
    reserved_quantity: int

    model_config = ConfigDict(from_attributes=True)


class ProductResponse(BaseModel):
    id: uuid.UUID
    merchant_id: uuid.UUID
    name: str
    description: str
    category: str
    price: int
    currency: str
    is_active: bool
    metadata: Dict[str, Any] = Field(default_factory=dict, validation_alias="product_metadata")
    inventory: Optional[InventoryResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ProductBulkResponse(BaseModel):
    created: int
    failed: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    items: List[ProductResponse] = Field(default_factory=list)

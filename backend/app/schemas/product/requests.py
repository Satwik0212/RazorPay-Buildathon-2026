from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    category: str = Field(min_length=1, max_length=100)
    price: int = Field(ge=0, description="Price in minor units (e.g. paise)")
    currency: str = Field(default="INR", min_length=3, max_length=3)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    initial_quantity: int = Field(default=10, ge=0)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    price: Optional[int] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ProductBulkCreate(BaseModel):
    products: List[ProductCreate]


class InventoryUpdate(BaseModel):
    available_quantity: int = Field(ge=0)

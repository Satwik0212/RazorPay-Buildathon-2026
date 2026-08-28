import uuid
from typing import Optional
from pydantic import BaseModel, Field


class CartCreate(BaseModel):
    merchant_id: uuid.UUID


class CartItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(default=1, gt=0, le=100)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0, le=100)

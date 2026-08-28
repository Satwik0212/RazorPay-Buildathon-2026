from typing import Optional
from pydantic import BaseModel, Field


class MerchantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)


class MerchantUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)
    is_active: Optional[bool] = None

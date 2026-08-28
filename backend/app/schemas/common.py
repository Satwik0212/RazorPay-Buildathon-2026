import uuid
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class Money(BaseModel):
    amount: int = Field(ge=0, description="Amount in minor units (e.g., paise)")
    currency: str = Field(default="INR", min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class PaginationParams(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail

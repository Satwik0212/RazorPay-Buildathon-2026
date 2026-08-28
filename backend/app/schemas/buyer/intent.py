import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator


class BuyerIntentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class StructuredIntent(BaseModel):
    category: Optional[str] = Field(default=None, max_length=100)
    min_budget: Optional[int] = Field(default=None, ge=0)
    max_budget: Optional[int] = Field(default=None, ge=0)
    requirements: List[str] = Field(default_factory=list, max_length=20)
    delivery_deadline_days: Optional[int] = Field(default=None, ge=0, le=365)
    preferences: List[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_budget(self):
        if (
            self.min_budget is not None
            and self.max_budget is not None
            and self.min_budget > self.max_budget
        ):
            raise ValueError("min_budget cannot exceed max_budget")
        return self


# Canonical alias for compatibility
BuyerIntent = StructuredIntent


class BuyerIntentResponse(BaseModel):
    intent_id: uuid.UUID
    intent: StructuredIntent


class CatalogueSearchRequest(BaseModel):
    category: Optional[str] = None
    max_budget: Optional[int] = None
    requirements: List[str] = Field(default_factory=list)
    preferences: List[str] = Field(default_factory=list)


class SearchResultItem(BaseModel):
    product_id: uuid.UUID
    name: str
    price: int
    category: str
    match_score: float
    matched_constraints: List[str] = Field(default_factory=list)
    failed_constraints: List[str] = Field(default_factory=list)


class CatalogueSearchResponse(BaseModel):
    results: List[SearchResultItem] = Field(default_factory=list)

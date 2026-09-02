from typing import Optional
from pydantic import BaseModel, Field


class UpsellSuggestionRequest(BaseModel):
    context: Optional[str] = Field(default=None, max_length=1000)
    limit: int = Field(default=5, ge=1, le=20)

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class RazorpayWebhookPayload(BaseModel):
    event: str
    account_id: Optional[str] = None
    contains: list[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[int] = None

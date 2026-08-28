import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WebhookEventResponse(BaseModel):
    id: uuid.UUID
    event_id: str
    event_type: str
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    signature_verified: bool
    processed: bool
    processing_error: Optional[str] = None
    received_at: datetime
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WebhookProcessResult(BaseModel):
    status: str
    message: str
    event_id: str
    duplicate: bool = False

import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PaymentResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    razorpay_payment_id: str
    status: str
    method: Optional[str] = None
    amount: int
    currency: str
    error_code: Optional[str] = None
    error_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentStatusResponse(BaseModel):
    order_id: uuid.UUID
    status: str
    payment_id: Optional[uuid.UUID] = None
    razorpay_payment_id: Optional[str] = None
    amount: int
    currency: str

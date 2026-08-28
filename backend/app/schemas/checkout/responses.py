import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CheckoutOrderResponse(BaseModel):
    order_id: uuid.UUID
    merchant_id: uuid.UUID
    customer_id: uuid.UUID
    cart_id: uuid.UUID
    authorization_id: uuid.UUID
    razorpay_order_id: str
    amount: int
    currency: str
    status: str
    receipt: str
    razorpay_key_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

import uuid
from typing import Optional
from pydantic import BaseModel


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

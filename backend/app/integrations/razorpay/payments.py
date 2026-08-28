from typing import Dict, Any, Optional
from app.integrations.razorpay.client import RazorpayClient


class RazorpayPaymentsAdapter:
    def __init__(self, client: Optional[RazorpayClient] = None):
        self.client = client or RazorpayClient()

    def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        return self.client.fetch_payment(payment_id=payment_id)

from typing import Dict, Any, Optional
from app.integrations.razorpay.client import RazorpayClient


class RazorpayOrdersAdapter:
    def __init__(self, client: Optional[RazorpayClient] = None):
        self.client = client or RazorpayClient()

    def create_order(self, amount: int, currency: str, receipt: str, notes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.client.create_order(amount=amount, currency=currency, receipt=receipt, notes=notes)

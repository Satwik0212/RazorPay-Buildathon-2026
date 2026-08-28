from typing import Dict, Any, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.integrations.razorpay.exceptions import (
    RazorpayIntegrationError,
    RazorpayOrderCreationError,
    RazorpayPaymentFetchError,
)


class RazorpayClient:
    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(
        self,
        key_id: str = settings.RAZORPAY_KEY_ID,
        key_secret: str = settings.RAZORPAY_KEY_SECRET,
        is_mock: bool = False,
    ):
        self.key_id = key_id
        self.key_secret = key_secret
        self.is_mock = is_mock or key_id.startswith("rzp_test_buildathon") or not key_secret

    def create_order(self, amount: int, currency: str, receipt: str, notes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Creates an external order with Razorpay.
        Amount must be in minor currency units (paise).
        """
        if self.is_mock:
            # Deterministic test double for local demo and testing
            mock_order_id = f"order_mock_{receipt[:16]}"
            logger.info(f"[MOCK RAZORPAY] Order created: {mock_order_id} for amount={amount} {currency}")
            return {
                "id": mock_order_id,
                "entity": "order",
                "amount": amount,
                "amount_paid": 0,
                "amount_due": amount,
                "currency": currency,
                "receipt": receipt,
                "status": "created",
                "attempts": 0,
                "notes": notes or {},
            }

        payload = {
            "amount": amount,
            "currency": currency,
            "receipt": receipt,
            "notes": notes or {},
        }

        try:
            with httpx.Client(base_url=self.BASE_URL, auth=(self.key_id, self.key_secret), timeout=10.0) as client:
                response = client.post("/orders", json=payload)
                if response.status_code != 200:
                    logger.error(f"Razorpay order creation failed: {response.status_code} - {response.text}")
                    raise RazorpayOrderCreationError(
                        f"Razorpay returned status {response.status_code}",
                        details={"status_code": response.status_code, "error": response.text},
                    )
                return response.json()
        except httpx.RequestError as exc:
            logger.error(f"Network error calling Razorpay: {exc}")
            raise RazorpayOrderCreationError(f"Network error connecting to Razorpay: {str(exc)}") from exc

    def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Fetches payment state from Razorpay.
        """
        if self.is_mock:
            logger.info(f"[MOCK RAZORPAY] Fetch payment: {payment_id}")
            return {
                "id": payment_id,
                "entity": "payment",
                "amount": 49900,
                "currency": "INR",
                "status": "captured",
                "method": "upi",
                "captured": True,
            }

        try:
            with httpx.Client(base_url=self.BASE_URL, auth=(self.key_id, self.key_secret), timeout=10.0) as client:
                response = client.get(f"/payments/{payment_id}")
                if response.status_code != 200:
                    raise RazorpayPaymentFetchError(
                        f"Razorpay returned status {response.status_code}",
                        details={"status_code": response.status_code, "error": response.text},
                    )
                return response.json()
        except httpx.RequestError as exc:
            raise RazorpayPaymentFetchError(f"Network error connecting to Razorpay: {str(exc)}") from exc

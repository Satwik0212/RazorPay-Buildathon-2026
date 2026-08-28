import hmac
import hashlib
from app.core.config import settings
from app.core.exceptions import WebhookSignatureError
from app.core.logging import logger


def verify_razorpay_webhook_signature(
    raw_body: bytes,
    signature: str,
    secret: str = settings.RAZORPAY_WEBHOOK_SECRET,
) -> bool:
    """
    Verifies Razorpay webhook HMAC SHA-256 signature using constant-time comparison over raw bytes.
    """
    if not signature or not secret:
        logger.warning("Missing signature or webhook secret during verification.")
        return False

    try:
        expected_signature = hmac.new(
            key=secret.encode("utf-8"),
            msg=raw_body,
            digestmod=hashlib.sha256,
        ).hexdigest()

        is_valid = hmac.compare_digest(expected_signature, signature)
        if not is_valid:
            logger.warning("Razorpay webhook signature mismatch.")
        return is_valid
    except Exception as exc:
        logger.error(f"Error during webhook signature verification: {exc}")
        return False


def validate_webhook_signature_or_raise(
    raw_body: bytes,
    signature: str,
    secret: str = settings.RAZORPAY_WEBHOOK_SECRET,
) -> None:
    if not verify_razorpay_webhook_signature(raw_body, signature, secret):
        raise WebhookSignatureError("Invalid Razorpay webhook signature header.")

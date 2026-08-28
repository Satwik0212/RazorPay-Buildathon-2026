import hmac
import hashlib
import json
import pytest
from app.security.webhook_verification import verify_razorpay_webhook_signature, validate_webhook_signature_or_raise
from app.core.exceptions import WebhookSignatureError


def test_webhook_signature_verification():
    secret = "test_webhook_secret_key_123"
    raw_body = json.dumps({"event": "payment.captured", "id": "evt_123"}).encode("utf-8")

    # Generate genuine HMAC signature
    valid_signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    # 1. Valid signature check
    assert verify_razorpay_webhook_signature(raw_body, valid_signature, secret) is True
    # Should not raise
    validate_webhook_signature_or_raise(raw_body, valid_signature, secret)

    # 2. Tampered body check
    tampered_body = json.dumps({"event": "payment.captured", "id": "evt_tampered"}).encode("utf-8")
    assert verify_razorpay_webhook_signature(tampered_body, valid_signature, secret) is False

    # 3. Forged signature check
    invalid_signature = "bad_signature_digest"
    assert verify_razorpay_webhook_signature(raw_body, invalid_signature, secret) is False
    with pytest.raises(WebhookSignatureError):
        validate_webhook_signature_or_raise(raw_body, invalid_signature, secret)

    # 4. Wrong secret check
    assert verify_razorpay_webhook_signature(raw_body, valid_signature, "wrong_secret") is False

from app.core.exceptions import AppException


class RazorpayIntegrationError(AppException):
    def __init__(self, message: str, code: str = "RAZORPAY_API_ERROR", status_code: int = 502, details: dict = None):
        super().__init__(message=message, code=code, status_code=status_code, details=details)


class RazorpayOrderCreationError(RazorpayIntegrationError):
    def __init__(self, message: str = "Failed to create order on Razorpay.", details: dict = None):
        super().__init__(message=message, code="RAZORPAY_ORDER_CREATION_FAILED", status_code=502, details=details)


class RazorpayPaymentFetchError(RazorpayIntegrationError):
    def __init__(self, message: str = "Failed to fetch payment details from Razorpay.", details: dict = None):
        super().__init__(message=message, code="RAZORPAY_PAYMENT_FETCH_FAILED", status_code=502, details=details)


class RazorpaySignatureVerificationError(RazorpayIntegrationError):
    def __init__(self, message: str = "Razorpay signature verification failed.", details: dict = None):
        super().__init__(message=message, code="RAZORPAY_SIGNATURE_INVALID", status_code=400, details=details)

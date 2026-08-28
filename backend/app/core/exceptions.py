from typing import Any, Dict, Optional


class AppException(Exception):
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppException):
    def __init__(self, resource: str, identifier: Any, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' was not found.",
            code="NOT_FOUND",
            status_code=404,
            details=details or {"resource": resource, "identifier": str(identifier)},
        )


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Invalid or expired authentication credentials.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
            details=details,
        )


class ForbiddenError(AppException):
    def __init__(self, message: str = "You do not have permission to perform this action.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            details=details,
        )


class ConflictError(AppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details,
        )


class IdempotencyConflictError(ConflictError):
    def __init__(self, message: str = "Duplicate request detected or order already created for this authorization.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details=details or {"reason": "IDEMPOTENCY_CONFLICT"},
        )
        self.code = "IDEMPOTENCY_CONFLICT"


class ValidationError(AppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class QuoteExpiredError(AppException):
    def __init__(self, message: str = "Quote has expired. A fresh quote must be generated.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="QUOTE_EXPIRED",
            status_code=400,
            details=details,
        )


class PolicyViolationError(AppException):
    def __init__(self, message: str, reason_code: str = "POLICY_BLOCKED", details: Optional[Dict[str, Any]] = None):
        merged_details = {"reason_code": reason_code}
        if details:
            merged_details.update(details)
        super().__init__(
            message=message,
            code="POLICY_VIOLATION",
            status_code=403,
            details=merged_details,
        )


class InsufficientInventoryError(AppException):
    def __init__(self, product_id: Any, requested: int, available: int):
        super().__init__(
            message=f"Insufficient inventory for product {product_id}. Requested: {requested}, Available: {available}",
            code="INSUFFICIENT_INVENTORY",
            status_code=400,
            details={"product_id": str(product_id), "requested": requested, "available": available},
        )


class WebhookSignatureError(AppException):
    def __init__(self, message: str = "Invalid Razorpay webhook signature.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="INVALID_WEBHOOK_SIGNATURE",
            status_code=400,
            details=details,
        )


class PaymentError(AppException):
    def __init__(self, message: str, code: str = "PAYMENT_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=code,
            status_code=400,
            details=details,
        )

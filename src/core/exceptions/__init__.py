"""
Custom exceptions for FlyReady Lab.

This module provides a hierarchy of exceptions for proper error handling
across the application.
"""

from typing import Optional, Dict, Any


class FlyReadyException(Exception):
    """
    Base exception for FlyReady Lab.

    All custom exceptions should inherit from this class.
    """

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }


# =====================
# Authentication Exceptions
# =====================

class AuthenticationError(FlyReadyException):
    """Base authentication exception."""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, code="AUTHENTICATION_ERROR", status_code=401, **kwargs)


class InvalidCredentialsError(AuthenticationError):
    """Invalid login credentials."""

    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message, code="INVALID_CREDENTIALS")


class TokenExpiredError(AuthenticationError):
    """JWT token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, code="TOKEN_EXPIRED")


class InvalidTokenError(AuthenticationError):
    """JWT token is invalid."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, code="INVALID_TOKEN")


class OAuthError(AuthenticationError):
    """OAuth authentication error."""

    def __init__(self, provider: str, message: str = "OAuth authentication failed"):
        super().__init__(message, code="OAUTH_ERROR", details={"provider": provider})


# =====================
# Authorization Exceptions
# =====================

class AuthorizationError(FlyReadyException):
    """Base authorization exception."""

    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(message, code="AUTHORIZATION_ERROR", status_code=403, **kwargs)


class PermissionDeniedError(AuthorizationError):
    """User lacks required permission."""

    def __init__(self, permission: str, message: str = "Permission denied"):
        super().__init__(message, code="PERMISSION_DENIED", details={"required_permission": permission})


class SubscriptionRequiredError(AuthorizationError):
    """Feature requires subscription."""

    def __init__(self, required_tier: str, message: str = "Subscription required"):
        super().__init__(message, code="SUBSCRIPTION_REQUIRED", details={"required_tier": required_tier})


class RateLimitExceededError(AuthorizationError):
    """Rate limit exceeded."""

    def __init__(self, limit: int, window: int, message: str = "Rate limit exceeded"):
        super().__init__(
            message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"limit": limit, "window_seconds": window}
        )


class UsageLimitExceededError(AuthorizationError):
    """API usage limit exceeded."""

    def __init__(self, limit_type: str, limit: int, message: str = "Usage limit exceeded"):
        super().__init__(
            message,
            code="USAGE_LIMIT_EXCEEDED",
            details={"limit_type": limit_type, "limit": limit}
        )


# =====================
# Resource Exceptions
# =====================

class ResourceError(FlyReadyException):
    """Base resource exception."""
    pass


class NotFoundError(ResourceError):
    """Resource not found."""

    def __init__(self, resource_type: str, resource_id: str, message: Optional[str] = None):
        msg = message or f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(
            msg,
            code="NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class AlreadyExistsError(ResourceError):
    """Resource already exists."""

    def __init__(self, resource_type: str, identifier: str, message: Optional[str] = None):
        msg = message or f"{resource_type} already exists"
        super().__init__(
            msg,
            code="ALREADY_EXISTS",
            status_code=409,
            details={"resource_type": resource_type, "identifier": identifier}
        )


class ConflictError(ResourceError):
    """Resource conflict."""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, code="CONFLICT", status_code=409, details=details)


# =====================
# Validation Exceptions
# =====================

class ValidationError(FlyReadyException):
    """Validation error."""

    def __init__(self, message: str, field: Optional[str] = None, errors: Optional[list] = None):
        details = {}
        if field:
            details["field"] = field
        if errors:
            details["errors"] = errors
        super().__init__(message, code="VALIDATION_ERROR", status_code=422, details=details)


class InvalidInputError(ValidationError):
    """Invalid input data."""

    def __init__(self, field: str, message: str):
        super().__init__(message, field=field)
        self.code = "INVALID_INPUT"


# =====================
# Payment Exceptions
# =====================

class PaymentError(FlyReadyException):
    """Base payment exception."""

    def __init__(self, message: str = "Payment failed", **kwargs):
        super().__init__(message, code="PAYMENT_ERROR", status_code=402, **kwargs)


class PaymentDeclinedError(PaymentError):
    """Payment was declined."""

    def __init__(self, reason: str, message: str = "Payment declined"):
        super().__init__(message, code="PAYMENT_DECLINED", details={"reason": reason})


class PaymentProcessingError(PaymentError):
    """Error processing payment."""

    def __init__(self, provider: str, message: str = "Payment processing error"):
        super().__init__(message, code="PAYMENT_PROCESSING_ERROR", details={"provider": provider})


class RefundError(PaymentError):
    """Refund error."""

    def __init__(self, payment_id: str, message: str = "Refund failed"):
        super().__init__(message, code="REFUND_ERROR", details={"payment_id": payment_id})


# =====================
# External Service Exceptions
# =====================

class ExternalServiceError(FlyReadyException):
    """Base external service exception."""

    def __init__(self, service: str, message: str = "External service error", **kwargs):
        super().__init__(message, code="EXTERNAL_SERVICE_ERROR", details={"service": service}, **kwargs)


class AIServiceError(ExternalServiceError):
    """AI service error."""

    def __init__(self, provider: str, message: str = "AI service error"):
        super().__init__("ai", message, code="AI_SERVICE_ERROR")
        self.details["provider"] = provider


class EmailServiceError(ExternalServiceError):
    """Email service error."""

    def __init__(self, message: str = "Failed to send email"):
        super().__init__("email", message, code="EMAIL_SERVICE_ERROR")


class NotificationServiceError(ExternalServiceError):
    """Notification service error."""

    def __init__(self, channel: str, message: str = "Failed to send notification"):
        super().__init__("notification", message, code="NOTIFICATION_SERVICE_ERROR")
        self.details["channel"] = channel


# =====================
# Business Logic Exceptions
# =====================

class BusinessLogicError(FlyReadyException):
    """Base business logic exception."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="BUSINESS_LOGIC_ERROR", status_code=400, **kwargs)


class BookingError(BusinessLogicError):
    """Booking related error."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)
        self.code = "BOOKING_ERROR"


class SessionNotAvailableError(BookingError):
    """Mentoring session slot not available."""

    def __init__(self, mentor_id: str, slot: str):
        super().__init__(
            f"Time slot {slot} is not available",
            details={"mentor_id": mentor_id, "slot": slot}
        )
        self.code = "SESSION_NOT_AVAILABLE"


class CancellationNotAllowedError(BookingError):
    """Cancellation not allowed."""

    def __init__(self, reason: str):
        super().__init__(f"Cancellation not allowed: {reason}")
        self.code = "CANCELLATION_NOT_ALLOWED"


# =====================
# Export all exceptions
# =====================

__all__ = [
    # Base
    "FlyReadyException",

    # Authentication
    "AuthenticationError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "InvalidTokenError",
    "OAuthError",

    # Authorization
    "AuthorizationError",
    "PermissionDeniedError",
    "SubscriptionRequiredError",
    "RateLimitExceededError",
    "UsageLimitExceededError",

    # Resource
    "ResourceError",
    "NotFoundError",
    "AlreadyExistsError",
    "ConflictError",

    # Validation
    "ValidationError",
    "InvalidInputError",

    # Payment
    "PaymentError",
    "PaymentDeclinedError",
    "PaymentProcessingError",
    "RefundError",

    # External Service
    "ExternalServiceError",
    "AIServiceError",
    "EmailServiceError",
    "NotificationServiceError",

    # Business Logic
    "BusinessLogicError",
    "BookingError",
    "SessionNotAvailableError",
    "CancellationNotAllowedError",
]

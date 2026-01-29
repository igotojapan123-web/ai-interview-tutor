"""
Error Handler Middleware.

Centralized error handling for the API.
"""

import logging
import traceback
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.exceptions import (
    FlyReadyException,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    PaymentError,
    PaymentProcessingError,
    RefundError,
    BookingError,
    SessionNotAvailableError,
    CancellationNotAllowedError,
    RateLimitExceededError,
    ExternalServiceError
)

logger = logging.getLogger(__name__)


# Exception to HTTP status code mapping
EXCEPTION_STATUS_MAP = {
    AuthenticationError: 401,
    AuthorizationError: 403,
    NotFoundError: 404,
    ValidationError: 400,
    PaymentError: 400,
    PaymentProcessingError: 402,
    RefundError: 400,
    BookingError: 400,
    SessionNotAvailableError: 409,
    CancellationNotAllowedError: 400,
    RateLimitExceededError: 429,
    ExternalServiceError: 503,
}


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling exceptions and converting them to HTTP responses.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        try:
            response = await call_next(request)
            return response

        except FlyReadyException as e:
            # Handle custom application errors
            status_code = EXCEPTION_STATUS_MAP.get(type(e), 400)
            error_response = self._create_error_response(
                status_code=status_code,
                error_code=e.code,
                message=str(e),
                details=e.details
            )

            # Log based on severity
            if status_code >= 500:
                logger.error(
                    f"Application error: {e.code}",
                    extra={
                        "error_code": e.code,
                        "status_code": status_code,
                        "path": request.url.path,
                        "method": request.method
                    }
                )
            else:
                logger.warning(
                    f"Client error: {e.code}",
                    extra={
                        "error_code": e.code,
                        "status_code": status_code,
                        "path": request.url.path
                    }
                )

            return error_response

        except ValueError as e:
            # Handle validation errors
            logger.warning(f"Validation error: {str(e)}")
            return self._create_error_response(
                status_code=400,
                error_code="VALIDATION_ERROR",
                message=str(e)
            )

        except Exception as e:
            # Handle unexpected errors
            error_id = self._generate_error_id()
            logger.exception(
                f"Unexpected error [{error_id}]: {str(e)}",
                extra={
                    "error_id": error_id,
                    "path": request.url.path,
                    "method": request.method,
                    "traceback": traceback.format_exc()
                }
            )

            # Don't expose internal errors in production
            return self._create_error_response(
                status_code=500,
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                details={"error_id": error_id}
            )

    def _create_error_response(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: dict = None
    ) -> JSONResponse:
        """Create standardized error response."""
        content = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message
            }
        }

        if details:
            content["error"]["details"] = details

        return JSONResponse(
            status_code=status_code,
            content=content
        )

    def _generate_error_id(self) -> str:
        """Generate unique error ID for tracking."""
        import secrets
        from datetime import datetime
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = secrets.token_hex(4).upper()
        return f"ERR-{timestamp}-{random_part}"


def setup_exception_handlers(app):
    """
    Setup FastAPI exception handlers.

    Alternative to middleware for more specific control.
    """
    from fastapi import HTTPException
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"errors": errors}
                }
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail or "An error occurred"
                }
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        import secrets
        from datetime import datetime

        error_id = f"ERR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4).upper()}"

        logger.exception(
            f"Unhandled exception [{error_id}]: {str(exc)}",
            extra={
                "error_id": error_id,
                "path": request.url.path,
                "method": request.method
            }
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {"error_id": error_id}
                }
            }
        )

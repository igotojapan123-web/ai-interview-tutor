"""
Logging Middleware.

Request/Response logging for the API.
"""

import time
import logging
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    """

    # Paths to exclude from logging
    EXCLUDED_PATHS = {"/health", "/metrics", "/docs", "/openapi.json", "/redoc"}

    # Headers to mask in logs
    SENSITIVE_HEADERS = {"authorization", "x-api-key", "cookie"}

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        # Skip excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Generate request ID
        request_id = self._generate_request_id()

        # Start timer
        start_time = time.perf_counter()

        # Log request
        await self._log_request(request, request_id)

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            duration = time.perf_counter() - start_time
            logger.error(
                f"Request failed [{request_id}]",
                extra={
                    "request_id": request_id,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e)
                }
            )
            raise

        # Calculate duration
        duration = time.perf_counter() - start_time

        # Log response
        self._log_response(request, response, request_id, duration)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response

    async def _log_request(self, request: Request, request_id: str) -> None:
        """Log incoming request details."""
        # Get safe headers
        headers = self._get_safe_headers(dict(request.headers))

        # Try to get request body for certain methods
        body = None
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await self._get_request_body(request)
            except Exception:
                body = "<unable to read body>"

        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": self._get_client_ip(request),
            "user_agent": headers.get("user-agent"),
        }

        if body:
            # Mask sensitive fields in body
            log_data["body"] = self._mask_sensitive_data(body)

        logger.info(
            f"Incoming request [{request_id}]: {request.method} {request.url.path}",
            extra=log_data
        )

    def _log_response(
        self,
        request: Request,
        response: Response,
        request_id: str,
        duration: float
    ) -> None:
        """Log outgoing response details."""
        duration_ms = round(duration * 1000, 2)

        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms
        }

        # Determine log level based on status code
        if response.status_code >= 500:
            logger.error(
                f"Response [{request_id}]: {response.status_code} in {duration_ms}ms",
                extra=log_data
            )
        elif response.status_code >= 400:
            logger.warning(
                f"Response [{request_id}]: {response.status_code} in {duration_ms}ms",
                extra=log_data
            )
        else:
            logger.info(
                f"Response [{request_id}]: {response.status_code} in {duration_ms}ms",
                extra=log_data
            )

    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        import secrets
        return secrets.token_hex(8)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded header (behind proxy)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _get_safe_headers(self, headers: dict) -> dict:
        """Get headers with sensitive values masked."""
        safe_headers = {}
        for key, value in headers.items():
            if key.lower() in self.SENSITIVE_HEADERS:
                safe_headers[key] = "***MASKED***"
            else:
                safe_headers[key] = value
        return safe_headers

    async def _get_request_body(self, request: Request) -> dict:
        """Try to read and parse request body."""
        try:
            body = await request.body()
            if body:
                return json.loads(body.decode())
        except Exception:
            pass
        return None

    def _mask_sensitive_data(self, data: dict) -> dict:
        """Mask sensitive fields in request data."""
        if not isinstance(data, dict):
            return data

        SENSITIVE_FIELDS = {
            "password", "password_hash", "token", "access_token",
            "refresh_token", "api_key", "secret", "credit_card"
        }

        masked = {}
        for key, value in data.items():
            if key.lower() in SENSITIVE_FIELDS:
                masked[key] = "***MASKED***"
            elif isinstance(value, dict):
                masked[key] = self._mask_sensitive_data(value)
            else:
                masked[key] = value
        return masked

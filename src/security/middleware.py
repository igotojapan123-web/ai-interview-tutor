"""
Security Middleware.

Enterprise-grade security middleware for FastAPI.
"""

import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional, Set

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware.

    Adds security headers, request validation, and logging.
    """

    # Security headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache",
    }

    # Content Security Policy
    CSP_POLICY = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://api.openai.com wss:; "
        "frame-ancestors 'none';"
    )

    def __init__(
        self,
        app: FastAPI,
        enable_csp: bool = True,
        enable_hsts: bool = True,
        allowed_hosts: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.enable_csp = enable_csp
        self.enable_hsts = enable_hsts
        self.allowed_hosts = set(allowed_hosts or ["*"])

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add security headers."""
        # Host validation
        if "*" not in self.allowed_hosts:
            host = request.headers.get("host", "").split(":")[0]
            if host not in self.allowed_hosts:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid host header"}
                )

        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Add security headers
        for header, value in self.SECURITY_HEADERS.items():
            response.headers[header] = value

        # Content Security Policy
        if self.enable_csp:
            response.headers["Content-Security-Policy"] = self.CSP_POLICY

        # HSTS (only for HTTPS)
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Processing time header
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        # Request ID for tracing
        request_id = request.headers.get("X-Request-ID", "")
        if request_id:
            response.headers["X-Request-ID"] = request_id

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.

    Implements sliding window rate limiting.
    """

    def __init__(
        self,
        app: FastAPI,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10,
        whitelist_ips: Optional[Set[str]] = None,
        whitelist_paths: Optional[Set[str]] = None,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
        self.whitelist_ips = whitelist_ips or {"127.0.0.1", "::1"}
        self.whitelist_paths = whitelist_paths or {"/health", "/_stcore/health"}

        # Request tracking
        self._minute_requests: Dict[str, List[float]] = defaultdict(list)
        self._hour_requests: Dict[str, List[float]] = defaultdict(list)
        self._burst_requests: Dict[str, List[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for proxy headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _clean_old_requests(
        self,
        requests: List[float],
        window_seconds: int
    ) -> List[float]:
        """Remove requests outside the time window."""
        cutoff = time.time() - window_seconds
        return [ts for ts in requests if ts > cutoff]

    def _check_rate_limit(
        self,
        client_ip: str,
        current_time: float
    ) -> Optional[str]:
        """
        Check if request should be rate limited.

        Returns:
            Error message if limited, None otherwise
        """
        # Clean old requests
        self._burst_requests[client_ip] = self._clean_old_requests(
            self._burst_requests[client_ip], 1
        )
        self._minute_requests[client_ip] = self._clean_old_requests(
            self._minute_requests[client_ip], 60
        )
        self._hour_requests[client_ip] = self._clean_old_requests(
            self._hour_requests[client_ip], 3600
        )

        # Check burst limit (per second)
        if len(self._burst_requests[client_ip]) >= self.burst_limit:
            return "Burst rate limit exceeded"

        # Check per-minute limit
        if len(self._minute_requests[client_ip]) >= self.requests_per_minute:
            return "Minute rate limit exceeded"

        # Check per-hour limit
        if len(self._hour_requests[client_ip]) >= self.requests_per_hour:
            return "Hour rate limit exceeded"

        return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        client_ip = self._get_client_ip(request)
        path = request.url.path

        # Skip rate limiting for whitelisted
        if client_ip in self.whitelist_ips or path in self.whitelist_paths:
            return await call_next(request)

        current_time = time.time()

        # Check rate limit
        error = self._check_rate_limit(client_ip, current_time)
        if error:
            logger.warning(f"Rate limited: {client_ip} - {error}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": error,
                    "retry_after": 60,
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                }
            )

        # Record request
        self._burst_requests[client_ip].append(current_time)
        self._minute_requests[client_ip].append(current_time)
        self._hour_requests[client_ip].append(current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = max(
            0,
            self.requests_per_minute - len(self._minute_requests[client_ip])
        )
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))

        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Request validation middleware.

    Validates incoming requests for security threats.
    """

    # Suspicious patterns
    SQL_INJECTION_PATTERNS = [
        "' or ", "' and ", "'; drop", "--", "/*", "*/",
        "union select", "insert into", "delete from",
    ]

    XSS_PATTERNS = [
        "<script", "javascript:", "onerror=", "onload=",
        "onclick=", "onfocus=", "onmouseover=",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        "../", "..\\", "%2e%2e/", "%2e%2e\\",
    ]

    # Maximum sizes
    MAX_QUERY_LENGTH = 2048
    MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(
        self,
        app: FastAPI,
        enable_sql_check: bool = True,
        enable_xss_check: bool = True,
        enable_path_check: bool = True,
    ):
        super().__init__(app)
        self.enable_sql_check = enable_sql_check
        self.enable_xss_check = enable_xss_check
        self.enable_path_check = enable_path_check

    def _check_patterns(
        self,
        text: str,
        patterns: List[str],
        attack_type: str
    ) -> Optional[str]:
        """Check text for malicious patterns."""
        text_lower = text.lower()
        for pattern in patterns:
            if pattern in text_lower:
                return f"Potential {attack_type} detected"
        return None

    def _validate_request(self, request: Request) -> Optional[str]:
        """
        Validate request for security threats.

        Returns:
            Error message if threat detected, None otherwise
        """
        # Check query string length
        query = str(request.query_params)
        if len(query) > self.MAX_QUERY_LENGTH:
            return "Query string too long"

        # Check for SQL injection
        if self.enable_sql_check:
            error = self._check_patterns(
                query, self.SQL_INJECTION_PATTERNS, "SQL injection"
            )
            if error:
                return error

        # Check for XSS
        if self.enable_xss_check:
            error = self._check_patterns(
                query, self.XSS_PATTERNS, "XSS attack"
            )
            if error:
                return error

        # Check for path traversal
        if self.enable_path_check:
            path = request.url.path
            error = self._check_patterns(
                path, self.PATH_TRAVERSAL_PATTERNS, "path traversal"
            )
            if error:
                return error

        return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate and process request."""
        # Validate request
        error = self._validate_request(request)
        if error:
            logger.warning(
                f"Security threat detected from {request.client.host}: {error}"
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid request"}
            )

        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_BODY_SIZE:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request body too large"}
            )

        return await call_next(request)


def setup_security_middleware(app: FastAPI) -> None:
    """
    Set up all security middleware for the application.

    Usage:
        app = FastAPI()
        setup_security_middleware(app)
    """
    # Add middleware in reverse order (last added = first executed)
    app.add_middleware(RequestValidationMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=60,
        requests_per_hour=1000,
    )
    app.add_middleware(
        SecurityMiddleware,
        enable_csp=True,
        enable_hsts=True,
    )

    logger.info("Security middleware configured")

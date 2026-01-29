"""
Authentication Service.

JWT-based authentication and authorization.
"""

import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # Subject (user_id)
    email: Optional[str] = None
    role: str = "user"
    exp: datetime
    iat: datetime
    jti: Optional[str] = None  # JWT ID for token revocation
    type: str = "access"  # access or refresh


class JWTService:
    """
    JWT authentication service.

    Handles token creation, validation, and refresh.
    """

    def __init__(self):
        settings = get_settings()
        self._secret_key = settings.security.jwt_secret_key
        self._algorithm = settings.security.jwt_algorithm
        self._access_token_expire = settings.security.access_token_expire_minutes
        self._refresh_token_expire = settings.security.refresh_token_expire_days

        # Token blacklist (in production, use Redis)
        self._blacklist: set = set()

    # =========================================================================
    # Token Creation
    # =========================================================================

    def create_access_token(
        self,
        user_id: str,
        email: Optional[str] = None,
        role: str = "user",
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create an access token.

        Args:
            user_id: User identifier
            email: User email
            role: User role
            additional_claims: Extra claims to include

        Returns:
            JWT access token
        """
        import secrets

        now = datetime.utcnow()
        expires = now + timedelta(minutes=self._access_token_expire)

        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "exp": expires,
            "iat": now,
            "jti": secrets.token_urlsafe(16),
            "type": "access",
        }

        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def create_refresh_token(
        self,
        user_id: str,
        email: Optional[str] = None
    ) -> str:
        """
        Create a refresh token.

        Args:
            user_id: User identifier
            email: User email

        Returns:
            JWT refresh token
        """
        import secrets

        now = datetime.utcnow()
        expires = now + timedelta(days=self._refresh_token_expire)

        payload = {
            "sub": user_id,
            "email": email,
            "exp": expires,
            "iat": now,
            "jti": secrets.token_urlsafe(16),
            "type": "refresh",
        }

        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def create_token_pair(
        self,
        user_id: str,
        email: Optional[str] = None,
        role: str = "user"
    ) -> Dict[str, str]:
        """
        Create both access and refresh tokens.

        Returns:
            Dict with access_token and refresh_token
        """
        return {
            "access_token": self.create_access_token(user_id, email, role),
            "refresh_token": self.create_refresh_token(user_id, email),
            "token_type": "bearer",
            "expires_in": self._access_token_expire * 60,  # seconds
        }

    # =========================================================================
    # Token Validation
    # =========================================================================

    def decode_token(self, token: str) -> TokenPayload:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token string

        Returns:
            TokenPayload with decoded data

        Raises:
            HTTPException: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm]
            )

            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and jti in self._blacklist:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )

            return TokenPayload(**payload)

        except JWTError as e:
            logger.warning(f"JWT decode error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def verify_access_token(self, token: str) -> TokenPayload:
        """Verify an access token."""
        payload = self.decode_token(token)
        if payload.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        return payload

    def verify_refresh_token(self, token: str) -> TokenPayload:
        """Verify a refresh token."""
        payload = self.decode_token(token)
        if payload.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        return payload

    # =========================================================================
    # Token Management
    # =========================================================================

    def refresh_tokens(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresh tokens using a refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New token pair
        """
        payload = self.verify_refresh_token(refresh_token)

        # Revoke old refresh token
        if payload.jti:
            self._blacklist.add(payload.jti)

        # Create new tokens
        return self.create_token_pair(
            user_id=payload.sub,
            email=payload.email,
            role=payload.role
        )

    def revoke_token(self, token: str) -> None:
        """
        Revoke a token (add to blacklist).

        Args:
            token: Token to revoke
        """
        try:
            payload = self.decode_token(token)
            if payload.jti:
                self._blacklist.add(payload.jti)
                logger.info(f"Token revoked: {payload.jti[:8]}...")
        except HTTPException:
            pass  # Token was already invalid


# Singleton instance
jwt_service = JWTService()

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


# =========================================================================
# FastAPI Dependencies
# =========================================================================

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> TokenPayload:
    """
    FastAPI dependency to get current authenticated user.

    Usage:
        @app.get("/protected")
        async def protected_route(user: TokenPayload = Depends(get_current_user)):
            return {"user_id": user.sub}
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return jwt_service.verify_access_token(credentials.credentials)


def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication.

    Usage:
        @require_auth
        async def my_handler(request: Request, user: TokenPayload):
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get("request")
        if not request:
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

        if not request:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Request object not found"
            )

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        token = auth_header.split(" ")[1]
        user = jwt_service.verify_access_token(token)
        kwargs["user"] = user

        return await func(*args, **kwargs)

    return wrapper


def require_role(allowed_roles: List[str]) -> Callable:
    """
    Decorator factory to require specific roles.

    Usage:
        @require_role(["admin", "mentor"])
        async def admin_only(request: Request, user: TokenPayload):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("user")
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            if user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required role: {', '.join(allowed_roles)}"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator

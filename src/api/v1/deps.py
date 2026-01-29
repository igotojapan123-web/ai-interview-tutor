"""
API Dependencies.

FastAPI dependency injection for services and authentication.
"""

from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.infrastructure.container import (
    get_container,
    get_auth_service,
    get_user_service,
    get_payment_service,
    get_mentor_service,
    get_job_service,
    get_recommendation_service
)
from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.services.payment_service import PaymentService
from src.services.mentor_service import MentorService
from src.services.job_service import JobService
from src.services.recommendation_service import RecommendationService
from src.core.models.user import User, SubscriptionTier
from src.core.exceptions import AuthenticationError, AuthorizationError

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Get current authenticated user from JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        user = auth_service.verify_access_token(credentials.credentials)
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None

    try:
        return auth_service.verify_access_token(credentials.credentials)
    except AuthenticationError:
        return None


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active (non-suspended) user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    return current_user


async def get_premium_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require premium subscription."""
    if current_user.subscription_tier == SubscriptionTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required"
        )
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require admin role."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


class RateLimiter:
    """Simple rate limiter dependency."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self._requests: dict = {}

    async def __call__(self, current_user: Optional[User] = Depends(get_current_user_optional)):
        # In production, implement proper rate limiting with Redis
        pass


# Service dependencies (re-exported for convenience)
def auth_service() -> AuthService:
    return get_auth_service()


def user_service() -> UserService:
    return get_user_service()


def payment_service() -> PaymentService:
    return get_payment_service()


def mentor_service() -> MentorService:
    return get_mentor_service()


def job_service() -> JobService:
    return get_job_service()


def recommendation_service() -> RecommendationService:
    return get_recommendation_service()

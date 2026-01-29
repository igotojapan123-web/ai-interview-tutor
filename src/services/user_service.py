"""
User service.

Business logic for user management.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from src.core.models.user import User, UserUpdate, SubscriptionTier, UserStatus, UserAPIUsage
from src.core.exceptions import NotFoundError, AuthorizationError, UsageLimitExceededError
from src.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    """User management service."""

    def __init__(self, user_repository: Optional[UserRepository] = None):
        self.user_repo = user_repository or UserRepository()

    def get_user(self, user_id: str) -> User:
        """Get user by ID."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.user_repo.get_by_email(email)

    def update_user(self, user_id: str, update_data: UserUpdate) -> User:
        """Update user profile."""
        user = self.get_user(user_id)

        # Apply updates
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if value is not None:
                setattr(user, field, value)

        user.touch()
        return self.user_repo.update(user)

    def upgrade_subscription(
        self,
        user_id: str,
        tier: SubscriptionTier,
        expires_at: datetime
    ) -> User:
        """Upgrade user subscription."""
        user = self.get_user(user_id)
        user.upgrade_subscription(tier, expires_at)
        logger.info(f"User {user_id} upgraded to {tier.value}")
        return self.user_repo.update(user)

    def downgrade_subscription(self, user_id: str) -> User:
        """Downgrade user to free tier."""
        user = self.get_user(user_id)
        user.downgrade_to_free()
        logger.info(f"User {user_id} downgraded to free")
        return self.user_repo.update(user)

    def check_api_limit(self, user_id: str, limit_type: str) -> bool:
        """
        Check if user has remaining API quota.

        Args:
            user_id: User ID
            limit_type: Type of limit (ai_calls, document_reviews, etc.)

        Returns:
            True if quota available

        Raises:
            UsageLimitExceededError: If quota exceeded
        """
        user = self.get_user(user_id)

        # Get usage (in production, track in database)
        # For now, always return True for premium users
        if user.is_premium:
            return True

        # Check tier limits
        from src.core.models.user import APIUsageLimit
        limits = APIUsageLimit.get_limits(user.subscription_tier)

        if limit_type == "ai_calls":
            limit = limits.daily_ai_calls
        elif limit_type == "document_reviews":
            limit = limits.daily_document_reviews
        else:
            return True

        # In production, check actual usage from database
        # For now, return True
        return True

    def increment_usage(self, user_id: str, usage_type: str) -> None:
        """Increment usage counter for a user."""
        # In production, update usage tracking in database
        logger.debug(f"Incremented {usage_type} for user {user_id}")

    def suspend_user(self, user_id: str, reason: str, admin_id: str) -> User:
        """Suspend a user account."""
        user = self.get_user(user_id)
        user.suspend(reason)
        user.updated_by = admin_id
        logger.warning(f"User {user_id} suspended by {admin_id}: {reason}")
        return self.user_repo.update(user)

    def activate_user(self, user_id: str) -> User:
        """Activate a user account."""
        user = self.get_user(user_id)
        user.activate()
        logger.info(f"User {user_id} activated")
        return self.user_repo.update(user)

    def delete_user(self, user_id: str) -> bool:
        """Soft delete a user."""
        user = self.get_user(user_id)
        user.status = UserStatus.DELETED
        self.user_repo.update(user)
        logger.info(f"User {user_id} deleted")
        return True

    def search_users(
        self,
        query: Optional[str] = None,
        status: Optional[UserStatus] = None,
        tier: Optional[SubscriptionTier] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Search users."""
        return self.user_repo.search(
            query=query,
            status=status,
            tier=tier,
            page=page,
            page_size=page_size
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get user statistics."""
        return self.user_repo.get_stats()

    def get_users_for_notification(
        self,
        notification_type: str,
        filters: Optional[Dict] = None
    ) -> List[User]:
        """Get users eligible for a notification."""
        users = self.user_repo.get_active_users()

        # Filter based on notification preferences
        result = []
        for user in users:
            prefs = user.preferences

            if notification_type == "email" and prefs.notification_email:
                result.append(user)
            elif notification_type == "push" and prefs.notification_push:
                result.append(user)
            elif notification_type == "kakao" and prefs.notification_kakao:
                result.append(user)

        return result

"""
User repository implementation.
"""

from typing import Optional, List

from src.repositories.base import JSONRepository
from src.core.models.user import User, UserStatus, SubscriptionTier, AuthProvider


class UserRepository(JSONRepository[User]):
    """
    Repository for User entities.

    Provides user-specific query methods.
    """

    def __init__(self, data_dir: str = "data"):
        super().__init__(
            data_dir=data_dir,
            filename="users.json",
            entity_class=User
        )

    def get_by_email(self, email: str) -> Optional[User]:
        """Find user by email address."""
        return self.find_one(email=email.lower())

    def get_by_provider(self, provider: AuthProvider, provider_id: str) -> Optional[User]:
        """Find user by OAuth provider and provider ID."""
        return self.find_one(auth_provider=provider.value, provider_id=provider_id)

    def get_active_users(self) -> List[User]:
        """Get all active users."""
        return self.find(status=UserStatus.ACTIVE.value)

    def get_by_subscription_tier(self, tier: SubscriptionTier) -> List[User]:
        """Get users by subscription tier."""
        return self.find(subscription_tier=tier.value)

    def get_premium_users(self) -> List[User]:
        """Get users with premium or enterprise subscription."""
        return self.find(
            subscription_tier=lambda t: t in [
                SubscriptionTier.PREMIUM.value,
                SubscriptionTier.ENTERPRISE.value
            ]
        )

    def get_users_with_expiring_subscription(self, days: int = 7) -> List[User]:
        """Get users whose subscription expires within given days."""
        from datetime import datetime, timedelta

        cutoff = datetime.utcnow() + timedelta(days=days)

        users = self.get_all()
        return [
            user for user in users
            if user.subscription_expires_at
            and user.subscription_expires_at <= cutoff
            and user.subscription_tier != SubscriptionTier.FREE
        ]

    def search(
        self,
        query: Optional[str] = None,
        status: Optional[UserStatus] = None,
        tier: Optional[SubscriptionTier] = None,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """
        Search users with filters.

        Args:
            query: Search in name and email
            status: Filter by status
            tier: Filter by subscription tier
            page: Page number
            page_size: Items per page

        Returns:
            Paginated results
        """
        criteria = {}

        if status:
            criteria["status"] = status.value

        if tier:
            criteria["subscription_tier"] = tier.value

        users = self.find(**criteria)

        # Apply text search
        if query:
            query_lower = query.lower()
            users = [
                u for u in users
                if query_lower in u.name.lower() or query_lower in u.email.lower()
            ]

        # Paginate
        total = len(users)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "items": users[start:end],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    def email_exists(self, email: str) -> bool:
        """Check if email is already registered."""
        return self.get_by_email(email) is not None

    def update_last_login(self, user_id: str) -> Optional[User]:
        """Update user's last login timestamp."""
        user = self.get_by_id(user_id)
        if user:
            user.record_login()
            return self.update(user)
        return None

    def get_stats(self) -> dict:
        """Get user statistics."""
        users = self.get_all()

        total = len(users)
        by_status = {}
        by_tier = {}

        for user in users:
            # Count by status
            status = user.status.value if hasattr(user.status, "value") else user.status
            by_status[status] = by_status.get(status, 0) + 1

            # Count by tier
            tier = user.subscription_tier.value if hasattr(user.subscription_tier, "value") else user.subscription_tier
            by_tier[tier] = by_tier.get(tier, 0) + 1

        return {
            "total": total,
            "by_status": by_status,
            "by_tier": by_tier,
            "active": by_status.get(UserStatus.ACTIVE.value, 0),
            "premium": by_tier.get(SubscriptionTier.PREMIUM.value, 0) + by_tier.get(SubscriptionTier.ENTERPRISE.value, 0)
        }

"""
User domain models.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import Field, EmailStr, field_validator

from src.core.models.base import AggregateRoot, BaseModel, get_current_timestamp


class SubscriptionTier(str, Enum):
    """User subscription tiers."""
    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class AuthProvider(str, Enum):
    """Authentication providers."""
    LOCAL = "local"
    KAKAO = "kakao"
    GOOGLE = "google"
    APPLE = "apple"


class UserRole(str, Enum):
    """User roles for authorization."""
    USER = "user"
    MENTOR = "mentor"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class UserStatus(str, Enum):
    """User account status."""
    PENDING = "pending"       # Email verification pending
    ACTIVE = "active"         # Active account
    SUSPENDED = "suspended"   # Temporarily suspended
    BANNED = "banned"         # Permanently banned
    DELETED = "deleted"       # Soft deleted


class APIUsageLimit(BaseModel):
    """API usage limits per tier."""
    tier: SubscriptionTier
    daily_ai_calls: int = Field(description="Daily AI API calls allowed")
    daily_document_reviews: int = Field(description="Daily document reviews allowed")
    monthly_mentor_sessions: int = Field(description="Monthly mentor sessions allowed")
    storage_mb: int = Field(description="Storage limit in MB")

    @classmethod
    def get_limits(cls, tier: SubscriptionTier) -> "APIUsageLimit":
        """Get limits for a specific tier."""
        limits = {
            SubscriptionTier.FREE: cls(
                tier=tier,
                daily_ai_calls=10,
                daily_document_reviews=1,
                monthly_mentor_sessions=0,
                storage_mb=100
            ),
            SubscriptionTier.STANDARD: cls(
                tier=tier,
                daily_ai_calls=50,
                daily_document_reviews=10,
                monthly_mentor_sessions=1,
                storage_mb=1000
            ),
            SubscriptionTier.PREMIUM: cls(
                tier=tier,
                daily_ai_calls=999999,  # Unlimited
                daily_document_reviews=999999,
                monthly_mentor_sessions=3,
                storage_mb=10000
            ),
            SubscriptionTier.ENTERPRISE: cls(
                tier=tier,
                daily_ai_calls=999999,
                daily_document_reviews=999999,
                monthly_mentor_sessions=999999,
                storage_mb=100000
            ),
        }
        return limits.get(tier, limits[SubscriptionTier.FREE])


class UserAPIUsage(BaseModel):
    """Track user's API usage."""
    user_id: str
    usage_date: date = Field(default_factory=date.today)
    ai_calls: int = Field(default=0)
    document_reviews: int = Field(default=0)
    mentor_sessions_this_month: int = Field(default=0)
    storage_used_mb: float = Field(default=0.0)

    def can_make_ai_call(self, tier: SubscriptionTier) -> bool:
        """Check if user can make an AI call."""
        limits = APIUsageLimit.get_limits(tier)
        return self.ai_calls < limits.daily_ai_calls

    def can_review_document(self, tier: SubscriptionTier) -> bool:
        """Check if user can review a document."""
        limits = APIUsageLimit.get_limits(tier)
        return self.document_reviews < limits.daily_document_reviews

    def increment_ai_calls(self) -> None:
        """Increment AI call count."""
        self.ai_calls += 1

    def increment_document_reviews(self) -> None:
        """Increment document review count."""
        self.document_reviews += 1


class UserPreferences(BaseModel):
    """User preferences and settings."""
    language: str = Field(default="ko", description="Preferred language")
    timezone: str = Field(default="Asia/Seoul", description="User timezone")
    notification_email: bool = Field(default=True)
    notification_push: bool = Field(default=True)
    notification_kakao: bool = Field(default=False)
    dark_mode: bool = Field(default=False)
    target_airlines: List[str] = Field(default_factory=list, description="Target airline codes")
    target_job_types: List[str] = Field(default_factory=list, description="Target job types")


class User(AggregateRoot):
    """
    User aggregate root.

    Represents a user in the system with all related information.
    """

    # Identity
    email: EmailStr = Field(description="User email address")
    name: str = Field(min_length=1, max_length=100, description="User display name")
    phone: Optional[str] = Field(default=None, max_length=20)
    profile_image: Optional[str] = Field(default=None, description="Profile image URL")

    # Authentication
    auth_provider: AuthProvider = Field(default=AuthProvider.LOCAL)
    provider_id: Optional[str] = Field(default=None, description="OAuth provider user ID")
    hashed_password: Optional[str] = Field(default=None, description="Hashed password for local auth")
    email_verified: bool = Field(default=False)
    phone_verified: bool = Field(default=False)

    # Authorization
    role: UserRole = Field(default=UserRole.USER)
    permissions: List[str] = Field(default_factory=list, description="Additional permissions")

    # Status
    status: UserStatus = Field(default=UserStatus.PENDING)
    status_reason: Optional[str] = Field(default=None, description="Reason for status change")

    # Subscription
    subscription_tier: SubscriptionTier = Field(default=SubscriptionTier.FREE)
    subscription_expires_at: Optional[datetime] = Field(default=None)
    trial_used: bool = Field(default=False, description="Whether user has used free trial")

    # Profile
    bio: Optional[str] = Field(default=None, max_length=500)
    birth_date: Optional[date] = Field(default=None)
    gender: Optional[str] = Field(default=None)

    # Preferences
    preferences: UserPreferences = Field(default_factory=UserPreferences)

    # Activity
    last_login_at: Optional[datetime] = Field(default=None)
    login_count: int = Field(default=0)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower().strip()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Normalize phone number."""
        if v is None:
            return None
        # Remove non-numeric characters
        cleaned = "".join(c for c in v if c.isdigit() or c == "+")
        return cleaned if cleaned else None

    @property
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == UserStatus.ACTIVE

    @property
    def is_premium(self) -> bool:
        """Check if user has premium or higher subscription."""
        return self.subscription_tier in [SubscriptionTier.PREMIUM, SubscriptionTier.ENTERPRISE]

    @property
    def subscription_active(self) -> bool:
        """Check if subscription is still active."""
        if self.subscription_tier == SubscriptionTier.FREE:
            return True
        if self.subscription_expires_at is None:
            return False
        return self.subscription_expires_at > get_current_timestamp()

    def record_login(self) -> None:
        """Record a login event."""
        self.last_login_at = get_current_timestamp()
        self.login_count += 1
        self.touch()

    def activate(self) -> None:
        """Activate user account."""
        self.status = UserStatus.ACTIVE
        self.email_verified = True
        self.touch()

    def suspend(self, reason: str) -> None:
        """Suspend user account."""
        self.status = UserStatus.SUSPENDED
        self.status_reason = reason
        self.touch()

    def upgrade_subscription(self, tier: SubscriptionTier, expires_at: datetime) -> None:
        """Upgrade user subscription."""
        self.subscription_tier = tier
        self.subscription_expires_at = expires_at
        self.touch()
        self.increment_version()

    def downgrade_to_free(self) -> None:
        """Downgrade to free tier."""
        self.subscription_tier = SubscriptionTier.FREE
        self.subscription_expires_at = None
        self.touch()


class UserCreate(BaseModel):
    """DTO for creating a new user."""
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: Optional[str] = Field(default=None, min_length=8)
    auth_provider: AuthProvider = Field(default=AuthProvider.LOCAL)
    provider_id: Optional[str] = None
    phone: Optional[str] = None
    profile_image: Optional[str] = None


class UserUpdate(BaseModel):
    """DTO for updating a user."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    phone: Optional[str] = None
    profile_image: Optional[str] = None
    bio: Optional[str] = Field(default=None, max_length=500)
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    preferences: Optional[UserPreferences] = None


class UserResponse(BaseModel):
    """DTO for user response (public-safe)."""
    id: str
    email: str
    name: str
    profile_image: Optional[str]
    role: UserRole
    subscription_tier: SubscriptionTier
    created_at: datetime

    @classmethod
    def from_user(cls, user: User) -> "UserResponse":
        """Create response from User entity."""
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            profile_image=user.profile_image,
            role=user.role,
            subscription_tier=user.subscription_tier,
            created_at=user.created_at
        )

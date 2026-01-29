"""
SQLAlchemy Database Models.

ORM models for all database tables.
"""

from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List
import uuid

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date, Time,
    Text, Numeric, ForeignKey, Enum, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from src.database.session import Base
from src.core.models.user import AuthProvider, SubscriptionTier
from src.core.models.payment import PaymentStatus, PaymentMethod, BillingCycle
from src.core.models.mentor import MentorType, MentorStatus, SessionType, SessionStatus
from src.core.models.job import JobType, RecruitmentStatus
from src.core.models.recommendation import SkillCategory, ContentType, DifficultyLevel


def generate_uuid() -> str:
    """Generate UUID string."""
    return str(uuid.uuid4())


# =============================================================================
# User Models
# =============================================================================

class UserModel(Base):
    """User database model."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    profile_image: Mapped[Optional[str]] = mapped_column(String(500))

    # Authentication
    auth_provider: Mapped[str] = mapped_column(
        String(20),
        default=AuthProvider.EMAIL.value
    )
    provider_user_id: Mapped[Optional[str]] = mapped_column(String(255))

    # Subscription
    subscription_tier: Mapped[str] = mapped_column(
        String(20),
        default=SubscriptionTier.FREE.value
    )
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Preferences
    target_airlines: Mapped[Optional[str]] = mapped_column(JSON, default=list)
    notification_email: Mapped[bool] = mapped_column(Boolean, default=True)
    notification_push: Mapped[bool] = mapped_column(Boolean, default=True)

    # Usage tracking
    interview_sessions_today: Mapped[int] = mapped_column(Integer, default=0)
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    last_interview_date: Mapped[Optional[date]] = mapped_column(Date)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    payments = relationship("PaymentModel", back_populates="user")
    subscriptions = relationship("SubscriptionModel", back_populates="user")
    mentor_profile = relationship("MentorModel", back_populates="user", uselist=False)
    mentee_sessions = relationship(
        "SessionModel",
        foreign_keys="SessionModel.mentee_id",
        back_populates="mentee"
    )

    # Indexes
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_subscription", "subscription_tier"),
        Index("idx_user_created", "created_at"),
    )


# =============================================================================
# Payment Models
# =============================================================================

class PaymentModel(Base):
    """Payment database model."""

    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    product_id: Mapped[str] = mapped_column(String(50), nullable=False)
    order_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="KRW")
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=PaymentStatus.PENDING.value)

    # Provider info
    provider_transaction_id: Mapped[Optional[str]] = mapped_column(String(100))
    receipt_url: Mapped[Optional[str]] = mapped_column(String(500))
    provider_response: Mapped[Optional[str]] = mapped_column(JSON)

    # Refund
    refunded_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    refund_reason: Mapped[Optional[str]] = mapped_column(Text)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    user = relationship("UserModel", back_populates="payments")

    __table_args__ = (
        Index("idx_payment_user", "user_id"),
        Index("idx_payment_order", "order_id"),
        Index("idx_payment_status", "status"),
    )


class SubscriptionModel(Base):
    """Subscription database model."""

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    product_id: Mapped[str] = mapped_column(String(50), nullable=False)

    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    billing_cycle: Mapped[str] = mapped_column(String(20), nullable=False)

    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    next_billing_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)

    last_payment_id: Mapped[Optional[str]] = mapped_column(String(36))
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("UserModel", back_populates="subscriptions")

    __table_args__ = (
        Index("idx_subscription_user", "user_id"),
        Index("idx_subscription_active", "is_active"),
    )


# =============================================================================
# Mentor Models
# =============================================================================

class MentorModel(Base):
    """Mentor database model."""

    __tablename__ = "mentors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    mentor_type: Mapped[str] = mapped_column(String(20), nullable=False)
    bio: Mapped[str] = mapped_column(Text, nullable=False)
    profile_image: Mapped[Optional[str]] = mapped_column(String(500))

    # Experience
    airlines: Mapped[str] = mapped_column(JSON, default=list)
    current_airline: Mapped[Optional[str]] = mapped_column(String(10))
    years_experience: Mapped[int] = mapped_column(Integer, default=0)

    # Services
    session_types: Mapped[str] = mapped_column(JSON, default=list)
    hourly_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    available_days: Mapped[str] = mapped_column(JSON, default=list)
    available_times: Mapped[str] = mapped_column(JSON, default=list)

    # Stats
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    verified_by: Mapped[Optional[str]] = mapped_column(String(36))

    status: Mapped[str] = mapped_column(String(20), default=MentorStatus.PENDING.value)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("UserModel", back_populates="mentor_profile")
    sessions = relationship("SessionModel", back_populates="mentor")

    __table_args__ = (
        Index("idx_mentor_type", "mentor_type"),
        Index("idx_mentor_rating", "rating"),
        Index("idx_mentor_verified", "is_verified"),
    )


class SessionModel(Base):
    """Mentoring session database model."""

    __tablename__ = "mentoring_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    mentor_id: Mapped[str] = mapped_column(String(36), ForeignKey("mentors.id"), nullable=False)
    mentee_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    session_type: Mapped[str] = mapped_column(String(30), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    scheduled_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)

    price: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=SessionStatus.PENDING.value)
    meeting_link: Mapped[Optional[str]] = mapped_column(String(500))

    notes: Mapped[Optional[str]] = mapped_column(Text)
    mentee_notes: Mapped[Optional[str]] = mapped_column(Text)
    mentor_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Review
    rating: Mapped[Optional[float]] = mapped_column(Float)
    review: Mapped[Optional[str]] = mapped_column(Text)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Cancellation
    cancelled_by: Mapped[Optional[str]] = mapped_column(String(36))
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    mentor = relationship("MentorModel", back_populates="sessions")
    mentee = relationship("UserModel", back_populates="mentee_sessions")

    __table_args__ = (
        Index("idx_session_mentor", "mentor_id"),
        Index("idx_session_mentee", "mentee_id"),
        Index("idx_session_date", "scheduled_date"),
        Index("idx_session_status", "status"),
    )


# =============================================================================
# Job Models
# =============================================================================

class JobPostingModel(Base):
    """Job posting database model."""

    __tablename__ = "job_postings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    airline_code: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    job_type: Mapped[str] = mapped_column(String(30), nullable=False)

    status: Mapped[str] = mapped_column(String(20), default=RecruitmentStatus.UPCOMING.value)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str] = mapped_column(JSON, default=list)

    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)

    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_domestic: Mapped[bool] = mapped_column(Boolean, default=True)

    content_hash: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    last_crawled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_job_airline", "airline_code"),
        Index("idx_job_status", "status"),
        Index("idx_job_dates", "start_date", "end_date"),
    )


class JobAlertModel(Base):
    """Job alert preferences database model."""

    __tablename__ = "job_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=False)

    airlines: Mapped[str] = mapped_column(JSON, default=list)
    job_types: Mapped[str] = mapped_column(JSON, default=list)

    notify_new_posting: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_deadline_7_days: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_deadline_3_days: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_deadline_1_day: Mapped[bool] = mapped_column(Boolean, default=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


# =============================================================================
# Recommendation Models
# =============================================================================

class SkillProfileModel(Base):
    """Skill profile database model."""

    __tablename__ = "skill_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=False)

    skills: Mapped[str] = mapped_column(JSON, default=dict)
    overall_readiness: Mapped[float] = mapped_column(Float, default=0.0)

    total_study_time_minutes: Mapped[int] = mapped_column(Integer, default=0)
    completed_content_count: Mapped[int] = mapped_column(Integer, default=0)
    current_streak_days: Mapped[int] = mapped_column(Integer, default=0)

    last_activity_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class LearningContentModel(Base):
    """Learning content database model."""

    __tablename__ = "learning_content"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    content_type: Mapped[str] = mapped_column(String(30), nullable=False)
    skill_category: Mapped[str] = mapped_column(String(30), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default=DifficultyLevel.BEGINNER.value)

    duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    content_url: Mapped[Optional[str]] = mapped_column(String(500))
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))

    tags: Mapped[str] = mapped_column(JSON, default=list)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    view_count: Mapped[int] = mapped_column(Integer, default=0)
    completion_count: Mapped[int] = mapped_column(Integer, default=0)
    average_rating: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_content_skill", "skill_category"),
        Index("idx_content_type", "content_type"),
        Index("idx_content_premium", "is_premium"),
    )

"""
Unit Tests for Domain Models.

Tests for all Pydantic models.
"""

import pytest
from datetime import datetime, timedelta, date, time
from decimal import Decimal
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.models.user import User, AuthProvider, SubscriptionTier
from src.core.models.payment import (
    Payment, PaymentStatus, PaymentMethod,
    Subscription, BillingCycle, Product, ProductType
)
from src.core.models.mentor import (
    Mentor, MentorType, SessionType, MentorStatus,
    MentoringSession, SessionStatus
)
from src.core.models.job import JobPosting, JobType, RecruitmentStatus
from src.core.models.recommendation import (
    SkillCategory, SkillScore, SkillProfile,
    LearningContent, ContentType, DifficultyLevel
)


# =============================================================================
# User Model Tests
# =============================================================================

class TestUserModel:
    """Tests for User model."""

    @pytest.mark.unit
    def test_user_creation(self):
        """Test basic user creation."""
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash="$2b$12$test",
            auth_provider=AuthProvider.EMAIL
        )

        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.subscription_tier == SubscriptionTier.FREE
        assert user.is_active is True

    @pytest.mark.unit
    def test_user_id_auto_generation(self):
        """Test that user ID is auto-generated."""
        user = User(
            email="autoid@example.com",
            name="Auto ID User",
            password_hash="$2b$12$test",
            auth_provider=AuthProvider.EMAIL
        )

        assert user.id is not None
        assert len(user.id) > 0

    @pytest.mark.unit
    def test_user_subscription_check(self):
        """Test subscription expiry check."""
        # Active subscription
        user = User(
            email="premium@example.com",
            name="Premium User",
            password_hash="$2b$12$test",
            auth_provider=AuthProvider.EMAIL,
            subscription_tier=SubscriptionTier.PREMIUM,
            subscription_expires_at=datetime.utcnow() + timedelta(days=30)
        )
        assert user.has_active_subscription is True

        # Expired subscription
        expired_user = User(
            email="expired@example.com",
            name="Expired User",
            password_hash="$2b$12$test",
            auth_provider=AuthProvider.EMAIL,
            subscription_tier=SubscriptionTier.PREMIUM,
            subscription_expires_at=datetime.utcnow() - timedelta(days=1)
        )
        assert expired_user.has_active_subscription is False

    @pytest.mark.unit
    def test_user_interview_limits(self):
        """Test interview limit based on tier."""
        free_user = User(
            email="free@example.com",
            name="Free User",
            password_hash="$2b$12$test",
            auth_provider=AuthProvider.EMAIL,
            subscription_tier=SubscriptionTier.FREE
        )
        assert free_user.interview_limit_daily == 3

        premium_user = User(
            email="premium@example.com",
            name="Premium User",
            password_hash="$2b$12$test",
            auth_provider=AuthProvider.EMAIL,
            subscription_tier=SubscriptionTier.PREMIUM
        )
        assert premium_user.interview_limit_daily == 999999  # Unlimited


# =============================================================================
# Payment Model Tests
# =============================================================================

class TestPaymentModel:
    """Tests for Payment model."""

    @pytest.mark.unit
    @pytest.mark.payment
    def test_payment_creation(self):
        """Test payment creation."""
        payment = Payment(
            user_id="user-001",
            product_id="standard_monthly",
            order_id="ORD-20240101-ABCD",
            amount=Decimal("19900"),
            payment_method=PaymentMethod.KAKAOPAY
        )

        assert payment.status == PaymentStatus.PENDING
        assert payment.amount == Decimal("19900")

    @pytest.mark.unit
    @pytest.mark.payment
    def test_payment_complete(self):
        """Test payment completion."""
        payment = Payment(
            user_id="user-001",
            product_id="standard_monthly",
            order_id="ORD-20240101-ABCD",
            amount=Decimal("19900"),
            payment_method=PaymentMethod.KAKAOPAY
        )

        payment.complete(
            provider_transaction_id="TXN-001",
            receipt_url="https://receipt.url"
        )

        assert payment.status == PaymentStatus.COMPLETED
        assert payment.provider_transaction_id == "TXN-001"
        assert payment.paid_at is not None

    @pytest.mark.unit
    @pytest.mark.payment
    def test_payment_refund(self):
        """Test payment refund."""
        payment = Payment(
            user_id="user-001",
            product_id="standard_monthly",
            order_id="ORD-20240101-ABCD",
            amount=Decimal("19900"),
            payment_method=PaymentMethod.KAKAOPAY,
            status=PaymentStatus.COMPLETED
        )

        payment.refund(Decimal("19900"), "Customer request")

        assert payment.status == PaymentStatus.REFUNDED
        assert payment.refunded_amount == Decimal("19900")


class TestSubscriptionModel:
    """Tests for Subscription model."""

    @pytest.mark.unit
    @pytest.mark.payment
    def test_subscription_creation(self):
        """Test subscription creation."""
        sub = Subscription(
            user_id="user-001",
            product_id="premium_monthly",
            tier=SubscriptionTier.PREMIUM,
            billing_cycle=BillingCycle.MONTHLY,
            starts_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )

        assert sub.is_active is True
        assert sub.tier == SubscriptionTier.PREMIUM

    @pytest.mark.unit
    @pytest.mark.payment
    def test_subscription_cancel(self):
        """Test subscription cancellation."""
        sub = Subscription(
            user_id="user-001",
            product_id="premium_monthly",
            tier=SubscriptionTier.PREMIUM,
            billing_cycle=BillingCycle.MONTHLY,
            starts_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )

        sub.cancel()

        assert sub.auto_renew is False
        assert sub.cancelled_at is not None


# =============================================================================
# Mentor Model Tests
# =============================================================================

class TestMentorModel:
    """Tests for Mentor model."""

    @pytest.mark.unit
    @pytest.mark.mentor
    def test_mentor_creation(self):
        """Test mentor creation."""
        mentor = Mentor(
            user_id="mentor-user-001",
            display_name="김멘토",
            mentor_type=MentorType.CURRENT_CREW,
            bio="대한항공 현직 승무원입니다.",
            airlines=["KE"],
            years_experience=5,
            session_types=[SessionType.MOCK_INTERVIEW],
            hourly_rate=50000,
            available_days=["월", "화"],
            available_times=["10:00", "14:00"]
        )

        assert mentor.display_name == "김멘토"
        assert mentor.is_verified is False
        assert mentor.rating == 0.0

    @pytest.mark.unit
    @pytest.mark.mentor
    def test_mentor_verification(self):
        """Test mentor verification."""
        mentor = Mentor(
            user_id="mentor-user-001",
            display_name="김멘토",
            mentor_type=MentorType.CURRENT_CREW,
            bio="테스트",
            airlines=["KE"],
            years_experience=5,
            session_types=[SessionType.MOCK_INTERVIEW],
            hourly_rate=50000,
            available_days=["월"],
            available_times=["10:00"]
        )

        mentor.verify("admin-001")

        assert mentor.is_verified is True
        assert mentor.verified_at is not None
        assert mentor.verified_by == "admin-001"

    @pytest.mark.unit
    @pytest.mark.mentor
    def test_mentor_rating_update(self):
        """Test mentor rating update."""
        mentor = Mentor(
            user_id="mentor-user-001",
            display_name="김멘토",
            mentor_type=MentorType.CURRENT_CREW,
            bio="테스트",
            airlines=["KE"],
            years_experience=5,
            session_types=[SessionType.MOCK_INTERVIEW],
            hourly_rate=50000,
            available_days=["월"],
            available_times=["10:00"],
            rating=4.0,
            total_reviews=10
        )

        mentor.update_rating(5.0)

        # New rating should be weighted average
        assert mentor.rating > 4.0
        assert mentor.total_reviews == 11


class TestMentoringSessionModel:
    """Tests for MentoringSession model."""

    @pytest.mark.unit
    @pytest.mark.mentor
    def test_session_creation(self):
        """Test session creation."""
        session = MentoringSession(
            mentor_id="mentor-001",
            mentee_id="user-001",
            session_type=SessionType.MOCK_INTERVIEW,
            scheduled_date=date.today() + timedelta(days=3),
            scheduled_time=time(14, 0),
            duration_minutes=60,
            price=50000
        )

        assert session.status == SessionStatus.PENDING
        assert session.can_cancel is True

    @pytest.mark.unit
    @pytest.mark.mentor
    def test_session_confirm(self):
        """Test session confirmation."""
        session = MentoringSession(
            mentor_id="mentor-001",
            mentee_id="user-001",
            session_type=SessionType.MOCK_INTERVIEW,
            scheduled_date=date.today() + timedelta(days=3),
            scheduled_time=time(14, 0),
            duration_minutes=60,
            price=50000
        )

        session.confirm("https://meet.example.com/session-001")

        assert session.status == SessionStatus.CONFIRMED
        assert session.meeting_link is not None


# =============================================================================
# Job Model Tests
# =============================================================================

class TestJobPostingModel:
    """Tests for JobPosting model."""

    @pytest.mark.unit
    def test_job_posting_creation(self):
        """Test job posting creation."""
        job = JobPosting(
            airline_code="KE",
            title="2024 객실승무원 채용",
            job_type=JobType.CABIN_CREW,
            description="대한항공 객실승무원을 모집합니다.",
            requirements=["TOEIC 600+"],
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30)
        )

        assert job.airline_code == "KE"
        assert job.is_open is True
        assert job.status == RecruitmentStatus.OPEN

    @pytest.mark.unit
    def test_job_days_until_deadline(self):
        """Test days until deadline calculation."""
        job = JobPosting(
            airline_code="KE",
            title="테스트 채용",
            job_type=JobType.CABIN_CREW,
            description="테스트",
            requirements=[],
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7)
        )

        assert job.days_until_deadline == 7

    @pytest.mark.unit
    def test_expired_job_not_open(self):
        """Test that expired job is not open."""
        job = JobPosting(
            airline_code="KE",
            title="만료된 채용",
            job_type=JobType.CABIN_CREW,
            description="테스트",
            requirements=[],
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() - timedelta(days=30)
        )

        assert job.is_open is False


# =============================================================================
# Recommendation Model Tests
# =============================================================================

class TestSkillModels:
    """Tests for skill-related models."""

    @pytest.mark.unit
    def test_skill_score_creation(self):
        """Test skill score creation."""
        score = SkillScore(
            category=SkillCategory.ENGLISH_SPEAKING,
            score=75.0
        )

        assert score.category == SkillCategory.ENGLISH_SPEAKING
        assert score.score == 75.0

    @pytest.mark.unit
    def test_skill_profile_creation(self):
        """Test skill profile creation."""
        profile = SkillProfile(user_id="user-001")

        assert profile.user_id == "user-001"
        assert profile.overall_readiness == 0.0

    @pytest.mark.unit
    def test_skill_profile_update(self):
        """Test skill profile update."""
        profile = SkillProfile(user_id="user-001")

        # Add some skills
        profile.skills[SkillCategory.ENGLISH_SPEAKING.value] = SkillScore(
            category=SkillCategory.ENGLISH_SPEAKING,
            score=80.0
        )
        profile.skills[SkillCategory.KOREAN_SPEAKING.value] = SkillScore(
            category=SkillCategory.KOREAN_SPEAKING,
            score=90.0
        )

        # Update skill
        profile.update_skill(SkillCategory.ENGLISH_SPEAKING, 85.0)

        assert profile.skills[SkillCategory.ENGLISH_SPEAKING.value].score == 85.0


class TestLearningContentModel:
    """Tests for LearningContent model."""

    @pytest.mark.unit
    def test_content_creation(self):
        """Test learning content creation."""
        content = LearningContent(
            title="영어 자기소개 연습",
            description="영어로 자기소개하는 방법을 배웁니다.",
            content_type=ContentType.VIDEO,
            skill_category=SkillCategory.ENGLISH_SPEAKING,
            difficulty=DifficultyLevel.BEGINNER,
            duration_minutes=15,
            content_url="https://example.com/video/001"
        )

        assert content.title == "영어 자기소개 연습"
        assert content.is_premium is False
        assert content.difficulty == DifficultyLevel.BEGINNER


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

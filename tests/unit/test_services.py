"""
Unit Tests for Service Layer.

Tests for all business logic services.
"""

import pytest
from datetime import datetime, timedelta, date, time
from decimal import Decimal
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.models.user import User, AuthProvider, SubscriptionTier
from src.core.models.payment import Payment, PaymentStatus, PaymentMethod, Subscription, BillingCycle
from src.core.models.mentor import Mentor, MentorType, SessionType, MentoringSession, SessionStatus
from src.core.exceptions import (
    AuthenticationError, NotFoundError, ValidationError,
    PaymentError, SessionNotAvailableError
)


# =============================================================================
# Auth Service Tests
# =============================================================================

class TestAuthService:
    """Tests for AuthService."""

    @pytest.fixture
    def auth_service(self, tmp_path):
        """Create AuthService with temp directory."""
        from src.services.auth_service import AuthService
        from src.repositories.user_repository import UserRepository

        repo = UserRepository(str(tmp_path))
        return AuthService(repo)

    @pytest.mark.unit
    @pytest.mark.auth
    def test_register_new_user(self, auth_service):
        """Test user registration."""
        user = auth_service.register(
            email="newuser@test.com",
            password="SecurePass123!",
            name="New User"
        )

        assert user is not None
        assert user.email == "newuser@test.com"
        assert user.name == "New User"
        assert user.auth_provider == AuthProvider.EMAIL
        assert user.subscription_tier == SubscriptionTier.FREE

    @pytest.mark.unit
    @pytest.mark.auth
    def test_register_duplicate_email_fails(self, auth_service):
        """Test that duplicate email registration fails."""
        # First registration
        auth_service.register(
            email="duplicate@test.com",
            password="SecurePass123!",
            name="First User"
        )

        # Second registration with same email should fail
        with pytest.raises(ValidationError):
            auth_service.register(
                email="duplicate@test.com",
                password="AnotherPass456!",
                name="Second User"
            )

    @pytest.mark.unit
    @pytest.mark.auth
    def test_authenticate_valid_credentials(self, auth_service):
        """Test authentication with valid credentials."""
        # Register user first
        auth_service.register(
            email="auth@test.com",
            password="ValidPass123!",
            name="Auth User"
        )

        # Authenticate
        user, tokens = auth_service.authenticate(
            email="auth@test.com",
            password="ValidPass123!"
        )

        assert user is not None
        assert user.email == "auth@test.com"
        assert "access_token" in tokens
        assert "refresh_token" in tokens

    @pytest.mark.unit
    @pytest.mark.auth
    def test_authenticate_invalid_password(self, auth_service):
        """Test authentication with invalid password."""
        # Register user
        auth_service.register(
            email="authfail@test.com",
            password="CorrectPass123!",
            name="Auth Fail User"
        )

        # Try wrong password
        with pytest.raises(AuthenticationError):
            auth_service.authenticate(
                email="authfail@test.com",
                password="WrongPassword!"
            )

    @pytest.mark.unit
    @pytest.mark.auth
    def test_create_token_pair(self, auth_service):
        """Test JWT token creation."""
        user = User(
            id="test-user-id",
            email="token@test.com",
            name="Token User",
            password_hash="hash",
            auth_provider=AuthProvider.EMAIL,
            subscription_tier=SubscriptionTier.FREE
        )

        tokens = auth_service.create_token_pair(user)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert len(tokens["access_token"]) > 50  # JWT is long

    @pytest.mark.unit
    @pytest.mark.auth
    def test_verify_valid_token(self, auth_service):
        """Test token verification."""
        # Register and get tokens
        auth_service.register(
            email="verify@test.com",
            password="VerifyPass123!",
            name="Verify User"
        )
        _, tokens = auth_service.authenticate(
            email="verify@test.com",
            password="VerifyPass123!"
        )

        # Verify token
        user = auth_service.verify_access_token(tokens["access_token"])
        assert user.email == "verify@test.com"


# =============================================================================
# User Service Tests
# =============================================================================

class TestUserService:
    """Tests for UserService."""

    @pytest.fixture
    def user_service(self, tmp_path):
        """Create UserService with temp directory."""
        from src.services.user_service import UserService
        from src.repositories.user_repository import UserRepository

        repo = UserRepository(str(tmp_path))
        return UserService(repo)

    @pytest.mark.unit
    def test_create_user(self, user_service):
        """Test user creation."""
        user = user_service.create_user(
            email="create@test.com",
            name="Created User",
            password_hash="$2b$12$test"
        )

        assert user.email == "create@test.com"
        assert user.name == "Created User"

    @pytest.mark.unit
    def test_get_user_by_id(self, user_service):
        """Test getting user by ID."""
        created = user_service.create_user(
            email="getid@test.com",
            name="Get ID User",
            password_hash="$2b$12$test"
        )

        found = user_service.get_user(created.id)
        assert found.id == created.id
        assert found.email == "getid@test.com"

    @pytest.mark.unit
    def test_get_nonexistent_user_raises(self, user_service):
        """Test that getting nonexistent user raises error."""
        with pytest.raises(NotFoundError):
            user_service.get_user("nonexistent-id")

    @pytest.mark.unit
    def test_update_profile(self, user_service):
        """Test profile update."""
        user = user_service.create_user(
            email="update@test.com",
            name="Original Name",
            password_hash="$2b$12$test"
        )

        updated = user_service.update_profile(
            user.id,
            {"name": "Updated Name", "phone": "010-1234-5678"}
        )

        assert updated.name == "Updated Name"
        assert updated.phone == "010-1234-5678"

    @pytest.mark.unit
    def test_upgrade_subscription(self, user_service):
        """Test subscription upgrade."""
        user = user_service.create_user(
            email="upgrade@test.com",
            name="Upgrade User",
            password_hash="$2b$12$test"
        )

        expires = datetime.utcnow() + timedelta(days=30)
        upgraded = user_service.upgrade_subscription(
            user.id,
            SubscriptionTier.PREMIUM,
            expires
        )

        assert upgraded.subscription_tier == SubscriptionTier.PREMIUM
        assert upgraded.subscription_expires_at is not None

    @pytest.mark.unit
    def test_record_interview_session(self, user_service):
        """Test recording interview session."""
        user = user_service.create_user(
            email="interview@test.com",
            name="Interview User",
            password_hash="$2b$12$test"
        )

        user_service.record_interview_session(user.id)
        updated = user_service.get_user(user.id)

        assert updated.interview_sessions_today == 1
        assert updated.total_sessions == 1


# =============================================================================
# Payment Service Tests
# =============================================================================

class TestPaymentService:
    """Tests for PaymentService."""

    @pytest.fixture
    def payment_service(self, tmp_path):
        """Create PaymentService with temp directory."""
        from src.services.payment_service import PaymentService
        from src.services.user_service import UserService
        from src.repositories.payment_repository import PaymentRepository, SubscriptionRepository
        from src.repositories.user_repository import UserRepository

        payment_repo = PaymentRepository(str(tmp_path))
        sub_repo = SubscriptionRepository(str(tmp_path))
        user_repo = UserRepository(str(tmp_path))
        user_service = UserService(user_repo)

        return PaymentService(payment_repo, sub_repo, user_service)

    @pytest.mark.unit
    @pytest.mark.payment
    def test_get_products(self, payment_service):
        """Test getting product catalog."""
        products = payment_service.get_products()

        assert len(products) > 0
        assert "standard_monthly" in products
        assert "premium_monthly" in products

    @pytest.mark.unit
    @pytest.mark.payment
    def test_get_product_by_id(self, payment_service):
        """Test getting specific product."""
        product = payment_service.get_product("standard_monthly")

        assert product.id == "standard_monthly"
        assert product.tier == SubscriptionTier.STANDARD
        assert product.price == Decimal("19900")

    @pytest.mark.unit
    @pytest.mark.payment
    def test_get_nonexistent_product_raises(self, payment_service):
        """Test that nonexistent product raises error."""
        with pytest.raises(NotFoundError):
            payment_service.get_product("nonexistent_product")

    @pytest.mark.unit
    @pytest.mark.payment
    def test_generate_order_id_format(self, payment_service):
        """Test order ID format."""
        order_id = payment_service.generate_order_id()

        assert order_id.startswith("ORD-")
        assert len(order_id) == 28  # ORD-YYYYMMDDHHMMSS-XXXXXXXX

    @pytest.mark.unit
    @pytest.mark.payment
    def test_initiate_payment(self, payment_service):
        """Test payment initiation."""
        from src.core.models.payment import PaymentCreate

        payment_data = PaymentCreate(
            user_id="test-user-001",
            product_id="standard_monthly",
            payment_method=PaymentMethod.KAKAOPAY
        )

        result = payment_service.initiate_payment(payment_data)

        assert result["success"] is True
        assert "payment_id" in result
        assert "order_id" in result
        assert "redirect_url" in result
        assert result["amount"] == 19900.0


# =============================================================================
# Mentor Service Tests
# =============================================================================

class TestMentorService:
    """Tests for MentorService."""

    @pytest.fixture
    def mentor_service(self, tmp_path):
        """Create MentorService with temp directory."""
        from src.services.mentor_service import MentorService
        from src.repositories.mentor_repository import MentorRepository, SessionRepository

        mentor_repo = MentorRepository(str(tmp_path))
        session_repo = SessionRepository(str(tmp_path))

        return MentorService(mentor_repo, session_repo)

    @pytest.fixture
    def sample_mentor_data(self):
        """Sample mentor registration data."""
        from src.core.models.mentor import MentorCreate
        return MentorCreate(
            user_id="mentor-user-001",
            display_name="김멘토",
            mentor_type=MentorType.CURRENT_CREW,
            bio="대한항공 현직 승무원 5년차입니다.",
            airlines=["KE", "OZ"],
            current_airline="KE",
            years_experience=5,
            session_types=[SessionType.MOCK_INTERVIEW],
            hourly_rate=50000,
            available_days=["월", "화", "수"],
            available_times=["10:00", "14:00"]
        )

    @pytest.mark.unit
    @pytest.mark.mentor
    def test_register_mentor(self, mentor_service, sample_mentor_data):
        """Test mentor registration."""
        mentor = mentor_service.register_mentor(sample_mentor_data)

        assert mentor.display_name == "김멘토"
        assert mentor.mentor_type == MentorType.CURRENT_CREW
        assert mentor.is_verified is False  # Not verified yet

    @pytest.mark.unit
    @pytest.mark.mentor
    def test_register_duplicate_mentor_fails(self, mentor_service, sample_mentor_data):
        """Test that duplicate mentor registration fails."""
        mentor_service.register_mentor(sample_mentor_data)

        with pytest.raises(ValidationError):
            mentor_service.register_mentor(sample_mentor_data)

    @pytest.mark.unit
    @pytest.mark.mentor
    def test_search_mentors(self, mentor_service, sample_mentor_data):
        """Test mentor search."""
        mentor_service.register_mentor(sample_mentor_data)

        result = mentor_service.search_mentors(
            mentor_type=MentorType.CURRENT_CREW,
            airline="KE"
        )

        assert result["total"] >= 1
        assert len(result["items"]) >= 1

    @pytest.mark.unit
    @pytest.mark.mentor
    def test_get_available_slots(self, mentor_service, sample_mentor_data):
        """Test getting available time slots."""
        mentor = mentor_service.register_mentor(sample_mentor_data)

        # Get slots for a future Monday
        future_date = date.today() + timedelta(days=(7 - date.today().weekday()))

        slots = mentor_service.get_available_slots(mentor.id, future_date)

        # Should return available times (depending on day)
        assert isinstance(slots, list)

    @pytest.mark.unit
    @pytest.mark.mentor
    def test_verify_mentor(self, mentor_service, sample_mentor_data):
        """Test mentor verification by admin."""
        mentor = mentor_service.register_mentor(sample_mentor_data)

        verified = mentor_service.verify_mentor(mentor.id, "admin-001")

        assert verified.is_verified is True


# =============================================================================
# Job Service Tests
# =============================================================================

class TestJobService:
    """Tests for JobService."""

    @pytest.fixture
    def job_service(self, tmp_path):
        """Create JobService with temp directory."""
        from src.services.job_service import JobService
        from src.repositories.job_repository import JobRepository, JobAlertRepository

        job_repo = JobRepository(str(tmp_path))
        alert_repo = JobAlertRepository(str(tmp_path))

        return JobService(job_repo, alert_repo)

    @pytest.mark.unit
    def test_create_job_posting(self, job_service):
        """Test job posting creation."""
        job_data = {
            "airline_code": "KE",
            "title": "2024 객실승무원 채용",
            "job_type": "cabin_crew",
            "description": "대한항공 객실승무원을 모집합니다.",
            "requirements": ["TOEIC 600+", "신장 162cm+"],
            "start_date": date.today(),
            "end_date": date.today() + timedelta(days=30)
        }

        job = job_service.create_job(job_data)

        assert job.airline_code == "KE"
        assert job.title == "2024 객실승무원 채용"
        assert job.is_open is True

    @pytest.mark.unit
    def test_get_open_jobs(self, job_service):
        """Test getting open job postings."""
        # Create a job
        job_data = {
            "airline_code": "OZ",
            "title": "아시아나 승무원 채용",
            "job_type": "cabin_crew",
            "description": "아시아나항공 채용",
            "requirements": [],
            "start_date": date.today(),
            "end_date": date.today() + timedelta(days=30)
        }
        job_service.create_job(job_data)

        jobs = job_service.get_open_jobs()

        assert len(jobs) >= 1

    @pytest.mark.unit
    def test_airline_names_mapping(self, job_service):
        """Test airline code to name mapping."""
        assert job_service.AIRLINE_NAMES["KE"] == "대한항공"
        assert job_service.AIRLINE_NAMES["OZ"] == "아시아나항공"
        assert job_service.AIRLINE_NAMES["SQ"] == "싱가포르항공"


# =============================================================================
# Recommendation Service Tests
# =============================================================================

class TestRecommendationService:
    """Tests for RecommendationService."""

    @pytest.fixture
    def recommendation_service(self, tmp_path):
        """Create RecommendationService with temp directory."""
        from src.services.recommendation_service import (
            RecommendationService,
            SkillProfileRepository,
            LearningContentRepository
        )

        profile_repo = SkillProfileRepository(str(tmp_path))
        content_repo = LearningContentRepository(str(tmp_path))

        return RecommendationService(profile_repo, content_repo)

    @pytest.mark.unit
    def test_get_or_create_profile(self, recommendation_service):
        """Test skill profile creation."""
        profile = recommendation_service.get_or_create_profile("user-001")

        assert profile.user_id == "user-001"
        assert len(profile.skills) > 0

    @pytest.mark.unit
    def test_update_skill_score(self, recommendation_service):
        """Test updating skill score."""
        from src.core.models.recommendation import SkillCategory

        profile = recommendation_service.update_skill(
            "user-002",
            SkillCategory.ENGLISH_SPEAKING,
            85.0
        )

        assert profile.skills[SkillCategory.ENGLISH_SPEAKING.value].score == 85.0

    @pytest.mark.unit
    def test_get_skill_summary(self, recommendation_service):
        """Test getting skill summary."""
        recommendation_service.get_or_create_profile("user-003")

        summary = recommendation_service.get_skill_summary("user-003")

        assert "readiness_score" in summary
        assert "skills" in summary
        assert "weaknesses" in summary
        assert "strengths" in summary

    @pytest.mark.unit
    def test_skill_weights_sum_to_one(self, recommendation_service):
        """Test that skill weights sum to approximately 1."""
        total = sum(recommendation_service.SKILL_WEIGHTS.values())
        assert 0.99 <= total <= 1.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

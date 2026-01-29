"""
Dependency Injection Container.

Centralizes creation and management of all application dependencies.
"""

from functools import lru_cache
from typing import Optional
import logging

from src.config.settings import Settings, get_settings
from src.repositories.user_repository import UserRepository
from src.repositories.payment_repository import PaymentRepository, SubscriptionRepository
from src.repositories.mentor_repository import MentorRepository, SessionRepository
from src.repositories.job_repository import JobRepository, JobAlertRepository
from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.services.payment_service import PaymentService
from src.services.mentor_service import MentorService
from src.services.job_service import JobService
from src.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)


class Container:
    """
    Dependency Injection Container.

    Provides singleton instances of all application components.
    Uses lazy initialization for efficiency.
    """

    _instance: Optional["Container"] = None

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize container with settings."""
        self._settings = settings or get_settings()
        self._data_dir = str(self._settings.base_dir / self._settings.database.data_dir)

        # Repository instances (lazy)
        self._user_repo: Optional[UserRepository] = None
        self._payment_repo: Optional[PaymentRepository] = None
        self._subscription_repo: Optional[SubscriptionRepository] = None
        self._mentor_repo: Optional[MentorRepository] = None
        self._session_repo: Optional[SessionRepository] = None
        self._job_repo: Optional[JobRepository] = None
        self._job_alert_repo: Optional[JobAlertRepository] = None

        # Service instances (lazy)
        self._auth_service: Optional[AuthService] = None
        self._user_service: Optional[UserService] = None
        self._payment_service: Optional[PaymentService] = None
        self._mentor_service: Optional[MentorService] = None
        self._job_service: Optional[JobService] = None
        self._recommendation_service: Optional[RecommendationService] = None

        logger.info("Container initialized")

    @classmethod
    def get_instance(cls, settings: Optional[Settings] = None) -> "Container":
        """Get or create singleton container instance."""
        if cls._instance is None:
            cls._instance = cls(settings)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset container (useful for testing)."""
        cls._instance = None

    # =====================
    # Settings
    # =====================

    @property
    def settings(self) -> Settings:
        """Get application settings."""
        return self._settings

    # =====================
    # Repositories
    # =====================

    @property
    def user_repository(self) -> UserRepository:
        """Get user repository instance."""
        if self._user_repo is None:
            self._user_repo = UserRepository(self._data_dir)
        return self._user_repo

    @property
    def payment_repository(self) -> PaymentRepository:
        """Get payment repository instance."""
        if self._payment_repo is None:
            self._payment_repo = PaymentRepository(self._data_dir)
        return self._payment_repo

    @property
    def subscription_repository(self) -> SubscriptionRepository:
        """Get subscription repository instance."""
        if self._subscription_repo is None:
            self._subscription_repo = SubscriptionRepository(self._data_dir)
        return self._subscription_repo

    @property
    def mentor_repository(self) -> MentorRepository:
        """Get mentor repository instance."""
        if self._mentor_repo is None:
            self._mentor_repo = MentorRepository(self._data_dir)
        return self._mentor_repo

    @property
    def session_repository(self) -> SessionRepository:
        """Get session repository instance."""
        if self._session_repo is None:
            self._session_repo = SessionRepository(self._data_dir)
        return self._session_repo

    @property
    def job_repository(self) -> JobRepository:
        """Get job repository instance."""
        if self._job_repo is None:
            self._job_repo = JobRepository(self._data_dir)
        return self._job_repo

    @property
    def job_alert_repository(self) -> JobAlertRepository:
        """Get job alert repository instance."""
        if self._job_alert_repo is None:
            self._job_alert_repo = JobAlertRepository(self._data_dir)
        return self._job_alert_repo

    # =====================
    # Services
    # =====================

    @property
    def auth_service(self) -> AuthService:
        """Get auth service instance."""
        if self._auth_service is None:
            self._auth_service = AuthService(self.user_repository)
        return self._auth_service

    @property
    def user_service(self) -> UserService:
        """Get user service instance."""
        if self._user_service is None:
            self._user_service = UserService(self.user_repository)
        return self._user_service

    @property
    def payment_service(self) -> PaymentService:
        """Get payment service instance."""
        if self._payment_service is None:
            self._payment_service = PaymentService(
                self.payment_repository,
                self.subscription_repository,
                self.user_service
            )
        return self._payment_service

    @property
    def mentor_service(self) -> MentorService:
        """Get mentor service instance."""
        if self._mentor_service is None:
            self._mentor_service = MentorService(
                self.mentor_repository,
                self.session_repository
            )
        return self._mentor_service

    @property
    def job_service(self) -> JobService:
        """Get job service instance."""
        if self._job_service is None:
            self._job_service = JobService(
                self.job_repository,
                self.job_alert_repository
            )
        return self._job_service

    @property
    def recommendation_service(self) -> RecommendationService:
        """Get recommendation service instance."""
        if self._recommendation_service is None:
            self._recommendation_service = RecommendationService()
        return self._recommendation_service


# Convenience functions for getting services
@lru_cache()
def get_container() -> Container:
    """Get the container instance."""
    return Container.get_instance()


def get_auth_service() -> AuthService:
    """Get auth service from container."""
    return get_container().auth_service


def get_user_service() -> UserService:
    """Get user service from container."""
    return get_container().user_service


def get_payment_service() -> PaymentService:
    """Get payment service from container."""
    return get_container().payment_service


def get_mentor_service() -> MentorService:
    """Get mentor service from container."""
    return get_container().mentor_service


def get_job_service() -> JobService:
    """Get job service from container."""
    return get_container().job_service


def get_recommendation_service() -> RecommendationService:
    """Get recommendation service from container."""
    return get_container().recommendation_service

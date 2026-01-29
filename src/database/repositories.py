"""
SQLAlchemy Repository Implementation.

Database-backed repositories for all entities.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, TypeVar, Generic, Type
import logging

from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session

from src.database.models import (
    UserModel, PaymentModel, SubscriptionModel,
    MentorModel, SessionModel,
    JobPostingModel, JobAlertModel,
    SkillProfileModel, LearningContentModel
)
from src.core.models.user import User, AuthProvider, SubscriptionTier
from src.core.models.payment import Payment, PaymentStatus, PaymentMethod, Subscription, BillingCycle
from src.core.models.mentor import (
    Mentor, MentorType, MentorStatus, SessionType,
    MentoringSession, SessionStatus
)
from src.core.models.job import JobPosting, JobType, RecruitmentStatus, JobAlert
from src.core.models.recommendation import SkillProfile, LearningContent, SkillCategory

logger = logging.getLogger(__name__)

T = TypeVar("T")
M = TypeVar("M")


# =============================================================================
# Base Repository
# =============================================================================

class SQLAlchemyRepository(Generic[T, M]):
    """
    Generic SQLAlchemy repository.

    Provides CRUD operations for database models.
    """

    def __init__(self, db: Session, model_class: Type[M], domain_class: Type[T]):
        self.db = db
        self.model_class = model_class
        self.domain_class = domain_class

    def _to_domain(self, model: M) -> T:
        """Convert database model to domain model."""
        raise NotImplementedError

    def _to_model(self, domain: T) -> M:
        """Convert domain model to database model."""
        raise NotImplementedError

    def get_by_id(self, id: str) -> Optional[T]:
        """Get entity by ID."""
        model = self.db.query(self.model_class).filter(
            self.model_class.id == id
        ).first()
        return self._to_domain(model) if model else None

    def create(self, entity: T) -> T:
        """Create new entity."""
        model = self._to_model(entity)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def update(self, entity: T) -> T:
        """Update existing entity."""
        model = self.db.query(self.model_class).filter(
            self.model_class.id == entity.id
        ).first()
        if model:
            updated = self._to_model(entity)
            for key, value in updated.__dict__.items():
                if not key.startswith("_"):
                    setattr(model, key, value)
            self.db.commit()
            self.db.refresh(model)
            return self._to_domain(model)
        return entity

    def delete(self, id: str) -> bool:
        """Delete entity by ID."""
        result = self.db.query(self.model_class).filter(
            self.model_class.id == id
        ).delete()
        self.db.commit()
        return result > 0

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        models = self.db.query(self.model_class).offset(skip).limit(limit).all()
        return [self._to_domain(m) for m in models]

    def count(self) -> int:
        """Count all entities."""
        return self.db.query(self.model_class).count()


# =============================================================================
# User Repository
# =============================================================================

class UserSQLRepository(SQLAlchemyRepository[User, UserModel]):
    """User repository with SQLAlchemy."""

    def __init__(self, db: Session):
        super().__init__(db, UserModel, User)

    def _to_domain(self, model: UserModel) -> User:
        """Convert UserModel to User domain object."""
        return User(
            id=model.id,
            email=model.email,
            name=model.name,
            password_hash=model.password_hash,
            phone=model.phone,
            profile_image=model.profile_image,
            auth_provider=AuthProvider(model.auth_provider),
            provider_user_id=model.provider_user_id,
            subscription_tier=SubscriptionTier(model.subscription_tier),
            subscription_expires_at=model.subscription_expires_at,
            target_airlines=model.target_airlines or [],
            notification_email=model.notification_email,
            notification_push=model.notification_push,
            interview_sessions_today=model.interview_sessions_today,
            total_sessions=model.total_sessions,
            last_interview_date=model.last_interview_date,
            is_active=model.is_active,
            email_verified=model.email_verified,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login_at=model.last_login_at
        )

    def _to_model(self, user: User) -> UserModel:
        """Convert User domain object to UserModel."""
        return UserModel(
            id=user.id,
            email=user.email,
            name=user.name,
            password_hash=user.password_hash,
            phone=user.phone,
            profile_image=user.profile_image,
            auth_provider=user.auth_provider.value,
            provider_user_id=user.provider_user_id,
            subscription_tier=user.subscription_tier.value,
            subscription_expires_at=user.subscription_expires_at,
            target_airlines=user.target_airlines,
            notification_email=user.notification_email,
            notification_push=user.notification_push,
            interview_sessions_today=user.interview_sessions_today,
            total_sessions=user.total_sessions,
            last_interview_date=user.last_interview_date,
            is_active=user.is_active,
            email_verified=user.email_verified
        )

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        model = self.db.query(UserModel).filter(
            func.lower(UserModel.email) == email.lower()
        ).first()
        return self._to_domain(model) if model else None

    def get_by_provider(self, provider: AuthProvider, provider_user_id: str) -> Optional[User]:
        """Get user by OAuth provider."""
        model = self.db.query(UserModel).filter(
            and_(
                UserModel.auth_provider == provider.value,
                UserModel.provider_user_id == provider_user_id
            )
        ).first()
        return self._to_domain(model) if model else None

    def search(
        self,
        query: Optional[str] = None,
        tier: Optional[SubscriptionTier] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Search users with filters."""
        q = self.db.query(UserModel)

        if query:
            search = f"%{query}%"
            q = q.filter(or_(
                UserModel.email.ilike(search),
                UserModel.name.ilike(search)
            ))

        if tier:
            q = q.filter(UserModel.subscription_tier == tier.value)

        total = q.count()
        models = q.order_by(desc(UserModel.created_at)) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()

        return {
            "items": [self._to_domain(m) for m in models],
            "total": total,
            "page": page,
            "page_size": page_size
        }


# =============================================================================
# Payment Repository
# =============================================================================

class PaymentSQLRepository(SQLAlchemyRepository[Payment, PaymentModel]):
    """Payment repository with SQLAlchemy."""

    def __init__(self, db: Session):
        super().__init__(db, PaymentModel, Payment)

    def _to_domain(self, model: PaymentModel) -> Payment:
        return Payment(
            id=model.id,
            user_id=model.user_id,
            product_id=model.product_id,
            order_id=model.order_id,
            amount=model.amount,
            currency=model.currency,
            payment_method=PaymentMethod(model.payment_method),
            status=PaymentStatus(model.status),
            provider_transaction_id=model.provider_transaction_id,
            receipt_url=model.receipt_url,
            refunded_amount=model.refunded_amount,
            refund_reason=model.refund_reason,
            refunded_at=model.refunded_at,
            created_at=model.created_at,
            paid_at=model.paid_at,
            failed_at=model.failed_at
        )

    def _to_model(self, payment: Payment) -> PaymentModel:
        return PaymentModel(
            id=payment.id,
            user_id=payment.user_id,
            product_id=payment.product_id,
            order_id=payment.order_id,
            amount=payment.amount,
            currency=payment.currency,
            payment_method=payment.payment_method.value,
            status=payment.status.value,
            provider_transaction_id=payment.provider_transaction_id,
            receipt_url=payment.receipt_url,
            refunded_amount=payment.refunded_amount,
            refund_reason=payment.refund_reason,
            refunded_at=payment.refunded_at,
            paid_at=payment.paid_at,
            failed_at=payment.failed_at
        )

    def get_by_order_id(self, order_id: str) -> Optional[Payment]:
        """Get payment by order ID."""
        model = self.db.query(PaymentModel).filter(
            PaymentModel.order_id == order_id
        ).first()
        return self._to_domain(model) if model else None

    def get_by_user(self, user_id: str) -> List[Payment]:
        """Get all payments for a user."""
        models = self.db.query(PaymentModel).filter(
            PaymentModel.user_id == user_id
        ).order_by(desc(PaymentModel.created_at)).all()
        return [self._to_domain(m) for m in models]

    def get_revenue_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get revenue statistics."""
        result = self.db.query(
            func.sum(PaymentModel.amount).label("total"),
            func.count(PaymentModel.id).label("count")
        ).filter(
            and_(
                PaymentModel.status == PaymentStatus.COMPLETED.value,
                PaymentModel.paid_at >= start_date,
                PaymentModel.paid_at <= end_date
            )
        ).first()

        return {
            "total_revenue": float(result.total or 0),
            "transaction_count": result.count or 0
        }


# =============================================================================
# Mentor Repository
# =============================================================================

class MentorSQLRepository(SQLAlchemyRepository[Mentor, MentorModel]):
    """Mentor repository with SQLAlchemy."""

    def __init__(self, db: Session):
        super().__init__(db, MentorModel, Mentor)

    def _to_domain(self, model: MentorModel) -> Mentor:
        return Mentor(
            id=model.id,
            user_id=model.user_id,
            display_name=model.display_name,
            mentor_type=MentorType(model.mentor_type),
            bio=model.bio,
            profile_image=model.profile_image,
            airlines=model.airlines or [],
            current_airline=model.current_airline,
            years_experience=model.years_experience,
            session_types=[SessionType(s) for s in (model.session_types or [])],
            hourly_rate=model.hourly_rate,
            available_days=model.available_days or [],
            available_times=model.available_times or [],
            rating=model.rating,
            total_sessions=model.total_sessions,
            total_reviews=model.total_reviews,
            is_verified=model.is_verified,
            verified_at=model.verified_at,
            verified_by=model.verified_by,
            status=MentorStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, mentor: Mentor) -> MentorModel:
        return MentorModel(
            id=mentor.id,
            user_id=mentor.user_id,
            display_name=mentor.display_name,
            mentor_type=mentor.mentor_type.value,
            bio=mentor.bio,
            profile_image=mentor.profile_image,
            airlines=mentor.airlines,
            current_airline=mentor.current_airline,
            years_experience=mentor.years_experience,
            session_types=[s.value for s in mentor.session_types],
            hourly_rate=mentor.hourly_rate,
            available_days=mentor.available_days,
            available_times=mentor.available_times,
            rating=mentor.rating,
            total_sessions=mentor.total_sessions,
            total_reviews=mentor.total_reviews,
            is_verified=mentor.is_verified,
            verified_at=mentor.verified_at,
            verified_by=mentor.verified_by,
            status=mentor.status.value if hasattr(mentor.status, 'value') else mentor.status
        )

    def get_by_user_id(self, user_id: str) -> Optional[Mentor]:
        """Get mentor by user ID."""
        model = self.db.query(MentorModel).filter(
            MentorModel.user_id == user_id
        ).first()
        return self._to_domain(model) if model else None

    def search(
        self,
        query: Optional[str] = None,
        mentor_type: Optional[MentorType] = None,
        airline: Optional[str] = None,
        session_type: Optional[SessionType] = None,
        max_rate: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Search mentors with filters."""
        q = self.db.query(MentorModel).filter(
            MentorModel.is_verified == True,
            MentorModel.status == MentorStatus.ACTIVE.value
        )

        if query:
            search = f"%{query}%"
            q = q.filter(or_(
                MentorModel.display_name.ilike(search),
                MentorModel.bio.ilike(search)
            ))

        if mentor_type:
            q = q.filter(MentorModel.mentor_type == mentor_type.value)

        if max_rate:
            q = q.filter(MentorModel.hourly_rate <= max_rate)

        total = q.count()
        models = q.order_by(desc(MentorModel.rating)) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()

        return {
            "items": [self._to_domain(m) for m in models],
            "total": total,
            "page": page,
            "page_size": page_size
        }

    def get_top_rated(self, limit: int = 10) -> List[Mentor]:
        """Get top-rated mentors."""
        models = self.db.query(MentorModel).filter(
            MentorModel.is_verified == True
        ).order_by(desc(MentorModel.rating)).limit(limit).all()
        return [self._to_domain(m) for m in models]


# =============================================================================
# Job Repository
# =============================================================================

class JobSQLRepository(SQLAlchemyRepository[JobPosting, JobPostingModel]):
    """Job posting repository with SQLAlchemy."""

    def __init__(self, db: Session):
        super().__init__(db, JobPostingModel, JobPosting)

    def _to_domain(self, model: JobPostingModel) -> JobPosting:
        return JobPosting(
            id=model.id,
            airline_code=model.airline_code,
            title=model.title,
            job_type=JobType(model.job_type),
            status=RecruitmentStatus(model.status),
            description=model.description,
            requirements=model.requirements or [],
            start_date=model.start_date,
            end_date=model.end_date,
            source_url=model.source_url,
            is_domestic=model.is_domestic,
            content_hash=model.content_hash,
            last_crawled_at=model.last_crawled_at,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, job: JobPosting) -> JobPostingModel:
        return JobPostingModel(
            id=job.id,
            airline_code=job.airline_code,
            title=job.title,
            job_type=job.job_type.value if hasattr(job.job_type, 'value') else job.job_type,
            status=job.status.value if hasattr(job.status, 'value') else job.status,
            description=job.description,
            requirements=job.requirements,
            start_date=job.start_date,
            end_date=job.end_date,
            source_url=job.source_url,
            is_domestic=job.is_domestic,
            content_hash=job.content_hash,
            last_crawled_at=job.last_crawled_at
        )

    def get_open_jobs(self) -> List[JobPosting]:
        """Get all open job postings."""
        today = date.today()
        models = self.db.query(JobPostingModel).filter(
            and_(
                JobPostingModel.status == RecruitmentStatus.OPEN.value,
                or_(
                    JobPostingModel.end_date >= today,
                    JobPostingModel.end_date == None
                )
            )
        ).order_by(desc(JobPostingModel.created_at)).all()
        return [self._to_domain(m) for m in models]

    def get_by_airline(self, airline_code: str) -> List[JobPosting]:
        """Get job postings by airline."""
        models = self.db.query(JobPostingModel).filter(
            JobPostingModel.airline_code == airline_code
        ).order_by(desc(JobPostingModel.created_at)).all()
        return [self._to_domain(m) for m in models]

    def get_upcoming_deadlines(self, days: int = 7) -> List[JobPosting]:
        """Get jobs with deadlines within N days."""
        today = date.today()
        deadline = today + timedelta(days=days)
        models = self.db.query(JobPostingModel).filter(
            and_(
                JobPostingModel.status == RecruitmentStatus.OPEN.value,
                JobPostingModel.end_date >= today,
                JobPostingModel.end_date <= deadline
            )
        ).order_by(JobPostingModel.end_date).all()
        return [self._to_domain(m) for m in models]

    def get_by_content_hash(self, content_hash: str) -> Optional[JobPosting]:
        """Get job by content hash (for deduplication)."""
        model = self.db.query(JobPostingModel).filter(
            JobPostingModel.content_hash == content_hash
        ).first()
        return self._to_domain(model) if model else None

    def get_stats(self) -> Dict[str, Any]:
        """Get job posting statistics."""
        total = self.db.query(JobPostingModel).count()
        open_count = self.db.query(JobPostingModel).filter(
            JobPostingModel.status == RecruitmentStatus.OPEN.value
        ).count()

        by_airline = self.db.query(
            JobPostingModel.airline_code,
            func.count(JobPostingModel.id)
        ).group_by(JobPostingModel.airline_code).all()

        return {
            "total": total,
            "open": open_count,
            "by_airline": {code: count for code, count in by_airline}
        }

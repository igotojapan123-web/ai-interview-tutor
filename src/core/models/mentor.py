"""
Mentor and mentoring session domain models.
"""

from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import Field, field_validator

from src.core.models.base import Entity, BaseModel


class MentorType(str, Enum):
    """Mentor category types."""
    CURRENT_CREW = "current_crew"      # 현직 승무원
    FORMER_CREW = "former_crew"        # 전직 승무원
    RECENT_PASS = "recent_pass"        # 최근 합격자
    INSTRUCTOR = "instructor"          # 전문 강사
    GROUND_STAFF = "ground_staff"      # 지상직


class MentorStatus(str, Enum):
    """Mentor account status."""
    PENDING = "pending"        # 승인 대기
    ACTIVE = "active"          # 활동중
    INACTIVE = "inactive"      # 휴면
    SUSPENDED = "suspended"    # 정지


class SessionType(str, Enum):
    """Mentoring session types."""
    VIDEO_CALL = "video_call"           # 화상 상담
    CHAT = "chat"                       # 채팅 상담
    DOCUMENT_REVIEW = "document_review"  # 서류 첨삭
    MOCK_INTERVIEW = "mock_interview"    # 모의 면접
    CAREER_CONSULT = "career_consult"    # 커리어 상담


class SessionStatus(str, Enum):
    """Mentoring session status."""
    PENDING = "pending"          # 예약 대기
    CONFIRMED = "confirmed"      # 확정
    IN_PROGRESS = "in_progress"  # 진행중
    COMPLETED = "completed"      # 완료
    CANCELLED = "cancelled"      # 취소
    NO_SHOW = "no_show"          # 노쇼


class TimeSlot(BaseModel):
    """Available time slot."""
    day_of_week: int = Field(ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: time
    end_time: time

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v: time, info) -> time:
        """Ensure end_time is after start_time."""
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


class MentorReview(BaseModel):
    """Review for a mentor."""
    id: str
    mentor_id: str
    session_id: str
    reviewer_id: str
    rating: float = Field(ge=1, le=5)
    content: Optional[str] = Field(default=None, max_length=1000)
    is_anonymous: bool = Field(default=False)
    created_at: datetime


class Mentor(Entity):
    """
    Mentor entity.

    Represents a mentor profile with their expertise and availability.
    """

    # User reference
    user_id: str = Field(description="Associated user account ID")

    # Profile
    name: str = Field(min_length=1, max_length=100)
    mentor_type: MentorType
    status: MentorStatus = Field(default=MentorStatus.PENDING)
    bio: str = Field(default="", max_length=2000)
    profile_image: Optional[str] = None

    # Career
    airlines: List[str] = Field(default_factory=list, description="Airline codes worked at")
    current_airline: Optional[str] = Field(default=None, description="Current airline code")
    position: Optional[str] = Field(default=None, description="Current position")
    years_experience: int = Field(default=0, ge=0)
    hire_year: Optional[int] = Field(default=None)

    # Expertise
    specialties: List[str] = Field(default_factory=list, description="Areas of expertise")
    languages: List[str] = Field(default_factory=list, description="Languages spoken")
    session_types: List[SessionType] = Field(default_factory=list)

    # Verification
    verified: bool = Field(default=False)
    verification_documents: List[str] = Field(default_factory=list, description="Uploaded document URLs")
    verified_at: Optional[datetime] = Field(default=None)
    verified_by: Optional[str] = Field(default=None)

    # Pricing
    hourly_rate: Decimal = Field(default=Decimal("30000"), description="Hourly rate in KRW")
    currency: str = Field(default="KRW")

    # Availability
    available_slots: List[TimeSlot] = Field(default_factory=list)
    timezone: str = Field(default="Asia/Seoul")
    max_sessions_per_week: int = Field(default=10)

    # Stats
    total_sessions: int = Field(default=0)
    total_reviews: int = Field(default=0)
    rating: float = Field(default=0.0, ge=0, le=5)

    # Settings
    instant_booking: bool = Field(default=False, description="Allow instant booking without approval")
    min_booking_notice_hours: int = Field(default=24, description="Minimum hours before session")
    cancellation_policy: str = Field(default="24h", description="Cancellation policy")

    @property
    def is_available(self) -> bool:
        """Check if mentor is available for bookings."""
        return self.status == MentorStatus.ACTIVE and self.verified

    def update_rating(self, new_rating: float) -> None:
        """Update rating with new review."""
        if self.total_reviews == 0:
            self.rating = new_rating
        else:
            # Calculate new average
            total_score = self.rating * self.total_reviews
            self.rating = (total_score + new_rating) / (self.total_reviews + 1)
        self.total_reviews += 1
        self.touch()

    def increment_sessions(self) -> None:
        """Increment total sessions count."""
        self.total_sessions += 1
        self.touch()

    def verify(self, verified_by: str) -> None:
        """Mark mentor as verified."""
        self.verified = True
        self.verified_at = datetime.utcnow()
        self.verified_by = verified_by
        self.status = MentorStatus.ACTIVE
        self.touch()


class MentoringSession(Entity):
    """
    Mentoring session entity.

    Represents a scheduled or completed mentoring session.
    """

    # Participants
    mentor_id: str
    mentee_id: str

    # Session details
    session_type: SessionType
    status: SessionStatus = Field(default=SessionStatus.PENDING)

    # Schedule
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int = Field(default=60, ge=15, le=180)
    timezone: str = Field(default="Asia/Seoul")

    # Topic
    topic: str = Field(default="", max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    mentee_questions: List[str] = Field(default_factory=list)

    # Meeting
    meeting_link: Optional[str] = Field(default=None)
    meeting_password: Optional[str] = Field(default=None)
    meeting_provider: Optional[str] = Field(default=None, description="zoom, google_meet, etc.")

    # Payment
    price: Decimal
    currency: str = Field(default="KRW")
    payment_id: Optional[str] = Field(default=None)
    paid: bool = Field(default=False)

    # Notes
    mentor_notes: Optional[str] = Field(default=None, max_length=5000)
    mentee_notes: Optional[str] = Field(default=None, max_length=5000)

    # Review
    rating: Optional[float] = Field(default=None, ge=1, le=5)
    review: Optional[str] = Field(default=None, max_length=2000)
    reviewed_at: Optional[datetime] = Field(default=None)

    # Timestamps
    confirmed_at: Optional[datetime] = Field(default=None)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    cancelled_at: Optional[datetime] = Field(default=None)
    cancelled_by: Optional[str] = Field(default=None)
    cancellation_reason: Optional[str] = Field(default=None)

    @property
    def scheduled_datetime(self) -> datetime:
        """Get combined scheduled datetime."""
        return datetime.combine(self.scheduled_date, self.scheduled_time)

    @property
    def is_upcoming(self) -> bool:
        """Check if session is upcoming."""
        return (
            self.status in [SessionStatus.PENDING, SessionStatus.CONFIRMED]
            and self.scheduled_datetime > datetime.utcnow()
        )

    @property
    def can_cancel(self) -> bool:
        """Check if session can be cancelled."""
        return self.status in [SessionStatus.PENDING, SessionStatus.CONFIRMED]

    def confirm(self, meeting_link: str) -> None:
        """Confirm the session."""
        self.status = SessionStatus.CONFIRMED
        self.meeting_link = meeting_link
        self.confirmed_at = datetime.utcnow()
        self.touch()

    def start(self) -> None:
        """Mark session as started."""
        self.status = SessionStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.touch()

    def complete(self) -> None:
        """Mark session as completed."""
        self.status = SessionStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.touch()

    def cancel(self, cancelled_by: str, reason: str) -> None:
        """Cancel the session."""
        self.status = SessionStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        self.cancelled_by = cancelled_by
        self.cancellation_reason = reason
        self.touch()

    def add_review(self, rating: float, review: str) -> None:
        """Add review for the session."""
        self.rating = rating
        self.review = review
        self.reviewed_at = datetime.utcnow()
        self.touch()


class MentorCreate(BaseModel):
    """DTO for creating a mentor profile."""
    user_id: str
    name: str
    mentor_type: MentorType
    bio: str = ""
    airlines: List[str] = []
    current_airline: Optional[str] = None
    position: Optional[str] = None
    years_experience: int = 0
    hire_year: Optional[int] = None
    specialties: List[str] = []
    languages: List[str] = ["ko"]
    session_types: List[SessionType] = []
    hourly_rate: Decimal = Decimal("30000")


class SessionCreate(BaseModel):
    """DTO for creating a mentoring session."""
    mentor_id: str
    mentee_id: str
    session_type: SessionType
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int = 60
    topic: str = ""
    mentee_questions: List[str] = []

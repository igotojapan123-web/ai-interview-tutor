"""
Mentor service.

Business logic for mentor matching and session management.
"""

from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
import logging
import secrets

from src.core.models.mentor import (
    Mentor, MentorCreate, MentorType, MentorStatus, SessionType,
    MentoringSession, SessionCreate, SessionStatus
)
from src.core.exceptions import (
    NotFoundError, ValidationError, BookingError,
    SessionNotAvailableError, CancellationNotAllowedError,
    AuthorizationError
)
from src.repositories.mentor_repository import MentorRepository, SessionRepository

logger = logging.getLogger(__name__)


class MentorService:
    """Mentor management and matching service."""

    AIRLINE_NAMES = {
        "KE": "대한항공", "OZ": "아시아나항공", "7C": "제주항공",
        "LJ": "진에어", "TW": "티웨이항공", "BX": "에어부산",
        "RS": "에어서울", "EK": "에미레이트항공", "SQ": "싱가포르항공",
        "CX": "캐세이퍼시픽", "QR": "카타르항공", "EY": "에티하드항공"
    }

    def __init__(
        self,
        mentor_repository: Optional[MentorRepository] = None,
        session_repository: Optional[SessionRepository] = None
    ):
        self.mentor_repo = mentor_repository or MentorRepository()
        self.session_repo = session_repository or SessionRepository()

    # =====================
    # Mentor Management
    # =====================

    def register_mentor(self, mentor_data: MentorCreate) -> Mentor:
        """Register a new mentor."""
        # Check if user already has mentor profile
        existing = self.mentor_repo.get_by_user_id(mentor_data.user_id)
        if existing:
            raise ValidationError("User already has a mentor profile")

        mentor = Mentor(**mentor_data.model_dump())
        mentor = self.mentor_repo.create(mentor)
        logger.info(f"New mentor registered: {mentor.id}")
        return mentor

    def get_mentor(self, mentor_id: str) -> Mentor:
        """Get mentor by ID."""
        mentor = self.mentor_repo.get_by_id(mentor_id)
        if not mentor:
            raise NotFoundError("Mentor", mentor_id)
        return mentor

    def update_mentor(self, mentor_id: str, updates: Dict[str, Any]) -> Mentor:
        """Update mentor profile."""
        mentor = self.get_mentor(mentor_id)
        for key, value in updates.items():
            if hasattr(mentor, key) and value is not None:
                setattr(mentor, key, value)
        return self.mentor_repo.update(mentor)

    def verify_mentor(self, mentor_id: str, admin_id: str) -> Mentor:
        """Verify a mentor (admin action)."""
        mentor = self.get_mentor(mentor_id)
        mentor.verify(admin_id)
        logger.info(f"Mentor {mentor_id} verified by {admin_id}")
        return self.mentor_repo.update(mentor)

    def search_mentors(
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
        return self.mentor_repo.search(
            query=query,
            mentor_type=mentor_type,
            airline=airline,
            session_type=session_type,
            max_rate=max_rate,
            page=page,
            page_size=page_size
        )

    def get_recommended_mentors(self, user_id: str, limit: int = 5) -> List[Mentor]:
        """Get recommended mentors for a user."""
        # In production, use ML-based recommendation
        # For now, return top-rated mentors
        return self.mentor_repo.get_top_rated(limit)

    def calculate_match_score(self, mentor: Mentor, criteria: Dict) -> float:
        """Calculate mentor-mentee match score."""
        score = 0.0

        # Airline match (40%)
        target_airlines = criteria.get("airlines", [])
        if target_airlines:
            matched = set(mentor.airlines) & set(target_airlines)
            if matched:
                score += 40 * (len(matched) / len(target_airlines))
            if mentor.current_airline in target_airlines:
                score += 10

        # Session type match (20%)
        if criteria.get("session_type") in mentor.session_types:
            score += 20

        # Rating (20%)
        score += mentor.rating * 4

        # Experience (10%)
        score += min(10, mentor.years_experience)

        return min(100, score)

    # =====================
    # Session Management
    # =====================

    def get_available_slots(self, mentor_id: str, target_date: date) -> List[str]:
        """Get available time slots for a mentor on a date."""
        mentor = self.get_mentor(mentor_id)

        # Check if date is valid
        if target_date < date.today():
            return []

        # Check day of week
        day_of_week = target_date.weekday()
        day_names = ["월", "화", "수", "목", "금", "토", "일"]
        if day_names[day_of_week] not in mentor.available_days:
            return []

        # Get existing sessions
        existing = self.session_repo.get_sessions_on_date(mentor_id, target_date)
        booked_times = {s.scheduled_time.strftime("%H:%M") for s in existing
                       if s.status in [SessionStatus.PENDING, SessionStatus.CONFIRMED]}

        # Return available times
        return [t for t in mentor.available_times if t not in booked_times]

    def create_session(self, session_data: SessionCreate) -> MentoringSession:
        """Create a mentoring session."""
        mentor = self.get_mentor(session_data.mentor_id)

        # Validate availability
        available = self.get_available_slots(mentor.id, session_data.scheduled_date)
        time_str = session_data.scheduled_time.strftime("%H:%M")
        if time_str not in available:
            raise SessionNotAvailableError(mentor.id, time_str)

        # Create session
        session = MentoringSession(
            **session_data.model_dump(),
            price=mentor.hourly_rate,
            status=SessionStatus.PENDING
        )

        session = self.session_repo.create(session)
        logger.info(f"Session created: {session.id}")
        return session

    def confirm_session(self, session_id: str, mentor_id: str) -> MentoringSession:
        """Confirm a session (mentor action)."""
        session = self.get_session(session_id)

        if session.mentor_id != mentor_id:
            raise AuthorizationError("Not authorized to confirm this session")

        if session.status != SessionStatus.PENDING:
            raise BookingError("Session is not pending")

        # Generate meeting link
        meeting_link = f"https://meet.flyreadylab.com/{session_id}"
        session.confirm(meeting_link)

        logger.info(f"Session {session_id} confirmed")
        return self.session_repo.update(session)

    def cancel_session(
        self,
        session_id: str,
        cancelled_by: str,
        reason: str
    ) -> MentoringSession:
        """Cancel a session."""
        session = self.get_session(session_id)

        if not session.can_cancel:
            raise CancellationNotAllowedError("Session cannot be cancelled")

        # Check cancellation policy (24h before)
        if session.scheduled_datetime - datetime.utcnow() < timedelta(hours=24):
            if cancelled_by == session.mentee_id:
                raise CancellationNotAllowedError(
                    "Cannot cancel within 24 hours of session"
                )

        session.cancel(cancelled_by, reason)
        logger.info(f"Session {session_id} cancelled by {cancelled_by}")
        return self.session_repo.update(session)

    def complete_session(self, session_id: str) -> MentoringSession:
        """Mark session as completed."""
        session = self.get_session(session_id)

        if session.status != SessionStatus.CONFIRMED:
            raise BookingError("Session must be confirmed before completing")

        session.complete()

        # Update mentor stats
        mentor = self.get_mentor(session.mentor_id)
        mentor.increment_sessions()
        self.mentor_repo.update(mentor)

        logger.info(f"Session {session_id} completed")
        return self.session_repo.update(session)

    def add_review(
        self,
        session_id: str,
        mentee_id: str,
        rating: float,
        review: str
    ) -> MentoringSession:
        """Add review for a completed session."""
        session = self.get_session(session_id)

        if session.mentee_id != mentee_id:
            raise AuthorizationError("Not authorized to review this session")

        if session.status != SessionStatus.COMPLETED:
            raise BookingError("Can only review completed sessions")

        if session.rating is not None:
            raise BookingError("Session already reviewed")

        session.add_review(rating, review)

        # Update mentor rating
        mentor = self.get_mentor(session.mentor_id)
        mentor.update_rating(rating)
        self.mentor_repo.update(mentor)

        logger.info(f"Review added for session {session_id}")
        return self.session_repo.update(session)

    def get_session(self, session_id: str) -> MentoringSession:
        """Get session by ID."""
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundError("Session", session_id)
        return session

    def get_user_sessions(
        self,
        user_id: str,
        is_mentor: bool = False,
        status: Optional[SessionStatus] = None
    ) -> List[MentoringSession]:
        """Get sessions for a user."""
        if is_mentor:
            return self.session_repo.get_by_mentor(user_id, status)
        return self.session_repo.get_by_mentee(user_id, status)

    def get_upcoming_sessions(self, user_id: str, is_mentor: bool = False) -> List[MentoringSession]:
        """Get upcoming sessions for a user."""
        return self.session_repo.get_upcoming_sessions(user_id, is_mentor)

    def get_stats(self) -> Dict[str, Any]:
        """Get mentor and session statistics."""
        return {
            "mentors": self.mentor_repo.get_stats(),
            "sessions": self.session_repo.get_stats()
        }

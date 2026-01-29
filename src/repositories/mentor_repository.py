"""
Mentor repository implementation.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List

from src.repositories.base import JSONRepository
from src.core.models.mentor import (
    Mentor, MentorType, MentorStatus, SessionType,
    MentoringSession, SessionStatus
)


class MentorRepository(JSONRepository[Mentor]):
    """Repository for Mentor entities."""

    def __init__(self, data_dir: str = "data"):
        super().__init__(
            data_dir=data_dir,
            filename="mentors.json",
            entity_class=Mentor
        )

    def get_by_user_id(self, user_id: str) -> Optional[Mentor]:
        """Get mentor profile by user ID."""
        return self.find_one(user_id=user_id)

    def get_active_mentors(self) -> List[Mentor]:
        """Get all active mentors."""
        return self.find(status=MentorStatus.ACTIVE.value, verified=True)

    def get_by_type(self, mentor_type: MentorType) -> List[Mentor]:
        """Get mentors by type."""
        return self.find(mentor_type=mentor_type.value, status=MentorStatus.ACTIVE.value)

    def get_by_airline(self, airline_code: str) -> List[Mentor]:
        """Get mentors who worked at a specific airline."""
        mentors = self.get_active_mentors()
        return [m for m in mentors if airline_code in m.airlines]

    def get_by_specialty(self, specialty: str) -> List[Mentor]:
        """Get mentors with a specific specialty."""
        mentors = self.get_active_mentors()
        return [m for m in mentors if specialty in m.specialties]

    def get_pending_verification(self) -> List[Mentor]:
        """Get mentors pending verification."""
        return self.find(status=MentorStatus.PENDING.value)

    def search(
        self,
        query: Optional[str] = None,
        mentor_type: Optional[MentorType] = None,
        airline: Optional[str] = None,
        session_type: Optional[SessionType] = None,
        max_rate: Optional[int] = None,
        min_rating: Optional[float] = None,
        sort_by: str = "rating",
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """
        Search mentors with filters.

        Args:
            query: Search in name, bio, specialties
            mentor_type: Filter by mentor type
            airline: Filter by airline
            session_type: Filter by supported session type
            max_rate: Maximum hourly rate
            min_rating: Minimum rating
            sort_by: Sort field (rating, sessions, rate)
            page: Page number
            page_size: Items per page

        Returns:
            Paginated results
        """
        mentors = self.get_active_mentors()

        # Apply filters
        if mentor_type:
            mentors = [m for m in mentors if m.mentor_type == mentor_type]

        if airline:
            mentors = [m for m in mentors if airline in m.airlines]

        if session_type:
            mentors = [m for m in mentors if session_type in m.session_types]

        if max_rate:
            mentors = [m for m in mentors if m.hourly_rate <= max_rate]

        if min_rating:
            mentors = [m for m in mentors if m.rating >= min_rating]

        if query:
            query_lower = query.lower()
            mentors = [
                m for m in mentors
                if query_lower in m.name.lower()
                or query_lower in m.bio.lower()
                or any(query_lower in s.lower() for s in m.specialties)
            ]

        # Sort
        if sort_by == "rating":
            mentors.sort(key=lambda m: (m.rating, m.total_reviews), reverse=True)
        elif sort_by == "sessions":
            mentors.sort(key=lambda m: m.total_sessions, reverse=True)
        elif sort_by == "rate_low":
            mentors.sort(key=lambda m: m.hourly_rate)
        elif sort_by == "rate_high":
            mentors.sort(key=lambda m: m.hourly_rate, reverse=True)

        # Paginate
        total = len(mentors)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "items": mentors[start:end],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    def get_top_rated(self, limit: int = 10) -> List[Mentor]:
        """Get top-rated mentors."""
        mentors = self.get_active_mentors()
        mentors.sort(key=lambda m: (m.rating, m.total_reviews), reverse=True)
        return mentors[:limit]

    def get_stats(self) -> dict:
        """Get mentor statistics."""
        mentors = self.get_all()

        active = [m for m in mentors if m.status == MentorStatus.ACTIVE]
        verified = [m for m in mentors if m.verified]

        by_type = {}
        for m in active:
            mtype = m.mentor_type.value if hasattr(m.mentor_type, "value") else m.mentor_type
            by_type[mtype] = by_type.get(mtype, 0) + 1

        total_sessions = sum(m.total_sessions for m in active)
        avg_rating = sum(m.rating for m in active) / len(active) if active else 0

        return {
            "total": len(mentors),
            "active": len(active),
            "verified": len(verified),
            "pending": len([m for m in mentors if m.status == MentorStatus.PENDING]),
            "by_type": by_type,
            "total_sessions": total_sessions,
            "average_rating": round(avg_rating, 2)
        }


class SessionRepository(JSONRepository[MentoringSession]):
    """Repository for MentoringSession entities."""

    def __init__(self, data_dir: str = "data"):
        super().__init__(
            data_dir=data_dir,
            filename="mentoring_sessions.json",
            entity_class=MentoringSession
        )

    def get_by_mentor(self, mentor_id: str, status: Optional[SessionStatus] = None) -> List[MentoringSession]:
        """Get sessions for a mentor."""
        criteria = {"mentor_id": mentor_id}
        if status:
            criteria["status"] = status.value
        return self.find(**criteria)

    def get_by_mentee(self, mentee_id: str, status: Optional[SessionStatus] = None) -> List[MentoringSession]:
        """Get sessions for a mentee."""
        criteria = {"mentee_id": mentee_id}
        if status:
            criteria["status"] = status.value
        return self.find(**criteria)

    def get_upcoming_sessions(self, user_id: str, is_mentor: bool = False) -> List[MentoringSession]:
        """Get upcoming sessions for a user."""
        field = "mentor_id" if is_mentor else "mentee_id"
        sessions = self.find(**{field: user_id})

        now = datetime.utcnow()
        return [
            s for s in sessions
            if s.status in [SessionStatus.PENDING, SessionStatus.CONFIRMED]
            and s.scheduled_datetime > now
        ]

    def get_sessions_on_date(self, mentor_id: str, session_date: date) -> List[MentoringSession]:
        """Get sessions for a mentor on a specific date."""
        sessions = self.get_by_mentor(mentor_id)
        return [s for s in sessions if s.scheduled_date == session_date]

    def get_pending_confirmation(self, mentor_id: str) -> List[MentoringSession]:
        """Get sessions pending confirmation."""
        return self.find(mentor_id=mentor_id, status=SessionStatus.PENDING.value)

    def get_completed_sessions(self, user_id: str, days: int = 30) -> List[MentoringSession]:
        """Get completed sessions in the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        sessions = self.find(status=SessionStatus.COMPLETED.value)

        return [
            s for s in sessions
            if (s.mentor_id == user_id or s.mentee_id == user_id)
            and s.completed_at
            and s.completed_at >= cutoff
        ]

    def get_unreviewed_sessions(self, mentee_id: str) -> List[MentoringSession]:
        """Get completed sessions that haven't been reviewed."""
        sessions = self.find(mentee_id=mentee_id, status=SessionStatus.COMPLETED.value)
        return [s for s in sessions if s.rating is None]

    def get_stats(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> dict:
        """Get session statistics."""
        sessions = self.get_all()

        if start_date:
            sessions = [s for s in sessions if s.created_at >= start_date]
        if end_date:
            sessions = [s for s in sessions if s.created_at <= end_date]

        total = len(sessions)
        by_status = {}
        by_type = {}
        total_revenue = sum(s.price for s in sessions if s.paid)

        for s in sessions:
            status = s.status.value if hasattr(s.status, "value") else s.status
            by_status[status] = by_status.get(status, 0) + 1

            stype = s.session_type.value if hasattr(s.session_type, "value") else s.session_type
            by_type[stype] = by_type.get(stype, 0) + 1

        completed = [s for s in sessions if s.status == SessionStatus.COMPLETED]
        avg_rating = sum(s.rating for s in completed if s.rating) / len(completed) if completed else 0

        return {
            "total": total,
            "by_status": by_status,
            "by_type": by_type,
            "completed": by_status.get(SessionStatus.COMPLETED.value, 0),
            "cancelled": by_status.get(SessionStatus.CANCELLED.value, 0),
            "total_revenue": float(total_revenue),
            "average_rating": round(avg_rating, 2)
        }

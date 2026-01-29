"""
Mentor endpoints.

Handles mentor profiles and session management.
"""

from typing import Optional, List
from datetime import date, time
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from src.api.v1.deps import (
    get_current_user,
    get_current_active_user,
    get_premium_user,
    get_admin_user,
    mentor_service
)
from src.services.mentor_service import MentorService
from src.core.models.mentor import (
    MentorCreate, SessionCreate, MentorType, SessionType, SessionStatus
)
from src.core.models.user import User
from src.core.exceptions import (
    NotFoundError, ValidationError, BookingError,
    SessionNotAvailableError, CancellationNotAllowedError, AuthorizationError
)

router = APIRouter()


# =====================
# Request/Response Schemas
# =====================

class MentorResponse(BaseModel):
    id: str
    user_id: str
    display_name: str
    mentor_type: str
    bio: str
    airlines: List[str]
    current_airline: Optional[str]
    years_experience: int
    session_types: List[str]
    hourly_rate: int
    rating: float
    total_sessions: int
    is_verified: bool
    profile_image: Optional[str]


class MentorCreateRequest(BaseModel):
    display_name: str
    mentor_type: str
    bio: str
    airlines: List[str]
    current_airline: Optional[str] = None
    years_experience: int
    session_types: List[str]
    hourly_rate: int
    available_days: List[str]
    available_times: List[str]


class MentorSearchResponse(BaseModel):
    items: List[MentorResponse]
    total: int
    page: int
    page_size: int


class SessionResponse(BaseModel):
    id: str
    mentor_id: str
    mentee_id: str
    session_type: str
    scheduled_date: str
    scheduled_time: str
    duration_minutes: int
    price: int
    status: str
    meeting_link: Optional[str]
    notes: Optional[str]


class SessionCreateRequest(BaseModel):
    mentor_id: str
    session_type: str
    scheduled_date: str  # YYYY-MM-DD
    scheduled_time: str  # HH:MM
    duration_minutes: int = 60
    notes: Optional[str] = None


class SessionCancelRequest(BaseModel):
    reason: str


class ReviewRequest(BaseModel):
    rating: float
    review: str


# =====================
# Mentor Endpoints
# =====================

@router.get("/", response_model=MentorSearchResponse)
async def search_mentors(
    query: Optional[str] = None,
    mentor_type: Optional[str] = None,
    airline: Optional[str] = None,
    session_type: Optional[str] = None,
    max_rate: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    mentor_svc: MentorService = Depends(mentor_service)
):
    """Search mentors with filters."""
    mentor_type_enum = MentorType(mentor_type) if mentor_type else None
    session_type_enum = SessionType(session_type) if session_type else None

    result = mentor_svc.search_mentors(
        query=query,
        mentor_type=mentor_type_enum,
        airline=airline,
        session_type=session_type_enum,
        max_rate=max_rate,
        page=page,
        page_size=page_size
    )

    items = [
        MentorResponse(
            id=m.id,
            user_id=m.user_id,
            display_name=m.display_name,
            mentor_type=m.mentor_type.value,
            bio=m.bio,
            airlines=m.airlines,
            current_airline=m.current_airline,
            years_experience=m.years_experience,
            session_types=[s.value for s in m.session_types],
            hourly_rate=m.hourly_rate,
            rating=m.rating,
            total_sessions=m.total_sessions,
            is_verified=m.is_verified,
            profile_image=m.profile_image
        )
        for m in result["items"]
    ]

    return MentorSearchResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"]
    )


@router.get("/recommended")
async def get_recommended_mentors(
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
    mentor_svc: MentorService = Depends(mentor_service)
):
    """Get recommended mentors for current user."""
    mentors = mentor_svc.get_recommended_mentors(current_user.id, limit)
    return [
        MentorResponse(
            id=m.id,
            user_id=m.user_id,
            display_name=m.display_name,
            mentor_type=m.mentor_type.value,
            bio=m.bio,
            airlines=m.airlines,
            current_airline=m.current_airline,
            years_experience=m.years_experience,
            session_types=[s.value for s in m.session_types],
            hourly_rate=m.hourly_rate,
            rating=m.rating,
            total_sessions=m.total_sessions,
            is_verified=m.is_verified,
            profile_image=m.profile_image
        )
        for m in mentors
    ]


@router.get("/{mentor_id}", response_model=MentorResponse)
async def get_mentor(
    mentor_id: str,
    mentor_svc: MentorService = Depends(mentor_service)
):
    """Get mentor details."""
    try:
        mentor = mentor_svc.get_mentor(mentor_id)
        return MentorResponse(
            id=mentor.id,
            user_id=mentor.user_id,
            display_name=mentor.display_name,
            mentor_type=mentor.mentor_type.value,
            bio=mentor.bio,
            airlines=mentor.airlines,
            current_airline=mentor.current_airline,
            years_experience=mentor.years_experience,
            session_types=[s.value for s in mentor.session_types],
            hourly_rate=mentor.hourly_rate,
            rating=mentor.rating,
            total_sessions=mentor.total_sessions,
            is_verified=mentor.is_verified,
            profile_image=mentor.profile_image
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor not found"
        )


@router.get("/{mentor_id}/availability")
async def get_mentor_availability(
    mentor_id: str,
    target_date: str = Query(..., description="Date in YYYY-MM-DD format"),
    mentor_svc: MentorService = Depends(mentor_service)
):
    """Get available time slots for a mentor on a specific date."""
    try:
        parsed_date = date.fromisoformat(target_date)
        slots = mentor_svc.get_available_slots(mentor_id, parsed_date)
        return {"date": target_date, "available_slots": slots}
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor not found"
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format"
        )


@router.post("/register", response_model=MentorResponse)
async def register_as_mentor(
    request: MentorCreateRequest,
    current_user: User = Depends(get_current_active_user),
    mentor_svc: MentorService = Depends(mentor_service)
):
    """Register current user as a mentor."""
    try:
        mentor_data = MentorCreate(
            user_id=current_user.id,
            display_name=request.display_name,
            mentor_type=MentorType(request.mentor_type),
            bio=request.bio,
            airlines=request.airlines,
            current_airline=request.current_airline,
            years_experience=request.years_experience,
            session_types=[SessionType(s) for s in request.session_types],
            hourly_rate=request.hourly_rate,
            available_days=request.available_days,
            available_times=request.available_times
        )
        mentor = mentor_svc.register_mentor(mentor_data)
        return MentorResponse(
            id=mentor.id,
            user_id=mentor.user_id,
            display_name=mentor.display_name,
            mentor_type=mentor.mentor_type.value,
            bio=mentor.bio,
            airlines=mentor.airlines,
            current_airline=mentor.current_airline,
            years_experience=mentor.years_experience,
            session_types=[s.value for s in mentor.session_types],
            hourly_rate=mentor.hourly_rate,
            rating=mentor.rating,
            total_sessions=mentor.total_sessions,
            is_verified=mentor.is_verified,
            profile_image=mentor.profile_image
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# =====================
# Session Endpoints
# =====================

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    current_user: User = Depends(get_premium_user),
    mentor_svc: MentorService = Depends(mentor_service)
):
    """Book a mentoring session (premium users only)."""
    try:
        session_data = SessionCreate(
            mentor_id=request.mentor_id,
            mentee_id=current_user.id,
            session_type=SessionType(request.session_type),
            scheduled_date=date.fromisoformat(request.scheduled_date),
            scheduled_time=time.fromisoformat(request.scheduled_time),
            duration_minutes=request.duration_minutes,
            notes=request.notes
        )
        session = mentor_svc.create_session(session_data)
        return SessionResponse(
            id=session.id,
            mentor_id=session.mentor_id,
            mentee_id=session.mentee_id,
            session_type=session.session_type.value,
            scheduled_date=session.scheduled_date.isoformat(),
            scheduled_time=session.scheduled_time.isoformat(),
            duration_minutes=session.duration_minutes,
            price=session.price,
            status=session.status.value,
            meeting_link=session.meeting_link,
            notes=session.notes
        )
    except (NotFoundError, SessionNotAvailableError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/sessions/my")
async def get_my_sessions(
    is_mentor: bool = Query(False),
    session_status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    mentor_svc: MentorService = Depends(mentor_service)
):
    """Get current user's sessions."""
    status_enum = SessionStatus(session_status) if session_status else None
    sessions = mentor_svc.get_user_sessions(current_user.id, is_mentor, status_enum)
    return [
        SessionResponse(
            id=s.id,
            mentor_id=s.mentor_id,
            mentee_id=s.mentee_id,
            session_type=s.session_type.value,
            scheduled_date=s.scheduled_date.isoformat(),
            scheduled_time=s.scheduled_time.isoformat(),
            duration_minutes=s.duration_minutes,
            price=s.price,
            status=s.status.value,
            meeting_link=s.meeting_link,
            notes=s.notes
        )
        for s in sessions
    ]


@router.get("/sessions/upcoming")
async def get_upcoming_sessions(
    is_mentor: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    mentor_svc: MentorService = Depends(mentor_service)
):
    """Get upcoming sessions."""
    sessions = mentor_svc.get_upcoming_sessions(current_user.id, is_mentor)
    return [
        SessionResponse(
            id=s.id,
            mentor_id=s.mentor_id,
            mentee_id=s.mentee_id,
            session_type=s.session_type.value,
            scheduled_date=s.scheduled_date.isoformat(),
            scheduled_time=s.scheduled_time.isoformat(),
            duration_minutes=s.duration_minutes,
            price=s.price,
            status=s.status.value,
            meeting_link=s.meeting_link,
            notes=s.notes
        )
        for s in sessions
    ]


@router.post("/sessions/{session_id}/confirm")
async def confirm_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    mentor_svc: MentorService = Depends(mentor_service)
):
    """Confirm a session (mentor action)."""
    try:
        # Get mentor profile for current user
        mentor = mentor_svc.mentor_repo.get_by_user_id(current_user.id)
        if not mentor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a mentor"
            )
        session = mentor_svc.confirm_session(session_id, mentor.id)
        return {"message": "Session confirmed", "meeting_link": session.meeting_link}
    except (AuthorizationError, BookingError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/sessions/{session_id}/cancel")
async def cancel_session(
    session_id: str,
    request: SessionCancelRequest,
    current_user: User = Depends(get_current_active_user),
    mentor_svc: MentorService = Depends(mentor_service)
):
    """Cancel a session."""
    try:
        session = mentor_svc.cancel_session(session_id, current_user.id, request.reason)
        return {"message": "Session cancelled"}
    except CancellationNotAllowedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/sessions/{session_id}/complete")
async def complete_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    mentor_svc: MentorService = Depends(mentor_service)
):
    """Mark session as completed (mentor action)."""
    try:
        session = mentor_svc.complete_session(session_id)
        return {"message": "Session completed"}
    except BookingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/sessions/{session_id}/review")
async def review_session(
    session_id: str,
    request: ReviewRequest,
    current_user: User = Depends(get_current_active_user),
    mentor_svc: MentorService = Depends(mentor_service)
):
    """Add review for a completed session."""
    try:
        if not 1 <= request.rating <= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating must be between 1 and 5"
            )
        session = mentor_svc.add_review(
            session_id,
            current_user.id,
            request.rating,
            request.review
        )
        return {"message": "Review added"}
    except (AuthorizationError, BookingError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# =====================
# Admin Endpoints
# =====================

@router.post("/{mentor_id}/verify")
async def verify_mentor(
    mentor_id: str,
    admin_user: User = Depends(get_admin_user),
    mentor_svc: MentorService = Depends(mentor_service)
):
    """Verify a mentor (admin only)."""
    try:
        mentor = mentor_svc.verify_mentor(mentor_id, admin_user.id)
        return {"message": "Mentor verified"}
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor not found"
        )


@router.get("/stats")
async def get_mentor_stats(
    admin_user: User = Depends(get_admin_user),
    mentor_svc: MentorService = Depends(mentor_service)
):
    """Get mentor and session statistics (admin only)."""
    return mentor_svc.get_stats()

"""
Real-time Events.

Event types and structures for WebSocket communication.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class EventType(str, Enum):
    """Types of real-time events."""

    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    HEARTBEAT = "heartbeat"

    # Notification events
    NOTIFICATION = "notification"
    NOTIFICATION_READ = "notification_read"

    # Chat events
    CHAT_MESSAGE = "chat_message"
    CHAT_TYPING = "chat_typing"
    CHAT_READ = "chat_read"

    # Session events
    SESSION_REMINDER = "session_reminder"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    SESSION_CANCELLED = "session_cancelled"

    # Job events
    JOB_NEW = "job_new"
    JOB_DEADLINE = "job_deadline"
    JOB_CLOSED = "job_closed"

    # User events
    USER_SUBSCRIPTION_CHANGED = "user_subscription_changed"
    USER_ACHIEVEMENT = "user_achievement"

    # System events
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    SYSTEM_MAINTENANCE = "system_maintenance"

    # Interview events
    INTERVIEW_FEEDBACK_READY = "interview_feedback_ready"
    INTERVIEW_PROGRESS = "interview_progress"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Event(BaseModel):
    """Base event structure for WebSocket communication."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)

    # Targeting
    user_id: Optional[str] = None  # Specific user
    room_id: Optional[str] = None  # Room/channel
    broadcast: bool = False  # Send to all

    class Config:
        use_enum_values = True


class Notification(BaseModel):
    """Notification structure."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    message: str
    type: EventType
    priority: NotificationPriority = NotificationPriority.NORMAL

    # Optional fields
    action_url: Optional[str] = None
    image_url: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)

    # Status
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class ChatMessage(BaseModel):
    """Chat message structure."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room_id: str
    sender_id: str
    sender_name: str

    content: str
    message_type: str = "text"  # text, image, file, system

    # Optional fields
    reply_to: Optional[str] = None
    attachments: list = Field(default_factory=list)

    # Status
    is_read: bool = False
    read_by: list = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TypingIndicator(BaseModel):
    """Typing indicator for chat."""

    room_id: str
    user_id: str
    user_name: str
    is_typing: bool = True


# =============================================================================
# Event Factory Functions
# =============================================================================

def create_notification_event(
    user_id: str,
    title: str,
    message: str,
    notification_type: EventType = EventType.NOTIFICATION,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    action_url: Optional[str] = None,
    data: Dict[str, Any] = None
) -> Event:
    """Create a notification event."""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        priority=priority,
        action_url=action_url,
        data=data or {}
    )

    return Event(
        type=EventType.NOTIFICATION,
        user_id=user_id,
        data=notification.model_dump()
    )


def create_chat_message_event(
    room_id: str,
    sender_id: str,
    sender_name: str,
    content: str,
    message_type: str = "text"
) -> Event:
    """Create a chat message event."""
    message = ChatMessage(
        room_id=room_id,
        sender_id=sender_id,
        sender_name=sender_name,
        content=content,
        message_type=message_type
    )

    return Event(
        type=EventType.CHAT_MESSAGE,
        room_id=room_id,
        data=message.model_dump()
    )


def create_session_reminder_event(
    user_id: str,
    session_id: str,
    mentor_name: str,
    scheduled_time: datetime,
    minutes_until: int
) -> Event:
    """Create a session reminder event."""
    return Event(
        type=EventType.SESSION_REMINDER,
        user_id=user_id,
        data={
            "session_id": session_id,
            "mentor_name": mentor_name,
            "scheduled_time": scheduled_time.isoformat(),
            "minutes_until": minutes_until,
            "message": f"{mentor_name} 멘토와의 세션이 {minutes_until}분 후에 시작됩니다."
        }
    )


def create_job_alert_event(
    user_id: str,
    job_id: str,
    airline_name: str,
    job_title: str,
    deadline: Optional[datetime] = None,
    is_new: bool = True
) -> Event:
    """Create a job alert event."""
    event_type = EventType.JOB_NEW if is_new else EventType.JOB_DEADLINE

    message = f"{airline_name}에서 새로운 채용공고가 등록되었습니다." if is_new else \
              f"{airline_name} 채용 마감이 임박했습니다."

    return Event(
        type=event_type,
        user_id=user_id,
        data={
            "job_id": job_id,
            "airline_name": airline_name,
            "job_title": job_title,
            "deadline": deadline.isoformat() if deadline else None,
            "message": message
        }
    )


def create_interview_feedback_event(
    user_id: str,
    interview_id: str,
    overall_score: float,
    feedback_summary: str
) -> Event:
    """Create an interview feedback ready event."""
    return Event(
        type=EventType.INTERVIEW_FEEDBACK_READY,
        user_id=user_id,
        data={
            "interview_id": interview_id,
            "overall_score": overall_score,
            "feedback_summary": feedback_summary,
            "message": f"면접 연습 결과가 준비되었습니다. (점수: {overall_score:.0f}점)"
        }
    )

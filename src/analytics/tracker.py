"""
Analytics Tracker.

Event tracking and user behavior analytics.
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Analytics event types."""
    # Page events
    PAGE_VIEW = "page_view"
    PAGE_EXIT = "page_exit"

    # User events
    USER_SIGNUP = "user_signup"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_PROFILE_UPDATE = "user_profile_update"

    # Interview events
    INTERVIEW_START = "interview_start"
    INTERVIEW_COMPLETE = "interview_complete"
    INTERVIEW_ABANDON = "interview_abandon"
    QUESTION_ANSWERED = "question_answered"
    FEEDBACK_VIEWED = "feedback_viewed"

    # Learning events
    PRACTICE_START = "practice_start"
    PRACTICE_COMPLETE = "practice_complete"
    SKILL_IMPROVED = "skill_improved"
    BADGE_EARNED = "badge_earned"

    # Content events
    VIDEO_PLAY = "video_play"
    VIDEO_COMPLETE = "video_complete"
    RESOURCE_DOWNLOAD = "resource_download"

    # Mentor events
    MENTOR_VIEW = "mentor_view"
    SESSION_BOOKED = "session_booked"
    SESSION_COMPLETED = "session_completed"

    # Payment events
    CHECKOUT_START = "checkout_start"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    SUBSCRIPTION_START = "subscription_start"
    SUBSCRIPTION_CANCEL = "subscription_cancel"

    # Search events
    SEARCH = "search"
    SEARCH_CLICK = "search_click"

    # Error events
    ERROR = "error"
    API_ERROR = "api_error"

    # Custom event
    CUSTOM = "custom"


@dataclass
class AnalyticsEvent:
    """Analytics event data."""
    event_type: EventType
    user_id: Optional[str]
    session_id: Optional[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    properties: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "properties": self.properties,
            "context": self.context,
        }


class AnalyticsTracker:
    """
    Analytics event tracker.

    Features:
    - Event tracking with batching
    - User session tracking
    - Funnel analysis
    - Real-time metrics
    """

    def __init__(self, batch_size: int = 100, flush_interval: int = 60):
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._event_queue: List[AnalyticsEvent] = []
        self._handlers: List[Callable] = []
        self._running = False

        # In-memory aggregations
        self._event_counts: Dict[str, int] = defaultdict(int)
        self._daily_active_users: Dict[str, set] = defaultdict(set)
        self._session_data: Dict[str, Dict] = {}
        self._funnels: Dict[str, List[str]] = {}

    async def start(self) -> None:
        """Start the background flush task."""
        if self._running:
            return

        self._running = True
        asyncio.create_task(self._flush_loop())
        logger.info("Analytics tracker started")

    async def stop(self) -> None:
        """Stop the tracker and flush remaining events."""
        self._running = False
        await self._flush()
        logger.info("Analytics tracker stopped")

    def add_handler(self, handler: Callable) -> None:
        """Add event handler (e.g., database writer, external service)."""
        self._handlers.append(handler)

    async def track(
        self,
        event_type: EventType,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track an analytics event.

        Args:
            event_type: Type of event
            user_id: User identifier
            session_id: Session identifier
            properties: Event-specific properties
            context: Additional context (device, location, etc.)
        """
        event = AnalyticsEvent(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            properties=properties or {},
            context=context or {}
        )

        self._event_queue.append(event)

        # Update aggregations
        self._event_counts[event_type.value] += 1

        if user_id:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            self._daily_active_users[today].add(user_id)

        # Flush if batch size reached
        if len(self._event_queue) >= self._batch_size:
            await self._flush()

    async def track_page_view(
        self,
        page: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        referrer: Optional[str] = None,
        **extra
    ) -> None:
        """Track a page view."""
        await self.track(
            EventType.PAGE_VIEW,
            user_id=user_id,
            session_id=session_id,
            properties={
                "page": page,
                "referrer": referrer,
                **extra
            }
        )

    async def track_interview(
        self,
        action: str,
        user_id: str,
        session_id: str,
        interview_type: str,
        score: Optional[float] = None,
        **extra
    ) -> None:
        """Track interview-related events."""
        event_map = {
            "start": EventType.INTERVIEW_START,
            "complete": EventType.INTERVIEW_COMPLETE,
            "abandon": EventType.INTERVIEW_ABANDON,
        }

        event_type = event_map.get(action, EventType.CUSTOM)

        await self.track(
            event_type,
            user_id=user_id,
            session_id=session_id,
            properties={
                "interview_type": interview_type,
                "score": score,
                **extra
            }
        )

    async def track_conversion(
        self,
        funnel: str,
        step: str,
        user_id: str,
        **extra
    ) -> None:
        """Track funnel conversion step."""
        await self.track(
            EventType.CUSTOM,
            user_id=user_id,
            properties={
                "funnel": funnel,
                "step": step,
                **extra
            }
        )

    # =========================================================================
    # Session Management
    # =========================================================================

    def start_session(self, session_id: str, user_id: Optional[str] = None) -> None:
        """Start tracking a session."""
        self._session_data[session_id] = {
            "user_id": user_id,
            "start_time": datetime.utcnow(),
            "events": [],
            "page_views": 0,
        }

    def end_session(self, session_id: str) -> Optional[Dict]:
        """End a session and return session data."""
        if session_id not in self._session_data:
            return None

        data = self._session_data.pop(session_id)
        data["end_time"] = datetime.utcnow()
        data["duration"] = (data["end_time"] - data["start_time"]).total_seconds()

        return data

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data."""
        return self._session_data.get(session_id)

    # =========================================================================
    # Funnel Analysis
    # =========================================================================

    def define_funnel(self, name: str, steps: List[str]) -> None:
        """Define a conversion funnel."""
        self._funnels[name] = steps

    def get_funnel_metrics(self, name: str) -> Dict[str, Any]:
        """Get funnel conversion metrics."""
        if name not in self._funnels:
            return {}

        steps = self._funnels[name]
        # This would query the database in production
        # For now, return placeholder
        return {
            "name": name,
            "steps": steps,
            "conversion_rates": {},
            "drop_off_rates": {},
        }

    # =========================================================================
    # Real-time Metrics
    # =========================================================================

    def get_event_counts(self) -> Dict[str, int]:
        """Get event counts."""
        return dict(self._event_counts)

    def get_daily_active_users(self, date: Optional[str] = None) -> int:
        """Get DAU count."""
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        return len(self._daily_active_users.get(date, set()))

    def get_active_sessions(self) -> int:
        """Get count of active sessions."""
        return len(self._session_data)

    def get_realtime_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics summary."""
        today = datetime.utcnow().strftime("%Y-%m-%d")

        return {
            "active_sessions": self.get_active_sessions(),
            "daily_active_users": self.get_daily_active_users(today),
            "events_today": sum(
                count for event, count in self._event_counts.items()
            ),
            "top_events": sorted(
                self._event_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
        }

    # =========================================================================
    # Internal Methods
    # =========================================================================

    async def _flush_loop(self) -> None:
        """Background task to flush events periodically."""
        while self._running:
            await asyncio.sleep(self._flush_interval)
            await self._flush()

    async def _flush(self) -> None:
        """Flush queued events to handlers."""
        if not self._event_queue:
            return

        events = self._event_queue.copy()
        self._event_queue.clear()

        for handler in self._handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(events)
                else:
                    handler(events)
            except Exception as e:
                logger.error(f"Analytics handler error: {e}")

        logger.debug(f"Flushed {len(events)} analytics events")


# Singleton instance
analytics_tracker = AnalyticsTracker()


# =========================================================================
# Decorator Functions
# =========================================================================

def track_event(
    event_type: EventType,
    properties_extractor: Optional[Callable] = None
):
    """
    Decorator to track function execution as an event.

    Args:
        event_type: Event type to track
        properties_extractor: Function to extract properties from args/kwargs

    Usage:
        @track_event(EventType.INTERVIEW_COMPLETE)
        async def complete_interview(user_id: str, score: float):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # Extract properties
            properties = {}
            if properties_extractor:
                properties = properties_extractor(*args, **kwargs, result=result)

            # Track event
            user_id = kwargs.get("user_id")
            session_id = kwargs.get("session_id")

            await analytics_tracker.track(
                event_type,
                user_id=user_id,
                session_id=session_id,
                properties=properties
            )

            return result

        return wrapper
    return decorator


def track_page_view(page: str):
    """
    Decorator to track page views.

    Usage:
        @track_page_view("/dashboard")
        async def dashboard_page(user_id: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_id = kwargs.get("user_id")
            session_id = kwargs.get("session_id")

            await analytics_tracker.track_page_view(
                page=page,
                user_id=user_id,
                session_id=session_id
            )

            return await func(*args, **kwargs)

        return wrapper
    return decorator

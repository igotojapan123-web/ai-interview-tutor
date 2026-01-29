"""
Notification Service.

Handles sending notifications via multiple channels.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel

from src.realtime.events import (
    Event, EventType, Notification, NotificationPriority,
    create_notification_event, create_session_reminder_event,
    create_job_alert_event, create_interview_feedback_event
)
from src.realtime.websocket import ws_manager

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    WEBSOCKET = "websocket"
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"


class NotificationService:
    """
    Multi-channel notification service.

    Handles sending notifications through various channels
    including WebSocket, email, and push notifications.
    """

    def __init__(self):
        self._notification_queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._is_running = False

    async def start(self) -> None:
        """Start the notification service."""
        if not self._is_running:
            self._is_running = True
            self._worker_task = asyncio.create_task(self._process_queue())
            logger.info("Notification service started")

    async def stop(self) -> None:
        """Stop the notification service."""
        self._is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            self._worker_task = None
        logger.info("Notification service stopped")

    async def _process_queue(self) -> None:
        """Process notification queue."""
        while self._is_running:
            try:
                notification = await asyncio.wait_for(
                    self._notification_queue.get(),
                    timeout=1.0
                )
                await self._deliver_notification(notification)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing notification: {e}")

    async def _deliver_notification(self, notification: Dict[str, Any]) -> None:
        """Deliver notification through appropriate channels."""
        channels = notification.get("channels", [NotificationChannel.WEBSOCKET])
        event = notification.get("event")
        user_id = notification.get("user_id")

        for channel in channels:
            try:
                if channel == NotificationChannel.WEBSOCKET:
                    await self._send_websocket(user_id, event)
                elif channel == NotificationChannel.EMAIL:
                    await self._send_email(notification)
                elif channel == NotificationChannel.PUSH:
                    await self._send_push(notification)
            except Exception as e:
                logger.error(f"Failed to deliver via {channel}: {e}")

    async def _send_websocket(self, user_id: str, event: Event) -> None:
        """Send notification via WebSocket."""
        await ws_manager.notify_user(user_id, event)

    async def _send_email(self, notification: Dict[str, Any]) -> None:
        """Send notification via email."""
        # In production, integrate with email service
        logger.info(f"Email notification queued for {notification.get('user_id')}")
        # Example: await email_service.send(...)

    async def _send_push(self, notification: Dict[str, Any]) -> None:
        """Send notification via push."""
        # In production, integrate with FCM/APNS
        logger.info(f"Push notification queued for {notification.get('user_id')}")
        # Example: await push_service.send(...)

    # ==========================================================================
    # High-level notification methods
    # ==========================================================================

    async def send_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: EventType = EventType.NOTIFICATION,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: List[NotificationChannel] = None,
        action_url: Optional[str] = None,
        data: Dict[str, Any] = None
    ) -> None:
        """
        Send a notification to a user.

        Args:
            user_id: Target user ID
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            channels: Delivery channels
            action_url: Optional action URL
            data: Additional data
        """
        channels = channels or [NotificationChannel.WEBSOCKET]

        event = create_notification_event(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            action_url=action_url,
            data=data
        )

        await self._notification_queue.put({
            "user_id": user_id,
            "event": event,
            "channels": channels,
            "title": title,
            "message": message
        })

    async def send_session_reminder(
        self,
        user_id: str,
        session_id: str,
        mentor_name: str,
        scheduled_time: datetime,
        minutes_until: int
    ) -> None:
        """Send session reminder notification."""
        event = create_session_reminder_event(
            user_id=user_id,
            session_id=session_id,
            mentor_name=mentor_name,
            scheduled_time=scheduled_time,
            minutes_until=minutes_until
        )

        # Urgent for close reminders
        channels = [NotificationChannel.WEBSOCKET]
        if minutes_until <= 15:
            channels.append(NotificationChannel.PUSH)

        await self._notification_queue.put({
            "user_id": user_id,
            "event": event,
            "channels": channels,
            "title": "세션 알림",
            "message": f"{mentor_name} 멘토와의 세션이 {minutes_until}분 후에 시작됩니다."
        })

    async def send_job_alert(
        self,
        user_id: str,
        job_id: str,
        airline_name: str,
        job_title: str,
        deadline: Optional[datetime] = None,
        is_new: bool = True
    ) -> None:
        """Send job alert notification."""
        event = create_job_alert_event(
            user_id=user_id,
            job_id=job_id,
            airline_name=airline_name,
            job_title=job_title,
            deadline=deadline,
            is_new=is_new
        )

        channels = [NotificationChannel.WEBSOCKET, NotificationChannel.EMAIL]

        title = "새 채용공고" if is_new else "마감 임박"
        message = f"{airline_name}: {job_title}"

        await self._notification_queue.put({
            "user_id": user_id,
            "event": event,
            "channels": channels,
            "title": title,
            "message": message
        })

    async def send_interview_feedback(
        self,
        user_id: str,
        interview_id: str,
        overall_score: float,
        feedback_summary: str
    ) -> None:
        """Send interview feedback notification."""
        event = create_interview_feedback_event(
            user_id=user_id,
            interview_id=interview_id,
            overall_score=overall_score,
            feedback_summary=feedback_summary
        )

        await self._notification_queue.put({
            "user_id": user_id,
            "event": event,
            "channels": [NotificationChannel.WEBSOCKET],
            "title": "면접 결과",
            "message": f"면접 연습 결과가 준비되었습니다. (점수: {overall_score:.0f}점)"
        })

    async def broadcast_announcement(
        self,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> None:
        """Broadcast system announcement to all users."""
        event = Event(
            type=EventType.SYSTEM_ANNOUNCEMENT,
            broadcast=True,
            data={
                "title": title,
                "message": message,
                "priority": priority.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        await ws_manager.broadcast(event)
        logger.info(f"System announcement broadcast: {title}")


# Singleton instance
notification_service = NotificationService()

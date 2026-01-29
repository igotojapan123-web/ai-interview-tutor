"""
Real-time Communication Package.

WebSocket-based real-time features.
"""

from src.realtime.websocket import WebSocketManager, ConnectionManager
from src.realtime.events import EventType, Event
from src.realtime.notifications import NotificationService

__all__ = [
    "WebSocketManager",
    "ConnectionManager",
    "EventType",
    "Event",
    "NotificationService"
]

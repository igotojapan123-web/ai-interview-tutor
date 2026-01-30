# websocket_handler.py
# WebSocket 실시간 통신 핸들러 (Streamlit 호환)

import json
import asyncio
import threading
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from collections import defaultdict

try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# ============================================================
# 이벤트 타입
# ============================================================

class EventType:
    """WebSocket 이벤트 유형"""
    MESSAGE = "message"
    NOTIFICATION = "notification"
    PROGRESS = "progress"
    UPDATE = "update"
    ERROR = "error"
    SYSTEM = "system"


@dataclass
class WebSocketMessage:
    """WebSocket 메시지"""
    event_type: str
    data: Any
    channel: str = "default"
    timestamp: str = None
    sender_id: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event_type,
            "data": self.data,
            "channel": self.channel,
            "timestamp": self.timestamp,
            "sender_id": self.sender_id
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


# ============================================================
# Pub/Sub 시스템 (Streamlit 호환)
# ============================================================

class PubSubHub:
    """Publish/Subscribe 허브"""

    def __init__(self):
        self._lock = threading.Lock()
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._message_history: Dict[str, List[WebSocketMessage]] = defaultdict(list)
        self._max_history = 100

    def subscribe(self, channel: str, callback: Callable) -> None:
        """채널 구독"""
        with self._lock:
            if callback not in self._subscribers[channel]:
                self._subscribers[channel].append(callback)
                logger.debug(f"Subscribed to channel: {channel}")

    def unsubscribe(self, channel: str, callback: Callable) -> None:
        """구독 해제"""
        with self._lock:
            if callback in self._subscribers[channel]:
                self._subscribers[channel].remove(callback)
                logger.debug(f"Unsubscribed from channel: {channel}")

    def publish(self, channel: str, message: WebSocketMessage) -> int:
        """메시지 발행"""
        with self._lock:
            # 히스토리 저장
            self._message_history[channel].append(message)
            if len(self._message_history[channel]) > self._max_history:
                self._message_history[channel] = self._message_history[channel][-self._max_history:]

            # 구독자에게 전달
            subscribers = self._subscribers.get(channel, [])
            for callback in subscribers:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Subscriber callback error: {e}")

            logger.debug(f"Published to {channel}: {len(subscribers)} subscribers")
            return len(subscribers)

    def get_history(self, channel: str, limit: int = 50) -> List[WebSocketMessage]:
        """채널 메시지 히스토리"""
        with self._lock:
            return self._message_history[channel][-limit:]

    def get_channels(self) -> List[str]:
        """활성 채널 목록"""
        with self._lock:
            return list(self._subscribers.keys())

    def get_subscriber_count(self, channel: str) -> int:
        """채널 구독자 수"""
        with self._lock:
            return len(self._subscribers.get(channel, []))


# 전역 Pub/Sub 허브
pubsub = PubSubHub()


# ============================================================
# 실시간 알림 시스템
# ============================================================

class RealtimeNotifier:
    """실시간 알림 관리"""

    def __init__(self):
        self._user_channels: Dict[str, str] = {}  # {user_id: channel_id}

    def register_user(self, user_id: str) -> str:
        """사용자 채널 등록"""
        channel = f"user_{user_id}"
        self._user_channels[user_id] = channel
        return channel

    def notify_user(self, user_id: str, notification: Dict[str, Any]) -> bool:
        """사용자에게 알림"""
        channel = self._user_channels.get(user_id)
        if not channel:
            return False

        message = WebSocketMessage(
            event_type=EventType.NOTIFICATION,
            data=notification,
            channel=channel
        )
        pubsub.publish(channel, message)
        return True

    def broadcast(self, notification: Dict[str, Any], channel: str = "broadcast") -> int:
        """전체 브로드캐스트"""
        message = WebSocketMessage(
            event_type=EventType.NOTIFICATION,
            data=notification,
            channel=channel
        )
        return pubsub.publish(channel, message)

    def send_progress(self, user_id: str, task: str, progress: float, message: str = "") -> bool:
        """진행 상황 알림"""
        channel = self._user_channels.get(user_id)
        if not channel:
            return False

        msg = WebSocketMessage(
            event_type=EventType.PROGRESS,
            data={
                "task": task,
                "progress": progress,
                "message": message
            },
            channel=channel
        )
        pubsub.publish(channel, msg)
        return True


# 전역 알림 시스템
notifier = RealtimeNotifier()


# ============================================================
# Streamlit 통합
# ============================================================

class StreamlitRealtimeManager:
    """Streamlit 실시간 업데이트 관리"""

    def __init__(self):
        self._session_callbacks: Dict[str, List[Callable]] = defaultdict(list)

    def setup_session(self, session_id: str) -> None:
        """세션 설정"""
        import streamlit as st

        if "realtime_messages" not in st.session_state:
            st.session_state.realtime_messages = []

        # 사용자 채널 구독
        channel = f"user_{session_id}"

        def on_message(msg: WebSocketMessage):
            st.session_state.realtime_messages.append(msg.to_dict())

        pubsub.subscribe(channel, on_message)
        pubsub.subscribe("broadcast", on_message)

    def get_messages(self) -> List[Dict[str, Any]]:
        """새 메시지 가져오기"""
        import streamlit as st

        messages = st.session_state.get("realtime_messages", [])
        st.session_state.realtime_messages = []
        return messages

    def render_notifications(self) -> None:
        """알림 렌더링"""
        import streamlit as st

        messages = self.get_messages()
        for msg in messages:
            if msg["event"] == EventType.NOTIFICATION:
                st.toast(msg["data"].get("message", ""), icon=msg["data"].get("icon", "info"))
            elif msg["event"] == EventType.PROGRESS:
                st.progress(msg["data"]["progress"], text=msg["data"].get("message", ""))


# 전역 Streamlit 관리자
st_realtime = StreamlitRealtimeManager()


# ============================================================
# 간편 함수
# ============================================================

def notify(user_id: str, message: str, icon: str = "info") -> bool:
    """사용자에게 알림"""
    return notifier.notify_user(user_id, {"message": message, "icon": icon})


def broadcast(message: str, icon: str = "info") -> int:
    """전체 브로드캐스트"""
    return notifier.broadcast({"message": message, "icon": icon})


def send_progress(user_id: str, task: str, progress: float, message: str = "") -> bool:
    """진행 상황 알림"""
    return notifier.send_progress(user_id, task, progress, message)


def subscribe(channel: str, callback: Callable) -> None:
    """채널 구독"""
    pubsub.subscribe(channel, callback)


def publish(channel: str, data: Any) -> int:
    """채널에 발행"""
    message = WebSocketMessage(EventType.MESSAGE, data, channel)
    return pubsub.publish(channel, message)


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=== WebSocket Handler ===")

    received = []

    def on_message(msg):
        received.append(msg)
        print(f"Received: {msg.event_type} - {msg.data}")

    # 구독
    pubsub.subscribe("test", on_message)

    # 발행
    publish("test", {"hello": "world"})
    broadcast("시스템 알림 테스트")

    print(f"\nReceived {len(received)} messages")
    print("\nReady!")

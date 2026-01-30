# notification_webhook.py
# Slack/Discord 웹훅 알림 시스템

import os
import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import threading

try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# ============================================================
# 설정
# ============================================================

# 환경변수에서 웹훅 URL 로드
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# 알림 쿨다운 (같은 에러 반복 알림 방지)
NOTIFICATION_COOLDOWN_SECONDS = 300  # 5분


class NotificationType(Enum):
    """알림 유형"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"
    CRITICAL = "critical"


# 알림 색상 매핑
COLORS = {
    NotificationType.ERROR: "#ef4444",      # 빨간색
    NotificationType.WARNING: "#f59e0b",    # 주황색
    NotificationType.INFO: "#3b82f6",       # 파란색
    NotificationType.SUCCESS: "#10b981",    # 초록색
    NotificationType.CRITICAL: "#dc2626",   # 진한 빨간색
}

ICONS = {
    NotificationType.ERROR: "🔴",
    NotificationType.WARNING: "🟡",
    NotificationType.INFO: "🔵",
    NotificationType.SUCCESS: "🟢",
    NotificationType.CRITICAL: "🚨",
}


# ============================================================
# 알림 쿨다운 관리
# ============================================================

_notification_cache: Dict[str, float] = {}


def _should_send_notification(key: str) -> bool:
    """알림 쿨다운 체크"""
    now = datetime.now().timestamp()
    last_sent = _notification_cache.get(key, 0)

    if now - last_sent < NOTIFICATION_COOLDOWN_SECONDS:
        return False

    _notification_cache[key] = now
    return True


# ============================================================
# Slack 알림
# ============================================================

def send_slack_notification(
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.INFO,
    fields: List[Dict[str, str]] = None,
    webhook_url: str = None
) -> bool:
    """
    Slack 웹훅으로 알림 전송

    Args:
        title: 알림 제목
        message: 알림 내용
        notification_type: 알림 유형
        fields: 추가 필드 [{"title": "...", "value": "...", "short": True}]
        webhook_url: 웹훅 URL (기본: 환경변수)

    Returns:
        성공 여부
    """
    url = webhook_url or SLACK_WEBHOOK_URL
    if not url:
        logger.warning("Slack 웹훅 URL이 설정되지 않음")
        return False

    # 쿨다운 체크
    cache_key = f"slack:{title}:{message[:50]}"
    if not _should_send_notification(cache_key):
        logger.debug(f"Slack 알림 쿨다운 중: {title}")
        return False

    try:
        color = COLORS.get(notification_type, "#808080")
        icon = ICONS.get(notification_type, "ℹ️")

        # Slack 메시지 포맷
        attachment = {
            "color": color,
            "title": f"{icon} {title}",
            "text": message,
            "footer": "FlyReady Lab",
            "ts": int(datetime.now().timestamp())
        }

        if fields:
            attachment["fields"] = fields

        payload = {
            "attachments": [attachment]
        }

        response = requests.post(
            url,
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            logger.info(f"Slack 알림 전송 성공: {title}")
            return True
        else:
            logger.error(f"Slack 알림 실패: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Slack 알림 오류: {e}")
        return False


# ============================================================
# Discord 알림
# ============================================================

def send_discord_notification(
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.INFO,
    fields: List[Dict[str, str]] = None,
    webhook_url: str = None
) -> bool:
    """
    Discord 웹훅으로 알림 전송

    Args:
        title: 알림 제목
        message: 알림 내용
        notification_type: 알림 유형
        fields: 추가 필드 [{"name": "...", "value": "...", "inline": True}]
        webhook_url: 웹훅 URL (기본: 환경변수)

    Returns:
        성공 여부
    """
    url = webhook_url or DISCORD_WEBHOOK_URL
    if not url:
        logger.warning("Discord 웹훅 URL이 설정되지 않음")
        return False

    # 쿨다운 체크
    cache_key = f"discord:{title}:{message[:50]}"
    if not _should_send_notification(cache_key):
        logger.debug(f"Discord 알림 쿨다운 중: {title}")
        return False

    try:
        color = int(COLORS.get(notification_type, "#808080").replace("#", ""), 16)
        icon = ICONS.get(notification_type, "ℹ️")

        # Discord Embed 포맷
        embed = {
            "title": f"{icon} {title}",
            "description": message,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "FlyReady Lab"
            }
        }

        if fields:
            embed["fields"] = [
                {"name": f["name"], "value": f["value"], "inline": f.get("inline", False)}
                for f in fields
            ]

        payload = {
            "embeds": [embed]
        }

        response = requests.post(
            url,
            json=payload,
            timeout=10
        )

        if response.status_code in [200, 204]:
            logger.info(f"Discord 알림 전송 성공: {title}")
            return True
        else:
            logger.error(f"Discord 알림 실패: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Discord 알림 오류: {e}")
        return False


# ============================================================
# 통합 알림 함수
# ============================================================

def send_notification(
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.INFO,
    fields: List[Dict[str, str]] = None,
    channels: List[str] = None
) -> Dict[str, bool]:
    """
    모든 채널로 알림 전송

    Args:
        title: 알림 제목
        message: 알림 내용
        notification_type: 알림 유형
        fields: 추가 필드
        channels: 전송할 채널 목록 ["slack", "discord"] (기본: 전체)

    Returns:
        각 채널별 성공 여부
    """
    if channels is None:
        channels = ["slack", "discord"]

    results = {}

    for channel in channels:
        if channel == "slack":
            results["slack"] = send_slack_notification(
                title, message, notification_type, fields
            )
        elif channel == "discord":
            # Discord 필드 포맷 변환
            discord_fields = None
            if fields:
                discord_fields = [
                    {"name": f.get("title", ""), "value": f.get("value", ""), "inline": f.get("short", False)}
                    for f in fields
                ]
            results["discord"] = send_discord_notification(
                title, message, notification_type, discord_fields
            )

    return results


def send_notification_async(
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.INFO,
    fields: List[Dict[str, str]] = None
) -> None:
    """비동기 알림 전송 (백그라운드)"""
    def _send():
        send_notification(title, message, notification_type, fields)

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()


# ============================================================
# 에러 알림 헬퍼
# ============================================================

def notify_error(
    error: Exception,
    page: str = None,
    user_id: str = None,
    additional_info: Dict[str, Any] = None
) -> None:
    """
    에러 발생 시 알림 전송

    Args:
        error: 발생한 예외
        page: 페이지 이름
        user_id: 사용자 ID
        additional_info: 추가 정보
    """
    title = f"에러 발생: {type(error).__name__}"
    message = str(error)

    fields = []
    if page:
        fields.append({"title": "페이지", "value": page, "short": True})
    if user_id:
        fields.append({"title": "사용자", "value": user_id[:8] + "...", "short": True})
    fields.append({"title": "시간", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "short": True})

    if additional_info:
        for key, value in additional_info.items():
            fields.append({"title": key, "value": str(value)[:100], "short": True})

    send_notification_async(title, message, NotificationType.ERROR, fields)


def notify_critical(
    title: str,
    message: str,
    additional_info: Dict[str, Any] = None
) -> None:
    """긴급 알림 전송"""
    fields = []
    fields.append({"title": "시간", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "short": True})

    if additional_info:
        for key, value in additional_info.items():
            fields.append({"title": key, "value": str(value)[:100], "short": True})

    # CRITICAL은 즉시 전송 (비동기 아님)
    send_notification(title, message, NotificationType.CRITICAL, fields)


def notify_daily_summary(
    total_users: int,
    total_errors: int,
    api_usage: Dict[str, int] = None
) -> None:
    """일일 요약 알림"""
    title = "📊 일일 요약 리포트"
    message = f"오늘 하루 FlyReady Lab 현황입니다."

    fields = [
        {"title": "총 사용자", "value": f"{total_users}명", "short": True},
        {"title": "에러 발생", "value": f"{total_errors}건", "short": True},
    ]

    if api_usage:
        for api_name, count in api_usage.items():
            fields.append({"title": f"{api_name} API", "value": f"{count}회", "short": True})

    send_notification_async(title, message, NotificationType.INFO, fields)


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=== Notification Webhook ===")
    print(f"Slack URL configured: {bool(SLACK_WEBHOOK_URL)}")
    print(f"Discord URL configured: {bool(DISCORD_WEBHOOK_URL)}")
    print("\nFunctions available:")
    print("  - send_slack_notification()")
    print("  - send_discord_notification()")
    print("  - send_notification() - 통합")
    print("  - send_notification_async() - 비동기")
    print("  - notify_error() - 에러 알림")
    print("  - notify_critical() - 긴급 알림")
    print("  - notify_daily_summary() - 일일 요약")
    print("\nReady!")

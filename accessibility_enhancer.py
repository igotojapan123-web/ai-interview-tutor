# -*- coding: utf-8 -*-
"""
accessibility_enhancer.py
E. 접근성 (-) 해결 모듈

해결하는 문제:
22. 모바일 불편 → 모바일 최적화 + 반응형 CSS
23. 알림 없음 → 푸시 알림 (학습 리마인더, 채용공고)
24. 오프라인 불가 → 오프라인 캐싱 (기본 학습 자료)
25. 텍스트 폴백 숨겨짐 → 음성 실패 시 자동 텍스트 모드 전환
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime, timedelta
import json


# ============================================================
# 22. 모바일 최적화
# ============================================================

class DeviceType(Enum):
    """디바이스 유형"""
    DESKTOP = "desktop"
    TABLET = "tablet"
    MOBILE = "mobile"


@dataclass
class ResponsiveSettings:
    """반응형 설정"""
    device_type: DeviceType
    breakpoint: int  # px
    font_scale: float
    button_size: str  # "small", "medium", "large"
    layout: str  # "horizontal", "vertical", "stacked"
    touch_friendly: bool


class ResponsiveLayoutManager:
    """반응형 레이아웃 관리자"""

    # 디바이스별 설정
    DEVICE_SETTINGS = {
        DeviceType.DESKTOP: ResponsiveSettings(
            DeviceType.DESKTOP, 1024, 1.0, "medium", "horizontal", False
        ),
        DeviceType.TABLET: ResponsiveSettings(
            DeviceType.TABLET, 768, 1.1, "medium", "horizontal", True
        ),
        DeviceType.MOBILE: ResponsiveSettings(
            DeviceType.MOBILE, 480, 1.2, "large", "vertical", True
        ),
    }

    def __init__(self):
        pass

    def detect_device(self, screen_width: int) -> DeviceType:
        """디바이스 감지"""
        if screen_width >= 1024:
            return DeviceType.DESKTOP
        elif screen_width >= 768:
            return DeviceType.TABLET
        else:
            return DeviceType.MOBILE

    def get_settings(self, device_type: DeviceType) -> ResponsiveSettings:
        """디바이스별 설정"""
        return self.DEVICE_SETTINGS.get(device_type, self.DEVICE_SETTINGS[DeviceType.DESKTOP])

    def get_responsive_css(self) -> str:
        """반응형 CSS 생성"""
        return """
/* 모바일 최적화 CSS */

/* 기본 (모바일 우선) */
.stButton > button {
    width: 100%;
    min-height: 48px;
    font-size: 16px;
    margin: 8px 0;
}

.stTextInput > div > div > input {
    font-size: 16px;
    min-height: 48px;
}

.stTextArea > div > div > textarea {
    font-size: 16px;
}

/* 탭 버튼 */
.stTabs [data-baseweb="tab-list"] {
    flex-wrap: wrap;
    gap: 4px;
}

.stTabs [data-baseweb="tab"] {
    flex: 1;
    min-width: 100px;
    justify-content: center;
}

/* 카드 레이아웃 */
.mobile-card {
    padding: 16px;
    margin: 8px 0;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* 하단 고정 버튼 */
.mobile-fixed-bottom {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 16px;
    background: white;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    z-index: 100;
}

/* 태블릿 이상 */
@media (min-width: 768px) {
    .stButton > button {
        width: auto;
        min-width: 120px;
    }

    .mobile-fixed-bottom {
        position: static;
        box-shadow: none;
    }
}

/* 데스크톱 */
@media (min-width: 1024px) {
    .stButton > button {
        min-height: 40px;
    }
}

/* 터치 친화적 요소 */
.touch-target {
    min-height: 44px;
    min-width: 44px;
    padding: 12px;
}

/* 스크롤 개선 */
.scroll-container {
    -webkit-overflow-scrolling: touch;
    overflow-y: auto;
}

/* 진동 피드백 지원 체크 */
@supports (touch-action: manipulation) {
    button, a, input, select, textarea {
        touch-action: manipulation;
    }
}
"""

    def get_mobile_layout_hints(self) -> Dict:
        """모바일 레이아웃 힌트"""
        return {
            "use_columns": False,
            "stack_elements": True,
            "full_width_buttons": True,
            "larger_fonts": True,
            "bottom_navigation": True,
            "swipe_gestures": True,
            "pull_to_refresh": True,
        }


# ============================================================
# 23. 알림 시스템
# ============================================================

class NotificationType(Enum):
    """알림 유형"""
    STUDY_REMINDER = "study_reminder"
    JOB_POSTING = "job_posting"
    STREAK_WARNING = "streak_warning"
    ACHIEVEMENT = "achievement"
    SCHEDULE = "schedule"


@dataclass
class Notification:
    """알림"""
    notification_id: str
    notification_type: NotificationType
    title: str
    message: str
    scheduled_time: datetime
    is_sent: bool = False
    is_read: bool = False
    action_url: Optional[str] = None
    priority: int = 1  # 1-5


@dataclass
class NotificationPreferences:
    """알림 설정"""
    user_id: str
    study_reminder_enabled: bool = True
    study_reminder_time: str = "19:00"
    job_posting_enabled: bool = True
    streak_warning_enabled: bool = True
    achievement_enabled: bool = True
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"


class NotificationManager:
    """알림 관리자"""

    # 알림 템플릿
    TEMPLATES = {
        NotificationType.STUDY_REMINDER: {
            "title": "오늘의 학습 시간!",
            "message": "오늘 연습 아직 안 하셨어요! 10분만 투자해보세요.",
            "priority": 2,
        },
        NotificationType.JOB_POSTING: {
            "title": "새 채용공고!",
            "message": "{airline}에서 채용을 시작했어요!",
            "priority": 4,
        },
        NotificationType.STREAK_WARNING: {
            "title": "스트릭이 끊기기 전에!",
            "message": "{streak}일 연속 기록이 끊어질 위기예요!",
            "priority": 3,
        },
        NotificationType.ACHIEVEMENT: {
            "title": "축하해요!",
            "message": "{achievement} 달성!",
            "priority": 2,
        },
        NotificationType.SCHEDULE: {
            "title": "면접 D-{days}",
            "message": "{airline} 면접까지 {days}일 남았어요!",
            "priority": 4,
        },
    }

    def __init__(self):
        self.pending_notifications: List[Notification] = []

    def create_notification(
        self,
        notification_type: NotificationType,
        params: Dict = None,
        scheduled_time: datetime = None
    ) -> Notification:
        """알림 생성"""

        template = self.TEMPLATES.get(notification_type, {})

        title = template.get("title", "알림")
        message = template.get("message", "")

        # 파라미터 치환
        if params:
            title = title.format(**params)
            message = message.format(**params)

        notification = Notification(
            notification_id=f"notif_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            notification_type=notification_type,
            title=title,
            message=message,
            scheduled_time=scheduled_time or datetime.now(),
            priority=template.get("priority", 1)
        )

        self.pending_notifications.append(notification)
        return notification

    def get_pending_notifications(self, user_id: str) -> List[Notification]:
        """대기 중인 알림"""
        now = datetime.now()
        return [n for n in self.pending_notifications if not n.is_sent and n.scheduled_time <= now]

    def schedule_study_reminder(
        self,
        user_id: str,
        preferences: NotificationPreferences
    ) -> Optional[Notification]:
        """학습 리마인더 예약"""

        if not preferences.study_reminder_enabled:
            return None

        # 알림 시간 파싱
        hour, minute = map(int, preferences.study_reminder_time.split(":"))
        reminder_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)

        if reminder_time < datetime.now():
            reminder_time += timedelta(days=1)

        return self.create_notification(
            NotificationType.STUDY_REMINDER,
            scheduled_time=reminder_time
        )

    def check_quiet_hours(self, preferences: NotificationPreferences) -> bool:
        """조용한 시간 확인"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        start = preferences.quiet_hours_start
        end = preferences.quiet_hours_end

        if start <= end:
            return start <= current_time <= end
        else:
            return current_time >= start or current_time <= end


# ============================================================
# 24. 오프라인 캐싱
# ============================================================

@dataclass
class CachedContent:
    """캐시된 콘텐츠"""
    content_id: str
    content_type: str
    data: Any
    cached_at: datetime
    expires_at: datetime
    size_bytes: int


class OfflineCacheManager:
    """오프라인 캐시 관리자"""

    # 캐시 가능한 콘텐츠 유형
    CACHEABLE_CONTENT = {
        "interview_tips": {"expires_hours": 168},  # 1주일
        "airline_info": {"expires_hours": 168},
        "question_bank": {"expires_hours": 24},
        "templates": {"expires_hours": 168},
        "user_progress": {"expires_hours": 1},
    }

    def __init__(self, max_cache_mb: int = 50):
        self.max_cache_bytes = max_cache_mb * 1024 * 1024
        self.cache: Dict[str, CachedContent] = {}

    def can_cache(self, content_type: str) -> bool:
        """캐시 가능 여부"""
        return content_type in self.CACHEABLE_CONTENT

    def cache_content(
        self,
        content_id: str,
        content_type: str,
        data: Any
    ) -> bool:
        """콘텐츠 캐시"""

        if not self.can_cache(content_type):
            return False

        settings = self.CACHEABLE_CONTENT[content_type]
        expires_hours = settings["expires_hours"]

        # 크기 계산 (간단한 추정)
        size = len(json.dumps(data)) if isinstance(data, (dict, list)) else len(str(data))

        cached = CachedContent(
            content_id=content_id,
            content_type=content_type,
            data=data,
            cached_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=expires_hours),
            size_bytes=size
        )

        self.cache[content_id] = cached
        return True

    def get_cached(self, content_id: str) -> Optional[Any]:
        """캐시된 콘텐츠 조회"""
        cached = self.cache.get(content_id)

        if not cached:
            return None

        if datetime.now() > cached.expires_at:
            del self.cache[content_id]
            return None

        return cached.data

    def get_cache_status(self) -> Dict:
        """캐시 상태"""
        total_size = sum(c.size_bytes for c in self.cache.values())
        return {
            "cached_items": len(self.cache),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "max_size_mb": self.max_cache_bytes / (1024 * 1024),
            "usage_percent": round((total_size / self.max_cache_bytes) * 100, 1)
        }

    def clear_expired(self) -> int:
        """만료된 캐시 정리"""
        now = datetime.now()
        expired = [k for k, v in self.cache.items() if v.expires_at < now]
        for key in expired:
            del self.cache[key]
        return len(expired)

    def get_offline_essential_list(self) -> List[str]:
        """오프라인 필수 콘텐츠 목록"""
        return [
            "interview_tips",
            "airline_info",
            "templates",
        ]


# ============================================================
# 25. 음성 폴백 시스템
# ============================================================

class InputMode(Enum):
    """입력 모드"""
    VOICE = "voice"
    TEXT = "text"
    HYBRID = "hybrid"


@dataclass
class InputModeStatus:
    """입력 모드 상태"""
    current_mode: InputMode
    voice_available: bool
    voice_error_count: int
    last_voice_error: Optional[str]
    auto_switched: bool
    switch_reason: Optional[str]


class VoiceFallbackManager:
    """음성 폴백 관리자"""

    # 폴백 설정
    MAX_VOICE_ERRORS = 3
    AUTO_SWITCH_THRESHOLD = 2

    def __init__(self):
        self.error_count = 0
        self.current_mode = InputMode.VOICE
        self.last_error = None

    def check_voice_availability(self) -> Dict:
        """음성 인식 가용성 확인"""
        # 실제로는 브라우저 API 확인
        return {
            "available": True,
            "permission_granted": True,
            "microphone_detected": True,
            "browser_supported": True,
        }

    def report_voice_error(self, error_message: str) -> InputModeStatus:
        """음성 오류 보고"""
        self.error_count += 1
        self.last_error = error_message

        auto_switched = False
        switch_reason = None

        if self.error_count >= self.AUTO_SWITCH_THRESHOLD:
            self.current_mode = InputMode.TEXT
            auto_switched = True
            switch_reason = f"음성 인식 오류 {self.error_count}회 발생"

        return InputModeStatus(
            current_mode=self.current_mode,
            voice_available=self.error_count < self.MAX_VOICE_ERRORS,
            voice_error_count=self.error_count,
            last_voice_error=self.last_error,
            auto_switched=auto_switched,
            switch_reason=switch_reason
        )

    def reset_voice_mode(self) -> None:
        """음성 모드 리셋"""
        self.error_count = 0
        self.current_mode = InputMode.VOICE
        self.last_error = None

    def get_mode_switch_ui(self) -> Dict:
        """모드 전환 UI 정보"""
        return {
            "show_toggle": True,
            "current_mode": self.current_mode.value,
            "voice_button_text": "음성으로 답변" if self.current_mode == InputMode.TEXT else "녹음 중...",
            "text_button_text": "텍스트로 답변" if self.current_mode == InputMode.VOICE else "입력 중...",
            "hint_message": self._get_hint_message()
        }

    def _get_hint_message(self) -> str:
        if self.current_mode == InputMode.TEXT:
            if self.error_count > 0:
                return "음성 인식에 문제가 있어 텍스트 모드로 전환되었습니다. 상단 버튼으로 다시 시도할 수 있어요."
            return "텍스트로 답변을 입력해주세요."
        else:
            return "마이크 버튼을 누르고 답변해주세요."

    def get_voice_troubleshooting(self) -> List[Dict]:
        """음성 인식 문제 해결 가이드"""
        return [
            {"step": 1, "title": "마이크 권한 확인", "desc": "브라우저에서 마이크 권한을 허용했는지 확인하세요"},
            {"step": 2, "title": "마이크 연결 확인", "desc": "마이크가 제대로 연결되어 있는지 확인하세요"},
            {"step": 3, "title": "주변 소음 줄이기", "desc": "조용한 환경에서 다시 시도해보세요"},
            {"step": 4, "title": "브라우저 새로고침", "desc": "페이지를 새로고침하고 다시 시도해보세요"},
            {"step": 5, "title": "텍스트 모드 사용", "desc": "계속 문제가 있다면 텍스트 입력을 사용하세요"},
        ]


# ============================================================
# 편의 함수들
# ============================================================

_layout_manager = ResponsiveLayoutManager()
_notification_manager = NotificationManager()
_cache_manager = OfflineCacheManager()
_fallback_manager = VoiceFallbackManager()


def detect_device_type(screen_width: int) -> str:
    """디바이스 유형 감지"""
    return _layout_manager.detect_device(screen_width).value


def get_responsive_settings(screen_width: int) -> ResponsiveSettings:
    """반응형 설정"""
    device = _layout_manager.detect_device(screen_width)
    return _layout_manager.get_settings(device)


def get_mobile_css() -> str:
    """모바일 CSS"""
    return _layout_manager.get_responsive_css()


def create_notification(
    notification_type: str,
    params: Dict = None
) -> Notification:
    """알림 생성"""
    nt = NotificationType(notification_type)
    return _notification_manager.create_notification(nt, params)


def schedule_study_reminder(user_id: str, reminder_time: str = "19:00") -> Optional[Notification]:
    """학습 리마인더 예약"""
    prefs = NotificationPreferences(user_id=user_id, study_reminder_time=reminder_time)
    return _notification_manager.schedule_study_reminder(user_id, prefs)


def cache_content(content_id: str, content_type: str, data: Any) -> bool:
    """콘텐츠 캐시"""
    return _cache_manager.cache_content(content_id, content_type, data)


def get_cached_content(content_id: str) -> Optional[Any]:
    """캐시된 콘텐츠"""
    return _cache_manager.get_cached(content_id)


def get_cache_status() -> Dict:
    """캐시 상태"""
    return _cache_manager.get_cache_status()


def report_voice_error(error: str) -> InputModeStatus:
    """음성 오류 보고"""
    return _fallback_manager.report_voice_error(error)


def get_input_mode_ui() -> Dict:
    """입력 모드 UI"""
    return _fallback_manager.get_mode_switch_ui()


def reset_voice_mode() -> None:
    """음성 모드 리셋"""
    _fallback_manager.reset_voice_mode()


def get_voice_troubleshooting() -> List[Dict]:
    """음성 문제 해결 가이드"""
    return _fallback_manager.get_voice_troubleshooting()

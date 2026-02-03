# analytics_tracker.py
# FlyReady Lab - 사용자 행동 분석 및 모니터링 시스템
# Phase A4: 로깅 고도화 500% 강화

import json
import time
import threading
import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# 설정
# =============================================================================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ANALYTICS_DIR = DATA_DIR / "analytics"
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)

# 파일 경로
USER_EVENTS_FILE = ANALYTICS_DIR / "user_events.json"
SESSION_DATA_FILE = ANALYTICS_DIR / "sessions.json"
METRICS_FILE = ANALYTICS_DIR / "metrics.json"
REALTIME_FILE = ANALYTICS_DIR / "realtime.json"

# =============================================================================
# 1. 이벤트 타입 정의
# =============================================================================

class EventCategory(Enum):
    """이벤트 카테고리"""
    PAGE = "page"              # 페이지 관련
    INTERVIEW = "interview"    # 면접 관련
    PRACTICE = "practice"      # 연습 관련
    ANALYSIS = "analysis"      # 분석 관련
    USER = "user"              # 사용자 관련
    SYSTEM = "system"          # 시스템 관련
    ERROR = "error"            # 에러 관련


class EventType(Enum):
    """이벤트 유형"""
    # 페이지 이벤트
    PAGE_VIEW = "page_view"
    PAGE_LEAVE = "page_leave"
    PAGE_SCROLL = "page_scroll"

    # 면접 이벤트
    INTERVIEW_START = "interview_start"
    INTERVIEW_END = "interview_end"
    QUESTION_SHOWN = "question_shown"
    ANSWER_SUBMIT = "answer_submit"
    FEEDBACK_VIEW = "feedback_view"

    # 연습 이벤트
    PRACTICE_START = "practice_start"
    PRACTICE_END = "practice_end"
    RECORDING_START = "recording_start"
    RECORDING_END = "recording_end"

    # 분석 이벤트
    VOICE_ANALYSIS = "voice_analysis"
    FACE_ANALYSIS = "face_analysis"
    POSTURE_ANALYSIS = "posture_analysis"
    SCORE_GENERATED = "score_generated"

    # 사용자 이벤트
    BUTTON_CLICK = "button_click"
    FORM_SUBMIT = "form_submit"
    FILE_UPLOAD = "file_upload"
    SETTING_CHANGE = "setting_change"

    # 시스템 이벤트
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    API_CALL = "api_call"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"


@dataclass
class AnalyticsEvent:
    """분석 이벤트 데이터"""
    event_type: str
    category: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: str = ""
    user_id: str = ""
    page: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None


# =============================================================================
# 2. 세션 관리
# =============================================================================

@dataclass
class UserSession:
    """사용자 세션"""
    session_id: str
    user_id: str = ""
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())
    page_views: int = 0
    events_count: int = 0
    pages_visited: List[str] = field(default_factory=list)
    device_info: Dict[str, str] = field(default_factory=dict)
    is_active: bool = True


class SessionManager:
    """세션 관리자"""

    SESSION_TIMEOUT = timedelta(minutes=30)

    def __init__(self):
        self._sessions: Dict[str, UserSession] = {}
        self._lock = threading.Lock()
        self._load_sessions()

    def _load_sessions(self):
        """세션 데이터 로드"""
        try:
            if SESSION_DATA_FILE.exists():
                with open(SESSION_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for sid, session_data in data.items():
                        self._sessions[sid] = UserSession(**session_data)
        except Exception as e:
            logger.error(f"세션 로드 실패: {e}")

    def _save_sessions(self):
        """세션 데이터 저장"""
        try:
            with open(SESSION_DATA_FILE, 'w', encoding='utf-8') as f:
                data = {sid: asdict(session) for sid, session in self._sessions.items()}
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"세션 저장 실패: {e}")

    def get_or_create_session(self, session_id: str = None, user_id: str = "") -> UserSession:
        """세션 가져오기 또는 생성"""
        with self._lock:
            if session_id and session_id in self._sessions:
                session = self._sessions[session_id]
                session.last_activity = datetime.now().isoformat()
                return session

            # 새 세션 생성
            new_id = session_id or str(uuid.uuid4())
            session = UserSession(session_id=new_id, user_id=user_id)
            self._sessions[new_id] = session
            self._save_sessions()
            return session

    def update_session(self, session_id: str, page: str = None, increment_events: bool = True):
        """세션 업데이트"""
        with self._lock:
            if session_id not in self._sessions:
                return

            session = self._sessions[session_id]
            session.last_activity = datetime.now().isoformat()

            if increment_events:
                session.events_count += 1

            if page:
                session.page_views += 1
                if page not in session.pages_visited:
                    session.pages_visited.append(page)

            self._save_sessions()

    def end_session(self, session_id: str):
        """세션 종료"""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].is_active = False
                self._save_sessions()

    def get_active_sessions(self) -> List[UserSession]:
        """활성 세션 목록"""
        cutoff = datetime.now() - self.SESSION_TIMEOUT
        with self._lock:
            return [
                s for s in self._sessions.values()
                if s.is_active and datetime.fromisoformat(s.last_activity) > cutoff
            ]

    def cleanup_inactive(self) -> int:
        """비활성 세션 정리"""
        cutoff = datetime.now() - self.SESSION_TIMEOUT
        with self._lock:
            inactive = [
                sid for sid, s in self._sessions.items()
                if datetime.fromisoformat(s.last_activity) < cutoff
            ]
            for sid in inactive:
                self._sessions[sid].is_active = False
            self._save_sessions()
            return len(inactive)


# 전역 세션 관리자
session_manager = SessionManager()


# =============================================================================
# 3. 이벤트 추적 시스템
# =============================================================================

class EventTracker:
    """이벤트 추적기"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._events: List[AnalyticsEvent] = []
        self._events_lock = threading.Lock()
        self._max_events = 10000
        self._flush_interval = 60  # 60초마다 자동 저장
        self._initialized = True

        # 백그라운드 저장 스레드
        self._start_auto_flush()

    def _start_auto_flush(self):
        """자동 저장 스레드 시작"""
        def flush_loop():
            while True:
                time.sleep(self._flush_interval)
                self.flush()

        thread = threading.Thread(target=flush_loop, daemon=True)
        thread.start()

    def track(
        self,
        event_type: EventType,
        category: EventCategory = None,
        session_id: str = "",
        user_id: str = "",
        page: str = "",
        properties: Dict[str, Any] = None,
        duration_ms: float = None
    ):
        """이벤트 추적"""
        event = AnalyticsEvent(
            event_type=event_type.value if isinstance(event_type, EventType) else event_type,
            category=category.value if category else self._infer_category(event_type),
            session_id=session_id,
            user_id=user_id,
            page=page,
            properties=properties or {},
            duration_ms=duration_ms
        )

        with self._events_lock:
            self._events.append(event)

            # 최대 개수 초과 시 저장 및 정리
            if len(self._events) >= self._max_events:
                self._flush_internal()

        # 세션 업데이트
        if session_id:
            session_manager.update_session(session_id, page)

        logger.debug(f"Event tracked: {event.event_type} on {page}")

    def _infer_category(self, event_type) -> str:
        """이벤트 타입에서 카테고리 추론"""
        if isinstance(event_type, EventType):
            event_type = event_type.value

        category_map = {
            "page": EventCategory.PAGE,
            "interview": EventCategory.INTERVIEW,
            "practice": EventCategory.PRACTICE,
            "analysis": EventCategory.ANALYSIS,
            "button": EventCategory.USER,
            "form": EventCategory.USER,
            "session": EventCategory.SYSTEM,
            "api": EventCategory.SYSTEM,
            "cache": EventCategory.SYSTEM,
        }

        for prefix, cat in category_map.items():
            if event_type.startswith(prefix):
                return cat.value

        return EventCategory.SYSTEM.value

    def flush(self):
        """이벤트를 파일에 저장"""
        with self._events_lock:
            self._flush_internal()

    def _flush_internal(self):
        """내부 저장 (락 필요 없음)"""
        if not self._events:
            return

        try:
            # 기존 데이터 로드
            existing = []
            if USER_EVENTS_FILE.exists():
                try:
                    with open(USER_EVENTS_FILE, 'r', encoding='utf-8') as f:
                        existing = json.load(f)
                except:
                    pass

            # 새 이벤트 추가
            new_events = [asdict(e) for e in self._events]
            all_events = existing + new_events

            # 최대 개수 유지 (가장 최근 10000개)
            if len(all_events) > self._max_events:
                all_events = all_events[-self._max_events:]

            # 저장
            with open(USER_EVENTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_events, f, ensure_ascii=False, indent=2)

            # 메모리 이벤트 클리어
            self._events.clear()

            logger.info(f"이벤트 저장 완료: {len(new_events)}개")

        except Exception as e:
            logger.error(f"이벤트 저장 실패: {e}")

    def get_events(
        self,
        event_type: str = None,
        category: str = None,
        session_id: str = None,
        hours: int = 24
    ) -> List[Dict]:
        """이벤트 조회"""
        cutoff = datetime.now() - timedelta(hours=hours)

        try:
            if not USER_EVENTS_FILE.exists():
                return []

            with open(USER_EVENTS_FILE, 'r', encoding='utf-8') as f:
                all_events = json.load(f)

            filtered = []
            for event in all_events:
                # 시간 필터
                try:
                    event_time = datetime.fromisoformat(event.get('timestamp', ''))
                    if event_time < cutoff:
                        continue
                except:
                    continue

                # 타입 필터
                if event_type and event.get('event_type') != event_type:
                    continue

                # 카테고리 필터
                if category and event.get('category') != category:
                    continue

                # 세션 필터
                if session_id and event.get('session_id') != session_id:
                    continue

                filtered.append(event)

            return filtered

        except Exception as e:
            logger.error(f"이벤트 조회 실패: {e}")
            return []


# 전역 이벤트 추적기
event_tracker = EventTracker()


# =============================================================================
# 4. 메트릭 수집 시스템
# =============================================================================

class MetricsCollector:
    """메트릭 수집기"""

    def __init__(self):
        self._metrics: Dict[str, List[Dict]] = defaultdict(list)
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._lock = threading.Lock()

    def increment(self, metric_name: str, value: int = 1, tags: Dict = None):
        """카운터 증가"""
        with self._lock:
            key = self._make_key(metric_name, tags)
            self._counters[key] += value

    def gauge(self, metric_name: str, value: float, tags: Dict = None):
        """게이지 설정"""
        with self._lock:
            key = self._make_key(metric_name, tags)
            self._gauges[key] = value

    def timing(self, metric_name: str, duration_ms: float, tags: Dict = None):
        """타이밍 기록"""
        with self._lock:
            key = self._make_key(metric_name, tags)
            self._metrics[key].append({
                "value": duration_ms,
                "timestamp": datetime.now().isoformat()
            })

            # 최대 1000개 유지
            if len(self._metrics[key]) > 1000:
                self._metrics[key] = self._metrics[key][-1000:]

    def _make_key(self, name: str, tags: Dict = None) -> str:
        """메트릭 키 생성"""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"

    def get_counter(self, metric_name: str, tags: Dict = None) -> int:
        """카운터 값 조회"""
        key = self._make_key(metric_name, tags)
        return self._counters.get(key, 0)

    def get_gauge(self, metric_name: str, tags: Dict = None) -> float:
        """게이지 값 조회"""
        key = self._make_key(metric_name, tags)
        return self._gauges.get(key, 0)

    def get_timing_stats(self, metric_name: str, tags: Dict = None) -> Dict:
        """타이밍 통계"""
        key = self._make_key(metric_name, tags)
        values = [m["value"] for m in self._metrics.get(key, [])]

        if not values:
            return {"count": 0}

        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "p50": sorted(values)[len(values) // 2],
            "p95": sorted(values)[int(len(values) * 0.95)] if len(values) >= 20 else max(values)
        }

    def get_all_metrics(self) -> Dict:
        """모든 메트릭"""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "timings": {k: self.get_timing_stats(k) for k in self._metrics.keys()}
            }

    def save(self):
        """메트릭 저장"""
        try:
            with open(METRICS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.get_all_metrics(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"메트릭 저장 실패: {e}")


# 전역 메트릭 수집기
metrics = MetricsCollector()


# =============================================================================
# 5. 실시간 모니터링
# =============================================================================

class RealtimeMonitor:
    """실시간 모니터링"""

    def __init__(self):
        self._current_stats: Dict[str, Any] = {
            "active_users": 0,
            "page_views_minute": 0,
            "api_calls_minute": 0,
            "errors_minute": 0,
            "avg_response_time": 0,
            "last_updated": ""
        }
        self._lock = threading.Lock()
        self._start_update_loop()

    def _start_update_loop(self):
        """실시간 업데이트 루프 시작"""
        def update():
            while True:
                self._update_stats()
                time.sleep(10)  # 10초마다 업데이트

        thread = threading.Thread(target=update, daemon=True)
        thread.start()

    def _update_stats(self):
        """통계 업데이트"""
        with self._lock:
            # 활성 사용자
            self._current_stats["active_users"] = len(session_manager.get_active_sessions())

            # 최근 1분 이벤트
            recent_events = event_tracker.get_events(hours=1/60)  # 1분

            page_views = sum(1 for e in recent_events if e.get('event_type') == 'page_view')
            api_calls = sum(1 for e in recent_events if e.get('event_type') == 'api_call')
            errors = sum(1 for e in recent_events if e.get('category') == 'error')

            self._current_stats["page_views_minute"] = page_views
            self._current_stats["api_calls_minute"] = api_calls
            self._current_stats["errors_minute"] = errors

            # 평균 응답 시간
            response_times = [
                e.get('duration_ms', 0) for e in recent_events
                if e.get('duration_ms')
            ]
            self._current_stats["avg_response_time"] = (
                sum(response_times) / len(response_times) if response_times else 0
            )

            self._current_stats["last_updated"] = datetime.now().isoformat()

            # 파일 저장
            try:
                with open(REALTIME_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self._current_stats, f, ensure_ascii=False, indent=2)
            except:
                pass

    def get_stats(self) -> Dict:
        """현재 통계"""
        with self._lock:
            return self._current_stats.copy()


# 전역 실시간 모니터
realtime_monitor = RealtimeMonitor()


# =============================================================================
# 6. 분석 대시보드 지원
# =============================================================================

class AnalyticsDashboard:
    """분석 대시보드 데이터"""

    @staticmethod
    def get_summary(days: int = 7) -> Dict:
        """요약 통계"""
        events = event_tracker.get_events(hours=days * 24)

        # 일별 이벤트
        daily_events = defaultdict(int)
        for e in events:
            date = e.get('timestamp', '')[:10]
            daily_events[date] += 1

        # 페이지별 조회수
        page_views = defaultdict(int)
        for e in events:
            if e.get('event_type') == 'page_view':
                page_views[e.get('page', 'unknown')] += 1

        # 이벤트 타입별
        event_types = defaultdict(int)
        for e in events:
            event_types[e.get('event_type', 'unknown')] += 1

        return {
            "total_events": len(events),
            "daily_events": dict(daily_events),
            "page_views": dict(page_views),
            "event_types": dict(event_types),
            "active_sessions": len(session_manager.get_active_sessions()),
            "generated_at": datetime.now().isoformat()
        }

    @staticmethod
    def get_user_journey(session_id: str) -> List[Dict]:
        """사용자 여정"""
        events = event_tracker.get_events(session_id=session_id)
        return sorted(events, key=lambda e: e.get('timestamp', ''))

    @staticmethod
    def get_popular_pages(days: int = 7, limit: int = 10) -> List[Dict]:
        """인기 페이지"""
        events = event_tracker.get_events(event_type='page_view', hours=days * 24)

        page_counts = defaultdict(int)
        for e in events:
            page_counts[e.get('page', 'unknown')] += 1

        sorted_pages = sorted(page_counts.items(), key=lambda x: x[1], reverse=True)

        return [
            {"page": page, "views": count}
            for page, count in sorted_pages[:limit]
        ]

    @staticmethod
    def get_interview_stats(days: int = 7) -> Dict:
        """면접 통계"""
        events = event_tracker.get_events(category='interview', hours=days * 24)

        starts = sum(1 for e in events if e.get('event_type') == 'interview_start')
        ends = sum(1 for e in events if e.get('event_type') == 'interview_end')
        answers = sum(1 for e in events if e.get('event_type') == 'answer_submit')

        return {
            "total_interviews": starts,
            "completed_interviews": ends,
            "completion_rate": (ends / starts * 100) if starts > 0 else 0,
            "total_answers": answers,
            "avg_answers_per_interview": (answers / starts) if starts > 0 else 0
        }


# =============================================================================
# 7. 편의 함수
# =============================================================================

def track_page_view(page: str, session_id: str = "", user_id: str = ""):
    """페이지 뷰 추적"""
    event_tracker.track(
        EventType.PAGE_VIEW,
        EventCategory.PAGE,
        session_id=session_id,
        user_id=user_id,
        page=page
    )
    metrics.increment("page_views", tags={"page": page})


def track_interview_start(session_id: str, interview_type: str = "", airline: str = ""):
    """면접 시작 추적"""
    event_tracker.track(
        EventType.INTERVIEW_START,
        EventCategory.INTERVIEW,
        session_id=session_id,
        properties={"interview_type": interview_type, "airline": airline}
    )
    metrics.increment("interviews_started")


def track_api_call(api_name: str, success: bool, duration_ms: float = None):
    """API 호출 추적"""
    event_tracker.track(
        EventType.API_CALL,
        EventCategory.SYSTEM,
        properties={"api_name": api_name, "success": success},
        duration_ms=duration_ms
    )
    metrics.increment(f"api_calls.{api_name}", tags={"success": str(success)})
    if duration_ms:
        metrics.timing(f"api_latency.{api_name}", duration_ms)


def track_button_click(button_name: str, page: str = "", session_id: str = ""):
    """버튼 클릭 추적"""
    event_tracker.track(
        EventType.BUTTON_CLICK,
        EventCategory.USER,
        session_id=session_id,
        page=page,
        properties={"button": button_name}
    )
    metrics.increment("button_clicks", tags={"button": button_name})


def track_error(error_type: str, error_message: str, page: str = "", session_id: str = ""):
    """에러 추적"""
    event_tracker.track(
        EventType.API_CALL,  # 재사용
        EventCategory.ERROR,
        session_id=session_id,
        page=page,
        properties={"error_type": error_type, "error_message": error_message[:200]}
    )
    metrics.increment("errors", tags={"type": error_type})


# =============================================================================
# Streamlit 통합
# =============================================================================

def init_analytics():
    """분석 시스템 초기화 (Streamlit 세션)"""
    try:
        import streamlit as st

        if 'analytics_session_id' not in st.session_state:
            st.session_state.analytics_session_id = str(uuid.uuid4())

            # 세션 생성
            session_manager.get_or_create_session(st.session_state.analytics_session_id)

            # 세션 시작 이벤트
            event_tracker.track(
                EventType.SESSION_START,
                EventCategory.SYSTEM,
                session_id=st.session_state.analytics_session_id
            )

            logger.info(f"Analytics initialized: {st.session_state.analytics_session_id[:8]}...")

        return st.session_state.analytics_session_id

    except Exception as e:
        logger.error(f"Analytics 초기화 실패: {e}")
        return ""


def get_current_session_id() -> str:
    """현재 세션 ID"""
    try:
        import streamlit as st
        return st.session_state.get('analytics_session_id', '')
    except:
        return ''


# =============================================================================
# 모듈 테스트
# =============================================================================

if __name__ == "__main__":
    print("=== Analytics Tracker Test ===")

    # 1. 이벤트 추적 테스트
    print("\n1. Event Tracking Test")
    event_tracker.track(
        EventType.PAGE_VIEW,
        EventCategory.PAGE,
        session_id="test_session",
        page="test_page"
    )
    print("   [OK] Event tracked")

    # 2. 세션 관리 테스트
    print("\n2. Session Management Test")
    session = session_manager.get_or_create_session("test_session", "test_user")
    print(f"   [OK] Session created: {session.session_id[:8]}...")

    # 3. 메트릭 테스트
    print("\n3. Metrics Test")
    metrics.increment("test_counter")
    metrics.gauge("test_gauge", 42.5)
    metrics.timing("test_timing", 150.0)
    print(f"   Counter: {metrics.get_counter('test_counter')}")
    print(f"   Gauge: {metrics.get_gauge('test_gauge')}")
    print(f"   Timing stats: {metrics.get_timing_stats('test_timing')}")

    # 4. 실시간 모니터 테스트
    print("\n4. Realtime Monitor Test")
    stats = realtime_monitor.get_stats()
    print(f"   Active users: {stats['active_users']}")

    # 5. 대시보드 테스트
    print("\n5. Dashboard Test")
    summary = AnalyticsDashboard.get_summary(days=1)
    print(f"   Total events: {summary['total_events']}")

    # 6. 이벤트 저장
    event_tracker.flush()
    print("\n[OK] Events flushed to file")

    print("\nModule ready!")

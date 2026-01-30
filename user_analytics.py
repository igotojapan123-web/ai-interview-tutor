# user_analytics.py
# 사용자 행동 분석 및 기능 사용 추적 시스템

import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict
from functools import wraps

try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# ============================================================
# 설정
# ============================================================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ANALYTICS_DIR = DATA_DIR / "analytics"
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)

# 이벤트 파일
EVENTS_FILE = ANALYTICS_DIR / "events.json"
DAILY_STATS_FILE = ANALYTICS_DIR / "daily_stats.json"
USER_PROFILES_FILE = ANALYTICS_DIR / "user_profiles.json"


# ============================================================
# 이벤트 유형 정의
# ============================================================

class EventType:
    """이벤트 유형 상수"""
    # 페이지 이벤트
    PAGE_VIEW = "page_view"
    PAGE_EXIT = "page_exit"

    # 기능 사용 이벤트
    FEATURE_START = "feature_start"
    FEATURE_COMPLETE = "feature_complete"
    FEATURE_ABORT = "feature_abort"

    # 인터뷰 관련
    INTERVIEW_START = "interview_start"
    INTERVIEW_COMPLETE = "interview_complete"
    QUESTION_ANSWERED = "question_answered"

    # 학습 관련
    STUDY_MATERIAL_VIEW = "study_material_view"
    PRACTICE_COMPLETE = "practice_complete"

    # API 관련
    API_CALL = "api_call"
    API_ERROR = "api_error"

    # 사용자 관련
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    USER_ACTION = "user_action"


# ============================================================
# 사용자 분석 클래스
# ============================================================

class UserAnalytics:
    """사용자 행동 분석 시스템"""

    def __init__(self):
        self._lock = threading.Lock()
        self._events_buffer: List[Dict[str, Any]] = []
        self._buffer_size = 100  # 버퍼 크기
        self._daily_stats: Dict[str, Dict[str, Any]] = {}
        self._user_profiles: Dict[str, Dict[str, Any]] = {}
        self._feature_usage: Dict[str, int] = defaultdict(int)

        # 기존 데이터 로드
        self._load_data()

    def _load_data(self) -> None:
        """저장된 데이터 로드"""
        try:
            if DAILY_STATS_FILE.exists():
                with open(DAILY_STATS_FILE, 'r', encoding='utf-8') as f:
                    self._daily_stats = json.load(f)

            if USER_PROFILES_FILE.exists():
                with open(USER_PROFILES_FILE, 'r', encoding='utf-8') as f:
                    self._user_profiles = json.load(f)

        except Exception as e:
            logger.error(f"분석 데이터 로드 실패: {e}")

    def _save_data(self) -> None:
        """데이터 저장"""
        try:
            with open(DAILY_STATS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._daily_stats, f, ensure_ascii=False, indent=2)

            with open(USER_PROFILES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._user_profiles, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"분석 데이터 저장 실패: {e}")

    # -------------------------------------------------------------------------
    # 이벤트 추적
    # -------------------------------------------------------------------------

    def track_event(
        self,
        event_type: str,
        user_id: str = None,
        properties: Dict[str, Any] = None,
        page: str = None
    ) -> None:
        """
        이벤트 추적

        Args:
            event_type: 이벤트 유형
            user_id: 사용자 ID (선택)
            properties: 추가 속성
            page: 페이지 이름
        """
        with self._lock:
            event = {
                "event": event_type,
                "user_id": user_id[:16] if user_id else "anonymous",
                "timestamp": datetime.now().isoformat(),
                "page": page,
                "properties": properties or {}
            }

            self._events_buffer.append(event)

            # 일일 통계 업데이트
            self._update_daily_stats(event)

            # 기능 사용 카운트
            if event_type in [EventType.FEATURE_START, EventType.FEATURE_COMPLETE]:
                feature = properties.get("feature") if properties else None
                if feature:
                    self._feature_usage[feature] += 1

            # 사용자 프로필 업데이트
            if user_id:
                self._update_user_profile(user_id, event)

            # 버퍼가 가득 차면 저장
            if len(self._events_buffer) >= self._buffer_size:
                self._flush_events()

    def _update_daily_stats(self, event: Dict[str, Any]) -> None:
        """일일 통계 업데이트"""
        date_key = datetime.now().strftime("%Y-%m-%d")

        if date_key not in self._daily_stats:
            self._daily_stats[date_key] = {
                "total_events": 0,
                "unique_users": set(),
                "page_views": defaultdict(int),
                "features_used": defaultdict(int),
                "interviews_completed": 0,
                "api_calls": 0,
                "errors": 0
            }

        stats = self._daily_stats[date_key]
        stats["total_events"] += 1

        if event.get("user_id"):
            if isinstance(stats["unique_users"], set):
                stats["unique_users"].add(event["user_id"])
            else:
                stats["unique_users"] = set(stats["unique_users"])
                stats["unique_users"].add(event["user_id"])

        if event.get("page"):
            stats["page_views"][event["page"]] += 1

        event_type = event.get("event")
        if event_type == EventType.INTERVIEW_COMPLETE:
            stats["interviews_completed"] += 1
        elif event_type == EventType.API_CALL:
            stats["api_calls"] += 1
        elif event_type == EventType.API_ERROR:
            stats["errors"] += 1

    def _update_user_profile(self, user_id: str, event: Dict[str, Any]) -> None:
        """사용자 프로필 업데이트"""
        if user_id not in self._user_profiles:
            self._user_profiles[user_id] = {
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "total_sessions": 0,
                "total_events": 0,
                "features_used": [],
                "pages_visited": [],
                "interviews_completed": 0,
                "practice_sessions": 0
            }

        profile = self._user_profiles[user_id]
        profile["last_seen"] = datetime.now().isoformat()
        profile["total_events"] += 1

        event_type = event.get("event")

        if event_type == EventType.SESSION_START:
            profile["total_sessions"] += 1
        elif event_type == EventType.INTERVIEW_COMPLETE:
            profile["interviews_completed"] += 1
        elif event_type == EventType.PRACTICE_COMPLETE:
            profile["practice_sessions"] += 1

        # 방문 페이지 추적 (최근 20개)
        if event.get("page") and event["page"] not in profile["pages_visited"][-20:]:
            profile["pages_visited"].append(event["page"])
            profile["pages_visited"] = profile["pages_visited"][-20:]

        # 사용 기능 추적
        props = event.get("properties", {})
        feature = props.get("feature")
        if feature and feature not in profile["features_used"]:
            profile["features_used"].append(feature)

    def _flush_events(self) -> None:
        """이벤트 버퍼를 파일에 저장"""
        if not self._events_buffer:
            return

        try:
            # 기존 이벤트 로드
            events = []
            if EVENTS_FILE.exists():
                with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
                    events = json.load(f)

            # 새 이벤트 추가
            events.extend(self._events_buffer)

            # 최근 10000개만 유지
            events = events[-10000:]

            # 저장
            with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(events, f, ensure_ascii=False)

            self._events_buffer.clear()
            self._save_data()

            logger.debug(f"분석 이벤트 저장: {len(events)}개")

        except Exception as e:
            logger.error(f"이벤트 저장 실패: {e}")

    # -------------------------------------------------------------------------
    # 특화 추적 함수
    # -------------------------------------------------------------------------

    def track_page_view(self, user_id: str, page: str, referrer: str = None) -> None:
        """페이지 조회 추적"""
        self.track_event(
            EventType.PAGE_VIEW,
            user_id=user_id,
            page=page,
            properties={"referrer": referrer}
        )

    def track_feature_use(
        self,
        user_id: str,
        feature: str,
        action: str = "start",
        duration_seconds: float = None
    ) -> None:
        """기능 사용 추적"""
        event_type = {
            "start": EventType.FEATURE_START,
            "complete": EventType.FEATURE_COMPLETE,
            "abort": EventType.FEATURE_ABORT
        }.get(action, EventType.FEATURE_START)

        self.track_event(
            event_type,
            user_id=user_id,
            properties={
                "feature": feature,
                "duration_seconds": duration_seconds
            }
        )

    def track_interview(
        self,
        user_id: str,
        interview_type: str,
        action: str = "start",
        score: float = None,
        duration_minutes: float = None
    ) -> None:
        """면접 연습 추적"""
        event_type = EventType.INTERVIEW_START if action == "start" else EventType.INTERVIEW_COMPLETE

        self.track_event(
            event_type,
            user_id=user_id,
            properties={
                "interview_type": interview_type,
                "score": score,
                "duration_minutes": duration_minutes
            }
        )

    def track_api_call(
        self,
        api_type: str,
        success: bool = True,
        duration_ms: float = None,
        error: str = None
    ) -> None:
        """API 호출 추적"""
        event_type = EventType.API_CALL if success else EventType.API_ERROR

        self.track_event(
            event_type,
            properties={
                "api_type": api_type,
                "success": success,
                "duration_ms": duration_ms,
                "error": error
            }
        )

    # -------------------------------------------------------------------------
    # 분석 리포트
    # -------------------------------------------------------------------------

    def get_daily_report(self, date: str = None) -> Dict[str, Any]:
        """일일 리포트"""
        date = date or datetime.now().strftime("%Y-%m-%d")

        with self._lock:
            stats = self._daily_stats.get(date, {})

            # set을 list로 변환
            if "unique_users" in stats and isinstance(stats["unique_users"], set):
                unique_count = len(stats["unique_users"])
            else:
                unique_count = len(stats.get("unique_users", []))

            return {
                "date": date,
                "total_events": stats.get("total_events", 0),
                "unique_users": unique_count,
                "page_views": dict(stats.get("page_views", {})),
                "features_used": dict(stats.get("features_used", {})),
                "interviews_completed": stats.get("interviews_completed", 0),
                "api_calls": stats.get("api_calls", 0),
                "errors": stats.get("errors", 0)
            }

    def get_feature_usage_report(self) -> Dict[str, Any]:
        """기능 사용 리포트"""
        with self._lock:
            sorted_features = sorted(
                self._feature_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )

            return {
                "total_feature_uses": sum(self._feature_usage.values()),
                "features": dict(sorted_features),
                "top_features": sorted_features[:10]
            }

    def get_user_retention(self, days: int = 7) -> Dict[str, Any]:
        """사용자 리텐션 분석"""
        with self._lock:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            daily_users = []
            for i in range(days):
                date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
                stats = self._daily_stats.get(date, {})

                users = stats.get("unique_users", [])
                if isinstance(users, set):
                    user_count = len(users)
                else:
                    user_count = len(users)

                daily_users.append({
                    "date": date,
                    "users": user_count
                })

            return {
                "period_days": days,
                "daily_active_users": daily_users,
                "average_dau": sum(d["users"] for d in daily_users) / max(len(daily_users), 1)
            }

    def get_user_journey(self, user_id: str) -> Dict[str, Any]:
        """사용자 여정 분석"""
        with self._lock:
            profile = self._user_profiles.get(user_id, {})

            return {
                "user_id": user_id[:8] + "...",
                "first_seen": profile.get("first_seen"),
                "last_seen": profile.get("last_seen"),
                "total_sessions": profile.get("total_sessions", 0),
                "total_events": profile.get("total_events", 0),
                "pages_visited": profile.get("pages_visited", []),
                "features_used": profile.get("features_used", []),
                "interviews_completed": profile.get("interviews_completed", 0),
                "practice_sessions": profile.get("practice_sessions", 0)
            }

    def get_popular_pages(self, days: int = 7) -> List[Dict[str, Any]]:
        """인기 페이지 분석"""
        with self._lock:
            page_totals = defaultdict(int)

            end_date = datetime.now()
            for i in range(days):
                date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
                stats = self._daily_stats.get(date, {})
                page_views = stats.get("page_views", {})

                for page, count in page_views.items():
                    page_totals[page] += count

            sorted_pages = sorted(page_totals.items(), key=lambda x: x[1], reverse=True)

            return [{"page": p, "views": v} for p, v in sorted_pages[:20]]

    def flush(self) -> None:
        """버퍼 강제 저장"""
        with self._lock:
            self._flush_events()


# 전역 인스턴스
analytics = UserAnalytics()


# ============================================================
# 데코레이터
# ============================================================

def track_feature(feature_name: str, get_user_id=None):
    """
    기능 사용 추적 데코레이터

    Usage:
        @track_feature("voice_interview")
        def start_voice_interview(user_id, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 사용자 ID 추출
            if get_user_id:
                user_id = get_user_id(*args, **kwargs)
            elif args:
                user_id = str(args[0])
            else:
                user_id = kwargs.get('user_id', 'anonymous')

            start_time = time.time()

            # 시작 추적
            analytics.track_feature_use(user_id, feature_name, "start")

            try:
                result = func(*args, **kwargs)

                # 완료 추적
                duration = time.time() - start_time
                analytics.track_feature_use(user_id, feature_name, "complete", duration)

                return result

            except Exception as e:
                # 중단 추적
                duration = time.time() - start_time
                analytics.track_feature_use(user_id, feature_name, "abort", duration)
                raise

        return wrapper
    return decorator


# ============================================================
# 간편 함수
# ============================================================

def track_page(user_id: str, page: str) -> None:
    """페이지 조회 추적"""
    analytics.track_page_view(user_id, page)


def track_feature_use(user_id: str, feature: str, action: str = "complete") -> None:
    """기능 사용 추적"""
    analytics.track_feature_use(user_id, feature, action)


def track_interview_complete(
    user_id: str,
    interview_type: str,
    score: float = None
) -> None:
    """면접 완료 추적"""
    analytics.track_interview(user_id, interview_type, "complete", score)


def get_analytics_summary() -> Dict[str, Any]:
    """분석 요약"""
    return {
        "today": analytics.get_daily_report(),
        "features": analytics.get_feature_usage_report(),
        "retention": analytics.get_user_retention(7),
        "popular_pages": analytics.get_popular_pages(7)
    }


# ============================================================
# Streamlit 컴포넌트
# ============================================================

def render_analytics_dashboard():
    """분석 대시보드 렌더링"""
    import streamlit as st

    st.markdown("### 사용자 분석")

    summary = get_analytics_summary()
    today = summary["today"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("오늘 이벤트", today["total_events"])

    with col2:
        st.metric("활성 사용자", today["unique_users"])

    with col3:
        st.metric("면접 완료", today["interviews_completed"])

    with col4:
        st.metric("API 호출", today["api_calls"])

    # 인기 페이지
    st.markdown("#### 인기 페이지 (7일)")
    popular = summary["popular_pages"][:5]
    for item in popular:
        st.text(f"  {item['page']}: {item['views']}회")


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=== User Analytics ===")

    # 테스트 이벤트
    test_user = "test_user_123"

    analytics.track_page_view(test_user, "home")
    analytics.track_page_view(test_user, "interview")
    analytics.track_feature_use(test_user, "voice_interview", "start")
    analytics.track_feature_use(test_user, "voice_interview", "complete", 300.5)
    analytics.track_interview(test_user, "korean", "complete", score=85.5)
    analytics.track_api_call("openai", success=True, duration_ms=150)

    # 리포트
    print("\n일일 리포트:")
    print(json.dumps(analytics.get_daily_report(), indent=2, ensure_ascii=False))

    print("\n기능 사용 리포트:")
    print(json.dumps(analytics.get_feature_usage_report(), indent=2, ensure_ascii=False))

    print("\n사용자 여정:")
    print(json.dumps(analytics.get_user_journey(test_user), indent=2, ensure_ascii=False))

    # 저장
    analytics.flush()
    print("\nReady!")

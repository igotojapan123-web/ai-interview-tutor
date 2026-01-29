# analytics.py
# FlyReady Lab - Enterprise Analytics System
# Stage 4: 대기업 수준 사용자 행동 분석
# Samsung-level quality implementation

import streamlit as st
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict
import threading

from logging_config import get_logger

logger = get_logger(__name__)

# =============================================================================
# 경로 설정
# =============================================================================

PROJECT_ROOT = Path(__file__).parent
ANALYTICS_DIR = PROJECT_ROOT / "logs" / "analytics"
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)

# 파일 경로
SESSION_LOG_FILE = ANALYTICS_DIR / "sessions.jsonl"
FUNNEL_LOG_FILE = ANALYTICS_DIR / "funnels.jsonl"
USER_JOURNEY_FILE = ANALYTICS_DIR / "journeys.jsonl"
DAILY_STATS_FILE = ANALYTICS_DIR / "daily_stats.json"


# =============================================================================
# 분석 유형 정의
# =============================================================================

class AnalyticsEventType(Enum):
    """분석 이벤트 유형"""
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    PAGE_VIEW = "page_view"
    BUTTON_CLICK = "button_click"
    FORM_SUBMIT = "form_submit"
    FEATURE_USE = "feature_use"
    ERROR = "error"
    CONVERSION = "conversion"
    ENGAGEMENT = "engagement"


class ConversionGoal(Enum):
    """전환 목표"""
    INTERVIEW_COMPLETE = "interview_complete"
    ESSAY_ANALYSIS = "essay_analysis"
    QUIZ_COMPLETE = "quiz_complete"
    PRACTICE_SESSION = "practice_session"
    FEATURE_DISCOVERY = "feature_discovery"


# =============================================================================
# 분석 데이터 구조
# =============================================================================

@dataclass
class AnalyticsEvent:
    """분석 이벤트"""
    event_type: AnalyticsEventType
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    page: Optional[str] = None
    action: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    duration_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "user_id": self.user_id,
            "page": self.page,
            "action": self.action,
            "properties": self.properties,
            "duration_seconds": self.duration_seconds
        }


@dataclass
class SessionData:
    """세션 데이터"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    user_id: Optional[str] = None
    pages_viewed: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    conversions: List[str] = field(default_factory=list)
    total_duration_seconds: float = 0
    device_info: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "user_id": self.user_id,
            "pages_viewed": self.pages_viewed,
            "page_count": len(self.pages_viewed),
            "unique_pages": len(set(self.pages_viewed)),
            "actions": self.actions,
            "action_count": len(self.actions),
            "conversions": self.conversions,
            "total_duration_seconds": self.total_duration_seconds,
            "device_info": self.device_info
        }


# =============================================================================
# 분석 시스템
# =============================================================================

class AnalyticsSystem:
    """사용자 행동 분석 시스템 (싱글톤)"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._active_sessions: Dict[str, SessionData] = {}
        self._page_view_times: Dict[str, datetime] = {}  # session_id -> last page view time
        self._daily_stats: Dict[str, Dict[str, int]] = {}
        self._load_daily_stats()

        logger.info("AnalyticsSystem initialized (Enterprise Level)")

    def _load_daily_stats(self):
        """일일 통계 로드"""
        try:
            if DAILY_STATS_FILE.exists():
                with open(DAILY_STATS_FILE, "r", encoding="utf-8") as f:
                    self._daily_stats = json.load(f)
        except Exception as e:
            logger.error(f"일일 통계 로드 실패: {e}")
            self._daily_stats = {}

    def _save_daily_stats(self):
        """일일 통계 저장"""
        try:
            with open(DAILY_STATS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._daily_stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"일일 통계 저장 실패: {e}")

    def _get_today_key(self) -> str:
        """오늘 날짜 키"""
        return datetime.now().strftime("%Y-%m-%d")

    def _increment_daily_stat(self, stat_name: str, increment: int = 1):
        """일일 통계 증가"""
        today = self._get_today_key()
        if today not in self._daily_stats:
            self._daily_stats[today] = {}
        self._daily_stats[today][stat_name] = self._daily_stats[today].get(stat_name, 0) + increment
        self._save_daily_stats()

    # -------------------------------------------------------------------------
    # 세션 관리
    # -------------------------------------------------------------------------

    def start_session(self, session_id: str, user_id: str = None, device_info: Dict[str, str] = None):
        """세션 시작"""
        session = SessionData(
            session_id=session_id,
            start_time=datetime.now(),
            user_id=user_id,
            device_info=device_info or {}
        )
        self._active_sessions[session_id] = session
        self._increment_daily_stat("sessions")

        # 이벤트 로그
        self._log_event(AnalyticsEvent(
            event_type=AnalyticsEventType.SESSION_START,
            session_id=session_id,
            user_id=user_id,
            properties=device_info or {}
        ))

        logger.info(f"Session started: {session_id}")

    def end_session(self, session_id: str):
        """세션 종료"""
        if session_id not in self._active_sessions:
            return

        session = self._active_sessions[session_id]
        session.end_time = datetime.now()
        session.total_duration_seconds = (session.end_time - session.start_time).total_seconds()

        # 세션 저장
        self._save_session(session)

        # 이벤트 로그
        self._log_event(AnalyticsEvent(
            event_type=AnalyticsEventType.SESSION_END,
            session_id=session_id,
            duration_seconds=session.total_duration_seconds,
            properties={"pages_viewed": len(session.pages_viewed)}
        ))

        # 세션 제거
        del self._active_sessions[session_id]

        logger.info(f"Session ended: {session_id} (duration: {session.total_duration_seconds:.1f}s)")

    def _save_session(self, session: SessionData):
        """세션 데이터 저장"""
        try:
            with open(SESSION_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(session.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"세션 저장 실패: {e}")

    # -------------------------------------------------------------------------
    # 이벤트 추적
    # -------------------------------------------------------------------------

    def track_page_view(self, page: str, session_id: str = None, user_id: str = None):
        """페이지 조회 추적"""
        session_id = session_id or self._get_current_session_id()

        # 세션에 페이지 추가
        if session_id and session_id in self._active_sessions:
            self._active_sessions[session_id].pages_viewed.append(page)

            # 이전 페이지 체류 시간 계산
            if session_id in self._page_view_times:
                duration = (datetime.now() - self._page_view_times[session_id]).total_seconds()
                self._log_event(AnalyticsEvent(
                    event_type=AnalyticsEventType.ENGAGEMENT,
                    session_id=session_id,
                    page=self._active_sessions[session_id].pages_viewed[-2] if len(self._active_sessions[session_id].pages_viewed) > 1 else None,
                    duration_seconds=duration
                ))

            self._page_view_times[session_id] = datetime.now()

        # 페이지 뷰 통계
        self._increment_daily_stat("page_views")
        self._increment_daily_stat(f"page_{page}")

        # 이벤트 로그
        self._log_event(AnalyticsEvent(
            event_type=AnalyticsEventType.PAGE_VIEW,
            session_id=session_id,
            user_id=user_id,
            page=page
        ))

    def track_action(self, action: str, page: str = None, properties: Dict[str, Any] = None, session_id: str = None):
        """사용자 액션 추적"""
        session_id = session_id or self._get_current_session_id()

        # 세션에 액션 추가
        if session_id and session_id in self._active_sessions:
            self._active_sessions[session_id].actions.append(action)

        # 액션 통계
        self._increment_daily_stat("actions")
        self._increment_daily_stat(f"action_{action}")

        # 이벤트 로그
        self._log_event(AnalyticsEvent(
            event_type=AnalyticsEventType.BUTTON_CLICK,
            session_id=session_id,
            page=page,
            action=action,
            properties=properties or {}
        ))

    def track_feature_usage(self, feature: str, properties: Dict[str, Any] = None, session_id: str = None):
        """기능 사용 추적"""
        session_id = session_id or self._get_current_session_id()

        self._increment_daily_stat("feature_usage")
        self._increment_daily_stat(f"feature_{feature}")

        self._log_event(AnalyticsEvent(
            event_type=AnalyticsEventType.FEATURE_USE,
            session_id=session_id,
            action=feature,
            properties=properties or {}
        ))

    def track_conversion(self, goal: ConversionGoal, properties: Dict[str, Any] = None, session_id: str = None):
        """전환 추적"""
        session_id = session_id or self._get_current_session_id()

        # 세션에 전환 추가
        if session_id and session_id in self._active_sessions:
            self._active_sessions[session_id].conversions.append(goal.value)

        # 전환 통계
        self._increment_daily_stat("conversions")
        self._increment_daily_stat(f"conversion_{goal.value}")

        self._log_event(AnalyticsEvent(
            event_type=AnalyticsEventType.CONVERSION,
            session_id=session_id,
            action=goal.value,
            properties=properties or {}
        ))

        logger.info(f"Conversion tracked: {goal.value}")

    def track_error(self, error_type: str, page: str = None, properties: Dict[str, Any] = None, session_id: str = None):
        """에러 추적"""
        session_id = session_id or self._get_current_session_id()

        self._increment_daily_stat("errors")
        self._increment_daily_stat(f"error_{error_type}")

        self._log_event(AnalyticsEvent(
            event_type=AnalyticsEventType.ERROR,
            session_id=session_id,
            page=page,
            action=error_type,
            properties=properties or {}
        ))

    def _log_event(self, event: AnalyticsEvent):
        """이벤트 로그 저장"""
        try:
            with open(USER_JOURNEY_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"이벤트 로그 저장 실패: {e}")

    def _get_current_session_id(self) -> Optional[str]:
        """현재 세션 ID 가져오기"""
        try:
            return st.session_state.get("session_id")
        except Exception:
            return None

    # -------------------------------------------------------------------------
    # 통계 조회
    # -------------------------------------------------------------------------

    def get_daily_stats(self, days: int = 7) -> Dict[str, Dict[str, int]]:
        """일일 통계 조회"""
        result = {}
        today = datetime.now()

        for i in range(days):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            result[date] = self._daily_stats.get(date, {})

        return result

    def get_page_stats(self, days: int = 7) -> Dict[str, int]:
        """페이지별 통계"""
        page_stats = defaultdict(int)

        for date, stats in self.get_daily_stats(days).items():
            for key, value in stats.items():
                if key.startswith("page_"):
                    page_name = key[5:]  # "page_" 제거
                    page_stats[page_name] += value

        return dict(sorted(page_stats.items(), key=lambda x: x[1], reverse=True))

    def get_feature_stats(self, days: int = 7) -> Dict[str, int]:
        """기능별 사용 통계"""
        feature_stats = defaultdict(int)

        for date, stats in self.get_daily_stats(days).items():
            for key, value in stats.items():
                if key.startswith("feature_"):
                    feature_name = key[8:]  # "feature_" 제거
                    feature_stats[feature_name] += value

        return dict(sorted(feature_stats.items(), key=lambda x: x[1], reverse=True))

    def get_conversion_stats(self, days: int = 7) -> Dict[str, int]:
        """전환 통계"""
        conversion_stats = defaultdict(int)

        for date, stats in self.get_daily_stats(days).items():
            for key, value in stats.items():
                if key.startswith("conversion_"):
                    conversion_name = key[11:]  # "conversion_" 제거
                    conversion_stats[conversion_name] += value

        return dict(sorted(conversion_stats.items(), key=lambda x: x[1], reverse=True))

    def get_summary_stats(self, days: int = 7) -> Dict[str, Any]:
        """요약 통계"""
        daily_stats = self.get_daily_stats(days)

        total_sessions = sum(s.get("sessions", 0) for s in daily_stats.values())
        total_page_views = sum(s.get("page_views", 0) for s in daily_stats.values())
        total_actions = sum(s.get("actions", 0) for s in daily_stats.values())
        total_conversions = sum(s.get("conversions", 0) for s in daily_stats.values())
        total_errors = sum(s.get("errors", 0) for s in daily_stats.values())

        # 평균 계산
        avg_pages_per_session = total_page_views / max(total_sessions, 1)
        avg_actions_per_session = total_actions / max(total_sessions, 1)
        conversion_rate = total_conversions / max(total_sessions, 1) * 100

        return {
            "period_days": days,
            "total_sessions": total_sessions,
            "total_page_views": total_page_views,
            "total_actions": total_actions,
            "total_conversions": total_conversions,
            "total_errors": total_errors,
            "avg_pages_per_session": round(avg_pages_per_session, 2),
            "avg_actions_per_session": round(avg_actions_per_session, 2),
            "conversion_rate_percent": round(conversion_rate, 2),
            "error_rate_percent": round(total_errors / max(total_sessions, 1) * 100, 2),
            "top_pages": self.get_page_stats(days),
            "top_features": self.get_feature_stats(days),
            "conversions": self.get_conversion_stats(days)
        }

    def get_active_sessions_count(self) -> int:
        """활성 세션 수"""
        return len(self._active_sessions)

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """활성 세션 목록"""
        return [s.to_dict() for s in self._active_sessions.values()]


# =============================================================================
# 퍼널 분석
# =============================================================================

class FunnelAnalyzer:
    """퍼널 분석기"""

    def __init__(self):
        self._funnels: Dict[str, List[str]] = {}

    def define_funnel(self, name: str, steps: List[str]):
        """퍼널 정의"""
        self._funnels[name] = steps

    def analyze_funnel(self, name: str, days: int = 7) -> Dict[str, Any]:
        """퍼널 분석"""
        if name not in self._funnels:
            return {"error": f"Funnel '{name}' not defined"}

        steps = self._funnels[name]
        analytics = get_analytics()
        daily_stats = analytics.get_daily_stats(days)

        # 각 단계별 카운트
        step_counts = []
        for step in steps:
            count = sum(s.get(f"page_{step}", 0) + s.get(f"action_{step}", 0) for s in daily_stats.values())
            step_counts.append(count)

        # 전환율 계산
        conversion_rates = []
        for i in range(len(step_counts)):
            if i == 0:
                conversion_rates.append(100.0)
            else:
                prev_count = step_counts[i - 1]
                curr_count = step_counts[i]
                rate = (curr_count / max(prev_count, 1)) * 100
                conversion_rates.append(round(rate, 2))

        return {
            "funnel_name": name,
            "steps": steps,
            "step_counts": step_counts,
            "conversion_rates": conversion_rates,
            "total_conversion": round(step_counts[-1] / max(step_counts[0], 1) * 100, 2) if step_counts else 0,
            "period_days": days
        }


# =============================================================================
# A/B 테스트
# =============================================================================

class ABTestManager:
    """A/B 테스트 관리자"""

    def __init__(self):
        self._tests: Dict[str, Dict[str, Any]] = {}
        self._assignments: Dict[str, Dict[str, str]] = {}  # session_id -> {test_name: variant}

    def create_test(self, name: str, variants: List[str], weights: List[float] = None):
        """A/B 테스트 생성"""
        if weights is None:
            weights = [1.0 / len(variants)] * len(variants)

        self._tests[name] = {
            "variants": variants,
            "weights": weights,
            "created_at": datetime.now().isoformat(),
            "results": {v: {"impressions": 0, "conversions": 0} for v in variants}
        }

    def get_variant(self, test_name: str, session_id: str) -> Optional[str]:
        """세션에 할당된 변형 반환 (없으면 새로 할당)"""
        import random

        if test_name not in self._tests:
            return None

        # 이미 할당된 경우
        if session_id in self._assignments and test_name in self._assignments[session_id]:
            return self._assignments[session_id][test_name]

        # 새로 할당
        test = self._tests[test_name]
        variant = random.choices(test["variants"], weights=test["weights"])[0]

        if session_id not in self._assignments:
            self._assignments[session_id] = {}
        self._assignments[session_id][test_name] = variant

        # 노출 기록
        test["results"][variant]["impressions"] += 1

        return variant

    def record_conversion(self, test_name: str, session_id: str):
        """전환 기록"""
        if test_name not in self._tests:
            return

        if session_id in self._assignments and test_name in self._assignments[session_id]:
            variant = self._assignments[session_id][test_name]
            self._tests[test_name]["results"][variant]["conversions"] += 1

    def get_test_results(self, test_name: str) -> Dict[str, Any]:
        """테스트 결과 조회"""
        if test_name not in self._tests:
            return {"error": f"Test '{test_name}' not found"}

        test = self._tests[test_name]
        results = {}

        for variant, data in test["results"].items():
            impressions = data["impressions"]
            conversions = data["conversions"]
            rate = (conversions / max(impressions, 1)) * 100

            results[variant] = {
                "impressions": impressions,
                "conversions": conversions,
                "conversion_rate": round(rate, 2)
            }

        return {
            "test_name": test_name,
            "variants": test["variants"],
            "created_at": test["created_at"],
            "results": results
        }


# =============================================================================
# 전역 인스턴스
# =============================================================================

_analytics = AnalyticsSystem()
_funnel_analyzer = FunnelAnalyzer()
_ab_test_manager = ABTestManager()


def get_analytics() -> AnalyticsSystem:
    """분석 시스템 인스턴스 반환"""
    return _analytics


def get_funnel_analyzer() -> FunnelAnalyzer:
    """퍼널 분석기 인스턴스 반환"""
    return _funnel_analyzer


def get_ab_test_manager() -> ABTestManager:
    """A/B 테스트 관리자 인스턴스 반환"""
    return _ab_test_manager


# =============================================================================
# 편의 함수
# =============================================================================

def track_page_view(page: str, session_id: str = None, user_id: str = None):
    """페이지 뷰 추적"""
    _analytics.track_page_view(page, session_id, user_id)


def track_action(action: str, page: str = None, properties: Dict[str, Any] = None):
    """액션 추적"""
    _analytics.track_action(action, page, properties)


def track_feature_usage(feature: str, properties: Dict[str, Any] = None):
    """기능 사용 추적"""
    _analytics.track_feature_usage(feature, properties)


def track_conversion(goal: ConversionGoal, properties: Dict[str, Any] = None):
    """전환 추적"""
    _analytics.track_conversion(goal, properties)


def get_summary_stats(days: int = 7) -> Dict[str, Any]:
    """요약 통계 조회"""
    return _analytics.get_summary_stats(days)


# =============================================================================
# Streamlit 세션 초기화
# =============================================================================

def init_analytics_session():
    """분석 세션 초기화 (Streamlit 페이지에서 호출)"""
    if "analytics_session_initialized" not in st.session_state:
        import secrets
        session_id = st.session_state.get("session_id") or secrets.token_urlsafe(16)
        st.session_state.session_id = session_id
        st.session_state.analytics_session_initialized = True

        _analytics.start_session(session_id)

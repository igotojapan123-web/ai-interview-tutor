# monitoring.py
# FlyReady Lab - Enterprise Monitoring System
# Stage 4: 대기업 수준 모니터링 및 분석
# Samsung-level quality implementation

import streamlit as st
import logging
import time
import threading
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import deque
import traceback
import hashlib

from logging_config import get_logger

logger = get_logger(__name__)

# =============================================================================
# 경로 설정
# =============================================================================

PROJECT_ROOT = Path(__file__).parent
LOGS_DIR = PROJECT_ROOT / "logs"
MONITORING_DIR = LOGS_DIR / "monitoring"
METRICS_DIR = PROJECT_ROOT / "metrics"

# 디렉토리 생성
for dir_path in [LOGS_DIR, MONITORING_DIR, METRICS_DIR]:
    dir_path.mkdir(exist_ok=True)

# Sentry DSN (환경 변수에서 가져오기)
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")

# 파일 경로
ERROR_LOG_FILE = MONITORING_DIR / "errors.json"
METRICS_LOG_FILE = MONITORING_DIR / "metrics.json"
EVENTS_LOG_FILE = MONITORING_DIR / "events.jsonl"


# =============================================================================
# 이벤트 타입 정의
# =============================================================================

class EventType(Enum):
    """모니터링 이벤트 유형"""
    # 에러 관련
    ERROR = "error"
    WARNING = "warning"
    CRITICAL = "critical"

    # 성능 관련
    PERFORMANCE = "performance"
    SLOW_REQUEST = "slow_request"
    MEMORY_HIGH = "memory_high"

    # 사용자 활동
    PAGE_VIEW = "page_view"
    USER_ACTION = "user_action"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    FEATURE_USAGE = "feature_usage"

    # 시스템 관련
    SYSTEM_INFO = "system_info"
    API_CALL = "api_call"
    API_ERROR = "api_error"
    API_LATENCY = "api_latency"

    # 보안 관련
    SECURITY_ALERT = "security_alert"
    AUTH_FAILURE = "auth_failure"
    RATE_LIMIT = "rate_limit"


class AlertLevel(Enum):
    """알림 레벨"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# =============================================================================
# 이벤트 데이터 구조
# =============================================================================

@dataclass
class MonitoringEvent:
    """모니터링 이벤트 데이터"""
    event_type: EventType
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    level: AlertLevel = AlertLevel.INFO
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    page: Optional[str] = None
    duration_ms: Optional[float] = None
    stack_trace: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "event_type": self.event_type.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "context": self.context,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "page": self.page,
            "duration_ms": self.duration_ms,
            "stack_trace": self.stack_trace,
            "tags": self.tags
        }

    def get_fingerprint(self) -> str:
        """이벤트 고유 식별자 (중복 감지용)"""
        content = f"{self.event_type.value}:{self.message}:{self.page}"
        return hashlib.md5(content.encode()).hexdigest()[:16]


@dataclass
class PerformanceMetric:
    """성능 메트릭 데이터"""
    name: str
    value: float
    unit: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags
        }


# =============================================================================
# 메트릭스 컬렉터
# =============================================================================

class MetricsCollector:
    """성능 메트릭스 수집기 (인메모리 + 파일 저장)"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._metrics: Dict[str, deque] = {}
        self._lock = threading.Lock()

    def record(self, name: str, value: float, unit: str = "", tags: Dict[str, str] = None):
        """메트릭 기록"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            tags=tags or {}
        )

        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = deque(maxlen=self.max_history)
            self._metrics[name].append(metric)

        # 파일에도 저장 (비동기)
        self._save_to_file(metric)

    def _save_to_file(self, metric: PerformanceMetric):
        """메트릭을 파일에 저장"""
        try:
            metrics = []
            if METRICS_LOG_FILE.exists():
                with open(METRICS_LOG_FILE, "r", encoding="utf-8") as f:
                    metrics = json.load(f)

            metrics.append(metric.to_dict())

            # 최근 10000개만 유지
            if len(metrics) > 10000:
                metrics = metrics[-10000:]

            with open(METRICS_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(metrics, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"메트릭 저장 실패: {e}")

    def get_latest(self, name: str) -> Optional[PerformanceMetric]:
        """최신 메트릭 조회"""
        with self._lock:
            if name in self._metrics and self._metrics[name]:
                return self._metrics[name][-1]
        return None

    def get_history(self, name: str, limit: int = 100) -> List[PerformanceMetric]:
        """메트릭 히스토리 조회"""
        with self._lock:
            if name not in self._metrics:
                return []
            return list(self._metrics[name])[-limit:]

    def get_average(self, name: str, window_minutes: int = 5) -> Optional[float]:
        """평균값 계산"""
        cutoff = datetime.now() - timedelta(minutes=window_minutes)

        with self._lock:
            if name not in self._metrics:
                return None

            values = [
                m.value for m in self._metrics[name]
                if m.timestamp > cutoff
            ]

            return sum(values) / len(values) if values else None

    def get_percentile(self, name: str, percentile: float, window_minutes: int = 5) -> Optional[float]:
        """백분위수 계산 (P50, P90, P99 등)"""
        cutoff = datetime.now() - timedelta(minutes=window_minutes)

        with self._lock:
            if name not in self._metrics:
                return None

            values = sorted([
                m.value for m in self._metrics[name]
                if m.timestamp > cutoff
            ])

            if not values:
                return None

            index = int(len(values) * percentile / 100)
            return values[min(index, len(values) - 1)]

    def get_all_metrics_summary(self) -> Dict[str, Any]:
        """모든 메트릭 요약"""
        summary = {}

        with self._lock:
            for name, metrics in self._metrics.items():
                if not metrics:
                    continue

                values = [m.value for m in metrics]
                summary[name] = {
                    "count": len(values),
                    "latest": values[-1] if values else None,
                    "min": min(values) if values else None,
                    "max": max(values) if values else None,
                    "avg": round(sum(values) / len(values), 2) if values else None,
                    "unit": metrics[-1].unit if metrics else ""
                }

        return summary


# =============================================================================
# 알림 관리자
# =============================================================================

class AlertManager:
    """알림 관리 시스템"""

    def __init__(self, cooldown_minutes: int = 5, max_alerts: int = 100):
        self.cooldown_minutes = cooldown_minutes
        self._alerts: deque = deque(maxlen=max_alerts)
        self._last_alert_time: Dict[str, datetime] = {}
        self._handlers: List[Callable[[MonitoringEvent], None]] = []
        self._lock = threading.Lock()

    def add_handler(self, handler: Callable[[MonitoringEvent], None]):
        """알림 핸들러 등록"""
        self._handlers.append(handler)

    def send_alert(self, event: MonitoringEvent) -> bool:
        """알림 발송 (쿨다운 체크 후)"""
        fingerprint = event.get_fingerprint()

        with self._lock:
            # 쿨다운 체크
            if fingerprint in self._last_alert_time:
                elapsed = datetime.now() - self._last_alert_time[fingerprint]
                if elapsed < timedelta(minutes=self.cooldown_minutes):
                    return False  # 쿨다운 중

            self._last_alert_time[fingerprint] = datetime.now()
            self._alerts.append(event)

        # 핸들러 실행
        for handler in self._handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")

        return True

    def get_recent_alerts(self, limit: int = 20) -> List[MonitoringEvent]:
        """최근 알림 조회"""
        with self._lock:
            return list(self._alerts)[-limit:]

    def get_alert_count(self, hours: int = 24) -> int:
        """기간 내 알림 수"""
        cutoff = datetime.now() - timedelta(hours=hours)
        with self._lock:
            return len([a for a in self._alerts if a.timestamp > cutoff])


# =============================================================================
# 중앙 모니터링 시스템 (싱글톤)
# =============================================================================

class MonitoringSystem:
    """중앙 집중식 모니터링 시스템"""

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
        self._events: deque = deque(maxlen=10000)
        self._metrics = MetricsCollector()
        self._alerts = AlertManager()
        self._start_time = datetime.now()
        self._error_count = 0
        self._request_count = 0
        self._page_views: Dict[str, int] = {}

        # Sentry 초기화
        self._init_sentry()

        # 기본 알림 핸들러 등록
        self._alerts.add_handler(self._default_alert_handler)

        logger.info("MonitoringSystem initialized (Enterprise Level)")

    def _init_sentry(self):
        """Sentry 초기화"""
        if SENTRY_DSN:
            try:
                import sentry_sdk
                sentry_sdk.init(
                    dsn=SENTRY_DSN,
                    traces_sample_rate=0.1,
                    profiles_sample_rate=0.1,
                    environment=os.environ.get("ENV", "development")
                )
                logger.info("Sentry 모니터링 활성화됨")
            except ImportError:
                logger.warning("sentry-sdk 패키지가 설치되지 않음")
            except Exception as e:
                logger.error(f"Sentry 초기화 실패: {e}")

    def _default_alert_handler(self, event: MonitoringEvent):
        """기본 알림 핸들러 - 로그 기록"""
        log_level = {
            AlertLevel.DEBUG: logging.DEBUG,
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }.get(event.level, logging.INFO)

        logger.log(log_level, f"[ALERT] {event.event_type.value}: {event.message}")

    # -------------------------------------------------------------------------
    # 이벤트 기록
    # -------------------------------------------------------------------------

    def log_event(self, event: MonitoringEvent):
        """이벤트 기록"""
        self._events.append(event)
        self._request_count += 1

        # 페이지 뷰 카운트
        if event.event_type == EventType.PAGE_VIEW and event.page:
            self._page_views[event.page] = self._page_views.get(event.page, 0) + 1

        # 에러 카운트
        if event.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
            self._error_count += 1
            # 알림 발송
            self._alerts.send_alert(event)

        # 파일 저장 (비동기)
        threading.Thread(target=self._save_event, args=(event,), daemon=True).start()

        # Sentry 전송 (에러인 경우)
        if event.level in [AlertLevel.ERROR, AlertLevel.CRITICAL] and SENTRY_DSN:
            self._send_to_sentry(event)

    def _save_event(self, event: MonitoringEvent):
        """이벤트 파일 저장 (JSONL 형식)"""
        try:
            with open(EVENTS_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to save event: {e}")

    def _send_to_sentry(self, event: MonitoringEvent):
        """Sentry에 에러 전송"""
        try:
            import sentry_sdk
            with sentry_sdk.push_scope() as scope:
                if event.user_id:
                    scope.set_user({"id": event.user_id})
                if event.page:
                    scope.set_tag("page", event.page)
                if event.session_id:
                    scope.set_tag("session_id", event.session_id)
                for key, value in event.context.items():
                    scope.set_extra(key, value)
                for key, value in event.tags.items():
                    scope.set_tag(key, value)

                if event.stack_trace:
                    sentry_sdk.capture_message(
                        f"{event.event_type.value}: {event.message}",
                        level=event.level.value
                    )
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # 편의 메서드
    # -------------------------------------------------------------------------

    def track_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        page: str = None,
        user_id: str = None
    ):
        """에러 추적"""
        event = MonitoringEvent(
            event_type=EventType.ERROR,
            message=str(error),
            level=AlertLevel.ERROR,
            context=context or {},
            page=page,
            user_id=user_id,
            stack_trace=traceback.format_exc()
        )
        self.log_event(event)

        # 에러 파일에도 저장
        self._save_error(error, context, page, user_id)

    def _save_error(self, error: Exception, context: Dict, page: str, user_id: str):
        """에러를 별도 파일에 저장"""
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {},
            "user_id": user_id,
            "page": page,
        }

        try:
            errors = []
            if ERROR_LOG_FILE.exists():
                with open(ERROR_LOG_FILE, "r", encoding="utf-8") as f:
                    errors = json.load(f)

            errors.append(error_data)

            # 최근 1000개만 유지
            if len(errors) > 1000:
                errors = errors[-1000:]

            with open(ERROR_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(errors, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"에러 로깅 실패: {e}")

    def track_page_view(self, page: str, user_id: str = None):
        """페이지 조회 추적"""
        session_id = None
        try:
            session_id = st.session_state.get("session_id")
        except Exception:
            pass

        event = MonitoringEvent(
            event_type=EventType.PAGE_VIEW,
            message=f"Page viewed: {page}",
            page=page,
            user_id=user_id,
            session_id=session_id
        )
        self.log_event(event)

        # 메트릭도 기록
        self._metrics.record("page_view", 1, "", {"page": page})

    def track_feature_usage(self, feature: str, user_id: str = None):
        """기능 사용 추적"""
        event = MonitoringEvent(
            event_type=EventType.FEATURE_USAGE,
            message=f"Feature used: {feature}",
            context={"feature": feature},
            user_id=user_id
        )
        self.log_event(event)
        self._metrics.record("feature_usage", 1, "", {"feature": feature})

    def track_api_latency(self, api_name: str, latency_ms: float, success: bool = True):
        """API 응답 시간 추적"""
        event_type = EventType.API_CALL if success else EventType.API_ERROR
        level = AlertLevel.INFO if success else AlertLevel.WARNING

        event = MonitoringEvent(
            event_type=event_type,
            message=f"API call: {api_name}",
            level=level,
            duration_ms=latency_ms,
            context={"api": api_name, "success": success}
        )
        self.log_event(event)
        self._metrics.record("api_latency", latency_ms, "ms", {"api": api_name})

        # 느린 API 감지 (3초 이상)
        if latency_ms > 3000:
            self._alerts.send_alert(MonitoringEvent(
                event_type=EventType.SLOW_REQUEST,
                message=f"Slow API: {api_name} ({latency_ms:.0f}ms)",
                level=AlertLevel.WARNING,
                duration_ms=latency_ms
            ))

    def track_api_error(self, api_name: str, error_type: str):
        """API 에러 추적"""
        event = MonitoringEvent(
            event_type=EventType.API_ERROR,
            message=f"API error: {api_name} - {error_type}",
            level=AlertLevel.WARNING,
            context={"api": api_name, "error_type": error_type}
        )
        self.log_event(event)
        self._metrics.record("api_error", 1, "", {"api": api_name, "error_type": error_type})

    def track_user_action(self, action: str, details: Dict[str, Any] = None, page: str = None):
        """사용자 액션 추적"""
        event = MonitoringEvent(
            event_type=EventType.USER_ACTION,
            message=action,
            context=details or {},
            page=page
        )
        self.log_event(event)

    def track_security_alert(self, alert_type: str, details: Dict[str, Any] = None):
        """보안 알림 추적"""
        event = MonitoringEvent(
            event_type=EventType.SECURITY_ALERT,
            message=f"Security alert: {alert_type}",
            level=AlertLevel.WARNING,
            context=details or {}
        )
        self.log_event(event)

    # -------------------------------------------------------------------------
    # 메트릭 기록
    # -------------------------------------------------------------------------

    def record_metric(self, name: str, value: float, unit: str = "", tags: Dict[str, str] = None):
        """성능 메트릭 기록"""
        self._metrics.record(name, value, unit, tags)

    def get_metrics(self) -> MetricsCollector:
        """메트릭스 컬렉터 반환"""
        return self._metrics

    # -------------------------------------------------------------------------
    # 타이밍 컨텍스트 매니저
    # -------------------------------------------------------------------------

    class Timer:
        """실행 시간 측정 컨텍스트 매니저"""

        def __init__(self, monitoring: 'MonitoringSystem', name: str, tags: Dict[str, str] = None):
            self.monitoring = monitoring
            self.name = name
            self.tags = tags or {}
            self.start_time = None
            self.duration_ms = None

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.duration_ms = (time.time() - self.start_time) * 1000
            self.monitoring.record_metric(self.name, self.duration_ms, "ms", self.tags)

            # 느린 작업 감지
            if self.duration_ms > 3000:
                self.monitoring._alerts.send_alert(MonitoringEvent(
                    event_type=EventType.SLOW_REQUEST,
                    message=f"Slow operation: {self.name}",
                    level=AlertLevel.WARNING,
                    duration_ms=self.duration_ms,
                    context=self.tags
                ))

            return False

    def timer(self, name: str, tags: Dict[str, str] = None) -> Timer:
        """타이머 생성"""
        return self.Timer(self, name, tags)

    # -------------------------------------------------------------------------
    # 시스템 상태 및 통계
    # -------------------------------------------------------------------------

    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        uptime = datetime.now() - self._start_time
        error_rate = self._error_count / max(self._request_count, 1) * 100

        return {
            "status": "healthy" if error_rate < 5 else "degraded" if error_rate < 20 else "unhealthy",
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_formatted": str(uptime).split('.')[0],
            "start_time": self._start_time.isoformat(),
            "total_events": len(self._events),
            "total_requests": self._request_count,
            "error_count": self._error_count,
            "error_rate_percent": round(error_rate, 2),
            "alert_count_24h": self._alerts.get_alert_count(24),
            "top_pages": dict(sorted(self._page_views.items(), key=lambda x: x[1], reverse=True)[:10]),
            "metrics_summary": self._metrics.get_all_metrics_summary()
        }

    def get_recent_events(
        self,
        limit: int = 50,
        event_type: EventType = None,
        level: AlertLevel = None
    ) -> List[Dict[str, Any]]:
        """최근 이벤트 조회"""
        events = list(self._events)

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if level:
            events = [e for e in events if e.level == level]

        return [e.to_dict() for e in events[-limit:]]

    def get_error_summary(self, days: int = 7) -> Dict[str, Any]:
        """에러 요약"""
        cutoff = datetime.now() - timedelta(days=days)

        errors = [
            e for e in self._events
            if e.event_type == EventType.ERROR and e.timestamp > cutoff
        ]

        # 에러 그룹화
        by_type: Dict[str, int] = {}
        by_page: Dict[str, int] = {}

        for error in errors:
            error_type = error.context.get("error_type", "Unknown")
            page = error.page or "Unknown"

            by_type[error_type] = by_type.get(error_type, 0) + 1
            by_page[page] = by_page.get(page, 0) + 1

        return {
            "total_errors": len(errors),
            "by_type": dict(sorted(by_type.items(), key=lambda x: x[1], reverse=True)),
            "by_page": dict(sorted(by_page.items(), key=lambda x: x[1], reverse=True)),
            "period_days": days
        }

    def get_alerts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """최근 알림 조회"""
        return [e.to_dict() for e in self._alerts.get_recent_alerts(limit)]

    def get_metrics_summary(self, metric_name: str, days: int = 7) -> Dict[str, Any]:
        """특정 메트릭 요약"""
        cutoff = datetime.now() - timedelta(days=days)
        history = self._metrics.get_history(metric_name, 10000)

        filtered = [m for m in history if m.timestamp > cutoff]

        if not filtered:
            return {"count": 0, "sum": 0, "avg": 0, "min": None, "max": None}

        values = [m.value for m in filtered]
        return {
            "count": len(values),
            "sum": sum(values),
            "avg": round(sum(values) / len(values), 2),
            "min": min(values),
            "max": max(values),
            "p50": self._metrics.get_percentile(metric_name, 50),
            "p90": self._metrics.get_percentile(metric_name, 90),
            "p99": self._metrics.get_percentile(metric_name, 99)
        }


# =============================================================================
# 전역 인스턴스
# =============================================================================

_monitoring = MonitoringSystem()


def get_monitoring() -> MonitoringSystem:
    """모니터링 시스템 인스턴스 반환"""
    return _monitoring


# =============================================================================
# 편의 함수 (기존 호환성 유지)
# =============================================================================

def init_monitoring():
    """모니터링 시스템 초기화"""
    return get_monitoring()


def track_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    page: Optional[str] = None
):
    """에러 추적"""
    _monitoring.track_error(error, context, page, user_id)


def track_metric(name: str, value: float, tags: Optional[Dict[str, str]] = None):
    """메트릭 수집"""
    _monitoring.record_metric(name, value, "", tags)


def track_page_view(page: str, user_id: Optional[str] = None):
    """페이지 조회 추적"""
    _monitoring.track_page_view(page, user_id)


def track_feature_usage(feature: str, user_id: Optional[str] = None):
    """기능 사용 추적"""
    _monitoring.track_feature_usage(feature, user_id)


def track_api_latency(api_name: str, latency_ms: float):
    """API 응답 시간 추적"""
    _monitoring.track_api_latency(api_name, latency_ms)


def track_api_error(api_name: str, error_type: str):
    """API 에러 추적"""
    _monitoring.track_api_error(api_name, error_type)


def get_error_summary(days: int = 7) -> Dict[str, Any]:
    """에러 요약 조회"""
    return _monitoring.get_error_summary(days)


def get_metrics_summary(metric_name: str, days: int = 7) -> Dict[str, Any]:
    """메트릭 요약 조회"""
    return _monitoring.get_metrics_summary(metric_name, days)


def health_check() -> Dict[str, Any]:
    """시스템 상태 체크"""
    from env_config import check_openai_key, GOOGLE_TTS_API_KEY

    status = _monitoring.get_system_status()

    # 추가 상태 체크
    checks = {}

    # OpenAI API 체크
    try:
        is_valid, msg = check_openai_key()
        checks["openai_api"] = {
            "status": "ok" if is_valid else "error",
            "message": msg
        }
    except Exception:
        checks["openai_api"] = {"status": "unknown", "message": "확인 불가"}

    # Google TTS 체크
    try:
        checks["google_tts"] = {
            "status": "ok" if GOOGLE_TTS_API_KEY else "warning",
            "message": "설정됨" if GOOGLE_TTS_API_KEY else "미설정"
        }
    except Exception:
        checks["google_tts"] = {"status": "unknown", "message": "확인 불가"}

    # 디스크 공간 체크
    try:
        import shutil
        total, used, free = shutil.disk_usage(str(MONITORING_DIR))
        free_gb = free / (1024 ** 3)
        checks["disk_space"] = {
            "status": "ok" if free_gb > 1 else "warning",
            "message": f"{free_gb:.1f}GB 남음"
        }
    except Exception:
        checks["disk_space"] = {"status": "unknown", "message": "확인 불가"}

    status["checks"] = checks

    # 전체 상태 재판단
    if any(c.get("status") == "error" for c in checks.values()):
        status["status"] = "unhealthy"
    elif any(c.get("status") == "warning" for c in checks.values()):
        status["status"] = "degraded"

    return status


# =============================================================================
# 데코레이터
# =============================================================================

def monitored(name: str = None, log_errors: bool = True):
    """모니터링 데코레이터"""
    def decorator(func: Callable):
        from functools import wraps
        metric_name = name or func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            with _monitoring.timer(metric_name):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if log_errors:
                        track_error(e, context={"function": func.__name__})
                    raise

        return wrapper
    return decorator


def track_api_call(endpoint: str = None):
    """API 호출 추적 데코레이터"""
    def decorator(func: Callable):
        from functools import wraps
        api_endpoint = endpoint or func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                _monitoring.track_api_latency(api_endpoint, duration, True)
                return result
            except Exception as e:
                duration = (time.time() - start) * 1000
                _monitoring.track_api_latency(api_endpoint, duration, False)
                _monitoring.track_api_error(api_endpoint, type(e).__name__)
                raise

        return wrapper
    return decorator


# =============================================================================
# 세션 초기화
# =============================================================================

def init_monitoring_session():
    """모니터링 세션 초기화 (Streamlit 페이지에서 호출)"""
    if "monitoring_session_initialized" not in st.session_state:
        import secrets
        st.session_state.monitoring_session_initialized = True
        st.session_state.session_id = secrets.token_urlsafe(16)
        st.session_state.session_start = datetime.now().isoformat()

        _monitoring.log_event(MonitoringEvent(
            event_type=EventType.SESSION_START,
            message="New session started",
            session_id=st.session_state.session_id
        ))

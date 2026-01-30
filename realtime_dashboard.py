# realtime_dashboard.py
# 실시간 사용자 활동 모니터링 대시보드

import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict

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
METRICS_FILE = DATA_DIR / "realtime_metrics.json"

# 메트릭 보관 기간
METRICS_RETENTION_HOURS = 24
AGGREGATION_INTERVAL_SECONDS = 60  # 1분 단위 집계


# ============================================================
# 실시간 메트릭 수집기
# ============================================================

class RealtimeMetrics:
    """실시간 메트릭 수집 및 관리"""

    def __init__(self):
        self._lock = threading.Lock()
        self._active_users: Dict[str, datetime] = {}  # {user_id: last_activity}
        self._page_views: Dict[str, int] = defaultdict(int)  # {page: count}
        self._api_calls: Dict[str, int] = defaultdict(int)  # {api_type: count}
        self._events: List[Dict[str, Any]] = []  # 최근 이벤트
        self._errors: List[Dict[str, Any]] = []  # 최근 에러
        self._hourly_stats: Dict[str, Dict[str, Any]] = {}  # 시간별 통계

        # 파일에서 로드
        self._load_metrics()

    def _load_metrics(self) -> None:
        """저장된 메트릭 로드"""
        try:
            if METRICS_FILE.exists():
                with open(METRICS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._hourly_stats = data.get("hourly_stats", {})
        except Exception as e:
            logger.error(f"메트릭 로드 실패: {e}")

    def _save_metrics(self) -> None:
        """메트릭 저장"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(METRICS_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    "hourly_stats": self._hourly_stats,
                    "last_updated": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"메트릭 저장 실패: {e}")

    # -------------------------------------------------------------------------
    # 이벤트 기록
    # -------------------------------------------------------------------------

    def record_user_activity(self, user_id: str, page: str = None) -> None:
        """사용자 활동 기록"""
        with self._lock:
            now = datetime.now()
            self._active_users[user_id] = now

            if page:
                self._page_views[page] += 1

            # 이벤트 기록
            self._events.append({
                "type": "activity",
                "user_id": user_id[:8] + "...",
                "page": page,
                "timestamp": now.isoformat()
            })

            # 이벤트 최대 100개 유지
            if len(self._events) > 100:
                self._events = self._events[-100:]

    def record_api_call(self, api_type: str, success: bool = True, duration_ms: float = None) -> None:
        """API 호출 기록"""
        with self._lock:
            self._api_calls[api_type] += 1

            self._events.append({
                "type": "api_call",
                "api": api_type,
                "success": success,
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat()
            })

    def record_error(self, error_type: str, message: str, page: str = None) -> None:
        """에러 기록"""
        with self._lock:
            self._errors.append({
                "type": error_type,
                "message": message[:200],
                "page": page,
                "timestamp": datetime.now().isoformat()
            })

            # 에러 최대 50개 유지
            if len(self._errors) > 50:
                self._errors = self._errors[-50:]

    def record_practice_complete(self, practice_type: str, score: float = None) -> None:
        """연습 완료 기록"""
        with self._lock:
            self._events.append({
                "type": "practice_complete",
                "practice_type": practice_type,
                "score": score,
                "timestamp": datetime.now().isoformat()
            })

    # -------------------------------------------------------------------------
    # 통계 조회
    # -------------------------------------------------------------------------

    def get_active_users_count(self, minutes: int = 5) -> int:
        """최근 N분 내 활성 사용자 수"""
        with self._lock:
            cutoff = datetime.now() - timedelta(minutes=minutes)
            return sum(1 for t in self._active_users.values() if t > cutoff)

    def get_page_views(self) -> Dict[str, int]:
        """페이지별 조회수"""
        with self._lock:
            return dict(self._page_views)

    def get_api_stats(self) -> Dict[str, int]:
        """API 호출 통계"""
        with self._lock:
            return dict(self._api_calls)

    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """최근 이벤트"""
        with self._lock:
            return self._events[-limit:][::-1]  # 최신순

    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 에러"""
        with self._lock:
            return self._errors[-limit:][::-1]

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """대시보드 요약 데이터"""
        with self._lock:
            now = datetime.now()

            # 활성 사용자
            active_5min = sum(1 for t in self._active_users.values()
                            if t > now - timedelta(minutes=5))
            active_1hour = sum(1 for t in self._active_users.values()
                              if t > now - timedelta(hours=1))

            # API 호출 총계
            total_api_calls = sum(self._api_calls.values())

            # 에러율
            recent_events = [e for e in self._events if e.get("type") == "api_call"]
            error_count = sum(1 for e in recent_events if not e.get("success", True))
            error_rate = (error_count / len(recent_events) * 100) if recent_events else 0

            # 인기 페이지 (상위 5개)
            top_pages = sorted(
                self._page_views.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]

            return {
                "timestamp": now.isoformat(),
                "active_users": {
                    "5min": active_5min,
                    "1hour": active_1hour,
                    "total_sessions": len(self._active_users)
                },
                "api": {
                    "total_calls": total_api_calls,
                    "by_type": dict(self._api_calls),
                    "error_rate": f"{error_rate:.1f}%"
                },
                "pages": {
                    "total_views": sum(self._page_views.values()),
                    "top_pages": top_pages
                },
                "recent_errors": len(self._errors),
                "system_status": "healthy" if error_rate < 5 else "warning" if error_rate < 10 else "critical"
            }

    # -------------------------------------------------------------------------
    # 시간별 집계
    # -------------------------------------------------------------------------

    def aggregate_hourly(self) -> None:
        """시간별 통계 집계"""
        with self._lock:
            hour_key = datetime.now().strftime("%Y-%m-%d %H:00")

            self._hourly_stats[hour_key] = {
                "active_users": len(self._active_users),
                "page_views": sum(self._page_views.values()),
                "api_calls": sum(self._api_calls.values()),
                "errors": len(self._errors),
                "timestamp": datetime.now().isoformat()
            }

            # 24시간 이전 데이터 삭제
            cutoff = (datetime.now() - timedelta(hours=METRICS_RETENTION_HOURS)).strftime("%Y-%m-%d %H:00")
            self._hourly_stats = {
                k: v for k, v in self._hourly_stats.items() if k >= cutoff
            }

            self._save_metrics()

    def get_hourly_trend(self, hours: int = 24) -> List[Dict[str, Any]]:
        """시간별 트렌드 데이터"""
        with self._lock:
            sorted_stats = sorted(self._hourly_stats.items(), key=lambda x: x[0])
            return [{"hour": k, **v} for k, v in sorted_stats[-hours:]]

    def reset_daily_counters(self) -> None:
        """일일 카운터 리셋"""
        with self._lock:
            self._page_views.clear()
            self._api_calls.clear()
            self._events.clear()
            self._errors.clear()

            # 오래된 활성 사용자 제거
            cutoff = datetime.now() - timedelta(hours=1)
            self._active_users = {
                uid: t for uid, t in self._active_users.items() if t > cutoff
            }

            logger.info("일일 카운터 리셋 완료")


# 전역 인스턴스
metrics = RealtimeMetrics()


# ============================================================
# 간편 함수
# ============================================================

def track_activity(user_id: str, page: str = None) -> None:
    """사용자 활동 추적"""
    metrics.record_user_activity(user_id, page)


def track_api_call(api_type: str, success: bool = True, duration_ms: float = None) -> None:
    """API 호출 추적"""
    metrics.record_api_call(api_type, success, duration_ms)


def track_error(error_type: str, message: str, page: str = None) -> None:
    """에러 추적"""
    metrics.record_error(error_type, message, page)


def get_dashboard_data() -> Dict[str, Any]:
    """대시보드 데이터 가져오기"""
    return metrics.get_dashboard_summary()


# ============================================================
# Streamlit 대시보드 컴포넌트
# ============================================================

def render_realtime_metrics_card():
    """실시간 메트릭 카드 렌더링"""
    import streamlit as st

    summary = get_dashboard_data()

    st.markdown("### 📊 실시간 현황")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "활성 사용자 (5분)",
            summary["active_users"]["5min"],
            delta=None
        )

    with col2:
        st.metric(
            "API 호출",
            summary["api"]["total_calls"],
            delta=None
        )

    with col3:
        st.metric(
            "페이지 조회",
            summary["pages"]["total_views"],
            delta=None
        )

    with col4:
        status_color = {
            "healthy": "🟢",
            "warning": "🟡",
            "critical": "🔴"
        }
        st.metric(
            "시스템 상태",
            status_color.get(summary["system_status"], "⚪") + " " + summary["system_status"].upper(),
            delta=None
        )


def render_activity_feed():
    """실시간 활동 피드"""
    import streamlit as st

    st.markdown("### 📜 최근 활동")

    events = metrics.get_recent_events(10)

    for event in events:
        event_type = event.get("type", "unknown")
        timestamp = event.get("timestamp", "")[:19]

        if event_type == "activity":
            st.text(f"👤 {timestamp} | 사용자 활동: {event.get('page', 'N/A')}")
        elif event_type == "api_call":
            icon = "✅" if event.get("success") else "❌"
            st.text(f"{icon} {timestamp} | API: {event.get('api', 'N/A')}")
        elif event_type == "practice_complete":
            st.text(f"🎯 {timestamp} | 연습 완료: {event.get('practice_type', 'N/A')}")


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=== Realtime Dashboard ===")

    # 테스트 데이터 생성
    for i in range(5):
        track_activity(f"user_{i}", f"page_{i % 3}")
        track_api_call("openai", success=True, duration_ms=100 + i * 10)

    track_error("APIError", "Test error message", "test_page")

    # 대시보드 데이터
    print("\nDashboard Summary:")
    summary = get_dashboard_data()
    print(json.dumps(summary, indent=2, ensure_ascii=False))

# admin_dashboard.py
# 고급 관리자 분석 대시보드

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

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


# ============================================================
# 대시보드 데이터 수집
# ============================================================

class AdminDashboard:
    """관리자 대시보드 데이터 집계"""

    def __init__(self):
        pass

    def get_overview(self) -> Dict[str, Any]:
        """전체 개요"""
        return {
            "timestamp": datetime.now().isoformat(),
            "users": self._get_user_stats(),
            "interviews": self._get_interview_stats(),
            "api": self._get_api_stats(),
            "system": self._get_system_stats()
        }

    def _get_user_stats(self) -> Dict[str, Any]:
        """사용자 통계"""
        try:
            from user_analytics import analytics
            return {
                "today_active": analytics.get_daily_report().get("unique_users", 0),
                "total_sessions": len(analytics._user_profiles),
                "retention_7d": analytics.get_user_retention(7).get("average_dau", 0)
            }
        except:
            return {"today_active": 0, "total_sessions": 0, "retention_7d": 0}

    def _get_interview_stats(self) -> Dict[str, Any]:
        """면접 통계"""
        try:
            from user_analytics import analytics
            report = analytics.get_daily_report()
            return {
                "today_completed": report.get("interviews_completed", 0),
                "popular_types": ["한국어 면접", "영어 면접", "롤플레잉"]
            }
        except:
            return {"today_completed": 0, "popular_types": []}

    def _get_api_stats(self) -> Dict[str, Any]:
        """API 통계"""
        try:
            from performance_monitor import monitor
            data = monitor.get_dashboard_data()
            return {
                "total_calls": data["api"]["total_calls"],
                "errors": data["api"]["errors"],
                "cache_hit_rate": self._calc_cache_rate(data["cache"])
            }
        except:
            return {"total_calls": 0, "errors": 0, "cache_hit_rate": "0%"}

    def _get_system_stats(self) -> Dict[str, Any]:
        """시스템 통계"""
        try:
            from performance_monitor import monitor
            data = monitor.get_dashboard_data()
            return {
                "cpu": f"{data['system']['cpu']:.1f}%",
                "memory": f"{data['system']['memory']:.1f}%",
                "uptime_hours": data["system"]["uptime"] / 3600
            }
        except:
            return {"cpu": "N/A", "memory": "N/A", "uptime_hours": 0}

    def _calc_cache_rate(self, cache: Dict) -> str:
        hits = cache.get("hits", 0)
        total = hits + cache.get("misses", 0)
        rate = (hits / total * 100) if total > 0 else 0
        return f"{rate:.1f}%"

    def get_experiments(self) -> List[Dict[str, Any]]:
        """A/B 테스트 현황"""
        try:
            from ab_testing import ab_engine
            experiments = []
            for exp in ab_engine.list_experiments():
                results = ab_engine.get_results(exp.id)
                experiments.append({
                    "name": exp.name,
                    "status": exp.status,
                    "participants": results.get("total_participants", 0),
                    "winner": results.get("winner")
                })
            return experiments
        except:
            return []

    def get_feature_flags(self) -> List[Dict[str, Any]]:
        """Feature Flags 현황"""
        try:
            from feature_flags import feature_flags
            flags = []
            for flag in feature_flags.list_flags():
                flags.append({
                    "name": flag.name,
                    "enabled": flag.enabled,
                    "rollout": f"{flag.rollout_percentage}%"
                })
            return flags
        except:
            return []

    def get_job_queue_status(self) -> Dict[str, Any]:
        """작업 큐 상태"""
        try:
            from job_queue import job_queue
            return job_queue.get_stats()
        except:
            return {"total_jobs": 0, "by_status": {}}


# 전역 인스턴스
admin_dashboard = AdminDashboard()


# ============================================================
# Streamlit 페이지
# ============================================================

def render_admin_dashboard():
    """관리자 대시보드 렌더링"""
    import streamlit as st

    st.title("관리자 대시보드")

    # 개요
    overview = admin_dashboard.get_overview()

    st.markdown("## 시스템 개요")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("활성 사용자", overview["users"]["today_active"])
    with col2:
        st.metric("오늘 면접", overview["interviews"]["today_completed"])
    with col3:
        st.metric("API 호출", overview["api"]["total_calls"])
    with col4:
        st.metric("캐시 히트율", overview["api"]["cache_hit_rate"])

    # 시스템 상태
    st.markdown("## 시스템 상태")
    sys = overview["system"]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("CPU", sys["cpu"])
    with col2:
        st.metric("Memory", sys["memory"])
    with col3:
        st.metric("Uptime", f"{sys['uptime_hours']:.1f}h")

    # A/B 테스트
    st.markdown("## A/B 테스트")
    experiments = admin_dashboard.get_experiments()
    if experiments:
        for exp in experiments:
            st.text(f"  {exp['name']}: {exp['status']} ({exp['participants']}명)")
    else:
        st.info("진행 중인 A/B 테스트 없음")

    # Feature Flags
    st.markdown("## Feature Flags")
    flags = admin_dashboard.get_feature_flags()
    if flags:
        for flag in flags:
            status = "ON" if flag["enabled"] else "OFF"
            st.text(f"  {flag['name']}: {status} ({flag['rollout']})")
    else:
        st.info("등록된 Feature Flag 없음")

    # 작업 큐
    st.markdown("## 작업 큐")
    queue_status = admin_dashboard.get_job_queue_status()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("대기", queue_status.get("by_status", {}).get("pending", 0))
    with col2:
        st.metric("실행중", queue_status.get("by_status", {}).get("running", 0))
    with col3:
        st.metric("완료", queue_status.get("by_status", {}).get("completed", 0))


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=== Admin Dashboard ===")
    print(json.dumps(admin_dashboard.get_overview(), indent=2, default=str))
    print("\nReady!")

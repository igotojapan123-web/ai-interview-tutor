# tests/test_user_analytics.py
# User Analytics 테스트

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from user_analytics import UserAnalytics, EventType


class TestUserAnalytics:
    """UserAnalytics 클래스 테스트"""

    @pytest.fixture
    def analytics(self):
        """새 Analytics 인스턴스"""
        return UserAnalytics()

    def test_track_event(self, analytics, sample_user_id):
        """이벤트 추적 테스트"""
        analytics.track_event(
            EventType.PAGE_VIEW,
            user_id=sample_user_id,
            page="home"
        )

        # 이벤트가 버퍼에 추가됨
        assert len(analytics._events_buffer) > 0

    def test_track_page_view(self, analytics, sample_user_id):
        """페이지 조회 추적 테스트"""
        analytics.track_page_view(sample_user_id, "interview")

        assert len(analytics._events_buffer) > 0
        assert analytics._events_buffer[-1]["page"] == "interview"

    def test_track_feature_use(self, analytics, sample_user_id):
        """기능 사용 추적 테스트"""
        analytics.track_feature_use(
            sample_user_id,
            "voice_interview",
            "start"
        )

        event = analytics._events_buffer[-1]
        assert event["event"] == EventType.FEATURE_START
        assert event["properties"]["feature"] == "voice_interview"

    def test_track_interview(self, analytics, sample_user_id):
        """면접 추적 테스트"""
        analytics.track_interview(
            sample_user_id,
            "korean",
            "complete",
            score=85.5,
            duration_minutes=30
        )

        event = analytics._events_buffer[-1]
        assert event["event"] == EventType.INTERVIEW_COMPLETE
        assert event["properties"]["score"] == 85.5

    def test_track_api_call(self, analytics):
        """API 호출 추적 테스트"""
        analytics.track_api_call(
            "openai",
            success=True,
            duration_ms=150
        )

        event = analytics._events_buffer[-1]
        assert event["event"] == EventType.API_CALL
        assert event["properties"]["api_type"] == "openai"

    def test_get_daily_report(self, analytics, sample_user_id):
        """일일 리포트 테스트"""
        # 이벤트 추가
        analytics.track_page_view(sample_user_id, "home")
        analytics.track_api_call("openai", success=True)

        report = analytics.get_daily_report()

        assert "date" in report
        assert "total_events" in report
        assert report["total_events"] >= 2

    def test_get_feature_usage_report(self, analytics, sample_user_id):
        """기능 사용 리포트 테스트"""
        analytics.track_feature_use(sample_user_id, "voice", "complete")
        analytics.track_feature_use(sample_user_id, "video", "complete")

        report = analytics.get_feature_usage_report()

        assert "total_feature_uses" in report
        assert "features" in report

    def test_get_user_journey(self, analytics, sample_user_id):
        """사용자 여정 테스트"""
        analytics.track_page_view(sample_user_id, "home")
        analytics.track_page_view(sample_user_id, "interview")

        journey = analytics.get_user_journey(sample_user_id)

        assert "first_seen" in journey
        assert "pages_visited" in journey

    def test_get_popular_pages(self, analytics, sample_user_id):
        """인기 페이지 테스트"""
        for _ in range(5):
            analytics.track_page_view(sample_user_id, "home")
        for _ in range(3):
            analytics.track_page_view(sample_user_id, "interview")

        pages = analytics.get_popular_pages(1)

        assert len(pages) > 0
        # home이 더 많이 방문됨
        if len(pages) >= 2:
            assert pages[0]["page"] == "home"


class TestEventTypes:
    """EventType 상수 테스트"""

    def test_event_types_exist(self):
        """이벤트 유형 존재 확인"""
        assert EventType.PAGE_VIEW == "page_view"
        assert EventType.FEATURE_START == "feature_start"
        assert EventType.INTERVIEW_COMPLETE == "interview_complete"
        assert EventType.API_CALL == "api_call"

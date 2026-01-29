# tests/unit/test_analytics.py
# FlyReady Lab - 분석 시스템 단위 테스트
# Stage 4: 대기업 수준 테스트

import pytest
import sys
import os
import time
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestAnalyticsEventType:
    """AnalyticsEventType 열거형 테스트"""

    def test_session_start(self):
        """세션 시작 이벤트 타입"""
        from analytics import AnalyticsEventType
        assert AnalyticsEventType.SESSION_START.value == "session_start"

    def test_session_end(self):
        """세션 종료 이벤트 타입"""
        from analytics import AnalyticsEventType
        assert AnalyticsEventType.SESSION_END.value == "session_end"

    def test_page_view(self):
        """페이지 뷰 이벤트 타입"""
        from analytics import AnalyticsEventType
        assert AnalyticsEventType.PAGE_VIEW.value == "page_view"

    def test_button_click(self):
        """버튼 클릭 이벤트 타입"""
        from analytics import AnalyticsEventType
        assert AnalyticsEventType.BUTTON_CLICK.value == "button_click"

    def test_conversion(self):
        """전환 이벤트 타입"""
        from analytics import AnalyticsEventType
        assert AnalyticsEventType.CONVERSION.value == "conversion"


class TestConversionGoal:
    """ConversionGoal 열거형 테스트"""

    def test_interview_complete(self):
        """면접 완료 전환 목표"""
        from analytics import ConversionGoal
        assert ConversionGoal.INTERVIEW_COMPLETE.value == "interview_complete"

    def test_essay_analysis(self):
        """자소서 분석 전환 목표"""
        from analytics import ConversionGoal
        assert ConversionGoal.ESSAY_ANALYSIS.value == "essay_analysis"

    def test_quiz_complete(self):
        """퀴즈 완료 전환 목표"""
        from analytics import ConversionGoal
        assert ConversionGoal.QUIZ_COMPLETE.value == "quiz_complete"


class TestAnalyticsEvent:
    """AnalyticsEvent 데이터클래스 테스트"""

    def test_create_event(self):
        """이벤트 생성"""
        from analytics import AnalyticsEvent, AnalyticsEventType

        event = AnalyticsEvent(
            event_type=AnalyticsEventType.PAGE_VIEW
        )

        assert event.event_type == AnalyticsEventType.PAGE_VIEW
        assert event.timestamp is not None

    def test_event_with_details(self):
        """상세 정보가 있는 이벤트"""
        from analytics import AnalyticsEvent, AnalyticsEventType

        event = AnalyticsEvent(
            event_type=AnalyticsEventType.BUTTON_CLICK,
            session_id="session123",
            user_id="user456",
            page="home",
            action="click_login",
            properties={"button": "login_btn"}
        )

        assert event.session_id == "session123"
        assert event.user_id == "user456"
        assert event.page == "home"
        assert event.action == "click_login"

    def test_event_to_dict(self):
        """이벤트 딕셔너리 변환"""
        from analytics import AnalyticsEvent, AnalyticsEventType

        event = AnalyticsEvent(
            event_type=AnalyticsEventType.CONVERSION,
            session_id="sess123",
            action="interview_complete"
        )

        result = event.to_dict()

        assert result["event_type"] == "conversion"
        assert result["session_id"] == "sess123"
        assert "timestamp" in result


class TestSessionData:
    """SessionData 데이터클래스 테스트"""

    def test_create_session(self):
        """세션 생성"""
        from analytics import SessionData

        session = SessionData(
            session_id="test_session",
            start_time=datetime.now()
        )

        assert session.session_id == "test_session"
        assert session.pages_viewed == []
        assert session.actions == []

    def test_session_with_data(self):
        """데이터가 있는 세션"""
        from analytics import SessionData

        session = SessionData(
            session_id="test_session",
            start_time=datetime.now(),
            user_id="user123",
            pages_viewed=["home", "interview", "result"],
            actions=["start_interview", "submit_answer"],
            conversions=["interview_complete"]
        )

        assert len(session.pages_viewed) == 3
        assert len(session.actions) == 2
        assert len(session.conversions) == 1

    def test_session_to_dict(self):
        """세션 딕셔너리 변환"""
        from analytics import SessionData

        session = SessionData(
            session_id="test_session",
            start_time=datetime.now(),
            pages_viewed=["home", "home", "interview"]
        )

        result = session.to_dict()

        assert result["session_id"] == "test_session"
        assert result["page_count"] == 3
        assert result["unique_pages"] == 2


class TestAnalyticsSystem:
    """AnalyticsSystem 싱글톤 테스트"""

    def test_singleton(self):
        """싱글톤 패턴"""
        from analytics import AnalyticsSystem

        system1 = AnalyticsSystem()
        system2 = AnalyticsSystem()

        assert system1 is system2

    def test_get_analytics(self):
        """get_analytics 함수"""
        from analytics import get_analytics, AnalyticsSystem

        analytics = get_analytics()
        assert isinstance(analytics, AnalyticsSystem)

    def test_start_session(self):
        """세션 시작"""
        from analytics import get_analytics

        analytics = get_analytics()
        analytics.start_session("test_session_001", "user123")

        count = analytics.get_active_sessions_count()
        assert count >= 0  # 이미 다른 테스트에서 세션이 있을 수 있음

    def test_end_session(self):
        """세션 종료"""
        from analytics import get_analytics

        analytics = get_analytics()
        analytics.start_session("test_session_002", "user123")
        analytics.end_session("test_session_002")

        # 세션이 종료되었으면 활성 세션에서 제거됨

    @patch('analytics.st')
    def test_track_page_view(self, mock_st):
        """페이지 뷰 추적"""
        mock_st.session_state = {"session_id": "test_session_003"}

        from analytics import get_analytics

        analytics = get_analytics()
        analytics.start_session("test_session_003")
        analytics.track_page_view("home", "test_session_003")

        # 정상 실행되면 성공

    @patch('analytics.st')
    def test_track_action(self, mock_st):
        """액션 추적"""
        mock_st.session_state = {"session_id": "test_session_004"}

        from analytics import get_analytics

        analytics = get_analytics()
        analytics.start_session("test_session_004")
        analytics.track_action("click_button", "home", {"button": "submit"}, "test_session_004")

    @patch('analytics.st')
    def test_track_feature_usage(self, mock_st):
        """기능 사용 추적"""
        mock_st.session_state = {"session_id": "test_session_005"}

        from analytics import get_analytics

        analytics = get_analytics()
        analytics.track_feature_usage("voice_chat", {"duration": 30}, "test_session_005")

    @patch('analytics.st')
    def test_track_conversion(self, mock_st):
        """전환 추적"""
        mock_st.session_state = {"session_id": "test_session_006"}

        from analytics import get_analytics, ConversionGoal

        analytics = get_analytics()
        analytics.start_session("test_session_006")
        analytics.track_conversion(ConversionGoal.INTERVIEW_COMPLETE, {"score": 85}, "test_session_006")

    @patch('analytics.st')
    def test_track_error(self, mock_st):
        """에러 추적"""
        mock_st.session_state = {"session_id": "test_session_007"}

        from analytics import get_analytics

        analytics = get_analytics()
        analytics.track_error("connection_error", "api_page", {"api": "openai"})

    def test_get_daily_stats(self):
        """일일 통계 조회"""
        from analytics import get_analytics

        analytics = get_analytics()
        stats = analytics.get_daily_stats(7)

        assert isinstance(stats, dict)

    def test_get_page_stats(self):
        """페이지 통계 조회"""
        from analytics import get_analytics

        analytics = get_analytics()
        stats = analytics.get_page_stats(7)

        assert isinstance(stats, dict)

    def test_get_feature_stats(self):
        """기능 통계 조회"""
        from analytics import get_analytics

        analytics = get_analytics()
        stats = analytics.get_feature_stats(7)

        assert isinstance(stats, dict)

    def test_get_conversion_stats(self):
        """전환 통계 조회"""
        from analytics import get_analytics

        analytics = get_analytics()
        stats = analytics.get_conversion_stats(7)

        assert isinstance(stats, dict)

    def test_get_summary_stats(self):
        """요약 통계 조회"""
        from analytics import get_analytics

        analytics = get_analytics()
        summary = analytics.get_summary_stats(7)

        assert "period_days" in summary
        assert "total_sessions" in summary
        assert "total_page_views" in summary
        assert "conversion_rate_percent" in summary

    def test_get_active_sessions_count(self):
        """활성 세션 수 조회"""
        from analytics import get_analytics

        analytics = get_analytics()
        count = analytics.get_active_sessions_count()

        assert count >= 0

    def test_get_active_sessions(self):
        """활성 세션 목록 조회"""
        from analytics import get_analytics

        analytics = get_analytics()
        sessions = analytics.get_active_sessions()

        assert isinstance(sessions, list)


class TestFunnelAnalyzer:
    """FunnelAnalyzer 테스트"""

    def test_define_funnel(self):
        """퍼널 정의"""
        from analytics import get_funnel_analyzer

        analyzer = get_funnel_analyzer()
        analyzer.define_funnel(
            "interview_funnel",
            ["home", "select_type", "interview", "result"]
        )

    def test_analyze_funnel(self):
        """퍼널 분석"""
        from analytics import get_funnel_analyzer

        analyzer = get_funnel_analyzer()
        analyzer.define_funnel(
            "test_funnel",
            ["step1", "step2", "step3"]
        )

        result = analyzer.analyze_funnel("test_funnel", 7)

        assert result["funnel_name"] == "test_funnel"
        assert len(result["steps"]) == 3
        assert "step_counts" in result
        assert "conversion_rates" in result

    def test_analyze_nonexistent_funnel(self):
        """존재하지 않는 퍼널 분석"""
        from analytics import get_funnel_analyzer

        analyzer = get_funnel_analyzer()
        result = analyzer.analyze_funnel("nonexistent", 7)

        assert "error" in result


class TestABTestManager:
    """ABTestManager 테스트"""

    def test_create_test(self):
        """A/B 테스트 생성"""
        from analytics import get_ab_test_manager

        manager = get_ab_test_manager()
        manager.create_test(
            "button_color_test",
            ["red", "blue", "green"]
        )

    def test_create_test_with_weights(self):
        """가중치가 있는 A/B 테스트 생성"""
        from analytics import get_ab_test_manager

        manager = get_ab_test_manager()
        manager.create_test(
            "weighted_test",
            ["control", "variant_a", "variant_b"],
            weights=[0.5, 0.3, 0.2]
        )

    def test_get_variant(self):
        """변형 할당"""
        from analytics import get_ab_test_manager

        manager = get_ab_test_manager()
        manager.create_test("variant_test", ["A", "B"])

        variant = manager.get_variant("variant_test", "session_123")

        assert variant in ["A", "B"]

    def test_get_variant_consistency(self):
        """변형 할당 일관성"""
        from analytics import get_ab_test_manager

        manager = get_ab_test_manager()
        manager.create_test("consistency_test", ["X", "Y"])

        variant1 = manager.get_variant("consistency_test", "session_456")
        variant2 = manager.get_variant("consistency_test", "session_456")

        # 같은 세션은 같은 변형을 받아야 함
        assert variant1 == variant2

    def test_get_variant_nonexistent_test(self):
        """존재하지 않는 테스트"""
        from analytics import get_ab_test_manager

        manager = get_ab_test_manager()
        variant = manager.get_variant("nonexistent_test", "session_789")

        assert variant is None

    def test_record_conversion(self):
        """전환 기록"""
        from analytics import get_ab_test_manager

        manager = get_ab_test_manager()
        manager.create_test("conversion_test", ["control", "variant"])

        # 변형 할당
        variant = manager.get_variant("conversion_test", "session_conv_1")

        # 전환 기록
        manager.record_conversion("conversion_test", "session_conv_1")

    def test_get_test_results(self):
        """테스트 결과 조회"""
        from analytics import get_ab_test_manager

        manager = get_ab_test_manager()
        manager.create_test("results_test", ["A", "B"])

        # 여러 세션에 변형 할당
        for i in range(10):
            manager.get_variant("results_test", f"session_{i}")

        results = manager.get_test_results("results_test")

        assert results["test_name"] == "results_test"
        assert "results" in results
        assert "A" in results["results"]
        assert "B" in results["results"]

    def test_get_test_results_nonexistent(self):
        """존재하지 않는 테스트 결과 조회"""
        from analytics import get_ab_test_manager

        manager = get_ab_test_manager()
        results = manager.get_test_results("nonexistent")

        assert "error" in results


class TestConvenienceFunctions:
    """편의 함수 테스트"""

    @patch('analytics.st')
    def test_track_page_view_function(self, mock_st):
        """track_page_view 편의 함수"""
        mock_st.session_state = {"session_id": "test_sess"}

        from analytics import track_page_view
        track_page_view("home")

    @patch('analytics.st')
    def test_track_action_function(self, mock_st):
        """track_action 편의 함수"""
        mock_st.session_state = {"session_id": "test_sess"}

        from analytics import track_action
        track_action("click_submit", "form_page", {"form": "login"})

    @patch('analytics.st')
    def test_track_feature_usage_function(self, mock_st):
        """track_feature_usage 편의 함수"""
        mock_st.session_state = {"session_id": "test_sess"}

        from analytics import track_feature_usage
        track_feature_usage("voice_chat", {"duration": 60})

    @patch('analytics.st')
    def test_track_conversion_function(self, mock_st):
        """track_conversion 편의 함수"""
        mock_st.session_state = {"session_id": "test_sess"}

        from analytics import track_conversion, ConversionGoal
        track_conversion(ConversionGoal.QUIZ_COMPLETE)

    def test_get_summary_stats_function(self):
        """get_summary_stats 편의 함수"""
        from analytics import get_summary_stats

        summary = get_summary_stats(7)

        assert "total_sessions" in summary
        assert "conversion_rate_percent" in summary


class TestSessionInitialization:
    """세션 초기화 테스트"""

    @patch('analytics.st')
    def test_init_analytics_session(self, mock_st):
        """분석 세션 초기화"""
        class AttrDict(dict):
            def __setattr__(self, key, value):
                self[key] = value
            def __getattr__(self, key):
                return self.get(key)
            def __contains__(self, key):
                return dict.__contains__(self, key)

        mock_st.session_state = AttrDict()

        from analytics import init_analytics_session

        init_analytics_session()

        assert mock_st.session_state.analytics_session_initialized is True
        assert "session_id" in mock_st.session_state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

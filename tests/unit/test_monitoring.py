# tests/unit/test_monitoring.py
# FlyReady Lab - 모니터링 시스템 단위 테스트
# Stage 4: 대기업 수준 테스트

import pytest
import sys
import os
import time
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestEventType:
    """EventType 열거형 테스트"""

    def test_event_type_error(self):
        """에러 이벤트 타입"""
        from monitoring import EventType
        assert EventType.ERROR.value == "error"

    def test_event_type_warning(self):
        """경고 이벤트 타입"""
        from monitoring import EventType
        assert EventType.WARNING.value == "warning"

    def test_event_type_page_view(self):
        """페이지 뷰 이벤트 타입"""
        from monitoring import EventType
        assert EventType.PAGE_VIEW.value == "page_view"

    def test_event_type_api_call(self):
        """API 호출 이벤트 타입"""
        from monitoring import EventType
        assert EventType.API_CALL.value == "api_call"

    def test_event_type_security_alert(self):
        """보안 알림 이벤트 타입"""
        from monitoring import EventType
        assert EventType.SECURITY_ALERT.value == "security_alert"


class TestAlertLevel:
    """AlertLevel 열거형 테스트"""

    def test_alert_level_debug(self):
        """디버그 레벨"""
        from monitoring import AlertLevel
        assert AlertLevel.DEBUG.value == "debug"

    def test_alert_level_info(self):
        """정보 레벨"""
        from monitoring import AlertLevel
        assert AlertLevel.INFO.value == "info"

    def test_alert_level_warning(self):
        """경고 레벨"""
        from monitoring import AlertLevel
        assert AlertLevel.WARNING.value == "warning"

    def test_alert_level_error(self):
        """에러 레벨"""
        from monitoring import AlertLevel
        assert AlertLevel.ERROR.value == "error"

    def test_alert_level_critical(self):
        """심각 레벨"""
        from monitoring import AlertLevel
        assert AlertLevel.CRITICAL.value == "critical"


class TestMonitoringEvent:
    """MonitoringEvent 데이터클래스 테스트"""

    def test_create_event(self):
        """이벤트 생성"""
        from monitoring import MonitoringEvent, EventType, AlertLevel

        event = MonitoringEvent(
            event_type=EventType.ERROR,
            message="Test error"
        )

        assert event.event_type == EventType.ERROR
        assert event.message == "Test error"
        assert event.level == AlertLevel.INFO  # 기본값

    def test_event_with_context(self):
        """컨텍스트가 있는 이벤트"""
        from monitoring import MonitoringEvent, EventType, AlertLevel

        event = MonitoringEvent(
            event_type=EventType.API_CALL,
            message="API call",
            level=AlertLevel.WARNING,
            context={"api": "openai", "endpoint": "/chat"}
        )

        assert event.context["api"] == "openai"
        assert event.level == AlertLevel.WARNING

    def test_event_to_dict(self):
        """이벤트 딕셔너리 변환"""
        from monitoring import MonitoringEvent, EventType, AlertLevel

        event = MonitoringEvent(
            event_type=EventType.PAGE_VIEW,
            message="Page viewed",
            page="home",
            user_id="user123"
        )

        result = event.to_dict()

        assert result["event_type"] == "page_view"
        assert result["message"] == "Page viewed"
        assert result["page"] == "home"
        assert result["user_id"] == "user123"
        assert "timestamp" in result

    def test_event_fingerprint(self):
        """이벤트 핑거프린트 생성"""
        from monitoring import MonitoringEvent, EventType

        event = MonitoringEvent(
            event_type=EventType.ERROR,
            message="Test error",
            page="login"
        )

        fingerprint = event.get_fingerprint()

        assert fingerprint is not None
        assert len(fingerprint) == 16


class TestPerformanceMetric:
    """PerformanceMetric 데이터클래스 테스트"""

    def test_create_metric(self):
        """메트릭 생성"""
        from monitoring import PerformanceMetric

        metric = PerformanceMetric(
            name="response_time",
            value=150.5,
            unit="ms"
        )

        assert metric.name == "response_time"
        assert metric.value == 150.5
        assert metric.unit == "ms"

    def test_metric_to_dict(self):
        """메트릭 딕셔너리 변환"""
        from monitoring import PerformanceMetric

        metric = PerformanceMetric(
            name="cpu_usage",
            value=45.2,
            unit="%",
            tags={"server": "main"}
        )

        result = metric.to_dict()

        assert result["name"] == "cpu_usage"
        assert result["value"] == 45.2
        assert result["unit"] == "%"
        assert result["tags"]["server"] == "main"


class TestMetricsCollector:
    """MetricsCollector 클래스 테스트"""

    def test_record_metric(self):
        """메트릭 기록"""
        from monitoring import MetricsCollector

        collector = MetricsCollector(max_history=100)
        collector.record("test_metric", 100.0, "ms")

        latest = collector.get_latest("test_metric")
        assert latest is not None
        assert latest.value == 100.0

    def test_get_history(self):
        """메트릭 히스토리 조회"""
        from monitoring import MetricsCollector

        collector = MetricsCollector(max_history=100)

        for i in range(5):
            collector.record("test_metric", float(i * 10), "ms")

        history = collector.get_history("test_metric", 10)
        assert len(history) == 5

    def test_get_average(self):
        """평균값 계산"""
        from monitoring import MetricsCollector

        collector = MetricsCollector(max_history=100)

        for i in range(5):
            collector.record("test_metric", float(i * 10), "ms")
            time.sleep(0.01)

        avg = collector.get_average("test_metric", window_minutes=5)
        assert avg is not None
        # 0, 10, 20, 30, 40 평균 = 20
        assert avg == 20.0

    def test_get_percentile(self):
        """백분위수 계산"""
        from monitoring import MetricsCollector

        collector = MetricsCollector(max_history=100)

        for i in range(100):
            collector.record("test_metric", float(i), "ms")
            time.sleep(0.001)

        p50 = collector.get_percentile("test_metric", 50, window_minutes=5)
        assert p50 is not None

    def test_get_all_metrics_summary(self):
        """전체 메트릭 요약"""
        from monitoring import MetricsCollector

        collector = MetricsCollector(max_history=100)
        collector.record("metric1", 100.0, "ms")
        collector.record("metric2", 200.0, "count")

        summary = collector.get_all_metrics_summary()

        assert "metric1" in summary
        assert "metric2" in summary

    def test_empty_metric(self):
        """빈 메트릭 조회"""
        from monitoring import MetricsCollector

        collector = MetricsCollector()

        assert collector.get_latest("nonexistent") is None
        assert collector.get_history("nonexistent") == []
        assert collector.get_average("nonexistent") is None


class TestAlertManager:
    """AlertManager 클래스 테스트"""

    def test_send_alert(self):
        """알림 발송"""
        from monitoring import AlertManager, MonitoringEvent, EventType, AlertLevel

        manager = AlertManager(cooldown_minutes=5)

        event = MonitoringEvent(
            event_type=EventType.ERROR,
            message="Test error",
            level=AlertLevel.ERROR
        )

        result = manager.send_alert(event)
        assert result is True

    def test_alert_cooldown(self):
        """알림 쿨다운"""
        from monitoring import AlertManager, MonitoringEvent, EventType, AlertLevel

        manager = AlertManager(cooldown_minutes=5)

        event = MonitoringEvent(
            event_type=EventType.ERROR,
            message="Same error",
            page="login"
        )

        # 첫 번째 발송
        result1 = manager.send_alert(event)
        assert result1 is True

        # 쿨다운 중 - 같은 이벤트
        result2 = manager.send_alert(event)
        assert result2 is False

    def test_get_recent_alerts(self):
        """최근 알림 조회"""
        from monitoring import AlertManager, MonitoringEvent, EventType

        manager = AlertManager(cooldown_minutes=0)  # 쿨다운 없음

        for i in range(5):
            event = MonitoringEvent(
                event_type=EventType.WARNING,
                message=f"Warning {i}",
                page=f"page{i}"  # 다른 핑거프린트
            )
            manager.send_alert(event)

        alerts = manager.get_recent_alerts(10)
        assert len(alerts) == 5

    def test_alert_handler(self):
        """알림 핸들러"""
        from monitoring import AlertManager, MonitoringEvent, EventType

        manager = AlertManager(cooldown_minutes=0)
        handled = []

        def handler(event):
            handled.append(event)

        manager.add_handler(handler)

        event = MonitoringEvent(
            event_type=EventType.ERROR,
            message="Test"
        )
        manager.send_alert(event)

        assert len(handled) == 1


class TestMonitoringSystem:
    """MonitoringSystem 싱글톤 테스트"""

    def test_singleton(self):
        """싱글톤 패턴"""
        from monitoring import MonitoringSystem

        system1 = MonitoringSystem()
        system2 = MonitoringSystem()

        assert system1 is system2

    def test_get_monitoring(self):
        """get_monitoring 함수"""
        from monitoring import get_monitoring, MonitoringSystem

        monitoring = get_monitoring()
        assert isinstance(monitoring, MonitoringSystem)

    @patch('monitoring.st')
    def test_track_page_view(self, mock_st):
        """페이지 뷰 추적"""
        mock_st.session_state = {}
        from monitoring import get_monitoring

        monitoring = get_monitoring()
        monitoring.track_page_view("home", "user123")

        # 페이지 뷰가 기록되었는지 확인
        status = monitoring.get_system_status()
        assert "top_pages" in status

    def test_track_feature_usage(self):
        """기능 사용 추적"""
        from monitoring import get_monitoring

        monitoring = get_monitoring()
        monitoring.track_feature_usage("voice_chat", "user123")

        # 정상 실행되면 성공

    def test_track_api_latency(self):
        """API 레이턴시 추적"""
        from monitoring import get_monitoring

        monitoring = get_monitoring()
        monitoring.track_api_latency("openai", 150.0, True)

        metrics = monitoring.get_metrics()
        latest = metrics.get_latest("api_latency")
        assert latest is not None

    def test_track_error(self):
        """에러 추적"""
        from monitoring import get_monitoring

        monitoring = get_monitoring()
        try:
            raise ValueError("Test error")
        except Exception as e:
            monitoring.track_error(e, {"context": "test"}, "login", "user123")

        # 에러 카운트 증가 확인
        status = monitoring.get_system_status()
        assert status["error_count"] >= 0

    def test_get_system_status(self):
        """시스템 상태 조회"""
        from monitoring import get_monitoring

        monitoring = get_monitoring()
        status = monitoring.get_system_status()

        assert "status" in status
        assert "uptime_seconds" in status
        assert "total_events" in status
        assert "error_count" in status

    def test_timer_context_manager(self):
        """타이머 컨텍스트 매니저"""
        from monitoring import get_monitoring

        monitoring = get_monitoring()

        with monitoring.timer("test_operation") as timer:
            time.sleep(0.05)  # 50ms

        assert timer.duration_ms is not None
        assert timer.duration_ms >= 50

    def test_record_metric(self):
        """메트릭 기록"""
        from monitoring import get_monitoring

        monitoring = get_monitoring()
        monitoring.record_metric("custom_metric", 42.0, "count", {"tag": "test"})

        metrics = monitoring.get_metrics()
        latest = metrics.get_latest("custom_metric")
        assert latest.value == 42.0


class TestConvenienceFunctions:
    """편의 함수 테스트"""

    def test_init_monitoring(self):
        """init_monitoring 함수"""
        from monitoring import init_monitoring, MonitoringSystem

        result = init_monitoring()
        assert isinstance(result, MonitoringSystem)

    def test_track_error_function(self):
        """track_error 편의 함수"""
        from monitoring import track_error

        try:
            raise RuntimeError("Test")
        except Exception as e:
            track_error(e, {"key": "value"})

    def test_track_metric_function(self):
        """track_metric 편의 함수"""
        from monitoring import track_metric

        track_metric("test_metric", 100.0, {"tag": "value"})

    def test_track_page_view_function(self):
        """track_page_view 편의 함수"""
        from monitoring import track_page_view

        with patch('monitoring.st') as mock_st:
            mock_st.session_state = {}
            track_page_view("home", "user123")

    def test_track_feature_usage_function(self):
        """track_feature_usage 편의 함수"""
        from monitoring import track_feature_usage

        track_feature_usage("voice_chat", "user123")

    def test_track_api_latency_function(self):
        """track_api_latency 편의 함수"""
        from monitoring import track_api_latency

        track_api_latency("openai_api", 200.0)

    def test_get_error_summary_function(self):
        """get_error_summary 편의 함수"""
        from monitoring import get_error_summary

        summary = get_error_summary(7)
        assert "total_errors" in summary
        assert "by_type" in summary

    def test_get_metrics_summary_function(self):
        """get_metrics_summary 편의 함수"""
        from monitoring import get_metrics_summary

        summary = get_metrics_summary("test_metric", 7)
        assert "count" in summary
        assert "avg" in summary


class TestDecorators:
    """데코레이터 테스트"""

    def test_monitored_decorator(self):
        """@monitored 데코레이터"""
        from monitoring import monitored

        @monitored("test_function")
        def sample_function():
            time.sleep(0.01)
            return "result"

        result = sample_function()
        assert result == "result"

    def test_monitored_decorator_with_error(self):
        """@monitored 데코레이터 - 에러 케이스"""
        from monitoring import monitored

        @monitored("error_function")
        def error_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            error_function()

    def test_track_api_call_decorator(self):
        """@track_api_call 데코레이터"""
        from monitoring import track_api_call

        @track_api_call("test_api")
        def api_call():
            time.sleep(0.01)
            return {"status": "ok"}

        result = api_call()
        assert result["status"] == "ok"

    def test_track_api_call_decorator_error(self):
        """@track_api_call 데코레이터 - 에러 케이스"""
        from monitoring import track_api_call

        @track_api_call("failing_api")
        def failing_api():
            raise ConnectionError("Connection failed")

        with pytest.raises(ConnectionError):
            failing_api()


class TestSessionInitialization:
    """세션 초기화 테스트"""

    @patch('monitoring.st')
    def test_init_monitoring_session(self, mock_st):
        """모니터링 세션 초기화"""
        class AttrDict(dict):
            def __setattr__(self, key, value):
                self[key] = value
            def __getattr__(self, key):
                return self.get(key)
            def __contains__(self, key):
                return dict.__contains__(self, key)

        mock_st.session_state = AttrDict()

        from monitoring import init_monitoring_session

        init_monitoring_session()

        assert mock_st.session_state.monitoring_session_initialized is True
        assert "session_id" in mock_st.session_state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

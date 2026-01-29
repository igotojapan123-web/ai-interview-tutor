# tests/unit/test_error_handler.py
# FlyReady Lab - 에러 핸들러 단위 테스트
# Stage 3: 대기업 수준 테스트

import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestErrorTypes:
    """에러 타입 테스트"""

    def test_error_type_enum_exists(self):
        """ErrorType enum 존재 확인"""
        from error_handler import ErrorType

        assert hasattr(ErrorType, 'NETWORK')
        assert hasattr(ErrorType, 'API')
        assert hasattr(ErrorType, 'VALIDATION')
        assert hasattr(ErrorType, 'AUTH')
        assert hasattr(ErrorType, 'TIMEOUT')
        assert hasattr(ErrorType, 'UNKNOWN')

    def test_error_type_values(self):
        """ErrorType 값 확인"""
        from error_handler import ErrorType

        # 최소 10개 이상의 에러 타입 존재
        assert len(list(ErrorType)) >= 10

    def test_error_severity_enum(self):
        """ErrorSeverity enum 존재 확인"""
        from error_handler import ErrorSeverity

        assert hasattr(ErrorSeverity, 'LOW')
        assert hasattr(ErrorSeverity, 'MEDIUM')
        assert hasattr(ErrorSeverity, 'HIGH')
        assert hasattr(ErrorSeverity, 'CRITICAL')


class TestUserFriendlyMessages:
    """사용자 친화적 메시지 테스트"""

    def test_user_messages_korean(self):
        """한국어 메시지 존재 확인"""
        from error_handler import ERROR_MESSAGES, ErrorType

        # 모든 에러 타입에 대해 한국어 메시지가 존재해야 함
        for error_type in ErrorType:
            assert error_type in ERROR_MESSAGES
            message_data = ERROR_MESSAGES[error_type]
            # 메시지 구조 확인
            assert "title" in message_data
            assert "message" in message_data
            # 한국어가 포함되어야 함
            assert any('\uAC00' <= char <= '\uD7A3' for char in message_data["title"])

    def test_messages_not_empty(self):
        """메시지가 비어있지 않음"""
        from error_handler import ERROR_MESSAGES

        for error_type, message_data in ERROR_MESSAGES.items():
            assert len(message_data["title"]) > 0
            assert len(message_data["message"]) > 0


class TestAppError:
    """AppError 데이터 클래스 테스트"""

    def test_app_error_creation(self):
        """AppError 생성"""
        from error_handler import AppError, ErrorType, ErrorSeverity

        error = AppError(
            error_type=ErrorType.VALIDATION,
            message="테스트 에러",
            severity=ErrorSeverity.MEDIUM
        )

        assert error.error_type == ErrorType.VALIDATION
        assert error.message == "테스트 에러"
        assert error.severity == ErrorSeverity.MEDIUM

    def test_app_error_defaults(self):
        """AppError 기본값"""
        from error_handler import AppError, ErrorType, ErrorSeverity

        error = AppError(
            error_type=ErrorType.UNKNOWN,
            message="기본 에러"
        )

        assert error.severity == ErrorSeverity.MEDIUM
        assert error.context == {}
        assert error.recoverable is True

    def test_app_error_timestamp(self):
        """AppError 타임스탬프"""
        from error_handler import AppError, ErrorType

        before = datetime.now()
        error = AppError(error_type=ErrorType.UNKNOWN, message="테스트")
        after = datetime.now()

        assert before <= error.timestamp <= after

    def test_app_error_to_dict(self):
        """AppError to_dict 메서드"""
        from error_handler import AppError, ErrorType

        error = AppError(error_type=ErrorType.API, message="테스트")
        error_dict = error.to_dict()

        assert "error_type" in error_dict
        assert "message" in error_dict
        assert "timestamp" in error_dict


class TestCircuitBreaker:
    """Circuit Breaker 패턴 테스트"""

    def test_circuit_breaker_creation(self):
        """CircuitBreaker 생성"""
        from error_handler import CircuitBreaker, CircuitState

        cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=30)

        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 30
        assert cb.state == CircuitState.CLOSED

    def test_circuit_breaker_record_failure(self):
        """실패 기록"""
        from error_handler import CircuitBreaker

        cb = CircuitBreaker(name="test_failure", failure_threshold=3, recovery_timeout=30)

        cb.record_failure()
        cb.record_failure()
        # 아직 threshold에 도달하지 않음

    def test_circuit_breaker_opens_on_threshold(self):
        """임계값 도달 시 열림"""
        from error_handler import CircuitBreaker, CircuitState

        cb = CircuitBreaker(name="test_open", failure_threshold=3, recovery_timeout=30)

        cb.record_failure()
        cb.record_failure()
        cb.record_failure()

        assert cb.state == CircuitState.OPEN

    def test_circuit_breaker_success_resets(self):
        """성공 시 리셋"""
        from error_handler import CircuitBreaker, CircuitState

        cb = CircuitBreaker(name="test_reset", failure_threshold=5, recovery_timeout=30)

        cb.record_failure()
        cb.record_failure()
        cb.record_success()

        assert cb.state == CircuitState.CLOSED

    def test_circuit_breaker_can_execute(self):
        """실행 가능 여부"""
        from error_handler import CircuitBreaker

        cb = CircuitBreaker(name="test_execute", failure_threshold=3, recovery_timeout=1)

        assert cb.can_execute() is True

        # 회로 열기
        for _ in range(3):
            cb.record_failure()

        assert cb.can_execute() is False


class TestErrorHandlerSingleton:
    """ErrorHandler 싱글톤 테스트"""

    def test_error_handler_singleton(self):
        """ErrorHandler 싱글톤 확인"""
        from error_handler import ErrorHandler

        handler1 = ErrorHandler()
        handler2 = ErrorHandler()

        # 싱글톤이므로 같은 인스턴스
        assert handler1 is handler2

    def test_error_handler_create_error(self):
        """에러 생성"""
        from error_handler import ErrorHandler, ErrorType

        handler = ErrorHandler()

        app_error = handler.create_error(Exception("테스트 예외"))

        assert app_error is not None
        assert app_error.message == "테스트 예외"


class TestDecorators:
    """데코레이터 테스트"""

    def test_with_error_handling_decorator_exists(self):
        """with_error_handling 데코레이터 존재"""
        from error_handler import with_error_handling

        @with_error_handling(default_return="기본값", show_ui=False)
        def test_func():
            return "성공"

        result = test_func()
        assert result == "성공"

    def test_with_error_handling_catches_exception(self):
        """예외 캐치"""
        from error_handler import with_error_handling

        @with_error_handling(default_return="에러 발생", show_ui=False)
        def test_func():
            raise ValueError("테스트 에러")

        result = test_func()
        assert result == "에러 발생"

    def test_with_retry_decorator_exists(self):
        """with_retry 데코레이터 존재"""
        from error_handler import with_retry

        call_count = 0

        @with_retry(max_retries=3, delay=0.01, show_progress=False)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("재시도 필요")
            return "성공"

        result = test_func()
        assert result == "성공"
        assert call_count == 3


class TestUIHelpers:
    """UI 헬퍼 함수 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('error_handler.st') as mock:
            mock.session_state = {}
            mock.error = MagicMock()
            mock.warning = MagicMock()
            mock.info = MagicMock()
            mock.success = MagicMock()
            mock.markdown = MagicMock()
            yield mock

    def test_show_error_function_exists(self):
        """show_error 함수 존재"""
        from error_handler import show_error
        assert callable(show_error)

    def test_show_warning_function_exists(self):
        """show_warning 함수 존재"""
        from error_handler import show_warning
        assert callable(show_warning)

    def test_show_info_function_exists(self):
        """show_info 함수 존재"""
        from error_handler import show_info
        assert callable(show_info)

    def test_show_success_function_exists(self):
        """show_success 함수 존재"""
        from error_handler import show_success
        assert callable(show_success)


class TestHTTPStatusMapping:
    """HTTP 상태 코드 매핑 테스트"""

    def test_http_error_mapping_exists(self):
        """HTTP_ERROR_MAPPING 존재"""
        from error_handler import HTTP_ERROR_MAPPING

        assert 400 in HTTP_ERROR_MAPPING
        assert 401 in HTTP_ERROR_MAPPING
        assert 403 in HTTP_ERROR_MAPPING
        assert 404 in HTTP_ERROR_MAPPING
        assert 500 in HTTP_ERROR_MAPPING
        assert 503 in HTTP_ERROR_MAPPING

    def test_http_error_mapping_structure(self):
        """HTTP 에러 매핑 구조 확인"""
        from error_handler import HTTP_ERROR_MAPPING, ErrorType

        for code, mapping in HTTP_ERROR_MAPPING.items():
            # 숫자 코드
            assert isinstance(code, int)
            # 매핑은 튜플 (ErrorType, message)
            assert isinstance(mapping, tuple)
            assert len(mapping) == 2
            assert isinstance(mapping[0], ErrorType)


class TestGetCircuitBreaker:
    """get_circuit_breaker 함수 테스트"""

    def test_get_circuit_breaker(self):
        """get_circuit_breaker 함수"""
        from error_handler import get_circuit_breaker

        cb1 = get_circuit_breaker("test_api")
        cb2 = get_circuit_breaker("test_api")

        # 같은 이름이면 같은 인스턴스
        assert cb1 is cb2

    def test_get_circuit_breaker_different_names(self):
        """다른 이름은 다른 인스턴스"""
        from error_handler import get_circuit_breaker

        cb1 = get_circuit_breaker("api_1")
        cb2 = get_circuit_breaker("api_2")

        assert cb1 is not cb2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

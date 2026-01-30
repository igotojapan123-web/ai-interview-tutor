# tests/test_safe_api.py
# Safe API 테스트

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from safe_api import (
    safe_api_call,
    validate_json_response,
    sanitize_user_input,
    validate_string,
    validate_int,
    validate_float,
    validate_list,
    validate_dict,
    validate_api_response,
    safe_get,
    safe_execute,
    SafeContext,
    escape_html,
    safe_json_parse,
    get_audio_hash,
    validate_room_name,
    validate_chat_message,
    validate_answer_text,
    validate_username,
    hash_password,
    verify_password,
    LoginRateLimiter
)


class TestValidateString:
    """validate_string 함수 테스트"""

    def test_basic_string(self):
        """기본 문자열 테스트"""
        result = validate_string("hello world")
        assert result == "hello world"

    def test_strip_whitespace(self):
        """공백 제거 테스트"""
        result = validate_string("  hello  ")
        assert result == "hello"

    def test_max_length(self):
        """최대 길이 테스트"""
        long_text = "a" * 2000
        result = validate_string(long_text, max_length=100)
        assert len(result) == 100

    def test_none_input(self):
        """None 입력 테스트"""
        result = validate_string(None)
        assert result == ""

    def test_default_value(self):
        """기본값 테스트"""
        result = validate_string(None, default="default")
        assert result == "default"


class TestValidateInt:
    """validate_int 함수 테스트"""

    def test_valid_int(self):
        """유효한 정수 테스트"""
        assert validate_int(42) == 42
        assert validate_int("123") == 123

    def test_invalid_input(self):
        """무효한 입력 테스트"""
        assert validate_int("not a number") == 0
        assert validate_int(None, default=10) == 10

    def test_min_max(self):
        """최소/최대값 테스트"""
        assert validate_int(5, min_val=10) == 10
        assert validate_int(100, max_val=50) == 50


class TestValidateFloat:
    """validate_float 함수 테스트"""

    def test_valid_float(self):
        """유효한 실수 테스트"""
        assert validate_float(3.14) == 3.14
        assert validate_float("2.5") == 2.5

    def test_min_max(self):
        """최소/최대값 테스트"""
        assert validate_float(0.5, min_val=1.0) == 1.0
        assert validate_float(10.0, max_val=5.0) == 5.0


class TestValidateList:
    """validate_list 함수 테스트"""

    def test_valid_list(self):
        """유효한 리스트 테스트"""
        assert validate_list([1, 2, 3]) == [1, 2, 3]

    def test_tuple_input(self):
        """튜플 입력 테스트"""
        assert validate_list((1, 2, 3)) == [1, 2, 3]

    def test_none_input(self):
        """None 입력 테스트"""
        assert validate_list(None) == []
        assert validate_list(None, default=[1, 2]) == [1, 2]


class TestValidateDict:
    """validate_dict 함수 테스트"""

    def test_valid_dict(self):
        """유효한 딕셔너리 테스트"""
        data = {"key": "value"}
        assert validate_dict(data) == data

    def test_required_keys(self):
        """필수 키 테스트"""
        data = {"name": "test"}
        assert validate_dict(data, required_keys=["name"]) == data
        assert validate_dict(data, required_keys=["name", "age"]) == {}


class TestSanitizeUserInput:
    """sanitize_user_input 함수 테스트"""

    def test_basic_sanitize(self):
        """기본 정제 테스트"""
        result = sanitize_user_input("hello world")
        assert result == "hello world"

    def test_html_strip(self):
        """HTML 태그 제거 테스트"""
        result = sanitize_user_input("<script>alert('xss')</script>hello")
        assert "<script>" not in result
        assert "hello" in result

    def test_max_length(self):
        """최대 길이 테스트"""
        long_text = "a" * 10000
        result = sanitize_user_input(long_text, max_length=100)
        assert len(result) == 100

    def test_none_input(self):
        """None 입력 테스트"""
        result = sanitize_user_input(None)
        assert result == ""


class TestValidateJsonResponse:
    """validate_json_response 함수 테스트"""

    def test_valid_response(self):
        """유효한 응답 테스트"""
        data = {"name": "test", "value": 123}
        is_valid, result, errors = validate_json_response(data)
        assert is_valid is True
        assert len(errors) == 0

    def test_required_fields(self):
        """필수 필드 테스트"""
        data = {"name": "test"}
        is_valid, result, errors = validate_json_response(
            data, required_fields=["name", "value"]
        )
        assert is_valid is False
        assert any("value" in e for e in errors)

    def test_schema_validation(self):
        """스키마 검증 테스트"""
        data = {"name": "test", "count": "not_a_number"}
        is_valid, result, errors = validate_json_response(
            data, schema={"count": int}
        )
        assert is_valid is False

    def test_none_response(self):
        """None 응답 테스트"""
        is_valid, result, errors = validate_json_response(None)
        assert is_valid is False


class TestSafeJsonParse:
    """safe_json_parse 함수 테스트"""

    def test_valid_json(self):
        """유효한 JSON 파싱 테스트"""
        result = safe_json_parse('{"key": "value"}')
        assert result == {"key": "value"}

    def test_invalid_json(self):
        """무효한 JSON 테스트"""
        result = safe_json_parse("not json", default={})
        assert result == {}

    def test_json_in_markdown(self):
        """마크다운 내 JSON 추출 테스트"""
        text = '```json\n{"key": "value"}\n```'
        result = safe_json_parse(text)
        assert result == {"key": "value"}

    def test_json_in_text(self):
        """텍스트 내 JSON 추출 테스트"""
        text = 'Some text {"key": "value"} more text'
        result = safe_json_parse(text)
        assert result == {"key": "value"}


class TestValidateApiResponse:
    """validate_api_response 함수 테스트"""

    def test_valid_response(self):
        """유효한 응답 테스트"""
        response = {"data": "test"}
        result = validate_api_response(response)
        assert result == response

    def test_none_response(self):
        """None 응답 테스트"""
        result = validate_api_response(None, default={})
        assert result == {}

    def test_error_response(self):
        """에러 응답 테스트"""
        response = {"error": "something went wrong"}
        result = validate_api_response(response, default={})
        assert result == {}

    def test_required_fields(self):
        """필수 필드 테스트"""
        response = {"name": "test"}
        result = validate_api_response(
            response, required_fields=["name", "value"], default={}
        )
        assert result == {}


class TestSafeGet:
    """safe_get 함수 테스트"""

    def test_nested_access(self):
        """중첩 접근 테스트"""
        data = {"user": {"profile": {"name": "John"}}}
        result = safe_get(data, "user", "profile", "name")
        assert result == "John"

    def test_missing_key(self):
        """누락된 키 테스트"""
        data = {"user": {}}
        result = safe_get(data, "user", "profile", "name", default="Unknown")
        assert result == "Unknown"

    def test_list_access(self):
        """리스트 접근 테스트"""
        data = {"items": [1, 2, 3]}
        result = safe_get(data, "items", 1)
        assert result == 2


class TestSafeExecute:
    """safe_execute 함수 테스트"""

    def test_successful_execution(self):
        """성공적인 실행 테스트"""
        def add(a, b):
            return a + b

        result = safe_execute(add, 1, 2)
        assert result == 3

    def test_failed_execution(self):
        """실패한 실행 테스트"""
        def fail():
            raise ValueError("error")

        result = safe_execute(fail, default="default", log_error=False)
        assert result == "default"


class TestSafeContext:
    """SafeContext 클래스 테스트"""

    def test_successful_context(self):
        """성공적인 컨텍스트 테스트"""
        with SafeContext("test") as ctx:
            ctx.result = "success"

        assert ctx.error is None

    def test_failed_context(self):
        """실패한 컨텍스트 테스트"""
        with SafeContext("test", default="default", log_error=False) as ctx:
            raise ValueError("error")

        assert ctx.error is not None


class TestEscapeHtml:
    """escape_html 함수 테스트"""

    def test_escape_tags(self):
        """태그 이스케이프 테스트"""
        result = escape_html("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_escape_quotes(self):
        """따옴표 이스케이프 테스트"""
        result = escape_html('say "hello"')
        assert "&quot;" in result


class TestGetAudioHash:
    """get_audio_hash 함수 테스트"""

    def test_hash_generation(self):
        """해시 생성 테스트"""
        data = b"test audio data"
        hash1 = get_audio_hash(data)
        hash2 = get_audio_hash(data)
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hex length

    def test_empty_data(self):
        """빈 데이터 테스트"""
        assert get_audio_hash(b"") == ""
        assert get_audio_hash(None) == ""


class TestValidationFunctions:
    """입력 검증 함수 테스트"""

    def test_validate_room_name(self):
        """방 이름 검증 테스트"""
        is_valid, name, error = validate_room_name("테스트 방")
        assert is_valid is True

        is_valid, name, error = validate_room_name("a")
        assert is_valid is False

    def test_validate_chat_message(self):
        """채팅 메시지 검증 테스트"""
        is_valid, msg, error = validate_chat_message("안녕하세요")
        assert is_valid is True

        is_valid, msg, error = validate_chat_message("")
        assert is_valid is False

    def test_validate_answer_text(self):
        """답변 텍스트 검증 테스트"""
        is_valid, answer, error = validate_answer_text("이것은 충분히 긴 답변입니다.")
        assert is_valid is True

        is_valid, answer, error = validate_answer_text("짧음")
        assert is_valid is False

    def test_validate_username(self):
        """사용자 이름 검증 테스트"""
        is_valid, name, error = validate_username("홍길동")
        assert is_valid is True

        is_valid, name, error = validate_username("a")
        assert is_valid is False


class TestPasswordFunctions:
    """비밀번호 함수 테스트"""

    def test_hash_password(self):
        """비밀번호 해시 테스트"""
        hash_value, salt = hash_password("password123")
        assert len(hash_value) > 0
        assert len(salt) > 0

    def test_verify_password(self):
        """비밀번호 검증 테스트"""
        password = "test_password"
        hash_value, salt = hash_password(password)

        assert verify_password(password, hash_value, salt) is True
        assert verify_password("wrong_password", hash_value, salt) is False


class TestLoginRateLimiter:
    """LoginRateLimiter 클래스 테스트"""

    def test_record_and_lock(self):
        """기록 및 잠금 테스트"""
        limiter = LoginRateLimiter(max_attempts=3, lockout_minutes=1)

        # 실패 기록
        for _ in range(3):
            limiter.record_attempt("user1", success=False)

        assert limiter.is_locked("user1") is True

    def test_successful_login(self):
        """성공적인 로그인 테스트"""
        limiter = LoginRateLimiter(max_attempts=3, lockout_minutes=1)

        limiter.record_attempt("user2", success=True)
        assert limiter.is_locked("user2") is False


class TestSafeApiCallDecorator:
    """safe_api_call 데코레이터 테스트"""

    def test_successful_call(self):
        """성공적인 호출 테스트"""
        @safe_api_call(max_retries=1)
        def success_func():
            return "success"

        result = success_func()
        assert result == "success"

    def test_failed_call_with_fallback(self):
        """실패한 호출 폴백 테스트"""
        @safe_api_call(max_retries=1, fallback="fallback", notify_on_failure=False)
        def fail_func():
            raise Exception("error")

        result = fail_func()
        assert result == "fallback"

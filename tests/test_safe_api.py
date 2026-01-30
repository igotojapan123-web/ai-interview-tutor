# tests/test_safe_api.py
# Safe API 테스트

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from safe_api import (
    SafeAPIResult,
    safe_openai_call,
    safe_whisper_call,
    validate_json_response,
    sanitize_input,
    validate_response_structure
)


class TestSafeAPIResult:
    """SafeAPIResult 클래스 테스트"""

    def test_success_result(self):
        """성공 결과 테스트"""
        result = SafeAPIResult.success("test data")

        assert result.success is True
        assert result.data == "test data"
        assert result.error is None

    def test_failure_result(self):
        """실패 결과 테스트"""
        result = SafeAPIResult.failure("error message")

        assert result.success is False
        assert result.data is None
        assert result.error == "error message"

    def test_to_dict(self):
        """딕셔너리 변환 테스트"""
        result = SafeAPIResult.success({"key": "value"})
        d = result.to_dict()

        assert d["success"] is True
        assert d["data"]["key"] == "value"


class TestValidateJsonResponse:
    """validate_json_response 함수 테스트"""

    def test_valid_json(self):
        """유효한 JSON 테스트"""
        json_str = '{"name": "test", "value": 123}'
        result = validate_json_response(json_str)

        assert result is not None
        assert result["name"] == "test"

    def test_invalid_json(self):
        """무효한 JSON 테스트"""
        result = validate_json_response("not json")
        assert result is None

    def test_json_in_text(self):
        """텍스트 내 JSON 추출 테스트"""
        text = 'Some text {"key": "value"} more text'
        result = validate_json_response(text)

        assert result is not None
        assert result["key"] == "value"


class TestSanitizeInput:
    """sanitize_input 함수 테스트"""

    def test_basic_sanitize(self):
        """기본 정제 테스트"""
        result = sanitize_input("hello world")
        assert result == "hello world"

    def test_strip_whitespace(self):
        """공백 제거 테스트"""
        result = sanitize_input("  hello  ")
        assert result == "hello"

    def test_max_length(self):
        """최대 길이 테스트"""
        long_text = "a" * 2000
        result = sanitize_input(long_text, max_length=100)
        assert len(result) == 100

    def test_none_input(self):
        """None 입력 테스트"""
        result = sanitize_input(None)
        assert result == ""

    def test_non_string_input(self):
        """비문자열 입력 테스트"""
        result = sanitize_input(123)
        assert result == "123"


class TestValidateResponseStructure:
    """validate_response_structure 함수 테스트"""

    def test_valid_structure(self):
        """유효한 구조 테스트"""
        data = {"name": "test", "value": 123}
        required = ["name", "value"]

        is_valid, missing = validate_response_structure(data, required)

        assert is_valid is True
        assert len(missing) == 0

    def test_missing_keys(self):
        """누락된 키 테스트"""
        data = {"name": "test"}
        required = ["name", "value", "other"]

        is_valid, missing = validate_response_structure(data, required)

        assert is_valid is False
        assert "value" in missing
        assert "other" in missing


class TestSafeOpenAICall:
    """safe_openai_call 함수 테스트"""

    def test_with_mock_client(self, mock_openai_client):
        """모킹된 클라이언트 테스트"""
        # 이 테스트는 실제 API 키 없이 모킹으로 진행
        pass  # 실제 테스트는 통합 테스트에서


class TestSafeWhisperCall:
    """safe_whisper_call 함수 테스트"""

    def test_with_mock_audio(self, temp_data_dir):
        """모킹된 오디오 테스트"""
        # 가상 오디오 파일 생성 불필요
        pass  # 실제 테스트는 통합 테스트에서

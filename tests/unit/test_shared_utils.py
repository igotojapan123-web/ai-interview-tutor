# tests/unit/test_shared_utils.py
# FlyReady Lab - 공용 유틸리티 단위 테스트
# Stage 3: 대기업 수준 테스트

import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from pathlib import Path
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestAPIKeyManagement:
    """API 키 관리 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('shared_utils.st') as mock:
            mock.session_state = {}
            mock.secrets = {}
            yield mock

    def test_get_api_key_from_session(self, mock_st):
        """세션에서 API 키 가져오기"""
        from shared_utils import get_api_key

        mock_st.session_state["OPENAI_API_KEY"] = "sk-test-key"

        result = get_api_key("OPENAI_API_KEY")
        assert result == "sk-test-key"

    def test_get_api_key_not_found(self, mock_st):
        """API 키 없음"""
        from shared_utils import get_api_key

        result = get_api_key("NONEXISTENT_KEY")
        assert result is None

    def test_set_api_key(self, mock_st):
        """API 키 설정"""
        from shared_utils import set_api_key

        set_api_key("TEST_KEY", "test-value")
        assert mock_st.session_state["TEST_KEY"] == "test-value"

    def test_mask_api_key_long(self):
        """긴 API 키 마스킹"""
        from shared_utils import mask_api_key

        key = "sk-proj-abcdefghijklmnopqrstuvwxyz12345678"
        masked = mask_api_key(key)

        # 원본 키가 그대로 노출되지 않아야 함
        assert key != masked
        # 앞뒤 visible_chars(4)만 보이고 중간은 마스킹
        assert masked.startswith("sk-p")
        assert masked.endswith("5678")
        assert "*" in masked

    def test_mask_api_key_short(self):
        """짧은 API 키 마스킹"""
        from shared_utils import mask_api_key

        key = "short"
        masked = mask_api_key(key)

        assert "short" not in masked or masked == "*****"


class TestJSONFileManagement:
    """JSON 파일 관리 테스트"""

    def test_load_json_existing_file(self, tmp_path):
        """존재하는 JSON 파일 로드"""
        from shared_utils import load_json

        file_path = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        result = load_json(file_path)

        assert result == test_data

    def test_load_json_nonexistent_file(self, tmp_path):
        """존재하지 않는 파일"""
        from shared_utils import load_json

        file_path = tmp_path / "nonexistent.json"
        result = load_json(file_path, default={"default": True})

        assert result == {"default": True}

    def test_load_json_invalid_json(self, tmp_path):
        """잘못된 JSON 파일"""
        from shared_utils import load_json

        file_path = tmp_path / "invalid.json"
        with open(file_path, "w") as f:
            f.write("not valid json {{{")

        result = load_json(file_path, default={})

        assert result == {}

    def test_save_json(self, tmp_path):
        """JSON 파일 저장"""
        from shared_utils import save_json

        file_path = tmp_path / "output.json"
        test_data = {"key": "값", "items": [1, 2, 3]}

        success = save_json(file_path, test_data)

        assert success is True
        assert file_path.exists()

        # 저장된 내용 확인
        with open(file_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded == test_data

    def test_save_json_creates_directory(self, tmp_path):
        """디렉토리 자동 생성"""
        from shared_utils import save_json

        file_path = tmp_path / "subdir" / "nested" / "file.json"
        test_data = {"nested": True}

        success = save_json(file_path, test_data)

        assert success is True
        assert file_path.exists()

    def test_append_to_json_array(self, tmp_path):
        """JSON 배열에 추가"""
        from shared_utils import append_to_json_array, load_json

        file_path = tmp_path / "array.json"

        # 빈 상태에서 추가
        append_to_json_array(file_path, {"item": 1})
        append_to_json_array(file_path, {"item": 2})
        append_to_json_array(file_path, {"item": 3})

        result = load_json(file_path)

        assert len(result) == 3

    def test_append_to_json_array_max_items(self, tmp_path):
        """JSON 배열 최대 항목 수 제한"""
        from shared_utils import append_to_json_array, load_json

        file_path = tmp_path / "limited.json"

        for i in range(10):
            append_to_json_array(file_path, i, max_items=5)

        result = load_json(file_path)

        assert len(result) == 5
        assert result[-1] == 9  # 마지막 항목


class TestSessionStateManagement:
    """세션 상태 관리 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('shared_utils.st') as mock:
            mock.session_state = {}
            yield mock

    def test_init_session_state(self, mock_st):
        """세션 상태 초기화"""
        from shared_utils import init_session_state

        defaults = {"key1": "value1", "key2": 42}
        init_session_state(defaults)

        assert mock_st.session_state["key1"] == "value1"
        assert mock_st.session_state["key2"] == 42

    def test_init_session_state_no_overwrite(self, mock_st):
        """기존 값 덮어쓰지 않음"""
        from shared_utils import init_session_state

        mock_st.session_state["existing"] = "original"

        init_session_state({"existing": "new", "new_key": "value"})

        assert mock_st.session_state["existing"] == "original"
        assert mock_st.session_state["new_key"] == "value"

    def test_get_session_value(self, mock_st):
        """세션 값 가져오기"""
        from shared_utils import get_session_value

        mock_st.session_state["test_key"] = "test_value"

        result = get_session_value("test_key")
        assert result == "test_value"

    def test_get_session_value_default(self, mock_st):
        """세션 값 기본값"""
        from shared_utils import get_session_value

        result = get_session_value("nonexistent", "default")
        assert result == "default"

    def test_set_session_value(self, mock_st):
        """세션 값 설정"""
        from shared_utils import set_session_value

        set_session_value("new_key", "new_value")
        assert mock_st.session_state["new_key"] == "new_value"

    def test_clear_session_keys(self, mock_st):
        """특정 키 삭제"""
        from shared_utils import clear_session_keys

        mock_st.session_state["key1"] = "value1"
        mock_st.session_state["key2"] = "value2"
        mock_st.session_state["keep"] = "value"

        clear_session_keys(["key1", "key2"])

        assert "key1" not in mock_st.session_state
        assert "key2" not in mock_st.session_state
        assert "keep" in mock_st.session_state

    def test_clear_session_prefix(self, mock_st):
        """접두사로 삭제"""
        from shared_utils import clear_session_prefix

        mock_st.session_state["page_data"] = "value"
        mock_st.session_state["page_step"] = 1
        mock_st.session_state["other"] = "keep"

        clear_session_prefix("page_")

        assert "page_data" not in mock_st.session_state
        assert "page_step" not in mock_st.session_state
        assert "other" in mock_st.session_state


class TestTextProcessing:
    """텍스트 처리 테스트"""

    def test_sanitize_text_whitespace(self):
        """공백 정제"""
        from shared_utils import sanitize_text

        result = sanitize_text("  multiple   spaces   ")
        assert result == "multiple spaces"

    def test_sanitize_text_max_length(self):
        """최대 길이 제한"""
        from shared_utils import sanitize_text

        long_text = "가" * 1000
        result = sanitize_text(long_text, max_length=100)

        assert len(result) == 100

    def test_sanitize_text_empty(self):
        """빈 입력"""
        from shared_utils import sanitize_text

        assert sanitize_text("") == ""
        assert sanitize_text(None) == ""

    def test_truncate_text(self):
        """텍스트 자르기"""
        from shared_utils import truncate_text

        result = truncate_text("이것은 긴 텍스트입니다.", max_length=10)

        assert len(result) <= 10
        assert result.endswith("...")

    def test_truncate_text_short(self):
        """짧은 텍스트는 그대로"""
        from shared_utils import truncate_text

        text = "짧은"
        result = truncate_text(text, max_length=100)

        assert result == text

    def test_format_number(self):
        """숫자 포맷팅"""
        from shared_utils import format_number

        assert format_number(1234567) == "1,234,567"
        assert format_number(1234.5678, decimal_places=2) == "1,234.57"

    def test_format_percentage(self):
        """백분율 포맷팅"""
        from shared_utils import format_percentage

        assert format_percentage(75.5) == "75.5%"
        assert format_percentage(100.0, decimal_places=0) == "100%"


class TestDateTimeUtils:
    """날짜/시간 유틸리티 테스트"""

    def test_format_datetime(self):
        """날짜/시간 포맷팅"""
        from shared_utils import format_datetime

        dt = datetime(2024, 1, 15, 14, 30)
        result = format_datetime(dt)

        assert "2024-01-15" in result
        assert "14:30" in result

    def test_format_datetime_now(self):
        """현재 시간 포맷팅"""
        from shared_utils import format_datetime

        result = format_datetime()
        assert len(result) > 0

    def test_format_date(self):
        """날짜 포맷팅"""
        from shared_utils import format_date

        dt = datetime(2024, 12, 25)
        result = format_date(dt)

        assert result == "2024-12-25"

    def test_format_time(self):
        """시간 포맷팅"""
        from shared_utils import format_time

        dt = datetime(2024, 1, 1, 9, 5)
        result = format_time(dt)

        assert result == "09:05"

    def test_format_relative_time_seconds(self):
        """상대 시간 - 초"""
        from shared_utils import format_relative_time

        now = datetime.now()
        dt = now - timedelta(seconds=30)
        result = format_relative_time(dt)

        assert "방금" in result

    def test_format_relative_time_minutes(self):
        """상대 시간 - 분"""
        from shared_utils import format_relative_time

        now = datetime.now()
        dt = now - timedelta(minutes=5)
        result = format_relative_time(dt)

        assert "분 전" in result

    def test_format_relative_time_hours(self):
        """상대 시간 - 시간"""
        from shared_utils import format_relative_time

        now = datetime.now()
        dt = now - timedelta(hours=3)
        result = format_relative_time(dt)

        assert "시간 전" in result

    def test_format_relative_time_days(self):
        """상대 시간 - 일"""
        from shared_utils import format_relative_time

        now = datetime.now()
        dt = now - timedelta(days=2)
        result = format_relative_time(dt)

        assert "일 전" in result


class TestFileUtils:
    """파일 유틸리티 테스트"""

    def test_ensure_dir(self, tmp_path):
        """디렉토리 생성"""
        from shared_utils import ensure_dir

        new_dir = tmp_path / "new_directory"
        result = ensure_dir(new_dir)

        assert result.exists()
        assert result.is_dir()

    def test_get_file_size_str(self):
        """파일 크기 문자열"""
        from shared_utils import get_file_size_str

        assert "B" in get_file_size_str(500)
        assert "KB" in get_file_size_str(1024)
        assert "MB" in get_file_size_str(1024 * 1024)
        assert "GB" in get_file_size_str(1024 * 1024 * 1024)

    def test_is_valid_filename_safe(self):
        """안전한 파일명"""
        from shared_utils import is_valid_filename

        assert is_valid_filename("document.pdf") is True
        assert is_valid_filename("my_file-123.txt") is True
        assert is_valid_filename("image.jpg") is True

    def test_is_valid_filename_unsafe(self):
        """위험한 파일명"""
        from shared_utils import is_valid_filename

        assert is_valid_filename("../etc/passwd") is False
        assert is_valid_filename("/root/file") is False
        assert is_valid_filename("file\x00.txt") is False


class TestListDictUtils:
    """리스트/딕셔너리 유틸리티 테스트"""

    def test_safe_get_dict(self):
        """딕셔너리 안전 접근"""
        from shared_utils import safe_get

        data = {"key": "value"}

        assert safe_get(data, "key") == "value"
        assert safe_get(data, "missing", "default") == "default"

    def test_safe_get_list(self):
        """리스트 안전 접근"""
        from shared_utils import safe_get

        data = [1, 2, 3]

        assert safe_get(data, 0) == 1
        assert safe_get(data, 10, "default") == "default"

    def test_chunk_list(self):
        """리스트 청크 분할"""
        from shared_utils import chunk_list

        items = list(range(10))
        chunks = chunk_list(items, 3)

        assert len(chunks) == 4
        assert chunks[0] == [0, 1, 2]
        assert chunks[-1] == [9]

    def test_flatten_list(self):
        """리스트 평탄화"""
        from shared_utils import flatten_list

        nested = [[1, 2], [3, [4, 5]], 6]
        result = flatten_list(nested)

        assert result == [1, 2, 3, 4, 5, 6]

    def test_remove_duplicates(self):
        """중복 제거"""
        from shared_utils import remove_duplicates

        items = [1, 2, 2, 3, 1, 4]
        result = remove_duplicates(items)

        assert result == [1, 2, 3, 4]

    def test_remove_duplicates_with_key(self):
        """키 기준 중복 제거"""
        from shared_utils import remove_duplicates

        items = [
            {"id": 1, "name": "a"},
            {"id": 2, "name": "b"},
            {"id": 1, "name": "c"},
        ]
        result = remove_duplicates(items, key="id")

        assert len(result) == 2


class TestValidation:
    """유효성 검사 테스트"""

    def test_is_valid_email_valid(self):
        """유효한 이메일"""
        from shared_utils import is_valid_email

        assert is_valid_email("test@example.com") is True
        assert is_valid_email("user.name@domain.co.kr") is True

    def test_is_valid_email_invalid(self):
        """잘못된 이메일"""
        from shared_utils import is_valid_email

        assert is_valid_email("not-email") is False
        assert is_valid_email("@domain.com") is False
        assert is_valid_email("") is False

    def test_is_valid_phone_valid(self):
        """유효한 전화번호"""
        from shared_utils import is_valid_phone

        assert is_valid_phone("010-1234-5678") is True
        assert is_valid_phone("01012345678") is True
        assert is_valid_phone("02-123-4567") is True

    def test_is_valid_phone_invalid(self):
        """잘못된 전화번호"""
        from shared_utils import is_valid_phone

        assert is_valid_phone("1234-5678") is False
        assert is_valid_phone("") is False

    def test_is_valid_url_valid(self):
        """유효한 URL"""
        from shared_utils import is_valid_url

        assert is_valid_url("https://www.example.com") is True
        assert is_valid_url("http://localhost:8080") is True

    def test_is_valid_url_invalid(self):
        """잘못된 URL"""
        from shared_utils import is_valid_url

        assert is_valid_url("not-a-url") is False
        assert is_valid_url("ftp://invalid") is False


class TestCaching:
    """캐싱 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('shared_utils.st') as mock:
            mock.session_state = {}
            yield mock

    def test_get_cached_loads_fresh(self, mock_st):
        """캐시 미스 시 로드"""
        from shared_utils import get_cached

        load_count = [0]

        def loader():
            load_count[0] += 1
            return "data"

        result = get_cached("test_key", loader)

        assert result == "data"
        assert load_count[0] == 1

    def test_get_cached_uses_cache(self, mock_st):
        """캐시 히트"""
        from shared_utils import get_cached
        import time

        load_count = [0]

        def loader():
            load_count[0] += 1
            return "data"

        # 첫 호출
        get_cached("test_key", loader, ttl_seconds=60)
        # 두 번째 호출 (캐시 사용)
        result = get_cached("test_key", loader, ttl_seconds=60)

        assert result == "data"
        assert load_count[0] == 1  # 한 번만 로드

    def test_clear_cache(self, mock_st):
        """캐시 삭제"""
        from shared_utils import get_cached, clear_cache

        mock_st.session_state["_cache_test"] = "cached_value"
        mock_st.session_state["_cache_test_time"] = 9999999999

        clear_cache("test")

        assert "_cache_test" not in mock_st.session_state


class TestUserActionLogging:
    """사용자 액션 로깅 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹 - 속성 접근 지원"""
        # MockSessionState를 사용하여 dict와 속성 접근 모두 지원
        class AttrDict(dict):
            def __setattr__(self, key, value):
                self[key] = value
            def __getattr__(self, key):
                return self.get(key)

        with patch('shared_utils.st') as mock:
            mock.session_state = AttrDict()
            yield mock

    def test_log_user_action(self, mock_st):
        """액션 로깅"""
        from shared_utils import log_user_action

        log_user_action("button_click", {"button_id": "submit"})

        assert "user_action_log" in mock_st.session_state
        assert len(mock_st.session_state["user_action_log"]) == 1

    def test_get_user_action_log(self, mock_st):
        """로그 조회"""
        from shared_utils import log_user_action, get_user_action_log

        log_user_action("action1")
        log_user_action("action2")

        logs = get_user_action_log()

        assert len(logs) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

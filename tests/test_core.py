"""
핵심 모듈 테스트
"""
import pytest
import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestImports:
    """모듈 임포트 테스트"""

    def test_import_config(self):
        """config 모듈 임포트"""
        import config
        assert hasattr(config, 'AIRLINES')
        assert len(config.AIRLINES) > 0

    def test_import_env_config(self):
        """env_config 모듈 임포트"""
        import env_config
        assert hasattr(env_config, 'OPENAI_API_KEY')
        assert hasattr(env_config, 'check_openai_key')

    def test_import_logging_config(self):
        """logging_config 모듈 임포트"""
        import logging_config
        assert hasattr(logging_config, 'get_logger')
        assert hasattr(logging_config, 'AppError')

    def test_import_validation(self):
        """validation 모듈 임포트"""
        import validation
        assert hasattr(validation, 'sanitize_text')
        assert hasattr(validation, 'validate_text_input')

    def test_import_api_utils(self):
        """api_utils 모듈 임포트"""
        import api_utils
        assert hasattr(api_utils, 'get_api_key')
        assert hasattr(api_utils, 'call_openai_chat')


class TestValidation:
    """입력 검증 테스트"""

    def test_sanitize_text_basic(self):
        """기본 텍스트 정제"""
        from validation import sanitize_text
        result = sanitize_text("  Hello World  ")
        assert result == "Hello World"

    def test_sanitize_text_html_escape(self):
        """HTML 이스케이프"""
        from validation import sanitize_text
        result = sanitize_text("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_sanitize_text_max_length(self):
        """최대 길이 제한"""
        from validation import sanitize_text
        long_text = "A" * 100000
        result = sanitize_text(long_text, max_length=1000)
        assert len(result) <= 1000

    def test_validate_text_input_empty(self):
        """빈 입력 검증"""
        from validation import validate_text_input
        is_valid, cleaned, message = validate_text_input("")
        assert not is_valid
        assert "입력" in message

    def test_validate_text_input_valid(self):
        """유효한 입력 검증"""
        from validation import validate_text_input
        is_valid, cleaned, message = validate_text_input("Hello World")
        assert is_valid
        assert cleaned == "Hello World"

    def test_is_safe_filename(self):
        """안전한 파일명 검증"""
        from validation import is_safe_filename
        assert is_safe_filename("document.pdf")
        assert is_safe_filename("my_file_123.txt")
        assert not is_safe_filename("../etc/passwd")
        assert not is_safe_filename("file<script>.txt")


class TestLogging:
    """로깅 테스트"""

    def test_get_logger(self):
        """로거 생성"""
        from logging_config import get_logger
        logger = get_logger("test_module")
        assert logger is not None
        assert logger.name == "test_module"

    def test_custom_exceptions(self):
        """커스텀 예외 클래스"""
        from logging_config import AppError, APIError, ValidationError

        with pytest.raises(AppError):
            raise AppError("테스트 에러")

        with pytest.raises(APIError):
            raise APIError("API 에러")

        with pytest.raises(ValidationError):
            raise ValidationError("검증 에러")


class TestEnvConfig:
    """환경 설정 테스트"""

    def test_validate_api_key_format(self):
        """API 키 형식 검증"""
        from env_config import validate_api_key

        # OpenAI 키 (최소 40자 이상 필요)
        long_key = "sk-proj-" + "a" * 40
        is_valid, _ = validate_api_key(long_key, "openai")
        assert is_valid

        is_valid, _ = validate_api_key("invalid-key", "openai")
        assert not is_valid

    def test_mask_api_key(self):
        """API 키 마스킹"""
        from env_config import mask_api_key

        masked = mask_api_key("sk-proj-abcdefghijklmnopqrstuvwxyz")
        assert "sk-proj-" in masked
        assert "..." in masked
        assert len(masked) < len("sk-proj-abcdefghijklmnopqrstuvwxyz")

        # 짧은 키는 *** 반환
        short_masked = mask_api_key("short")
        assert short_masked == "***"


class TestConfig:
    """설정 데이터 테스트"""

    def test_airlines_list(self):
        """항공사 목록"""
        from config import AIRLINES
        assert "대한항공" in AIRLINES
        assert "아시아나항공" in AIRLINES
        assert len(AIRLINES) >= 5

    def test_airline_values(self):
        """항공사별 인재상"""
        from config import AIRLINE_VALUES
        assert "대한항공" in AIRLINE_VALUES
        assert len(AIRLINE_VALUES["대한항공"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

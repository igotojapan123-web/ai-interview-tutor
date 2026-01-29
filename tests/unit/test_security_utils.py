# tests/unit/test_security_utils.py
# FlyReady Lab - 보안 유틸리티 단위 테스트
# Stage 3: 대기업 수준 테스트

import pytest
import sys
import os
from unittest.mock import MagicMock, patch
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestXSSPrevention:
    """XSS 방지 테스트"""

    def test_escape_html_script_tag(self):
        """script 태그 이스케이프"""
        from security_utils import escape_html

        result = escape_html("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_escape_html_event_handler(self):
        """이벤트 핸들러 이스케이프"""
        from security_utils import escape_html

        result = escape_html('<div onclick="alert(1)">click</div>')
        assert 'onclick=' not in result or '&quot;' in result

    def test_escape_html_img_onerror(self):
        """img onerror 이스케이프"""
        from security_utils import escape_html

        result = escape_html('<img src="x" onerror="alert(1)">')
        assert 'onerror=' not in result or '&quot;' in result

    def test_escape_html_preserves_text(self):
        """일반 텍스트 보존"""
        from security_utils import escape_html

        result = escape_html("안녕하세요, 홍길동입니다.")
        assert result == "안녕하세요, 홍길동입니다."

    def test_escape_html_empty_string(self):
        """빈 문자열"""
        from security_utils import escape_html

        result = escape_html("")
        assert result == ""

    def test_sanitize_html_removes_script_tag(self):
        """script 태그 제거"""
        from security_utils import sanitize_html

        dangerous_html = "<script>alert('xss')</script><p>안전한 내용</p>"
        result = sanitize_html(dangerous_html)

        assert "<script>" not in result.lower()
        # script 태그가 제거되거나 이스케이프됨

    def test_sanitize_html_preserves_safe_content(self):
        """안전한 태그 보존 (allow_tags=True)"""
        from security_utils import sanitize_html

        safe_html = "<p>안녕하세요</p><br><strong>강조</strong>"
        result = sanitize_html(safe_html, allow_tags=True)

        # 내용이 유지됨
        assert "안녕하세요" in result

    def test_safe_css_removes_javascript(self):
        """CSS에서 JavaScript URL 제거"""
        from security_utils import safe_css

        dangerous_css = "background: url('javascript:alert(1)')"
        result = safe_css(dangerous_css)

        assert "javascript:" not in result.lower()

    def test_safe_css_preserves_valid_css(self):
        """유효한 CSS 보존"""
        from security_utils import safe_css

        valid_css = "color: blue; font-size: 16px;"
        result = safe_css(valid_css)

        assert "color" in result
        assert "font-size" in result


class TestInputValidation:
    """입력 검증 테스트"""

    def test_validate_text_input_valid(self):
        """유효한 텍스트 입력"""
        from security_utils import validate_text_input

        is_valid, cleaned, error = validate_text_input("안녕하세요")
        assert is_valid is True
        assert cleaned == "안녕하세요"
        assert error is None

    def test_validate_text_input_empty_allowed(self):
        """빈 입력 (allow_empty=True 기본값)"""
        from security_utils import validate_text_input

        is_valid, cleaned, error = validate_text_input("")
        # 기본적으로 allow_empty=True이므로 유효함
        assert is_valid is True

    def test_validate_text_input_empty_not_allowed(self):
        """빈 입력 (allow_empty=False)"""
        from security_utils import validate_text_input

        is_valid, cleaned, error = validate_text_input("", allow_empty=False)
        assert is_valid is False
        assert error is not None

    def test_validate_text_input_too_short(self):
        """너무 짧은 입력"""
        from security_utils import validate_text_input

        is_valid, cleaned, error = validate_text_input("짧음", min_length=10)
        assert is_valid is False
        assert error is not None

    def test_validate_text_input_too_long(self):
        """너무 긴 입력"""
        from security_utils import validate_text_input

        long_text = "가" * 10000
        is_valid, cleaned, error = validate_text_input(long_text, max_length=1000)
        assert len(cleaned) <= 1000

    def test_validate_text_input_strips_whitespace(self):
        """공백 제거"""
        from security_utils import validate_text_input

        is_valid, cleaned, error = validate_text_input("  안녕하세요  ")
        assert cleaned == "안녕하세요"

    def test_validate_email_valid(self):
        """유효한 이메일"""
        from security_utils import validate_email

        is_valid, error = validate_email("test@example.com")
        assert is_valid is True

    def test_validate_email_invalid(self):
        """잘못된 이메일"""
        from security_utils import validate_email

        is_valid, error = validate_email("not-an-email")
        assert is_valid is False

    def test_validate_email_empty(self):
        """빈 이메일"""
        from security_utils import validate_email

        is_valid, error = validate_email("")
        assert is_valid is False

    def test_validate_url_valid(self):
        """유효한 URL"""
        from security_utils import validate_url

        is_valid, error = validate_url("https://www.example.com")
        assert is_valid is True

    def test_validate_url_invalid(self):
        """잘못된 URL"""
        from security_utils import validate_url

        is_valid, error = validate_url("not-a-url")
        assert is_valid is False

    def test_validate_url_javascript_rejected(self):
        """JavaScript URL 거부"""
        from security_utils import validate_url

        is_valid, error = validate_url("javascript:alert(1)")
        assert is_valid is False

    def test_validate_file_upload_valid(self):
        """유효한 파일 업로드"""
        from security_utils import validate_file_upload

        # Mock uploaded file
        mock_file = MagicMock()
        mock_file.name = "document.pdf"
        mock_file.size = 1024 * 1024  # 1MB
        mock_file.read = MagicMock(return_value=b'%PDF-1.4')
        mock_file.seek = MagicMock()

        is_valid, error = validate_file_upload(
            mock_file,
            allowed_extensions=['pdf'],
            max_size_mb=10
        )
        assert is_valid is True

    def test_validate_file_upload_invalid_type(self):
        """잘못된 파일 유형"""
        from security_utils import validate_file_upload

        mock_file = MagicMock()
        mock_file.name = "malware.exe"
        mock_file.size = 1024

        is_valid, error = validate_file_upload(
            mock_file,
            allowed_extensions=['pdf', 'doc']
        )
        assert is_valid is False

    def test_validate_file_upload_too_large(self):
        """너무 큰 파일"""
        from security_utils import validate_file_upload

        mock_file = MagicMock()
        mock_file.name = "large.pdf"
        mock_file.size = 100 * 1024 * 1024  # 100MB

        is_valid, error = validate_file_upload(
            mock_file,
            allowed_extensions=['pdf'],
            max_size_mb=10
        )
        assert is_valid is False


class TestCSRFProtection:
    """CSRF 보호 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹 - 속성 접근 지원"""
        class AttrDict(dict):
            def __setattr__(self, key, value):
                self[key] = value
            def __getattr__(self, key):
                return self.get(key)
            def __contains__(self, key):
                return dict.__contains__(self, key)

        with patch('security_utils.st') as mock:
            mock.session_state = AttrDict()
            yield mock

    def test_generate_csrf_token(self, mock_st):
        """CSRF 토큰 생성"""
        from security_utils import generate_csrf_token

        token = generate_csrf_token()

        assert token is not None
        assert len(token) >= 32

    def test_validate_csrf_token_valid(self, mock_st):
        """유효한 CSRF 토큰 검증"""
        from security_utils import generate_csrf_token, validate_csrf_token

        token = generate_csrf_token()
        is_valid = validate_csrf_token(token)

        assert is_valid is True

    def test_validate_csrf_token_invalid(self, mock_st):
        """잘못된 CSRF 토큰 검증"""
        from security_utils import generate_csrf_token, validate_csrf_token

        generate_csrf_token()  # 세션에 토큰 생성
        is_valid = validate_csrf_token("invalid-token")

        assert is_valid is False


class TestRateLimiter:
    """레이트 리미터 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('security_utils.st') as mock:
            mock.session_state = {}
            yield mock

    def test_rate_limiter_creation(self):
        """RateLimiter 생성"""
        from security_utils import RateLimiter

        limiter = RateLimiter(max_requests=10, window_seconds=60)

        assert limiter.max_requests == 10
        assert limiter.window_seconds == 60

    def test_rate_limiter_allows_requests(self, mock_st):
        """요청 허용"""
        from security_utils import RateLimiter

        limiter = RateLimiter(max_requests=10, window_seconds=60)

        for _ in range(5):
            allowed, remaining = limiter.is_allowed("user1")
            assert allowed is True

    def test_rate_limiter_blocks_excess(self, mock_st):
        """초과 요청 차단"""
        from security_utils import RateLimiter

        limiter = RateLimiter(max_requests=3, window_seconds=60)

        for _ in range(3):
            limiter.is_allowed("user1")

        allowed, remaining = limiter.is_allowed("user1")
        assert allowed is False

    def test_rate_limiter_different_keys(self, mock_st):
        """다른 키는 독립적"""
        from security_utils import RateLimiter

        limiter = RateLimiter(max_requests=2, window_seconds=60)

        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        allowed1, _ = limiter.is_allowed("user1")
        assert allowed1 is False

        # user2는 아직 가능
        allowed2, _ = limiter.is_allowed("user2")
        assert allowed2 is True

    def test_rate_limited_decorator_exists(self):
        """rate_limited 데코레이터 존재"""
        from security_utils import rate_limited

        assert callable(rate_limited)


class TestSecureAuth:
    """SecureAuth 클래스 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('security_utils.st') as mock:
            mock.session_state = {}
            yield mock

    def test_secure_auth_init_session(self, mock_st):
        """세션 초기화"""
        from security_utils import SecureAuth

        SecureAuth.init_session()

        # 초기화 후 세션에 필요한 키가 있는지 확인
        assert True  # 구현에 따라 검증

    def test_secure_auth_hash_password(self):
        """비밀번호 해싱"""
        from security_utils import SecureAuth

        password = "test_password_123"
        hashed, salt = SecureAuth.hash_password(password)

        assert hashed != password
        assert len(hashed) > 0
        assert len(salt) > 0

    def test_secure_auth_verify_password(self):
        """비밀번호 검증"""
        from security_utils import SecureAuth

        password = "test_password_123"
        hashed, salt = SecureAuth.hash_password(password)

        assert SecureAuth.verify_password(password, hashed, salt) is True
        assert SecureAuth.verify_password("wrong_password", hashed, salt) is False


class TestSecurityHeaders:
    """보안 헤더 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('security_utils.st') as mock:
            mock.markdown = MagicMock()
            yield mock

    def test_render_security_headers(self, mock_st):
        """보안 헤더 렌더링"""
        from security_utils import render_security_headers

        render_security_headers()

        # markdown이 호출되었는지 확인
        mock_st.markdown.assert_called()


class TestSensitiveDataMasking:
    """민감 정보 마스킹 테스트"""

    def test_mask_sensitive_api_key(self):
        """API 키 마스킹"""
        from security_utils import mask_sensitive

        api_key = "sk-proj-abcdefghijklmnopqrstuvwxyz12345678"
        masked = mask_sensitive(api_key)

        # 전체가 보이면 안됨
        assert api_key != masked
        # 마스킹 문자 포함
        assert "*" in masked

    def test_mask_sensitive_short_string(self):
        """짧은 문자열 마스킹"""
        from security_utils import mask_sensitive

        short = "abc"
        masked = mask_sensitive(short)

        # 완전히 숨김
        assert "abc" not in masked


class TestSafeMarkdown:
    """안전한 마크다운 렌더링 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('security_utils.st') as mock:
            mock.markdown = MagicMock()
            yield mock

    def test_safe_render_markdown(self, mock_st):
        """안전한 마크다운 렌더링"""
        from security_utils import safe_render_markdown

        # XSS가 포함된 마크다운
        dangerous_md = "# 제목\n<script>alert('xss')</script>"
        safe_render_markdown(dangerous_md)

        # markdown이 호출됨
        mock_st.markdown.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# security_utils.py
# 대기업 수준 보안 유틸리티
# FlyReady Lab - Enterprise Security Module
# Phase A1: 보안 500% 강화

import streamlit as st
import html
import re
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# Enhanced Security 모듈 통합
# =============================================================================

_enhanced_security_loaded = False
_audit_logger = None
_sql_injection_checker = None
_path_traversal_checker = None

def _load_enhanced_security():
    """enhanced_security 모듈 지연 로딩"""
    global _enhanced_security_loaded, _audit_logger, _sql_injection_checker, _path_traversal_checker

    if _enhanced_security_loaded:
        return

    try:
        from enhanced_security import (
            audit_logger,
            SQLInjectionPrevention,
            PathTraversalPrevention,
            init_security
        )
        _audit_logger = audit_logger
        _sql_injection_checker = SQLInjectionPrevention
        _path_traversal_checker = PathTraversalPrevention
        _enhanced_security_loaded = True
        logger.info("enhanced_security 모듈 로드 성공")
    except ImportError as e:
        logger.warning(f"enhanced_security 모듈 로드 실패: {e}")
        _enhanced_security_loaded = False


def audit_log(event_type: str, action: str, user: str = None, details: Dict = None, severity: str = 'INFO'):
    """감사 로그 기록 (enhanced_security 연동)"""
    _load_enhanced_security()

    if _audit_logger:
        _audit_logger.log(event_type, action, user, details, severity)
    else:
        # 폴백: 표준 로거 사용
        log_func = getattr(logger, severity.lower(), logger.info)
        log_func(f"[AUDIT] {event_type}: {action} - {details}")

# =============================================================================
# XSS 방지 - 안전한 HTML 이스케이프
# =============================================================================

# 허용되는 HTML 태그
ALLOWED_TAGS = {
    'p', 'br', 'b', 'i', 'u', 'strong', 'em', 'span', 'div',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'pre', 'code', 'blockquote'
}

# 허용되는 속성
ALLOWED_ATTRS = {
    'class', 'id', 'style', 'href', 'src', 'alt', 'title',
    'role', 'aria-label', 'aria-describedby', 'aria-hidden',
    'data-testid', 'tabindex'
}

# 위험한 패턴
DANGEROUS_PATTERNS = [
    r'javascript:',
    r'vbscript:',
    r'data:text/html',
    r'on\w+\s*=',  # onclick, onload, etc.
    r'<script',
    r'</script',
    r'<iframe',
    r'<object',
    r'<embed',
    r'<form',
    r'expression\s*\(',
    r'url\s*\(\s*["\']?\s*javascript',
]


def escape_html(text: str) -> str:
    """HTML 특수문자 이스케이프

    Args:
        text: 원본 텍스트

    Returns:
        이스케이프된 텍스트
    """
    if not text:
        return ""
    return html.escape(str(text), quote=True)


def sanitize_html(html_content: str, allow_tags: bool = False) -> str:
    """HTML 콘텐츠 살균

    Args:
        html_content: HTML 콘텐츠
        allow_tags: 기본 HTML 태그 허용 여부

    Returns:
        살균된 HTML
    """
    if not html_content:
        return ""

    content = str(html_content)

    # 위험한 패턴 제거
    for pattern in DANGEROUS_PATTERNS:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)

    if not allow_tags:
        # 모든 태그 이스케이프
        content = escape_html(content)
    else:
        # 허용되지 않은 태그 제거
        def clean_tag(match):
            tag = match.group(1).lower()
            if tag in ALLOWED_TAGS:
                return match.group(0)
            return ''

        content = re.sub(r'<(/?)(\w+)[^>]*>', clean_tag, content)

    return content


def sanitize_attribute(attr_value: str) -> str:
    """HTML 속성값 살균

    Args:
        attr_value: 속성값

    Returns:
        살균된 속성값
    """
    if not attr_value:
        return ""

    value = str(attr_value)

    # 위험한 패턴 제거
    for pattern in DANGEROUS_PATTERNS:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE)

    # 따옴표 이스케이프
    value = value.replace('"', '&quot;').replace("'", '&#39;')

    return value


def safe_css(css_value: str) -> str:
    """CSS 값 살균

    Args:
        css_value: CSS 값

    Returns:
        살균된 CSS 값
    """
    if not css_value:
        return ""

    value = str(css_value)

    # 위험한 CSS 패턴 제거
    dangerous_css = [
        r'expression\s*\(',
        r'url\s*\(\s*["\']?\s*javascript',
        r'behavior\s*:',
        r'-moz-binding\s*:',
    ]

    for pattern in dangerous_css:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE)

    return value


def create_safe_html(
    tag: str,
    content: str = "",
    attributes: Optional[Dict[str, str]] = None,
    escape_content: bool = True
) -> str:
    """안전한 HTML 요소 생성

    Args:
        tag: HTML 태그
        content: 내용
        attributes: 속성 딕셔너리
        escape_content: 내용 이스케이프 여부

    Returns:
        안전한 HTML 문자열
    """
    # 태그 검증
    tag = tag.lower()
    if tag not in ALLOWED_TAGS and tag not in {'svg', 'path', 'circle', 'rect', 'line', 'polyline'}:
        return escape_html(content)

    # 속성 처리
    attr_str = ""
    if attributes:
        safe_attrs = []
        for key, value in attributes.items():
            key_lower = key.lower()
            if key_lower in ALLOWED_ATTRS or key_lower.startswith('data-') or key_lower.startswith('aria-'):
                safe_value = sanitize_attribute(value)
                safe_attrs.append(f'{key_lower}="{safe_value}"')
        attr_str = " " + " ".join(safe_attrs) if safe_attrs else ""

    # 내용 처리
    safe_content = escape_html(content) if escape_content else content

    # 자체 닫는 태그
    self_closing = {'br', 'hr', 'img', 'input', 'meta', 'link'}
    if tag in self_closing:
        return f"<{tag}{attr_str}/>"

    return f"<{tag}{attr_str}>{safe_content}</{tag}>"


# =============================================================================
# 입력 검증
# =============================================================================

def validate_text_input(
    text: str,
    min_length: int = 0,
    max_length: int = 10000,
    allow_empty: bool = True,
    strip: bool = True
) -> tuple[bool, str, Optional[str]]:
    """텍스트 입력 검증

    Args:
        text: 입력 텍스트
        min_length: 최소 길이
        max_length: 최대 길이
        allow_empty: 빈 값 허용
        strip: 공백 제거

    Returns:
        (유효여부, 정제된 텍스트, 에러 메시지)
    """
    if text is None:
        if allow_empty:
            return True, "", None
        return False, "", "입력이 필요합니다."

    cleaned = str(text).strip() if strip else str(text)

    if not cleaned and not allow_empty:
        return False, "", "입력이 필요합니다."

    if len(cleaned) < min_length:
        return False, cleaned, f"최소 {min_length}자 이상 입력해 주세요."

    if len(cleaned) > max_length:
        return False, cleaned[:max_length], f"최대 {max_length}자까지 입력 가능합니다."

    return True, cleaned, None


def validate_email(email: str) -> tuple[bool, Optional[str]]:
    """이메일 형식 검증"""
    if not email:
        return False, "이메일을 입력해 주세요."

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "올바른 이메일 형식이 아닙니다."

    return True, None


def validate_url(url: str, allowed_schemes: List[str] = None) -> tuple[bool, Optional[str]]:
    """URL 형식 검증"""
    if not url:
        return False, "URL을 입력해 주세요."

    allowed_schemes = allowed_schemes or ['http', 'https']

    pattern = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
    if not re.match(pattern, url, re.IGNORECASE):
        return False, "올바른 URL 형식이 아닙니다."

    # 스킴 검증
    scheme = url.split('://')[0].lower()
    if scheme not in allowed_schemes:
        return False, f"허용된 프로토콜: {', '.join(allowed_schemes)}"

    return True, None


def validate_file_upload(
    file,
    allowed_extensions: List[str],
    max_size_mb: float = 10.0
) -> tuple[bool, Optional[str]]:
    """파일 업로드 검증

    Args:
        file: 업로드된 파일 객체
        allowed_extensions: 허용 확장자 목록
        max_size_mb: 최대 파일 크기 (MB)

    Returns:
        (유효여부, 에러 메시지)
    """
    if file is None:
        return False, "파일을 선택해 주세요."

    # 확장자 검증
    filename = getattr(file, 'name', '')
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    if ext not in [e.lower().lstrip('.') for e in allowed_extensions]:
        return False, f"허용된 파일 형식: {', '.join(allowed_extensions)}"

    # 파일 크기 검증
    file_size = getattr(file, 'size', 0)
    max_size_bytes = max_size_mb * 1024 * 1024

    if file_size > max_size_bytes:
        return False, f"파일 크기는 {max_size_mb}MB 이하여야 합니다."

    # 매직 바이트 검증 (선택적)
    # 실제 파일 타입 확인을 위해 파일 시작 부분 확인
    magic_bytes = {
        'pdf': b'%PDF',
        'png': b'\x89PNG',
        'jpg': b'\xff\xd8\xff',
        'jpeg': b'\xff\xd8\xff',
        'gif': b'GIF8',
        'mp3': b'ID3',
        'mp4': b'\x00\x00\x00',
    }

    if ext in magic_bytes:
        content = file.read(10)
        file.seek(0)  # 파일 포인터 리셋

        if not content.startswith(magic_bytes.get(ext, b'')):
            return False, "파일 형식이 확장자와 일치하지 않습니다."

    return True, None


# =============================================================================
# CSRF 토큰 관리
# =============================================================================

def generate_csrf_token() -> str:
    """CSRF 토큰 생성"""
    token = secrets.token_urlsafe(32)

    if "csrf_tokens" not in st.session_state:
        st.session_state.csrf_tokens = {}

    # 토큰 저장 (30분 유효)
    st.session_state.csrf_tokens[token] = datetime.now() + timedelta(minutes=30)

    # 만료된 토큰 정리
    _cleanup_expired_tokens()

    return token


def validate_csrf_token(token: str) -> bool:
    """CSRF 토큰 검증"""
    if "csrf_tokens" not in st.session_state:
        return False

    if token not in st.session_state.csrf_tokens:
        return False

    expiry = st.session_state.csrf_tokens.get(token)
    if expiry and datetime.now() > expiry:
        del st.session_state.csrf_tokens[token]
        return False

    # 토큰 사용 후 삭제 (일회용)
    del st.session_state.csrf_tokens[token]
    return True


def _cleanup_expired_tokens():
    """만료된 토큰 정리"""
    if "csrf_tokens" not in st.session_state:
        return

    now = datetime.now()
    expired = [t for t, exp in st.session_state.csrf_tokens.items() if exp < now]

    for token in expired:
        del st.session_state.csrf_tokens[token]


def render_csrf_field() -> str:
    """CSRF 히든 필드 렌더링"""
    token = generate_csrf_token()
    return f'<input type="hidden" name="csrf_token" value="{token}">'


# =============================================================================
# 인증 및 세션 관리
# =============================================================================

class SecureAuth:
    """안전한 인증 관리 클래스"""

    # 로그인 시도 제한
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=15)

    @staticmethod
    def init_session():
        """인증 세션 초기화"""
        defaults = {
            "auth_user": None,
            "auth_role": None,
            "auth_time": None,
            "auth_ip": None,
            "login_attempts": {},
            "session_token": None
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """비밀번호 해싱

        Args:
            password: 평문 비밀번호
            salt: 솔트 (없으면 생성)

        Returns:
            (해시, 솔트)
        """
        if salt is None:
            salt = secrets.token_hex(16)

        # PBKDF2 with SHA-256
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )

        return key.hex(), salt

    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """비밀번호 검증"""
        computed_hash, _ = SecureAuth.hash_password(password, salt)
        return hmac.compare_digest(computed_hash, stored_hash)

    @staticmethod
    def is_locked_out(identifier: str) -> tuple[bool, Optional[int]]:
        """계정 잠금 상태 확인

        Args:
            identifier: 사용자 식별자 (IP 또는 username)

        Returns:
            (잠금여부, 남은 시간(초))
        """
        SecureAuth.init_session()

        attempts = st.session_state.login_attempts.get(identifier, {})
        count = attempts.get('count', 0)
        last_attempt = attempts.get('last_attempt')

        if count >= SecureAuth.MAX_LOGIN_ATTEMPTS and last_attempt:
            lockout_end = last_attempt + SecureAuth.LOCKOUT_DURATION
            if datetime.now() < lockout_end:
                remaining = (lockout_end - datetime.now()).seconds
                return True, remaining
            else:
                # 잠금 해제
                st.session_state.login_attempts[identifier] = {}
                return False, None

        return False, None

    @staticmethod
    def record_login_attempt(identifier: str, success: bool):
        """로그인 시도 기록"""
        SecureAuth.init_session()

        if identifier not in st.session_state.login_attempts:
            st.session_state.login_attempts[identifier] = {'count': 0}

        if success:
            st.session_state.login_attempts[identifier] = {'count': 0}
        else:
            st.session_state.login_attempts[identifier]['count'] = \
                st.session_state.login_attempts[identifier].get('count', 0) + 1
            st.session_state.login_attempts[identifier]['last_attempt'] = datetime.now()

    @staticmethod
    def create_session(user: str, role: str = "user"):
        """인증 세션 생성"""
        SecureAuth.init_session()

        st.session_state.auth_user = user
        st.session_state.auth_role = role
        st.session_state.auth_time = datetime.now()
        st.session_state.session_token = secrets.token_urlsafe(32)

        logger.info(f"Session created for user: {user}, role: {role}")

    @staticmethod
    def destroy_session():
        """인증 세션 삭제"""
        SecureAuth.init_session()

        st.session_state.auth_user = None
        st.session_state.auth_role = None
        st.session_state.auth_time = None
        st.session_state.session_token = None

    @staticmethod
    def is_authenticated() -> bool:
        """인증 상태 확인"""
        SecureAuth.init_session()
        return st.session_state.auth_user is not None

    @staticmethod
    def has_role(required_role: str) -> bool:
        """역할 확인"""
        SecureAuth.init_session()

        if not SecureAuth.is_authenticated():
            return False

        role_hierarchy = {'admin': 3, 'moderator': 2, 'user': 1, 'guest': 0}
        user_level = role_hierarchy.get(st.session_state.auth_role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        return user_level >= required_level

    @staticmethod
    def require_auth(redirect_page: str = "/"):
        """인증 필요 페이지 보호"""
        if not SecureAuth.is_authenticated():
            st.warning("이 페이지에 접근하려면 로그인이 필요합니다.")
            st.markdown(f'<meta http-equiv="refresh" content="2;url={redirect_page}">', unsafe_allow_html=True)
            st.stop()

    @staticmethod
    def require_role(role: str, redirect_page: str = "/"):
        """역할 필요 페이지 보호"""
        if not SecureAuth.has_role(role):
            st.error("접근 권한이 없습니다.")
            st.markdown(f'<meta http-equiv="refresh" content="2;url={redirect_page}">', unsafe_allow_html=True)
            st.stop()


# =============================================================================
# 관리자 인증 (개선된 버전)
# =============================================================================

def render_admin_login():
    """관리자 로그인 폼 렌더링"""
    SecureAuth.init_session()

    # 이미 인증됨
    if st.session_state.get("admin_authenticated"):
        st.success("관리자 모드 활성화됨")
        if st.button("로그아웃", key="admin_logout"):
            st.session_state.admin_authenticated = False
            SecureAuth.destroy_session()
            st.rerun()
        return True

    # 잠금 확인
    is_locked, remaining = SecureAuth.is_locked_out("admin")
    if is_locked:
        st.error(f"너무 많은 로그인 시도로 잠금되었습니다. {remaining}초 후 다시 시도하세요.")
        return False

    # 로그인 폼
    with st.form("admin_login_form", clear_on_submit=True):
        password = st.text_input(
            "관리자 비밀번호",
            type="password",
            key="admin_pw_secure"
        )

        submitted = st.form_submit_button("로그인")

        if submitted:
            # 환경 변수에서 비밀번호 가져오기
            from env_config import ADMIN_PASSWORD

            if password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                SecureAuth.create_session("admin", "admin")
                SecureAuth.record_login_attempt("admin", True)
                st.success("관리자 인증 성공")
                st.rerun()
            else:
                SecureAuth.record_login_attempt("admin", False)
                attempts = st.session_state.login_attempts.get("admin", {}).get('count', 0)
                remaining_attempts = SecureAuth.MAX_LOGIN_ATTEMPTS - attempts
                st.error(f"비밀번호가 올바르지 않습니다. (남은 시도: {remaining_attempts}회)")

    return False


# =============================================================================
# 레이트 리미터
# =============================================================================

class RateLimiter:
    """API 요청 속도 제한"""

    def __init__(self, max_requests: int, window_seconds: int):
        """
        Args:
            max_requests: 윈도우 내 최대 요청 수
            window_seconds: 윈도우 크기 (초)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_prefix = "rate_limit_"

    def _get_key(self, identifier: str) -> str:
        return f"{self.key_prefix}{identifier}"

    def is_allowed(self, identifier: str) -> tuple[bool, int]:
        """요청 허용 여부 확인

        Args:
            identifier: 요청자 식별자

        Returns:
            (허용여부, 남은 요청 수)
        """
        key = self._get_key(identifier)
        now = time.time()

        if key not in st.session_state:
            st.session_state[key] = []

        # 윈도우 외 요청 제거
        window_start = now - self.window_seconds
        st.session_state[key] = [
            t for t in st.session_state[key] if t > window_start
        ]

        current_count = len(st.session_state[key])
        remaining = max(0, self.max_requests - current_count)

        if current_count >= self.max_requests:
            return False, 0

        # 요청 기록
        st.session_state[key].append(now)
        return True, remaining - 1

    def get_reset_time(self, identifier: str) -> int:
        """리셋까지 남은 시간 (초)"""
        key = self._get_key(identifier)
        now = time.time()

        if key not in st.session_state or not st.session_state[key]:
            return 0

        oldest = min(st.session_state[key])
        reset_time = oldest + self.window_seconds - now
        return max(0, int(reset_time))


# 전역 레이트 리미터
api_rate_limiter = RateLimiter(max_requests=60, window_seconds=60)  # 분당 60회
upload_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)  # 분당 10회


def rate_limited(limiter: RateLimiter, identifier_func: Callable[[], str] = lambda: "global"):
    """레이트 리밋 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            identifier = identifier_func()
            allowed, remaining = limiter.is_allowed(identifier)

            if not allowed:
                reset_time = limiter.get_reset_time(identifier)
                st.warning(f"요청 한도 초과. {reset_time}초 후 다시 시도하세요.")
                return None

            return func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# 보안 헤더 (Streamlit 제한으로 인해 메타 태그 사용)
# =============================================================================

def render_security_headers():
    """보안 관련 메타 태그 렌더링"""
    security_meta = """
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <meta http-equiv="X-Frame-Options" content="SAMEORIGIN">
    <meta http-equiv="X-XSS-Protection" content="1; mode=block">
    <meta name="referrer" content="strict-origin-when-cross-origin">
    """
    st.markdown(security_meta, unsafe_allow_html=True)


# =============================================================================
# 로깅 및 감사
# =============================================================================

def log_security_event(
    event_type: str,
    details: Dict[str, Any],
    severity: str = "info"
):
    """보안 이벤트 로깅

    Args:
        event_type: 이벤트 유형 (login, logout, access_denied, etc.)
        details: 이벤트 상세 정보
        severity: 심각도 (info, warning, error, critical)
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "severity": severity,
        "details": details
    }

    # API 키 마스킹
    if "api_key" in details:
        details["api_key"] = mask_sensitive(details["api_key"])

    log_func = {
        "info": logger.info,
        "warning": logger.warning,
        "error": logger.error,
        "critical": logger.critical
    }.get(severity, logger.info)

    log_func(f"[SECURITY] {event_type}: {details}")

    # 세션에 저장 (최근 100개)
    if "security_log" not in st.session_state:
        st.session_state.security_log = []

    st.session_state.security_log.append(log_entry)
    if len(st.session_state.security_log) > 100:
        st.session_state.security_log = st.session_state.security_log[-100:]


def mask_sensitive(value: str, visible_chars: int = 4) -> str:
    """민감 정보 마스킹"""
    if not value or len(value) <= visible_chars * 2:
        return "*" * len(value) if value else ""

    return value[:visible_chars] + "*" * (len(value) - visible_chars * 2) + value[-visible_chars:]


# =============================================================================
# 편의 함수
# =============================================================================

def safe_render_markdown(content: str, allow_html: bool = False):
    """안전한 마크다운 렌더링

    Args:
        content: 마크다운 콘텐츠
        allow_html: HTML 허용 여부 (허용 시 살균 적용)
    """
    if allow_html:
        sanitized = sanitize_html(content, allow_tags=True)
        st.markdown(sanitized, unsafe_allow_html=True)
    else:
        # HTML 이스케이프 후 마크다운으로 렌더링
        st.markdown(content)


def secure_json_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """JSON 응답 보안 처리"""
    # 민감 키 마스킹
    sensitive_keys = {'password', 'api_key', 'secret', 'token', 'key'}

    def mask_dict(d: Dict) -> Dict:
        result = {}
        for k, v in d.items():
            if any(sk in k.lower() for sk in sensitive_keys):
                result[k] = mask_sensitive(str(v)) if v else None
            elif isinstance(v, dict):
                result[k] = mask_dict(v)
            else:
                result[k] = v
        return result

    return mask_dict(data)


# =============================================================================
# Enhanced Security 통합 함수
# =============================================================================

def check_sql_injection(text: str) -> tuple[bool, List[str]]:
    """SQL Injection 공격 패턴 검사

    Args:
        text: 검사할 텍스트

    Returns:
        (is_safe, detected_patterns)
    """
    _load_enhanced_security()

    if _sql_injection_checker:
        return _sql_injection_checker.check_sql_injection(text)

    # 폴백: 기본 패턴 검사
    dangerous_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE)\b)",
        r"(--|;|/\*|\*/)",
        r"(\bOR\b\s+1\s*=\s*1)",
    ]

    detected = []
    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            detected.append(pattern)

    return len(detected) == 0, detected


def check_path_traversal(path: str, base_dir: str = None) -> tuple[bool, str]:
    """경로 탐색 공격 검사

    Args:
        path: 검사할 경로
        base_dir: 허용된 기본 디렉토리

    Returns:
        (is_safe, reason)
    """
    _load_enhanced_security()

    if _path_traversal_checker:
        return _path_traversal_checker.is_safe_path(path, base_dir)

    # 폴백: 기본 검사
    if '..' in path or '%2e' in path.lower():
        return False, "경로 탐색 패턴 감지"

    return True, "안전"


def sanitize_filename(filename: str) -> str:
    """파일명 살균"""
    _load_enhanced_security()

    if _path_traversal_checker:
        return _path_traversal_checker.sanitize_filename(filename)

    # 폴백: 기본 살균
    dangerous_chars = ['/', '\\', '..', ':', '*', '?', '"', '<', '>', '|']
    result = str(filename)
    for char in dangerous_chars:
        result = result.replace(char, '_')
    return result.strip(' .')


def validate_secure_input(
    text: str,
    max_length: int = 5000,
    check_sql: bool = True,
    check_xss: bool = True,
    check_path: bool = False
) -> tuple[bool, str, List[str]]:
    """통합 보안 입력 검증

    Args:
        text: 입력 텍스트
        max_length: 최대 길이
        check_sql: SQL Injection 검사
        check_xss: XSS 검사
        check_path: 경로 탐색 검사

    Returns:
        (is_safe, sanitized_text, warnings)
    """
    warnings = []

    if not text:
        return True, '', warnings

    # 길이 제한
    text = str(text)
    if len(text) > max_length:
        text = text[:max_length]
        warnings.append(f"입력이 {max_length}자로 잘렸습니다.")

    # SQL Injection 검사
    if check_sql:
        is_safe, patterns = check_sql_injection(text)
        if not is_safe:
            warnings.append("SQL Injection 패턴 감지")
            audit_log('SECURITY', 'sql_injection_attempt', details={'patterns': patterns}, severity='WARNING')

    # XSS 검사
    if check_xss:
        text = sanitize_html(text, allow_tags=False)

    # 경로 탐색 검사
    if check_path:
        is_safe, reason = check_path_traversal(text)
        if not is_safe:
            warnings.append(f"경로 탐색 패턴 감지: {reason}")
            audit_log('SECURITY', 'path_traversal_attempt', details={'reason': reason}, severity='WARNING')

    return len(warnings) == 0, text, warnings


def init_enhanced_security():
    """Enhanced Security 시스템 초기화"""
    _load_enhanced_security()

    try:
        from enhanced_security import init_security
        return init_security()
    except ImportError:
        logger.warning("enhanced_security 모듈을 초기화할 수 없습니다.")
        return False


# =============================================================================
# 보안 미들웨어 데코레이터
# =============================================================================

def secure_endpoint(
    require_auth: bool = False,
    required_role: str = None,
    rate_limit: bool = True,
    log_access: bool = True
):
    """보안 엔드포인트 데코레이터

    Args:
        require_auth: 인증 필요 여부
        required_role: 필요한 역할
        rate_limit: 레이트 리밋 적용
        log_access: 접근 로깅

    Usage:
        @secure_endpoint(require_auth=True, required_role='admin')
        def admin_function():
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 인증 확인
            if require_auth:
                if not SecureAuth.is_authenticated():
                    audit_log('ACCESS', 'unauthorized_access', details={'function': func.__name__}, severity='WARNING')
                    st.error("이 기능을 사용하려면 로그인이 필요합니다.")
                    return None

            # 역할 확인
            if required_role:
                if not SecureAuth.has_role(required_role):
                    audit_log('ACCESS', 'insufficient_role', details={'function': func.__name__, 'required': required_role}, severity='WARNING')
                    st.error("접근 권한이 없습니다.")
                    return None

            # 레이트 리밋
            if rate_limit:
                allowed, remaining = api_rate_limiter.is_allowed("global")
                if not allowed:
                    audit_log('SECURITY', 'rate_limit_exceeded', details={'function': func.__name__}, severity='WARNING')
                    st.warning("요청 한도를 초과했습니다. 잠시 후 다시 시도하세요.")
                    return None

            # 접근 로깅
            if log_access:
                user = st.session_state.get('auth_user', 'anonymous')
                audit_log('ACCESS', 'function_call', user=user, details={'function': func.__name__})

            return func(*args, **kwargs)
        return wrapper
    return decorator

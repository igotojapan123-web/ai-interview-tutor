# csrf_protection.py
# CSRF 토큰 보호 시스템

import secrets
import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import threading

try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# ============================================================
# 설정
# ============================================================

TOKEN_LENGTH = 32  # 토큰 길이 (바이트)
TOKEN_EXPIRY_MINUTES = 60  # 토큰 유효 시간 (분)
MAX_TOKENS_PER_SESSION = 10  # 세션당 최대 토큰 수


# ============================================================
# CSRF 토큰 관리 클래스
# ============================================================

class CSRFProtection:
    """CSRF 토큰 생성 및 검증"""

    def __init__(self, expiry_minutes: int = TOKEN_EXPIRY_MINUTES):
        self.expiry_minutes = expiry_minutes
        self._tokens: Dict[str, Dict[str, Any]] = {}  # {session_id: {token: expiry_time}}
        self._lock = threading.Lock()

    def generate_token(self, session_id: str) -> str:
        """
        새 CSRF 토큰 생성

        Args:
            session_id: 세션 ID

        Returns:
            생성된 토큰
        """
        with self._lock:
            # 토큰 생성
            token = secrets.token_urlsafe(TOKEN_LENGTH)
            expiry = datetime.now() + timedelta(minutes=self.expiry_minutes)

            # 세션별 토큰 저장
            if session_id not in self._tokens:
                self._tokens[session_id] = {}

            # 오래된 토큰 정리
            self._cleanup_session_tokens(session_id)

            # 최대 토큰 수 제한
            if len(self._tokens[session_id]) >= MAX_TOKENS_PER_SESSION:
                # 가장 오래된 토큰 제거
                oldest = min(self._tokens[session_id].items(), key=lambda x: x[1])
                del self._tokens[session_id][oldest[0]]

            self._tokens[session_id][token] = expiry

            logger.debug(f"CSRF token generated: session={session_id[:8]}...")
            return token

    def validate_token(self, session_id: str, token: str, consume: bool = True) -> Tuple[bool, str]:
        """
        CSRF 토큰 검증

        Args:
            session_id: 세션 ID
            token: 검증할 토큰
            consume: 검증 후 토큰 소비 여부

        Returns:
            (valid: bool, message: str)
        """
        with self._lock:
            if not token:
                return False, "CSRF 토큰이 없습니다."

            if session_id not in self._tokens:
                return False, "유효하지 않은 세션입니다."

            if token not in self._tokens[session_id]:
                logger.warning(f"Invalid CSRF token: session={session_id[:8]}...")
                return False, "유효하지 않은 토큰입니다."

            expiry = self._tokens[session_id][token]
            if datetime.now() > expiry:
                del self._tokens[session_id][token]
                return False, "토큰이 만료되었습니다. 페이지를 새로고침 해주세요."

            # 토큰 소비 (일회용)
            if consume:
                del self._tokens[session_id][token]

            return True, "OK"

    def _cleanup_session_tokens(self, session_id: str) -> None:
        """만료된 토큰 정리"""
        if session_id not in self._tokens:
            return

        now = datetime.now()
        expired = [t for t, exp in self._tokens[session_id].items() if now > exp]
        for token in expired:
            del self._tokens[session_id][token]

    def cleanup_all(self) -> int:
        """모든 만료된 토큰 정리"""
        with self._lock:
            cleaned = 0
            now = datetime.now()

            for session_id in list(self._tokens.keys()):
                expired = [t for t, exp in self._tokens[session_id].items() if now > exp]
                for token in expired:
                    del self._tokens[session_id][token]
                    cleaned += 1

                # 빈 세션 제거
                if not self._tokens[session_id]:
                    del self._tokens[session_id]

            return cleaned

    def get_session_token_count(self, session_id: str) -> int:
        """세션의 활성 토큰 수"""
        with self._lock:
            if session_id not in self._tokens:
                return 0
            self._cleanup_session_tokens(session_id)
            return len(self._tokens[session_id])


# 전역 CSRF 인스턴스
csrf = CSRFProtection()


# ============================================================
# Streamlit 통합
# ============================================================

def get_csrf_token() -> str:
    """
    현재 세션의 CSRF 토큰 가져오기/생성

    Usage in Streamlit:
        token = get_csrf_token()
        st.hidden("csrf_token", token)
    """
    import streamlit as st

    # 세션 ID 가져오기
    if 'session_id' not in st.session_state:
        st.session_state.session_id = secrets.token_urlsafe(16)

    session_id = st.session_state.session_id

    # 토큰 생성
    token = csrf.generate_token(session_id)

    # 세션에도 저장 (폼에서 사용)
    st.session_state.csrf_token = token

    return token


def validate_csrf_token(token: str = None) -> Tuple[bool, str]:
    """
    CSRF 토큰 검증

    Args:
        token: 검증할 토큰 (없으면 세션에서 가져옴)

    Returns:
        (valid: bool, message: str)
    """
    import streamlit as st

    if 'session_id' not in st.session_state:
        return False, "세션이 유효하지 않습니다."

    session_id = st.session_state.session_id

    # 토큰이 없으면 세션에서 가져옴
    if token is None:
        token = st.session_state.get('submitted_csrf_token')

    return csrf.validate_token(session_id, token)


def csrf_protect(func):
    """
    CSRF 보호 데코레이터 (Streamlit 콜백용)

    Usage:
        @csrf_protect
        def on_submit():
            ...
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        import streamlit as st

        token = st.session_state.get('csrf_token')
        valid, message = validate_csrf_token(token)

        if not valid:
            st.error(f"🚫 보안 오류: {message}")
            logger.warning(f"CSRF validation failed: {message}")
            return None

        return func(*args, **kwargs)

    return wrapper


# ============================================================
# HTML 폼용 헬퍼
# ============================================================

def get_csrf_hidden_input() -> str:
    """CSRF 토큰 hidden input HTML"""
    token = get_csrf_token()
    return f'<input type="hidden" name="csrf_token" value="{token}">'


def get_csrf_meta_tag() -> str:
    """CSRF 토큰 meta 태그 (AJAX용)"""
    token = get_csrf_token()
    return f'<meta name="csrf-token" content="{token}">'


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=== CSRF Protection ===")

    # 테스트
    session_id = "test_session_123"

    # 토큰 생성
    token1 = csrf.generate_token(session_id)
    print(f"Generated token: {token1[:20]}...")

    # 유효성 검증
    valid, msg = csrf.validate_token(session_id, token1)
    print(f"Validation 1: {valid} - {msg}")

    # 소비된 토큰 재사용 시도
    valid, msg = csrf.validate_token(session_id, token1)
    print(f"Validation 2 (reuse): {valid} - {msg}")

    # 잘못된 토큰
    valid, msg = csrf.validate_token(session_id, "invalid_token")
    print(f"Validation 3 (invalid): {valid} - {msg}")

    print("\nReady!")

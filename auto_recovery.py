# auto_recovery.py
# FlyReady Lab - 자동 에러 복구 시스템
# API 호출 안정화, 자동 재시도, 우아한 실패 처리

import os
import time
import random
import functools
from typing import Callable, Any, Optional, Dict, TypeVar, Union
from datetime import datetime
import threading

# 로깅
try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# ============================================================
# 설정
# ============================================================

# 재시도 설정
DEFAULT_MAX_RETRIES = 5          # 최대 재시도 횟수
DEFAULT_BASE_DELAY = 1.0         # 기본 대기 시간 (초)
DEFAULT_MAX_DELAY = 30.0         # 최대 대기 시간 (초)
DEFAULT_TIMEOUT = 120            # 기본 타임아웃 (초) - 넉넉하게

# API별 타임아웃 설정 (넉넉하게)
API_TIMEOUTS = {
    "openai": 180,       # GPT 응답 대기 - 3분
    "did": 300,          # D-ID 영상 생성 - 5분
    "clova": 60,         # Clova STT - 1분
    "google_tts": 60,    # Google TTS - 1분
    "default": 120       # 기본 - 2분
}

# 재시도 가능한 에러 타입
RETRYABLE_ERRORS = (
    ConnectionError,
    TimeoutError,
    OSError,
)

# 재시도 가능한 에러 메시지 패턴
RETRYABLE_MESSAGES = [
    "timeout",
    "timed out",
    "connection",
    "network",
    "temporarily",
    "rate limit",
    "too many requests",
    "503",
    "502",
    "504",
    "overloaded",
    "capacity",
]

# ============================================================
# 에러 분류
# ============================================================

class ErrorCategory:
    """에러 카테고리"""
    TRANSIENT = "transient"      # 일시적 (재시도로 해결 가능)
    RATE_LIMIT = "rate_limit"    # 속도 제한 (대기 후 재시도)
    AUTH = "auth"                # 인증 오류 (재시도 불가)
    INPUT = "input"              # 입력 오류 (재시도 불가)
    SERVER = "server"            # 서버 오류 (재시도 가능)
    UNKNOWN = "unknown"          # 알 수 없음

def categorize_error(error: Exception) -> str:
    """에러 카테고리 분류"""
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()

    # 속도 제한
    if any(msg in error_str for msg in ["rate limit", "too many requests", "429"]):
        return ErrorCategory.RATE_LIMIT

    # 인증 오류
    if any(msg in error_str for msg in ["unauthorized", "403", "401", "invalid key", "api key"]):
        return ErrorCategory.AUTH

    # 입력 오류
    if any(msg in error_str for msg in ["invalid", "bad request", "400", "validation"]):
        return ErrorCategory.INPUT

    # 서버 오류
    if any(msg in error_str for msg in ["500", "502", "503", "504", "server error", "internal"]):
        return ErrorCategory.SERVER

    # 일시적 오류
    if any(msg in error_str for msg in RETRYABLE_MESSAGES):
        return ErrorCategory.TRANSIENT

    if isinstance(error, RETRYABLE_ERRORS):
        return ErrorCategory.TRANSIENT

    return ErrorCategory.UNKNOWN

def is_retryable(error: Exception) -> bool:
    """재시도 가능한 에러인지 확인"""
    category = categorize_error(error)
    return category in [
        ErrorCategory.TRANSIENT,
        ErrorCategory.RATE_LIMIT,
        ErrorCategory.SERVER,
    ]

# ============================================================
# 자동 복구 데코레이터
# ============================================================

T = TypeVar('T')

def auto_retry(
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    timeout: int = DEFAULT_TIMEOUT,
    fallback: Any = None,
    on_error: Callable = None,
    silent: bool = False,
    api_name: str = "default"
) -> Callable:
    """
    자동 재시도 데코레이터

    Args:
        max_retries: 최대 재시도 횟수
        base_delay: 기본 대기 시간
        max_delay: 최대 대기 시간
        timeout: 타임아웃 (초)
        fallback: 모든 재시도 실패시 반환할 기본값
        on_error: 에러 발생시 호출할 콜백
        silent: True면 사용자에게 에러 표시 안함
        api_name: API 이름 (타임아웃 설정용)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # API별 타임아웃 적용
            actual_timeout = API_TIMEOUTS.get(api_name, timeout)

            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    # timeout 파라미터는 함수가 받을 수 있는 경우에만 전달
                    # (일반 함수에는 전달하지 않음)

                    result = func(*args, **kwargs)

                    # 성공시 재시도 카운트 초기화
                    if attempt > 0:
                        logger.info(f"[AutoRecovery] {func.__name__} 성공 (재시도 {attempt}회)")

                    return result

                except Exception as e:
                    last_error = e
                    category = categorize_error(e)

                    # 로깅
                    logger.warning(
                        f"[AutoRecovery] {func.__name__} 에러 "
                        f"(시도 {attempt + 1}/{max_retries + 1}): "
                        f"[{category}] {type(e).__name__}: {str(e)[:100]}"
                    )

                    # 재시도 불가능한 에러
                    if not is_retryable(e):
                        logger.error(f"[AutoRecovery] 재시도 불가능한 에러: {category}")
                        break

                    # 마지막 시도였으면 종료
                    if attempt >= max_retries:
                        break

                    # 대기 시간 계산 (지수 백오프 + 지터)
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.1)
                    wait_time = delay + jitter

                    # Rate limit인 경우 더 오래 대기
                    if category == ErrorCategory.RATE_LIMIT:
                        wait_time = min(wait_time * 2, max_delay)

                    logger.info(f"[AutoRecovery] {wait_time:.1f}초 후 재시도...")
                    time.sleep(wait_time)

            # 모든 재시도 실패
            if on_error:
                try:
                    on_error(last_error, func.__name__)
                except:
                    pass

            # 관리자에게 알림 (백그라운드)
            _notify_admin_async(last_error, func.__name__, max_retries)

            # fallback 값 반환 또는 에러 발생
            if fallback is not None:
                logger.info(f"[AutoRecovery] fallback 값 반환: {func.__name__}")
                return fallback

            # 사용자 친화적 에러 메시지
            if not silent:
                raise UserFriendlyError(
                    "일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
                    original_error=last_error
                )

            raise last_error

        return wrapper
    return decorator

# ============================================================
# 사용자 친화적 에러
# ============================================================

class UserFriendlyError(Exception):
    """사용자에게 보여줄 친절한 에러"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(message)

    def __str__(self):
        return self.message

# 에러 타입별 사용자 메시지
USER_MESSAGES = {
    ErrorCategory.TRANSIENT: "잠시 연결이 불안정합니다. 다시 시도해주세요.",
    ErrorCategory.RATE_LIMIT: "요청이 많아 잠시 대기 중입니다. 곧 처리됩니다.",
    ErrorCategory.AUTH: "인증에 문제가 있습니다. 관리자에게 문의해주세요.",
    ErrorCategory.INPUT: "입력 내용을 확인해주세요.",
    ErrorCategory.SERVER: "서버 점검 중입니다. 잠시 후 다시 시도해주세요.",
    ErrorCategory.UNKNOWN: "일시적인 문제가 발생했습니다. 다시 시도해주세요.",
}

def get_user_message(error: Exception) -> str:
    """사용자 친화적 메시지 반환"""
    category = categorize_error(error)
    return USER_MESSAGES.get(category, USER_MESSAGES[ErrorCategory.UNKNOWN])

# ============================================================
# 관리자 알림 (백그라운드)
# ============================================================

def _notify_admin_async(error: Exception, func_name: str, retries: int):
    """백그라운드로 관리자에게 알림"""
    def notify():
        try:
            from error_monitor import ErrorLogger, ErrorLevel

            # 에러 로깅 (ERROR 레벨로 → 이메일 알림 자동 트리거)
            error_logger = ErrorLogger()
            error_id = error_logger.log_error(
                error=error,
                level=ErrorLevel.ERROR,
                page=f"[자동복구실패] {func_name}",
                context={"retries": retries, "auto_recovery": True, "all_retries_failed": True}
            )
            # error_monitor가 자동으로 이메일 발송함
        except Exception as e:
            logger.error(f"알림 전송 실패: {e}")

    thread = threading.Thread(target=notify, daemon=True)
    thread.start()

# ============================================================
# API 래퍼 클래스
# ============================================================

class SafeAPIClient:
    """안전한 API 클라이언트 래퍼"""

    def __init__(self, api_name: str = "default"):
        self.api_name = api_name
        self.timeout = API_TIMEOUTS.get(api_name, DEFAULT_TIMEOUT)

    def call(
        self,
        func: Callable,
        *args,
        fallback: Any = None,
        **kwargs
    ) -> Any:
        """안전한 API 호출"""

        @auto_retry(
            max_retries=DEFAULT_MAX_RETRIES,
            timeout=self.timeout,
            fallback=fallback,
            api_name=self.api_name
        )
        def wrapped_call():
            return func(*args, **kwargs)

        return wrapped_call()

# ============================================================
# OpenAI 전용 래퍼
# ============================================================

class SafeOpenAI:
    """OpenAI API 안전 래퍼"""

    def __init__(self):
        self.timeout = API_TIMEOUTS["openai"]

    @auto_retry(max_retries=5, api_name="openai")
    def chat_completion(self, **kwargs) -> dict:
        """ChatCompletion API 호출"""
        from openai import OpenAI
        client = OpenAI(timeout=self.timeout)

        # 타임아웃 설정
        kwargs.pop('timeout', None)  # 중복 제거

        response = client.chat.completions.create(**kwargs)
        return response

    @auto_retry(max_retries=5, api_name="openai", fallback="")
    def simple_chat(self, prompt: str, system: str = "", model: str = "gpt-4o-mini") -> str:
        """간단한 채팅 (텍스트만 반환)"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.chat_completion(
            model=model,
            messages=messages,
            temperature=0.7
        )

        return response.choices[0].message.content

# ============================================================
# D-ID 전용 래퍼
# ============================================================

class SafeDID:
    """D-ID API 안전 래퍼"""

    def __init__(self):
        self.timeout = API_TIMEOUTS["did"]
        self.api_key = os.getenv("DID_API_KEY", "")

    @auto_retry(max_retries=3, api_name="did")
    def create_talk(self, **kwargs) -> dict:
        """Talk 영상 생성"""
        import requests

        headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://api.d-id.com/talks",
            headers=headers,
            json=kwargs,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    @auto_retry(max_retries=10, api_name="did")  # 폴링은 더 많이 재시도
    def get_talk(self, talk_id: str) -> dict:
        """Talk 상태 조회"""
        import requests

        headers = {
            "Authorization": f"Basic {self.api_key}"
        }

        response = requests.get(
            f"https://api.d-id.com/talks/{talk_id}",
            headers=headers,
            timeout=60
        )
        response.raise_for_status()
        return response.json()

# ============================================================
# 편의 함수
# ============================================================

def safe_api_call(
    func: Callable,
    *args,
    fallback: Any = None,
    api_name: str = "default",
    **kwargs
) -> Any:
    """
    안전한 API 호출 간편 함수

    사용예:
        result = safe_api_call(some_api_function, arg1, arg2, fallback="기본값")
    """
    client = SafeAPIClient(api_name)
    return client.call(func, *args, fallback=fallback, **kwargs)


def with_recovery(fallback: Any = None, api_name: str = "default"):
    """
    자동 복구 데코레이터 간편 버전

    사용예:
        @with_recovery(fallback="기본값")
        def my_api_function():
            ...
    """
    return auto_retry(
        max_retries=DEFAULT_MAX_RETRIES,
        fallback=fallback,
        api_name=api_name
    )

# ============================================================
# Streamlit 통합
# ============================================================

def safe_streamlit_action(func: Callable, error_message: str = None) -> Any:
    """
    Streamlit 액션을 안전하게 실행
    에러 발생시 st.error 대신 친절한 메시지 표시
    """
    import streamlit as st

    try:
        return func()
    except UserFriendlyError as e:
        st.warning(e.message)
        return None
    except Exception as e:
        message = error_message or get_user_message(e)
        st.warning(message)

        # 백그라운드 알림
        _notify_admin_async(e, func.__name__ if hasattr(func, '__name__') else "unknown", 0)
        return None


# ============================================================
# 초기화 확인
# ============================================================

if __name__ == "__main__":
    print("=== Auto Recovery System ===")
    print(f"Max Retries: {DEFAULT_MAX_RETRIES}")
    print(f"Default Timeout: {DEFAULT_TIMEOUT}s")
    print(f"API Timeouts: {API_TIMEOUTS}")
    print("Ready!")

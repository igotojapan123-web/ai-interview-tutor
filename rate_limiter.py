# rate_limiter.py
# API Rate Limiting - 사용자별 API 호출 제한 (DDoS 방지)

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from collections import defaultdict
from functools import wraps

try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# ============================================================
# 설정
# ============================================================

# 기본 Rate Limit 설정
DEFAULT_LIMITS = {
    "openai": {"requests": 60, "window_seconds": 60},      # 60 req/min
    "whisper": {"requests": 30, "window_seconds": 60},     # 30 req/min
    "tts": {"requests": 30, "window_seconds": 60},         # 30 req/min
    "did": {"requests": 10, "window_seconds": 60},         # 10 req/min
    "general": {"requests": 100, "window_seconds": 60},    # 100 req/min
}

# 전역 제한 (모든 사용자 합계)
GLOBAL_LIMITS = {
    "openai": {"requests": 500, "window_seconds": 60},
    "whisper": {"requests": 200, "window_seconds": 60},
}


# ============================================================
# Rate Limiter 클래스
# ============================================================

class RateLimiter:
    """슬라이딩 윈도우 기반 Rate Limiter"""

    def __init__(self):
        self._user_requests: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
        self._global_requests: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()
        self._blocked_users: Dict[str, datetime] = {}

    def _clean_old_requests(self, requests: list, window_seconds: int) -> list:
        """오래된 요청 기록 제거"""
        cutoff = time.time() - window_seconds
        return [t for t in requests if t > cutoff]

    def check_rate_limit(
        self,
        user_id: str,
        api_type: str = "general",
        custom_limit: Dict[str, int] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Rate Limit 체크

        Args:
            user_id: 사용자 ID
            api_type: API 유형 (openai, whisper, tts, did, general)
            custom_limit: 커스텀 제한 {"requests": N, "window_seconds": S}

        Returns:
            (allowed: bool, info: dict)
        """
        with self._lock:
            # 차단된 사용자 확인
            if user_id in self._blocked_users:
                if datetime.now() < self._blocked_users[user_id]:
                    remaining = (self._blocked_users[user_id] - datetime.now()).seconds
                    return False, {
                        "error": "rate_limit_exceeded",
                        "message": f"너무 많은 요청입니다. {remaining}초 후 다시 시도하세요.",
                        "retry_after": remaining
                    }
                else:
                    del self._blocked_users[user_id]

            # 제한 설정 가져오기
            limit = custom_limit or DEFAULT_LIMITS.get(api_type, DEFAULT_LIMITS["general"])
            max_requests = limit["requests"]
            window = limit["window_seconds"]

            # 사용자별 요청 기록 정리
            user_requests = self._user_requests[user_id][api_type]
            user_requests = self._clean_old_requests(user_requests, window)
            self._user_requests[user_id][api_type] = user_requests

            # 전역 요청 기록 정리
            if api_type in GLOBAL_LIMITS:
                global_requests = self._global_requests[api_type]
                global_requests = self._clean_old_requests(global_requests, GLOBAL_LIMITS[api_type]["window_seconds"])
                self._global_requests[api_type] = global_requests

                # 전역 제한 체크
                if len(global_requests) >= GLOBAL_LIMITS[api_type]["requests"]:
                    return False, {
                        "error": "global_rate_limit",
                        "message": "서비스가 일시적으로 혼잡합니다. 잠시 후 다시 시도하세요.",
                        "retry_after": 10
                    }

            # 사용자 제한 체크
            current_count = len(user_requests)
            if current_count >= max_requests:
                # 차단 시간 설정 (반복 위반시 증가)
                block_duration = min(60 * (current_count // max_requests), 300)  # 최대 5분
                self._blocked_users[user_id] = datetime.now() + timedelta(seconds=block_duration)

                logger.warning(f"Rate limit exceeded: user={user_id}, api={api_type}, count={current_count}")

                return False, {
                    "error": "rate_limit_exceeded",
                    "message": f"요청 한도 초과 ({max_requests}회/{window}초). {block_duration}초 후 다시 시도하세요.",
                    "retry_after": block_duration,
                    "current": current_count,
                    "limit": max_requests
                }

            return True, {
                "allowed": True,
                "current": current_count,
                "limit": max_requests,
                "remaining": max_requests - current_count - 1
            }

    def record_request(self, user_id: str, api_type: str = "general") -> None:
        """요청 기록"""
        with self._lock:
            self._user_requests[user_id][api_type].append(time.time())

            if api_type in GLOBAL_LIMITS:
                self._global_requests[api_type].append(time.time())

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """사용자별 요청 통계"""
        with self._lock:
            stats = {}
            for api_type, requests in self._user_requests[user_id].items():
                limit = DEFAULT_LIMITS.get(api_type, DEFAULT_LIMITS["general"])
                cleaned = self._clean_old_requests(requests, limit["window_seconds"])
                stats[api_type] = {
                    "current": len(cleaned),
                    "limit": limit["requests"],
                    "remaining": max(0, limit["requests"] - len(cleaned))
                }
            return stats

    def reset_user(self, user_id: str) -> None:
        """사용자 제한 리셋"""
        with self._lock:
            if user_id in self._user_requests:
                del self._user_requests[user_id]
            if user_id in self._blocked_users:
                del self._blocked_users[user_id]
            logger.info(f"Rate limit reset: user={user_id}")


# 전역 Rate Limiter 인스턴스
rate_limiter = RateLimiter()


# ============================================================
# 데코레이터
# ============================================================

def rate_limit(api_type: str = "general", get_user_id=None):
    """
    Rate Limit 데코레이터

    Args:
        api_type: API 유형
        get_user_id: 사용자 ID를 가져오는 함수 (기본: 첫 번째 인자)

    Usage:
        @rate_limit("openai")
        def call_openai(user_id, prompt):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 사용자 ID 추출
            if get_user_id:
                user_id = get_user_id(*args, **kwargs)
            elif args:
                user_id = str(args[0])
            else:
                user_id = kwargs.get('user_id', 'anonymous')

            # Rate Limit 체크
            allowed, info = rate_limiter.check_rate_limit(user_id, api_type)

            if not allowed:
                logger.warning(f"Rate limited: {func.__name__}, user={user_id}")
                raise RateLimitExceeded(info.get("message", "Rate limit exceeded"), info)

            # 요청 기록
            rate_limiter.record_request(user_id, api_type)

            return func(*args, **kwargs)

        return wrapper
    return decorator


class RateLimitExceeded(Exception):
    """Rate Limit 초과 예외"""
    def __init__(self, message: str, info: Dict[str, Any] = None):
        super().__init__(message)
        self.info = info or {}
        self.retry_after = info.get("retry_after", 60) if info else 60


# ============================================================
# Streamlit 통합
# ============================================================

def check_rate_limit_st(api_type: str = "general") -> Tuple[bool, Optional[str]]:
    """
    Streamlit용 Rate Limit 체크

    Returns:
        (allowed: bool, error_message: Optional[str])
    """
    import streamlit as st

    user_id = st.session_state.get('user_id', 'anonymous')
    allowed, info = rate_limiter.check_rate_limit(user_id, api_type)

    if not allowed:
        return False, info.get("message", "요청 한도를 초과했습니다.")

    rate_limiter.record_request(user_id, api_type)
    return True, None


def show_rate_limit_warning():
    """Rate Limit 경고 표시"""
    import streamlit as st

    user_id = st.session_state.get('user_id', 'anonymous')
    stats = rate_limiter.get_user_stats(user_id)

    for api_type, info in stats.items():
        if info["remaining"] <= 5:
            st.warning(f"⚠️ {api_type} API 요청 한도가 거의 다 되었습니다. ({info['current']}/{info['limit']})")


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=== Rate Limiter ===")

    # 테스트
    test_user = "test_user_123"

    for i in range(65):
        allowed, info = rate_limiter.check_rate_limit(test_user, "openai")
        if allowed:
            rate_limiter.record_request(test_user, "openai")
            print(f"Request {i+1}: OK (remaining: {info.get('remaining', 'N/A')})")
        else:
            print(f"Request {i+1}: BLOCKED - {info.get('message')}")
            break

    print("\nUser stats:", rate_limiter.get_user_stats(test_user))

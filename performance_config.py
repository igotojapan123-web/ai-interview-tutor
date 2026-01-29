# performance_config.py
# 성능 최적화 설정 및 유틸리티

import streamlit as st
from functools import wraps
import time
from typing import Callable, Any
from logging_config import get_logger

logger = get_logger(__name__)

# ========================================
# 성능 설정
# ========================================

# 캐시 TTL (초)
CACHE_TTL = {
    "static_data": 3600,      # 정적 데이터 (1시간)
    "user_data": 60,          # 사용자 데이터 (1분)
    "api_response": 300,      # API 응답 (5분)
    "dashboard": 60,          # 대시보드 (1분)
}

# API 타임아웃 (초)
API_TIMEOUT = {
    "openai_chat": 90,
    "openai_vision": 120,
    "openai_whisper": 60,
    "openai_tts": 30,
    "clova_tts": 30,
    "default": 60,
}

# 동시 요청 제한
CONCURRENT_LIMITS = {
    "llm_calls": 3,           # 동시 LLM 호출 수
    "tts_calls": 5,           # 동시 TTS 호출 수
    "file_uploads": 2,        # 동시 파일 업로드 수
}

# 메모리 제한
MEMORY_LIMITS = {
    "max_session_data_mb": 50,    # 세션당 최대 데이터 (MB)
    "max_upload_mb": 50,          # 최대 업로드 크기 (MB)
    "max_response_cache": 100,    # 최대 캐시 응답 수
}


# ========================================
# 성능 모니터링 데코레이터
# ========================================

def measure_time(func_name: str = None):
    """함수 실행 시간 측정 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start

            name = func_name or func.__name__
            if elapsed > 5:  # 5초 이상 소요시 경고
                logger.warning(f"[SLOW] {name}: {elapsed:.2f}초 소요")
            elif elapsed > 1:  # 1초 이상 소요시 info
                logger.info(f"[PERF] {name}: {elapsed:.2f}초 소요")

            return result
        return wrapper
    return decorator


def cache_result(ttl: int = 300):
    """결과 캐싱 데코레이터 (세션 기반)"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 캐시 키 생성
            cache_key = f"_cache_{func.__name__}_{hash(str(args) + str(kwargs))}"
            cache_time_key = f"{cache_key}_time"

            # 캐시 확인
            if cache_key in st.session_state:
                cached_time = st.session_state.get(cache_time_key, 0)
                if time.time() - cached_time < ttl:
                    return st.session_state[cache_key]

            # 새로 계산
            result = func(*args, **kwargs)
            st.session_state[cache_key] = result
            st.session_state[cache_time_key] = time.time()

            return result
        return wrapper
    return decorator


# ========================================
# 세션 메모리 관리
# ========================================

def cleanup_old_session_data():
    """오래된 세션 데이터 정리"""
    if "_last_cleanup" not in st.session_state:
        st.session_state._last_cleanup = time.time()
        return

    # 5분마다 정리
    if time.time() - st.session_state._last_cleanup < 300:
        return

    keys_to_remove = []
    current_time = time.time()

    for key in list(st.session_state.keys()):
        # 캐시 데이터 중 만료된 것 제거
        if key.startswith("_cache_") and key.endswith("_time"):
            if current_time - st.session_state[key] > CACHE_TTL["api_response"]:
                base_key = key[:-5]  # _time 제거
                keys_to_remove.extend([key, base_key])

    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]

    st.session_state._last_cleanup = current_time

    if keys_to_remove:
        logger.debug(f"세션 정리: {len(keys_to_remove)}개 항목 제거")


def get_session_memory_usage() -> dict:
    """세션 메모리 사용량 추정"""
    import sys

    total_size = 0
    item_count = 0

    for key, value in st.session_state.items():
        try:
            total_size += sys.getsizeof(value)
            item_count += 1
        except Exception:
            pass

    return {
        "total_mb": total_size / (1024 * 1024),
        "item_count": item_count,
    }


# ========================================
# 요청 제한 (Rate Limiting)
# ========================================

class RateLimiter:
    """간단한 요청 제한기"""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key = f"_rate_limit_{id(self)}"

    def is_allowed(self) -> bool:
        """요청 허용 여부 확인"""
        current_time = time.time()

        if self.key not in st.session_state:
            st.session_state[self.key] = []

        # 오래된 요청 제거
        requests = st.session_state[self.key]
        requests = [t for t in requests if current_time - t < self.window_seconds]
        st.session_state[self.key] = requests

        if len(requests) >= self.max_requests:
            return False

        requests.append(current_time)
        st.session_state[self.key] = requests
        return True


# 전역 Rate Limiter 인스턴스
llm_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)  # 분당 10회
tts_rate_limiter = RateLimiter(max_requests=20, window_seconds=60)  # 분당 20회


# ========================================
# 초기화 함수
# ========================================

def init_performance_optimizations():
    """성능 최적화 초기화 (앱 시작 시 호출)"""
    cleanup_old_session_data()

    # 세션 메모리 체크
    memory = get_session_memory_usage()
    if memory["total_mb"] > MEMORY_LIMITS["max_session_data_mb"]:
        logger.warning(f"세션 메모리 과다 사용: {memory['total_mb']:.2f}MB")

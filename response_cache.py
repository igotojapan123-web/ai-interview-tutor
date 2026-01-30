# response_cache.py
# LLM 응답 캐싱 시스템 - API 비용 절감

import hashlib
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Callable
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

BASE_DIR = Path(__file__).parent
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 캐시 설정
DEFAULT_TTL_SECONDS = 3600  # 1시간
MAX_CACHE_SIZE_MB = 100  # 최대 캐시 크기
MAX_CACHE_ENTRIES = 1000  # 최대 캐시 항목 수

# 캐시 가능한 API 유형
CACHEABLE_APIS = {
    "question_generation": {"ttl": 7200},      # 질문 생성: 2시간
    "answer_evaluation": {"ttl": 1800},        # 답변 평가: 30분
    "tts": {"ttl": 86400},                     # TTS: 24시간
    "translation": {"ttl": 86400},             # 번역: 24시간
    "ideal_answer": {"ttl": 3600},             # 모범 답안: 1시간
}


# ============================================================
# 캐시 클래스
# ============================================================

class ResponseCache:
    """LLM 응답 캐시 (메모리 + 파일)"""

    def __init__(self, max_entries: int = MAX_CACHE_ENTRIES):
        self.max_entries = max_entries
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "saved_calls": 0
        }

        # 파일 캐시 로드
        self._load_file_cache()

    def _generate_key(self, api_type: str, params: Dict[str, Any]) -> str:
        """캐시 키 생성"""
        # 파라미터를 정렬하여 일관된 키 생성
        sorted_params = json.dumps(params, sort_keys=True, ensure_ascii=False)
        combined = f"{api_type}:{sorted_params}"
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

    def get(self, api_type: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        캐시에서 응답 가져오기

        Args:
            api_type: API 유형
            params: 요청 파라미터

        Returns:
            캐시된 응답 또는 None
        """
        key = self._generate_key(api_type, params)

        with self._lock:
            if key in self._memory_cache:
                entry = self._memory_cache[key]

                # TTL 확인
                if time.time() < entry["expires_at"]:
                    self._stats["hits"] += 1
                    self._stats["saved_calls"] += 1
                    logger.debug(f"Cache HIT: {api_type} (key={key[:8]}...)")
                    return entry["response"]
                else:
                    # 만료된 항목 제거
                    del self._memory_cache[key]

            self._stats["misses"] += 1
            return None

    def set(
        self,
        api_type: str,
        params: Dict[str, Any],
        response: Any,
        ttl: int = None
    ) -> None:
        """
        응답을 캐시에 저장

        Args:
            api_type: API 유형
            params: 요청 파라미터
            response: 저장할 응답
            ttl: 유효 시간 (초)
        """
        # TTL 결정
        if ttl is None:
            ttl = CACHEABLE_APIS.get(api_type, {}).get("ttl", DEFAULT_TTL_SECONDS)

        key = self._generate_key(api_type, params)

        with self._lock:
            # 최대 항목 수 체크
            if len(self._memory_cache) >= self.max_entries:
                self._evict_oldest()

            self._memory_cache[key] = {
                "api_type": api_type,
                "response": response,
                "created_at": time.time(),
                "expires_at": time.time() + ttl,
                "params_hash": hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:16]
            }

            logger.debug(f"Cache SET: {api_type} (key={key[:8]}..., ttl={ttl}s)")

    def _evict_oldest(self) -> None:
        """가장 오래된 항목 제거 (LRU)"""
        if not self._memory_cache:
            return

        oldest_key = min(
            self._memory_cache.keys(),
            key=lambda k: self._memory_cache[k]["created_at"]
        )
        del self._memory_cache[oldest_key]

    def invalidate(self, api_type: str = None, key: str = None) -> int:
        """
        캐시 무효화

        Args:
            api_type: 특정 API 유형만 무효화
            key: 특정 키만 무효화

        Returns:
            삭제된 항목 수
        """
        with self._lock:
            if key:
                if key in self._memory_cache:
                    del self._memory_cache[key]
                    return 1
                return 0

            if api_type:
                keys_to_delete = [
                    k for k, v in self._memory_cache.items()
                    if v.get("api_type") == api_type
                ]
            else:
                keys_to_delete = list(self._memory_cache.keys())

            for k in keys_to_delete:
                del self._memory_cache[k]

            logger.info(f"Cache invalidated: {len(keys_to_delete)} entries")
            return len(keys_to_delete)

    def cleanup_expired(self) -> int:
        """만료된 항목 정리"""
        with self._lock:
            now = time.time()
            expired = [k for k, v in self._memory_cache.items() if now >= v["expires_at"]]

            for k in expired:
                del self._memory_cache[k]

            if expired:
                logger.info(f"Cache cleanup: {len(expired)} expired entries removed")

            return len(expired)

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0

            return {
                "entries": len(self._memory_cache),
                "max_entries": self.max_entries,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": f"{hit_rate:.1f}%",
                "saved_api_calls": self._stats["saved_calls"],
                "estimated_savings": f"${self._stats['saved_calls'] * 0.002:.2f}"  # ~$0.002/call
            }

    def _load_file_cache(self) -> None:
        """파일 캐시 로드 (시작 시)"""
        cache_file = CACHE_DIR / "response_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 만료되지 않은 항목만 로드
                now = time.time()
                for key, entry in data.items():
                    if entry.get("expires_at", 0) > now:
                        self._memory_cache[key] = entry

                logger.info(f"Loaded {len(self._memory_cache)} cache entries from file")
            except Exception as e:
                logger.error(f"Failed to load cache file: {e}")

    def save_to_file(self) -> None:
        """캐시를 파일에 저장"""
        cache_file = CACHE_DIR / "response_cache.json"
        try:
            with self._lock:
                # 직렬화 가능한 항목만 저장
                serializable = {}
                for key, entry in self._memory_cache.items():
                    try:
                        json.dumps(entry)
                        serializable[key] = entry
                    except:
                        pass

                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(serializable, f, ensure_ascii=False)

            logger.info(f"Saved {len(serializable)} cache entries to file")
        except Exception as e:
            logger.error(f"Failed to save cache file: {e}")


# 전역 캐시 인스턴스
response_cache = ResponseCache()


# ============================================================
# 데코레이터
# ============================================================

def cached(api_type: str, ttl: int = None, key_params: list = None):
    """
    응답 캐싱 데코레이터

    Args:
        api_type: API 유형
        ttl: 캐시 유효 시간 (초)
        key_params: 캐시 키에 포함할 파라미터 이름 리스트

    Usage:
        @cached("question_generation", ttl=3600)
        def generate_questions(airline: str, count: int):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키용 파라미터 추출
            if key_params:
                params = {k: kwargs.get(k) for k in key_params if k in kwargs}
            else:
                params = kwargs.copy()

            # 위치 인자도 추가
            if args:
                params["_args"] = str(args)

            # 캐시 확인
            cached_response = response_cache.get(api_type, params)
            if cached_response is not None:
                return cached_response

            # 실제 함수 호출
            response = func(*args, **kwargs)

            # 캐시 저장 (None이 아닌 경우만)
            if response is not None:
                response_cache.set(api_type, params, response, ttl)

            return response

        return wrapper
    return decorator


# ============================================================
# 간편 함수
# ============================================================

def get_cached_or_call(
    api_type: str,
    params: Dict[str, Any],
    call_func: Callable,
    ttl: int = None
) -> Any:
    """
    캐시된 응답 가져오거나 함수 호출

    Args:
        api_type: API 유형
        params: 파라미터
        call_func: 캐시 미스 시 호출할 함수
        ttl: 캐시 유효 시간

    Returns:
        캐시된 또는 새로운 응답
    """
    # 캐시 확인
    cached = response_cache.get(api_type, params)
    if cached is not None:
        return cached

    # 함수 호출
    response = call_func()

    # 캐시 저장
    if response is not None:
        response_cache.set(api_type, params, response, ttl)

    return response


def clear_cache(api_type: str = None) -> int:
    """캐시 삭제"""
    return response_cache.invalidate(api_type)


def get_cache_stats() -> Dict[str, Any]:
    """캐시 통계 조회"""
    return response_cache.get_stats()


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=== Response Cache ===")

    # 테스트
    @cached("test_api", ttl=60)
    def expensive_api_call(prompt: str):
        print(f"API called with: {prompt}")
        time.sleep(0.5)  # 시뮬레이션
        return f"Response for: {prompt}"

    # 첫 번째 호출 (캐시 미스)
    print("\n1st call:")
    result1 = expensive_api_call(prompt="Hello")
    print(f"Result: {result1}")

    # 두 번째 호출 (캐시 히트)
    print("\n2nd call (should be cached):")
    result2 = expensive_api_call(prompt="Hello")
    print(f"Result: {result2}")

    # 다른 파라미터 (캐시 미스)
    print("\n3rd call (different param):")
    result3 = expensive_api_call(prompt="World")
    print(f"Result: {result3}")

    # 통계
    print("\nCache stats:", get_cache_stats())

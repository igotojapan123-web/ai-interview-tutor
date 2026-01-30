# tests/test_response_cache.py
# Response Cache 테스트

import pytest
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from response_cache import ResponseCache, cached, get_cached_or_call


class TestResponseCache:
    """ResponseCache 클래스 테스트"""

    @pytest.fixture
    def cache(self):
        """새 캐시 인스턴스"""
        return ResponseCache(max_entries=100)

    def test_cache_set_get(self, cache):
        """캐시 저장/조회 테스트"""
        params = {"prompt": "hello"}
        response = {"text": "world"}

        cache.set("test_api", params, response)
        result = cache.get("test_api", params)

        assert result == response

    def test_cache_miss(self, cache):
        """캐시 미스 테스트"""
        result = cache.get("nonexistent", {"key": "value"})
        assert result is None

    def test_cache_ttl_expiry(self, cache):
        """TTL 만료 테스트"""
        params = {"prompt": "test"}
        response = {"text": "response"}

        # 1초 TTL로 저장
        cache.set("test_api", params, response, ttl=1)

        # 즉시 조회 - 히트
        assert cache.get("test_api", params) == response

        # 2초 대기
        time.sleep(2)

        # 만료 후 조회 - 미스
        assert cache.get("test_api", params) is None

    def test_cache_invalidate_all(self, cache):
        """전체 무효화 테스트"""
        cache.set("api1", {"a": 1}, "response1")
        cache.set("api2", {"b": 2}, "response2")

        deleted = cache.invalidate()

        assert deleted == 2
        assert cache.get("api1", {"a": 1}) is None

    def test_cache_invalidate_by_type(self, cache):
        """타입별 무효화 테스트"""
        cache.set("api1", {"a": 1}, "response1")
        cache.set("api2", {"b": 2}, "response2")

        deleted = cache.invalidate(api_type="api1")

        assert deleted == 1
        assert cache.get("api1", {"a": 1}) is None
        assert cache.get("api2", {"b": 2}) == "response2"

    def test_cache_stats(self, cache):
        """캐시 통계 테스트"""
        params = {"key": "value"}
        cache.set("test", params, "response")

        # 히트
        cache.get("test", params)
        # 미스
        cache.get("other", {"x": "y"})

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert "50.0%" in stats["hit_rate"]

    def test_cache_max_entries(self, cache):
        """최대 항목 수 테스트"""
        # 100개 초과 저장
        for i in range(110):
            cache.set("test", {"i": i}, f"response_{i}")

        stats = cache.get_stats()
        assert stats["entries"] <= 100


class TestCachedDecorator:
    """cached 데코레이터 테스트"""

    def test_decorator_caches_result(self):
        """데코레이터 결과 캐싱 테스트"""
        call_count = 0

        @cached("test_api", ttl=60)
        def expensive_func(value):
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        # 첫 호출
        result1 = expensive_func(value="a")
        assert call_count == 1

        # 두 번째 호출 (캐시 히트)
        result2 = expensive_func(value="a")
        assert call_count == 1  # 함수 호출 안됨
        assert result1 == result2

    def test_decorator_different_params(self):
        """다른 파라미터 캐시 분리 테스트"""
        call_count = 0

        @cached("test_api2", ttl=60)
        def func(value):
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        func(value="a")
        func(value="b")

        assert call_count == 2  # 각각 호출됨


class TestGetCachedOrCall:
    """get_cached_or_call 함수 테스트"""

    def test_calls_function_on_miss(self):
        """미스시 함수 호출 테스트"""
        called = False

        def my_func():
            nonlocal called
            called = True
            return "new_result"

        result = get_cached_or_call(
            "unique_api",
            {"unique": "params_" + str(time.time())},
            my_func
        )

        assert called is True
        assert result == "new_result"

    def test_returns_cached_on_hit(self):
        """히트시 캐시 반환 테스트"""
        from response_cache import response_cache

        # 캐시에 미리 저장
        params = {"cached": "test"}
        response_cache.set("cached_api", params, "cached_response")

        called = False

        def my_func():
            nonlocal called
            called = True
            return "new_result"

        result = get_cached_or_call("cached_api", params, my_func)

        assert called is False  # 함수 호출 안됨
        assert result == "cached_response"

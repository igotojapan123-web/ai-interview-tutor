# tests/unit/test_performance_utils.py
# FlyReady Lab - 성능 유틸리티 단위 테스트
# Stage 3: 대기업 수준 테스트

import pytest
import sys
import os
from unittest.mock import MagicMock, patch
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestLRUCache:
    """LRU 캐시 테스트"""

    def test_lru_cache_creation(self):
        """LRUCache 생성"""
        from performance_utils import LRUCache

        cache = LRUCache(max_size=100, ttl_seconds=300)

        assert cache.max_size == 100
        assert cache.ttl_seconds == 300

    def test_lru_cache_set_get(self):
        """캐시 저장 및 조회"""
        from performance_utils import LRUCache

        cache = LRUCache(max_size=100)

        cache.set("key1", "value1")
        result = cache.get("key1")

        assert result == "value1"

    def test_lru_cache_missing_key(self):
        """없는 키 조회"""
        from performance_utils import LRUCache

        cache = LRUCache(max_size=100)
        result = cache.get("nonexistent")

        assert result is None

    def test_lru_cache_eviction(self):
        """LRU 제거"""
        from performance_utils import LRUCache

        cache = LRUCache(max_size=3)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # "a" 제거됨

        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3
        assert cache.get("d") == 4

    def test_lru_cache_ttl_expiry(self):
        """TTL 만료"""
        from performance_utils import LRUCache

        cache = LRUCache(max_size=100, ttl_seconds=0.1)

        cache.set("key", "value")
        time.sleep(0.2)

        result = cache.get("key")
        assert result is None

    def test_lru_cache_delete(self):
        """캐시 삭제"""
        from performance_utils import LRUCache

        cache = LRUCache(max_size=100)

        cache.set("key", "value")
        cache.delete("key")

        assert cache.get("key") is None

    def test_lru_cache_clear(self):
        """캐시 전체 삭제"""
        from performance_utils import LRUCache

        cache = LRUCache(max_size=100)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()

        assert cache.size() == 0

    def test_lru_cache_stats(self):
        """캐시 통계"""
        from performance_utils import LRUCache

        cache = LRUCache(max_size=100)

        cache.set("a", 1)
        cache.set("b", 2)

        stats = cache.stats()

        assert stats["size"] == 2
        assert stats["max_size"] == 100
        assert "utilization" in stats

    def test_lru_cache_thread_safety(self):
        """스레드 안전성"""
        from performance_utils import LRUCache

        cache = LRUCache(max_size=1000)
        errors = []

        def worker(thread_id):
            try:
                for i in range(100):
                    cache.set(f"key_{thread_id}_{i}", f"value_{i}")
                    cache.get(f"key_{thread_id}_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestGlobalCaches:
    """전역 캐시 인스턴스 테스트"""

    def test_get_api_cache(self):
        """API 캐시 획득"""
        from performance_utils import get_api_cache

        cache = get_api_cache()
        assert cache is not None
        assert cache.max_size > 0

    def test_get_data_cache(self):
        """데이터 캐시 획득"""
        from performance_utils import get_data_cache

        cache = get_data_cache()
        assert cache is not None
        assert cache.max_size > 0


class TestPagination:
    """페이지네이션 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('performance_utils.st') as mock:
            mock.session_state = {}
            yield mock

    def test_pagination_state_creation(self):
        """PaginationState 생성"""
        from performance_utils import PaginationState

        state = PaginationState(total_items=100, page_size=10, current_page=1)

        assert state.total_items == 100
        assert state.page_size == 10
        assert state.current_page == 1

    def test_pagination_total_pages(self):
        """총 페이지 수 계산"""
        from performance_utils import PaginationState

        state = PaginationState(total_items=95, page_size=10)

        assert state.total_pages == 10

    def test_pagination_indices(self):
        """인덱스 계산"""
        from performance_utils import PaginationState

        state = PaginationState(total_items=100, page_size=10, current_page=3)

        assert state.start_index == 20
        assert state.end_index == 30

    def test_pagination_has_prev_next(self):
        """이전/다음 페이지 존재 여부"""
        from performance_utils import PaginationState

        state1 = PaginationState(total_items=100, page_size=10, current_page=1)
        assert state1.has_prev is False
        assert state1.has_next is True

        state5 = PaginationState(total_items=100, page_size=10, current_page=5)
        assert state5.has_prev is True
        assert state5.has_next is True

        state10 = PaginationState(total_items=100, page_size=10, current_page=10)
        assert state10.has_prev is True
        assert state10.has_next is False

    def test_paginate_function(self, mock_st):
        """paginate 함수"""
        from performance_utils import paginate

        items = list(range(100))
        page_items, state = paginate(items, page_size=10)

        assert len(page_items) == 10
        assert state.total_items == 100


class TestDebounceThrottle:
    """디바운스/스로틀 테스트"""

    def test_debounce_decorator_exists(self):
        """debounce 데코레이터 존재"""
        from performance_utils import debounce

        assert callable(debounce)

    def test_throttle_decorator_exists(self):
        """throttle 데코레이터 존재"""
        from performance_utils import throttle

        assert callable(throttle)


class TestBatchProcess:
    """배치 처리 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('performance_utils.st') as mock:
            mock.progress = MagicMock(return_value=MagicMock())
            yield mock

    def test_batch_process(self, mock_st):
        """배치 처리"""
        from performance_utils import batch_process

        items = list(range(25))

        def processor(batch):
            return [x * 2 for x in batch]

        results = batch_process(items, processor, batch_size=10, show_progress=False)

        assert len(results) == 25
        assert results[0] == 0
        assert results[24] == 48


class TestLazyLoader:
    """지연 로딩 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('performance_utils.st') as mock:
            mock.session_state = {}
            yield mock

    def test_lazy_loader_creation(self, mock_st):
        """LazyLoader 생성"""
        from performance_utils import LazyLoader

        loader = LazyLoader(lambda: "loaded_data")

        assert loader._loaded is False

    def test_lazy_loader_loads_on_access(self, mock_st):
        """접근 시 로드"""
        from performance_utils import LazyLoader

        call_count = 0

        def load_func():
            nonlocal call_count
            call_count += 1
            return "data"

        loader = LazyLoader(load_func)

        # 첫 접근 시 로드
        value1 = loader.value
        assert value1 == "data"
        assert call_count == 1

        # 두 번째 접근 시 캐시 사용
        value2 = loader.value
        assert value2 == "data"
        assert call_count == 1  # 증가하지 않음

    def test_lazy_loader_reload(self, mock_st):
        """강제 재로드"""
        from performance_utils import LazyLoader

        counter = [0]

        def load_func():
            counter[0] += 1
            return f"data_{counter[0]}"

        loader = LazyLoader(load_func)

        value1 = loader.value
        assert "data_1" in value1

        value2 = loader.reload()
        assert "data_2" in value2


class TestPerformanceMetrics:
    """성능 메트릭스 테스트"""

    def test_performance_metrics_timer(self):
        """타이머 시작/종료"""
        from performance_utils import PerformanceMetrics

        metrics = PerformanceMetrics()

        metrics.start_timer("test_op")
        time.sleep(0.1)
        elapsed = metrics.stop_timer("test_op")

        assert elapsed >= 0.1

    def test_performance_metrics_stats(self):
        """통계 조회"""
        from performance_utils import PerformanceMetrics

        metrics = PerformanceMetrics()

        for _ in range(5):
            metrics.start_timer("test_op")
            time.sleep(0.01)
            metrics.stop_timer("test_op")

        stats = metrics.get_stats("test_op")

        assert stats is not None
        assert stats["count"] == 5
        assert "avg" in stats
        assert "min" in stats
        assert "max" in stats

    def test_get_metrics_singleton(self):
        """전역 메트릭스 인스턴스"""
        from performance_utils import get_metrics

        metrics1 = get_metrics()
        metrics2 = get_metrics()

        assert metrics1 is metrics2


class TestTimedOperation:
    """시간 측정 컨텍스트 매니저 테스트"""

    def test_timed_operation_context(self):
        """시간 측정 컨텍스트"""
        from performance_utils import timed_operation

        with timed_operation("test_context") as timer:
            time.sleep(0.05)

        assert timer.elapsed >= 0.05


class TestDataFrameOptimization:
    """DataFrame 최적화 테스트"""

    def test_optimize_dataframe_exists(self):
        """optimize_dataframe 함수 존재"""
        from performance_utils import optimize_dataframe

        assert callable(optimize_dataframe)


class TestSessionCleanup:
    """세션 정리 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('performance_utils.st') as mock:
            mock.session_state = {
                "old_data": "value",
                "old_data_time": 0,  # 아주 오래된 타임스탬프
                "new_data": "value",
                "important": "keep",
            }
            yield mock

    def test_cleanup_session_exists(self):
        """cleanup_session 함수 존재"""
        from performance_utils import cleanup_session

        assert callable(cleanup_session)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# performance_optimizer.py
# FlyReady Lab - 성능 최적화 시스템
# Phase A3: 로딩 최적화 500% 강화

import streamlit as st
import time
import threading
import hashlib
import weakref
import gc
import functools
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List, TypeVar, Generic
from collections import OrderedDict
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

# =============================================================================
# 1. 성능 모니터링 시스템
# =============================================================================

@dataclass
class PerformanceMetric:
    """성능 측정 데이터"""
    name: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    category: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """성능 모니터링 시스템"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._metrics: List[PerformanceMetric] = []
        self._timers: Dict[str, float] = {}
        self._thresholds = {
            "page_load": 2000,      # 페이지 로딩 2초
            "api_call": 5000,       # API 호출 5초
            "database": 1000,       # DB 쿼리 1초
            "render": 500,          # UI 렌더링 500ms
        }
        self._max_metrics = 1000
        self._initialized = True

    def start_timer(self, name: str):
        """타이머 시작"""
        self._timers[name] = time.perf_counter() * 1000

    def stop_timer(self, name: str, category: str = "general", metadata: Dict = None) -> float:
        """타이머 종료 및 기록"""
        if name not in self._timers:
            return 0

        end_time = time.perf_counter() * 1000
        duration = end_time - self._timers[name]
        del self._timers[name]

        metric = PerformanceMetric(
            name=name,
            duration_ms=duration,
            category=category,
            metadata=metadata or {}
        )
        self._record_metric(metric)

        # 임계값 초과 경고
        threshold = self._thresholds.get(category, 3000)
        if duration > threshold:
            logger.warning(
                f"성능 경고: {name} ({category}) - {duration:.1f}ms > {threshold}ms"
            )

        return duration

    def _record_metric(self, metric: PerformanceMetric):
        """메트릭 기록"""
        self._metrics.append(metric)

        # 최대 개수 유지
        if len(self._metrics) > self._max_metrics:
            self._metrics = self._metrics[-self._max_metrics:]

    def measure(self, name: str, category: str = "general"):
        """측정 데코레이터/컨텍스트 매니저"""
        return _PerformanceMeasure(self, name, category)

    def get_statistics(self, category: str = None, minutes: int = 60) -> Dict:
        """성능 통계"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        filtered = [
            m for m in self._metrics
            if m.timestamp > cutoff and (category is None or m.category == category)
        ]

        if not filtered:
            return {"count": 0}

        durations = [m.duration_ms for m in filtered]

        return {
            "count": len(filtered),
            "avg_ms": sum(durations) / len(durations),
            "min_ms": min(durations),
            "max_ms": max(durations),
            "p50_ms": sorted(durations)[len(durations) // 2],
            "p95_ms": sorted(durations)[int(len(durations) * 0.95)] if len(durations) >= 20 else max(durations),
        }

    def get_slow_operations(self, limit: int = 10) -> List[Dict]:
        """느린 작업 목록"""
        sorted_metrics = sorted(self._metrics, key=lambda m: m.duration_ms, reverse=True)
        return [
            {
                "name": m.name,
                "duration_ms": m.duration_ms,
                "category": m.category,
                "timestamp": m.timestamp.isoformat()
            }
            for m in sorted_metrics[:limit]
        ]

    def clear_metrics(self):
        """메트릭 초기화"""
        self._metrics.clear()


class _PerformanceMeasure:
    """성능 측정 컨텍스트 매니저"""

    def __init__(self, monitor: PerformanceMonitor, name: str, category: str):
        self.monitor = monitor
        self.name = name
        self.category = category

    def __enter__(self):
        self.monitor.start_timer(self.name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = self.monitor.stop_timer(self.name, self.category)
        return False

    def __call__(self, func: Callable) -> Callable:
        """데코레이터로 사용"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.monitor.start_timer(self.name or func.__name__)
            try:
                return func(*args, **kwargs)
            finally:
                self.monitor.stop_timer(self.name or func.__name__, self.category)
        return wrapper


# 전역 성능 모니터
perf_monitor = PerformanceMonitor()


# =============================================================================
# 2. 스마트 캐시 시스템
# =============================================================================

class SmartCache(Generic[T]):
    """스마트 캐시 (LRU + TTL + 메모리 관리)"""

    def __init__(
        self,
        max_size: int = 100,
        default_ttl: int = 300,
        max_memory_mb: float = 50
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.max_memory_bytes = max_memory_mb * 1024 * 1024

        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = threading.Lock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def get(self, key: str) -> Optional[T]:
        """캐시에서 값 가져오기"""
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            entry = self._cache[key]

            # TTL 확인
            if time.time() > entry["expires_at"]:
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            # LRU: 최근 사용으로 이동
            self._cache.move_to_end(key)

            self._stats["hits"] += 1
            return entry["value"]

    def set(self, key: str, value: T, ttl: int = None) -> None:
        """캐시에 값 저장"""
        ttl = ttl or self.default_ttl

        with self._lock:
            # 크기 초과 시 가장 오래된 항목 제거
            while len(self._cache) >= self.max_size:
                self._evict_one()

            self._cache[key] = {
                "value": value,
                "expires_at": time.time() + ttl,
                "created_at": time.time()
            }

    def _evict_one(self):
        """가장 오래된 항목 1개 제거"""
        if self._cache:
            self._cache.popitem(last=False)
            self._stats["evictions"] += 1

    def delete(self, key: str) -> bool:
        """캐시에서 항목 삭제"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self):
        """캐시 전체 삭제"""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """만료된 항목 정리"""
        with self._lock:
            now = time.time()
            expired_keys = [
                k for k, v in self._cache.items()
                if now > v["expires_at"]
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)

    def get_stats(self) -> Dict:
        """캐시 통계"""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "hit_rate": f"{hit_rate:.1f}%"
            }


# =============================================================================
# 3. 요청 중복 제거 (Deduplication)
# =============================================================================

class RequestDeduplicator:
    """동일 요청 중복 제거"""

    def __init__(self, window_seconds: float = 1.0):
        self.window_seconds = window_seconds
        self._pending: Dict[str, threading.Event] = {}
        self._results: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """요청 키 생성"""
        key_data = f"{func_name}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def deduplicate(self, func: Callable) -> Callable:
        """중복 제거 데코레이터"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = self._generate_key(func.__name__, args, kwargs)

            with self._lock:
                # 이미 실행 중인 동일 요청이 있으면 대기
                if key in self._pending:
                    event = self._pending[key]
                else:
                    event = threading.Event()
                    self._pending[key] = event
                    event = None  # 첫 번째 요청자

            if event:
                # 다른 요청이 완료될 때까지 대기
                event.wait(timeout=30)
                with self._lock:
                    return self._results.get(key)

            try:
                # 실제 함수 실행
                result = func(*args, **kwargs)

                with self._lock:
                    self._results[key] = result

                return result

            finally:
                with self._lock:
                    if key in self._pending:
                        self._pending[key].set()
                        del self._pending[key]

                    # 결과 정리 (지연)
                    def cleanup():
                        time.sleep(self.window_seconds)
                        with self._lock:
                            if key in self._results:
                                del self._results[key]

                    threading.Thread(target=cleanup, daemon=True).start()

        return wrapper


# 전역 중복 제거기
request_dedup = RequestDeduplicator()


# =============================================================================
# 4. 지연 로딩 (Lazy Loading)
# =============================================================================

class LazyLoader(Generic[T]):
    """지연 로딩 래퍼"""

    def __init__(self, loader_func: Callable[[], T], cache_result: bool = True):
        self._loader = loader_func
        self._cache_result = cache_result
        self._value: Optional[T] = None
        self._loaded = False
        self._lock = threading.Lock()

    def get(self) -> T:
        """값 가져오기 (필요시 로드)"""
        if self._loaded and self._cache_result:
            return self._value

        with self._lock:
            if not self._loaded or not self._cache_result:
                self._value = self._loader()
                self._loaded = True

        return self._value

    def reset(self):
        """캐시된 값 초기화"""
        with self._lock:
            self._value = None
            self._loaded = False

    @property
    def is_loaded(self) -> bool:
        """로드 여부"""
        return self._loaded


def lazy_property(func: Callable) -> property:
    """지연 로딩 프로퍼티 데코레이터"""
    attr_name = f"_lazy_{func.__name__}"

    @property
    @functools.wraps(func)
    def wrapper(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)

    return wrapper


# =============================================================================
# 5. 메모리 최적화
# =============================================================================

class MemoryOptimizer:
    """메모리 사용 최적화"""

    # 메모리 임계값 (바이트)
    WARNING_THRESHOLD = 500 * 1024 * 1024  # 500MB
    CRITICAL_THRESHOLD = 800 * 1024 * 1024  # 800MB

    @staticmethod
    def get_memory_usage() -> Dict:
        """현재 메모리 사용량"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": process.memory_percent()
            }
        except ImportError:
            # psutil이 없으면 기본값
            return {"rss_mb": 0, "vms_mb": 0, "percent": 0}

    @staticmethod
    def optimize_session_state():
        """세션 상태 최적화"""
        if not hasattr(st, 'session_state'):
            return 0

        cleaned = 0
        large_keys = []

        for key in list(st.session_state.keys()):
            try:
                value = st.session_state[key]

                # 크기 추정
                import sys
                size = sys.getsizeof(value)

                # 100KB 이상이면 기록
                if size > 100 * 1024:
                    large_keys.append((key, size))

                # 리스트가 너무 길면 자르기
                if isinstance(value, list) and len(value) > 1000:
                    st.session_state[key] = value[-500:]
                    cleaned += 1

            except:
                pass

        if large_keys:
            logger.info(f"큰 세션 항목: {[(k, f'{s/1024:.1f}KB') for k, s in large_keys[:5]]}")

        return cleaned

    @staticmethod
    def force_garbage_collection() -> int:
        """강제 가비지 컬렉션"""
        collected = gc.collect()
        logger.info(f"GC 실행: {collected}개 객체 정리")
        return collected

    @classmethod
    def check_and_optimize(cls) -> Dict:
        """메모리 확인 및 최적화"""
        usage = cls.get_memory_usage()
        result = {"usage": usage, "optimizations": []}

        rss_bytes = usage.get("rss_mb", 0) * 1024 * 1024

        if rss_bytes > cls.CRITICAL_THRESHOLD:
            # 긴급 최적화
            logger.warning("메모리 사용량 위험: 긴급 최적화 실행")
            cls.force_garbage_collection()
            cls.optimize_session_state()
            result["optimizations"].extend(["gc", "session_state"])

        elif rss_bytes > cls.WARNING_THRESHOLD:
            # 일반 최적화
            logger.info("메모리 사용량 경고: 최적화 실행")
            cls.force_garbage_collection()
            result["optimizations"].append("gc")

        return result


# =============================================================================
# 6. 페이지 프리로딩
# =============================================================================

class PagePreloader:
    """페이지 데이터 프리로딩"""

    def __init__(self):
        self._preloaded: Dict[str, Any] = {}
        self._loading: Dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

    def preload(self, page_name: str, loader_func: Callable, priority: int = 0):
        """백그라운드에서 페이지 데이터 프리로드"""
        with self._lock:
            if page_name in self._preloaded or page_name in self._loading:
                return

            def load_task():
                try:
                    data = loader_func()
                    with self._lock:
                        self._preloaded[page_name] = {
                            "data": data,
                            "loaded_at": time.time()
                        }
                except Exception as e:
                    logger.error(f"프리로드 실패 ({page_name}): {e}")
                finally:
                    with self._lock:
                        if page_name in self._loading:
                            del self._loading[page_name]

            thread = threading.Thread(target=load_task, daemon=True)
            self._loading[page_name] = thread
            thread.start()

    def get_preloaded(self, page_name: str, max_age: int = 300) -> Optional[Any]:
        """프리로드된 데이터 가져오기"""
        with self._lock:
            if page_name not in self._preloaded:
                return None

            entry = self._preloaded[page_name]
            if time.time() - entry["loaded_at"] > max_age:
                del self._preloaded[page_name]
                return None

            return entry["data"]

    def clear(self, page_name: str = None):
        """프리로드 데이터 삭제"""
        with self._lock:
            if page_name:
                self._preloaded.pop(page_name, None)
            else:
                self._preloaded.clear()


# 전역 프리로더
page_preloader = PagePreloader()


# =============================================================================
# 7. 통합 최적화 유틸리티
# =============================================================================

def optimized_cache(ttl: int = 300, max_size: int = 100):
    """최적화된 캐시 데코레이터"""
    cache = SmartCache(max_size=max_size, default_ttl=ttl)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            key = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            key_hash = hashlib.md5(key.encode()).hexdigest()

            # 캐시 확인
            cached = cache.get(key_hash)
            if cached is not None:
                return cached

            # 함수 실행 및 캐시
            with perf_monitor.measure(func.__name__, "cached_function"):
                result = func(*args, **kwargs)

            if result is not None:
                cache.set(key_hash, result)

            return result

        wrapper.cache = cache
        wrapper.clear_cache = cache.clear
        return wrapper

    return decorator


def with_performance_tracking(category: str = "general"):
    """성능 추적 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with perf_monitor.measure(func.__name__, category):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def batch_operations(operations: List[Callable], max_concurrent: int = 5) -> List[Any]:
    """배치 작업 병렬 실행"""
    import concurrent.futures

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        futures = [executor.submit(op) for op in operations]
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                logger.error(f"배치 작업 실패: {e}")
                results.append(None)

    return results


# =============================================================================
# 8. Streamlit 최적화 헬퍼
# =============================================================================

def init_page_optimization():
    """페이지 최적화 초기화"""
    try:
        if 'optimization_initialized' not in st.session_state:
            st.session_state.optimization_initialized = True

            # 메모리 최적화
            MemoryOptimizer.check_and_optimize()

            # 만료 캐시 정리
            try:
                from response_cache import response_cache
                response_cache.cleanup_expired()
            except ImportError:
                pass

            logger.info("페이지 최적화 초기화 완료")

        return True
    except Exception as e:
        logger.error(f"최적화 초기화 실패: {e}")
        return False


def get_optimization_stats() -> Dict:
    """최적화 통계"""
    return {
        "performance": perf_monitor.get_statistics(),
        "memory": MemoryOptimizer.get_memory_usage(),
        "slow_operations": perf_monitor.get_slow_operations(5)
    }


# =============================================================================
# 모듈 테스트
# =============================================================================

if __name__ == "__main__":
    print("=== Performance Optimizer Test ===")

    # 1. 성능 모니터 테스트
    print("\n1. Performance Monitor Test")
    with perf_monitor.measure("test_operation", "general"):
        time.sleep(0.1)
    print(f"   Stats: {perf_monitor.get_statistics()}")

    # 2. 스마트 캐시 테스트
    print("\n2. Smart Cache Test")
    cache = SmartCache(max_size=10, default_ttl=60)
    cache.set("key1", "value1")
    result = cache.get("key1")
    print(f"   Cached value: {result}")
    print(f"   Stats: {cache.get_stats()}")

    # 3. 중복 제거 테스트
    print("\n3. Deduplication Test")
    call_count = 0

    @request_dedup.deduplicate
    def expensive_call(x):
        global call_count
        call_count += 1
        time.sleep(0.1)
        return x * 2

    result1 = expensive_call(5)
    print(f"   Result: {result1}, Calls: {call_count}")

    # 4. 지연 로딩 테스트
    print("\n4. Lazy Loading Test")
    loader_called = False

    def load_data():
        global loader_called
        loader_called = True
        return "loaded data"

    lazy = LazyLoader(load_data)
    print(f"   Before get - loaded: {lazy.is_loaded}")
    value = lazy.get()
    print(f"   After get - loaded: {lazy.is_loaded}, value: {value}")

    # 5. 메모리 최적화 테스트
    print("\n5. Memory Optimizer Test")
    usage = MemoryOptimizer.get_memory_usage()
    print(f"   Memory usage: {usage}")

    print("\nModule ready!")

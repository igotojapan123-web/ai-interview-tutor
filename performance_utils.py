# performance_utils.py
# 대기업 수준 성능 최적화 유틸리티
# FlyReady Lab - Enterprise Performance Utilities

import streamlit as st
from functools import wraps
import time
import threading
from typing import Callable, Any, Optional, Dict, List, TypeVar, Generic, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


# =============================================================================
# LRU 캐시 (메모리 제한)
# =============================================================================

class LRUCache(Generic[T]):
    """LRU (Least Recently Used) 캐시"""

    def __init__(self, max_size: int = 100, ttl_seconds: Optional[int] = None):
        """
        Args:
            max_size: 최대 항목 수
            ttl_seconds: 항목 TTL (초)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[T]:
        """캐시에서 값 조회"""
        with self._lock:
            if key not in self._cache:
                return None

            # TTL 체크
            if self.ttl_seconds:
                timestamp = self._timestamps.get(key, 0)
                if time.time() - timestamp > self.ttl_seconds:
                    del self._cache[key]
                    del self._timestamps[key]
                    return None

            # LRU 업데이트 (최근 사용으로 이동)
            self._cache.move_to_end(key)
            return self._cache[key]

    def set(self, key: str, value: T):
        """캐시에 값 저장"""
        with self._lock:
            # 이미 존재하면 업데이트
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = value
                self._timestamps[key] = time.time()
                return

            # 용량 초과시 가장 오래된 항목 제거
            while len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._timestamps.pop(oldest_key, None)

            self._cache[key] = value
            self._timestamps[key] = time.time()

    def delete(self, key: str):
        """캐시에서 삭제"""
        with self._lock:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)

    def clear(self):
        """캐시 전체 삭제"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

    def size(self) -> int:
        """현재 캐시 크기"""
        return len(self._cache)

    def stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "utilization": len(self._cache) / self.max_size * 100
        }


# 전역 캐시 인스턴스
_api_cache = LRUCache[Any](max_size=100, ttl_seconds=300)
_data_cache = LRUCache[Any](max_size=200, ttl_seconds=3600)


def get_api_cache() -> LRUCache:
    """API 캐시 인스턴스 반환"""
    return _api_cache


def get_data_cache() -> LRUCache:
    """데이터 캐시 인스턴스 반환"""
    return _data_cache


# =============================================================================
# 페이지네이션 (Lazy Loading)
# =============================================================================

@dataclass
class PaginationState:
    """페이지네이션 상태"""
    total_items: int
    page_size: int
    current_page: int = 1

    @property
    def total_pages(self) -> int:
        return max(1, (self.total_items + self.page_size - 1) // self.page_size)

    @property
    def start_index(self) -> int:
        return (self.current_page - 1) * self.page_size

    @property
    def end_index(self) -> int:
        return min(self.start_index + self.page_size, self.total_items)

    @property
    def has_prev(self) -> bool:
        return self.current_page > 1

    @property
    def has_next(self) -> bool:
        return self.current_page < self.total_pages


def paginate(
    items: List[T],
    page_size: int = 20,
    state_key: str = "pagination"
) -> tuple[List[T], PaginationState]:
    """리스트 페이지네이션

    Args:
        items: 전체 항목 리스트
        page_size: 페이지당 항목 수
        state_key: 세션 상태 키

    Returns:
        (현재 페이지 항목, 페이지네이션 상태)
    """
    # 현재 페이지 가져오기
    if state_key not in st.session_state:
        st.session_state[state_key] = 1

    current_page = st.session_state[state_key]
    total_items = len(items)

    state = PaginationState(
        total_items=total_items,
        page_size=page_size,
        current_page=current_page
    )

    # 페이지 범위 조정
    if state.current_page > state.total_pages:
        state.current_page = state.total_pages
        st.session_state[state_key] = state.current_page

    # 현재 페이지 항목
    page_items = items[state.start_index:state.end_index]

    return page_items, state


def render_pagination_controls(
    state: PaginationState,
    state_key: str = "pagination",
    show_info: bool = True
):
    """페이지네이션 컨트롤 렌더링"""
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button("처음", disabled=not state.has_prev, key=f"{state_key}_first"):
            st.session_state[state_key] = 1
            st.rerun()

    with col2:
        if st.button("이전", disabled=not state.has_prev, key=f"{state_key}_prev"):
            st.session_state[state_key] = state.current_page - 1
            st.rerun()

    with col3:
        if show_info:
            st.markdown(
                f"<div style='text-align:center;padding:8px;'>"
                f"<b>{state.current_page}</b> / {state.total_pages} "
                f"<span style='color:#666;'>({state.total_items}개)</span>"
                f"</div>",
                unsafe_allow_html=True
            )

    with col4:
        if st.button("다음", disabled=not state.has_next, key=f"{state_key}_next"):
            st.session_state[state_key] = state.current_page + 1
            st.rerun()

    with col5:
        if st.button("마지막", disabled=not state.has_next, key=f"{state_key}_last"):
            st.session_state[state_key] = state.total_pages
            st.rerun()


# =============================================================================
# 가상 스크롤 (대용량 리스트)
# =============================================================================

def virtual_list(
    items: List[T],
    render_func: Callable[[T, int], None],
    visible_count: int = 20,
    item_height: int = 50,
    state_key: str = "virtual_scroll"
):
    """가상 스크롤 리스트

    Args:
        items: 전체 항목
        render_func: 항목 렌더링 함수 (item, index) -> None
        visible_count: 보이는 항목 수
        item_height: 항목 높이 (px)
        state_key: 상태 키
    """
    total = len(items)

    if state_key not in st.session_state:
        st.session_state[state_key] = 0

    scroll_position = st.session_state[state_key]

    # 표시할 항목 범위 계산
    start_idx = max(0, scroll_position)
    end_idx = min(total, start_idx + visible_count)

    # 스크롤 영역 렌더링
    container_height = visible_count * item_height

    st.markdown(f"""
    <div style="height:{container_height}px;overflow-y:auto;border:1px solid #e2e8f0;border-radius:8px;">
    """, unsafe_allow_html=True)

    # 항목 렌더링
    for idx in range(start_idx, end_idx):
        render_func(items[idx], idx)

    st.markdown("</div>", unsafe_allow_html=True)

    # 스크롤 컨트롤
    if total > visible_count:
        col1, col2 = st.columns([3, 1])
        with col1:
            new_pos = st.slider(
                "스크롤",
                0,
                total - visible_count,
                scroll_position,
                key=f"{state_key}_slider",
                label_visibility="collapsed"
            )
            if new_pos != scroll_position:
                st.session_state[state_key] = new_pos


# =============================================================================
# 디바운싱 / 스로틀링
# =============================================================================

def debounce(wait_seconds: float):
    """디바운스 데코레이터 (연속 호출 시 마지막만 실행)"""
    def decorator(func: Callable) -> Callable:
        last_call_key = f"_debounce_{func.__name__}_last"
        timer_key = f"_debounce_{func.__name__}_timer"

        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()

            # 이전 타이머 취소
            if timer_key in st.session_state:
                st.session_state[timer_key] = None

            st.session_state[last_call_key] = current_time

            # 지연 후 실행
            def delayed_call():
                time.sleep(wait_seconds)
                if st.session_state.get(last_call_key) == current_time:
                    return func(*args, **kwargs)

            # 별도 스레드에서 실행
            thread = threading.Thread(target=delayed_call)
            st.session_state[timer_key] = thread
            thread.start()

        return wrapper
    return decorator


def throttle(min_interval_seconds: float):
    """스로틀 데코레이터 (최소 간격으로 실행 제한)"""
    def decorator(func: Callable) -> Callable:
        last_call_key = f"_throttle_{func.__name__}"

        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            last_call = st.session_state.get(last_call_key, 0)

            if current_time - last_call >= min_interval_seconds:
                st.session_state[last_call_key] = current_time
                return func(*args, **kwargs)
            else:
                logger.debug(f"Throttled: {func.__name__}")
                return None

        return wrapper
    return decorator


# =============================================================================
# 배치 처리
# =============================================================================

def batch_process(
    items: List[T],
    processor: Callable[[List[T]], List[Any]],
    batch_size: int = 10,
    show_progress: bool = True,
    progress_label: str = "처리 중"
) -> List[Any]:
    """배치 처리

    Args:
        items: 처리할 항목들
        processor: 배치 처리 함수
        batch_size: 배치 크기
        show_progress: 진행률 표시
        progress_label: 진행률 레이블

    Returns:
        처리 결과 리스트
    """
    results = []
    total = len(items)
    batches = [items[i:i + batch_size] for i in range(0, total, batch_size)]

    if show_progress:
        progress_bar = st.progress(0, text=progress_label)

    for i, batch in enumerate(batches):
        batch_results = processor(batch)
        results.extend(batch_results)

        if show_progress:
            progress = (i + 1) / len(batches)
            progress_bar.progress(progress, text=f"{progress_label} ({i + 1}/{len(batches)})")

    if show_progress:
        progress_bar.empty()

    return results


# =============================================================================
# 지연 로딩 (Lazy Loading)
# =============================================================================

class LazyLoader(Generic[T]):
    """지연 로딩 래퍼"""

    def __init__(self, loader_func: Callable[[], T], cache_key: Optional[str] = None):
        """
        Args:
            loader_func: 데이터 로드 함수
            cache_key: 캐시 키 (None이면 캐시 안함)
        """
        self._loader_func = loader_func
        self._cache_key = cache_key
        self._loaded = False
        self._value: Optional[T] = None

    @property
    def value(self) -> T:
        """값 반환 (필요시 로드)"""
        if not self._loaded:
            # 캐시 확인
            if self._cache_key and self._cache_key in st.session_state:
                self._value = st.session_state[self._cache_key]
            else:
                self._value = self._loader_func()
                if self._cache_key:
                    st.session_state[self._cache_key] = self._value

            self._loaded = True

        return self._value

    def reload(self) -> T:
        """강제 재로드"""
        self._loaded = False
        if self._cache_key and self._cache_key in st.session_state:
            del st.session_state[self._cache_key]
        return self.value


def lazy_load(cache_key: Optional[str] = None):
    """지연 로딩 데코레이터"""
    def decorator(func: Callable[[], T]) -> LazyLoader[T]:
        return LazyLoader(func, cache_key)
    return decorator


# =============================================================================
# 성능 메트릭스
# =============================================================================

@dataclass
class PerformanceMetrics:
    """성능 메트릭스 수집"""

    _metrics: Dict[str, List[float]] = field(default_factory=dict)
    _start_times: Dict[str, float] = field(default_factory=dict)

    def start_timer(self, name: str):
        """타이머 시작"""
        self._start_times[name] = time.time()

    def stop_timer(self, name: str) -> float:
        """타이머 종료 및 시간 반환"""
        if name not in self._start_times:
            return 0.0

        elapsed = time.time() - self._start_times[name]
        del self._start_times[name]

        if name not in self._metrics:
            self._metrics[name] = []

        self._metrics[name].append(elapsed)

        # 최근 100개만 유지
        if len(self._metrics[name]) > 100:
            self._metrics[name] = self._metrics[name][-100:]

        return elapsed

    def get_stats(self, name: str) -> Optional[Dict[str, float]]:
        """통계 반환"""
        if name not in self._metrics or not self._metrics[name]:
            return None

        values = self._metrics[name]
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "last": values[-1]
        }

    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """모든 통계 반환"""
        return {name: self.get_stats(name) for name in self._metrics if self._metrics[name]}


# 전역 메트릭스 인스턴스
_performance_metrics = PerformanceMetrics()


def get_metrics() -> PerformanceMetrics:
    """성능 메트릭스 인스턴스 반환"""
    return _performance_metrics


def timed_operation(name: str):
    """시간 측정 컨텍스트 매니저"""
    class TimedContext:
        def __init__(self):
            self.elapsed = 0.0

        def __enter__(self):
            _performance_metrics.start_timer(name)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.elapsed = _performance_metrics.stop_timer(name)
            return False

    return TimedContext()


# =============================================================================
# 메모리 최적화
# =============================================================================

def optimize_dataframe(df):
    """DataFrame 메모리 최적화"""
    try:
        import pandas as pd

        for col in df.columns:
            col_type = df[col].dtype

            # 정수형 최적화
            if col_type == 'int64':
                if df[col].min() >= 0:
                    if df[col].max() <= 255:
                        df[col] = df[col].astype('uint8')
                    elif df[col].max() <= 65535:
                        df[col] = df[col].astype('uint16')
                    elif df[col].max() <= 4294967295:
                        df[col] = df[col].astype('uint32')
                else:
                    if df[col].min() >= -128 and df[col].max() <= 127:
                        df[col] = df[col].astype('int8')
                    elif df[col].min() >= -32768 and df[col].max() <= 32767:
                        df[col] = df[col].astype('int16')
                    elif df[col].min() >= -2147483648 and df[col].max() <= 2147483647:
                        df[col] = df[col].astype('int32')

            # 실수형 최적화
            elif col_type == 'float64':
                df[col] = df[col].astype('float32')

            # 문자열 카테고리화
            elif col_type == 'object':
                unique_ratio = len(df[col].unique()) / len(df[col])
                if unique_ratio < 0.5:  # 고유값 비율이 50% 미만이면 카테고리로
                    df[col] = df[col].astype('category')

        return df
    except ImportError:
        return df


# =============================================================================
# 세션 정리
# =============================================================================

def cleanup_session(max_age_seconds: int = 3600, exclude_keys: List[str] = None):
    """오래된 세션 데이터 정리

    Args:
        max_age_seconds: 최대 유지 시간 (초)
        exclude_keys: 제외할 키 패턴
    """
    exclude_keys = exclude_keys or []
    current_time = time.time()

    keys_to_remove = []

    for key in list(st.session_state.keys()):
        # 제외 패턴 체크
        if any(pattern in key for pattern in exclude_keys):
            continue

        # 타임스탬프가 있는 캐시 키 체크
        if key.endswith("_time"):
            timestamp = st.session_state.get(key, 0)
            if isinstance(timestamp, (int, float)) and current_time - timestamp > max_age_seconds:
                base_key = key[:-5]
                keys_to_remove.extend([key, base_key])

    for key in set(keys_to_remove):
        if key in st.session_state:
            del st.session_state[key]

    if keys_to_remove:
        logger.debug(f"Session cleanup: {len(keys_to_remove)} items removed")


# =============================================================================
# 성능 대시보드 컴포넌트
# =============================================================================

def render_performance_dashboard():
    """성능 대시보드 렌더링 (관리자용)"""
    st.subheader("성능 메트릭스")

    # 캐시 상태
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**API 캐시**")
        api_stats = _api_cache.stats()
        st.metric("사용량", f"{api_stats['size']}/{api_stats['max_size']}")
        st.progress(api_stats['utilization'] / 100)

    with col2:
        st.markdown("**데이터 캐시**")
        data_stats = _data_cache.stats()
        st.metric("사용량", f"{data_stats['size']}/{data_stats['max_size']}")
        st.progress(data_stats['utilization'] / 100)

    # 성능 통계
    st.markdown("**실행 시간 통계**")
    all_stats = _performance_metrics.get_all_stats()

    if all_stats:
        for name, stats in all_stats.items():
            if stats:
                st.markdown(f"**{name}**")
                cols = st.columns(4)
                cols[0].metric("평균", f"{stats['avg']:.3f}s")
                cols[1].metric("최소", f"{stats['min']:.3f}s")
                cols[2].metric("최대", f"{stats['max']:.3f}s")
                cols[3].metric("횟수", f"{stats['count']}")
    else:
        st.info("수집된 성능 데이터가 없습니다.")

    # 세션 상태
    import sys
    session_size = sum(sys.getsizeof(v) for v in st.session_state.values()) / (1024 * 1024)
    st.metric("세션 메모리", f"{session_size:.2f} MB")

    # 정리 버튼
    if st.button("캐시 정리"):
        _api_cache.clear()
        _data_cache.clear()
        cleanup_session()
        st.success("캐시가 정리되었습니다.")
        st.rerun()

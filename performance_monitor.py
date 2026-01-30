# performance_monitor.py
# 성능 모니터링 시스템 - Prometheus 메트릭 형식 지원

import time
import threading
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from collections import defaultdict
from functools import wraps

try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# ============================================================
# 메트릭 타입
# ============================================================

class MetricType:
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """메트릭 정의"""
    name: str
    type: str
    description: str
    value: float = 0
    labels: Dict[str, str] = None
    buckets: List[float] = None  # histogram용
    observations: List[float] = None  # summary용

    def __post_init__(self):
        if self.labels is None:
            self.labels = {}
        if self.buckets is None:
            self.buckets = [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
        if self.observations is None:
            self.observations = []


# ============================================================
# 성능 모니터
# ============================================================

class PerformanceMonitor:
    """성능 메트릭 수집 및 모니터링"""

    def __init__(self):
        self._lock = threading.Lock()
        self._metrics: Dict[str, Metric] = {}
        self._histogram_buckets: Dict[str, Dict[float, int]] = defaultdict(lambda: defaultdict(int))
        self._start_time = time.time()

        # 기본 메트릭 등록
        self._register_default_metrics()

    def _register_default_metrics(self) -> None:
        """기본 메트릭 등록"""
        # 요청 메트릭
        self.register("http_requests_total", MetricType.COUNTER, "Total HTTP requests")
        self.register("http_request_duration_seconds", MetricType.HISTOGRAM, "HTTP request duration")
        self.register("http_requests_in_progress", MetricType.GAUGE, "HTTP requests in progress")

        # API 메트릭
        self.register("api_calls_total", MetricType.COUNTER, "Total API calls")
        self.register("api_call_duration_seconds", MetricType.HISTOGRAM, "API call duration")
        self.register("api_errors_total", MetricType.COUNTER, "Total API errors")

        # 시스템 메트릭
        self.register("system_cpu_percent", MetricType.GAUGE, "CPU usage percent")
        self.register("system_memory_percent", MetricType.GAUGE, "Memory usage percent")
        self.register("system_disk_percent", MetricType.GAUGE, "Disk usage percent")

        # 앱 메트릭
        self.register("app_uptime_seconds", MetricType.GAUGE, "Application uptime")
        self.register("active_users", MetricType.GAUGE, "Active users")
        self.register("cache_hits_total", MetricType.COUNTER, "Cache hits")
        self.register("cache_misses_total", MetricType.COUNTER, "Cache misses")

    # -------------------------------------------------------------------------
    # 메트릭 관리
    # -------------------------------------------------------------------------

    def register(
        self,
        name: str,
        metric_type: str,
        description: str,
        labels: Dict[str, str] = None
    ) -> None:
        """메트릭 등록"""
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._metrics:
                self._metrics[key] = Metric(
                    name=name,
                    type=metric_type,
                    description=description,
                    labels=labels or {}
                )

    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """메트릭 키 생성"""
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    # -------------------------------------------------------------------------
    # Counter
    # -------------------------------------------------------------------------

    def inc(self, name: str, value: float = 1, labels: Dict[str, str] = None) -> None:
        """카운터 증가"""
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._metrics:
                self.register(name, MetricType.COUNTER, "", labels)
            self._metrics[key].value += value

    # -------------------------------------------------------------------------
    # Gauge
    # -------------------------------------------------------------------------

    def set(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """게이지 설정"""
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._metrics:
                self.register(name, MetricType.GAUGE, "", labels)
            self._metrics[key].value = value

    def inc_gauge(self, name: str, value: float = 1, labels: Dict[str, str] = None) -> None:
        """게이지 증가"""
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._metrics:
                self.register(name, MetricType.GAUGE, "", labels)
            self._metrics[key].value += value

    def dec_gauge(self, name: str, value: float = 1, labels: Dict[str, str] = None) -> None:
        """게이지 감소"""
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._metrics:
                self.register(name, MetricType.GAUGE, "", labels)
            self._metrics[key].value -= value

    # -------------------------------------------------------------------------
    # Histogram
    # -------------------------------------------------------------------------

    def observe(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """히스토그램 관측"""
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._metrics:
                self.register(name, MetricType.HISTOGRAM, "", labels)

            metric = self._metrics[key]
            metric.observations.append(value)

            # 버킷 업데이트
            for bucket in metric.buckets:
                if value <= bucket:
                    self._histogram_buckets[key][bucket] += 1

            # 최근 1000개만 유지
            if len(metric.observations) > 1000:
                metric.observations = metric.observations[-1000:]

    # -------------------------------------------------------------------------
    # 시스템 메트릭 수집
    # -------------------------------------------------------------------------

    def collect_system_metrics(self) -> None:
        """시스템 메트릭 수집"""
        try:
            # CPU
            cpu = psutil.cpu_percent(interval=0.1)
            self.set("system_cpu_percent", cpu)

            # Memory
            memory = psutil.virtual_memory()
            self.set("system_memory_percent", memory.percent)

            # Disk
            disk = psutil.disk_usage("/")
            self.set("system_disk_percent", disk.percent)

            # Uptime
            self.set("app_uptime_seconds", time.time() - self._start_time)

        except Exception as e:
            logger.error(f"시스템 메트릭 수집 실패: {e}")

    # -------------------------------------------------------------------------
    # 메트릭 조회
    # -------------------------------------------------------------------------

    def get(self, name: str, labels: Dict[str, str] = None) -> Optional[float]:
        """메트릭 값 조회"""
        with self._lock:
            key = self._make_key(name, labels)
            metric = self._metrics.get(key)
            return metric.value if metric else None

    def get_all(self) -> Dict[str, Any]:
        """모든 메트릭 조회"""
        with self._lock:
            result = {}
            for key, metric in self._metrics.items():
                result[key] = {
                    "name": metric.name,
                    "type": metric.type,
                    "value": metric.value,
                    "labels": metric.labels
                }
            return result

    # -------------------------------------------------------------------------
    # Prometheus 형식 출력
    # -------------------------------------------------------------------------

    def export_prometheus(self) -> str:
        """Prometheus 형식으로 메트릭 내보내기"""
        self.collect_system_metrics()

        lines = []
        with self._lock:
            # 메트릭별로 그룹화
            by_name = defaultdict(list)
            for key, metric in self._metrics.items():
                by_name[metric.name].append((key, metric))

            for name, metrics in sorted(by_name.items()):
                first_metric = metrics[0][1]

                # HELP
                if first_metric.description:
                    lines.append(f"# HELP {name} {first_metric.description}")

                # TYPE
                lines.append(f"# TYPE {name} {first_metric.type}")

                # Values
                for key, metric in metrics:
                    if metric.labels:
                        label_str = ",".join(f'{k}="{v}"' for k, v in metric.labels.items())
                        lines.append(f"{name}{{{label_str}}} {metric.value}")
                    else:
                        lines.append(f"{name} {metric.value}")

                    # Histogram 버킷
                    if metric.type == MetricType.HISTOGRAM and metric.observations:
                        for bucket in metric.buckets:
                            count = self._histogram_buckets[key].get(bucket, 0)
                            lines.append(f'{name}_bucket{{le="{bucket}"}} {count}')
                        lines.append(f'{name}_bucket{{le="+Inf"}} {len(metric.observations)}')
                        lines.append(f"{name}_count {len(metric.observations)}")
                        lines.append(f"{name}_sum {sum(metric.observations)}")

                lines.append("")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # 대시보드 데이터
    # -------------------------------------------------------------------------

    def get_dashboard_data(self) -> Dict[str, Any]:
        """대시보드용 데이터"""
        self.collect_system_metrics()

        with self._lock:
            return {
                "system": {
                    "cpu": self.get("system_cpu_percent") or 0,
                    "memory": self.get("system_memory_percent") or 0,
                    "disk": self.get("system_disk_percent") or 0,
                    "uptime": self.get("app_uptime_seconds") or 0
                },
                "requests": {
                    "total": self.get("http_requests_total") or 0,
                    "in_progress": self.get("http_requests_in_progress") or 0
                },
                "api": {
                    "total_calls": self.get("api_calls_total") or 0,
                    "errors": self.get("api_errors_total") or 0
                },
                "cache": {
                    "hits": self.get("cache_hits_total") or 0,
                    "misses": self.get("cache_misses_total") or 0
                },
                "timestamp": datetime.now().isoformat()
            }


# 전역 인스턴스
monitor = PerformanceMonitor()


# ============================================================
# 데코레이터
# ============================================================

def track_time(metric_name: str, labels: Dict[str, str] = None):
    """실행 시간 추적 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start
                monitor.observe(metric_name, duration, labels)
        return wrapper
    return decorator


def count_calls(metric_name: str, labels: Dict[str, str] = None):
    """호출 횟수 카운팅 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor.inc(metric_name, 1, labels)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================
# 간편 함수
# ============================================================

def track_request(duration: float, method: str = "GET", status: int = 200) -> None:
    """HTTP 요청 추적"""
    labels = {"method": method, "status": str(status)}
    monitor.inc("http_requests_total", 1, labels)
    monitor.observe("http_request_duration_seconds", duration, labels)


def track_api_call(api_type: str, duration: float, success: bool = True) -> None:
    """API 호출 추적"""
    labels = {"api": api_type}
    monitor.inc("api_calls_total", 1, labels)
    monitor.observe("api_call_duration_seconds", duration, labels)
    if not success:
        monitor.inc("api_errors_total", 1, labels)


def track_cache(hit: bool) -> None:
    """캐시 히트/미스 추적"""
    if hit:
        monitor.inc("cache_hits_total")
    else:
        monitor.inc("cache_misses_total")


def set_active_users(count: int) -> None:
    """활성 사용자 수 설정"""
    monitor.set("active_users", count)


def get_metrics() -> Dict[str, Any]:
    """모든 메트릭 조회"""
    return monitor.get_all()


def get_prometheus_metrics() -> str:
    """Prometheus 형식 메트릭"""
    return monitor.export_prometheus()


# ============================================================
# Streamlit 컴포넌트
# ============================================================

def render_performance_dashboard():
    """성능 대시보드"""
    import streamlit as st

    st.markdown("### 시스템 성능")

    data = monitor.get_dashboard_data()

    # 시스템 메트릭
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("CPU", f"{data['system']['cpu']:.1f}%")
    with col2:
        st.metric("Memory", f"{data['system']['memory']:.1f}%")
    with col3:
        st.metric("Disk", f"{data['system']['disk']:.1f}%")
    with col4:
        uptime_hours = data["system"]["uptime"] / 3600
        st.metric("Uptime", f"{uptime_hours:.1f}h")

    # API 메트릭
    st.markdown("#### API 현황")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 호출", int(data["api"]["total_calls"]))
    with col2:
        st.metric("에러", int(data["api"]["errors"]))
    with col3:
        hits = data["cache"]["hits"]
        total = hits + data["cache"]["misses"]
        rate = (hits / total * 100) if total > 0 else 0
        st.metric("캐시 히트율", f"{rate:.1f}%")


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=== Performance Monitor ===")

    # 테스트 메트릭
    for i in range(10):
        track_request(0.1 + i * 0.05, "GET", 200)
        track_api_call("openai", 0.5 + i * 0.1)

    track_cache(True)
    track_cache(True)
    track_cache(False)

    set_active_users(5)

    # 대시보드 데이터
    print("\n대시보드:")
    import json
    print(json.dumps(monitor.get_dashboard_data(), indent=2))

    # Prometheus 형식
    print("\nPrometheus 메트릭:")
    print(monitor.export_prometheus()[:500] + "...")

    print("\nReady!")

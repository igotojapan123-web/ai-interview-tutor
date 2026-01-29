"""
Metrics Collector.

Prometheus-compatible metrics collection.
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricValue:
    """Metric value with labels."""
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class Counter:
    """
    Counter metric - monotonically increasing value.

    Use for: requests, errors, items processed
    """

    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: Dict[Tuple, float] = defaultdict(float)

    def inc(self, amount: float = 1, **label_values) -> None:
        """Increment counter."""
        key = tuple(label_values.get(l, "") for l in self.labels)
        self._values[key] += amount

    def get(self, **label_values) -> float:
        """Get current value."""
        key = tuple(label_values.get(l, "") for l in self.labels)
        return self._values[key]

    def collect(self) -> List[MetricValue]:
        """Collect all values."""
        result = []
        for key, value in self._values.items():
            labels = dict(zip(self.labels, key))
            result.append(MetricValue(value=value, labels=labels))
        return result


class Gauge:
    """
    Gauge metric - value that can go up and down.

    Use for: temperature, memory usage, active connections
    """

    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: Dict[Tuple, float] = defaultdict(float)

    def set(self, value: float, **label_values) -> None:
        """Set gauge value."""
        key = tuple(label_values.get(l, "") for l in self.labels)
        self._values[key] = value

    def inc(self, amount: float = 1, **label_values) -> None:
        """Increment gauge."""
        key = tuple(label_values.get(l, "") for l in self.labels)
        self._values[key] += amount

    def dec(self, amount: float = 1, **label_values) -> None:
        """Decrement gauge."""
        key = tuple(label_values.get(l, "") for l in self.labels)
        self._values[key] -= amount

    def get(self, **label_values) -> float:
        """Get current value."""
        key = tuple(label_values.get(l, "") for l in self.labels)
        return self._values[key]

    def collect(self) -> List[MetricValue]:
        """Collect all values."""
        result = []
        for key, value in self._values.items():
            labels = dict(zip(self.labels, key))
            result.append(MetricValue(value=value, labels=labels))
        return result


class Histogram:
    """
    Histogram metric - distribution of values.

    Use for: request duration, response size
    """

    DEFAULT_BUCKETS = (
        0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float("inf")
    )

    def __init__(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[Tuple[float, ...]] = None
    ):
        self.name = name
        self.description = description
        self.labels = labels or []
        self.buckets = buckets or self.DEFAULT_BUCKETS

        self._bucket_counts: Dict[Tuple, Dict[float, int]] = defaultdict(
            lambda: {b: 0 for b in self.buckets}
        )
        self._sums: Dict[Tuple, float] = defaultdict(float)
        self._counts: Dict[Tuple, int] = defaultdict(int)

    def observe(self, value: float, **label_values) -> None:
        """Observe a value."""
        key = tuple(label_values.get(l, "") for l in self.labels)

        self._sums[key] += value
        self._counts[key] += 1

        for bucket in self.buckets:
            if value <= bucket:
                self._bucket_counts[key][bucket] += 1

    def get_summary(self, **label_values) -> Dict[str, float]:
        """Get histogram summary."""
        key = tuple(label_values.get(l, "") for l in self.labels)

        count = self._counts[key]
        if count == 0:
            return {"count": 0, "sum": 0, "avg": 0}

        return {
            "count": count,
            "sum": self._sums[key],
            "avg": self._sums[key] / count,
            "buckets": dict(self._bucket_counts[key])
        }

    def collect(self) -> List[Dict[str, Any]]:
        """Collect all histogram data."""
        result = []
        for key in self._counts.keys():
            labels = dict(zip(self.labels, key))
            result.append({
                "labels": labels,
                "count": self._counts[key],
                "sum": self._sums[key],
                "buckets": dict(self._bucket_counts[key])
            })
        return result


class MetricsCollector:
    """
    Central metrics collector.

    Manages all application metrics and provides Prometheus export.
    """

    def __init__(self):
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}

        # Pre-defined metrics
        self._setup_default_metrics()

    def _setup_default_metrics(self) -> None:
        """Set up default application metrics."""
        # HTTP metrics
        self.create_counter(
            "http_requests_total",
            "Total HTTP requests",
            labels=["method", "endpoint", "status"]
        )
        self.create_histogram(
            "http_request_duration_seconds",
            "HTTP request duration",
            labels=["method", "endpoint"]
        )

        # Database metrics
        self.create_counter(
            "db_queries_total",
            "Total database queries",
            labels=["operation", "table"]
        )
        self.create_histogram(
            "db_query_duration_seconds",
            "Database query duration",
            labels=["operation"]
        )

        # Cache metrics
        self.create_counter(
            "cache_requests_total",
            "Total cache requests",
            labels=["operation", "result"]
        )

        # AI metrics
        self.create_counter(
            "ai_requests_total",
            "Total AI API requests",
            labels=["provider", "model"]
        )
        self.create_histogram(
            "ai_request_duration_seconds",
            "AI request duration",
            labels=["provider"]
        )

        # Business metrics
        self.create_counter(
            "interviews_total",
            "Total interviews",
            labels=["type", "status"]
        )
        self.create_gauge(
            "active_users",
            "Current active users"
        )
        self.create_gauge(
            "active_sessions",
            "Current active interview sessions"
        )

    # =========================================================================
    # Metric Creation
    # =========================================================================

    def create_counter(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None
    ) -> Counter:
        """Create and register a counter."""
        counter = Counter(name, description, labels)
        self._counters[name] = counter
        return counter

    def create_gauge(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None
    ) -> Gauge:
        """Create and register a gauge."""
        gauge = Gauge(name, description, labels)
        self._gauges[name] = gauge
        return gauge

    def create_histogram(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[Tuple[float, ...]] = None
    ) -> Histogram:
        """Create and register a histogram."""
        histogram = Histogram(name, description, labels, buckets)
        self._histograms[name] = histogram
        return histogram

    # =========================================================================
    # Metric Access
    # =========================================================================

    def counter(self, name: str) -> Optional[Counter]:
        """Get counter by name."""
        return self._counters.get(name)

    def gauge(self, name: str) -> Optional[Gauge]:
        """Get gauge by name."""
        return self._gauges.get(name)

    def histogram(self, name: str) -> Optional[Histogram]:
        """Get histogram by name."""
        return self._histograms.get(name)

    # =========================================================================
    # Collection & Export
    # =========================================================================

    def collect_all(self) -> Dict[str, Any]:
        """Collect all metrics."""
        return {
            "counters": {
                name: counter.collect()
                for name, counter in self._counters.items()
            },
            "gauges": {
                name: gauge.collect()
                for name, gauge in self._gauges.items()
            },
            "histograms": {
                name: histogram.collect()
                for name, histogram in self._histograms.items()
            }
        }

    def to_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        # Counters
        for name, counter in self._counters.items():
            lines.append(f"# HELP {name} {counter.description}")
            lines.append(f"# TYPE {name} counter")

            for value in counter.collect():
                label_str = self._format_labels(value.labels)
                lines.append(f"{name}{label_str} {value.value}")

        # Gauges
        for name, gauge in self._gauges.items():
            lines.append(f"# HELP {name} {gauge.description}")
            lines.append(f"# TYPE {name} gauge")

            for value in gauge.collect():
                label_str = self._format_labels(value.labels)
                lines.append(f"{name}{label_str} {value.value}")

        # Histograms
        for name, histogram in self._histograms.items():
            lines.append(f"# HELP {name} {histogram.description}")
            lines.append(f"# TYPE {name} histogram")

            for data in histogram.collect():
                label_str = self._format_labels(data["labels"])

                # Buckets
                for bucket, count in data["buckets"].items():
                    bucket_labels = {**data["labels"], "le": str(bucket)}
                    bucket_label_str = self._format_labels(bucket_labels)
                    lines.append(f"{name}_bucket{bucket_label_str} {count}")

                lines.append(f"{name}_sum{label_str} {data['sum']}")
                lines.append(f"{name}_count{label_str} {data['count']}")

        return "\n".join(lines)

    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus."""
        if not labels:
            return ""

        parts = [f'{k}="{v}"' for k, v in labels.items()]
        return "{" + ",".join(parts) + "}"


# Singleton instance
metrics_collector = MetricsCollector()


# =========================================================================
# Decorators
# =========================================================================

def measure_time(histogram_name: str, **label_values):
    """
    Decorator to measure function execution time.

    Usage:
        @measure_time("http_request_duration_seconds", method="GET")
        async def handler():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            histogram = metrics_collector.histogram(histogram_name)
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                if histogram:
                    histogram.observe(time.time() - start, **label_values)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            histogram = metrics_collector.histogram(histogram_name)
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                if histogram:
                    histogram.observe(time.time() - start, **label_values)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def count_calls(counter_name: str, **label_values):
    """
    Decorator to count function calls.

    Usage:
        @count_calls("api_calls_total", endpoint="/users")
        async def get_users():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            counter = metrics_collector.counter(counter_name)
            if counter:
                counter.inc(**label_values)
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            counter = metrics_collector.counter(counter_name)
            if counter:
                counter.inc(**label_values)
            return func(*args, **kwargs)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator

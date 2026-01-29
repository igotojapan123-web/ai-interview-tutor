"""
Analytics Module.

Enterprise-grade analytics, tracking, and visualization.
"""

from src.analytics.tracker import (
    AnalyticsTracker,
    analytics_tracker,
    track_event,
    track_page_view,
)
from src.analytics.metrics import (
    MetricsCollector,
    metrics_collector,
    Counter,
    Gauge,
    Histogram,
)
from src.analytics.dashboard import (
    AnalyticsDashboard,
    DashboardWidget,
    ChartType,
)
from src.analytics.progress import (
    ProgressTracker,
    LearningProgress,
    SkillLevel,
)
from src.analytics.reports import (
    ReportGenerator,
    ReportType,
    ReportFormat,
)

__all__ = [
    # Tracker
    "AnalyticsTracker",
    "analytics_tracker",
    "track_event",
    "track_page_view",
    # Metrics
    "MetricsCollector",
    "metrics_collector",
    "Counter",
    "Gauge",
    "Histogram",
    # Dashboard
    "AnalyticsDashboard",
    "DashboardWidget",
    "ChartType",
    # Progress
    "ProgressTracker",
    "LearningProgress",
    "SkillLevel",
    # Reports
    "ReportGenerator",
    "ReportType",
    "ReportFormat",
]

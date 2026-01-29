"""
Analytics Dashboard.

Dashboard data providers and visualization helpers.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ChartType(str, Enum):
    """Chart visualization types."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"
    SCATTER = "scatter"
    RADAR = "radar"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    FUNNEL = "funnel"


class TimeRange(str, Enum):
    """Time range options."""
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_YEAR = "this_year"
    CUSTOM = "custom"


@dataclass
class ChartData:
    """Chart data structure."""
    labels: List[str]
    datasets: List[Dict[str, Any]]
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardWidget:
    """Dashboard widget configuration."""
    id: str
    title: str
    type: str  # metric, chart, table, list
    size: str = "medium"  # small, medium, large, full
    chart_type: Optional[ChartType] = None
    data_source: Optional[str] = None
    refresh_interval: int = 60  # seconds
    config: Dict[str, Any] = field(default_factory=dict)


class AnalyticsDashboard:
    """
    Analytics dashboard data provider.

    Provides aggregated data for dashboard visualization.
    """

    def __init__(self):
        # Demo data - in production, this would query the database
        self._cache: Dict[str, Any] = {}

    # =========================================================================
    # Overview Metrics
    # =========================================================================

    async def get_overview_metrics(
        self,
        time_range: TimeRange = TimeRange.LAST_30_DAYS
    ) -> Dict[str, Any]:
        """Get overview metrics for dashboard."""
        date_range = self._get_date_range(time_range)

        return {
            "total_users": await self._get_total_users(date_range),
            "active_users": await self._get_active_users(date_range),
            "new_users": await self._get_new_users(date_range),
            "total_sessions": await self._get_total_sessions(date_range),
            "avg_session_duration": await self._get_avg_session_duration(date_range),
            "total_questions": await self._get_total_questions(date_range),
            "avg_score": await self._get_avg_score(date_range),
            "conversion_rate": await self._get_conversion_rate(date_range),
            "revenue": await self._get_revenue(date_range),
        }

    async def get_metric_with_change(
        self,
        metric_name: str,
        time_range: TimeRange = TimeRange.LAST_30_DAYS
    ) -> Dict[str, Any]:
        """Get metric value with period-over-period change."""
        current_range = self._get_date_range(time_range)
        previous_range = self._get_previous_date_range(time_range)

        current_value = await self._get_metric_value(metric_name, current_range)
        previous_value = await self._get_metric_value(metric_name, previous_range)

        if previous_value > 0:
            change_percent = ((current_value - previous_value) / previous_value) * 100
        else:
            change_percent = 100 if current_value > 0 else 0

        return {
            "value": current_value,
            "previous_value": previous_value,
            "change_percent": round(change_percent, 2),
            "trend": "up" if change_percent > 0 else "down" if change_percent < 0 else "stable",
        }

    # =========================================================================
    # Chart Data
    # =========================================================================

    async def get_users_chart(
        self,
        time_range: TimeRange = TimeRange.LAST_30_DAYS,
        granularity: str = "day"
    ) -> ChartData:
        """Get user growth chart data."""
        date_range = self._get_date_range(time_range)
        labels, new_users, active_users = await self._get_users_time_series(
            date_range, granularity
        )

        return ChartData(
            labels=labels,
            datasets=[
                {
                    "label": "신규 사용자",
                    "data": new_users,
                    "borderColor": "#4CAF50",
                    "backgroundColor": "rgba(76, 175, 80, 0.1)",
                    "fill": True,
                },
                {
                    "label": "활성 사용자",
                    "data": active_users,
                    "borderColor": "#2196F3",
                    "backgroundColor": "rgba(33, 150, 243, 0.1)",
                    "fill": True,
                },
            ],
            options={
                "responsive": True,
                "maintainAspectRatio": False,
            }
        )

    async def get_sessions_chart(
        self,
        time_range: TimeRange = TimeRange.LAST_30_DAYS
    ) -> ChartData:
        """Get sessions chart data."""
        date_range = self._get_date_range(time_range)
        labels, sessions, completions = await self._get_sessions_time_series(date_range)

        return ChartData(
            labels=labels,
            datasets=[
                {
                    "label": "시작된 세션",
                    "data": sessions,
                    "backgroundColor": "#42A5F5",
                },
                {
                    "label": "완료된 세션",
                    "data": completions,
                    "backgroundColor": "#66BB6A",
                },
            ]
        )

    async def get_score_distribution(
        self,
        time_range: TimeRange = TimeRange.LAST_30_DAYS
    ) -> ChartData:
        """Get score distribution chart."""
        date_range = self._get_date_range(time_range)
        distribution = await self._get_score_distribution_data(date_range)

        return ChartData(
            labels=["0-20", "20-40", "40-60", "60-80", "80-100"],
            datasets=[
                {
                    "label": "점수 분포",
                    "data": distribution,
                    "backgroundColor": [
                        "#EF5350",
                        "#FF7043",
                        "#FFCA28",
                        "#66BB6A",
                        "#42A5F5",
                    ],
                }
            ]
        )

    async def get_interview_types_chart(
        self,
        time_range: TimeRange = TimeRange.LAST_30_DAYS
    ) -> ChartData:
        """Get interview types breakdown."""
        date_range = self._get_date_range(time_range)
        types_data = await self._get_interview_types_data(date_range)

        return ChartData(
            labels=list(types_data.keys()),
            datasets=[
                {
                    "data": list(types_data.values()),
                    "backgroundColor": [
                        "#FF6384",
                        "#36A2EB",
                        "#FFCE56",
                        "#4BC0C0",
                        "#9966FF",
                    ],
                }
            ]
        )

    async def get_skill_radar_chart(self, user_id: str) -> ChartData:
        """Get skill radar chart for user."""
        from src.analytics.progress import progress_tracker

        skills = await progress_tracker.get_skill_radar(user_id)

        return ChartData(
            labels=list(skills.keys()),
            datasets=[
                {
                    "label": "현재 수준",
                    "data": list(skills.values()),
                    "backgroundColor": "rgba(54, 162, 235, 0.2)",
                    "borderColor": "rgb(54, 162, 235)",
                    "pointBackgroundColor": "rgb(54, 162, 235)",
                }
            ]
        )

    async def get_retention_heatmap(
        self,
        time_range: TimeRange = TimeRange.LAST_90_DAYS
    ) -> ChartData:
        """Get user retention heatmap data."""
        # Generate cohort retention data
        cohorts = []
        retention_data = []

        for week in range(12):
            cohort_date = datetime.utcnow() - timedelta(weeks=11 - week)
            cohorts.append(cohort_date.strftime("%m/%d"))

            # Simulated retention rates (decreasing over time)
            week_retention = []
            for period in range(min(12 - week, 12)):
                rate = max(0, 100 - (period * 8) - (week * 2))
                week_retention.append(rate)

            retention_data.append(week_retention)

        return ChartData(
            labels=cohorts,
            datasets=[
                {
                    "data": retention_data,
                    "colorScale": {
                        "min": 0,
                        "max": 100,
                        "colors": ["#FEE0D2", "#FC9272", "#DE2D26"],
                    }
                }
            ]
        )

    async def get_funnel_chart(
        self,
        funnel_name: str = "conversion"
    ) -> ChartData:
        """Get funnel chart data."""
        funnel_data = await self._get_funnel_data(funnel_name)

        return ChartData(
            labels=[step["name"] for step in funnel_data],
            datasets=[
                {
                    "data": [step["count"] for step in funnel_data],
                    "backgroundColor": [
                        "#4CAF50",
                        "#8BC34A",
                        "#CDDC39",
                        "#FFC107",
                        "#FF9800",
                    ],
                }
            ]
        )

    # =========================================================================
    # Tables & Lists
    # =========================================================================

    async def get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing users."""
        from src.analytics.progress import progress_tracker

        leaderboard = await progress_tracker.get_leaderboard(limit)
        return leaderboard

    async def get_recent_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent interview sessions."""
        # In production, query database
        return [
            {
                "id": f"session_{i}",
                "user": f"user_{i}",
                "type": "self_introduction",
                "score": 75 + (i % 25),
                "duration": 15 + (i % 10),
                "completed_at": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
            }
            for i in range(limit)
        ]

    async def get_popular_questions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most practiced questions."""
        # In production, query database
        questions = [
            "1분 자기소개 해주세요",
            "왜 승무원이 되고 싶으신가요?",
            "서비스란 무엇이라고 생각하시나요?",
            "팀워크 경험을 말씀해주세요",
            "갈등 상황 해결 경험",
        ]

        return [
            {
                "question": q,
                "practice_count": 1000 - (i * 100),
                "avg_score": 70 + (i * 2),
            }
            for i, q in enumerate(questions[:limit])
        ]

    # =========================================================================
    # Dashboard Configuration
    # =========================================================================

    def get_dashboard_layout(self, dashboard_type: str = "default") -> List[DashboardWidget]:
        """Get dashboard widget layout."""
        layouts = {
            "default": [
                DashboardWidget(
                    id="total_users",
                    title="전체 사용자",
                    type="metric",
                    size="small",
                    data_source="overview_metrics.total_users"
                ),
                DashboardWidget(
                    id="active_users",
                    title="활성 사용자",
                    type="metric",
                    size="small",
                    data_source="overview_metrics.active_users"
                ),
                DashboardWidget(
                    id="avg_score",
                    title="평균 점수",
                    type="metric",
                    size="small",
                    data_source="overview_metrics.avg_score"
                ),
                DashboardWidget(
                    id="revenue",
                    title="매출",
                    type="metric",
                    size="small",
                    data_source="overview_metrics.revenue"
                ),
                DashboardWidget(
                    id="users_chart",
                    title="사용자 추이",
                    type="chart",
                    chart_type=ChartType.LINE,
                    size="large",
                    data_source="users_chart"
                ),
                DashboardWidget(
                    id="sessions_chart",
                    title="세션 현황",
                    type="chart",
                    chart_type=ChartType.BAR,
                    size="medium",
                    data_source="sessions_chart"
                ),
                DashboardWidget(
                    id="score_distribution",
                    title="점수 분포",
                    type="chart",
                    chart_type=ChartType.PIE,
                    size="medium",
                    data_source="score_distribution"
                ),
                DashboardWidget(
                    id="recent_sessions",
                    title="최근 세션",
                    type="table",
                    size="large",
                    data_source="recent_sessions"
                ),
                DashboardWidget(
                    id="top_users",
                    title="상위 사용자",
                    type="list",
                    size="medium",
                    data_source="top_users"
                ),
            ],
            "user": [
                DashboardWidget(
                    id="skill_radar",
                    title="스킬 레이더",
                    type="chart",
                    chart_type=ChartType.RADAR,
                    size="large"
                ),
                DashboardWidget(
                    id="progress_gauge",
                    title="학습 진행률",
                    type="chart",
                    chart_type=ChartType.GAUGE,
                    size="medium"
                ),
            ]
        }

        return layouts.get(dashboard_type, layouts["default"])

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _get_date_range(self, time_range: TimeRange) -> Tuple[datetime, datetime]:
        """Convert time range to date range."""
        now = datetime.utcnow()

        ranges = {
            TimeRange.TODAY: (now.replace(hour=0, minute=0, second=0), now),
            TimeRange.YESTERDAY: (
                (now - timedelta(days=1)).replace(hour=0, minute=0, second=0),
                now.replace(hour=0, minute=0, second=0)
            ),
            TimeRange.LAST_7_DAYS: (now - timedelta(days=7), now),
            TimeRange.LAST_30_DAYS: (now - timedelta(days=30), now),
            TimeRange.LAST_90_DAYS: (now - timedelta(days=90), now),
        }

        return ranges.get(time_range, (now - timedelta(days=30), now))

    def _get_previous_date_range(self, time_range: TimeRange) -> Tuple[datetime, datetime]:
        """Get previous period date range for comparison."""
        start, end = self._get_date_range(time_range)
        duration = end - start
        return (start - duration, start)

    # Data fetching methods (return demo data)
    async def _get_total_users(self, date_range: Tuple) -> int:
        return 1234

    async def _get_active_users(self, date_range: Tuple) -> int:
        return 567

    async def _get_new_users(self, date_range: Tuple) -> int:
        return 89

    async def _get_total_sessions(self, date_range: Tuple) -> int:
        return 3456

    async def _get_avg_session_duration(self, date_range: Tuple) -> float:
        return 18.5

    async def _get_total_questions(self, date_range: Tuple) -> int:
        return 12345

    async def _get_avg_score(self, date_range: Tuple) -> float:
        return 72.5

    async def _get_conversion_rate(self, date_range: Tuple) -> float:
        return 12.5

    async def _get_revenue(self, date_range: Tuple) -> float:
        return 5678900

    async def _get_metric_value(self, metric_name: str, date_range: Tuple) -> float:
        # Map metric names to methods
        return 100

    async def _get_users_time_series(
        self,
        date_range: Tuple,
        granularity: str
    ) -> Tuple[List[str], List[int], List[int]]:
        # Generate demo data
        days = 30
        labels = [(datetime.utcnow() - timedelta(days=i)).strftime("%m/%d") for i in range(days)]
        labels.reverse()
        new_users = [10 + i % 20 for i in range(days)]
        active_users = [50 + i % 30 for i in range(days)]
        return labels, new_users, active_users

    async def _get_sessions_time_series(self, date_range: Tuple) -> Tuple[List, List, List]:
        days = 30
        labels = [(datetime.utcnow() - timedelta(days=i)).strftime("%m/%d") for i in range(days)]
        labels.reverse()
        sessions = [30 + i % 40 for i in range(days)]
        completions = [25 + i % 35 for i in range(days)]
        return labels, sessions, completions

    async def _get_score_distribution_data(self, date_range: Tuple) -> List[int]:
        return [50, 120, 350, 480, 200]

    async def _get_interview_types_data(self, date_range: Tuple) -> Dict[str, int]:
        return {
            "자기소개": 450,
            "지원동기": 320,
            "상황면접": 280,
            "서비스마인드": 200,
            "영어면접": 150,
        }

    async def _get_funnel_data(self, funnel_name: str) -> List[Dict]:
        return [
            {"name": "방문", "count": 10000},
            {"name": "회원가입", "count": 3000},
            {"name": "첫 연습", "count": 1500},
            {"name": "결제", "count": 300},
            {"name": "구독", "count": 150},
        ]


# Singleton instance
analytics_dashboard = AnalyticsDashboard()

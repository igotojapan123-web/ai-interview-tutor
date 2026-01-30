# weekly_report.py
# FlyReady Lab - 주간 자동 리포트 시스템
# 자동 점검, 리포트 생성, 스케줄링

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading
import time

# 로깅 설정
try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# 경로 설정
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = DATA_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 유틸리티
# ============================================================

def load_json(filepath: Path, default: Any = None) -> Any:
    if default is None:
        default = {}
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return default

def save_json(filepath: Path, data: Any) -> bool:
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return True
    except:
        return False

# ============================================================
# 리포트 생성기
# ============================================================

class ReportGenerator:
    """리포트 생성 클래스"""

    def __init__(self):
        self.report_history = load_json(REPORTS_DIR / "history.json", {"reports": []})

    def _save_history(self):
        save_json(REPORTS_DIR / "history.json", self.report_history)

    def generate_daily_report(self, date: str = None) -> Dict:
        """일일 리포트 생성"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        report = {
            "type": "daily",
            "date": date,
            "generated_at": datetime.now().isoformat(),
            "sections": {}
        }

        # 1. 사용자 지표
        report["sections"]["users"] = self._get_user_metrics(days=1)

        # 2. 구독/수익 지표
        report["sections"]["revenue"] = self._get_revenue_metrics(days=1)

        # 3. 사용량 지표
        report["sections"]["usage"] = self._get_usage_metrics(days=1)

        # 4. 에러/시스템 지표
        report["sections"]["system"] = self._get_system_metrics(days=1)

        # 저장
        report_file = REPORTS_DIR / f"daily_{date}.json"
        save_json(report_file, report)

        return report

    def generate_weekly_report(self, end_date: str = None) -> Dict:
        """주간 리포트 생성"""
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        start_dt = end_dt - timedelta(days=7)
        start_date = start_dt.strftime("%Y-%m-%d")

        report = {
            "type": "weekly",
            "period": f"{start_date} ~ {end_date}",
            "start_date": start_date,
            "end_date": end_date,
            "generated_at": datetime.now().isoformat(),
            "sections": {},
            "summary": {},
            "recommendations": []
        }

        # 1. 사용자 지표
        users = self._get_user_metrics(days=7)
        report["sections"]["users"] = users

        # 2. 구독/수익 지표
        revenue = self._get_revenue_metrics(days=7)
        report["sections"]["revenue"] = revenue

        # 3. 사용량 지표
        usage = self._get_usage_metrics(days=7)
        report["sections"]["usage"] = usage

        # 4. 에러/시스템 지표
        system = self._get_system_metrics(days=7)
        report["sections"]["system"] = system

        # 5. 기능별 분석
        report["sections"]["features"] = self._get_feature_analysis(days=7)

        # 6. 트렌드 비교 (전주 대비)
        report["sections"]["trends"] = self._get_trend_comparison()

        # 요약 생성
        report["summary"] = self._generate_summary(report["sections"])

        # 권장 사항 생성
        report["recommendations"] = self._generate_recommendations(report["sections"])

        # 저장
        week_num = end_dt.isocalendar()[1]
        report_file = REPORTS_DIR / f"weekly_{end_dt.year}_W{week_num:02d}.json"
        save_json(report_file, report)

        # 히스토리에 추가
        self.report_history["reports"].append({
            "type": "weekly",
            "file": str(report_file),
            "period": report["period"],
            "generated_at": report["generated_at"]
        })
        self._save_history()

        return report

    def generate_monthly_report(self, year: int = None, month: int = None) -> Dict:
        """월간 리포트 생성"""
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month

        # 해당 월의 시작일과 종료일
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=1)
        days = (end_dt - start_dt).days + 1

        report = {
            "type": "monthly",
            "year": year,
            "month": month,
            "period": f"{year}년 {month}월",
            "days": days,
            "generated_at": datetime.now().isoformat(),
            "sections": {},
            "summary": {},
            "highlights": [],
            "concerns": []
        }

        # 각 섹션 데이터
        report["sections"]["users"] = self._get_user_metrics(days=days)
        report["sections"]["revenue"] = self._get_revenue_metrics(days=days)
        report["sections"]["usage"] = self._get_usage_metrics(days=days)
        report["sections"]["system"] = self._get_system_metrics(days=days)

        # 요약 및 하이라이트
        report["summary"] = self._generate_monthly_summary(report["sections"])
        report["highlights"] = self._get_monthly_highlights(report["sections"])
        report["concerns"] = self._get_monthly_concerns(report["sections"])

        # 저장
        report_file = REPORTS_DIR / f"monthly_{year}_{month:02d}.json"
        save_json(report_file, report)

        return report

    # ============================================================
    # 지표 수집 메서드
    # ============================================================

    def _get_user_metrics(self, days: int = 7) -> Dict:
        """사용자 지표 수집"""
        try:
            from admin_dashboard import UserManager, SubscriptionManager
            user_mgr = UserManager()
            sub_mgr = SubscriptionManager()

            stats = user_mgr.get_user_statistics()

            return {
                "total_users": stats.get("total_users", 0),
                "active_users": stats.get(f"active_users_{days}d", stats.get("active_users_7d", 0)),
                "new_users": stats.get(f"new_users_{days}d", stats.get("new_users_7d", 0)),
                "by_plan": stats.get("by_plan", {}),
                "churn_rate": sub_mgr.get_churn_rate(days),
            }
        except Exception as e:
            logger.error(f"사용자 지표 수집 실패: {e}")
            return {}

    def _get_revenue_metrics(self, days: int = 7) -> Dict:
        """수익 지표 수집"""
        try:
            from admin_dashboard import RevenueManager, SubscriptionManager
            rev_mgr = RevenueManager()
            sub_mgr = SubscriptionManager()

            return {
                "total_revenue": rev_mgr.get_total_revenue(days),
                "mrr": rev_mgr.get_mrr(),
                "active_subscriptions": len(sub_mgr.get_active_subscriptions()),
                "expiring_soon": len(sub_mgr.get_expiring_subscriptions(7)),
                "daily_revenue": rev_mgr.get_daily_revenue(days),
            }
        except Exception as e:
            logger.error(f"수익 지표 수집 실패: {e}")
            return {}

    def _get_usage_metrics(self, days: int = 7) -> Dict:
        """사용량 지표 수집"""
        try:
            from admin_dashboard import UsageStatsManager
            usage_mgr = UsageStatsManager()

            stats = usage_mgr.get_usage_statistics()

            return {
                "dau_today": stats.get("dau_today", 0),
                "dau_trend": stats.get("dau_7d", []),
                "feature_usage": stats.get("feature_usage_7d", {}),
            }
        except Exception as e:
            logger.error(f"사용량 지표 수집 실패: {e}")
            return {}

    def _get_system_metrics(self, days: int = 7) -> Dict:
        """시스템 지표 수집"""
        try:
            from error_monitor import ErrorLogger, APIUsageMonitor, run_health_check
            error_logger = ErrorLogger()
            api_monitor = APIUsageMonitor()

            error_stats = error_logger.get_statistics()
            health = run_health_check()

            return {
                "errors_count": error_stats.get(f"errors_{days}d", error_stats.get("errors_7d", 0)),
                "unresolved_errors": error_stats.get("unresolved", 0),
                "errors_by_type": error_stats.get("by_type", {}),
                "api_usage": api_monitor.get_usage_summary(),
                "health_status": health.get("status", "unknown"),
                "health_checks": health.get("checks", []),
            }
        except Exception as e:
            logger.error(f"시스템 지표 수집 실패: {e}")
            return {}

    def _get_feature_analysis(self, days: int = 7) -> Dict:
        """기능별 분석"""
        try:
            from admin_dashboard import UsageStatsManager
            usage_mgr = UsageStatsManager()

            features = ["모의면접", "자소서첨삭", "퀴즈", "AI코칭", "그룹면접"]
            analysis = {}

            for feature in features:
                usage = usage_mgr.get_feature_usage(feature, days)
                analysis[feature] = {
                    "usage_count": usage,
                    "trend": "stable"  # TODO: 실제 트렌드 계산
                }

            return analysis
        except Exception as e:
            logger.error(f"기능 분석 실패: {e}")
            return {}

    def _get_trend_comparison(self) -> Dict:
        """전주 대비 트렌드"""
        try:
            this_week = self._get_user_metrics(7)
            # 전주 데이터 (간단 버전)
            last_week = self._get_user_metrics(14)

            return {
                "users_change": self._calc_change(
                    this_week.get("new_users", 0),
                    last_week.get("new_users", 0) // 2
                ),
                "note": "전주 대비 변화율"
            }
        except Exception as e:
            return {}

    def _calc_change(self, current: int, previous: int) -> float:
        """변화율 계산"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return ((current - previous) / previous) * 100

    # ============================================================
    # 요약 및 권장사항 생성
    # ============================================================

    def _generate_summary(self, sections: Dict) -> Dict:
        """요약 생성"""
        users = sections.get("users", {})
        revenue = sections.get("revenue", {})
        system = sections.get("system", {})

        return {
            "total_users": users.get("total_users", 0),
            "wau": users.get("active_users", 0),
            "new_users_week": users.get("new_users", 0),
            "churn_rate": users.get("churn_rate", 0),
            "revenue_week": revenue.get("total_revenue", 0),
            "mrr": revenue.get("mrr", 0),
            "errors_week": system.get("errors_count", 0),
            "resolution_rate": self._calc_resolution_rate(system),
        }

    def _calc_resolution_rate(self, system: Dict) -> float:
        """에러 해결률 계산"""
        total = system.get("errors_count", 0)
        unresolved = system.get("unresolved_errors", 0)
        if total == 0:
            return 100.0
        return ((total - unresolved) / total) * 100

    def _generate_recommendations(self, sections: Dict) -> List[str]:
        """권장사항 생성"""
        recommendations = []

        users = sections.get("users", {})
        revenue = sections.get("revenue", {})
        system = sections.get("system", {})

        # 이탈률 체크
        churn = users.get("churn_rate", 0)
        if churn > 10:
            recommendations.append(f"이탈률이 {churn:.1f}%로 높습니다. 사용자 리텐션 개선이 필요합니다.")

        # 에러 체크
        errors = system.get("unresolved_errors", 0)
        if errors > 10:
            recommendations.append(f"미해결 에러가 {errors}건 있습니다. 우선 처리가 필요합니다.")

        # 만료 예정 구독 체크
        expiring = revenue.get("expiring_soon", 0)
        if expiring > 5:
            recommendations.append(f"{expiring}건의 구독이 7일 내 만료 예정입니다. 갱신 알림을 보내세요.")

        if not recommendations:
            recommendations.append("현재 특별한 조치가 필요하지 않습니다.")

        return recommendations

    def _generate_monthly_summary(self, sections: Dict) -> Dict:
        """월간 요약 생성"""
        return self._generate_summary(sections)

    def _get_monthly_highlights(self, sections: Dict) -> List[str]:
        """월간 하이라이트"""
        highlights = []

        users = sections.get("users", {})
        revenue = sections.get("revenue", {})

        new_users = users.get("new_users", 0)
        if new_users > 100:
            highlights.append(f"이번 달 {new_users}명의 신규 사용자가 가입했습니다!")

        total_revenue = revenue.get("total_revenue", 0)
        if total_revenue > 0:
            highlights.append(f"이번 달 총 매출: {total_revenue:,}원")

        return highlights

    def _get_monthly_concerns(self, sections: Dict) -> List[str]:
        """월간 우려사항"""
        return self._generate_recommendations(sections)

    # ============================================================
    # 리포트 조회
    # ============================================================

    def get_recent_reports(self, report_type: str = None, limit: int = 10) -> List[Dict]:
        """최근 리포트 목록"""
        reports = self.report_history.get("reports", [])

        if report_type:
            reports = [r for r in reports if r.get("type") == report_type]

        return reports[-limit:]

    def get_report(self, filepath: str) -> Optional[Dict]:
        """리포트 파일 로드"""
        return load_json(Path(filepath))

# ============================================================
# 자동 점검 스케줄러
# ============================================================

class HealthCheckScheduler:
    """자동 점검 스케줄러"""

    def __init__(self):
        self.running = False
        self.thread = None
        self.check_interval = 3600  # 1시간마다

    def start(self):
        """스케줄러 시작"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info("헬스 체크 스케줄러 시작")

    def stop(self):
        """스케줄러 중지"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("헬스 체크 스케줄러 중지")

    def _run_loop(self):
        """스케줄러 루프"""
        while self.running:
            try:
                self._run_checks()
            except Exception as e:
                logger.error(f"헬스 체크 실패: {e}")

            time.sleep(self.check_interval)

    def _run_checks(self):
        """헬스 체크 실행"""
        try:
            from error_monitor import run_health_check
            from admin_alerts import get_alert_manager

            result = run_health_check()

            # 문제 발견 시 알림
            if result.get("status") != "healthy":
                failed_checks = [
                    c["name"] for c in result.get("checks", [])
                    if c.get("status") != "pass"
                ]

                if failed_checks:
                    alert_mgr = get_alert_manager()
                    alert_mgr.send_system_alert(
                        "시스템 상태 이상 감지",
                        f"실패한 체크: {', '.join(failed_checks)}",
                        is_critical=(result.get("status") == "unhealthy")
                    )
        except Exception as e:
            logger.error(f"헬스 체크 실행 실패: {e}")

# ============================================================
# 주간 리포트 스케줄러
# ============================================================

class WeeklyReportScheduler:
    """주간 리포트 스케줄러"""

    def __init__(self):
        self.running = False
        self.thread = None
        self.check_interval = 3600  # 1시간마다 체크

    def start(self):
        """스케줄러 시작"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info("주간 리포트 스케줄러 시작")

    def stop(self):
        """스케줄러 중지"""
        self.running = False

    def _run_loop(self):
        """스케줄러 루프"""
        while self.running:
            try:
                self._check_and_generate()
            except Exception as e:
                logger.error(f"주간 리포트 생성 실패: {e}")

            time.sleep(self.check_interval)

    def _check_and_generate(self):
        """주간 리포트 생성 체크 및 실행"""
        now = datetime.now()

        # 매주 월요일 오전 9시에 생성
        if now.weekday() == 0 and now.hour == 9:
            self._generate_and_send()

    def _generate_and_send(self):
        """리포트 생성 및 전송"""
        try:
            generator = ReportGenerator()
            report = generator.generate_weekly_report()

            # 알림 전송
            from admin_alerts import get_alert_manager
            alert_mgr = get_alert_manager()
            alert_mgr.send_weekly_report(report.get("summary", {}))

            logger.info("주간 리포트 생성 및 전송 완료")
        except Exception as e:
            logger.error(f"주간 리포트 생성/전송 실패: {e}")

# ============================================================
# 수동 점검 함수
# ============================================================

def run_full_check() -> Dict:
    """전체 시스템 점검 실행"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }

    # 1. 헬스 체크
    try:
        from error_monitor import run_health_check
        results["checks"]["health"] = run_health_check()
    except Exception as e:
        results["checks"]["health"] = {"status": "error", "error": str(e)}

    # 2. 에러 통계
    try:
        from error_monitor import get_error_stats
        results["checks"]["errors"] = get_error_stats()
    except Exception as e:
        results["checks"]["errors"] = {"error": str(e)}

    # 3. API 사용량
    try:
        from error_monitor import get_api_monitor
        api_monitor = get_api_monitor()
        results["checks"]["api_usage"] = api_monitor.get_usage_summary()
    except Exception as e:
        results["checks"]["api_usage"] = {"error": str(e)}

    # 4. 사용자/구독 상태
    try:
        from admin_dashboard import get_dashboard_summary
        results["checks"]["dashboard"] = get_dashboard_summary()
    except Exception as e:
        results["checks"]["dashboard"] = {"error": str(e)}

    # 전체 상태 결정
    all_healthy = True
    for check_name, check_result in results["checks"].items():
        if isinstance(check_result, dict):
            if check_result.get("status") not in ["healthy", "pass", None]:
                all_healthy = False
            if check_result.get("error"):
                all_healthy = False

    results["overall_status"] = "healthy" if all_healthy else "issues_detected"

    return results

def generate_quick_report() -> str:
    """빠른 상태 리포트 생성 (텍스트)"""
    check_results = run_full_check()

    report_lines = [
        "=" * 50,
        "FlyReady Lab 시스템 상태 리포트",
        f"생성 시간: {check_results['timestamp']}",
        "=" * 50,
        "",
    ]

    # 전체 상태
    status = check_results.get("overall_status", "unknown")
    status_icon = "OK" if status == "healthy" else "WARN"
    report_lines.append(f"[{status_icon}] 전체 상태: {status}")
    report_lines.append("")

    # 헬스 체크
    health = check_results.get("checks", {}).get("health", {})
    report_lines.append(f"[HEALTH] 시스템 헬스: {health.get('status', 'unknown')}")

    # 에러 통계
    errors = check_results.get("checks", {}).get("errors", {})
    report_lines.append(f"[ERRORS] 24시간 에러: {errors.get('errors_24h', 'N/A')}건")
    report_lines.append(f"[ERRORS] 미해결: {errors.get('unresolved', 'N/A')}건")

    # API 사용량
    api = check_results.get("checks", {}).get("api_usage", {})
    for api_name, usage in api.items():
        if isinstance(usage, dict):
            pct = usage.get("percentage", 0)
            report_lines.append(f"[API] {api_name}: {pct:.1f}% 사용")

    # 대시보드 요약
    dashboard = check_results.get("checks", {}).get("dashboard", {})
    users = dashboard.get("users", {})
    revenue = dashboard.get("revenue", {})

    report_lines.append("")
    report_lines.append(f"[USERS] 총 사용자: {users.get('total_users', 'N/A')}")
    report_lines.append(f"[USERS] 7일 활성: {users.get('active_users_7d', 'N/A')}")
    report_lines.append(f"[REVENUE] MRR: {revenue.get('mrr', 0):,}원")

    report_lines.append("")
    report_lines.append("=" * 50)

    return "\n".join(report_lines)

# ============================================================
# 전역 스케줄러 인스턴스
# ============================================================

_health_scheduler = None
_weekly_scheduler = None

def start_schedulers():
    """모든 스케줄러 시작"""
    global _health_scheduler, _weekly_scheduler

    if _health_scheduler is None:
        _health_scheduler = HealthCheckScheduler()
        _health_scheduler.start()

    if _weekly_scheduler is None:
        _weekly_scheduler = WeeklyReportScheduler()
        _weekly_scheduler.start()

def stop_schedulers():
    """모든 스케줄러 중지"""
    global _health_scheduler, _weekly_scheduler

    if _health_scheduler:
        _health_scheduler.stop()
    if _weekly_scheduler:
        _weekly_scheduler.stop()

# ============================================================
# CLI 인터페이스
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "check":
            print(generate_quick_report())

        elif command == "daily":
            generator = ReportGenerator()
            report = generator.generate_daily_report()
            print(f"일일 리포트 생성 완료: {report['date']}")

        elif command == "weekly":
            generator = ReportGenerator()
            report = generator.generate_weekly_report()
            print(f"주간 리포트 생성 완료: {report['period']}")

        elif command == "monthly":
            generator = ReportGenerator()
            report = generator.generate_monthly_report()
            print(f"월간 리포트 생성 완료: {report['period']}")

        else:
            print(f"알 수 없는 명령: {command}")
            print("사용법: python weekly_report.py [check|daily|weekly|monthly]")
    else:
        print("FlyReady Lab 리포트 시스템")
        print("사용법: python weekly_report.py [check|daily|weekly|monthly]")

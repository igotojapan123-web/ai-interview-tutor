# error_monitor.py
# FlyReady Lab - 에러 모니터링 시스템
# Sentry 연동, 실시간 알림, 에러 집계

import os
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from collections import defaultdict
from functools import wraps
import threading
import hashlib

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
ERROR_DIR = DATA_DIR / "errors"
ERROR_DIR.mkdir(parents=True, exist_ok=True)

# 파일 경로
ERROR_LOG_FILE = ERROR_DIR / "error_log.json"
ERROR_STATS_FILE = ERROR_DIR / "error_stats.json"
ALERT_HISTORY_FILE = ERROR_DIR / "alert_history.json"

# ============================================================
# Sentry 연동
# ============================================================

SENTRY_AVAILABLE = False
SENTRY_DSN = os.getenv("SENTRY_DSN", "")

try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration

    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            environment=os.getenv("ENVIRONMENT", "production"),
            integrations=[
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                )
            ],
        )
        SENTRY_AVAILABLE = True
        logger.info("Sentry 연동 완료")
except ImportError:
    logger.info("Sentry SDK 미설치 - 로컬 에러 로깅만 사용")
except Exception as e:
    logger.warning(f"Sentry 초기화 실패: {e}")

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
# 에러 심각도 레벨
# ============================================================

class ErrorLevel:
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    @staticmethod
    def get_priority(level: str) -> int:
        priorities = {
            "debug": 0,
            "info": 1,
            "warning": 2,
            "error": 3,
            "critical": 4
        }
        return priorities.get(level, 0)

# ============================================================
# 에러 로거
# ============================================================

class ErrorLogger:
    """에러 로깅 클래스"""

    def __init__(self):
        self.errors = load_json(ERROR_LOG_FILE, {"errors": []})
        self.stats = load_json(ERROR_STATS_FILE, {
            "total": 0,
            "by_level": {},
            "by_type": {},
            "by_page": {}
        })

    def _save(self):
        save_json(ERROR_LOG_FILE, self.errors)
        save_json(ERROR_STATS_FILE, self.stats)

    def log_error(self, error: Exception, context: Dict = None,
                  level: str = ErrorLevel.ERROR, page: str = "",
                  user_id: str = "") -> str:
        """에러 로깅"""
        error_id = hashlib.md5(
            f"{type(error).__name__}{str(error)}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        error_entry = {
            "id": error_id,
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "page": page,
            "user_id": user_id,
            "context": context or {},
            "resolved": False,
        }

        # 에러 로그에 추가
        if "errors" not in self.errors:
            self.errors["errors"] = []
        self.errors["errors"].append(error_entry)

        # 최대 5000개 유지
        if len(self.errors["errors"]) > 5000:
            self.errors["errors"] = self.errors["errors"][-5000:]

        # 통계 업데이트
        self._update_stats(error_entry)

        # Sentry에 전송
        if SENTRY_AVAILABLE and level in [ErrorLevel.ERROR, ErrorLevel.CRITICAL]:
            try:
                sentry_sdk.capture_exception(error)
            except:
                pass

        self._save()

        # 심각한 에러는 즉시 알림
        if level == ErrorLevel.CRITICAL:
            self._send_critical_alert(error_entry)

        return error_id

    def _update_stats(self, error_entry: Dict):
        """통계 업데이트"""
        self.stats["total"] = self.stats.get("total", 0) + 1

        level = error_entry.get("level", "error")
        if "by_level" not in self.stats:
            self.stats["by_level"] = {}
        self.stats["by_level"][level] = self.stats["by_level"].get(level, 0) + 1

        error_type = error_entry.get("type", "Unknown")
        if "by_type" not in self.stats:
            self.stats["by_type"] = {}
        self.stats["by_type"][error_type] = self.stats["by_type"].get(error_type, 0) + 1

        page = error_entry.get("page", "unknown")
        if page:
            if "by_page" not in self.stats:
                self.stats["by_page"] = {}
            self.stats["by_page"][page] = self.stats["by_page"].get(page, 0) + 1

    def _send_critical_alert(self, error_entry: Dict):
        """심각한 에러 즉시 알림"""
        try:
            from admin_alerts import AlertManager
            alert_mgr = AlertManager()
            alert_mgr.send_error_alert(error_entry)
        except Exception as e:
            logger.error(f"알림 전송 실패: {e}")

    def get_errors(self, days: int = 7, level: str = None,
                   resolved: bool = None) -> List[Dict]:
        """에러 목록 조회"""
        cutoff = datetime.now() - timedelta(days=days)
        filtered = []

        for error in self.errors.get("errors", []):
            timestamp = error.get("timestamp")
            if timestamp:
                try:
                    error_dt = datetime.fromisoformat(timestamp)
                    if error_dt < cutoff:
                        continue
                except:
                    continue

            if level and error.get("level") != level:
                continue
            if resolved is not None and error.get("resolved") != resolved:
                continue

            filtered.append(error)

        return filtered

    def resolve_error(self, error_id: str, resolution: str = "") -> bool:
        """에러 해결 표시"""
        for i, error in enumerate(self.errors.get("errors", [])):
            if error.get("id") == error_id:
                self.errors["errors"][i]["resolved"] = True
                self.errors["errors"][i]["resolved_at"] = datetime.now().isoformat()
                self.errors["errors"][i]["resolution"] = resolution
                self._save()
                return True
        return False

    def get_statistics(self) -> Dict:
        """에러 통계"""
        errors_7d = self.get_errors(days=7)
        errors_24h = self.get_errors(days=1)

        # 최근 에러 트렌드
        trend = defaultdict(int)
        for error in errors_7d:
            date = error.get("timestamp", "")[:10]
            trend[date] += 1

        return {
            "total": self.stats.get("total", 0),
            "errors_24h": len(errors_24h),
            "errors_7d": len(errors_7d),
            "unresolved": len([e for e in errors_7d if not e.get("resolved")]),
            "by_level": self.stats.get("by_level", {}),
            "by_type": self.stats.get("by_type", {}),
            "by_page": self.stats.get("by_page", {}),
            "trend_7d": dict(trend),
        }

# ============================================================
# 에러 핸들러 데코레이터
# ============================================================

def monitor_errors(page: str = "", level: str = ErrorLevel.ERROR):
    """에러 모니터링 데코레이터"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_logger = ErrorLogger()
                error_logger.log_error(
                    error=e,
                    context={
                        "function": func.__name__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    },
                    level=level,
                    page=page
                )
                raise
        return wrapper
    return decorator

def safe_execute(func: Callable, *args, default=None, page: str = "", **kwargs):
    """안전한 함수 실행 (에러 시 기본값 반환)"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_logger = ErrorLogger()
        error_logger.log_error(
            error=e,
            context={
                "function": func.__name__,
                "args": str(args)[:200],
            },
            level=ErrorLevel.WARNING,
            page=page
        )
        return default

# ============================================================
# 시스템 상태 모니터
# ============================================================

class SystemMonitor:
    """시스템 상태 모니터링"""

    def __init__(self):
        self.checks = []

    def add_check(self, name: str, check_func: Callable) -> None:
        """상태 체크 추가"""
        self.checks.append({"name": name, "func": check_func})

    def run_checks(self) -> Dict:
        """모든 상태 체크 실행"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "checks": []
        }

        for check in self.checks:
            try:
                result = check["func"]()
                check_result = {
                    "name": check["name"],
                    "status": "pass" if result else "fail",
                    "result": result
                }
            except Exception as e:
                check_result = {
                    "name": check["name"],
                    "status": "error",
                    "error": str(e)
                }
                results["status"] = "unhealthy"

            results["checks"].append(check_result)

            if check_result["status"] != "pass":
                results["status"] = "degraded" if results["status"] == "healthy" else results["status"]

        return results

# 기본 시스템 체크
def create_default_monitor() -> SystemMonitor:
    """기본 시스템 모니터 생성"""
    monitor = SystemMonitor()

    # 데이터 디렉토리 체크
    def check_data_dir():
        return DATA_DIR.exists() and DATA_DIR.is_dir()
    monitor.add_check("data_directory", check_data_dir)

    # 로그 파일 체크
    def check_log_files():
        return ERROR_LOG_FILE.parent.exists()
    monitor.add_check("log_directory", check_log_files)

    # OpenAI API 체크
    def check_openai():
        api_key = os.getenv("OPENAI_API_KEY", "")
        return bool(api_key and len(api_key) > 20)
    monitor.add_check("openai_api_key", check_openai)

    return monitor

# ============================================================
# 에러 집계 및 분석
# ============================================================

class ErrorAnalyzer:
    """에러 패턴 분석"""

    def __init__(self):
        self.error_logger = ErrorLogger()

    def get_top_errors(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """가장 많이 발생한 에러 Top N"""
        errors = self.error_logger.get_errors(days=days)

        # 에러 타입별 그룹화
        error_counts = defaultdict(lambda: {"count": 0, "latest": None, "messages": []})

        for error in errors:
            error_type = error.get("type", "Unknown")
            error_counts[error_type]["count"] += 1
            error_counts[error_type]["latest"] = error.get("timestamp")
            if len(error_counts[error_type]["messages"]) < 3:
                error_counts[error_type]["messages"].append(error.get("message", ""))

        # 정렬 및 상위 N개 반환
        sorted_errors = sorted(
            error_counts.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:limit]

        return [
            {"type": k, **v}
            for k, v in sorted_errors
        ]

    def get_error_hotspots(self, days: int = 7) -> List[Dict]:
        """에러가 많이 발생하는 페이지"""
        errors = self.error_logger.get_errors(days=days)

        page_counts = defaultdict(int)
        for error in errors:
            page = error.get("page", "unknown")
            if page:
                page_counts[page] += 1

        sorted_pages = sorted(
            page_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return [{"page": k, "count": v} for k, v in sorted_pages]

    def detect_spike(self, threshold: float = 2.0) -> Optional[Dict]:
        """에러 급증 감지"""
        errors_1h = len(self.error_logger.get_errors(days=1/24))  # 최근 1시간

        # 이전 24시간 평균
        errors_24h = len(self.error_logger.get_errors(days=1))
        avg_hourly = errors_24h / 24

        if avg_hourly > 0 and errors_1h > avg_hourly * threshold:
            return {
                "detected": True,
                "current_rate": errors_1h,
                "average_rate": avg_hourly,
                "spike_factor": errors_1h / avg_hourly
            }

        return None

# ============================================================
# API 사용량 모니터
# ============================================================

class APIUsageMonitor:
    """API 사용량 모니터링"""

    API_LIMITS = {
        "openai": {"daily": 10000, "warning_threshold": 0.8},
        "d-id": {"daily": 100, "warning_threshold": 0.7},
        "clova": {"daily": 5000, "warning_threshold": 0.8},
    }

    def __init__(self):
        self.usage_file = ERROR_DIR / "api_usage.json"
        self.usage = load_json(self.usage_file, {"daily": {}})

    def _save(self):
        save_json(self.usage_file, self.usage)

    def record_api_call(self, api_name: str, tokens: int = 1) -> None:
        """API 호출 기록"""
        today = datetime.now().strftime("%Y-%m-%d")

        if "daily" not in self.usage:
            self.usage["daily"] = {}
        if today not in self.usage["daily"]:
            self.usage["daily"][today] = {}
        if api_name not in self.usage["daily"][today]:
            self.usage["daily"][today][api_name] = 0

        self.usage["daily"][today][api_name] += tokens
        self._save()

        # 임계치 체크
        self._check_threshold(api_name, today)

    def _check_threshold(self, api_name: str, date: str):
        """사용량 임계치 체크"""
        limit_info = self.API_LIMITS.get(api_name)
        if not limit_info:
            return

        current = self.usage["daily"].get(date, {}).get(api_name, 0)
        threshold = limit_info["daily"] * limit_info["warning_threshold"]

        if current >= threshold:
            try:
                from admin_alerts import AlertManager
                alert_mgr = AlertManager()
                alert_mgr.send_usage_alert(api_name, current, limit_info["daily"])
            except:
                logger.warning(f"API 사용량 경고: {api_name} - {current}/{limit_info['daily']}")

    def get_usage(self, api_name: str = None, days: int = 7) -> Dict:
        """API 사용량 조회"""
        result = {}

        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_usage = self.usage.get("daily", {}).get(date, {})

            if api_name:
                result[date] = day_usage.get(api_name, 0)
            else:
                result[date] = day_usage

        return result

    def get_usage_summary(self) -> Dict:
        """사용량 요약"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_usage = self.usage.get("daily", {}).get(today, {})

        summary = {}
        for api_name, limit_info in self.API_LIMITS.items():
            current = today_usage.get(api_name, 0)
            limit = limit_info["daily"]
            summary[api_name] = {
                "current": current,
                "limit": limit,
                "percentage": (current / limit * 100) if limit > 0 else 0,
                "remaining": limit - current
            }

        return summary

# ============================================================
# 전역 인스턴스
# ============================================================

_error_logger = None
_system_monitor = None
_api_monitor = None

def get_error_logger() -> ErrorLogger:
    global _error_logger
    if _error_logger is None:
        _error_logger = ErrorLogger()
    return _error_logger

def get_system_monitor() -> SystemMonitor:
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = create_default_monitor()
    return _system_monitor

def get_api_monitor() -> APIUsageMonitor:
    global _api_monitor
    if _api_monitor is None:
        _api_monitor = APIUsageMonitor()
    return _api_monitor

# ============================================================
# 간편 함수
# ============================================================

def log_error(error: Exception, **kwargs) -> str:
    """에러 로깅 간편 함수"""
    return get_error_logger().log_error(error, **kwargs)

def get_error_stats() -> Dict:
    """에러 통계 간편 함수"""
    return get_error_logger().get_statistics()

def run_health_check() -> Dict:
    """헬스 체크 간편 함수"""
    return get_system_monitor().run_checks()

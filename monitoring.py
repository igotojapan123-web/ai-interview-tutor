# monitoring.py
# 에러 추적 및 모니터링 시스템

import os
import json
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from logging_config import get_logger

logger = get_logger(__name__)

# ========================================
# 모니터링 설정
# ========================================

MONITORING_DIR = os.path.join(os.path.dirname(__file__), "logs", "monitoring")
ERROR_LOG_FILE = os.path.join(MONITORING_DIR, "errors.json")
METRICS_LOG_FILE = os.path.join(MONITORING_DIR, "metrics.json")

# Sentry DSN (설정 시 활성화)
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")


# ========================================
# 에러 추적
# ========================================

def init_monitoring():
    """모니터링 시스템 초기화"""
    os.makedirs(MONITORING_DIR, exist_ok=True)

    # Sentry 초기화 (DSN이 설정된 경우)
    if SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=SENTRY_DSN,
                traces_sample_rate=0.1,  # 10% 샘플링
                profiles_sample_rate=0.1,
            )
            logger.info("Sentry 모니터링 활성화됨")
        except ImportError:
            logger.warning("sentry-sdk 패키지가 설치되지 않음")
        except Exception as e:
            logger.error(f"Sentry 초기화 실패: {e}")


def track_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    page: Optional[str] = None
):
    """에러 추적 및 로깅"""
    error_data = {
        "timestamp": datetime.now().isoformat(),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "context": context or {},
        "user_id": user_id,
        "page": page,
    }

    # 파일에 기록
    try:
        errors = []
        if os.path.exists(ERROR_LOG_FILE):
            with open(ERROR_LOG_FILE, "r", encoding="utf-8") as f:
                errors = json.load(f)

        errors.append(error_data)

        # 최근 1000개만 유지
        if len(errors) > 1000:
            errors = errors[-1000:]

        with open(ERROR_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(errors, f, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"에러 로깅 실패: {e}")

    # Sentry에 전송
    if SENTRY_DSN:
        try:
            import sentry_sdk
            with sentry_sdk.push_scope() as scope:
                if user_id:
                    scope.set_user({"id": user_id})
                if page:
                    scope.set_tag("page", page)
                if context:
                    for key, value in context.items():
                        scope.set_extra(key, value)
                sentry_sdk.capture_exception(error)
        except:
            pass

    # 로컬 로깅
    logger.error(f"[{page or 'unknown'}] {type(error).__name__}: {error}")


# ========================================
# 메트릭 수집
# ========================================

def track_metric(
    name: str,
    value: float,
    tags: Optional[Dict[str, str]] = None
):
    """메트릭 수집"""
    metric_data = {
        "timestamp": datetime.now().isoformat(),
        "name": name,
        "value": value,
        "tags": tags or {},
    }

    try:
        metrics = []
        if os.path.exists(METRICS_LOG_FILE):
            with open(METRICS_LOG_FILE, "r", encoding="utf-8") as f:
                metrics = json.load(f)

        metrics.append(metric_data)

        # 최근 10000개만 유지
        if len(metrics) > 10000:
            metrics = metrics[-10000:]

        with open(METRICS_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"메트릭 저장 실패: {e}")


def track_page_view(page: str, user_id: Optional[str] = None):
    """페이지 조회 추적"""
    track_metric("page_view", 1, {"page": page, "user_id": user_id or "anonymous"})


def track_feature_usage(feature: str, user_id: Optional[str] = None):
    """기능 사용 추적"""
    track_metric("feature_usage", 1, {"feature": feature, "user_id": user_id or "anonymous"})


def track_api_latency(api_name: str, latency_ms: float):
    """API 응답 시간 추적"""
    track_metric("api_latency", latency_ms, {"api": api_name})


def track_api_error(api_name: str, error_type: str):
    """API 에러 추적"""
    track_metric("api_error", 1, {"api": api_name, "error_type": error_type})


# ========================================
# 대시보드용 데이터 조회
# ========================================

def get_error_summary(days: int = 7) -> Dict[str, Any]:
    """에러 요약 조회"""
    from datetime import timedelta

    try:
        if not os.path.exists(ERROR_LOG_FILE):
            return {"total": 0, "by_type": {}, "by_page": {}}

        with open(ERROR_LOG_FILE, "r", encoding="utf-8") as f:
            errors = json.load(f)

        cutoff = datetime.now() - timedelta(days=days)
        recent_errors = [
            e for e in errors
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]

        by_type = {}
        by_page = {}

        for error in recent_errors:
            error_type = error.get("error_type", "Unknown")
            page = error.get("page", "Unknown")

            by_type[error_type] = by_type.get(error_type, 0) + 1
            by_page[page] = by_page.get(page, 0) + 1

        return {
            "total": len(recent_errors),
            "by_type": by_type,
            "by_page": by_page,
        }

    except Exception as e:
        logger.error(f"에러 요약 조회 실패: {e}")
        return {"total": 0, "by_type": {}, "by_page": {}}


def get_metrics_summary(metric_name: str, days: int = 7) -> Dict[str, Any]:
    """메트릭 요약 조회"""
    from datetime import timedelta

    try:
        if not os.path.exists(METRICS_LOG_FILE):
            return {"count": 0, "sum": 0, "avg": 0}

        with open(METRICS_LOG_FILE, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        cutoff = datetime.now() - timedelta(days=days)
        filtered = [
            m for m in metrics
            if m.get("name") == metric_name
            and datetime.fromisoformat(m["timestamp"]) > cutoff
        ]

        if not filtered:
            return {"count": 0, "sum": 0, "avg": 0}

        values = [m["value"] for m in filtered]
        return {
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values),
        }

    except Exception as e:
        logger.error(f"메트릭 요약 조회 실패: {e}")
        return {"count": 0, "sum": 0, "avg": 0}


# ========================================
# 상태 체크
# ========================================

def health_check() -> Dict[str, Any]:
    """시스템 상태 체크"""
    from env_config import check_openai_key, GOOGLE_TTS_API_KEY

    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }

    # OpenAI API 체크
    is_valid, msg = check_openai_key()
    status["checks"]["openai_api"] = {
        "status": "ok" if is_valid else "error",
        "message": msg
    }

    # Google TTS 체크
    status["checks"]["google_tts"] = {
        "status": "ok" if GOOGLE_TTS_API_KEY else "warning",
        "message": "설정됨" if GOOGLE_TTS_API_KEY else "미설정"
    }

    # 디스크 공간 체크 (로그 디렉토리)
    try:
        import shutil
        total, used, free = shutil.disk_usage(MONITORING_DIR)
        free_gb = free / (1024 ** 3)
        status["checks"]["disk_space"] = {
            "status": "ok" if free_gb > 1 else "warning",
            "message": f"{free_gb:.1f}GB 남음"
        }
    except:
        status["checks"]["disk_space"] = {"status": "unknown", "message": "확인 불가"}

    # 전체 상태 판단
    if any(c["status"] == "error" for c in status["checks"].values()):
        status["status"] = "unhealthy"
    elif any(c["status"] == "warning" for c in status["checks"].values()):
        status["status"] = "degraded"

    return status

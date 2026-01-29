# health_check.py
# FlyReady Lab - Enterprise Health Check System
# Stage 4: 대기업 수준 시스템 상태 모니터링
# Samsung-level quality implementation

import os
import sys
import time
import json
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from logging_config import get_logger

logger = get_logger(__name__)

# =============================================================================
# 상태 정의
# =============================================================================

class HealthStatus(Enum):
    """시스템 상태"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CheckType(Enum):
    """체크 유형"""
    API = "api"
    DATABASE = "database"
    DISK = "disk"
    MEMORY = "memory"
    CPU = "cpu"
    EXTERNAL_SERVICE = "external_service"
    CUSTOM = "custom"


# =============================================================================
# 체크 결과 데이터 구조
# =============================================================================

@dataclass
class HealthCheckResult:
    """헬스 체크 결과"""
    name: str
    check_type: CheckType
    status: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "check_type": self.check_type.value,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": round(self.duration_ms, 2),
            "details": self.details
        }


@dataclass
class SystemHealth:
    """전체 시스템 상태"""
    status: HealthStatus
    checks: List[HealthCheckResult]
    timestamp: datetime = field(default_factory=datetime.now)
    uptime_seconds: float = 0
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "uptime_seconds": int(self.uptime_seconds),
            "uptime_formatted": str(timedelta(seconds=int(self.uptime_seconds))),
            "version": self.version,
            "checks": [c.to_dict() for c in self.checks],
            "summary": {
                "total": len(self.checks),
                "healthy": len([c for c in self.checks if c.status == HealthStatus.HEALTHY]),
                "degraded": len([c for c in self.checks if c.status == HealthStatus.DEGRADED]),
                "unhealthy": len([c for c in self.checks if c.status == HealthStatus.UNHEALTHY])
            }
        }


# =============================================================================
# 헬스 체크 시스템
# =============================================================================

class HealthCheckSystem:
    """시스템 상태 체크 시스템"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._start_time = datetime.now()
        self._custom_checks: Dict[str, Callable[[], HealthCheckResult]] = {}
        self._last_results: List[HealthCheckResult] = []
        self._check_history: List[SystemHealth] = []

        logger.info("HealthCheckSystem initialized")

    def register_check(self, name: str, check_func: Callable[[], HealthCheckResult]):
        """커스텀 체크 등록"""
        self._custom_checks[name] = check_func

    def unregister_check(self, name: str):
        """커스텀 체크 해제"""
        if name in self._custom_checks:
            del self._custom_checks[name]

    # -------------------------------------------------------------------------
    # 개별 체크
    # -------------------------------------------------------------------------

    def check_openai_api(self) -> HealthCheckResult:
        """OpenAI API 상태 체크"""
        start = time.time()
        try:
            from env_config import check_openai_key
            is_valid, message = check_openai_key()

            return HealthCheckResult(
                name="OpenAI API",
                check_type=CheckType.API,
                status=HealthStatus.HEALTHY if is_valid else HealthStatus.UNHEALTHY,
                message=message,
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return HealthCheckResult(
                name="OpenAI API",
                check_type=CheckType.API,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                duration_ms=(time.time() - start) * 1000
            )

    def check_google_tts(self) -> HealthCheckResult:
        """Google TTS API 상태 체크"""
        start = time.time()
        try:
            from env_config import GOOGLE_TTS_API_KEY

            if GOOGLE_TTS_API_KEY:
                status = HealthStatus.HEALTHY
                message = "API 키 설정됨"
            else:
                status = HealthStatus.DEGRADED
                message = "API 키 미설정 (음성 기능 제한)"

            return HealthCheckResult(
                name="Google TTS",
                check_type=CheckType.EXTERNAL_SERVICE,
                status=status,
                message=message,
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return HealthCheckResult(
                name="Google TTS",
                check_type=CheckType.EXTERNAL_SERVICE,
                status=HealthStatus.UNKNOWN,
                message=str(e),
                duration_ms=(time.time() - start) * 1000
            )

    def check_disk_space(self) -> HealthCheckResult:
        """디스크 공간 체크"""
        start = time.time()
        try:
            import shutil
            project_root = Path(__file__).parent
            total, used, free = shutil.disk_usage(str(project_root))

            free_gb = free / (1024 ** 3)
            used_percent = (used / total) * 100

            if free_gb > 5:
                status = HealthStatus.HEALTHY
                message = f"{free_gb:.1f}GB 사용 가능"
            elif free_gb > 1:
                status = HealthStatus.DEGRADED
                message = f"{free_gb:.1f}GB 사용 가능 (공간 부족 주의)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"{free_gb:.1f}GB 사용 가능 (긴급 정리 필요)"

            return HealthCheckResult(
                name="Disk Space",
                check_type=CheckType.DISK,
                status=status,
                message=message,
                duration_ms=(time.time() - start) * 1000,
                details={
                    "total_gb": round(total / (1024 ** 3), 2),
                    "used_gb": round(used / (1024 ** 3), 2),
                    "free_gb": round(free_gb, 2),
                    "used_percent": round(used_percent, 2)
                }
            )
        except Exception as e:
            return HealthCheckResult(
                name="Disk Space",
                check_type=CheckType.DISK,
                status=HealthStatus.UNKNOWN,
                message=str(e),
                duration_ms=(time.time() - start) * 1000
            )

    def check_memory(self) -> HealthCheckResult:
        """메모리 사용량 체크"""
        start = time.time()
        try:
            memory = psutil.virtual_memory()
            used_percent = memory.percent

            if used_percent < 70:
                status = HealthStatus.HEALTHY
                message = f"메모리 사용률 {used_percent:.1f}%"
            elif used_percent < 85:
                status = HealthStatus.DEGRADED
                message = f"메모리 사용률 {used_percent:.1f}% (주의)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"메모리 사용률 {used_percent:.1f}% (위험)"

            return HealthCheckResult(
                name="Memory",
                check_type=CheckType.MEMORY,
                status=status,
                message=message,
                duration_ms=(time.time() - start) * 1000,
                details={
                    "total_gb": round(memory.total / (1024 ** 3), 2),
                    "available_gb": round(memory.available / (1024 ** 3), 2),
                    "used_percent": round(used_percent, 2)
                }
            )
        except Exception as e:
            return HealthCheckResult(
                name="Memory",
                check_type=CheckType.MEMORY,
                status=HealthStatus.UNKNOWN,
                message=str(e),
                duration_ms=(time.time() - start) * 1000
            )

    def check_cpu(self) -> HealthCheckResult:
        """CPU 사용량 체크"""
        start = time.time()
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)

            if cpu_percent < 70:
                status = HealthStatus.HEALTHY
                message = f"CPU 사용률 {cpu_percent:.1f}%"
            elif cpu_percent < 90:
                status = HealthStatus.DEGRADED
                message = f"CPU 사용률 {cpu_percent:.1f}% (높음)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"CPU 사용률 {cpu_percent:.1f}% (과부하)"

            return HealthCheckResult(
                name="CPU",
                check_type=CheckType.CPU,
                status=status,
                message=message,
                duration_ms=(time.time() - start) * 1000,
                details={
                    "cpu_percent": round(cpu_percent, 2),
                    "cpu_count": psutil.cpu_count()
                }
            )
        except Exception as e:
            return HealthCheckResult(
                name="CPU",
                check_type=CheckType.CPU,
                status=HealthStatus.UNKNOWN,
                message=str(e),
                duration_ms=(time.time() - start) * 1000
            )

    def check_log_directory(self) -> HealthCheckResult:
        """로그 디렉토리 체크"""
        start = time.time()
        try:
            log_dir = Path(__file__).parent / "logs"

            if not log_dir.exists():
                log_dir.mkdir(parents=True, exist_ok=True)

            # 로그 파일 수와 크기 계산
            log_files = list(log_dir.rglob("*"))
            file_count = len([f for f in log_files if f.is_file()])
            total_size = sum(f.stat().st_size for f in log_files if f.is_file())
            total_size_mb = total_size / (1024 * 1024)

            if total_size_mb < 100:
                status = HealthStatus.HEALTHY
                message = f"로그 {file_count}개 ({total_size_mb:.1f}MB)"
            elif total_size_mb < 500:
                status = HealthStatus.DEGRADED
                message = f"로그 {file_count}개 ({total_size_mb:.1f}MB) - 정리 권장"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"로그 {file_count}개 ({total_size_mb:.1f}MB) - 정리 필요"

            return HealthCheckResult(
                name="Log Directory",
                check_type=CheckType.DISK,
                status=status,
                message=message,
                duration_ms=(time.time() - start) * 1000,
                details={
                    "file_count": file_count,
                    "total_size_mb": round(total_size_mb, 2),
                    "path": str(log_dir)
                }
            )
        except Exception as e:
            return HealthCheckResult(
                name="Log Directory",
                check_type=CheckType.DISK,
                status=HealthStatus.UNKNOWN,
                message=str(e),
                duration_ms=(time.time() - start) * 1000
            )

    def check_python_version(self) -> HealthCheckResult:
        """Python 버전 체크"""
        start = time.time()
        version = sys.version_info

        if version.major >= 3 and version.minor >= 9:
            status = HealthStatus.HEALTHY
            message = f"Python {version.major}.{version.minor}.{version.micro}"
        elif version.major >= 3 and version.minor >= 8:
            status = HealthStatus.DEGRADED
            message = f"Python {version.major}.{version.minor}.{version.micro} (업그레이드 권장)"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"Python {version.major}.{version.minor}.{version.micro} (지원 버전 아님)"

        return HealthCheckResult(
            name="Python Version",
            check_type=CheckType.CUSTOM,
            status=status,
            message=message,
            duration_ms=(time.time() - start) * 1000,
            details={
                "major": version.major,
                "minor": version.minor,
                "micro": version.micro
            }
        )

    def check_required_packages(self) -> HealthCheckResult:
        """필수 패키지 설치 체크"""
        start = time.time()
        required = ["streamlit", "openai", "requests", "pydantic"]
        missing = []
        installed = []

        for pkg in required:
            try:
                __import__(pkg)
                installed.append(pkg)
            except ImportError:
                missing.append(pkg)

        if not missing:
            status = HealthStatus.HEALTHY
            message = f"필수 패키지 {len(installed)}개 설치됨"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"미설치 패키지: {', '.join(missing)}"

        return HealthCheckResult(
            name="Required Packages",
            check_type=CheckType.CUSTOM,
            status=status,
            message=message,
            duration_ms=(time.time() - start) * 1000,
            details={
                "installed": installed,
                "missing": missing
            }
        )

    # -------------------------------------------------------------------------
    # 전체 체크
    # -------------------------------------------------------------------------

    def run_all_checks(self) -> SystemHealth:
        """모든 체크 실행"""
        checks = []

        # 기본 체크 실행
        checks.append(self.check_openai_api())
        checks.append(self.check_google_tts())
        checks.append(self.check_disk_space())
        checks.append(self.check_memory())
        checks.append(self.check_cpu())
        checks.append(self.check_log_directory())
        checks.append(self.check_python_version())
        checks.append(self.check_required_packages())

        # 커스텀 체크 실행
        for name, check_func in self._custom_checks.items():
            try:
                result = check_func()
                checks.append(result)
            except Exception as e:
                checks.append(HealthCheckResult(
                    name=name,
                    check_type=CheckType.CUSTOM,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e)
                ))

        # 전체 상태 판단
        if any(c.status == HealthStatus.UNHEALTHY for c in checks):
            overall_status = HealthStatus.UNHEALTHY
        elif any(c.status == HealthStatus.DEGRADED for c in checks):
            overall_status = HealthStatus.DEGRADED
        elif any(c.status == HealthStatus.UNKNOWN for c in checks):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        uptime = (datetime.now() - self._start_time).total_seconds()

        health = SystemHealth(
            status=overall_status,
            checks=checks,
            uptime_seconds=uptime,
            version=self._get_app_version()
        )

        # 결과 저장
        self._last_results = checks
        self._check_history.append(health)
        if len(self._check_history) > 100:
            self._check_history = self._check_history[-100:]

        return health

    def get_last_results(self) -> List[HealthCheckResult]:
        """마지막 체크 결과"""
        return self._last_results

    def get_check_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """체크 히스토리"""
        return [h.to_dict() for h in self._check_history[-limit:]]

    def _get_app_version(self) -> str:
        """앱 버전 가져오기"""
        try:
            from constants import APP_VERSION
            return APP_VERSION
        except (ImportError, AttributeError):
            return "1.0.0"


# =============================================================================
# 전역 인스턴스
# =============================================================================

_health_check = HealthCheckSystem()


def get_health_check() -> HealthCheckSystem:
    """헬스 체크 시스템 인스턴스 반환"""
    return _health_check


# =============================================================================
# 편의 함수
# =============================================================================

def run_health_check() -> Dict[str, Any]:
    """헬스 체크 실행"""
    return _health_check.run_all_checks().to_dict()


def get_quick_status() -> Dict[str, Any]:
    """빠른 상태 확인 (API, 디스크, 메모리만)"""
    checks = [
        _health_check.check_openai_api(),
        _health_check.check_disk_space(),
        _health_check.check_memory()
    ]

    if any(c.status == HealthStatus.UNHEALTHY for c in checks):
        status = "unhealthy"
    elif any(c.status == HealthStatus.DEGRADED for c in checks):
        status = "degraded"
    else:
        status = "healthy"

    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "checks": [c.to_dict() for c in checks]
    }


def is_healthy() -> bool:
    """시스템이 정상인지 확인"""
    result = _health_check.run_all_checks()
    return result.status == HealthStatus.HEALTHY


def register_custom_check(name: str, check_func: Callable[[], HealthCheckResult]):
    """커스텀 체크 등록"""
    _health_check.register_check(name, check_func)

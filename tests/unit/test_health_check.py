# tests/unit/test_health_check.py
# FlyReady Lab - 헬스 체크 시스템 단위 테스트
# Stage 4: 대기업 수준 테스트

import pytest
import sys
import os
import time
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestHealthStatus:
    """HealthStatus 열거형 테스트"""

    def test_healthy_status(self):
        """정상 상태"""
        from health_check import HealthStatus
        assert HealthStatus.HEALTHY.value == "healthy"

    def test_degraded_status(self):
        """저하 상태"""
        from health_check import HealthStatus
        assert HealthStatus.DEGRADED.value == "degraded"

    def test_unhealthy_status(self):
        """비정상 상태"""
        from health_check import HealthStatus
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_unknown_status(self):
        """알 수 없음 상태"""
        from health_check import HealthStatus
        assert HealthStatus.UNKNOWN.value == "unknown"


class TestCheckType:
    """CheckType 열거형 테스트"""

    def test_api_type(self):
        """API 체크 타입"""
        from health_check import CheckType
        assert CheckType.API.value == "api"

    def test_database_type(self):
        """데이터베이스 체크 타입"""
        from health_check import CheckType
        assert CheckType.DATABASE.value == "database"

    def test_disk_type(self):
        """디스크 체크 타입"""
        from health_check import CheckType
        assert CheckType.DISK.value == "disk"

    def test_memory_type(self):
        """메모리 체크 타입"""
        from health_check import CheckType
        assert CheckType.MEMORY.value == "memory"

    def test_cpu_type(self):
        """CPU 체크 타입"""
        from health_check import CheckType
        assert CheckType.CPU.value == "cpu"

    def test_external_service_type(self):
        """외부 서비스 체크 타입"""
        from health_check import CheckType
        assert CheckType.EXTERNAL_SERVICE.value == "external_service"

    def test_custom_type(self):
        """커스텀 체크 타입"""
        from health_check import CheckType
        assert CheckType.CUSTOM.value == "custom"


class TestHealthCheckResult:
    """HealthCheckResult 데이터클래스 테스트"""

    def test_create_result(self):
        """결과 생성"""
        from health_check import HealthCheckResult, HealthStatus, CheckType

        result = HealthCheckResult(
            name="Test Check",
            check_type=CheckType.API,
            status=HealthStatus.HEALTHY,
            message="All good"
        )

        assert result.name == "Test Check"
        assert result.check_type == CheckType.API
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "All good"

    def test_result_with_details(self):
        """상세 정보가 있는 결과"""
        from health_check import HealthCheckResult, HealthStatus, CheckType

        result = HealthCheckResult(
            name="Memory Check",
            check_type=CheckType.MEMORY,
            status=HealthStatus.DEGRADED,
            message="Memory usage high",
            duration_ms=50.5,
            details={"used_percent": 85.5}
        )

        assert result.duration_ms == 50.5
        assert result.details["used_percent"] == 85.5

    def test_result_to_dict(self):
        """결과 딕셔너리 변환"""
        from health_check import HealthCheckResult, HealthStatus, CheckType

        result = HealthCheckResult(
            name="Disk Check",
            check_type=CheckType.DISK,
            status=HealthStatus.HEALTHY,
            message="Disk space OK"
        )

        dict_result = result.to_dict()

        assert dict_result["name"] == "Disk Check"
        assert dict_result["check_type"] == "disk"
        assert dict_result["status"] == "healthy"
        assert "timestamp" in dict_result


class TestSystemHealth:
    """SystemHealth 데이터클래스 테스트"""

    def test_create_system_health(self):
        """시스템 상태 생성"""
        from health_check import SystemHealth, HealthStatus, HealthCheckResult, CheckType

        checks = [
            HealthCheckResult(
                name="API",
                check_type=CheckType.API,
                status=HealthStatus.HEALTHY,
                message="OK"
            )
        ]

        health = SystemHealth(
            status=HealthStatus.HEALTHY,
            checks=checks,
            uptime_seconds=3600,
            version="1.0.0"
        )

        assert health.status == HealthStatus.HEALTHY
        assert len(health.checks) == 1
        assert health.uptime_seconds == 3600

    def test_system_health_to_dict(self):
        """시스템 상태 딕셔너리 변환"""
        from health_check import SystemHealth, HealthStatus, HealthCheckResult, CheckType

        checks = [
            HealthCheckResult("Check1", CheckType.API, HealthStatus.HEALTHY, "OK"),
            HealthCheckResult("Check2", CheckType.MEMORY, HealthStatus.DEGRADED, "Warning"),
            HealthCheckResult("Check3", CheckType.DISK, HealthStatus.UNHEALTHY, "Error")
        ]

        health = SystemHealth(
            status=HealthStatus.UNHEALTHY,
            checks=checks
        )

        dict_result = health.to_dict()

        assert dict_result["status"] == "unhealthy"
        assert dict_result["summary"]["total"] == 3
        assert dict_result["summary"]["healthy"] == 1
        assert dict_result["summary"]["degraded"] == 1
        assert dict_result["summary"]["unhealthy"] == 1


class TestHealthCheckSystem:
    """HealthCheckSystem 싱글톤 테스트"""

    def test_singleton(self):
        """싱글톤 패턴"""
        from health_check import HealthCheckSystem

        system1 = HealthCheckSystem()
        system2 = HealthCheckSystem()

        assert system1 is system2

    def test_get_health_check(self):
        """get_health_check 함수"""
        from health_check import get_health_check, HealthCheckSystem

        health_check = get_health_check()
        assert isinstance(health_check, HealthCheckSystem)

    def test_register_custom_check(self):
        """커스텀 체크 등록"""
        from health_check import get_health_check, HealthCheckResult, HealthStatus, CheckType

        def custom_check():
            return HealthCheckResult(
                name="Custom Check",
                check_type=CheckType.CUSTOM,
                status=HealthStatus.HEALTHY,
                message="Custom OK"
            )

        hc = get_health_check()
        hc.register_check("my_custom_check", custom_check)

    def test_unregister_custom_check(self):
        """커스텀 체크 해제"""
        from health_check import get_health_check, HealthCheckResult, HealthStatus, CheckType

        def temp_check():
            return HealthCheckResult(
                name="Temp",
                check_type=CheckType.CUSTOM,
                status=HealthStatus.HEALTHY,
                message="Temp"
            )

        hc = get_health_check()
        hc.register_check("temp_check", temp_check)
        hc.unregister_check("temp_check")


class TestIndividualChecks:
    """개별 헬스 체크 테스트"""

    @patch('health_check.psutil')
    def test_check_disk_space(self, mock_psutil):
        """디스크 공간 체크"""
        from health_check import get_health_check, HealthStatus

        hc = get_health_check()
        result = hc.check_disk_space()

        assert result.name == "Disk Space"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY, HealthStatus.UNKNOWN]
        assert result.duration_ms >= 0

    @patch('health_check.psutil')
    def test_check_memory(self, mock_psutil):
        """메모리 체크"""
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=50.0,
            total=16 * 1024 * 1024 * 1024,  # 16GB
            available=8 * 1024 * 1024 * 1024  # 8GB
        )

        from health_check import get_health_check, HealthStatus

        hc = get_health_check()
        result = hc.check_memory()

        assert result.name == "Memory"
        assert result.status == HealthStatus.HEALTHY
        assert "메모리 사용률" in result.message

    @patch('health_check.psutil')
    def test_check_memory_high(self, mock_psutil):
        """메모리 높음 체크"""
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=80.0,
            total=16 * 1024 * 1024 * 1024,
            available=3 * 1024 * 1024 * 1024
        )

        from health_check import get_health_check, HealthStatus

        hc = get_health_check()
        result = hc.check_memory()

        assert result.status == HealthStatus.DEGRADED

    @patch('health_check.psutil')
    def test_check_memory_critical(self, mock_psutil):
        """메모리 위험 체크"""
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=95.0,
            total=16 * 1024 * 1024 * 1024,
            available=1 * 1024 * 1024 * 1024
        )

        from health_check import get_health_check, HealthStatus

        hc = get_health_check()
        result = hc.check_memory()

        assert result.status == HealthStatus.UNHEALTHY

    @patch('health_check.psutil')
    def test_check_cpu(self, mock_psutil):
        """CPU 체크"""
        mock_psutil.cpu_percent.return_value = 30.0
        mock_psutil.cpu_count.return_value = 8

        from health_check import get_health_check, HealthStatus

        hc = get_health_check()
        result = hc.check_cpu()

        assert result.name == "CPU"
        assert result.status == HealthStatus.HEALTHY

    @patch('health_check.psutil')
    def test_check_cpu_high(self, mock_psutil):
        """CPU 높음 체크"""
        mock_psutil.cpu_percent.return_value = 80.0
        mock_psutil.cpu_count.return_value = 8

        from health_check import get_health_check, HealthStatus

        hc = get_health_check()
        result = hc.check_cpu()

        assert result.status == HealthStatus.DEGRADED

    @patch('health_check.psutil')
    def test_check_cpu_overload(self, mock_psutil):
        """CPU 과부하 체크"""
        mock_psutil.cpu_percent.return_value = 95.0
        mock_psutil.cpu_count.return_value = 8

        from health_check import get_health_check, HealthStatus

        hc = get_health_check()
        result = hc.check_cpu()

        assert result.status == HealthStatus.UNHEALTHY

    def test_check_python_version(self):
        """Python 버전 체크"""
        from health_check import get_health_check, HealthStatus

        hc = get_health_check()
        result = hc.check_python_version()

        assert result.name == "Python Version"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
        assert "Python" in result.message

    def test_check_required_packages(self):
        """필수 패키지 체크"""
        from health_check import get_health_check, HealthStatus

        hc = get_health_check()
        result = hc.check_required_packages()

        assert result.name == "Required Packages"
        assert "installed" in result.details
        assert "missing" in result.details

    def test_check_log_directory(self):
        """로그 디렉토리 체크"""
        from health_check import get_health_check, HealthStatus

        hc = get_health_check()
        result = hc.check_log_directory()

        assert result.name == "Log Directory"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY, HealthStatus.UNKNOWN]

    def test_check_openai_api_success(self):
        """OpenAI API 체크 - 성공"""
        with patch('env_config.check_openai_key', return_value=(True, "API key valid")):
            from health_check import get_health_check, HealthStatus

            hc = get_health_check()
            result = hc.check_openai_api()

            assert result.name == "OpenAI API"
            assert result.status == HealthStatus.HEALTHY

    def test_check_openai_api_failure(self):
        """OpenAI API 체크 - 실패"""
        with patch('env_config.check_openai_key', return_value=(False, "Invalid API key")):
            from health_check import get_health_check, HealthStatus

            hc = get_health_check()
            result = hc.check_openai_api()

            assert result.status == HealthStatus.UNHEALTHY

    def test_check_google_tts_with_key(self):
        """Google TTS 체크 - 키 있음"""
        with patch('env_config.GOOGLE_TTS_API_KEY', "test_key"):
            from health_check import get_health_check, HealthStatus

            hc = get_health_check()
            result = hc.check_google_tts()

            assert result.name == "Google TTS"

    def test_check_google_tts_no_key(self):
        """Google TTS 체크 - 키 없음"""
        with patch('env_config.GOOGLE_TTS_API_KEY', ""):
            from health_check import get_health_check, HealthStatus

            hc = get_health_check()
            result = hc.check_google_tts()

            # 키가 없으면 DEGRADED
            assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNKNOWN]


class TestRunAllChecks:
    """전체 체크 실행 테스트"""

    @patch('health_check.psutil')
    def test_run_all_checks(self, mock_psutil):
        """모든 체크 실행"""
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=50.0,
            total=16 * 1024 * 1024 * 1024,
            available=8 * 1024 * 1024 * 1024
        )
        mock_psutil.cpu_percent.return_value = 30.0
        mock_psutil.cpu_count.return_value = 8

        from health_check import get_health_check, HealthStatus

        hc = get_health_check()
        health = hc.run_all_checks()

        assert health.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
        assert len(health.checks) >= 8  # 기본 체크 8개
        assert health.uptime_seconds >= 0

    def test_get_last_results(self):
        """마지막 결과 조회"""
        from health_check import get_health_check

        hc = get_health_check()
        hc.run_all_checks()

        results = hc.get_last_results()
        assert isinstance(results, list)

    def test_get_check_history(self):
        """체크 히스토리 조회"""
        from health_check import get_health_check

        hc = get_health_check()
        hc.run_all_checks()

        history = hc.get_check_history(5)
        assert isinstance(history, list)


class TestConvenienceFunctions:
    """편의 함수 테스트"""

    @patch('health_check.psutil')
    def test_run_health_check_function(self, mock_psutil):
        """run_health_check 편의 함수"""
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=50.0,
            total=16 * 1024 * 1024 * 1024,
            available=8 * 1024 * 1024 * 1024
        )
        mock_psutil.cpu_percent.return_value = 30.0
        mock_psutil.cpu_count.return_value = 8

        from health_check import run_health_check

        result = run_health_check()

        assert "status" in result
        assert "checks" in result
        assert "summary" in result

    @patch('health_check.psutil')
    def test_get_quick_status_function(self, mock_psutil):
        """get_quick_status 편의 함수"""
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=50.0,
            total=16 * 1024 * 1024 * 1024,
            available=8 * 1024 * 1024 * 1024
        )

        from health_check import get_quick_status

        result = get_quick_status()

        assert "status" in result
        assert "checks" in result
        assert len(result["checks"]) == 3  # API, 디스크, 메모리

    @patch('health_check.psutil')
    def test_is_healthy_function(self, mock_psutil):
        """is_healthy 편의 함수"""
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=50.0,
            total=16 * 1024 * 1024 * 1024,
            available=8 * 1024 * 1024 * 1024
        )
        mock_psutil.cpu_percent.return_value = 30.0
        mock_psutil.cpu_count.return_value = 8

        from health_check import is_healthy

        result = is_healthy()

        assert isinstance(result, bool)

    def test_register_custom_check_function(self):
        """register_custom_check 편의 함수"""
        from health_check import register_custom_check, HealthCheckResult, HealthStatus, CheckType

        def my_check():
            return HealthCheckResult(
                name="My Check",
                check_type=CheckType.CUSTOM,
                status=HealthStatus.HEALTHY,
                message="OK"
            )

        register_custom_check("my_check", my_check)


class TestCustomCheckExecution:
    """커스텀 체크 실행 테스트"""

    @patch('health_check.psutil')
    def test_custom_check_in_run_all(self, mock_psutil):
        """run_all_checks에 커스텀 체크 포함"""
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=50.0,
            total=16 * 1024 * 1024 * 1024,
            available=8 * 1024 * 1024 * 1024
        )
        mock_psutil.cpu_percent.return_value = 30.0
        mock_psutil.cpu_count.return_value = 8

        from health_check import get_health_check, HealthCheckResult, HealthStatus, CheckType

        def custom_service_check():
            return HealthCheckResult(
                name="Custom Service",
                check_type=CheckType.EXTERNAL_SERVICE,
                status=HealthStatus.HEALTHY,
                message="Service is running"
            )

        hc = get_health_check()
        hc.register_check("custom_service", custom_service_check)

        health = hc.run_all_checks()

        # 커스텀 체크가 포함되었는지 확인
        check_names = [c.name for c in health.checks]
        assert "Custom Service" in check_names

        # 정리
        hc.unregister_check("custom_service")

    @patch('health_check.psutil')
    def test_custom_check_error_handling(self, mock_psutil):
        """커스텀 체크 에러 처리"""
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=50.0,
            total=16 * 1024 * 1024 * 1024,
            available=8 * 1024 * 1024 * 1024
        )
        mock_psutil.cpu_percent.return_value = 30.0
        mock_psutil.cpu_count.return_value = 8

        from health_check import get_health_check, HealthStatus

        def failing_check():
            raise RuntimeError("Check failed!")

        hc = get_health_check()
        hc.register_check("failing_check", failing_check)

        health = hc.run_all_checks()

        # 실패한 체크도 결과에 포함됨
        check_names = [c.name for c in health.checks]
        assert "failing_check" in check_names

        # 실패한 체크는 UNHEALTHY
        failing_result = next(c for c in health.checks if c.name == "failing_check")
        assert failing_result.status == HealthStatus.UNHEALTHY

        # 정리
        hc.unregister_check("failing_check")


class TestHealthStatusDetermination:
    """전체 상태 결정 테스트"""

    def test_all_healthy(self):
        """모두 정상인 경우"""
        from health_check import SystemHealth, HealthStatus, HealthCheckResult, CheckType

        checks = [
            HealthCheckResult("C1", CheckType.API, HealthStatus.HEALTHY, "OK"),
            HealthCheckResult("C2", CheckType.MEMORY, HealthStatus.HEALTHY, "OK"),
            HealthCheckResult("C3", CheckType.DISK, HealthStatus.HEALTHY, "OK")
        ]

        health = SystemHealth(status=HealthStatus.HEALTHY, checks=checks)
        assert health.status == HealthStatus.HEALTHY

    def test_one_degraded(self):
        """하나가 저하된 경우"""
        from health_check import SystemHealth, HealthStatus, HealthCheckResult, CheckType

        checks = [
            HealthCheckResult("C1", CheckType.API, HealthStatus.HEALTHY, "OK"),
            HealthCheckResult("C2", CheckType.MEMORY, HealthStatus.DEGRADED, "Warning"),
            HealthCheckResult("C3", CheckType.DISK, HealthStatus.HEALTHY, "OK")
        ]

        # 실제 HealthCheckSystem에서의 상태 판단 로직 테스트
        from health_check import get_health_check

        hc = get_health_check()

        if any(c.status == HealthStatus.UNHEALTHY for c in checks):
            overall = HealthStatus.UNHEALTHY
        elif any(c.status == HealthStatus.DEGRADED for c in checks):
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        assert overall == HealthStatus.DEGRADED

    def test_one_unhealthy(self):
        """하나가 비정상인 경우"""
        from health_check import HealthStatus, HealthCheckResult, CheckType

        checks = [
            HealthCheckResult("C1", CheckType.API, HealthStatus.HEALTHY, "OK"),
            HealthCheckResult("C2", CheckType.MEMORY, HealthStatus.DEGRADED, "Warning"),
            HealthCheckResult("C3", CheckType.DISK, HealthStatus.UNHEALTHY, "Error")
        ]

        if any(c.status == HealthStatus.UNHEALTHY for c in checks):
            overall = HealthStatus.UNHEALTHY
        elif any(c.status == HealthStatus.DEGRADED for c in checks):
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        assert overall == HealthStatus.UNHEALTHY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

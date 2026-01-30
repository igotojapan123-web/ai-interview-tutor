# api_versioning.py
# API 버전 관리 시스템

from datetime import datetime
from typing import Dict, Any, List, Callable, Optional
from functools import wraps

try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# ============================================================
# 설정
# ============================================================

CURRENT_API_VERSION = "v2"
SUPPORTED_VERSIONS = ["v1", "v2"]
DEFAULT_VERSION = "v2"
DEPRECATED_VERSIONS = ["v1"]


# ============================================================
# API 버전 관리자
# ============================================================

class APIVersionManager:
    """API 버전 관리"""

    def __init__(self):
        self._handlers: Dict[str, Dict[str, Callable]] = {}  # {endpoint: {version: handler}}
        self._deprecation_notices: Dict[str, str] = {}

    def register(self, endpoint: str, version: str) -> Callable:
        """API 핸들러 등록 데코레이터"""
        def decorator(func: Callable) -> Callable:
            if endpoint not in self._handlers:
                self._handlers[endpoint] = {}
            self._handlers[endpoint][version] = func
            logger.debug(f"API 등록: {endpoint} ({version})")
            return func
        return decorator

    def get_handler(self, endpoint: str, version: str) -> Optional[Callable]:
        """버전별 핸들러 조회"""
        handlers = self._handlers.get(endpoint, {})

        # 요청 버전 핸들러
        if version in handlers:
            return handlers[version]

        # 기본 버전 폴백
        if DEFAULT_VERSION in handlers:
            return handlers[DEFAULT_VERSION]

        return None

    def call(self, endpoint: str, version: str, *args, **kwargs) -> Any:
        """버전별 API 호출"""
        handler = self.get_handler(endpoint, version)

        if not handler:
            raise APIVersionError(f"지원하지 않는 API: {endpoint} ({version})")

        # Deprecation 경고
        if version in DEPRECATED_VERSIONS:
            logger.warning(f"Deprecated API 호출: {endpoint} ({version})")

        return handler(*args, **kwargs)

    def set_deprecation_notice(self, version: str, notice: str) -> None:
        """Deprecation 공지 설정"""
        self._deprecation_notices[version] = notice

    def get_deprecation_notice(self, version: str) -> Optional[str]:
        """Deprecation 공지 조회"""
        return self._deprecation_notices.get(version)

    def get_supported_versions(self) -> List[str]:
        """지원 버전 목록"""
        return SUPPORTED_VERSIONS.copy()

    def is_supported(self, version: str) -> bool:
        """버전 지원 여부"""
        return version in SUPPORTED_VERSIONS

    def is_deprecated(self, version: str) -> bool:
        """Deprecation 여부"""
        return version in DEPRECATED_VERSIONS


class APIVersionError(Exception):
    """API 버전 오류"""
    pass


# 전역 인스턴스
api_manager = APIVersionManager()


# ============================================================
# 데코레이터
# ============================================================

def versioned_api(endpoint: str):
    """
    버전별 API 데코레이터

    Usage:
        @versioned_api("get_questions")
        def get_questions_v2(airline, count):
            return new_implementation()

        @api_manager.register("get_questions", "v1")
        def get_questions_v1(airline, count):
            return old_implementation()
    """
    def decorator(func: Callable) -> Callable:
        # 현재 버전으로 등록
        api_manager._handlers.setdefault(endpoint, {})[CURRENT_API_VERSION] = func

        @wraps(func)
        def wrapper(*args, version: str = DEFAULT_VERSION, **kwargs):
            return api_manager.call(endpoint, version, *args, **kwargs)

        return wrapper
    return decorator


def deprecated_api(version: str, sunset_date: str = None):
    """
    Deprecated API 표시 데코레이터
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            notice = f"이 API는 deprecated됩니다."
            if sunset_date:
                notice += f" 종료 예정: {sunset_date}"
            logger.warning(f"Deprecated API 호출: {func.__name__} - {notice}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================
# 버전 정보
# ============================================================

def get_api_info() -> Dict[str, Any]:
    """API 정보"""
    return {
        "current_version": CURRENT_API_VERSION,
        "supported_versions": SUPPORTED_VERSIONS,
        "deprecated_versions": DEPRECATED_VERSIONS,
        "default_version": DEFAULT_VERSION
    }


def get_version_headers(version: str) -> Dict[str, str]:
    """응답 헤더 (버전 정보)"""
    headers = {
        "X-API-Version": version,
        "X-API-Supported-Versions": ",".join(SUPPORTED_VERSIONS)
    }

    if api_manager.is_deprecated(version):
        headers["X-API-Deprecated"] = "true"
        notice = api_manager.get_deprecation_notice(version)
        if notice:
            headers["X-API-Deprecation-Notice"] = notice

    return headers


# ============================================================
# 예시 API 등록
# ============================================================

@api_manager.register("generate_questions", "v1")
def generate_questions_v1(airline: str, count: int = 5) -> Dict[str, Any]:
    """v1: 기본 질문 생성"""
    return {
        "version": "v1",
        "airline": airline,
        "questions": [f"질문 {i+1}" for i in range(count)]
    }


@api_manager.register("generate_questions", "v2")
def generate_questions_v2(airline: str, count: int = 5, difficulty: str = "medium") -> Dict[str, Any]:
    """v2: 난이도 추가"""
    return {
        "version": "v2",
        "airline": airline,
        "difficulty": difficulty,
        "questions": [f"{difficulty} 질문 {i+1}" for i in range(count)]
    }


@api_manager.register("evaluate_answer", "v1")
def evaluate_answer_v1(answer: str) -> Dict[str, Any]:
    """v1: 기본 평가"""
    return {
        "version": "v1",
        "score": 75,
        "feedback": "기본 피드백"
    }


@api_manager.register("evaluate_answer", "v2")
def evaluate_answer_v2(answer: str, criteria: List[str] = None) -> Dict[str, Any]:
    """v2: 상세 평가"""
    return {
        "version": "v2",
        "score": 85,
        "criteria_scores": {c: 80 for c in (criteria or ["내용", "전달력"])},
        "feedback": "상세 피드백",
        "suggestions": ["개선점 1", "개선점 2"]
    }


# Deprecation 공지
api_manager.set_deprecation_notice("v1", "v1은 2024년 12월 종료 예정입니다. v2로 마이그레이션하세요.")


# ============================================================
# 간편 함수
# ============================================================

def call_api(endpoint: str, version: str = DEFAULT_VERSION, **kwargs) -> Any:
    """API 호출"""
    return api_manager.call(endpoint, version, **kwargs)


def is_version_supported(version: str) -> bool:
    """버전 지원 여부"""
    return api_manager.is_supported(version)


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=== API Versioning ===")

    # API 정보
    print("\nAPI 정보:")
    import json
    print(json.dumps(get_api_info(), indent=2))

    # v1 호출
    print("\nv1 API 호출:")
    result_v1 = call_api("generate_questions", "v1", airline="korean_air", count=3)
    print(json.dumps(result_v1, indent=2, ensure_ascii=False))

    # v2 호출
    print("\nv2 API 호출:")
    result_v2 = call_api("generate_questions", "v2", airline="korean_air", count=3, difficulty="hard")
    print(json.dumps(result_v2, indent=2, ensure_ascii=False))

    # 헤더
    print("\n응답 헤더 (v1):")
    print(get_version_headers("v1"))

    print("\nReady!")

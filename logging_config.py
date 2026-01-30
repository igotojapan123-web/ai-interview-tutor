# logging_config.py
# 중앙 집중식 로깅 설정

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# 로그 디렉토리
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 로그 포맷
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """앱 전체 로깅 설정

    Args:
        level: 로깅 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 이름 (없으면 날짜 기반 자동 생성)
        console: 콘솔 출력 여부

    Returns:
        루트 로거
    """
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 기존 핸들러 제거
    root_logger.handlers.clear()

    # 포매터
    formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)

    # 콘솔 핸들러
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # 파일 핸들러
    if log_file is None:
        log_file = f"app_{datetime.now().strftime('%Y%m%d')}.log"

    file_path = LOG_DIR / log_file
    file_handler = logging.FileHandler(file_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """모듈별 로거 가져오기

    Args:
        name: 모듈 이름 (일반적으로 __name__ 사용)

    Returns:
        해당 모듈의 로거
    """
    return logging.getLogger(name)


# 앱 에러 클래스
class AppError(Exception):
    """앱 기본 에러"""
    def __init__(self, message: str, error_code: str = "UNKNOWN", **kwargs):
        self.message = message
        self.error_code = error_code
        self.details = kwargs
        logger = get_logger(__name__)
        logger.error(f"[{error_code}] {message}", extra=kwargs)
        super().__init__(self.message)


class APIError(AppError):
    """API 호출 에러"""
    def __init__(self, message: str, api_name: str = "", **kwargs):
        super().__init__(message, error_code=f"API_{api_name.upper()}", **kwargs)


class ValidationError(AppError):
    """입력 검증 에러"""
    def __init__(self, message: str, field: str = "", **kwargs):
        super().__init__(message, error_code="VALIDATION", field=field, **kwargs)


class ConfigError(AppError):
    """설정 에러"""
    def __init__(self, message: str, config_key: str = "", **kwargs):
        super().__init__(message, error_code="CONFIG", config_key=config_key, **kwargs)


# ============================================================
# 로깅 유틸리티 함수 (강화)
# ============================================================

def log_api_call(api_name: str, success: bool, duration_ms: float = None, error: str = None):
    """
    API 호출 결과 로깅

    Args:
        api_name: API 이름 (예: 'OpenAI', 'Whisper')
        success: 성공 여부
        duration_ms: 응답 시간 (밀리초)
        error: 에러 메시지 (실패 시)
    """
    logger = get_logger("api")
    duration_str = f" ({duration_ms:.0f}ms)" if duration_ms else ""

    if success:
        logger.info(f"[API] {api_name} 호출 성공{duration_str}")
    else:
        logger.error(f"[API] {api_name} 호출 실패{duration_str}: {error or 'Unknown error'}")


def log_page_access(page_name: str, user_id: str = None):
    """
    페이지 접근 로깅

    Args:
        page_name: 페이지 이름
        user_id: 사용자 ID (선택)
    """
    logger = get_logger("access")
    user_str = f" (user: {user_id})" if user_id else ""
    logger.info(f"[PAGE] {page_name} 접근{user_str}")


def log_user_action(action: str, page: str = None, details: dict = None):
    """
    사용자 액션 로깅

    Args:
        action: 액션 이름 (예: 'start_interview', 'submit_answer')
        page: 페이지 이름
        details: 추가 정보
    """
    logger = get_logger("action")
    page_str = f" [{page}]" if page else ""
    details_str = f" - {details}" if details else ""
    logger.info(f"[ACTION]{page_str} {action}{details_str}")


def log_error_with_context(error: Exception, context: dict = None, page: str = None):
    """
    컨텍스트와 함께 에러 로깅

    Args:
        error: 발생한 예외
        context: 추가 컨텍스트 정보
        page: 페이지 이름
    """
    logger = get_logger("error")
    page_str = f"[{page}] " if page else ""
    context_str = f" | Context: {context}" if context else ""

    logger.error(f"{page_str}{type(error).__name__}: {str(error)}{context_str}")

    # 스택 트레이스도 기록 (DEBUG 레벨)
    import traceback
    logger.debug(f"Stack trace: {traceback.format_exc()}")


def log_performance(operation: str, duration_ms: float, threshold_ms: float = 1000):
    """
    성능 로깅 (느린 작업 감지)

    Args:
        operation: 작업 이름
        duration_ms: 소요 시간 (밀리초)
        threshold_ms: 경고 임계값 (밀리초)
    """
    logger = get_logger("performance")

    if duration_ms > threshold_ms:
        logger.warning(f"[SLOW] {operation}: {duration_ms:.0f}ms (threshold: {threshold_ms}ms)")
    else:
        logger.debug(f"[PERF] {operation}: {duration_ms:.0f}ms")


# 기본 로깅 설정 (import 시 자동 실행)
_default_logger = setup_logging(level=logging.INFO, console=False)

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


# 기본 로깅 설정 (import 시 자동 실행)
_default_logger = setup_logging(level=logging.INFO, console=False)

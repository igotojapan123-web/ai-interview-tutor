# safe_utils.py
# FlyReady Lab - 안전한 유틸리티 함수 모음
# 모든 에러 핸들링과 타입 검증을 중앙 관리

import json
import os
import re
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, TypeVar, Callable
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


# =====================
# 안전한 수학 연산
# =====================

def safe_divide(numerator: Union[int, float],
                denominator: Union[int, float],
                default: Union[int, float] = 0) -> Union[int, float]:
    """안전한 나눗셈 - Division by Zero 방지"""
    try:
        if denominator is None or denominator == 0:
            return default
        if not isinstance(numerator, (int, float)):
            return default
        if not isinstance(denominator, (int, float)):
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def safe_percentage(part: Union[int, float],
                   whole: Union[int, float],
                   decimals: int = 0) -> Union[int, float]:
    """안전한 퍼센트 계산"""
    result = safe_divide(part, whole, 0) * 100
    if decimals == 0:
        return int(result)
    return round(result, decimals)


def safe_average(values: List[Union[int, float]],
                 default: Union[int, float] = 0) -> Union[int, float]:
    """안전한 평균 계산"""
    if not values or not isinstance(values, (list, tuple)):
        return default
    valid_values = [v for v in values if isinstance(v, (int, float))]
    if not valid_values:
        return default
    return safe_divide(sum(valid_values), len(valid_values), default)


# =====================
# 안전한 날짜/시간 처리
# =====================

def safe_parse_date(date_str: str,
                    format_str: str = "%Y-%m-%d",
                    default: Optional[datetime] = None) -> Optional[datetime]:
    """안전한 날짜 파싱"""
    if not date_str or not isinstance(date_str, str):
        return default
    try:
        # 날짜 문자열 정규화 (첫 10자만 사용)
        clean_str = date_str.strip()[:10] if len(date_str) >= 10 else date_str.strip()
        return datetime.strptime(clean_str, format_str)
    except (ValueError, TypeError, AttributeError) as e:
        logger.debug(f"날짜 파싱 실패: {date_str} - {e}")
        return default


def safe_parse_date_to_date(date_str: str,
                            format_str: str = "%Y-%m-%d"):
    """안전한 날짜 파싱 (date 객체 반환)"""
    result = safe_parse_date(date_str, format_str)
    return result.date() if result else None


def get_days_diff(date1: datetime, date2: datetime = None) -> int:
    """두 날짜 사이의 일수 차이 계산"""
    if date2 is None:
        date2 = datetime.now()
    try:
        if hasattr(date1, 'date'):
            d1 = date1.date() if callable(date1.date) else date1
        else:
            d1 = date1
        if hasattr(date2, 'date'):
            d2 = date2.date() if callable(date2.date) else date2
        else:
            d2 = date2
        return (d1 - d2).days
    except (TypeError, AttributeError):
        return 0


def get_week_start(date: datetime = None) -> datetime:
    """주의 시작일 (월요일) 반환"""
    if date is None:
        date = datetime.now()
    try:
        if hasattr(date, 'date'):
            d = date.date() if callable(date.date) else date
        else:
            d = date
        days_since_monday = d.weekday()
        return d - timedelta(days=days_since_monday)
    except (TypeError, AttributeError):
        return datetime.now().date() - timedelta(days=datetime.now().weekday())


# =====================
# 안전한 데이터 접근
# =====================

def safe_get(data: Any,
             key: str,
             default: Any = None) -> Any:
    """안전한 딕셔너리/객체 접근"""
    if data is None:
        return default
    try:
        if isinstance(data, dict):
            return data.get(key, default)
        if hasattr(data, key):
            return getattr(data, key, default)
        return default
    except (TypeError, KeyError, AttributeError):
        return default


def safe_get_nested(data: Any,
                    keys: List[str],
                    default: Any = None) -> Any:
    """안전한 중첩 딕셔너리 접근

    예: safe_get_nested(data, ['user', 'profile', 'name'], 'Unknown')
    """
    if not keys or data is None:
        return default
    current = data
    for key in keys:
        current = safe_get(current, key, None)
        if current is None:
            return default
    return current if current is not None else default


def safe_list_get(lst: List,
                  index: int,
                  default: Any = None) -> Any:
    """안전한 리스트 인덱스 접근"""
    if not isinstance(lst, (list, tuple)):
        return default
    try:
        if -len(lst) <= index < len(lst):
            return lst[index]
        return default
    except (TypeError, IndexError):
        return default


# =====================
# 안전한 파일 처리
# =====================

def safe_load_json(filepath: str,
                   default: Any = None,
                   encoding: str = "utf-8") -> Any:
    """안전한 JSON 파일 로드"""
    if default is None:
        default = {}

    if not filepath or not isinstance(filepath, str):
        logger.warning("잘못된 파일 경로")
        return default

    if not os.path.exists(filepath):
        logger.debug(f"파일 없음: {filepath}")
        return default

    try:
        # 파일 크기 검사 (100MB 제한)
        file_size = os.path.getsize(filepath)
        if file_size > 100 * 1024 * 1024:
            logger.error(f"파일 크기 초과: {filepath} ({file_size} bytes)")
            return default

        with open(filepath, "r", encoding=encoding) as f:
            data = json.load(f)

        # 타입 검증
        if default is not None and not isinstance(data, type(default)):
            logger.warning(f"예상치 못한 데이터 타입: {type(data)}, 기대: {type(default)}")
            # 여전히 데이터 반환 (경고만)

        return data

    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패 ({filepath}): {e}")
        return default
    except PermissionError as e:
        logger.error(f"파일 권한 오류 ({filepath}): {e}")
        return default
    except Exception as e:
        logger.error(f"파일 읽기 실패 ({filepath}): {type(e).__name__} - {e}")
        return default


def safe_save_json(filepath: str,
                   data: Any,
                   encoding: str = "utf-8",
                   indent: int = 2) -> bool:
    """안전한 JSON 파일 저장"""
    if not filepath or not isinstance(filepath, str):
        logger.error("잘못된 파일 경로")
        return False

    try:
        # 디렉토리가 없으면 생성
        dir_path = os.path.dirname(filepath)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        # 임시 파일에 먼저 쓰기 (원자적 쓰기)
        temp_path = filepath + ".tmp"
        with open(temp_path, "w", encoding=encoding) as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)

        # 성공하면 원본 파일로 교체
        if os.path.exists(filepath):
            os.replace(temp_path, filepath)
        else:
            os.rename(temp_path, filepath)

        return True

    except (TypeError, ValueError) as e:
        logger.error(f"JSON 직렬화 실패: {e}")
        return False
    except PermissionError as e:
        logger.error(f"파일 쓰기 권한 오류 ({filepath}): {e}")
        return False
    except Exception as e:
        logger.error(f"파일 저장 실패 ({filepath}): {type(e).__name__} - {e}")
        # 임시 파일 정리
        temp_path = filepath + ".tmp"
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return False


# =====================
# 안전한 문자열 처리
# =====================

def safe_str(value: Any, default: str = "") -> str:
    """안전한 문자열 변환"""
    if value is None:
        return default
    try:
        return str(value)
    except (TypeError, ValueError):
        return default


def safe_strip(value: str, default: str = "") -> str:
    """안전한 문자열 트림"""
    if not isinstance(value, str):
        return default
    return value.strip()


def safe_truncate(text: str,
                  max_length: int,
                  suffix: str = "...") -> str:
    """안전한 문자열 자르기"""
    if not isinstance(text, str):
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def sanitize_html(text: str) -> str:
    """HTML 특수문자 이스케이프 (XSS 방지)"""
    if not isinstance(text, str):
        return ""
    escape_map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
    }
    for char, escape in escape_map.items():
        text = text.replace(char, escape)
    return text


# =====================
# 입력 검증
# =====================

def validate_email(email: str) -> bool:
    """이메일 형식 검증"""
    if not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> bool:
    """날짜 형식 검증"""
    return safe_parse_date(date_str, format_str) is not None


def validate_range(value: Union[int, float],
                   min_val: Union[int, float] = None,
                   max_val: Union[int, float] = None) -> bool:
    """숫자 범위 검증"""
    if not isinstance(value, (int, float)):
        return False
    if min_val is not None and value < min_val:
        return False
    if max_val is not None and value > max_val:
        return False
    return True


# =====================
# 에러 핸들링 데코레이터
# =====================

def handle_errors(default_return: Any = None,
                  log_level: str = "error",
                  reraise: bool = False):
    """에러 핸들링 데코레이터

    사용법:
        @handle_errors(default_return=[], log_level="warning")
        def my_function():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_func = getattr(logger, log_level, logger.error)
                log_func(f"{func.__name__} 실패: {type(e).__name__} - {e}")
                if reraise:
                    raise
                return default_return
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3,
                     delay_seconds: float = 1.0,
                     exponential_backoff: bool = True,
                     exceptions: tuple = (Exception,)):
    """재시도 데코레이터

    사용법:
        @retry_on_failure(max_retries=3, delay_seconds=1.0)
        def api_call():
            ...
    """
    import time

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay_seconds * (2 ** attempt if exponential_backoff else 1)
                        logger.warning(f"{func.__name__} 재시도 {attempt + 1}/{max_retries} "
                                      f"(대기: {wait_time:.1f}초) - {e}")
                        time.sleep(wait_time)
            logger.error(f"{func.__name__} 최종 실패: {last_exception}")
            raise last_exception
        return wrapper
    return decorator


# =====================
# 상수 및 설정
# =====================

class Constants:
    """애플리케이션 상수"""

    # 날짜/시간
    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    # 임계값
    URGENT_DAYS = 7
    WARNING_DAYS = 3
    MIN_PRACTICE_COUNT = 5

    # 캐시
    CACHE_TTL_SHORT = 60      # 1분
    CACHE_TTL_MEDIUM = 300    # 5분
    CACHE_TTL_LONG = 3600     # 1시간

    # 파일 크기
    MAX_FILE_SIZE_MB = 100
    MAX_UPLOAD_SIZE_MB = 50

    # 점수
    SCORE_MIN = 0
    SCORE_MAX = 100
    LOW_SCORE_THRESHOLD = 60


# =====================
# 타입 변환
# =====================

def to_int(value: Any, default: int = 0) -> int:
    """안전한 정수 변환"""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default
    return default


def to_float(value: Any, default: float = 0.0) -> float:
    """안전한 실수 변환"""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    return default


def to_bool(value: Any, default: bool = False) -> bool:
    """안전한 불리언 변환"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    if isinstance(value, (int, float)):
        return value != 0
    return default

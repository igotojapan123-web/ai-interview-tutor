# shared_utils.py
# 대기업 수준 공용 유틸리티 모듈
# FlyReady Lab - Shared Utilities (중복 코드 통합)
#
# 이 모듈은 여러 파일에서 중복 정의된 함수들을 통합합니다.
# 모든 페이지에서 이 모듈을 import하여 사용하세요.

import streamlit as st
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# 파일 경로 설정
# =============================================================================

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent

# 데이터 디렉토리
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
TEMP_DIR = PROJECT_ROOT / "temp"

# 디렉토리 생성 (없으면)
for dir_path in [DATA_DIR, LOGS_DIR, TEMP_DIR]:
    dir_path.mkdir(exist_ok=True)


# =============================================================================
# API 키 관리 (통합)
# =============================================================================

def get_api_key(key_name: str = "OPENAI_API_KEY") -> Optional[str]:
    """API 키 가져오기 (통합 버전)

    우선순위:
    1. st.session_state
    2. st.secrets
    3. 환경 변수
    4. env_config 모듈

    Args:
        key_name: API 키 이름 (기본값: OPENAI_API_KEY)

    Returns:
        API 키 문자열 또는 None
    """
    # 1. 세션 상태에서 확인
    if key_name in st.session_state:
        return st.session_state[key_name]

    # 2. Streamlit secrets에서 확인
    try:
        if hasattr(st, 'secrets') and key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass

    # 3. 환경 변수에서 확인
    env_value = os.environ.get(key_name)
    if env_value:
        return env_value

    # 4. env_config 모듈에서 확인
    try:
        from env_config import OPENAI_API_KEY, CLOVA_CLIENT_ID, CLOVA_CLIENT_SECRET

        key_mapping = {
            "OPENAI_API_KEY": OPENAI_API_KEY,
            "CLOVA_CLIENT_ID": CLOVA_CLIENT_ID,
            "CLOVA_CLIENT_SECRET": CLOVA_CLIENT_SECRET,
        }

        if key_name in key_mapping:
            return key_mapping[key_name]
    except ImportError:
        pass

    logger.warning(f"API key not found: {key_name}")
    return None


def set_api_key(key_name: str, value: str):
    """API 키 설정 (세션에 저장)"""
    st.session_state[key_name] = value


def mask_api_key(key: str, visible_chars: int = 4) -> str:
    """API 키 마스킹"""
    if not key or len(key) <= visible_chars * 2:
        return "*" * len(key) if key else ""
    return key[:visible_chars] + "*" * (len(key) - visible_chars * 2) + key[-visible_chars:]


# =============================================================================
# JSON 파일 관리 (통합)
# =============================================================================

def load_json(
    filepath: Union[str, Path],
    default: Any = None,
    encoding: str = "utf-8"
) -> Any:
    """JSON 파일 로드 (통합 버전)

    Args:
        filepath: 파일 경로
        default: 파일이 없을 때 기본값
        encoding: 인코딩

    Returns:
        JSON 데이터 또는 기본값
    """
    try:
        path = Path(filepath)
        if not path.exists():
            logger.debug(f"JSON file not found: {filepath}")
            return default if default is not None else {}

        with open(path, "r", encoding=encoding) as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {filepath}: {e}")
        return default if default is not None else {}
    except Exception as e:
        logger.error(f"Error loading JSON {filepath}: {e}")
        return default if default is not None else {}


def save_json(
    filepath: Union[str, Path],
    data: Any,
    encoding: str = "utf-8",
    indent: int = 2,
    ensure_ascii: bool = False
) -> bool:
    """JSON 파일 저장 (통합 버전)

    Args:
        filepath: 파일 경로
        data: 저장할 데이터
        encoding: 인코딩
        indent: 들여쓰기
        ensure_ascii: ASCII 강제 여부

    Returns:
        성공 여부
    """
    try:
        path = Path(filepath)

        # 디렉토리 생성
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding=encoding) as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)

        logger.debug(f"JSON saved: {filepath}")
        return True

    except Exception as e:
        logger.error(f"Error saving JSON {filepath}: {e}")
        return False


def append_to_json_array(
    filepath: Union[str, Path],
    item: Any,
    max_items: Optional[int] = None
) -> bool:
    """JSON 배열에 항목 추가

    Args:
        filepath: 파일 경로
        item: 추가할 항목
        max_items: 최대 항목 수 (초과 시 오래된 것 삭제)

    Returns:
        성공 여부
    """
    data = load_json(filepath, default=[])

    if not isinstance(data, list):
        data = []

    data.append(item)

    # 최대 항목 수 제한
    if max_items and len(data) > max_items:
        data = data[-max_items:]

    return save_json(filepath, data)


# =============================================================================
# 세션 상태 관리 (통합)
# =============================================================================

def init_session_state(defaults: Dict[str, Any]):
    """세션 상태 초기화

    Args:
        defaults: 기본값 딕셔너리
    """
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_session_value(key: str, default: Any = None) -> Any:
    """세션 값 가져오기"""
    return st.session_state.get(key, default)


def set_session_value(key: str, value: Any):
    """세션 값 설정"""
    st.session_state[key] = value


def clear_session_keys(keys: List[str]):
    """특정 세션 키들 삭제"""
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]


def clear_session_prefix(prefix: str):
    """특정 접두사로 시작하는 세션 키들 삭제"""
    keys_to_delete = [k for k in st.session_state.keys() if k.startswith(prefix)]
    for key in keys_to_delete:
        del st.session_state[key]


# =============================================================================
# 텍스트 처리 유틸리티
# =============================================================================

def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """텍스트 정제

    Args:
        text: 입력 텍스트
        max_length: 최대 길이

    Returns:
        정제된 텍스트
    """
    if not text:
        return ""

    # 문자열로 변환
    text = str(text)

    # 앞뒤 공백 제거
    text = text.strip()

    # 연속 공백 제거
    import re
    text = re.sub(r'\s+', ' ', text)

    # 길이 제한
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """텍스트 자르기

    Args:
        text: 입력 텍스트
        max_length: 최대 길이
        suffix: 접미사

    Returns:
        잘린 텍스트
    """
    if not text or len(text) <= max_length:
        return text or ""

    return text[:max_length - len(suffix)] + suffix


def format_number(num: Union[int, float], decimal_places: int = 0) -> str:
    """숫자 포맷팅 (천 단위 구분)

    Args:
        num: 숫자
        decimal_places: 소수점 자리수

    Returns:
        포맷된 문자열
    """
    if decimal_places > 0:
        return f"{num:,.{decimal_places}f}"
    return f"{int(num):,}"


def format_percentage(value: float, decimal_places: int = 1) -> str:
    """백분율 포맷팅"""
    return f"{value:.{decimal_places}f}%"


# =============================================================================
# 날짜/시간 유틸리티
# =============================================================================

def format_datetime(
    dt: Optional[datetime] = None,
    format_str: str = "%Y-%m-%d %H:%M"
) -> str:
    """날짜/시간 포맷팅

    Args:
        dt: datetime 객체 (None이면 현재 시간)
        format_str: 포맷 문자열

    Returns:
        포맷된 문자열
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)


def format_date(dt: Optional[datetime] = None) -> str:
    """날짜 포맷팅 (YYYY-MM-DD)"""
    return format_datetime(dt, "%Y-%m-%d")


def format_time(dt: Optional[datetime] = None) -> str:
    """시간 포맷팅 (HH:MM)"""
    return format_datetime(dt, "%H:%M")


def format_relative_time(dt: datetime) -> str:
    """상대 시간 포맷팅 (예: "3분 전")"""
    now = datetime.now()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return "방금 전"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}분 전"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}시간 전"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days}일 전"
    else:
        return format_date(dt)


def get_today_string() -> str:
    """오늘 날짜 문자열 (YYYY-MM-DD)"""
    return format_date()


# =============================================================================
# 파일 유틸리티
# =============================================================================

def ensure_dir(path: Union[str, Path]) -> Path:
    """디렉토리 확인/생성

    Args:
        path: 디렉토리 경로

    Returns:
        Path 객체
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size_str(size_bytes: int) -> str:
    """파일 크기 문자열 변환

    Args:
        size_bytes: 바이트 크기

    Returns:
        읽기 쉬운 크기 문자열
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def is_valid_filename(filename: str) -> bool:
    """안전한 파일명인지 확인"""
    if not filename:
        return False

    # 위험한 패턴 체크
    dangerous_patterns = ['..', '/', '\\', '\0']
    for pattern in dangerous_patterns:
        if pattern in filename:
            return False

    # 허용된 문자만 포함하는지 확인
    import re
    if not re.match(r'^[\w\-. ]+$', filename):
        return False

    return True


# =============================================================================
# 리스트/딕셔너리 유틸리티
# =============================================================================

def safe_get(data: Union[Dict, List], key: Any, default: Any = None) -> Any:
    """안전하게 값 가져오기

    Args:
        data: 딕셔너리 또는 리스트
        key: 키 또는 인덱스
        default: 기본값

    Returns:
        값 또는 기본값
    """
    try:
        if isinstance(data, dict):
            return data.get(key, default)
        elif isinstance(data, (list, tuple)):
            return data[key] if 0 <= key < len(data) else default
    except (KeyError, IndexError, TypeError):
        pass
    return default


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """리스트를 청크로 분할

    Args:
        lst: 입력 리스트
        chunk_size: 청크 크기

    Returns:
        청크 리스트
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_list(nested_list: List) -> List:
    """중첩 리스트 평탄화"""
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def remove_duplicates(lst: List, key: Optional[str] = None) -> List:
    """중복 제거 (순서 유지)

    Args:
        lst: 입력 리스트
        key: 딕셔너리인 경우 비교할 키

    Returns:
        중복 제거된 리스트
    """
    seen = set()
    result = []

    for item in lst:
        check_value = item.get(key) if key and isinstance(item, dict) else item
        check_key = str(check_value)

        if check_key not in seen:
            seen.add(check_key)
            result.append(item)

    return result


# =============================================================================
# 유효성 검사 유틸리티
# =============================================================================

def is_valid_email(email: str) -> bool:
    """이메일 형식 검사"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email)) if email else False


def is_valid_phone(phone: str) -> bool:
    """전화번호 형식 검사 (한국)"""
    import re
    # 010-1234-5678, 01012345678, 02-123-4567 등
    pattern = r'^(0\d{1,2})-?(\d{3,4})-?(\d{4})$'
    return bool(re.match(pattern, phone)) if phone else False


def is_valid_url(url: str) -> bool:
    """URL 형식 검사"""
    import re
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url, re.IGNORECASE)) if url else False


# =============================================================================
# 에러 처리 헬퍼
# =============================================================================

def safe_execute(func, *args, default=None, **kwargs):
    """안전한 함수 실행

    Args:
        func: 실행할 함수
        *args: 위치 인자
        default: 에러 시 반환값
        **kwargs: 키워드 인자

    Returns:
        함수 결과 또는 기본값
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error in {func.__name__}: {e}")
        return default


# =============================================================================
# 캐싱 헬퍼
# =============================================================================

def get_cached(
    key: str,
    loader_func,
    ttl_seconds: int = 300,
    force_reload: bool = False
):
    """세션 기반 캐시

    Args:
        key: 캐시 키
        loader_func: 데이터 로드 함수
        ttl_seconds: TTL (초)
        force_reload: 강제 갱신

    Returns:
        캐시된 데이터 또는 새로 로드한 데이터
    """
    import time

    cache_key = f"_cache_{key}"
    time_key = f"_cache_{key}_time"

    current_time = time.time()

    # 캐시 확인
    if not force_reload and cache_key in st.session_state:
        cached_time = st.session_state.get(time_key, 0)
        if current_time - cached_time < ttl_seconds:
            return st.session_state[cache_key]

    # 새로 로드
    data = loader_func()
    st.session_state[cache_key] = data
    st.session_state[time_key] = current_time

    return data


def clear_cache(key: str):
    """특정 캐시 삭제"""
    cache_key = f"_cache_{key}"
    time_key = f"_cache_{key}_time"

    if cache_key in st.session_state:
        del st.session_state[cache_key]
    if time_key in st.session_state:
        del st.session_state[time_key]


# =============================================================================
# 로깅 헬퍼
# =============================================================================

def log_user_action(action: str, details: Optional[Dict] = None):
    """사용자 액션 로깅

    Args:
        action: 액션 이름
        details: 추가 정보
    """
    log_entry = {
        "timestamp": format_datetime(),
        "action": action,
        "details": details or {}
    }

    # 세션에 저장
    if "user_action_log" not in st.session_state:
        st.session_state.user_action_log = []

    st.session_state.user_action_log.append(log_entry)

    # 최대 100개 유지
    if len(st.session_state.user_action_log) > 100:
        st.session_state.user_action_log = st.session_state.user_action_log[-100:]

    logger.info(f"User action: {action} - {details}")


def get_user_action_log() -> List[Dict]:
    """사용자 액션 로그 조회"""
    return st.session_state.get("user_action_log", [])

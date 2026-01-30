# safe_api.py
# FlyReady Lab - 안전한 API 호출 및 데이터 처리 유틸리티
# 모든 API 호출, 데이터 검증, 에러 처리를 위한 공통 모듈

import os
import time
import json
import hashlib
import functools
import traceback
from typing import Any, Dict, List, Optional, Callable, TypeVar, Union
from datetime import datetime
import threading

# 로깅
try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# ============================================================
# 1. 안전한 API 호출 데코레이터
# ============================================================

T = TypeVar('T')

def safe_api_call(
    max_retries: int = 3,
    base_delay: float = 1.0,
    timeout: int = 120,
    fallback: Any = None,
    notify_on_failure: bool = True
) -> Callable:
    """
    안전한 API 호출 데코레이터
    - 자동 재시도 (지수 백오프)
    - 타임아웃 처리
    - 에러 로깅
    - 실패시 fallback 반환
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None

            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)

                    if attempt > 0:
                        logger.info(f"[SafeAPI] {func.__name__} 성공 (재시도 {attempt}회)")

                    return result

                except Exception as e:
                    last_error = e
                    error_msg = str(e).lower()

                    # 재시도 불가능한 에러
                    if any(x in error_msg for x in ['invalid', 'unauthorized', '401', '403', 'api key']):
                        logger.error(f"[SafeAPI] {func.__name__} 인증 오류 (재시도 안함): {e}")
                        break

                    # 재시도 가능한 에러
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"[SafeAPI] {func.__name__} 실패 (시도 {attempt+1}/{max_retries}): {e}")
                        logger.info(f"[SafeAPI] {delay:.1f}초 후 재시도...")
                        time.sleep(delay)
                    else:
                        logger.error(f"[SafeAPI] {func.__name__} 최종 실패: {e}")

            # 모든 재시도 실패
            if notify_on_failure and last_error:
                _log_api_failure(func.__name__, last_error)

            if fallback is not None:
                return fallback

            return None

        return wrapper
    return decorator


def _log_api_failure(func_name: str, error: Exception):
    """API 실패 로깅 (백그라운드)"""
    def log():
        try:
            from error_monitor import ErrorLogger, ErrorLevel
            error_logger = ErrorLogger()
            error_logger.log_error(
                error=error,
                level=ErrorLevel.ERROR,
                page=f"API: {func_name}",
                context={"api_call": True}
            )
        except:
            pass

    thread = threading.Thread(target=log, daemon=True)
    thread.start()


# ============================================================
# 2. 오디오 중복 감지 (해시 기반)
# ============================================================

def get_audio_hash(audio_data: bytes) -> str:
    """
    오디오 데이터의 고유 해시값 생성
    - id() 대신 실제 데이터 해시 사용
    - 동일한 오디오는 항상 같은 해시
    """
    if not audio_data:
        return ""

    # 바이트 데이터의 MD5 해시
    return hashlib.md5(audio_data).hexdigest()


def is_audio_processed(audio_data: bytes, session_key: str, session_state) -> bool:
    """
    오디오가 이미 처리되었는지 확인

    Args:
        audio_data: 오디오 바이트 데이터
        session_key: 세션 상태 키 (예: 'mock_processed_audio_hash')
        session_state: st.session_state

    Returns:
        True if already processed, False if new
    """
    if not audio_data:
        return True  # 빈 데이터는 처리 안함

    current_hash = get_audio_hash(audio_data)
    previous_hash = getattr(session_state, session_key, None)

    if current_hash == previous_hash:
        return True  # 이미 처리됨

    # 새 해시 저장
    setattr(session_state, session_key, current_hash)
    return False  # 새 오디오


# ============================================================
# 3. 입력값 검증 유틸리티
# ============================================================

def validate_string(value: Any, default: str = "", max_length: int = 10000) -> str:
    """문자열 검증 및 정제"""
    if value is None:
        return default

    try:
        result = str(value).strip()
        if len(result) > max_length:
            result = result[:max_length]
        return result
    except:
        return default


def validate_int(value: Any, default: int = 0, min_val: int = None, max_val: int = None) -> int:
    """정수 검증"""
    try:
        result = int(value)
        if min_val is not None and result < min_val:
            return min_val
        if max_val is not None and result > max_val:
            return max_val
        return result
    except:
        return default


def validate_float(value: Any, default: float = 0.0, min_val: float = None, max_val: float = None) -> float:
    """실수 검증"""
    try:
        result = float(value)
        if min_val is not None and result < min_val:
            return min_val
        if max_val is not None and result > max_val:
            return max_val
        return result
    except:
        return default


def validate_list(value: Any, default: List = None) -> List:
    """리스트 검증"""
    if default is None:
        default = []

    if value is None:
        return default

    if isinstance(value, list):
        return value

    if isinstance(value, (tuple, set)):
        return list(value)

    return default


def validate_dict(value: Any, default: Dict = None, required_keys: List[str] = None) -> Dict:
    """딕셔너리 검증"""
    if default is None:
        default = {}

    if value is None:
        return default

    if not isinstance(value, dict):
        return default

    # 필수 키 확인
    if required_keys:
        for key in required_keys:
            if key not in value:
                return default

    return value


# ============================================================
# 4. JSON 응답 검증
# ============================================================

def validate_api_response(
    response: Any,
    required_fields: List[str] = None,
    default: Any = None
) -> Any:
    """
    API 응답 검증

    Args:
        response: API 응답 (dict 또는 기타)
        required_fields: 필수 필드 목록
        default: 검증 실패시 반환할 기본값
    """
    if response is None:
        logger.warning("[Validate] API 응답이 None")
        return default

    if not isinstance(response, dict):
        logger.warning(f"[Validate] API 응답이 dict가 아님: {type(response)}")
        return default

    # 에러 응답 체크
    if "error" in response:
        logger.warning(f"[Validate] API 에러 응답: {response.get('error')}")
        return default

    # 필수 필드 체크
    if required_fields:
        missing = [f for f in required_fields if f not in response]
        if missing:
            logger.warning(f"[Validate] 필수 필드 누락: {missing}")
            return default

    return response


def safe_get(data: Dict, *keys, default: Any = None) -> Any:
    """
    중첩된 딕셔너리에서 안전하게 값 가져오기

    예: safe_get(data, 'user', 'profile', 'name', default='Unknown')
    """
    result = data

    for key in keys:
        if result is None:
            return default

        if isinstance(result, dict):
            result = result.get(key)
        elif isinstance(result, (list, tuple)) and isinstance(key, int):
            try:
                result = result[key]
            except (IndexError, TypeError):
                return default
        else:
            return default

    return result if result is not None else default


# ============================================================
# 5. 세션 상태 안전 관리
# ============================================================

def safe_session_get(session_state, key: str, default: Any = None) -> Any:
    """세션 상태에서 안전하게 값 가져오기"""
    try:
        if hasattr(session_state, key):
            value = getattr(session_state, key)
            return value if value is not None else default
        return default
    except:
        return default


def safe_session_set(session_state, key: str, value: Any) -> bool:
    """세션 상태에 안전하게 값 설정"""
    try:
        setattr(session_state, key, value)
        return True
    except:
        return False


def init_session_state(session_state, defaults: Dict[str, Any]) -> None:
    """
    세션 상태 초기화 (없는 키만 설정)

    예: init_session_state(st.session_state, {
        'user_id': str(uuid.uuid4()),
        'answers': [],
        'scores': {}
    })
    """
    for key, default_value in defaults.items():
        if not hasattr(session_state, key) or getattr(session_state, key) is None:
            setattr(session_state, key, default_value)


def safe_list_append(session_state, key: str, item: Any) -> bool:
    """세션 상태의 리스트에 안전하게 항목 추가"""
    try:
        current = getattr(session_state, key, None)
        if current is None:
            setattr(session_state, key, [item])
        elif isinstance(current, list):
            current.append(item)
        else:
            setattr(session_state, key, [item])
        return True
    except:
        return False


# ============================================================
# 6. 안전한 에러 래퍼
# ============================================================

def safe_execute(
    func: Callable,
    *args,
    default: Any = None,
    error_message: str = None,
    log_error: bool = True,
    **kwargs
) -> Any:
    """
    함수를 안전하게 실행

    Args:
        func: 실행할 함수
        default: 에러시 반환할 기본값
        error_message: 사용자에게 보여줄 에러 메시지
        log_error: 에러 로깅 여부
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            logger.error(f"[SafeExecute] {func.__name__} 실패: {e}")
            logger.debug(traceback.format_exc())

        return default


class SafeContext:
    """
    안전한 실행 컨텍스트 매니저

    예:
        with SafeContext("API 호출", default=[]):
            result = api_call()
    """

    def __init__(self, name: str, default: Any = None, log_error: bool = True):
        self.name = name
        self.default = default
        self.log_error = log_error
        self.result = default
        self.error = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error = exc_val
            if self.log_error:
                logger.error(f"[SafeContext] {self.name} 실패: {exc_val}")
            return True  # 예외 억제
        return False


# ============================================================
# 7. 보안 유틸리티
# ============================================================

def hash_password(password: str, salt: str = None) -> tuple:
    """
    비밀번호 해시 (salt 포함)

    Returns:
        (hash, salt) 튜플
    """
    import secrets

    if salt is None:
        salt = secrets.token_hex(16)

    # PBKDF2 사용 (SHA256보다 안전)
    import hashlib
    hash_value = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt.encode(),
        100000  # 반복 횟수
    ).hex()

    return hash_value, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """비밀번호 검증"""
    computed_hash, _ = hash_password(password, salt)
    return computed_hash == stored_hash


class LoginRateLimiter:
    """로그인 시도 제한"""

    def __init__(self, max_attempts: int = 5, lockout_minutes: int = 15):
        self.max_attempts = max_attempts
        self.lockout_minutes = lockout_minutes
        self._attempts = {}  # {username: [(timestamp, success), ...]}

    def record_attempt(self, username: str, success: bool):
        """로그인 시도 기록"""
        now = datetime.now()

        if username not in self._attempts:
            self._attempts[username] = []

        self._attempts[username].append((now, success))

        # 오래된 기록 삭제 (1시간 이상)
        cutoff = now.timestamp() - 3600
        self._attempts[username] = [
            (t, s) for t, s in self._attempts[username]
            if t.timestamp() > cutoff
        ]

    def is_locked(self, username: str) -> bool:
        """계정 잠금 여부 확인"""
        if username not in self._attempts:
            return False

        now = datetime.now()
        lockout_cutoff = now.timestamp() - (self.lockout_minutes * 60)

        # 최근 실패 횟수 계산
        recent_failures = sum(
            1 for t, s in self._attempts[username]
            if not s and t.timestamp() > lockout_cutoff
        )

        return recent_failures >= self.max_attempts

    def get_remaining_lockout(self, username: str) -> int:
        """남은 잠금 시간 (초)"""
        if username not in self._attempts:
            return 0

        failures = [t for t, s in self._attempts[username] if not s]
        if not failures:
            return 0

        last_failure = max(failures)
        unlock_time = last_failure.timestamp() + (self.lockout_minutes * 60)
        remaining = unlock_time - datetime.now().timestamp()

        return max(0, int(remaining))


# 전역 로그인 제한기
login_limiter = LoginRateLimiter()


# ============================================================
# 8. HTML 이스케이프
# ============================================================

def escape_html(text: str) -> str:
    """HTML 특수문자 이스케이프"""
    if not text:
        return ""

    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def safe_markdown(text: str, allow_html: bool = False) -> str:
    """안전한 마크다운 텍스트"""
    if not text:
        return ""

    if not allow_html:
        text = escape_html(text)

    return text


# ============================================================
# 9. 사용자 입력 검증 (강화)
# ============================================================

def sanitize_user_input(
    text: str,
    max_length: int = 5000,
    strip_html: bool = True,
    allow_newlines: bool = True
) -> str:
    """
    사용자 입력 정제 및 검증

    Args:
        text: 입력 텍스트
        max_length: 최대 길이
        strip_html: HTML 태그 제거 여부
        allow_newlines: 줄바꿈 허용 여부
    """
    if not text:
        return ""

    result = str(text).strip()

    # 길이 제한
    if len(result) > max_length:
        result = result[:max_length]

    # HTML 태그 제거
    if strip_html:
        import re
        result = re.sub(r'<[^>]+>', '', result)

    # 줄바꿈 처리
    if not allow_newlines:
        result = result.replace('\n', ' ').replace('\r', '')

    # 연속 공백 제거
    result = ' '.join(result.split())

    return result


def validate_room_name(name: str) -> tuple:
    """
    방 이름 검증

    Returns:
        (is_valid, cleaned_name, error_message)
    """
    if not name:
        return False, "", "방 이름을 입력해주세요"

    cleaned = sanitize_user_input(name, max_length=30, allow_newlines=False)

    if len(cleaned) < 2:
        return False, cleaned, "방 이름은 2자 이상이어야 합니다"

    if len(cleaned) > 30:
        return False, cleaned[:30], "방 이름은 30자 이하여야 합니다"

    return True, cleaned, ""


def validate_chat_message(message: str) -> tuple:
    """
    채팅 메시지 검증

    Returns:
        (is_valid, cleaned_message, error_message)
    """
    if not message:
        return False, "", "메시지를 입력해주세요"

    cleaned = sanitize_user_input(message, max_length=500, allow_newlines=False)

    if len(cleaned) < 1:
        return False, cleaned, "메시지를 입력해주세요"

    return True, cleaned, ""


def validate_answer_text(answer: str, min_length: int = 10, max_length: int = 5000) -> tuple:
    """
    답변 텍스트 검증

    Returns:
        (is_valid, cleaned_answer, error_message)
    """
    if not answer:
        return False, "", "답변을 입력해주세요"

    cleaned = sanitize_user_input(answer, max_length=max_length, allow_newlines=True)

    if len(cleaned) < min_length:
        return False, cleaned, f"답변은 {min_length}자 이상이어야 합니다"

    return True, cleaned, ""


def validate_username(username: str) -> tuple:
    """
    사용자 이름 검증

    Returns:
        (is_valid, cleaned_name, error_message)
    """
    if not username:
        return False, "", "이름을 입력해주세요"

    cleaned = sanitize_user_input(username, max_length=20, allow_newlines=False)

    if len(cleaned) < 2:
        return False, cleaned, "이름은 2자 이상이어야 합니다"

    if len(cleaned) > 20:
        return False, cleaned[:20], "이름은 20자 이하여야 합니다"

    # 특수문자 체크 (한글, 영문, 숫자, 기본 특수문자만 허용)
    import re
    if not re.match(r'^[가-힣a-zA-Z0-9_\- ]+$', cleaned):
        return False, cleaned, "이름에 특수문자를 사용할 수 없습니다"

    return True, cleaned, ""


# ============================================================
# 10. JSON 응답 안전 파싱
# ============================================================

def safe_json_parse(text: str, default: Any = None) -> Any:
    """
    JSON 문자열 안전 파싱

    Args:
        text: JSON 문자열 또는 JSON을 포함한 텍스트
        default: 파싱 실패시 반환값
    """
    if not text:
        return default

    import re

    # 이미 dict/list면 그대로 반환
    if isinstance(text, (dict, list)):
        return text

    try:
        # 직접 파싱 시도
        return json.loads(text)
    except:
        pass

    # JSON 블록 추출 시도
    try:
        # ```json ... ``` 블록 찾기
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if json_match:
            return json.loads(json_match.group(1))

        # { ... } 또는 [ ... ] 찾기
        brace_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
        if brace_match:
            return json.loads(brace_match.group(1))
    except:
        pass

    return default


def validate_json_response(
    response: Any,
    schema: Dict[str, type] = None,
    required_fields: List[str] = None
) -> tuple:
    """
    JSON 응답 스키마 검증

    Args:
        response: 검증할 응답
        schema: 필드별 타입 정의 {'field': type}
        required_fields: 필수 필드 목록

    Returns:
        (is_valid, response_or_default, errors)
    """
    errors = []

    if response is None:
        return False, {}, ["응답이 없습니다"]

    if not isinstance(response, dict):
        return False, {}, ["응답이 객체 형식이 아닙니다"]

    # 필수 필드 체크
    if required_fields:
        for field in required_fields:
            if field not in response:
                errors.append(f"필수 필드 누락: {field}")

    # 스키마 타입 체크
    if schema:
        for field, expected_type in schema.items():
            if field in response:
                if not isinstance(response[field], expected_type):
                    errors.append(f"타입 불일치: {field} (기대: {expected_type.__name__})")

    if errors:
        return False, response, errors

    return True, response, []


# ============================================================
# 초기화 확인
# ============================================================

if __name__ == "__main__":
    print("=== Safe API Module ===")
    print("Functions available:")
    print("  - safe_api_call (decorator)")
    print("  - get_audio_hash, is_audio_processed")
    print("  - validate_string, validate_int, validate_dict, validate_list")
    print("  - validate_api_response, safe_get")
    print("  - safe_session_get, safe_session_set, init_session_state")
    print("  - safe_execute, SafeContext")
    print("  - hash_password, verify_password, LoginRateLimiter")
    print("  - escape_html, safe_markdown")
    print("Ready!")

# enhanced_error_handler.py
# FlyReady Lab - 강화된 에러 핸들링 시스템
# Phase A2: 에러 핸들링 500% 강화

import streamlit as st
import traceback
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List, Tuple
from functools import wraps
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

# =============================================================================
# 1. 사용자 친화적 에러 메시지 시스템
# =============================================================================

class ErrorCategory(Enum):
    """에러 카테고리"""
    NETWORK = "network"          # 네트워크 관련
    API = "api"                  # API 호출 관련
    AUTH = "auth"                # 인증 관련
    VALIDATION = "validation"    # 입력 검증 관련
    FILE = "file"                # 파일 처리 관련
    DATABASE = "database"        # 데이터베이스 관련
    MEDIA = "media"              # 미디어 처리 관련
    SYSTEM = "system"            # 시스템 관련
    UNKNOWN = "unknown"          # 알 수 없는 에러


class UserFriendlyMessages:
    """사용자 친화적 에러 메시지 매핑"""

    # 에러 타입별 친화적 메시지
    MESSAGES = {
        # 네트워크 에러
        "ConnectionError": {
            "category": ErrorCategory.NETWORK,
            "title": "연결 문제가 발생했습니다",
            "message": "인터넷 연결을 확인해 주세요. 잠시 후 다시 시도하시면 됩니다.",
            "icon": "wifi_off",
            "action": "retry",
            "retry_delay": 3
        },
        "TimeoutError": {
            "category": ErrorCategory.NETWORK,
            "title": "응답 시간이 초과되었습니다",
            "message": "서버 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요.",
            "icon": "schedule",
            "action": "retry",
            "retry_delay": 5
        },
        "HTTPError": {
            "category": ErrorCategory.API,
            "title": "서버 요청 실패",
            "message": "서버와의 통신에 문제가 있습니다. 잠시 후 다시 시도해 주세요.",
            "icon": "cloud_off",
            "action": "retry",
            "retry_delay": 3
        },

        # API 에러
        "APIError": {
            "category": ErrorCategory.API,
            "title": "API 오류가 발생했습니다",
            "message": "외부 서비스 연동에 문제가 있습니다. 잠시 후 다시 시도해 주세요.",
            "icon": "api",
            "action": "retry",
            "retry_delay": 5
        },
        "RateLimitError": {
            "category": ErrorCategory.API,
            "title": "요청이 너무 많습니다",
            "message": "잠시 휴식 후 다시 시도해 주세요. 1분 후 자동으로 재시도됩니다.",
            "icon": "speed",
            "action": "wait",
            "retry_delay": 60
        },
        "AuthenticationError": {
            "category": ErrorCategory.AUTH,
            "title": "인증 오류",
            "message": "서비스 인증에 문제가 있습니다. 관리자에게 문의해 주세요.",
            "icon": "lock",
            "action": "contact",
            "retry_delay": 0
        },

        # 파일 에러
        "FileNotFoundError": {
            "category": ErrorCategory.FILE,
            "title": "파일을 찾을 수 없습니다",
            "message": "요청하신 파일이 존재하지 않습니다. 파일 경로를 확인해 주세요.",
            "icon": "folder_off",
            "action": "check",
            "retry_delay": 0
        },
        "PermissionError": {
            "category": ErrorCategory.FILE,
            "title": "권한이 없습니다",
            "message": "파일에 접근할 권한이 없습니다. 관리자에게 문의해 주세요.",
            "icon": "lock",
            "action": "contact",
            "retry_delay": 0
        },
        "IOError": {
            "category": ErrorCategory.FILE,
            "title": "파일 처리 오류",
            "message": "파일을 처리하는 중 문제가 발생했습니다. 다른 파일로 시도해 보세요.",
            "icon": "error",
            "action": "retry",
            "retry_delay": 0
        },

        # 입력 검증 에러
        "ValueError": {
            "category": ErrorCategory.VALIDATION,
            "title": "입력값이 올바르지 않습니다",
            "message": "입력하신 내용을 다시 확인해 주세요.",
            "icon": "warning",
            "action": "fix_input",
            "retry_delay": 0
        },
        "TypeError": {
            "category": ErrorCategory.VALIDATION,
            "title": "데이터 형식 오류",
            "message": "입력 데이터 형식이 맞지 않습니다. 올바른 형식으로 입력해 주세요.",
            "icon": "warning",
            "action": "fix_input",
            "retry_delay": 0
        },
        "ValidationError": {
            "category": ErrorCategory.VALIDATION,
            "title": "입력 검증 실패",
            "message": "입력하신 내용이 요구사항에 맞지 않습니다. 다시 확인해 주세요.",
            "icon": "warning",
            "action": "fix_input",
            "retry_delay": 0
        },

        # 미디어 에러
        "AudioProcessingError": {
            "category": ErrorCategory.MEDIA,
            "title": "음성 처리 오류",
            "message": "음성을 처리하는 중 문제가 발생했습니다. 다시 녹음해 주세요.",
            "icon": "mic_off",
            "action": "retry",
            "retry_delay": 0
        },
        "VideoProcessingError": {
            "category": ErrorCategory.MEDIA,
            "title": "영상 처리 오류",
            "message": "영상을 처리하는 중 문제가 발생했습니다. 카메라를 확인해 주세요.",
            "icon": "videocam_off",
            "action": "check",
            "retry_delay": 0
        },
        "WebcamError": {
            "category": ErrorCategory.MEDIA,
            "title": "웹캠 연결 오류",
            "message": "웹캠에 접근할 수 없습니다. 브라우저 권한을 확인해 주세요.",
            "icon": "videocam_off",
            "action": "check",
            "retry_delay": 0
        },

        # 시스템 에러
        "MemoryError": {
            "category": ErrorCategory.SYSTEM,
            "title": "메모리 부족",
            "message": "시스템 메모리가 부족합니다. 다른 프로그램을 종료하고 다시 시도해 주세요.",
            "icon": "memory",
            "action": "refresh",
            "retry_delay": 0
        },
        "KeyError": {
            "category": ErrorCategory.SYSTEM,
            "title": "데이터 오류",
            "message": "필요한 데이터를 찾을 수 없습니다. 페이지를 새로고침해 주세요.",
            "icon": "error",
            "action": "refresh",
            "retry_delay": 0
        },
        "AttributeError": {
            "category": ErrorCategory.SYSTEM,
            "title": "시스템 오류",
            "message": "시스템에 일시적인 문제가 있습니다. 페이지를 새로고침해 주세요.",
            "icon": "error",
            "action": "refresh",
            "retry_delay": 0
        },
    }

    # 기본 에러 메시지
    DEFAULT_MESSAGE = {
        "category": ErrorCategory.UNKNOWN,
        "title": "오류가 발생했습니다",
        "message": "일시적인 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.",
        "icon": "error",
        "action": "retry",
        "retry_delay": 3
    }

    @classmethod
    def get_message(cls, error: Exception) -> Dict[str, Any]:
        """에러에 대한 사용자 친화적 메시지 반환"""
        error_type = type(error).__name__

        # 정확한 매칭
        if error_type in cls.MESSAGES:
            return cls.MESSAGES[error_type].copy()

        # 부분 매칭 (에러 메시지 기반)
        error_str = str(error).lower()

        if "timeout" in error_str:
            return cls.MESSAGES["TimeoutError"].copy()
        elif "connection" in error_str or "connect" in error_str:
            return cls.MESSAGES["ConnectionError"].copy()
        elif "rate limit" in error_str or "too many" in error_str:
            return cls.MESSAGES["RateLimitError"].copy()
        elif "auth" in error_str or "unauthorized" in error_str or "403" in error_str:
            return cls.MESSAGES["AuthenticationError"].copy()
        elif "permission" in error_str:
            return cls.MESSAGES["PermissionError"].copy()
        elif "webcam" in error_str or "camera" in error_str:
            return cls.MESSAGES["WebcamError"].copy()
        elif "audio" in error_str or "microphone" in error_str:
            return cls.MESSAGES["AudioProcessingError"].copy()

        return cls.DEFAULT_MESSAGE.copy()

    @classmethod
    def format_for_display(cls, error: Exception, include_details: bool = False) -> str:
        """디스플레이용 포맷된 에러 메시지"""
        info = cls.get_message(error)

        message = f"**{info['title']}**\n\n{info['message']}"

        if include_details:
            message += f"\n\n_기술적 세부사항: {type(error).__name__}: {str(error)[:100]}_"

        return message


# =============================================================================
# 2. 자동 복구 메커니즘
# =============================================================================

class AutoRecovery:
    """자동 복구 시스템"""

    # 복구 가능한 에러 타입과 전략
    RECOVERY_STRATEGIES = {
        ErrorCategory.NETWORK: {
            "max_retries": 3,
            "base_delay": 2,
            "exponential_backoff": True,
            "fallback": "show_offline_mode"
        },
        ErrorCategory.API: {
            "max_retries": 3,
            "base_delay": 5,
            "exponential_backoff": True,
            "fallback": "use_cached_response"
        },
        ErrorCategory.MEDIA: {
            "max_retries": 2,
            "base_delay": 1,
            "exponential_backoff": False,
            "fallback": "disable_feature"
        },
        ErrorCategory.SYSTEM: {
            "max_retries": 1,
            "base_delay": 0,
            "exponential_backoff": False,
            "fallback": "refresh_session"
        }
    }

    def __init__(self):
        self._retry_counts = {}
        self._last_errors = {}
        self._recovery_lock = threading.Lock()

    def _get_retry_key(self, func_name: str, category: ErrorCategory) -> str:
        """재시도 키 생성"""
        return f"{func_name}:{category.value}"

    def get_strategy(self, category: ErrorCategory) -> Dict:
        """카테고리별 복구 전략"""
        return self.RECOVERY_STRATEGIES.get(category, {
            "max_retries": 1,
            "base_delay": 3,
            "exponential_backoff": False,
            "fallback": None
        })

    def should_retry(self, func_name: str, category: ErrorCategory) -> Tuple[bool, int]:
        """재시도 여부 및 대기 시간 결정

        Returns:
            (should_retry, wait_seconds)
        """
        with self._recovery_lock:
            key = self._get_retry_key(func_name, category)
            strategy = self.get_strategy(category)

            current_count = self._retry_counts.get(key, 0)
            max_retries = strategy.get("max_retries", 1)

            if current_count >= max_retries:
                return False, 0

            # 대기 시간 계산
            base_delay = strategy.get("base_delay", 3)
            if strategy.get("exponential_backoff"):
                wait_time = base_delay * (2 ** current_count)
            else:
                wait_time = base_delay

            # 재시도 횟수 증가
            self._retry_counts[key] = current_count + 1

            return True, wait_time

    def reset_retry_count(self, func_name: str, category: ErrorCategory):
        """재시도 횟수 리셋 (성공 시)"""
        with self._recovery_lock:
            key = self._get_retry_key(func_name, category)
            if key in self._retry_counts:
                del self._retry_counts[key]

    def execute_fallback(self, fallback_name: str, context: Dict = None) -> Any:
        """폴백 전략 실행"""
        fallback_handlers = {
            "show_offline_mode": self._fallback_offline_mode,
            "use_cached_response": self._fallback_cached_response,
            "disable_feature": self._fallback_disable_feature,
            "refresh_session": self._fallback_refresh_session,
        }

        handler = fallback_handlers.get(fallback_name)
        if handler:
            return handler(context or {})
        return None

    def _fallback_offline_mode(self, context: Dict) -> Dict:
        """오프라인 모드 전환"""
        return {
            "status": "offline",
            "message": "오프라인 모드로 전환되었습니다. 일부 기능이 제한됩니다.",
            "available_features": ["saved_data", "practice_mode"]
        }

    def _fallback_cached_response(self, context: Dict) -> Dict:
        """캐시된 응답 사용"""
        cache_key = context.get("cache_key")
        if cache_key:
            # 캐시에서 데이터 조회 시도
            cached = self._get_from_cache(cache_key)
            if cached:
                return {
                    "status": "cached",
                    "message": "이전에 저장된 데이터를 표시합니다.",
                    "data": cached
                }
        return {
            "status": "no_cache",
            "message": "캐시된 데이터가 없습니다."
        }

    def _fallback_disable_feature(self, context: Dict) -> Dict:
        """기능 비활성화"""
        feature = context.get("feature", "unknown")
        return {
            "status": "disabled",
            "message": f"{feature} 기능이 일시적으로 비활성화되었습니다.",
            "alternative": context.get("alternative")
        }

    def _fallback_refresh_session(self, context: Dict) -> Dict:
        """세션 새로고침"""
        return {
            "status": "refresh",
            "message": "페이지를 새로고침해 주세요.",
            "auto_refresh": True
        }

    def _get_from_cache(self, key: str) -> Any:
        """캐시 조회"""
        try:
            if hasattr(st, 'session_state') and key in st.session_state:
                return st.session_state[key]
        except:
            pass
        return None


# 전역 자동 복구 인스턴스
auto_recovery = AutoRecovery()


# =============================================================================
# 3. 전역 에러 핸들러
# =============================================================================

def global_error_handler(
    show_user_message: bool = True,
    log_error: bool = True,
    auto_recover: bool = True,
    fallback_value: Any = None,
    error_category: ErrorCategory = None
):
    """전역 에러 핸들러 데코레이터

    Args:
        show_user_message: 사용자에게 메시지 표시
        log_error: 에러 로깅
        auto_recover: 자동 복구 시도
        fallback_value: 에러 시 반환할 기본값
        error_category: 에러 카테고리 (None이면 자동 감지)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # 성공 시 재시도 카운트 리셋
                if error_category:
                    auto_recovery.reset_retry_count(func.__name__, error_category)
                return result

            except Exception as e:
                # 에러 정보 수집
                error_info = UserFriendlyMessages.get_message(e)
                category = error_category or error_info.get("category", ErrorCategory.UNKNOWN)

                # 에러 로깅
                if log_error:
                    _log_error(e, func.__name__, args, kwargs, category)

                # 자동 복구 시도
                if auto_recover:
                    should_retry, wait_time = auto_recovery.should_retry(func.__name__, category)

                    if should_retry:
                        logger.info(f"자동 복구 시도: {func.__name__}, 대기 {wait_time}초")
                        time.sleep(wait_time)

                        try:
                            result = func(*args, **kwargs)
                            auto_recovery.reset_retry_count(func.__name__, category)
                            return result
                        except Exception as retry_error:
                            logger.warning(f"재시도 실패: {retry_error}")

                    # 폴백 실행
                    strategy = auto_recovery.get_strategy(category)
                    fallback_name = strategy.get("fallback")
                    if fallback_name:
                        fallback_result = auto_recovery.execute_fallback(
                            fallback_name,
                            {"feature": func.__name__}
                        )
                        if fallback_result:
                            if show_user_message:
                                st.info(fallback_result.get("message", ""))
                            return fallback_result

                # 사용자 메시지 표시
                if show_user_message:
                    _show_error_ui(e, error_info)

                return fallback_value

        return wrapper
    return decorator


def _log_error(error: Exception, func_name: str, args: tuple, kwargs: dict, category: ErrorCategory):
    """에러 로깅"""
    try:
        from error_monitor import get_error_logger, ErrorLevel
        error_logger = get_error_logger()

        error_logger.log_error(
            error=error,
            context={
                "function": func_name,
                "category": category.value,
                "args_preview": str(args)[:100],
                "kwargs_preview": str(kwargs)[:100]
            },
            level=ErrorLevel.ERROR,
            page=func_name
        )
    except ImportError:
        logger.error(f"[{func_name}] {type(error).__name__}: {error}")
    except Exception as log_error:
        logger.error(f"에러 로깅 실패: {log_error}")


def _show_error_ui(error: Exception, error_info: Dict):
    """에러 UI 표시"""
    title = error_info.get("title", "오류가 발생했습니다")
    message = error_info.get("message", "잠시 후 다시 시도해 주세요.")
    action = error_info.get("action", "retry")

    # Material 아이콘 사용
    icon_map = {
        "wifi_off": "signal_wifi_off",
        "cloud_off": "cloud_off",
        "lock": "lock",
        "error": "error",
        "warning": "warning",
        "schedule": "schedule",
    }
    icon = icon_map.get(error_info.get("icon", "error"), "error")

    # Streamlit 에러 표시
    with st.container():
        st.error(f"**{title}**")
        st.write(message)

        # 액션 버튼
        col1, col2 = st.columns(2)

        if action == "retry":
            if col1.button("다시 시도", key=f"retry_{id(error)}"):
                st.rerun()
        elif action == "refresh":
            if col1.button("새로고침", key=f"refresh_{id(error)}"):
                st.rerun()
        elif action == "contact":
            col1.markdown("[관리자 문의](mailto:support@flyready.kr)")

        if col2.button("홈으로", key=f"home_{id(error)}"):
            st.switch_page("홈.py")


# =============================================================================
# 4. 컨텍스트 매니저 기반 에러 핸들링
# =============================================================================

class SafeOperation:
    """안전한 작업 실행 컨텍스트 매니저

    Usage:
        with SafeOperation("데이터 로딩", show_error=True) as op:
            data = load_data()
            op.set_result(data)

        if op.success:
            use(op.result)
    """

    def __init__(
        self,
        operation_name: str,
        show_error: bool = True,
        auto_recover: bool = True,
        default_result: Any = None,
        category: ErrorCategory = None
    ):
        self.operation_name = operation_name
        self.show_error = show_error
        self.auto_recover = auto_recover
        self.default_result = default_result
        self.category = category

        self.success = False
        self.error = None
        self.result = default_result
        self._start_time = None

    def __enter__(self):
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self._start_time

        if exc_type is None:
            self.success = True
            logger.debug(f"[{self.operation_name}] 완료 ({elapsed:.2f}s)")
            return False

        # 에러 발생
        self.error = exc_val
        self.success = False

        # 에러 정보 수집
        error_info = UserFriendlyMessages.get_message(exc_val)
        category = self.category or error_info.get("category", ErrorCategory.UNKNOWN)

        # 로깅
        _log_error(exc_val, self.operation_name, (), {}, category)

        # 자동 복구 시도
        if self.auto_recover:
            strategy = auto_recovery.get_strategy(category)
            fallback_name = strategy.get("fallback")

            if fallback_name:
                fallback_result = auto_recovery.execute_fallback(
                    fallback_name,
                    {"feature": self.operation_name}
                )
                if fallback_result:
                    self.result = fallback_result
                    if self.show_error:
                        st.info(fallback_result.get("message", ""))

        # 사용자 메시지 표시
        if self.show_error:
            _show_error_ui(exc_val, error_info)

        # 예외 억제
        return True

    def set_result(self, result: Any):
        """결과 설정"""
        self.result = result


# =============================================================================
# 5. 에러 복구 유틸리티
# =============================================================================

def with_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    exponential_backoff: bool = True,
    exceptions: tuple = (Exception,),
    on_retry: Callable = None
):
    """재시도 데코레이터

    Args:
        max_retries: 최대 재시도 횟수
        delay: 기본 대기 시간
        exponential_backoff: 지수 백오프 사용
        exceptions: 재시도할 예외 타입
        on_retry: 재시도 시 호출할 콜백
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        wait_time = delay * (2 ** attempt if exponential_backoff else 1)
                        logger.warning(
                            f"재시도 {attempt + 1}/{max_retries}: {func.__name__}, "
                            f"대기 {wait_time:.1f}초, 오류: {e}"
                        )

                        if on_retry:
                            on_retry(attempt, e)

                        time.sleep(wait_time)
                    else:
                        logger.error(f"최대 재시도 초과: {func.__name__}")

            raise last_exception

        return wrapper
    return decorator


def safe_call(func: Callable, *args, default: Any = None, **kwargs) -> Any:
    """안전한 함수 호출

    Args:
        func: 실행할 함수
        default: 에러 시 반환값

    Returns:
        함수 결과 또는 기본값
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"safe_call 실패: {func.__name__}: {e}")
        return default


def chain_recovery(*funcs: Callable, default: Any = None) -> Any:
    """복구 체인 실행 (첫 번째 성공하는 함수 결과 반환)

    Args:
        funcs: 순서대로 시도할 함수들
        default: 모두 실패 시 반환값

    Usage:
        result = chain_recovery(
            lambda: api_call_primary(),
            lambda: api_call_secondary(),
            lambda: cached_data(),
            default=[]
        )
    """
    for i, func in enumerate(funcs):
        try:
            result = func()
            if result is not None:
                logger.info(f"복구 체인 성공 (시도 {i + 1}/{len(funcs)})")
                return result
        except Exception as e:
            logger.warning(f"복구 체인 실패 (시도 {i + 1}/{len(funcs)}): {e}")
            continue

    logger.warning("복구 체인 모두 실패, 기본값 반환")
    return default


# =============================================================================
# 6. 에러 리포트 생성
# =============================================================================

def generate_error_report(error: Exception, context: Dict = None) -> str:
    """상세 에러 리포트 생성 (관리자/디버깅용)"""
    now = datetime.now()

    report = [
        "=" * 60,
        "FlyReady Lab Error Report",
        "=" * 60,
        f"발생 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}",
        f"에러 타입: {type(error).__name__}",
        f"에러 메시지: {str(error)}",
        "",
        "--- 트레이스백 ---",
        traceback.format_exc(),
        "",
    ]

    if context:
        report.append("--- 컨텍스트 ---")
        for key, value in context.items():
            report.append(f"{key}: {value}")
        report.append("")

    # 환경 정보
    report.extend([
        "--- 환경 정보 ---",
        f"Python 버전: {__import__('sys').version}",
    ])

    try:
        import streamlit as st
        report.append(f"Streamlit 버전: {st.__version__}")
    except:
        pass

    report.append("=" * 60)

    return "\n".join(report)


# =============================================================================
# 초기화
# =============================================================================

def init_error_handling():
    """에러 핸들링 시스템 초기화"""
    try:
        # 기본 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 세션 상태에 에러 핸들링 초기화 표시
        if hasattr(st, 'session_state'):
            if 'error_handling_initialized' not in st.session_state:
                st.session_state.error_handling_initialized = True
                st.session_state.error_history = []
                logger.info("에러 핸들링 시스템 초기화 완료")

        return True
    except Exception as e:
        logger.error(f"에러 핸들링 초기화 실패: {e}")
        return False


# =============================================================================
# 모듈 테스트
# =============================================================================

if __name__ == "__main__":
    print("=== Enhanced Error Handler Test ===")

    # 테스트 1: 사용자 친화적 메시지
    print("\n1. 사용자 친화적 메시지 테스트")
    test_errors = [
        ConnectionError("Failed to connect"),
        TimeoutError("Request timed out"),
        ValueError("Invalid input"),
        FileNotFoundError("File not found"),
    ]

    for error in test_errors:
        info = UserFriendlyMessages.get_message(error)
        print(f"   {type(error).__name__}: {info['title']}")

    # 테스트 2: 자동 복구
    print("\n2. 자동 복구 테스트")
    ar = AutoRecovery()

    should_retry, wait = ar.should_retry("test_func", ErrorCategory.NETWORK)
    print(f"   첫 번째 시도 - 재시도: {should_retry}, 대기: {wait}초")

    should_retry, wait = ar.should_retry("test_func", ErrorCategory.NETWORK)
    print(f"   두 번째 시도 - 재시도: {should_retry}, 대기: {wait}초")

    # 테스트 3: with_retry 데코레이터
    print("\n3. 재시도 데코레이터 테스트")

    attempt_count = 0

    @with_retry(max_retries=2, delay=0.1)
    def flaky_function():
        global attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ConnectionError("Temporary failure")
        return "success"

    try:
        result = flaky_function()
        print(f"   결과: {result}, 시도 횟수: {attempt_count}")
    except Exception as e:
        print(f"   실패: {e}")

    print("\n모듈 준비 완료!")

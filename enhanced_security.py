# enhanced_security.py
# FlyReady Lab - 엔터프라이즈급 보안 강화 모듈
# Phase A1: 보안 500% 강화

import os
import re
import json
import hmac
import base64
import hashlib
import secrets
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Callable
from functools import wraps
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# =============================================================================
# 1. API 키 암호화/복호화 시스템
# =============================================================================

class SecureKeyManager:
    """API 키 암호화 관리자

    API 키를 안전하게 암호화하여 저장하고,
    런타임에만 복호화하여 사용합니다.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._encryption_key = None
        self._fernet = None
        self._key_cache = {}
        self._cache_ttl = 300  # 5분 캐시
        self._initialized = True
        self._init_encryption()

    def _init_encryption(self):
        """암호화 키 초기화"""
        # 마스터 키 생성 (환경변수 또는 머신 고유값 기반)
        master_seed = os.environ.get('FLYREADY_MASTER_KEY', '')

        if not master_seed:
            # 머신 고유값 + 프로젝트 경로 조합
            machine_id = self._get_machine_id()
            project_path = str(Path(__file__).parent.absolute())
            master_seed = f"{machine_id}:{project_path}"

        # PBKDF2로 암호화 키 도출
        salt = b'flyready_secure_salt_v1'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_seed.encode()))
        self._fernet = Fernet(key)

    def _get_machine_id(self) -> str:
        """머신 고유 ID 생성"""
        try:
            import platform
            import uuid

            machine_info = [
                platform.node(),
                platform.machine(),
                str(uuid.getnode()),
            ]
            return hashlib.sha256(':'.join(machine_info).encode()).hexdigest()[:32]
        except:
            return 'default_machine_id'

    def encrypt_key(self, api_key: str) -> str:
        """API 키 암호화"""
        if not api_key:
            return ''

        try:
            encrypted = self._fernet.encrypt(api_key.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"키 암호화 실패: {e}")
            return ''

    def decrypt_key(self, encrypted_key: str) -> str:
        """API 키 복호화"""
        if not encrypted_key:
            return ''

        # 캐시 확인
        cache_key = hashlib.md5(encrypted_key.encode()).hexdigest()
        if cache_key in self._key_cache:
            cached_value, cached_time = self._key_cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self._cache_ttl:
                return cached_value

        try:
            decoded = base64.urlsafe_b64decode(encrypted_key.encode())
            decrypted = self._fernet.decrypt(decoded).decode()

            # 캐시 저장
            self._key_cache[cache_key] = (decrypted, datetime.now())

            return decrypted
        except Exception as e:
            logger.error(f"키 복호화 실패: {e}")
            return ''

    def clear_cache(self):
        """키 캐시 삭제"""
        self._key_cache.clear()

    def rotate_master_key(self, new_master_key: str):
        """마스터 키 교체 (모든 키 재암호화 필요)"""
        logger.warning("마스터 키 교체 - 모든 API 키 재암호화 필요")
        self._key_cache.clear()

        old_fernet = self._fernet

        # 새 키로 초기화
        salt = b'flyready_secure_salt_v1'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(new_master_key.encode()))
        self._fernet = Fernet(key)

        return old_fernet, self._fernet


# 전역 키 관리자
secure_key_manager = SecureKeyManager()


# =============================================================================
# 2. SQL Injection 방지
# =============================================================================

class SQLInjectionPrevention:
    """SQL Injection 공격 방지"""

    # 위험한 SQL 패턴
    DANGEROUS_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|EXEC|EXECUTE)\b)",
        r"(--|\#|/\*|\*/)",  # SQL 주석
        r"(\bOR\b\s+\d+\s*=\s*\d+)",  # OR 1=1
        r"(\bAND\b\s+\d+\s*=\s*\d+)",  # AND 1=1
        r"(\bUNION\b.*\bSELECT\b)",  # UNION SELECT
        r"(;.*\b(DROP|DELETE|UPDATE|INSERT)\b)",  # 다중 쿼리
        r"(\bWHERE\b\s+\d+\s*=\s*\d+)",  # WHERE 1=1
        r"(\bHAVING\b\s+\d+\s*=\s*\d+)",  # HAVING 1=1
        r"(\'|\"|`)\s*(;|--)",  # 따옴표 후 세미콜론/주석
        r"(\bCHAR\b\s*\()",  # CHAR() 함수
        r"(\bCONCAT\b\s*\()",  # CONCAT() 함수
        r"(\bCONVERT\b\s*\()",  # CONVERT() 함수
        r"(0x[0-9a-fA-F]+)",  # 16진수 값
    ]

    # 컴파일된 패턴
    _compiled_patterns = None

    @classmethod
    def _get_patterns(cls):
        if cls._compiled_patterns is None:
            cls._compiled_patterns = [
                re.compile(p, re.IGNORECASE)
                for p in cls.DANGEROUS_PATTERNS
            ]
        return cls._compiled_patterns

    @classmethod
    def check_sql_injection(cls, text: str) -> Tuple[bool, List[str]]:
        """SQL Injection 공격 패턴 탐지

        Args:
            text: 검사할 텍스트

        Returns:
            (is_safe, detected_patterns)
        """
        if not text:
            return True, []

        detected = []
        for pattern in cls._get_patterns():
            if pattern.search(text):
                detected.append(pattern.pattern)

        return len(detected) == 0, detected

    @classmethod
    def sanitize_for_sql(cls, text: str, allow_quotes: bool = False) -> str:
        """SQL에 안전한 문자열로 변환

        Args:
            text: 원본 텍스트
            allow_quotes: 따옴표 허용 여부

        Returns:
            살균된 텍스트
        """
        if not text:
            return ''

        result = str(text)

        # 위험한 문자 제거
        dangerous_chars = [';', '--', '/*', '*/', '#']
        for char in dangerous_chars:
            result = result.replace(char, '')

        # 따옴표 처리
        if not allow_quotes:
            result = result.replace("'", "''").replace('"', '""')

        # 백슬래시 이스케이프
        result = result.replace('\\', '\\\\')

        return result

    @classmethod
    def escape_like_pattern(cls, text: str) -> str:
        """LIKE 패턴 이스케이프"""
        if not text:
            return ''

        # LIKE 특수문자 이스케이프
        special_chars = ['%', '_', '[', ']', '^']
        result = str(text)

        for char in special_chars:
            result = result.replace(char, f'\\{char}')

        return result


def sql_safe(func):
    """SQL Injection 방지 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 모든 문자열 인자 검사
        for i, arg in enumerate(args):
            if isinstance(arg, str):
                is_safe, patterns = SQLInjectionPrevention.check_sql_injection(arg)
                if not is_safe:
                    logger.warning(f"SQL Injection 시도 탐지: {patterns}")
                    raise ValueError("잠재적 SQL Injection 공격이 감지되었습니다.")

        for key, value in kwargs.items():
            if isinstance(value, str):
                is_safe, patterns = SQLInjectionPrevention.check_sql_injection(value)
                if not is_safe:
                    logger.warning(f"SQL Injection 시도 탐지 ({key}): {patterns}")
                    raise ValueError("잠재적 SQL Injection 공격이 감지되었습니다.")

        return func(*args, **kwargs)
    return wrapper


# =============================================================================
# 3. 경로 탐색 공격 방지
# =============================================================================

class PathTraversalPrevention:
    """경로 탐색(Path Traversal) 공격 방지"""

    DANGEROUS_PATTERNS = [
        r'\.\./',
        r'\.\.',
        r'\.\.\\',
        r'%2e%2e',
        r'%252e%252e',
        r'\.%00',
        r'%00',
    ]

    @classmethod
    def is_safe_path(cls, path: str, base_dir: str = None) -> Tuple[bool, str]:
        """경로 안전성 검사

        Args:
            path: 검사할 경로
            base_dir: 허용된 기본 디렉토리

        Returns:
            (is_safe, reason)
        """
        if not path:
            return False, "경로가 비어있습니다."

        # 위험 패턴 검사
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                return False, f"위험한 경로 패턴 감지: {pattern}"

        # 절대 경로 검사
        if base_dir:
            try:
                base_path = Path(base_dir).resolve()
                target_path = Path(path).resolve()

                # 기본 디렉토리 내에 있는지 확인
                if not str(target_path).startswith(str(base_path)):
                    return False, "허용된 디렉토리 외부 접근 시도"
            except Exception as e:
                return False, f"경로 검증 오류: {e}"

        return True, "안전"

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """파일명 살균"""
        if not filename:
            return ''

        # 위험한 문자 제거
        dangerous_chars = ['/', '\\', '..', ':', '*', '?', '"', '<', '>', '|', '\x00']
        result = str(filename)

        for char in dangerous_chars:
            result = result.replace(char, '_')

        # 앞뒤 공백 및 점 제거
        result = result.strip(' .')

        # 빈 문자열 방지
        if not result:
            result = 'unnamed'

        return result

    @classmethod
    def get_safe_upload_path(
        cls,
        filename: str,
        upload_dir: str,
        allowed_extensions: List[str] = None
    ) -> Tuple[bool, str, str]:
        """안전한 업로드 경로 생성

        Returns:
            (is_valid, safe_path, error_message)
        """
        # 파일명 살균
        safe_filename = cls.sanitize_filename(filename)

        # 확장자 검사
        if allowed_extensions:
            ext = Path(safe_filename).suffix.lower().lstrip('.')
            if ext not in [e.lower().lstrip('.') for e in allowed_extensions]:
                return False, '', f"허용되지 않은 파일 형식: {ext}"

        # 고유 파일명 생성 (충돌 방지)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = secrets.token_hex(4)

        name_parts = safe_filename.rsplit('.', 1)
        if len(name_parts) == 2:
            unique_filename = f"{name_parts[0]}_{timestamp}_{random_suffix}.{name_parts[1]}"
        else:
            unique_filename = f"{safe_filename}_{timestamp}_{random_suffix}"

        # 경로 조합
        safe_path = Path(upload_dir) / unique_filename

        # 최종 경로 검증
        is_safe, reason = cls.is_safe_path(str(safe_path), upload_dir)
        if not is_safe:
            return False, '', reason

        return True, str(safe_path), ''


# =============================================================================
# 4. 세션 보안 강화
# =============================================================================

class SecureSessionManager:
    """강화된 세션 관리"""

    SESSION_TIMEOUT = timedelta(hours=4)  # 세션 타임아웃
    SESSION_ROTATION_INTERVAL = timedelta(minutes=30)  # 토큰 갱신 주기
    MAX_CONCURRENT_SESSIONS = 3  # 최대 동시 세션 수

    @staticmethod
    def generate_session_token() -> str:
        """보안 세션 토큰 생성"""
        # 256비트 랜덤 토큰
        token = secrets.token_urlsafe(32)

        # 타임스탬프 포함 (검증용) - 정수로 저장
        timestamp = int(datetime.now().timestamp())

        # HMAC 서명 (정수 타임스탬프 사용)
        secret = os.environ.get('SESSION_SECRET', 'default_session_secret')
        signature = hmac.new(
            secret.encode(),
            f"{token}:{timestamp}".encode(),
            hashlib.sha256
        ).hexdigest()[:16]

        return f"{token}.{timestamp}.{signature}"

    @staticmethod
    def validate_session_token(token: str) -> Tuple[bool, str]:
        """세션 토큰 검증"""
        if not token:
            return False, "토큰이 없습니다."

        try:
            parts = token.split('.')
            if len(parts) != 3:
                return False, "잘못된 토큰 형식"

            token_value, timestamp_str, signature = parts
            timestamp = int(timestamp_str)

            # 서명 검증
            secret = os.environ.get('SESSION_SECRET', 'default_session_secret')
            expected_signature = hmac.new(
                secret.encode(),
                f"{token_value}:{timestamp}".encode(),
                hashlib.sha256
            ).hexdigest()[:16]

            if not hmac.compare_digest(signature, expected_signature):
                return False, "토큰 서명 불일치"

            # 만료 확인
            token_time = datetime.fromtimestamp(timestamp)
            if datetime.now() - token_time > SecureSessionManager.SESSION_TIMEOUT:
                return False, "세션이 만료되었습니다."

            return True, "유효"

        except Exception as e:
            return False, f"토큰 검증 오류: {e}"

    @staticmethod
    def should_rotate_token(token: str) -> bool:
        """토큰 갱신 필요 여부"""
        if not token:
            return True

        try:
            parts = token.split('.')
            if len(parts) != 3:
                return True

            timestamp = int(parts[1])
            token_time = datetime.fromtimestamp(timestamp)

            return datetime.now() - token_time > SecureSessionManager.SESSION_ROTATION_INTERVAL

        except:
            return True

    @staticmethod
    def get_session_fingerprint() -> str:
        """세션 핑거프린트 생성 (세션 고정 공격 방지)"""
        try:
            import streamlit as st

            # 사용 가능한 정보로 핑거프린트 생성
            components = []

            # 세션 ID가 있으면 사용
            if hasattr(st, 'session_state'):
                session_id = getattr(st.session_state, '_session_id', str(id(st.session_state)))
                components.append(session_id)

            # 랜덤 요소 추가 (첫 생성 시에만)
            if not components:
                components.append(secrets.token_hex(16))

            fingerprint_data = ':'.join(components)
            return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]

        except:
            return secrets.token_hex(16)


# =============================================================================
# 5. 강화된 보안 헤더
# =============================================================================

class SecurityHeaders:
    """보안 HTTP 헤더 관리"""

    @staticmethod
    def get_csp_policy(
        allow_inline_styles: bool = True,
        allow_inline_scripts: bool = False,
        custom_sources: Dict[str, List[str]] = None
    ) -> str:
        """Content Security Policy 생성"""

        directives = {
            'default-src': ["'self'"],
            'script-src': ["'self'", "https://cdn.jsdelivr.net"],
            'style-src': ["'self'", "https://fonts.googleapis.com"],
            'font-src': ["'self'", "https://fonts.gstatic.com"],
            'img-src': ["'self'", "data:", "https:"],
            'connect-src': ["'self'", "https://api.openai.com", "https://api.d-id.com"],
            'frame-ancestors': ["'self'"],
            'form-action': ["'self'"],
            'base-uri': ["'self'"],
        }

        if allow_inline_styles:
            directives['style-src'].append("'unsafe-inline'")

        if allow_inline_scripts:
            # 가능하면 nonce 사용 권장
            directives['script-src'].append("'unsafe-inline'")

        if custom_sources:
            for directive, sources in custom_sources.items():
                if directive in directives:
                    directives[directive].extend(sources)
                else:
                    directives[directive] = sources

        policy_parts = [
            f"{directive} {' '.join(sources)}"
            for directive, sources in directives.items()
        ]

        return "; ".join(policy_parts)

    @staticmethod
    def render_security_meta_tags(include_csp: bool = True) -> str:
        """보안 메타 태그 HTML 생성"""

        tags = [
            '<meta http-equiv="X-Content-Type-Options" content="nosniff">',
            '<meta http-equiv="X-Frame-Options" content="SAMEORIGIN">',
            '<meta http-equiv="X-XSS-Protection" content="1; mode=block">',
            '<meta name="referrer" content="strict-origin-when-cross-origin">',
            '<meta http-equiv="Permissions-Policy" content="camera=(), microphone=(), geolocation=()">',
        ]

        if include_csp:
            csp = SecurityHeaders.get_csp_policy(allow_inline_styles=True)
            tags.append(f'<meta http-equiv="Content-Security-Policy" content="{csp}">')

        return '\n'.join(tags)


# =============================================================================
# 6. 감사 로그 시스템
# =============================================================================

class AuditLogger:
    """감사 로그 시스템"""

    _instance = None
    _lock = threading.Lock()

    LOG_FILE = Path(__file__).parent / 'logs' / 'audit.log'
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_LOG_FILES = 5

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._ensure_log_directory()

    def _ensure_log_directory(self):
        """로그 디렉토리 생성"""
        self.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _rotate_logs(self):
        """로그 로테이션"""
        if not self.LOG_FILE.exists():
            return

        if self.LOG_FILE.stat().st_size < self.MAX_LOG_SIZE:
            return

        # 기존 로그 파일 이동
        for i in range(self.MAX_LOG_FILES - 1, 0, -1):
            old_file = self.LOG_FILE.with_suffix(f'.log.{i}')
            new_file = self.LOG_FILE.with_suffix(f'.log.{i + 1}')

            if old_file.exists():
                if i == self.MAX_LOG_FILES - 1:
                    old_file.unlink()
                else:
                    old_file.rename(new_file)

        # 현재 로그 파일 이동
        self.LOG_FILE.rename(self.LOG_FILE.with_suffix('.log.1'))

    def log(
        self,
        event_type: str,
        action: str,
        user: str = None,
        details: Dict[str, Any] = None,
        severity: str = 'INFO',
        ip_address: str = None
    ):
        """감사 로그 기록

        Args:
            event_type: 이벤트 유형 (AUTH, ACCESS, DATA, SECURITY, ERROR)
            action: 수행된 작업
            user: 사용자 식별자
            details: 추가 상세 정보
            severity: 심각도 (INFO, WARNING, ERROR, CRITICAL)
            ip_address: IP 주소
        """
        self._rotate_logs()

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'action': action,
            'user': user or 'anonymous',
            'severity': severity,
            'ip_address': ip_address,
            'details': self._sanitize_details(details or {}),
        }

        try:
            with open(self.LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"감사 로그 기록 실패: {e}")

        # 심각한 이벤트는 표준 로거에도 기록
        if severity in ('ERROR', 'CRITICAL'):
            logger.warning(f"[AUDIT] {event_type}: {action} - {details}")

    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """민감 정보 마스킹"""
        sensitive_keys = {
            'password', 'api_key', 'secret', 'token', 'key',
            'credential', 'auth', 'session'
        }

        result = {}
        for key, value in details.items():
            key_lower = key.lower()

            if any(sk in key_lower for sk in sensitive_keys):
                if isinstance(value, str) and len(value) > 8:
                    result[key] = value[:4] + '****' + value[-4:]
                else:
                    result[key] = '****'
            elif isinstance(value, dict):
                result[key] = self._sanitize_details(value)
            else:
                result[key] = value

        return result

    def get_recent_logs(
        self,
        count: int = 100,
        event_type: str = None,
        severity: str = None
    ) -> List[Dict]:
        """최근 로그 조회"""
        logs = []

        try:
            if not self.LOG_FILE.exists():
                return logs

            with open(self.LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in reversed(lines):
                if len(logs) >= count:
                    break

                try:
                    entry = json.loads(line.strip())

                    if event_type and entry.get('event_type') != event_type:
                        continue

                    if severity and entry.get('severity') != severity:
                        continue

                    logs.append(entry)
                except:
                    continue

        except Exception as e:
            logger.error(f"로그 조회 실패: {e}")

        return logs


# 전역 감사 로거
audit_logger = AuditLogger()


# =============================================================================
# 7. 통합 보안 유틸리티 함수
# =============================================================================

def secure_input(
    text: str,
    max_length: int = 5000,
    check_sql: bool = True,
    check_xss: bool = True
) -> Tuple[bool, str, List[str]]:
    """통합 입력 검증

    Args:
        text: 입력 텍스트
        max_length: 최대 길이
        check_sql: SQL Injection 검사
        check_xss: XSS 검사

    Returns:
        (is_safe, sanitized_text, warnings)
    """
    warnings = []

    if not text:
        return True, '', warnings

    # 길이 제한
    text = str(text)
    if len(text) > max_length:
        text = text[:max_length]
        warnings.append(f"입력이 {max_length}자로 잘렸습니다.")

    # SQL Injection 검사
    if check_sql:
        is_safe, patterns = SQLInjectionPrevention.check_sql_injection(text)
        if not is_safe:
            warnings.append("SQL Injection 패턴 감지")
            text = SQLInjectionPrevention.sanitize_for_sql(text)

    # XSS 검사 (기존 security_utils 활용)
    if check_xss:
        try:
            from security_utils import sanitize_html
            text = sanitize_html(text, allow_tags=False)
        except ImportError:
            # 기본 HTML 이스케이프
            import html
            text = html.escape(text)

    return len(warnings) == 0, text, warnings


def validate_and_log_access(
    resource: str,
    user: str = None,
    action: str = 'access',
    required_role: str = None
) -> bool:
    """리소스 접근 검증 및 로깅"""
    try:
        import streamlit as st

        # 인증 확인
        if required_role:
            from security_utils import SecureAuth
            if not SecureAuth.has_role(required_role):
                audit_logger.log(
                    event_type='ACCESS',
                    action=f'{action}_denied',
                    user=user,
                    details={'resource': resource, 'required_role': required_role},
                    severity='WARNING'
                )
                return False

        # 접근 로그
        audit_logger.log(
            event_type='ACCESS',
            action=action,
            user=user,
            details={'resource': resource},
            severity='INFO'
        )

        return True

    except Exception as e:
        logger.error(f"접근 검증 오류: {e}")
        return False


# =============================================================================
# 8. 보안 설정 초기화
# =============================================================================

def init_security():
    """보안 시스템 초기화"""
    try:
        import streamlit as st

        # 세션 상태 초기화
        if 'security_initialized' not in st.session_state:
            st.session_state.security_initialized = True
            st.session_state.session_fingerprint = SecureSessionManager.get_session_fingerprint()
            st.session_state.session_token = SecureSessionManager.generate_session_token()

            audit_logger.log(
                event_type='AUTH',
                action='session_created',
                details={'fingerprint': st.session_state.session_fingerprint[:8] + '...'}
            )

        # 세션 토큰 갱신 확인
        if SecureSessionManager.should_rotate_token(
            st.session_state.get('session_token', '')
        ):
            old_token = st.session_state.get('session_token', '')[:8]
            st.session_state.session_token = SecureSessionManager.generate_session_token()

            audit_logger.log(
                event_type='AUTH',
                action='token_rotated',
                details={'old_token_prefix': old_token}
            )

        logger.info("보안 시스템 초기화 완료")
        return True

    except Exception as e:
        logger.error(f"보안 시스템 초기화 실패: {e}")
        return False


# =============================================================================
# 모듈 테스트
# =============================================================================

if __name__ == "__main__":
    print("=== Enhanced Security Module ===")
    print("\n1. API 키 암호화 테스트")
    test_key = "sk-test1234567890abcdef"
    encrypted = secure_key_manager.encrypt_key(test_key)
    decrypted = secure_key_manager.decrypt_key(encrypted)
    print(f"   원본: {test_key}")
    print(f"   암호화: {encrypted[:20]}...")
    print(f"   복호화: {decrypted}")
    print(f"   일치: {test_key == decrypted}")

    print("\n2. SQL Injection 검사 테스트")
    test_inputs = [
        "normal text",
        "SELECT * FROM users",
        "1; DROP TABLE users--",
        "' OR '1'='1",
    ]
    for inp in test_inputs:
        is_safe, patterns = SQLInjectionPrevention.check_sql_injection(inp)
        status = "안전" if is_safe else "위험"
        print(f"   '{inp[:30]}...' -> {status}")

    print("\n3. 경로 검증 테스트")
    test_paths = [
        "/uploads/file.txt",
        "../../../etc/passwd",
        "file%00.txt",
    ]
    for path in test_paths:
        is_safe, reason = PathTraversalPrevention.is_safe_path(path)
        status = "안전" if is_safe else f"위험: {reason}"
        print(f"   '{path}' -> {status}")

    print("\n4. 세션 토큰 테스트")
    token = SecureSessionManager.generate_session_token()
    is_valid, msg = SecureSessionManager.validate_session_token(token)
    print(f"   토큰: {token[:20]}...")
    print(f"   유효: {is_valid} ({msg})")

    print("\n모듈 준비 완료!")

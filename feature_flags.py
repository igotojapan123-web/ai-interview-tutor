# feature_flags.py
# Feature Flags 시스템 - 기능 토글 및 점진적 롤아웃

import json
import hashlib
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
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

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
FLAGS_FILE = DATA_DIR / "feature_flags.json"


# ============================================================
# 데이터 클래스
# ============================================================

@dataclass
class FeatureFlag:
    """Feature Flag 정의"""
    name: str
    description: str
    enabled: bool = False
    rollout_percentage: float = 100.0  # 0-100
    user_whitelist: List[str] = None   # 항상 활성화할 사용자
    user_blacklist: List[str] = None   # 항상 비활성화할 사용자
    conditions: Dict[str, Any] = None  # 추가 조건
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if self.user_whitelist is None:
            self.user_whitelist = []
        if self.user_blacklist is None:
            self.user_blacklist = []
        if self.conditions is None:
            self.conditions = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()


# ============================================================
# Feature Flags 관리자
# ============================================================

class FeatureFlagsManager:
    """Feature Flags 관리 클래스"""

    def __init__(self):
        self._lock = threading.Lock()
        self._flags: Dict[str, FeatureFlag] = {}
        self._evaluation_cache: Dict[str, Dict[str, bool]] = {}
        self._load_flags()

    def _load_flags(self) -> None:
        """저장된 플래그 로드"""
        try:
            if FLAGS_FILE.exists():
                with open(FLAGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for flag_data in data.get("flags", []):
                        flag = FeatureFlag(**flag_data)
                        self._flags[flag.name] = flag
        except Exception as e:
            logger.error(f"Feature Flags 로드 실패: {e}")

    def _save_flags(self) -> None:
        """플래그 저장"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(FLAGS_FILE, "w", encoding="utf-8") as f:
                flags_data = {"flags": [asdict(f) for f in self._flags.values()]}
                json.dump(flags_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Feature Flags 저장 실패: {e}")

    # -------------------------------------------------------------------------
    # 플래그 관리
    # -------------------------------------------------------------------------

    def create_flag(
        self,
        name: str,
        description: str,
        enabled: bool = False,
        rollout_percentage: float = 100.0
    ) -> FeatureFlag:
        """새 플래그 생성"""
        with self._lock:
            if name in self._flags:
                raise ValueError(f"플래그가 이미 존재합니다: {name}")

            flag = FeatureFlag(
                name=name,
                description=description,
                enabled=enabled,
                rollout_percentage=rollout_percentage
            )
            self._flags[name] = flag
            self._save_flags()
            logger.info(f"Feature Flag 생성: {name}")
            return flag

    def update_flag(
        self,
        name: str,
        enabled: bool = None,
        rollout_percentage: float = None,
        user_whitelist: List[str] = None,
        user_blacklist: List[str] = None
    ) -> Optional[FeatureFlag]:
        """플래그 업데이트"""
        with self._lock:
            if name not in self._flags:
                return None

            flag = self._flags[name]
            if enabled is not None:
                flag.enabled = enabled
            if rollout_percentage is not None:
                flag.rollout_percentage = rollout_percentage
            if user_whitelist is not None:
                flag.user_whitelist = user_whitelist
            if user_blacklist is not None:
                flag.user_blacklist = user_blacklist
            flag.updated_at = datetime.now().isoformat()

            # 캐시 무효화
            if name in self._evaluation_cache:
                del self._evaluation_cache[name]

            self._save_flags()
            logger.info(f"Feature Flag 업데이트: {name}")
            return flag

    def delete_flag(self, name: str) -> bool:
        """플래그 삭제"""
        with self._lock:
            if name not in self._flags:
                return False

            del self._flags[name]
            if name in self._evaluation_cache:
                del self._evaluation_cache[name]
            self._save_flags()
            logger.info(f"Feature Flag 삭제: {name}")
            return True

    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        """플래그 조회"""
        return self._flags.get(name)

    def list_flags(self) -> List[FeatureFlag]:
        """모든 플래그 목록"""
        return list(self._flags.values())

    # -------------------------------------------------------------------------
    # 플래그 평가
    # -------------------------------------------------------------------------

    def is_enabled(
        self,
        flag_name: str,
        user_id: str = None,
        context: Dict[str, Any] = None
    ) -> bool:
        """
        플래그 활성화 여부 확인

        Args:
            flag_name: 플래그 이름
            user_id: 사용자 ID (점진적 롤아웃용)
            context: 추가 컨텍스트

        Returns:
            활성화 여부
        """
        with self._lock:
            flag = self._flags.get(flag_name)
            if not flag:
                return False

            # 기본적으로 비활성화
            if not flag.enabled:
                return False

            # 화이트리스트 확인
            if user_id and user_id in flag.user_whitelist:
                return True

            # 블랙리스트 확인
            if user_id and user_id in flag.user_blacklist:
                return False

            # 점진적 롤아웃
            if flag.rollout_percentage < 100:
                if not user_id:
                    return False
                if not self._is_in_rollout(flag_name, user_id, flag.rollout_percentage):
                    return False

            # 조건 확인
            if flag.conditions and context:
                if not self._evaluate_conditions(flag.conditions, context):
                    return False

            return True

    def _is_in_rollout(self, flag_name: str, user_id: str, percentage: float) -> bool:
        """점진적 롤아웃 확인 (일관된 해시 기반)"""
        hash_input = f"{flag_name}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        user_percentage = hash_value % 10000 / 100.0
        return user_percentage < percentage

    def _evaluate_conditions(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """조건 평가"""
        for key, expected in conditions.items():
            actual = context.get(key)
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
        return True

    # -------------------------------------------------------------------------
    # 편의 메서드
    # -------------------------------------------------------------------------

    def enable(self, flag_name: str) -> None:
        """플래그 활성화"""
        self.update_flag(flag_name, enabled=True)

    def disable(self, flag_name: str) -> None:
        """플래그 비활성화"""
        self.update_flag(flag_name, enabled=False)

    def set_rollout(self, flag_name: str, percentage: float) -> None:
        """롤아웃 퍼센트 설정"""
        self.update_flag(flag_name, rollout_percentage=percentage)


# 전역 인스턴스
feature_flags = FeatureFlagsManager()


# ============================================================
# 데코레이터
# ============================================================

def feature_flag(flag_name: str, default: Any = None, get_user_id: Callable = None):
    """
    Feature Flag 데코레이터

    Usage:
        @feature_flag("new_ui")
        def render_page(user_id):
            return new_ui()

        # 비활성화시 기본값 반환
        @feature_flag("beta_feature", default="old_result")
        def get_data():
            return new_data()
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 사용자 ID 추출
            user_id = None
            if get_user_id:
                user_id = get_user_id(*args, **kwargs)
            elif args:
                user_id = str(args[0])
            else:
                user_id = kwargs.get("user_id")

            # 플래그 확인
            if feature_flags.is_enabled(flag_name, user_id):
                return func(*args, **kwargs)
            else:
                logger.debug(f"Feature flag disabled: {flag_name}")
                return default

        return wrapper
    return decorator


def require_flag(flag_name: str):
    """
    플래그 필수 데코레이터 (비활성화시 예외 발생)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = kwargs.get("user_id")
            if not feature_flags.is_enabled(flag_name, user_id):
                raise FeatureDisabledException(f"기능이 비활성화되어 있습니다: {flag_name}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


class FeatureDisabledException(Exception):
    """기능 비활성화 예외"""
    pass


# ============================================================
# 간편 함수
# ============================================================

def is_enabled(flag_name: str, user_id: str = None) -> bool:
    """플래그 활성화 확인"""
    return feature_flags.is_enabled(flag_name, user_id)


def create_flag(name: str, description: str, enabled: bool = False) -> FeatureFlag:
    """플래그 생성"""
    return feature_flags.create_flag(name, description, enabled)


def enable_flag(name: str) -> None:
    """플래그 활성화"""
    feature_flags.enable(name)


def disable_flag(name: str) -> None:
    """플래그 비활성화"""
    feature_flags.disable(name)


def set_rollout(name: str, percentage: float) -> None:
    """롤아웃 퍼센트 설정"""
    feature_flags.set_rollout(name, percentage)


# ============================================================
# 기본 플래그 초기화
# ============================================================

def initialize_default_flags() -> None:
    """기본 Feature Flags 초기화"""
    default_flags = [
        ("new_voice_interview", "새로운 음성 면접 UI", False),
        ("ai_feedback_v2", "개선된 AI 피드백 시스템", False),
        ("video_analysis", "실시간 비디오 분석", False),
        ("group_interview_beta", "그룹 면접 베타", False),
        ("dark_mode", "다크 모드", True),
        ("analytics_dashboard", "분석 대시보드", True),
        ("export_feature", "데이터 내보내기", True),
    ]

    for name, description, enabled in default_flags:
        try:
            feature_flags.create_flag(name, description, enabled)
        except ValueError:
            pass  # 이미 존재


# ============================================================
# Streamlit 컴포넌트
# ============================================================

def render_feature_flags_admin():
    """Feature Flags 관리 UI"""
    import streamlit as st

    st.markdown("### Feature Flags 관리")

    flags = feature_flags.list_flags()

    for flag in flags:
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.text(f"{flag.name}: {flag.description}")

        with col2:
            new_state = st.checkbox(
                "활성화",
                value=flag.enabled,
                key=f"flag_{flag.name}"
            )
            if new_state != flag.enabled:
                feature_flags.update_flag(flag.name, enabled=new_state)
                st.rerun()

        with col3:
            st.text(f"{flag.rollout_percentage}%")


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=== Feature Flags System ===")

    # 기본 플래그 초기화
    initialize_default_flags()

    # 테스트
    print("\n플래그 목록:")
    for flag in feature_flags.list_flags():
        status = "ON" if flag.enabled else "OFF"
        print(f"  {flag.name}: {status} ({flag.rollout_percentage}%)")

    print("\nReady!")

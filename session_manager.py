# session_manager.py
# 세션 타임아웃 및 관리 시스템

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import streamlit as st

try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# ============================================================
# 설정
# ============================================================

DEFAULT_TIMEOUT_MINUTES = 30  # 기본 세션 타임아웃 (30분)
WARNING_BEFORE_MINUTES = 5   # 타임아웃 5분 전 경고
CHECK_INTERVAL_SECONDS = 60  # 체크 간격 (1분)


# ============================================================
# 세션 타임아웃 관리
# ============================================================

class SessionManager:
    """세션 타임아웃 관리 클래스"""

    def __init__(self, timeout_minutes: int = DEFAULT_TIMEOUT_MINUTES):
        self.timeout_minutes = timeout_minutes
        self.warning_minutes = WARNING_BEFORE_MINUTES

    def init_session(self, session_state) -> None:
        """세션 초기화 (최초 접속 시)"""
        if 'session_last_activity' not in session_state:
            session_state.session_last_activity = time.time()
            session_state.session_started_at = datetime.now().isoformat()
            session_state.session_timeout_minutes = self.timeout_minutes
            logger.info(f"새 세션 시작: timeout={self.timeout_minutes}분")

    def update_activity(self, session_state) -> None:
        """활동 시간 갱신 (사용자 액션 시 호출)"""
        session_state.session_last_activity = time.time()

    def check_timeout(self, session_state) -> Dict[str, Any]:
        """
        타임아웃 체크

        Returns:
            {
                'expired': bool,      # 만료 여부
                'warning': bool,      # 경고 필요 여부
                'remaining_seconds': int,  # 남은 시간 (초)
                'remaining_minutes': int   # 남은 시간 (분)
            }
        """
        if 'session_last_activity' not in session_state:
            self.init_session(session_state)
            return {'expired': False, 'warning': False, 'remaining_seconds': self.timeout_minutes * 60, 'remaining_minutes': self.timeout_minutes}

        last_activity = session_state.session_last_activity
        elapsed = time.time() - last_activity
        timeout_seconds = self.timeout_minutes * 60
        remaining = timeout_seconds - elapsed

        result = {
            'expired': remaining <= 0,
            'warning': 0 < remaining <= (self.warning_minutes * 60),
            'remaining_seconds': max(0, int(remaining)),
            'remaining_minutes': max(0, int(remaining / 60))
        }

        if result['expired']:
            logger.info(f"세션 타임아웃: {elapsed/60:.1f}분 비활성")

        return result

    def reset_session(self, session_state) -> None:
        """세션 리셋 (타임아웃 후 재시작)"""
        # 세션 관련 키만 삭제
        keys_to_keep = ['session_last_activity', 'session_started_at', 'session_timeout_minutes']

        for key in list(session_state.keys()):
            if key not in keys_to_keep:
                del session_state[key]

        self.init_session(session_state)
        logger.info("세션 리셋 완료")

    def extend_session(self, session_state, additional_minutes: int = 15) -> None:
        """세션 연장"""
        self.update_activity(session_state)
        logger.info(f"세션 연장: +{additional_minutes}분")


# 전역 세션 매니저
session_manager = SessionManager()


# ============================================================
# Streamlit 통합 함수
# ============================================================

def init_session_timeout(timeout_minutes: int = DEFAULT_TIMEOUT_MINUTES) -> None:
    """세션 타임아웃 초기화 (페이지 상단에서 호출)"""
    global session_manager
    session_manager = SessionManager(timeout_minutes)
    session_manager.init_session(st.session_state)


def check_and_handle_timeout() -> bool:
    """
    타임아웃 체크 및 처리

    Returns:
        True if session is valid, False if expired
    """
    result = session_manager.check_timeout(st.session_state)

    if result['expired']:
        # 세션 만료 처리
        st.warning("⏰ 세션이 만료되었습니다. 페이지를 새로고침 해주세요.")
        st.info(f"마지막 활동 후 {session_manager.timeout_minutes}분이 지났습니다.")

        if st.button("🔄 새로 시작하기"):
            session_manager.reset_session(st.session_state)
            st.rerun()

        return False

    elif result['warning']:
        # 타임아웃 경고
        st.toast(f"⚠️ 세션이 {result['remaining_minutes']}분 후 만료됩니다.", icon="⏰")

    return True


def update_user_activity() -> None:
    """사용자 활동 기록 (버튼 클릭, 입력 등에서 호출)"""
    session_manager.update_activity(st.session_state)


def get_session_info() -> Dict[str, Any]:
    """세션 정보 조회"""
    if 'session_started_at' not in st.session_state:
        return {'active': False}

    result = session_manager.check_timeout(st.session_state)

    return {
        'active': not result['expired'],
        'started_at': st.session_state.get('session_started_at'),
        'remaining_minutes': result['remaining_minutes'],
        'timeout_minutes': session_manager.timeout_minutes
    }


# ============================================================
# 세션 타임아웃 UI 컴포넌트
# ============================================================

def render_session_status(show_always: bool = False) -> None:
    """세션 상태 표시 UI"""
    info = get_session_info()

    if not info.get('active'):
        return

    remaining = info.get('remaining_minutes', 0)

    # 항상 표시하거나 5분 이하일 때만 표시
    if show_always or remaining <= 5:
        if remaining <= 2:
            color = "#ef4444"  # 빨간색
            icon = "🔴"
        elif remaining <= 5:
            color = "#f59e0b"  # 주황색
            icon = "🟡"
        else:
            color = "#10b981"  # 초록색
            icon = "🟢"

        st.markdown(f"""
        <div style="
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: white;
            padding: 10px 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid {color};
            font-size: 0.85rem;
            z-index: 9999;
        ">
            {icon} 세션 남은 시간: <strong>{remaining}분</strong>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=== Session Manager ===")
    print(f"Default timeout: {DEFAULT_TIMEOUT_MINUTES} minutes")
    print(f"Warning before: {WARNING_BEFORE_MINUTES} minutes")
    print("Ready!")

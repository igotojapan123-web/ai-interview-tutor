# auth_utils.py
# 공통 인증/비밀번호 체크 모듈

import streamlit as st


def _get_password(key: str) -> str:
    """비밀번호를 Streamlit secrets 또는 env_config에서 가져옴"""
    # 1. Streamlit secrets 먼저 확인 (Streamlit Cloud)
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
    except:
        pass
    
    # 2. env_config에서 가져오기 (로컬)
    try:
        from env_config import TESTER_PASSWORD, ADMIN_PASSWORD
        if key == "TESTER_PASSWORD":
            return TESTER_PASSWORD
        elif key == "ADMIN_PASSWORD":
            return ADMIN_PASSWORD
    except:
        pass
    
    return ""


def is_authenticated() -> bool:
    """현재 인증 상태 확인"""
    return st.session_state.get("authenticated", False)


def require_auth(title: str = "FlyReady Lab") -> bool:
    """인증 필요 - 미인증시 비밀번호 입력 화면 표시"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title(title)
        password = st.text_input("비밀번호를 입력하세요", type="password", key="auth_pw")

        if password:
            tester_pw = _get_password("TESTER_PASSWORD")
            if password == tester_pw:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다")
        st.stop()

    return True


def check_tester_password(title: str = "AI 면접 코칭") -> bool:
    """테스터 비밀번호 확인 (일반 사용자용)"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title(title)
        password = st.text_input("비밀번호를 입력하세요", type="password", key="tester_pw")

        if password:
            tester_pw = _get_password("TESTER_PASSWORD")
            if password == tester_pw:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다")
        st.stop()

    return True


def check_admin_password(title: str = "관리자 모드") -> bool:
    """관리자 비밀번호 확인"""
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        st.title(title)
        password = st.text_input("관리자 비밀번호를 입력하세요", type="password", key="admin_pw")

        if password:
            admin_pw = _get_password("ADMIN_PASSWORD")
            if password == admin_pw:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("관리자 비밀번호가 틀렸습니다")
        st.stop()

    return True

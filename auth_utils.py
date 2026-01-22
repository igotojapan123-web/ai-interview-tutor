# auth_utils.py
# 공통 인증/비밀번호 체크 모듈

import streamlit as st
from env_config import TESTER_PASSWORD, ADMIN_PASSWORD

def check_tester_password(title: str = "AI 면접 코칭") -> bool:
    """테스터 비밀번호 확인 (일반 사용자용)"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title(title)
        password = st.text_input("비밀번호를 입력하세요", type="password", key="tester_pw")

        if password:
            if password == TESTER_PASSWORD:
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
            if password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("관리자 비밀번호가 틀렸습니다")
        st.stop()

    return True

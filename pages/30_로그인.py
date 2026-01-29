# pages/30_로그인.py
# FlyReady Lab - 로그인 페이지

import streamlit as st
import os
import sys

# 상위 디렉토리 import 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="로그인 - FlyReady Lab",
    page_icon="✈️",
    layout="centered"
)

# 인증 시스템 import
try:
    from auth_system import AuthManager, get_kakao_auth_url, get_google_auth_url, get_apple_auth_url
    AUTH_AVAILABLE = True
    auth_manager = AuthManager()
except ImportError:
    AUTH_AVAILABLE = False
    auth_manager = None

# CSS
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
* { font-family: 'Pretendard', -apple-system, sans-serif; }
[data-testid="stSidebar"] { display: none; }
.block-container { max-width: 400px; padding-top: 60px; }

.login-header {
    text-align: center;
    margin-bottom: 40px;
}
.login-header h1 {
    font-size: 1.8rem;
    font-weight: 800;
    color: #1e3a5f;
    margin-bottom: 8px;
}
.login-header p {
    color: #64748b;
    font-size: 0.95rem;
}

.social-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    width: 100%;
    padding: 14px 20px;
    border-radius: 10px;
    font-size: 0.95rem;
    font-weight: 600;
    text-decoration: none;
    margin-bottom: 12px;
    transition: all 0.2s;
}
.social-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.kakao-btn {
    background: #FEE500;
    color: #191919;
}
.google-btn {
    background: white;
    color: #333;
    border: 1px solid #ddd;
}
.apple-btn {
    background: #000;
    color: white;
}

.divider {
    display: flex;
    align-items: center;
    margin: 24px 0;
    color: #94a3b8;
    font-size: 0.85rem;
}
.divider::before, .divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #e2e8f0;
}
.divider::before { margin-right: 16px; }
.divider::after { margin-left: 16px; }

.footer-links {
    text-align: center;
    margin-top: 32px;
    padding-top: 24px;
    border-top: 1px solid #e2e8f0;
}
.footer-links a {
    color: #3b82f6;
    text-decoration: none;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# 헤더
st.markdown("""
<div class="login-header">
    <h1>FlyReady Lab</h1>
    <p>승무원 면접 합격의 지름길</p>
</div>
""", unsafe_allow_html=True)

# OAuth 콜백 처리
query_params = st.query_params
if "code" in query_params:
    code = query_params.get("code")
    provider = query_params.get("provider", "kakao")

    if AUTH_AVAILABLE:
        try:
            if provider == "kakao":
                user = auth_manager.process_kakao_callback(code)
            elif provider == "google":
                user = auth_manager.process_google_callback(code)
            elif provider == "apple":
                user = auth_manager.process_apple_callback(code)
            else:
                user = None

            if user:
                st.session_state.user_id = user.id
                st.session_state.user_info = user
                st.session_state.is_logged_in = True
                st.success(f"환영합니다, {user.name}님!")
                st.balloons()
                st.switch_page("홈.py")
            else:
                st.error("로그인에 실패했습니다. 다시 시도해주세요.")
        except Exception as e:
            st.error(f"로그인 처리 중 오류가 발생했습니다: {e}")

# 소셜 로그인 버튼
if AUTH_AVAILABLE:
    kakao_url = get_kakao_auth_url()
    google_url = get_google_auth_url()
    apple_url = get_apple_auth_url()

    st.markdown(f"""
    <a href="{kakao_url}" class="social-btn kakao-btn">
        <svg width="20" height="20" viewBox="0 0 20 20"><path fill="#191919" d="M10 0C4.477 0 0 3.582 0 8c0 2.867 1.887 5.39 4.727 6.823-.152.543-.981 3.5-.981 3.5s-.028.234.124.323c.151.09.345.017.345.017.456-.063 5.285-3.463 5.785-3.83.667.09 1.333.167 2 .167 5.523 0 10-3.582 10-8S15.523 0 10 0z"/></svg>
        카카오로 시작하기
    </a>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <a href="{google_url}" class="social-btn google-btn">
        <svg width="20" height="20" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
        Google로 계속하기
    </a>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <a href="{apple_url}" class="social-btn apple-btn">
        <svg width="20" height="20" viewBox="0 0 24 24"><path fill="white" d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/></svg>
        Apple로 계속하기
    </a>
    """, unsafe_allow_html=True)
else:
    st.warning("인증 시스템을 불러올 수 없습니다.")

    # 데모 로그인
    st.markdown('<div class="divider">또는</div>', unsafe_allow_html=True)

    with st.form("demo_login"):
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")

        if st.form_submit_button("로그인", use_container_width=True):
            # 데모용 로그인 처리
            st.session_state.user_id = "demo_user"
            st.session_state.is_logged_in = True
            st.success("로그인 성공!")
            st.switch_page("홈.py")

# 하단 링크
st.markdown("""
<div class="footer-links">
    <a href="/회원가입">계정이 없으신가요? 회원가입</a>
</div>
""", unsafe_allow_html=True)

"""
모든 페이지에서 정식 웹사이트로 리다이렉트하는 공통 모듈
"""

import streamlit as st

def show_redirect_and_stop():
    """정식 웹사이트 안내 표시 후 실행 중단"""
    st.set_page_config(
        page_title="FlyReady - 정식 버전 이전 안내",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        .redirect-overlay {
            position: fixed;
            top: 0; left: 0;
            width: 100vw; height: 100vh;
            background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4c1d95 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        }
        .redirect-card {
            background: white;
            border-radius: 24px;
            padding: 48px;
            max-width: 500px;
            text-align: center;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        .redirect-icon { font-size: 64px; margin-bottom: 24px; }
        .redirect-title { font-size: 28px; font-weight: 700; color: #1e1b4b; margin-bottom: 16px; }
        .redirect-subtitle { font-size: 16px; color: #64748b; margin-bottom: 32px; line-height: 1.6; }
        .redirect-btn {
            display: inline-block;
            background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
            color: white !important;
            padding: 16px 48px;
            border-radius: 12px;
            font-size: 18px;
            font-weight: 600;
            text-decoration: none !important;
        }
        .stApp > header { display: none !important; }
        footer { display: none !important; }
        #MainMenu { display: none !important; }
    </style>
    <div class="redirect-overlay">
        <div class="redirect-card">
            <div class="redirect-icon">✈️</div>
            <div class="redirect-title">FLYREADY 정식 버전 출시!</div>
            <div class="redirect-subtitle">
                베타 테스트가 종료되었습니다.<br>
                정식 버전에서 더 강력한 기능을 만나보세요!
            </div>
            <a href="https://flyready.co.kr" class="redirect-btn">
                정식 버전 바로가기 →
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

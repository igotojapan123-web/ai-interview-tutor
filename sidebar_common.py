# sidebar_common.py
# 공통 사이드바 모듈 - 모든 페이지에서 import하여 사용

import streamlit as st
import base64
from pathlib import Path

def get_logo_base64():
    logo_path = Path(__file__).parent / "logo.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# 네비게이션 메뉴 구조
NAV_MENU = {
    "면접 연습": [
        {"icon": "🎤", "name": "모의면접", "page": "모의면접"},
        {"icon": "🎭", "name": "롤플레잉", "page": "롤플레잉"},
        {"icon": "🌐", "name": "영어면접", "page": "영어면접"},
        {"icon": "💬", "name": "토론면접", "page": "토론면접"},
    ],
    "준비 도구": [
        {"icon": "📝", "name": "자소서 첨삭", "page": "자소서첨삭"},
        {"icon": "🎯", "name": "실전 연습", "page": "실전연습"},
        {"icon": "👗", "name": "이미지메이킹", "page": "이미지메이킹"},
        {"icon": "🎙️", "name": "기내방송 연습", "page": "기내방송연습"},
        {"icon": "😊", "name": "표정 연습", "page": "표정연습"},
    ],
    "학습 · 정보": [
        {"icon": "✈️", "name": "항공 퀴즈", "page": "항공사퀴즈"},
        {"icon": "💡", "name": "면접 꿀팁", "page": "면접꿀팁"},
        {"icon": "🏢", "name": "항공사 가이드", "page": "항공사가이드"},
        {"icon": "🏋️", "name": "국민체력", "page": "국민체력"},
        {"icon": "📊", "name": "기업 분석", "page": "기업분석"},
    ],
    "학습 관리": [
        {"icon": "📈", "name": "진도 관리", "page": "진도관리"},
        {"icon": "📉", "name": "성장 그래프", "page": "성장그래프"},
        {"icon": "📢", "name": "채용 알림", "page": "채용알림"},
        {"icon": "🏆", "name": "합격자 DB", "page": "합격자DB"},
        {"icon": "📅", "name": "D-Day 캘린더", "page": "D-Day캘린더"},
    ],
}

def render_sidebar(current_page=""):
    """공통 사이드바 렌더링

    Args:
        current_page: 현재 페이지 이름 (예: "모의면접", "롤플레잉" 등)
    """
    # 비밀번호 인증 체크 (미인증 시 접근 차단)
    from auth_utils import check_tester_password
    check_tester_password("flyready_lab 베타 테스트")

    with st.sidebar:
        # 사이드바 CSS
        st.markdown("""
        <style>
        /* 기본 Streamlit 페이지 네비게이션 숨김 */
        [data-testid="stSidebarNav"] { display: none !important; }
        [data-testid="stSidebarNavItems"] { display: none !important; }
        [data-testid="stSidebarNavLink"] { display: none !important; }
        [data-testid="stSidebarNavSeparator"] { display: none !important; }
        [data-testid="stSidebar"] nav { display: none !important; }
        [data-testid="stSidebarUserContent"] > div:first-child > ul { display: none !important; }
        .st-emotion-cache-16tkqhc { display: none !important; }
        .st-emotion-cache-eczf16 { display: none !important; }
        [data-testid="stSidebar"] [data-testid="stPageLink"] { display: none !important; }
        [data-testid="stSidebar"] button[kind="header"] { display: none !important; }
        [data-testid="stSidebarCollapseButton"] { display: none !important; }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f2439 0%, #1a3a5c 30%, #1e4976 100%);
            min-width: 260px;
            max-width: 260px;
        }
        [data-testid="stSidebar"] * {
            color: white !important;
        }
        [data-testid="stSidebar"] .stMarkdown p {
            color: white !important;
        }

        .sidebar-header {
            text-align: center;
            padding: 20px 15px 15px 15px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 10px;
        }
        .sidebar-logo {
            height: 36px;
            margin-bottom: 8px;
        }
        .sidebar-brand {
            font-size: 1.1rem;
            font-weight: 800;
            color: white !important;
            letter-spacing: -0.5px;
        }
        .sidebar-crew {
            margin-top: 10px;
            font-size: 2.5rem;
            line-height: 1;
        }
        .sidebar-tagline {
            font-size: 0.7rem;
            color: rgba(255,255,255,0.6) !important;
            margin-top: 5px;
        }

        .sidebar-home-btn {
            display: block;
            text-align: center;
            padding: 10px;
            margin: 10px 10px 15px 10px;
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
            color: white !important;
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 600;
            transition: background 0.2s;
        }
        .sidebar-home-btn:hover {
            background: rgba(255,255,255,0.2);
        }

        .sidebar-category {
            font-size: 0.7rem;
            font-weight: 700;
            color: rgba(255,255,255,0.45) !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 12px 18px 5px 18px;
            margin-top: 5px;
        }

        .sidebar-nav-item {
            display: block;
            padding: 8px 18px;
            color: rgba(255,255,255,0.8) !important;
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 500;
            border-left: 3px solid transparent;
            transition: all 0.2s;
        }
        .sidebar-nav-item:hover {
            background: rgba(255,255,255,0.08);
            color: white !important;
            border-left-color: rgba(255,255,255,0.3);
        }
        .sidebar-nav-item.active {
            background: rgba(59,130,246,0.25);
            color: white !important;
            border-left-color: #60a5fa;
            font-weight: 700;
        }

        .sidebar-footer {
            position: fixed;
            bottom: 0;
            width: 260px;
            text-align: center;
            padding: 12px 10px;
            background: rgba(0,0,0,0.2);
            border-top: 1px solid rgba(255,255,255,0.08);
        }
        .sidebar-footer-text {
            font-size: 0.65rem;
            color: rgba(255,255,255,0.35) !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # 헤더 (로고 + 승무원 이미지)
        logo_b64 = get_logo_base64()
        if logo_b64:
            logo_img = f'<img src="data:image/png;base64,{logo_b64}" class="sidebar-logo">'
        else:
            logo_img = '<div class="sidebar-brand">flyready_lab</div>'

        st.markdown(f"""
        <div class="sidebar-header">
            {logo_img}
            <div class="sidebar-crew">👩‍✈️</div>
            <div class="sidebar-tagline">AI 승무원 면접 준비 플랫폼</div>
        </div>
        """, unsafe_allow_html=True)

        # 홈 버튼
        st.markdown('<a href="/" class="sidebar-home-btn">🏠 홈 대시보드</a>', unsafe_allow_html=True)

        # 네비게이션 메뉴
        nav_html = ""
        for category, items in NAV_MENU.items():
            nav_html += f'<div class="sidebar-category">{category}</div>'
            for item in items:
                active_class = "active" if item["page"] == current_page else ""
                nav_html += f'<a href="/{item["page"]}" class="sidebar-nav-item {active_class}">{item["icon"]} {item["name"]}</a>'

        st.markdown(nav_html, unsafe_allow_html=True)

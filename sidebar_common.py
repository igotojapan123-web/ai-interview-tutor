# sidebar_common.py
# 공통 사이드바 모듈 - 전문적인 디자인 (이모지 없는 버전)

import streamlit as st
import base64
from pathlib import Path
from env_config import ADMIN_PASSWORD

# 디자인 시스템 import
try:
    from ui_config import NAV_MENU, COLORS, get_sidebar_css
    UI_CONFIG_AVAILABLE = True
except ImportError:
    UI_CONFIG_AVAILABLE = False

@st.cache_resource
def get_logo_base64():
    """로고 이미지 Base64 인코딩 (영구 캐시)"""
    logo_path = Path(__file__).parent / "logo.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def render_sidebar(current_page=""):
    """공통 사이드바 렌더링 (전문적인 디자인)

    Args:
        current_page: 현재 페이지 이름 (예: "모의면접", "롤플레잉" 등)
    """
    with st.sidebar:
        # CSS 스타일 적용
        if UI_CONFIG_AVAILABLE:
            st.markdown(get_sidebar_css(), unsafe_allow_html=True)
        else:
            # 폴백 CSS
            st.markdown("""
            <style>
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

            .stTabs [data-baseweb="tab-list"] {
                overflow-x: auto;
                flex-wrap: nowrap !important;
                gap: 2px;
                -webkit-overflow-scrolling: touch;
                scrollbar-width: thin;
                padding-bottom: 4px;
            }
            .stTabs [data-baseweb="tab-list"] button {
                white-space: nowrap;
                flex-shrink: 0;
            }
            .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
                height: 4px;
            }
            .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb {
                background: rgba(0,0,0,0.2);
                border-radius: 2px;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0f2439 0%, #1e3a5f 30%, #2d5a87 100%);
                min-width: 260px;
                max-width: 260px;
            }
            [data-testid="stSidebar"] * {
                color: white !important;
            }
            [data-testid="stSidebar"] .stMarkdown p {
                color: white !important;
            }
            </style>
            """, unsafe_allow_html=True)

        # 헤더 (로고)
        logo_b64 = get_logo_base64()
        if logo_b64:
            logo_img = f'<img src="data:image/png;base64,{logo_b64}" class="fr-sidebar-logo">'
        else:
            logo_img = '<div class="fr-sidebar-brand">FlyReady Lab</div>'

        st.markdown(f"""
        <div class="fr-sidebar-header">
            {logo_img}
            <div class="fr-sidebar-tagline">AI 승무원 면접 코칭</div>
        </div>
        """, unsafe_allow_html=True)

        # 홈 버튼
        st.markdown('<a href="/" class="fr-sidebar-home">홈 대시보드</a>', unsafe_allow_html=True)

        # 네비게이션 메뉴 구성
        if UI_CONFIG_AVAILABLE:
            nav_menu = NAV_MENU
        else:
            # 폴백 메뉴
            nav_menu = {
                "면접 연습": [
                    {"name": "모의면접", "page": "모의면접", "desc": "AI 면접관"},
                    {"name": "롤플레잉", "page": "롤플레잉", "desc": "기내 상황"},
                    {"name": "영어면접", "page": "영어면접", "desc": "영어 답변"},
                    {"name": "토론면접", "page": "토론면접", "desc": "그룹 토론"},
                ],
                "준비 도구": [
                    {"name": "자소서 첨삭", "page": "자소서첨삭", "desc": "AI 피드백"},
                    {"name": "실전 연습", "page": "실전연습", "desc": "종합 분석"},
                    {"name": "이미지메이킹", "page": "이미지메이킹", "desc": "복장 체크"},
                    {"name": "기내방송", "page": "기내방송연습", "desc": "스크립트"},
                    {"name": "표정 연습", "page": "표정연습", "desc": "표정 분석"},
                ],
                "학습 정보": [
                    {"name": "항공 퀴즈", "page": "항공사퀴즈", "desc": "187문항"},
                    {"name": "면접 꿀팁", "page": "면접꿀팁", "desc": "핵심 팁"},
                    {"name": "항공사 가이드", "page": "항공사가이드", "desc": "각 사 정보"},
                    {"name": "국민체력", "page": "국민체력", "desc": "체력 기준"},
                    {"name": "기업 분석", "page": "기업분석", "desc": "기업 정보"},
                ],
                "학습 관리": [
                    {"name": "진도 관리", "page": "진도관리", "desc": "학습 현황"},
                    {"name": "성장 그래프", "page": "성장그래프", "desc": "점수 추이"},
                    {"name": "채용 알림", "page": "채용알림", "desc": "공고 소식"},
                    {"name": "합격자 DB", "page": "합격자DB", "desc": "합격 자료"},
                    {"name": "D-Day 캘린더", "page": "D-Day캘린더", "desc": "일정 관리"},
                ],
            }

        # 네비게이션 HTML 생성
        nav_html = ""
        for category, items in nav_menu.items():
            nav_html += f'<div class="fr-sidebar-category">{category}</div>'
            for item in items:
                active_class = "active" if item["page"] == current_page else ""
                desc_html = f'<span class="fr-sidebar-item-desc">{item.get("desc", "")}</span>' if item.get("desc") else ""
                nav_html += f'''
                <a href="/{item["page"]}" class="fr-sidebar-item {active_class}">
                    <span>{item["name"]}</span>
                    {desc_html}
                </a>
                '''

        # 관리자 모드 활성화 시 관리자 링크 추가
        if st.session_state.get("admin_authenticated", False):
            nav_html += '<div class="fr-sidebar-category">관리자</div>'
            active_class = "active" if current_page == "관리자" else ""
            nav_html += f'<a href="/관리자" class="fr-sidebar-item {active_class}"><span>관리자 모드</span></a>'

        st.markdown(nav_html, unsafe_allow_html=True)

        # 관리자 접근 (URL에 ?admin=1 추가 시에만 표시)
        show_admin = st.query_params.get("admin") == "1"
        if show_admin:
            st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)
            if not st.session_state.get("admin_authenticated", False):
                admin_pw = st.text_input("관리자 비밀번호", type="password", key="admin_pw_input")
                if admin_pw == ADMIN_PASSWORD:
                    st.session_state["admin_authenticated"] = True
                    st.rerun()
                elif admin_pw:
                    st.error("비밀번호 오류")
            else:
                st.success("관리자 모드")
                confirm = st.checkbox("로그아웃", key="admin_logout_check")
                if confirm:
                    st.session_state["admin_authenticated"] = False
                    st.session_state["admin_logout_check"] = False
                    st.rerun()

# nav_utils.py
# 깔끔한 사이드바 네비게이션 유틸리티

import streamlit as st

# 페이지 카테고리 구조
NAV_STRUCTURE = {
    "면접 연습": {
        "icon": "🎤",
        "pages": [
            {"name": "모의면접", "icon": "🎤", "path": "/모의면접"},
            {"name": "롤플레잉", "icon": "🎭", "path": "/롤플레잉"},
            {"name": "영어면접", "icon": "🌐", "path": "/영어면접"},
            {"name": "토론면접", "icon": "💬", "path": "/토론면접"},
        ]
    },
    "자소서/질문": {
        "icon": "📝",
        "pages": [
            {"name": "자소서 첨삭", "icon": "📝", "path": "/자소서첨삭"},
            {"name": "자소서기반 질문", "icon": "❓", "path": "/자소서기반질문"},
        ]
    },
    "준비 도구": {
        "icon": "🛠️",
        "pages": [
            {"name": "이미지메이킹", "icon": "👗", "path": "/이미지메이킹"},
            {"name": "체력 준비", "icon": "🏊", "path": "/체력준비"},
            {"name": "기내방송 연습", "icon": "🎙️", "path": "/기내방송연습"},
            {"name": "표정 연습", "icon": "😊", "path": "/표정연습"},
        ]
    },
    "학습/정보": {
        "icon": "📚",
        "pages": [
            {"name": "항공상식 퀴즈", "icon": "✈️", "path": "/항공상식퀴즈"},
            {"name": "면접 꿀팁", "icon": "💡", "path": "/면접꿀팁"},
            {"name": "항공사 가이드", "icon": "🏢", "path": "/항공사가이드"},
            {"name": "기업 분석", "icon": "📊", "path": "/기업분석"},
        ]
    },
    "커뮤니티": {
        "icon": "👥",
        "pages": [
            {"name": "Q&A 게시판", "icon": "💬", "path": "/QnA게시판"},
            {"name": "합격자 DB", "icon": "🏆", "path": "/합격자DB"},
        ]
    },
    "관리": {
        "icon": "📈",
        "pages": [
            {"name": "진도 관리", "icon": "📈", "path": "/진도관리"},
            {"name": "성장 그래프", "icon": "📉", "path": "/성장그래프"},
            {"name": "채용 알림", "icon": "📢", "path": "/채용알림"},
            {"name": "D-Day 캘린더", "icon": "📅", "path": "/D데이캘린더"},
        ]
    },
}


def get_clean_sidebar_css():
    """깔끔한 사이드바 CSS 반환"""
    return """
    <style>
    /* 기본 Streamlit 페이지 목록 숨기기 */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* 사이드바 전체 배경 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a5f 0%, #2d5a87 100%) !important;
    }

    section[data-testid="stSidebar"] > div {
        background: transparent !important;
    }

    /* 사이드바 내부 모든 텍스트 흰색 */
    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }

    /* expander 스타일 */
    section[data-testid="stSidebar"] .streamlit-expanderHeader {
        background: rgba(255,255,255,0.1) !important;
        border-radius: 8px;
        color: white !important;
    }

    section[data-testid="stSidebar"] .streamlit-expanderContent {
        background: rgba(255,255,255,0.05) !important;
        border-radius: 0 0 8px 8px;
    }

    /* 카테고리 제목 스타일 */
    .nav-category {
        color: #93c5fd !important;
        font-size: 0.8rem;
        font-weight: 700;
        margin: 25px 0 12px 0;
        padding-left: 5px;
    }

    /* 네비게이션 링크 스타일 */
    .nav-link {
        display: block;
        color: white !important;
        text-decoration: none;
        padding: 10px 15px;
        border-radius: 8px;
        margin: 4px 0;
        transition: all 0.2s;
        font-size: 0.95rem;
        background: rgba(255,255,255,0.08);
    }

    .nav-link:hover {
        background: rgba(255,255,255,0.2) !important;
        color: white !important;
        transform: translateX(3px);
        text-decoration: none;
    }

    .nav-link.active {
        background: rgba(255,255,255,0.25) !important;
        color: white !important;
        font-weight: 700;
        border-left: 3px solid #60a5fa;
    }

    /* 홈 버튼 강조 */
    .home-btn {
        display: block;
        background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
        color: white !important;
        text-decoration: none;
        padding: 14px 20px;
        border-radius: 12px;
        margin: 15px 10px 25px 10px;
        text-align: center;
        font-weight: 700;
        font-size: 1rem;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }

    .home-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(59, 130, 246, 0.5);
        text-decoration: none;
        color: white !important;
    }

    /* 구분선 */
    .nav-divider {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.15);
        margin: 20px 10px;
    }
    </style>
    """


def render_sidebar(current_page: str = ""):
    """깔끔한 사이드바 렌더링"""

    # CSS 적용
    st.markdown(get_clean_sidebar_css(), unsafe_allow_html=True)

    with st.sidebar:
        # 상단 여백
        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)

        # 홈 버튼
        st.markdown('<a href="/" class="home-btn">🏠 홈으로</a>', unsafe_allow_html=True)

        # 구분선
        st.markdown('<hr class="nav-divider">', unsafe_allow_html=True)

        # 카테고리별 네비게이션
        for category, data in NAV_STRUCTURE.items():
            st.markdown(f'<div class="nav-category">{data["icon"]} {category}</div>', unsafe_allow_html=True)

            nav_html = ""
            for page in data["pages"]:
                is_active = current_page == page["name"]
                active_class = "active" if is_active else ""
                nav_html += f'<a href="{page["path"]}" class="nav-link {active_class}">{page["icon"]} {page["name"]}</a>'

            st.markdown(f'<div style="padding: 0 10px;">{nav_html}</div>', unsafe_allow_html=True)

        # 하단 여백
        st.markdown("<br><br>", unsafe_allow_html=True)


def render_minimal_sidebar(current_page: str = "", category: str = ""):
    """최소화된 사이드바 - 현재 카테고리 + 홈 버튼만"""

    st.markdown(get_clean_sidebar_css(), unsafe_allow_html=True)

    with st.sidebar:
        # 홈 버튼
        st.markdown('<a href="/" class="home-btn">🏠 홈으로</a>', unsafe_allow_html=True)

        # 현재 카테고리만 표시
        if category and category in NAV_STRUCTURE:
            data = NAV_STRUCTURE[category]
            st.markdown(f'<div class="nav-category">{data["icon"]} {category}</div>', unsafe_allow_html=True)

            for page in data["pages"]:
                is_active = current_page == page["name"]
                active_class = "active" if is_active else ""
                st.markdown(
                    f'<a href="{page["path"]}" class="nav-link {active_class}">'
                    f'{page["icon"]} {page["name"]}</a>',
                    unsafe_allow_html=True
                )

            st.markdown('<hr class="nav-divider">', unsafe_allow_html=True)

        # 다른 메뉴 보기
        with st.expander("📋 다른 메뉴 보기"):
            for cat_name, cat_data in NAV_STRUCTURE.items():
                if cat_name != category:
                    st.markdown(f"**{cat_data['icon']} {cat_name}**")
                    for page in cat_data["pages"]:
                        st.markdown(f"[{page['icon']} {page['name']}]({page['path']})")


def get_page_header_html(title: str, subtitle: str = "", icon: str = ""):
    """페이지 상단 헤더 HTML"""
    return f'''
    <div style="
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 25px 30px;
        border-radius: 15px;
        margin-bottom: 25px;
        color: white;
    ">
        <h1 style="margin: 0; font-size: 1.8rem; display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 2rem;">{icon}</span> {title}
        </h1>
        {f'<p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1rem;">{subtitle}</p>' if subtitle else ''}
    </div>
    '''

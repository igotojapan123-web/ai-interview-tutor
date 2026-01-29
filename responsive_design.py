# responsive_design.py
# 대기업 수준 반응형 디자인 시스템
# FlyReady Lab - Enterprise Responsive Design Module

import streamlit as st
from typing import Optional, Dict, List, Tuple
from enum import Enum

# =============================================================================
# 브레이크포인트 시스템
# =============================================================================

class Breakpoint(Enum):
    """표준 브레이크포인트"""
    XS = 320    # 소형 모바일
    SM = 640    # 모바일
    MD = 768    # 태블릿
    LG = 1024   # 데스크탑
    XL = 1280   # 대형 데스크탑
    XXL = 1536  # 초대형


# 브레이크포인트 픽셀값
BREAKPOINTS = {
    "xs": 320,
    "sm": 640,
    "md": 768,
    "lg": 1024,
    "xl": 1280,
    "xxl": 1536
}


# =============================================================================
# 반응형 CSS
# =============================================================================

def get_responsive_css() -> str:
    """반응형 CSS 반환"""
    return """
    <style>
    /* =================================
       반응형 기본 설정
       ================================= */

    /* 뷰포트 메타 */
    @viewport {
        width: device-width;
        initial-scale: 1;
    }

    /* 기본 박스 모델 */
    *, *::before, *::after {
        box-sizing: border-box;
    }

    /* =================================
       모바일 네비게이션
       ================================= */

    /* 사이드바 모바일 최적화 */
    @media (max-width: 768px) {
        [data-testid="stSidebar"] {
            min-width: 100% !important;
            max-width: 100% !important;
            transform: translateX(-100%);
            transition: transform 0.3s ease;
        }

        [data-testid="stSidebar"][aria-expanded="true"] {
            transform: translateX(0);
        }

        /* 메인 콘텐츠 패딩 조정 */
        .main .block-container {
            padding: 1rem !important;
            max-width: 100% !important;
        }

        /* 제목 크기 조정 */
        h1 { font-size: 1.75rem !important; }
        h2 { font-size: 1.5rem !important; }
        h3 { font-size: 1.25rem !important; }
    }

    /* =================================
       터치 타겟 최적화 (최소 44px)
       ================================= */

    @media (max-width: 768px) {
        /* 버튼 */
        .stButton > button {
            min-height: 48px !important;
            padding: 12px 24px !important;
            font-size: 16px !important;
        }

        /* 입력 필드 */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > div {
            min-height: 48px !important;
            font-size: 16px !important; /* iOS 줌 방지 */
        }

        /* 체크박스/라디오 */
        .stCheckbox > label,
        .stRadio > label {
            min-height: 44px !important;
            display: flex !important;
            align-items: center !important;
        }

        /* 탭 */
        .stTabs [data-baseweb="tab"] {
            min-height: 48px !important;
            padding: 12px 16px !important;
        }

        /* 확장 패널 */
        .streamlit-expanderHeader {
            min-height: 48px !important;
        }
    }

    /* =================================
       그리드 시스템
       ================================= */

    .fr-grid {
        display: grid;
        gap: 16px;
    }

    /* 1열 (모바일) */
    @media (max-width: 639px) {
        .fr-grid { grid-template-columns: 1fr; }
        .fr-grid-2, .fr-grid-3, .fr-grid-4 { grid-template-columns: 1fr; }
    }

    /* 2열 (태블릿) */
    @media (min-width: 640px) and (max-width: 1023px) {
        .fr-grid-2 { grid-template-columns: repeat(2, 1fr); }
        .fr-grid-3 { grid-template-columns: repeat(2, 1fr); }
        .fr-grid-4 { grid-template-columns: repeat(2, 1fr); }
    }

    /* 다중 열 (데스크탑) */
    @media (min-width: 1024px) {
        .fr-grid-2 { grid-template-columns: repeat(2, 1fr); }
        .fr-grid-3 { grid-template-columns: repeat(3, 1fr); }
        .fr-grid-4 { grid-template-columns: repeat(4, 1fr); }
    }

    /* =================================
       반응형 타이포그래피
       ================================= */

    /* 모바일 */
    @media (max-width: 639px) {
        .fr-text-responsive {
            font-size: 14px;
            line-height: 1.6;
        }
        .fr-heading-responsive {
            font-size: 20px;
            line-height: 1.3;
        }
    }

    /* 태블릿 */
    @media (min-width: 640px) and (max-width: 1023px) {
        .fr-text-responsive {
            font-size: 15px;
            line-height: 1.6;
        }
        .fr-heading-responsive {
            font-size: 24px;
            line-height: 1.3;
        }
    }

    /* 데스크탑 */
    @media (min-width: 1024px) {
        .fr-text-responsive {
            font-size: 16px;
            line-height: 1.6;
        }
        .fr-heading-responsive {
            font-size: 28px;
            line-height: 1.3;
        }
    }

    /* =================================
       반응형 카드
       ================================= */

    .fr-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        overflow: hidden;
    }

    @media (max-width: 639px) {
        .fr-card {
            border-radius: 8px;
            margin: 0 -8px;  /* 전체 너비 활용 */
        }
        .fr-card-body {
            padding: 16px;
        }
    }

    @media (min-width: 640px) {
        .fr-card-body {
            padding: 24px;
        }
    }

    /* =================================
       반응형 테이블
       ================================= */

    .fr-table-responsive {
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }

    @media (max-width: 639px) {
        .fr-table-responsive table {
            min-width: 600px;
        }

        /* 스택형 테이블 (선택적) */
        .fr-table-stack thead {
            display: none;
        }

        .fr-table-stack tr {
            display: block;
            margin-bottom: 16px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px;
        }

        .fr-table-stack td {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #f1f5f9;
        }

        .fr-table-stack td:last-child {
            border-bottom: none;
        }

        .fr-table-stack td::before {
            content: attr(data-label);
            font-weight: 600;
            color: #64748b;
        }
    }

    /* =================================
       반응형 이미지/미디어
       ================================= */

    .fr-img-responsive {
        max-width: 100%;
        height: auto;
        display: block;
    }

    .fr-video-responsive {
        position: relative;
        padding-bottom: 56.25%; /* 16:9 */
        height: 0;
        overflow: hidden;
    }

    .fr-video-responsive iframe,
    .fr-video-responsive video {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
    }

    /* =================================
       모바일 전용 유틸리티
       ================================= */

    /* 모바일에서만 표시 */
    .fr-mobile-only {
        display: none !important;
    }

    @media (max-width: 768px) {
        .fr-mobile-only {
            display: block !important;
        }
        .fr-desktop-only {
            display: none !important;
        }
    }

    /* 데스크탑에서만 표시 */
    @media (min-width: 769px) {
        .fr-desktop-only {
            display: block !important;
        }
    }

    /* =================================
       간격 유틸리티 (반응형)
       ================================= */

    @media (max-width: 639px) {
        .fr-p-responsive { padding: 12px; }
        .fr-m-responsive { margin: 12px; }
        .fr-gap-responsive { gap: 12px; }
    }

    @media (min-width: 640px) and (max-width: 1023px) {
        .fr-p-responsive { padding: 16px; }
        .fr-m-responsive { margin: 16px; }
        .fr-gap-responsive { gap: 16px; }
    }

    @media (min-width: 1024px) {
        .fr-p-responsive { padding: 24px; }
        .fr-m-responsive { margin: 24px; }
        .fr-gap-responsive { gap: 24px; }
    }

    /* =================================
       플렉스 유틸리티 (반응형)
       ================================= */

    .fr-flex {
        display: flex;
    }

    .fr-flex-wrap {
        flex-wrap: wrap;
    }

    @media (max-width: 639px) {
        .fr-flex-col-mobile {
            flex-direction: column;
        }
    }

    /* =================================
       하단 네비게이션 (모바일)
       ================================= */

    .fr-bottom-nav {
        display: none;
    }

    @media (max-width: 768px) {
        .fr-bottom-nav {
            display: flex;
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            border-top: 1px solid #e2e8f0;
            padding: 8px 0;
            padding-bottom: calc(8px + env(safe-area-inset-bottom));
            z-index: 1000;
            justify-content: space-around;
        }

        .fr-bottom-nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 8px 16px;
            color: #64748b;
            text-decoration: none;
            font-size: 12px;
            min-width: 64px;
        }

        .fr-bottom-nav-item.active {
            color: #2563eb;
        }

        .fr-bottom-nav-item svg {
            width: 24px;
            height: 24px;
            margin-bottom: 4px;
        }

        /* 하단 네비게이션 공간 확보 */
        .main .block-container {
            padding-bottom: 80px !important;
        }
    }

    /* =================================
       Safe Area (노치 대응)
       ================================= */

    @supports (padding: env(safe-area-inset-top)) {
        .fr-safe-area-top {
            padding-top: env(safe-area-inset-top);
        }
        .fr-safe-area-bottom {
            padding-bottom: env(safe-area-inset-bottom);
        }
    }

    /* =================================
       프린트 스타일
       ================================= */

    @media print {
        [data-testid="stSidebar"] {
            display: none !important;
        }

        .main .block-container {
            max-width: 100% !important;
            padding: 0 !important;
        }

        .stButton,
        .fr-bottom-nav {
            display: none !important;
        }

        a[href]::after {
            content: " (" attr(href) ")";
            font-size: 0.8em;
            color: #666;
        }
    }

    /* =================================
       Streamlit 특정 반응형 수정
       ================================= */

    /* 열 간격 */
    @media (max-width: 639px) {
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }
    }

    /* 메트릭 카드 */
    @media (max-width: 639px) {
        [data-testid="stMetric"] {
            padding: 12px !important;
        }

        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 24px !important;
        }
    }

    /* 차트 */
    @media (max-width: 639px) {
        .js-plotly-plot {
            max-width: 100% !important;
        }
    }

    /* 데이터프레임 */
    @media (max-width: 639px) {
        [data-testid="stDataFrame"] {
            max-width: 100% !important;
            overflow-x: auto !important;
        }
    }

    /* =================================
       터치 피드백
       ================================= */

    @media (hover: none) and (pointer: coarse) {
        /* 터치 장치에서 호버 효과 비활성화 */
        .stButton > button:hover {
            transform: none;
            box-shadow: none;
        }

        /* 터치 피드백 */
        .stButton > button:active {
            transform: scale(0.98);
            opacity: 0.9;
        }
    }

    /* =================================
       가로/세로 모드 대응
       ================================= */

    @media (orientation: landscape) and (max-height: 500px) {
        /* 가로 모드에서 높이가 낮을 때 */
        .fr-landscape-compact {
            padding-top: 8px;
            padding-bottom: 8px;
        }
    }
    </style>
    """


# =============================================================================
# 뷰포트 메타 태그
# =============================================================================

def get_viewport_meta() -> str:
    """뷰포트 메타 태그 반환"""
    return """
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5, user-scalable=yes">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="theme-color" content="#0f2439">
    """


# =============================================================================
# 반응형 그리드 컴포넌트
# =============================================================================

def responsive_columns(
    items: List,
    mobile_cols: int = 1,
    tablet_cols: int = 2,
    desktop_cols: int = 3
) -> List[List]:
    """반응형 컬럼 분할 (서버사이드)

    Args:
        items: 아이템 리스트
        mobile_cols: 모바일 컬럼 수
        tablet_cols: 태블릿 컬럼 수
        desktop_cols: 데스크탑 컬럼 수

    Returns:
        Streamlit columns에 맞게 분할된 리스트
    """
    # Streamlit에서는 서버사이드 렌더링이므로 데스크탑 기준으로 반환
    # CSS로 모바일/태블릿 대응
    return [items[i:i + desktop_cols] for i in range(0, len(items), desktop_cols)]


def render_responsive_grid(
    items: List[Dict],
    render_func,
    columns: int = 3,
    gap: int = 16
):
    """반응형 그리드 렌더링

    Args:
        items: 아이템 리스트
        render_func: 아이템 렌더링 함수
        columns: 기본 열 수
        gap: 간격 (px)
    """
    st.markdown(f"""
    <div class="fr-grid fr-grid-{columns}" style="gap: {gap}px;">
    """, unsafe_allow_html=True)

    cols = st.columns(columns)

    for i, item in enumerate(items):
        with cols[i % columns]:
            render_func(item)

    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# 모바일 하단 네비게이션
# =============================================================================

def render_bottom_navigation(
    items: List[Dict[str, str]],
    current_page: str
):
    """모바일 하단 네비게이션 렌더링

    Args:
        items: [{"name": "홈", "page": "home", "icon": "<svg>..."}, ...]
        current_page: 현재 페이지 ID
    """
    nav_items = ""

    for item in items:
        active_class = "active" if item["page"] == current_page else ""
        nav_items += f"""
        <a href="/{item['page']}" class="fr-bottom-nav-item {active_class}">
            {item.get('icon', '')}
            <span>{item['name']}</span>
        </a>
        """

    nav_html = f"""
    <nav class="fr-bottom-nav" role="navigation" aria-label="모바일 메뉴">
        {nav_items}
    </nav>
    """

    st.markdown(nav_html, unsafe_allow_html=True)


# 기본 네비게이션 아이템
DEFAULT_BOTTOM_NAV = [
    {
        "name": "홈",
        "page": "홈",
        "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'
    },
    {
        "name": "면접",
        "page": "모의면접",
        "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>'
    },
    {
        "name": "연습",
        "page": "실전연습",
        "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>'
    },
    {
        "name": "학습",
        "page": "진도관리",
        "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>'
    },
]


# =============================================================================
# 반응형 카드 컴포넌트
# =============================================================================

def render_responsive_card(
    title: str,
    content: str,
    footer: Optional[str] = None,
    image_url: Optional[str] = None
):
    """반응형 카드 렌더링"""
    image_html = f'<img src="{image_url}" class="fr-img-responsive" style="width:100%;border-bottom:1px solid #e2e8f0;">' if image_url else ''

    footer_html = f'<div class="fr-card-footer" style="padding:16px;border-top:1px solid #e2e8f0;background:#f8fafc;">{footer}</div>' if footer else ''

    card_html = f"""
    <div class="fr-card">
        {image_html}
        <div class="fr-card-body">
            <h4 style="margin:0 0 12px 0;color:#1e293b;font-size:18px;">{title}</h4>
            <p style="margin:0;color:#64748b;line-height:1.6;">{content}</p>
        </div>
        {footer_html}
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


# =============================================================================
# 반응형 테이블
# =============================================================================

def render_responsive_table(
    headers: List[str],
    rows: List[List[str]],
    stack_on_mobile: bool = True
):
    """반응형 테이블 렌더링

    Args:
        headers: 헤더 목록
        rows: 행 데이터
        stack_on_mobile: 모바일에서 스택 형태로 표시
    """
    table_class = "fr-table-stack" if stack_on_mobile else ""

    header_html = "".join([f"<th>{h}</th>" for h in headers])

    rows_html = ""
    for row in rows:
        cells = ""
        for i, cell in enumerate(row):
            data_label = f'data-label="{headers[i]}"' if stack_on_mobile else ''
            cells += f"<td {data_label}>{cell}</td>"
        rows_html += f"<tr>{cells}</tr>"

    table_html = f"""
    <div class="fr-table-responsive">
        <table class="{table_class}" style="width:100%;border-collapse:collapse;">
            <thead>
                <tr style="background:#f1f5f9;">
                    {header_html}
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """

    st.markdown(table_html, unsafe_allow_html=True)


# =============================================================================
# 초기화 함수
# =============================================================================

def init_responsive_design():
    """반응형 디자인 초기화 (페이지 시작 시 호출)"""
    # 뷰포트 메타 태그
    st.markdown(get_viewport_meta(), unsafe_allow_html=True)

    # 반응형 CSS
    st.markdown(get_responsive_css(), unsafe_allow_html=True)


# =============================================================================
# 디바이스 감지 (제한적)
# =============================================================================

def get_device_hint() -> str:
    """디바이스 힌트 반환 (JavaScript 기반)

    Note: Streamlit에서는 서버사이드 렌더링이므로 정확한 감지가 어려움
    클라이언트 사이드 JavaScript로 보완
    """
    return """
    <script>
    (function() {
        var isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        var isTablet = /(tablet|ipad|playbook|silk)|(android(?!.*mobi))/i.test(navigator.userAgent);

        document.body.classList.add(isMobile ? 'fr-device-mobile' : 'fr-device-desktop');
        if (isTablet) document.body.classList.add('fr-device-tablet');

        // 화면 방향 감지
        function updateOrientation() {
            if (window.innerHeight > window.innerWidth) {
                document.body.classList.add('fr-orientation-portrait');
                document.body.classList.remove('fr-orientation-landscape');
            } else {
                document.body.classList.add('fr-orientation-landscape');
                document.body.classList.remove('fr-orientation-portrait');
            }
        }

        updateOrientation();
        window.addEventListener('resize', updateOrientation);
        window.addEventListener('orientationchange', updateOrientation);
    })();
    </script>
    """


def inject_device_detection():
    """디바이스 감지 스크립트 삽입"""
    st.markdown(get_device_hint(), unsafe_allow_html=True)

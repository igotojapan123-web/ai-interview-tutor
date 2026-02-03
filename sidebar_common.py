# sidebar_common.py
# FlyReady Lab - Enterprise Navigation Module (Simplified)
# Fixed version without complex f-string CSS that causes rendering issues

import streamlit as st

# Legacy imports for backward compatibility
try:
    from env_config import ADMIN_PASSWORD
except ImportError:
    ADMIN_PASSWORD = "admin123"

# Enhancement modules - 비활성화 (안정성 문제)
ENHANCEMENT_AVAILABLE = False
MODULES_AVAILABLE = {}


def get_simple_css():
    """Simple, reliable CSS without complex f-string issues."""
    return """
    <style>
    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    [data-testid="stToolbar"] {display: none;}
    [data-testid="stSidebarNav"] {display: none !important;}
    [data-testid="stSidebar"] {display: none !important;}

    /* Material Icon 텍스트 폴백 숨김 (keyboard_arrow_down 등) */
    [data-testid="stIconMaterial"] {
        font-size: 0 !important;
        line-height: 0 !important;
        overflow: hidden !important;
    }

    /* Import premium font */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    /* Root variables */
    :root {
        --primary: #2563EB;
        --primary-dark: #1D4ED8;
        --text-primary: #0F172A;
        --text-secondary: #64748B;
        --bg-primary: #FFFFFF;
        --bg-secondary: #F8FAFC;
        --border: #E2E8F0;
        --nav-height: 64px;
    }

    /* Base styles */
    html, body, [class*="st-"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    .main .block-container {
        padding-top: calc(var(--nav-height) + 32px) !important;
        max-width: 1280px;
        margin: 0 auto;
    }

    /* Navigation Bar */
    .nav-container {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: var(--nav-height);
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-bottom: 1px solid var(--border);
        z-index: 9999;
        display: flex;
        align-items: center;
        padding: 0 32px;
    }

    .nav-inner {
        max-width: 1400px;
        width: 100%;
        margin: 0 auto;
        display: flex;
        align-items: center;
        gap: 32px;
    }

    .nav-right {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-left: auto;
    }

    .nav-btn {
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        text-decoration: none;
        transition: all 0.2s;
    }

    .nav-btn-ghost {
        color: #475569;
    }

    .nav-btn-ghost:hover {
        color: #0F172A;
        background: #F1F5F9;
    }

    .nav-btn-primary {
        background: #2563EB !important;
        color: #FFFFFF !important;
        text-shadow: none !important;
    }

    .nav-btn-primary:hover {
        background: #1D4ED8 !important;
        color: #FFFFFF !important;
    }

    .nav-btn-primary:visited,
    .nav-btn-primary:active,
    .nav-btn-primary:link {
        color: #FFFFFF !important;
    }

    .nav-logo {
        display: flex;
        align-items: center;
        gap: 10px;
        text-decoration: none;
        font-weight: 700;
        font-size: 20px;
        color: var(--text-primary);
    }

    .nav-logo-icon {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #2563EB, #7C3AED);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        color: white;
    }

    .nav-links {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .nav-link {
        padding: 8px 16px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 14px;
        font-weight: 500;
        color: var(--text-secondary);
        transition: all 0.2s ease;
    }

    .nav-link:hover {
        background: var(--bg-secondary);
        color: var(--text-primary);
    }

    .nav-link.active {
        background: rgba(37, 99, 235, 0.1);
        color: var(--primary);
    }

    /* Page Header */
    .page-header {
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 1px solid var(--border);
    }

    .page-title {
        font-size: 28px;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
    }

    /* Cards */
    .stExpander {
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        background: white !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
        border: none !important;
        color: #FFFFFF !important;
    }

    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
        color: #FFFFFF !important;
    }

    /* Primary 버튼 내부 텍스트 - 강제 흰색 */
    .stButton > button[kind="primary"] p,
    .stButton > button[kind="primary"] span,
    .stButton > button[data-testid="baseButton-primary"] p,
    .stButton > button[data-testid="baseButton-primary"] span {
        color: #FFFFFF !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: var(--bg-secondary);
        padding: 4px;
        border-radius: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        font-weight: 500;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        border-radius: 8px !important;
        border: 1px solid var(--border) !important;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background: var(--bg-secondary);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid var(--border);
    }

    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #2563EB, #7C3AED) !important;
    }

    /* Footer */
    .footer {
        margin-top: 48px;
        padding: 24px 0;
        border-top: 1px solid var(--border);
        text-align: center;
        color: var(--text-secondary);
        font-size: 13px;
    }
    </style>
    """


def render_navbar(current_page: str = ""):
    """Render simple navigation bar with login button."""

    nav_items = [
        ("홈", "/", "home"),
        ("튜토리얼", "/시작하기", "시작하기"),
        ("면접연습", "/모의면접", "모의면접"),
        ("자소서", "/자소서작성", "자소서작성"),
        ("퀴즈", "/항공사퀴즈", "항공사퀴즈"),
        ("학습관리", "/진도관리", "진도관리"),
    ]

    links_html = ""
    for label, href, page_id in nav_items:
        active_class = "active" if current_page == page_id else ""
        links_html += f'<a href="{href}" target="_self" class="nav-link {active_class}">{label}</a>'

    navbar_html = f"""
    <div class="nav-container">
        <div class="nav-inner">
            <a href="/" target="_self" class="nav-logo">
                <div class="nav-logo-icon">F</div>
                <span>FlyReady Lab</span>
            </a>
            <nav class="nav-links">
                {links_html}
            </nav>
            <div class="nav-right">
                <a href="/로그인" target="_self" class="nav-btn nav-btn-ghost">로그인</a>
                <a href="/구독" target="_self" class="nav-btn nav-btn-primary">무료 체험</a>
            </div>
        </div>
    </div>
    """

    st.markdown(navbar_html, unsafe_allow_html=True)


def render_page_header(title: str):
    """Render page header."""
    st.markdown(f"""
    <div class="page-header">
        <h1 class="page-title">{title}</h1>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    """Render page footer."""
    st.markdown("""
    <div class="footer">
        <p>FlyReady Lab - AI Flight Attendant Interview Coaching Platform</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar(current_page: str = ""):
    """Render enterprise-grade navigation.

    Args:
        current_page: Current page identifier for highlighting
    """
    # Apply simple CSS
    st.markdown(get_simple_css(), unsafe_allow_html=True)

    # Render navigation bar
    render_navbar(current_page)


def init_page(
    title: str,
    page_title: str = None,
    current_page: str = "",
    wide_layout: bool = True
):
    """Initialize page with enterprise layout.

    Args:
        title: Page title displayed in header
        page_title: Browser tab title (defaults to "FlyReady Lab - {title}")
        current_page: Current page identifier for nav highlighting
        wide_layout: Use wide layout (True) or centered (False)
    """
    st.set_page_config(
        page_title=page_title or f"FlyReady Lab - {title}",
        page_icon="✈",
        layout="wide" if wide_layout else "centered",
        initial_sidebar_state="collapsed"
    )

    # Apply layout and render navbar
    render_sidebar(current_page)

    # Page header
    render_page_header(title)


def end_page(show_footer: bool = True):
    """End page with footer."""
    if show_footer:
        render_footer()


# Legacy admin functions
def check_admin_access():
    """Check for admin access (legacy support)."""
    show_admin = st.query_params.get("admin") == "1"
    if show_admin:
        if not st.session_state.get("admin_authenticated", False):
            with st.sidebar:
                admin_pw = st.text_input("관리자 비밀번호", type="password", key="admin_pw")
                if admin_pw == ADMIN_PASSWORD:
                    st.session_state["admin_authenticated"] = True
                    st.rerun()
                elif admin_pw:
                    st.error("비밀번호 오류")
    return st.session_state.get("admin_authenticated", False)

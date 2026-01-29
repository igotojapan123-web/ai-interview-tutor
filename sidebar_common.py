# sidebar_common.py
# FlyReady Lab - Enterprise Navigation Module
# Beautiful dropdown navigation with all features

import streamlit as st

# Legacy imports for backward compatibility
try:
    from env_config import ADMIN_PASSWORD
except ImportError:
    ADMIN_PASSWORD = "admin123"


def get_simple_css():
    """Premium CSS with dropdown navigation."""
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

    /* Material Icon 텍스트 폴백 숨김 */
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
        --primary-light: #3B82F6;
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
        padding-top: 120px !important;
        max-width: 1280px;
        margin: 0 auto;
    }

    /* ========== Main Navigation Bar ========== */
    .flyready-nav {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 60px;
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-bottom: 1px solid var(--border);
        z-index: 9999;
        display: flex;
        align-items: center;
        padding: 0 32px;
        gap: 32px;
    }

    .flyready-nav .nav-logo {
        display: flex;
        align-items: center;
        gap: 10px;
        text-decoration: none;
        font-weight: 700;
        font-size: 18px;
        color: var(--text-primary);
        flex-shrink: 0;
    }

    .flyready-nav .logo-icon {
        width: 34px;
        height: 34px;
        background: linear-gradient(135deg, #2563EB, #7C3AED);
        border-radius: 9px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        font-weight: 800;
        color: white;
    }

    .flyready-nav .nav-links {
        display: flex;
        align-items: center;
        gap: 4px;
        flex: 1;
    }

    .flyready-nav .nav-link {
        padding: 8px 16px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 14px;
        font-weight: 500;
        color: var(--text-secondary);
        transition: all 0.2s ease;
    }

    .flyready-nav .nav-link:hover {
        background: var(--bg-secondary);
        color: var(--text-primary);
    }

    .flyready-nav .nav-link.active {
        background: rgba(37, 99, 235, 0.1);
        color: var(--primary);
        font-weight: 600;
    }

    .flyready-nav .nav-right {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-left: auto;
        flex-shrink: 0;
    }

    .flyready-nav .nav-btn {
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 500;
        text-decoration: none;
        transition: all 0.2s;
        white-space: nowrap;
    }

    .flyready-nav .nav-btn.ghost {
        color: #475569;
    }

    .flyready-nav .nav-btn.ghost:hover {
        color: #0F172A;
        background: #F1F5F9;
    }

    .flyready-nav .nav-btn.primary {
        background: linear-gradient(135deg, #2563EB, #1D4ED8);
        color: #ffffff !important;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
    }

    .flyready-nav .nav-btn.primary:hover {
        background: linear-gradient(135deg, #1D4ED8, #1e40af);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
        transform: translateY(-1px);
    }

    /* ========== Sub Navigation Bar ========== */
    .sub-nav {
        position: fixed;
        top: 60px;
        left: 0;
        right: 0;
        height: 44px;
        background: var(--bg-secondary);
        border-bottom: 1px solid var(--border);
        z-index: 9998;
        display: flex;
        align-items: center;
        padding: 0 32px;
        gap: 16px;
        animation: slideDown 0.2s ease;
    }

    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .sub-nav .sub-label {
        font-size: 12px;
        font-weight: 600;
        color: var(--primary);
        padding: 4px 10px;
        background: rgba(37, 99, 235, 0.1);
        border-radius: 6px;
        margin-right: 8px;
    }

    .sub-nav .sub-link {
        padding: 6px 12px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 13px;
        font-weight: 500;
        color: var(--text-secondary);
        transition: all 0.15s ease;
    }

    .sub-nav .sub-link:hover {
        background: white;
        color: var(--text-primary);
    }

    .sub-nav .sub-link.active {
        background: white;
        color: var(--primary);
        font-weight: 600;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }

    /* ========== Page Styles ========== */
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
        transition: all 0.3s ease !important;
    }

    .stExpander:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.08) !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.25s ease !important;
        padding: 0.6rem 1.2rem !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
        border: none !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.15);
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
    }

    .stButton > button[kind="primary"] p,
    .stButton > button[kind="primary"] span,
    .stButton > button[kind="primary"] div {
        color: #ffffff !important;
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.45) !important;
        background: linear-gradient(135deg, #1D4ED8, #1e40af) !important;
    }

    .stButton > button[kind="secondary"] {
        background: #f1f5f9 !important;
        border: 1px solid #e2e8f0 !important;
        color: #1e293b !important;
        font-weight: 600 !important;
    }

    .stButton > button[kind="secondary"]:hover {
        background: #e2e8f0 !important;
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }

    .stButton > button:not([kind]) {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        color: #334155 !important;
    }

    .stButton > button:not([kind]):hover {
        background: #f8fafc !important;
        border-color: #cbd5e1 !important;
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

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
    }

    /* ========== Animations ========== */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }

    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }

    .main .block-container {
        animation: fadeIn 0.4s ease;
    }

    /* Metric Cards */
    [data-testid="stMetric"] {
        animation: fadeInUp 0.5s ease;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        background: var(--bg-secondary);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid var(--border);
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        border-color: var(--primary);
    }

    /* Expander Cards */
    .stExpander {
        animation: fadeInUp 0.4s ease;
    }

    /* Success/Error/Warning Messages */
    .stSuccess, .stError, .stWarning, .stInfo {
        animation: slideInRight 0.3s ease;
        border-radius: 10px !important;
    }

    /* Form Inputs Focus Animation */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        transform: scale(1.01);
    }

    /* Tab Animation */
    .stTabs [data-baseweb="tab-panel"] {
        animation: fadeIn 0.3s ease;
    }

    .stTabs [data-baseweb="tab"] {
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        transform: translateY(-1px);
    }

    /* Progress Bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #2563EB, #7C3AED) !important;
        animation: shimmer 2s infinite linear;
        background-size: 200% 100%;
    }

    /* Spinner/Loading */
    .stSpinner > div {
        border-color: var(--primary) transparent transparent transparent !important;
    }

    /* Data Frames and Tables */
    .stDataFrame {
        animation: fadeIn 0.4s ease;
        border-radius: 12px;
        overflow: hidden;
    }

    /* Image hover effect */
    .stImage {
        transition: all 0.3s ease;
        border-radius: 12px;
        overflow: hidden;
    }

    .stImage:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }

    /* Download Button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #059669, #10b981) !important;
        color: white !important;
        border: none !important;
    }

    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.4) !important;
    }

    /* Checkbox and Radio */
    .stCheckbox, .stRadio {
        transition: all 0.2s ease;
    }

    .stCheckbox:hover, .stRadio:hover {
        transform: translateX(2px);
    }

    /* Columns Animation - staggered */
    [data-testid="column"]:nth-child(1) { animation: fadeInUp 0.4s ease 0s both; }
    [data-testid="column"]:nth-child(2) { animation: fadeInUp 0.4s ease 0.1s both; }
    [data-testid="column"]:nth-child(3) { animation: fadeInUp 0.4s ease 0.2s both; }
    [data-testid="column"]:nth-child(4) { animation: fadeInUp 0.4s ease 0.3s both; }

    /* Footer */
    .footer {
        margin-top: 48px;
        padding: 24px 0;
        border-top: 1px solid var(--border);
        text-align: center;
        color: var(--text-secondary);
        font-size: 13px;
        animation: fadeIn 0.5s ease 0.3s both;
    }

    /* Mobile Responsive */
    @media (max-width: 1024px) {
        .nav-container {
            padding: 0 16px;
        }
        .nav-dropdown-menu {
            min-width: 200px;
        }
        .nav-btn-primary {
            padding: 8px 12px;
            font-size: 12px;
        }
    }
    </style>
    """


def render_navbar(current_page: str = ""):
    """Render navigation using Streamlit native components for reliable dropdown."""

    # Navigation structure
    nav_cats = {
        "면접연습": [("AI 모의면접", "모의면접"), ("롤플레잉", "롤플레잉"), ("영어면접", "영어면접"), ("토론면접", "토론면접"), ("실전연습", "실전연습")],
        "준비도구": [("자소서 첨삭", "자소서첨삭"), ("자소서 질문", "자소서기반질문"), ("이미지메이킹", "이미지메이킹"), ("기내방송", "기내방송연습"), ("표정연습", "표정연습")],
        "학습정보": [("항공상식 퀴즈", "항공사퀴즈"), ("면접 꿀팁", "면접꿀팁"), ("항공사 가이드", "항공사가이드"), ("기업분석", "기업분석"), ("합격자 DB", "합격자DB")],
        "학습관리": [("진도관리", "진도관리"), ("성장그래프", "성장그래프"), ("채용정보", "채용정보"), ("D-Day", "D-Day캘린더")],
    }

    # Find active category
    active_cat = ""
    for cat, items in nav_cats.items():
        for _, page_id in items:
            if current_page == page_id:
                active_cat = cat
                break

    # Build links HTML
    home_active = "active" if current_page == "home" else ""
    links_html = f'<a href="/" target="_self" class="nav-link {home_active}">홈</a>'

    for cat, items in nav_cats.items():
        cat_active = "active" if cat == active_cat else ""
        first_title, first_page = items[0]
        links_html += f'<a href="/{first_page}" target="_self" class="nav-link {cat_active}">{cat}</a>'

    navbar_html = f'''<div class="flyready-nav">
<a href="/" target="_self" class="nav-logo"><div class="logo-icon">F</div><span>FlyReady Lab</span></a>
<div class="nav-links">{links_html}</div>
<div class="nav-right">
<span class="nav-btn" style="background: #10b981; color: white; font-weight: 600;">Beta Test</span>
</div>
</div>'''

    st.markdown(navbar_html, unsafe_allow_html=True)

    # Show sub-navigation for active category
    if active_cat and active_cat in nav_cats:
        items = nav_cats[active_cat]
        sub_links = ""
        for title, page_id in items:
            item_active = "active" if current_page == page_id else ""
            sub_links += f'<a href="/{page_id}" target="_self" class="sub-link {item_active}">{title}</a>'

        sub_nav_html = f'<div class="sub-nav"><span class="sub-label">{active_cat}</span>{sub_links}</div>'
        st.markdown(sub_nav_html, unsafe_allow_html=True)


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
    """Render enterprise-grade navigation."""
    st.markdown(get_simple_css(), unsafe_allow_html=True)
    render_navbar(current_page)


def init_page(
    title: str,
    page_title: str = None,
    current_page: str = "",
    wide_layout: bool = True
):
    """Initialize page with enterprise layout."""
    st.set_page_config(
        page_title=page_title or f"FlyReady Lab - {title}",
        page_icon="✈",
        layout="wide" if wide_layout else "centered",
        initial_sidebar_state="collapsed"
    )
    render_sidebar(current_page)
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

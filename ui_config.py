# ui_config.py
# FlyReady Lab 디자인 시스템 - 전문적이고 깔끔한 UI 설정
# 이모지 없이 아이콘과 텍스트로 구성

# ============================================
# 색상 팔레트
# ============================================
COLORS = {
    # 기본 브랜드 색상
    "primary": "#1e3a5f",        # 네이비 블루 (메인)
    "primary_light": "#2d5a87",  # 밝은 네이비
    "primary_dark": "#0f2439",   # 어두운 네이비

    # 강조 색상
    "accent": "#3b82f6",         # 파랑 (강조)
    "accent_light": "#60a5fa",   # 밝은 파랑
    "accent_hover": "#2563eb",   # 호버 파랑

    # 상태 색상
    "success": "#10b981",        # 녹색 (성공)
    "warning": "#f59e0b",        # 주황 (경고)
    "error": "#ef4444",          # 빨강 (에러)
    "info": "#3b82f6",           # 파랑 (정보)

    # 중립 색상
    "text_primary": "#1e293b",   # 진한 텍스트
    "text_secondary": "#64748b", # 옅은 텍스트
    "text_muted": "#94a3b8",     # 비활성 텍스트
    "background": "#f8fafc",     # 배경
    "surface": "#ffffff",        # 카드 배경
    "border": "#e2e8f0",         # 테두리

    # 그라데이션
    "gradient_primary": "linear-gradient(135deg, #1e3a5f 0%, #3b82f6 100%)",
    "gradient_surface": "linear-gradient(145deg, #f8fafc, #f1f5f9)",
}

# ============================================
# 타이포그래피
# ============================================
TYPOGRAPHY = {
    "font_family": "'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    "h1": {"size": "2rem", "weight": "800", "line_height": "1.2"},
    "h2": {"size": "1.5rem", "weight": "700", "line_height": "1.3"},
    "h3": {"size": "1.25rem", "weight": "600", "line_height": "1.4"},
    "body": {"size": "1rem", "weight": "400", "line_height": "1.6"},
    "caption": {"size": "0.875rem", "weight": "400", "line_height": "1.5"},
    "small": {"size": "0.75rem", "weight": "400", "line_height": "1.4"},
}

# ============================================
# 간격 시스템
# ============================================
SPACING = {
    "xs": "4px",
    "sm": "8px",
    "md": "16px",
    "lg": "24px",
    "xl": "32px",
    "xxl": "48px",
}

# ============================================
# 네비게이션 메뉴 (이모지 없는 버전)
# ============================================
NAV_MENU = {
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

# 메인 페이지 카드 구성 (이모지 없는 버전)
MAIN_PAGE_CARDS = {
    "면접 연습": [
        {"name": "AI 모의면접", "page": "모의면접", "desc": "실전처럼 연습하고 즉시 피드백 받기", "highlight": True},
        {"name": "기내 롤플레잉", "page": "롤플레잉", "desc": "실제 기내 상황 시뮬레이션"},
        {"name": "영어면접", "page": "영어면접", "desc": "영어 질문 답변 연습"},
        {"name": "토론면접", "page": "토론면접", "desc": "그룹 토론 시뮬레이션"},
    ],
    "준비 도구": [
        {"name": "자소서 작성 도우미", "page": "자소서작성", "desc": "문항 의도 분석 + AI 챗봇", "highlight": True},
        {"name": "자소서 AI 첨삭", "page": "자소서첨삭", "desc": "AI가 자소서 피드백 제공"},
        {"name": "에어로케이 가이드", "page": "에어로케이", "desc": "경험 포트폴리오 컨설팅", "highlight": True},
        {"name": "실전 연습", "page": "실전연습", "desc": "영상/음성 종합 분석 연습"},
        {"name": "이미지메이킹", "page": "이미지메이킹", "desc": "메이크업/복장 가이드"},
        {"name": "기내방송 연습", "page": "기내방송연습", "desc": "한국어/영어 15개 스크립트"},
    ],
    "학습 정보": [
        {"name": "항공 상식 퀴즈", "page": "항공사퀴즈", "desc": "187문항"},
        {"name": "면접 꿀팁", "page": "면접꿀팁", "desc": "핵심 포인트"},
        {"name": "항공사 가이드", "page": "항공사가이드", "desc": "항공사별 정보"},
        {"name": "국민체력/수영", "page": "국민체력", "desc": "체력 기준"},
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

# ============================================
# 공통 CSS 스타일
# ============================================
def get_base_css():
    """기본 CSS 스타일 반환"""
    return f"""
<style>
/* Pretendard 폰트 로드 */
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

/* 기본 레이아웃 */
* {{
    font-family: {TYPOGRAPHY['font_family']};
}}

[data-testid="stSidebar"] {{ display: none; }}
[data-testid="collapsedControl"] {{ display: none; }}
.block-container {{ padding: 0 !important; max-width: 100% !important; }}
header[data-testid="stHeader"] {{ display: none; }}
.stApp {{ background: {COLORS['background']}; }}

/* 스크롤바 스타일링 */
::-webkit-scrollbar {{
    width: 8px;
    height: 8px;
}}
::-webkit-scrollbar-track {{
    background: {COLORS['background']};
}}
::-webkit-scrollbar-thumb {{
    background: {COLORS['border']};
    border-radius: 4px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: {COLORS['text_muted']};
}}

/* 헤더 */
.fr-header {{
    background: {COLORS['surface']};
    padding: 16px 48px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    position: sticky;
    top: 0;
    z-index: 100;
}}
.fr-logo {{
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 1.25rem;
    font-weight: 800;
    color: {COLORS['primary']};
    text-decoration: none;
}}
.fr-logo img {{ height: 36px; }}
.fr-header-text {{
    font-size: 0.9rem;
    color: {COLORS['text_secondary']};
    font-weight: 500;
}}

/* 히어로 섹션 */
.fr-hero {{
    background: {COLORS['gradient_primary']};
    padding: 40px 48px;
    color: white;
}}
.fr-hero h1 {{
    font-size: 1.75rem;
    font-weight: 800;
    margin: 0 0 8px 0;
}}
.fr-hero p {{
    font-size: 0.95rem;
    opacity: 0.85;
    margin: 0;
}}
.fr-hero-actions {{
    display: flex;
    gap: 12px;
    margin-top: 20px;
}}
.fr-btn {{
    display: inline-block;
    padding: 12px 28px;
    border-radius: 8px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s;
    font-size: 0.9rem;
}}
.fr-btn-primary {{
    background: {COLORS['surface']};
    color: {COLORS['primary']};
}}
.fr-btn-primary:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}}
.fr-btn-secondary {{
    background: rgba(255,255,255,0.1);
    color: white;
    border: 1px solid rgba(255,255,255,0.2);
}}

/* 메인 컨텐츠 */
.fr-main {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 32px 24px;
}}

/* 통계 카드 그리드 */
.fr-stats-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}}
.fr-stat-card {{
    background: {COLORS['surface']};
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    border-left: 4px solid {COLORS['accent']};
    transition: all 0.2s;
}}
.fr-stat-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}}
.fr-stat-value {{
    font-size: 1.75rem;
    font-weight: 800;
    color: {COLORS['primary']};
    margin-bottom: 4px;
}}
.fr-stat-label {{
    font-size: 0.8rem;
    color: {COLORS['text_secondary']};
    font-weight: 500;
}}

/* 섹션 */
.fr-section {{
    background: {COLORS['surface']};
    border-radius: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    padding: 28px;
    margin-bottom: 24px;
}}
.fr-section-title {{
    font-size: 1.1rem;
    color: {COLORS['primary']};
    margin-bottom: 20px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.fr-section-title::before {{
    content: '';
    width: 4px;
    height: 20px;
    background: {COLORS['accent']};
    border-radius: 2px;
}}

/* 카드 그리드 */
.fr-card-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
}}
.fr-card {{
    background: {COLORS['background']};
    border-radius: 12px;
    padding: 24px 20px;
    text-align: center;
    text-decoration: none;
    color: inherit;
    transition: all 0.2s;
    border: 1px solid transparent;
}}
.fr-card:hover {{
    background: #eff6ff;
    border-color: {COLORS['accent']};
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}}
.fr-card-title {{
    font-size: 0.95rem;
    font-weight: 700;
    color: {COLORS['primary']};
    margin-bottom: 6px;
}}
.fr-card-desc {{
    font-size: 0.8rem;
    color: {COLORS['text_secondary']};
    line-height: 1.4;
}}

/* 미니 카드 그리드 */
.fr-mini-grid {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
}}
.fr-mini-card {{
    background: {COLORS['background']};
    border-radius: 10px;
    padding: 16px 12px;
    text-align: center;
    text-decoration: none;
    color: inherit;
    transition: all 0.2s;
    border: 1px solid {COLORS['border']};
}}
.fr-mini-card:hover {{
    background: #eff6ff;
    border-color: {COLORS['accent_light']};
    transform: translateY(-2px);
}}
.fr-mini-card-title {{
    font-size: 0.85rem;
    font-weight: 600;
    color: {COLORS['text_primary']};
}}

/* D-Day 및 추천 영역 */
.fr-info-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 24px;
}}
.fr-info-box {{
    background: {COLORS['surface']};
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}
.fr-info-title {{
    font-size: 1rem;
    font-weight: 700;
    color: {COLORS['primary']};
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid {COLORS['border']};
}}
.fr-dday-item {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: {COLORS['background']};
    border-radius: 8px;
    margin-bottom: 8px;
    border-left: 3px solid {COLORS['accent']};
}}
.fr-dday-item.urgent {{ border-left-color: {COLORS['error']}; background: #fef2f2; }}
.fr-dday-item.warning {{ border-left-color: {COLORS['warning']}; background: #fffbeb; }}
.fr-dday-name {{
    font-size: 0.9rem;
    font-weight: 600;
    color: {COLORS['text_primary']};
}}
.fr-dday-date {{
    font-size: 0.75rem;
    color: {COLORS['text_secondary']};
}}
.fr-dday-badge {{
    font-size: 0.8rem;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 16px;
    color: white;
}}
.fr-dday-badge.red {{ background: {COLORS['error']}; }}
.fr-dday-badge.orange {{ background: {COLORS['warning']}; }}
.fr-dday-badge.blue {{ background: {COLORS['accent']}; }}

.fr-recommend-item {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: {COLORS['background']};
    border-radius: 8px;
    margin-bottom: 8px;
    border-left: 3px solid {COLORS['success']};
}}
.fr-recommend-text {{
    font-size: 0.85rem;
    font-weight: 500;
    color: {COLORS['text_primary']};
}}

/* 푸터 */
.fr-footer {{
    background: {COLORS['primary']};
    padding: 32px;
    text-align: center;
    color: rgba(255,255,255,0.7);
    margin-top: 48px;
}}
.fr-footer-brand {{
    font-size: 1.1rem;
    font-weight: 700;
    color: white;
    margin-bottom: 8px;
}}
.fr-footer p {{ margin: 4px 0; font-size: 0.85rem; }}

/* 반응형 */
@media (max-width: 900px) {{
    .fr-stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .fr-info-grid {{ grid-template-columns: 1fr; }}
    .fr-card-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .fr-mini-grid {{ grid-template-columns: repeat(3, 1fr); }}
    .fr-header {{ padding: 12px 20px; }}
    .fr-hero {{ padding: 28px 20px; }}
    .fr-hero h1 {{ font-size: 1.4rem; }}
}}
@media (max-width: 500px) {{
    .fr-stats-grid {{ grid-template-columns: 1fr 1fr; }}
    .fr-card-grid {{ grid-template-columns: 1fr; }}
    .fr-mini-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}
</style>
"""


def get_sidebar_css():
    """사이드바 CSS 스타일 반환"""
    return f"""
<style>
/* 기본 Streamlit 페이지 네비게이션 숨김 */
[data-testid="stSidebarNav"] {{ display: none !important; }}
[data-testid="stSidebarNavItems"] {{ display: none !important; }}
[data-testid="stSidebarNavLink"] {{ display: none !important; }}
[data-testid="stSidebarNavSeparator"] {{ display: none !important; }}
[data-testid="stSidebar"] nav {{ display: none !important; }}
[data-testid="stSidebarUserContent"] > div:first-child > ul {{ display: none !important; }}
.st-emotion-cache-16tkqhc {{ display: none !important; }}
.st-emotion-cache-eczf16 {{ display: none !important; }}
[data-testid="stSidebar"] [data-testid="stPageLink"] {{ display: none !important; }}
[data-testid="stSidebar"] button[kind="header"] {{ display: none !important; }}
[data-testid="stSidebarCollapseButton"] {{ display: none !important; }}

/* 탭 오버플로우 방지 */
.stTabs [data-baseweb="tab-list"] {{
    overflow-x: auto;
    flex-wrap: nowrap !important;
    gap: 2px;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
    padding-bottom: 4px;
}}
.stTabs [data-baseweb="tab-list"] button {{
    white-space: nowrap;
    flex-shrink: 0;
}}
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {{
    height: 4px;
}}
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb {{
    background: rgba(0,0,0,0.2);
    border-radius: 2px;
}}

/* 사이드바 기본 스타일 */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {COLORS['primary_dark']} 0%, {COLORS['primary']} 30%, {COLORS['primary_light']} 100%);
    min-width: 260px;
    max-width: 260px;
}}
[data-testid="stSidebar"] * {{
    color: white !important;
}}
[data-testid="stSidebar"] .stMarkdown p {{
    color: white !important;
}}

/* 사이드바 헤더 */
.fr-sidebar-header {{
    text-align: center;
    padding: 24px 16px 20px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 12px;
}}
.fr-sidebar-logo {{
    height: 32px;
    margin-bottom: 6px;
}}
.fr-sidebar-brand {{
    font-size: 1.1rem;
    font-weight: 800;
    color: white !important;
    letter-spacing: -0.5px;
}}
.fr-sidebar-tagline {{
    font-size: 0.7rem;
    color: rgba(255,255,255,0.5) !important;
    margin-top: 4px;
}}

/* 홈 버튼 */
.fr-sidebar-home {{
    display: block;
    text-align: center;
    padding: 10px;
    margin: 12px 12px 16px 12px;
    background: rgba(255,255,255,0.08);
    border-radius: 8px;
    color: white !important;
    text-decoration: none;
    font-size: 0.85rem;
    font-weight: 600;
    transition: background 0.2s;
}}
.fr-sidebar-home:hover {{
    background: rgba(255,255,255,0.15);
}}

/* 카테고리 헤더 */
.fr-sidebar-category {{
    font-size: 0.65rem;
    font-weight: 700;
    color: rgba(255,255,255,0.4) !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    padding: 14px 18px 6px 18px;
    margin-top: 4px;
}}

/* 네비게이션 아이템 */
.fr-sidebar-item {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 18px;
    color: rgba(255,255,255,0.75) !important;
    text-decoration: none;
    font-size: 0.85rem;
    font-weight: 500;
    border-left: 3px solid transparent;
    transition: all 0.2s;
}}
.fr-sidebar-item:hover {{
    background: rgba(255,255,255,0.06);
    color: white !important;
    border-left-color: rgba(255,255,255,0.2);
}}
.fr-sidebar-item.active {{
    background: rgba(59,130,246,0.2);
    color: white !important;
    border-left-color: {COLORS['accent_light']};
    font-weight: 600;
}}
.fr-sidebar-item-desc {{
    font-size: 0.7rem;
    color: rgba(255,255,255,0.4) !important;
}}

/* 사이드바 푸터 */
.fr-sidebar-footer {{
    position: fixed;
    bottom: 0;
    width: 260px;
    text-align: center;
    padding: 12px 10px;
    background: rgba(0,0,0,0.15);
    border-top: 1px solid rgba(255,255,255,0.05);
}}
.fr-sidebar-footer-text {{
    font-size: 0.6rem;
    color: rgba(255,255,255,0.3) !important;
}}
</style>
"""


def get_page_css():
    """페이지별 공통 CSS 스타일 반환"""
    return f"""
<style>
/* 페이지 타이틀 스타일 */
.fr-page-title {{
    font-size: 1.75rem;
    font-weight: 800;
    color: {COLORS['primary']};
    margin-bottom: 8px;
}}
.fr-page-subtitle {{
    font-size: 0.95rem;
    color: {COLORS['text_secondary']};
    margin-bottom: 24px;
}}

/* 상태 배지 */
.fr-badge {{
    display: inline-block;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
}}
.fr-badge-success {{ background: #dcfce7; color: #166534; }}
.fr-badge-warning {{ background: #fef3c7; color: #92400e; }}
.fr-badge-error {{ background: #fee2e2; color: #991b1b; }}
.fr-badge-info {{ background: #dbeafe; color: #1e40af; }}

/* 진행률 바 */
.fr-progress {{
    background: {COLORS['border']};
    border-radius: 6px;
    height: 8px;
    overflow: hidden;
}}
.fr-progress-bar {{
    height: 100%;
    background: {COLORS['accent']};
    border-radius: 6px;
    transition: width 0.3s ease;
}}

/* 알림 박스 */
.fr-alert {{
    padding: 16px 20px;
    border-radius: 10px;
    margin: 12px 0;
}}
.fr-alert-info {{
    background: #eff6ff;
    border-left: 4px solid {COLORS['accent']};
    color: {COLORS['text_primary']};
}}
.fr-alert-success {{
    background: #f0fdf4;
    border-left: 4px solid {COLORS['success']};
    color: {COLORS['text_primary']};
}}
.fr-alert-warning {{
    background: #fffbeb;
    border-left: 4px solid {COLORS['warning']};
    color: {COLORS['text_primary']};
}}
.fr-alert-error {{
    background: #fef2f2;
    border-left: 4px solid {COLORS['error']};
    color: {COLORS['text_primary']};
}}

/* 타이머 */
.fr-timer {{
    background: {COLORS['gradient_primary']};
    border-radius: 12px;
    padding: 16px 24px;
    text-align: center;
    color: white;
}}
.fr-timer-display {{
    font-size: 2.5rem;
    font-weight: bold;
    font-family: 'Courier New', monospace;
}}

/* 아바타/캐릭터 */
.fr-avatar {{
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    font-weight: 600;
}}
.fr-avatar-passenger {{
    background: {COLORS['accent']};
    color: white;
}}
.fr-avatar-crew {{
    background: {COLORS['success']};
    color: white;
}}

/* 대화 말풍선 */
.fr-chat-bubble {{
    max-width: 80%;
    padding: 14px 18px;
    border-radius: 16px;
    margin: 8px 0;
    line-height: 1.6;
}}
.fr-chat-passenger {{
    background: #eff6ff;
    border-bottom-left-radius: 4px;
    margin-right: auto;
}}
.fr-chat-crew {{
    background: #f0fdf4;
    border-bottom-right-radius: 4px;
    margin-left: auto;
}}

/* 결과 카드 */
.fr-result-card {{
    background: {COLORS['surface']};
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    margin: 16px 0;
}}
.fr-result-score {{
    font-size: 3rem;
    font-weight: 800;
    color: {COLORS['primary']};
    text-align: center;
}}
.fr-result-grade {{
    display: inline-block;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    text-align: center;
    line-height: 48px;
    font-size: 1.5rem;
    font-weight: 800;
    color: white;
}}
.fr-grade-s {{ background: linear-gradient(135deg, #fbbf24, #f59e0b); }}
.fr-grade-a {{ background: linear-gradient(135deg, #34d399, #10b981); }}
.fr-grade-b {{ background: linear-gradient(135deg, #60a5fa, #3b82f6); }}
.fr-grade-c {{ background: linear-gradient(135deg, #fbbf24, #f59e0b); }}
.fr-grade-d {{ background: linear-gradient(135deg, #f87171, #ef4444); }}
</style>
"""


# ============================================
# 유틸리티 함수
# ============================================
def format_stat_card(value, label, color_class=""):
    """통계 카드 HTML 생성"""
    return f"""
    <div class="fr-stat-card {color_class}">
        <div class="fr-stat-value">{value}</div>
        <div class="fr-stat-label">{label}</div>
    </div>
    """


def format_page_header(title, subtitle=""):
    """페이지 헤더 HTML 생성"""
    subtitle_html = f'<div class="fr-page-subtitle">{subtitle}</div>' if subtitle else ''
    return f"""
    <div class="fr-page-title">{title}</div>
    {subtitle_html}
    """


def format_alert(message, alert_type="info"):
    """알림 박스 HTML 생성"""
    return f'<div class="fr-alert fr-alert-{alert_type}">{message}</div>'


def format_progress_bar(percent, color=None):
    """진행률 바 HTML 생성"""
    if color is None:
        color = COLORS['accent']
    return f"""
    <div class="fr-progress">
        <div class="fr-progress-bar" style="width: {percent}%; background: {color};"></div>
    </div>
    """


def format_badge(text, badge_type="info"):
    """배지 HTML 생성"""
    return f'<span class="fr-badge fr-badge-{badge_type}">{text}</span>'

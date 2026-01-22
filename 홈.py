# 홈.py
# flyready_lab - 메인 페이지 (깔끔한 버전)

import streamlit as st
import base64
from pathlib import Path
from datetime import datetime

from auth_utils import check_tester_password

# 사용량 제한 시스템
try:
    from usage_limiter import render_beta_banner, render_usage_summary
    USAGE_LIMITER_AVAILABLE = True
except ImportError:
    USAGE_LIMITER_AVAILABLE = False

# 로고 이미지 로드
def get_logo_base64():
    logo_path = Path(__file__).parent / "logo.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

LOGO_BASE64 = get_logo_base64()

st.set_page_config(
    page_title="flyready_lab",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 비밀번호 확인
check_tester_password("flyready_lab 베타 테스트")

# 세션 시간 초기화
try:
    from motivation import init_session_time, check_and_show_motivation
    init_session_time()
    if check_and_show_motivation():
        st.rerun()
    if st.session_state.get("show_motivation_popup", False):
        from motivation import show_motivation_popup
        show_motivation_popup()
except:
    pass

# CSS 스타일
st.markdown("""
<style>
/* 사이드바 숨기기 */
[data-testid="stSidebar"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
.block-container { padding: 0 !important; max-width: 100% !important; }
header[data-testid="stHeader"] { display: none; }
.stApp { background: #f8fafc; }

/* 헤더 */
.header {
    background: white;
    padding: 18px 60px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 15px rgba(0,0,0,0.04);
    position: sticky;
    top: 0;
    z-index: 100;
}
.logo {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 1.5rem;
    font-weight: 800;
    color: #1e3a5f;
    text-decoration: none;
}
.logo img { height: 40px; }

/* 히어로 섹션 */
.hero {
    background: linear-gradient(135deg, #1e3a5f 0%, #3b82f6 100%);
    padding: 60px;
    color: white;
    text-align: center;
}
.hero h1 {
    font-size: 2.5rem;
    margin-bottom: 15px;
    font-weight: 800;
}
.hero p {
    font-size: 1.1rem;
    opacity: 0.9;
    margin-bottom: 35px;
    line-height: 1.6;
}
.hero-buttons {
    display: flex;
    gap: 15px;
    justify-content: center;
    flex-wrap: wrap;
}
.hero-btn {
    display: inline-block;
    padding: 16px 40px;
    border-radius: 50px;
    font-weight: 700;
    text-decoration: none;
    transition: all 0.3s;
    font-size: 1rem;
}
.hero-btn.primary {
    background: white;
    color: #1e3a5f;
}
.hero-btn.primary:hover {
    transform: translateY(-3px);
    box-shadow: 0 15px 40px rgba(0,0,0,0.2);
}
.hero-btn.secondary {
    background: rgba(255,255,255,0.15);
    color: white;
    border: 2px solid rgba(255,255,255,0.3);
}
.hero-btn.secondary:hover {
    background: rgba(255,255,255,0.25);
}

/* 메인 컨텐츠 */
.main-content {
    max-width: 1100px;
    margin: 40px auto;
    padding: 0 20px;
}

/* 섹션 */
.section {
    background: white;
    border-radius: 20px;
    box-shadow: 0 4px 25px rgba(0,0,0,0.05);
    padding: 35px;
    margin-bottom: 30px;
}
.section-title {
    font-size: 1.2rem;
    color: #1e3a5f;
    margin-bottom: 25px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 10px;
}
.section-title .icon {
    font-size: 1.4rem;
}

/* 카드 그리드 */
.card-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 18px;
}
.card {
    background: linear-gradient(145deg, #f8fafc, #f1f5f9);
    border-radius: 16px;
    padding: 28px 20px;
    text-align: center;
    text-decoration: none;
    color: inherit;
    transition: all 0.3s;
    border: 2px solid transparent;
}
.card:hover {
    background: linear-gradient(145deg, #eff6ff, #dbeafe);
    border-color: #3b82f6;
    transform: translateY(-5px);
    box-shadow: 0 15px 35px rgba(59, 130, 246, 0.15);
}
.card .icon {
    font-size: 2.5rem;
    margin-bottom: 15px;
}
.card .title {
    font-size: 1rem;
    font-weight: 700;
    color: #1e3a5f;
    margin-bottom: 8px;
}
.card .desc {
    font-size: 0.85rem;
    color: #64748b;
    line-height: 1.4;
}

/* 미니 카드 그리드 */
.mini-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 15px;
}
.mini-card {
    background: #f8fafc;
    border-radius: 14px;
    padding: 22px 15px;
    text-align: center;
    text-decoration: none;
    color: inherit;
    transition: all 0.25s;
    border: 1px solid #e2e8f0;
}
.mini-card:hover {
    background: #eff6ff;
    border-color: #93c5fd;
    transform: translateY(-3px);
}
.mini-card .icon {
    font-size: 1.8rem;
    margin-bottom: 10px;
}
.mini-card .title {
    font-size: 0.9rem;
    font-weight: 600;
    color: #334155;
}

/* 푸터 */
.footer {
    background: #1e3a5f;
    padding: 40px;
    text-align: center;
    color: rgba(255,255,255,0.7);
}
.footer p { margin: 5px 0; font-size: 0.9rem; }
.footer .brand {
    font-size: 1.2rem;
    font-weight: 700;
    color: white;
    margin-bottom: 10px;
}

/* 반응형 */
@media (max-width: 900px) {
    .card-grid { grid-template-columns: repeat(2, 1fr); }
    .mini-grid { grid-template-columns: repeat(3, 1fr); }
    .header { padding: 15px 20px; }
    .hero { padding: 40px 20px; }
    .hero h1 { font-size: 1.8rem; }
}
@media (max-width: 500px) {
    .card-grid { grid-template-columns: 1fr; }
    .mini-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
""", unsafe_allow_html=True)

# 헤더
if LOGO_BASE64:
    logo_html = f'<img src="data:image/png;base64,{LOGO_BASE64}" alt="flyready_lab">'
else:
    logo_html = '<span style="color: #3b82f6;">flyready</span><span style="color: #1e3a5f;">_lab</span>'

st.markdown(f'''
<div class="header">
    <a href="/" class="logo">{logo_html}</a>
</div>
''', unsafe_allow_html=True)

# 히어로 섹션
st.markdown('''
<div class="hero">
    <h1>✈️ AI와 함께하는 승무원 면접 준비</h1>
    <p>실전 모의면접부터 자소서 첨삭, 롤플레잉까지<br>당신의 합격을 위한 모든 준비가 여기에</p>
    <div class="hero-buttons">
        <a href="/모의면접" class="hero-btn primary">🎤 모의면접 시작</a>
        <a href="/롤플레잉" class="hero-btn secondary">🎭 롤플레잉</a>
        <a href="/자소서첨삭" class="hero-btn secondary">📝 자소서 첨삭</a>
    </div>
</div>
''', unsafe_allow_html=True)

# 메인 컨텐츠 시작
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# 베타 테스트 배너 & 사용량 요약
if USAGE_LIMITER_AVAILABLE:
    render_beta_banner()
    st.markdown(render_usage_summary(), unsafe_allow_html=True)

# 섹션 1: 면접 연습
st.markdown('''
<div class="section">
    <div class="section-title"><span class="icon">🎤</span> 면접 연습</div>
    <div class="card-grid">
        <a href="/모의면접" class="card">
            <div class="icon">🎤</div>
            <div class="title">AI 모의면접</div>
            <div class="desc">실전처럼 연습하고<br>즉시 피드백 받기</div>
        </a>
        <a href="/롤플레잉" class="card">
            <div class="icon">🎭</div>
            <div class="title">기내 롤플레잉</div>
            <div class="desc">실제 기내 상황<br>시뮬레이션</div>
        </a>
        <a href="/영어면접" class="card">
            <div class="icon">🌐</div>
            <div class="title">영어면접</div>
            <div class="desc">영어 질문<br>답변 연습</div>
        </a>
        <a href="/토론면접" class="card">
            <div class="icon">💬</div>
            <div class="title">토론면접</div>
            <div class="desc">그룹 토론<br>시뮬레이션</div>
        </a>
    </div>
</div>
''', unsafe_allow_html=True)

# 섹션 2: 준비 도구
st.markdown('''
<div class="section">
    <div class="section-title"><span class="icon">📚</span> 준비 도구</div>
    <div class="card-grid">
        <a href="/자소서첨삭" class="card">
            <div class="icon">📝</div>
            <div class="title">자소서 AI 첨삭</div>
            <div class="desc">AI가 자소서<br>피드백 제공</div>
        </a>
        <a href="/자소서기반질문" class="card">
            <div class="icon">❓</div>
            <div class="title">자소서 기반 질문</div>
            <div class="desc">예상 질문<br>자동 생성</div>
        </a>
        <a href="/이미지메이킹" class="card">
            <div class="icon">👗</div>
            <div class="title">이미지메이킹</div>
            <div class="desc">메이크업/복장<br>가이드</div>
        </a>
        <a href="/기내방송연습" class="card">
            <div class="icon">🎙️</div>
            <div class="title">기내방송 연습</div>
            <div class="desc">한국어/영어<br>기내방송</div>
        </a>
    </div>
</div>
''', unsafe_allow_html=True)

# 섹션 3: 학습/커뮤니티
st.markdown('''
<div class="section">
    <div class="section-title"><span class="icon">🎯</span> 학습 · 정보</div>
    <div class="mini-grid">
        <a href="/항공상식퀴즈" class="mini-card">
            <div class="icon">✈️</div>
            <div class="title">항공 상식 퀴즈</div>
        </a>
        <a href="/면접꿀팁" class="mini-card">
            <div class="icon">💡</div>
            <div class="title">면접 꿀팁</div>
        </a>
        <a href="/항공사가이드" class="mini-card">
            <div class="icon">🏢</div>
            <div class="title">항공사 가이드</div>
        </a>
        <a href="/체력준비" class="mini-card">
            <div class="icon">🏊</div>
            <div class="title">체력 준비</div>
        </a>
        <a href="/기업분석" class="mini-card">
            <div class="icon">📊</div>
            <div class="title">기업 분석</div>
        </a>
    </div>
</div>
''', unsafe_allow_html=True)

# 섹션 4: 관리
st.markdown('''
<div class="section">
    <div class="section-title"><span class="icon">📋</span> 학습 관리</div>
    <div class="mini-grid">
        <a href="/진도관리" class="mini-card">
            <div class="icon">📈</div>
            <div class="title">진도 관리</div>
        </a>
        <a href="/성장그래프" class="mini-card">
            <div class="icon">📉</div>
            <div class="title">성장 그래프</div>
        </a>
        <a href="/채용알림" class="mini-card">
            <div class="icon">📢</div>
            <div class="title">채용 알림</div>
        </a>
        <a href="/합격자DB" class="mini-card">
            <div class="icon">🏆</div>
            <div class="title">합격자 DB</div>
        </a>
        <a href="/D데이캘린더" class="mini-card">
            <div class="icon">📅</div>
            <div class="title">D-Day</div>
        </a>
    </div>
</div>
''', unsafe_allow_html=True)

# 메인 컨텐츠 종료
st.markdown('</div>', unsafe_allow_html=True)

# 푸터
st.markdown('''
<div class="footer">
    <div class="brand">✈️ flyready_lab</div>
    <p>당신의 꿈을 응원합니다</p>
    <p style="margin-top: 15px; font-size: 0.8rem; opacity: 0.6;">© 2024 flyready_lab. All rights reserved.</p>
</div>
''', unsafe_allow_html=True)

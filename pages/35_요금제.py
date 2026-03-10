# 35_요금제.py

# 정식 웹사이트 이전 안내
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from redirect_to_web import show_redirect_and_stop
show_redirect_and_stop()

import streamlit as st

st.set_page_config(
    page_title="요금제 - FlyReady Lab",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

css = """<base target="_self">
<script>
document.addEventListener('click', function(e) {
    var target = e.target;
    while (target && target.tagName !== 'A') {
        target = target.parentNode;
    }
    if (target && target.tagName === 'A') {
        var href = target.getAttribute('href');
        if (href && href.startsWith('/') && !href.startsWith('//')) {
            e.preventDefault();
            window.location.href = href;
        }
    }
});
</script>

<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
* { font-family: 'Pretendard', sans-serif; }
[data-testid="stSidebar"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
header[data-testid="stHeader"] { display: none; }
.block-container { padding: 0 !important; max-width: 100% !important; }
.stApp { background: #f8fafc; }
.pricing-header { background: white; padding: 16px 48px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.pricing-logo { font-size: 1.25rem; font-weight: 800; color: #1e3a5f; text-decoration: none; }
.pricing-logo span { color: #3b82f6; }
.pricing-back { color: #475569; text-decoration: none; font-weight: 600; padding: 8px 16px; border-radius: 6px; transition: all 0.2s; }
.pricing-back:hover { background: #eff6ff; color: #3b82f6; }
.pricing-section { background: white; padding: 60px 24px; min-height: calc(100vh - 80px); }
.pricing-inner { max-width: 1200px; margin: 0 auto; }
.pricing-title { font-size: 2.5rem; font-weight: 800; color: #1e3a5f; text-align: center; margin-bottom: 16px; }
.pricing-subtitle { font-size: 1.1rem; color: #64748b; text-align: center; margin-bottom: 48px; }
.pricing-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
@media (max-width: 900px) { .pricing-grid { grid-template-columns: 1fr; } .pricing-header { padding: 12px 20px; } }
.pricing-card { background: white; border-radius: 16px; padding: 32px 24px; border: 2px solid #e2e8f0; text-align: center; transition: all 0.3s; }
.pricing-card:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.08); }
.pricing-card.popular { border-color: #3b82f6; position: relative; }
.pricing-card.premium { border-color: #8b5cf6; }
.pricing-card.premium-plus { border-color: #f59e0b; }
.plan-price.premium-plus { color: #f59e0b; }
.plan-btn-premium-plus { background: #d97706 !important; color: #FFFFFF !important; }
.plan-btn-premium-plus:hover { background: #b45309 !important; color: #FFFFFF !important; }
.popular-badge { position: absolute; top: -14px; left: 50%; transform: translateX(-50%); background: #3b82f6; color: white; font-size: 0.8rem; font-weight: 600; padding: 6px 16px; border-radius: 20px; }
.plan-name { font-size: 1.25rem; font-weight: 700; color: #1e3a5f; margin-bottom: 8px; }
.plan-price { font-size: 2.5rem; font-weight: 800; margin-bottom: 4px; }
.plan-price.free { color: #1e3a5f; }
.plan-price.standard { color: #3b82f6; }
.plan-price.premium { color: #8b5cf6; }
.plan-period { font-size: 0.9rem; color: #64748b; margin-bottom: 24px; }
.plan-features { list-style: none; padding: 0; margin: 0 0 24px 0; text-align: left; }
.section-label { font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; padding: 12px 0 4px 0; border-top: 1px solid #e2e8f0; margin-top: 8px; }
.section-label:first-child { border-top: none; margin-top: 0; }
.plan-features li { display: flex; align-items: center; gap: 10px; padding: 10px 0; font-size: 0.9rem; color: #334155; }
.check { color: #22c55e; font-weight: bold; }
.limited { color: #f59e0b; font-weight: bold; }
.cross { color: #cbd5e1; }
.plan-btn { display: block; width: 100%; padding: 16px; border-radius: 10px; font-size: 1rem; font-weight: 700; text-decoration: none; text-align: center; transition: all 0.2s; box-sizing: border-box; }
.plan-btn-secondary { background: #e2e8f0; color: #475569; }
.plan-btn-secondary:hover { background: #cbd5e1; }
.plan-btn-primary { background: #1d4ed8 !important; color: #FFFFFF !important; }
.plan-btn-primary:hover { background: #1e40af !important; color: #FFFFFF !important; }
.plan-btn-premium { background: #6d28d9 !important; color: #FFFFFF !important; }
.plan-btn-premium:hover { background: #5b21b6 !important; color: #FFFFFF !important; }
.feature-note { font-size: 0.85rem; color: #94a3b8; text-align: center; margin-top: 40px; padding-top: 24px; border-top: 1px solid #e2e8f0; }

/* Material Icon 텍스트 폴백 숨김 */
[data-testid="stIconMaterial"] {
    font-size: 0 !important;
    line-height: 0 !important;
    overflow: hidden !important;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

header = """
<div class="pricing-header">
    <a target="_self" href="/" class="pricing-logo"><span>Fly</span>Ready Lab</a>
    <a target="_self" href="/" class="pricing-back">← 홈으로</a>
</div>
"""
st.markdown(header, unsafe_allow_html=True)

pricing = """
<div class="pricing-section">
    <div class="pricing-inner">
        <h1 class="pricing-title">요금제</h1>
        <p class="pricing-subtitle">나에게 맞는 플랜을 선택하세요</p>
        <div style="background: linear-gradient(135deg, #8b5cf6, #6d28d9); color: white; padding: 16px 24px; border-radius: 12px; text-align: center; margin-bottom: 32px;">
            <span style="font-size: 1.1rem; font-weight: 700;">🎁 프리미엄 3일 무료 체험</span>
            <span style="margin-left: 12px; opacity: 0.9;">모든 기능을 먼저 경험해보세요</span>
        </div>
        <div class="pricing-grid">
            <div class="pricing-card">
                <div class="plan-name">FREE</div>
                <div class="plan-price free">₩0</div>
                <div class="plan-period">무료</div>
                <ul class="plan-features">
                    <li class="section-label">면접 연습</li>
                    <li><span class="limited">△</span> 주 1회 모의면접</li>
                    <li><span class="limited">△</span> 1개 시나리오 (자기소개)</li>
                    <li><span class="limited">△</span> 점수만 제공 (피드백 없음)</li>
                    <li class="section-label">학습 자료</li>
                    <li><span class="limited">△</span> 월 1회 자소서 첨삭</li>
                    <li><span class="limited">△</span> 10문항 퀴즈 맛보기</li>
                    <li class="section-label">학습 관리</li>
                    <li><span class="limited">△</span> 최근 3일 성장 그래프</li>
                    <li><span class="limited">△</span> 1개 일정만 관리</li>
                    <li class="section-label">미지원</li>
                    <li><span class="cross">✗</span> 롤플레잉 / 토론면접</li>
                    <li><span class="cross">✗</span> 영어면접 / 음성면접</li>
                    <li><span class="cross">✗</span> 스터디 매칭</li>
                </ul>
                <a target="_self" href="#" class="plan-btn plan-btn-secondary">현재 플랜</a>
            </div>
            <div class="pricing-card popular">
                <span class="popular-badge">인기</span>
                <div class="plan-name">STANDARD</div>
                <div class="plan-price standard">₩29,000</div>
                <div class="plan-period">월간 구독</div>
                <ul class="plan-features">
                    <li class="section-label">면접 연습</li>
                    <li><span class="check">✓</span> 하루 3회 모의면접</li>
                    <li><span class="check">✓</span> 10개 시나리오</li>
                    <li><span class="check">✓</span> 기본 피드백 (3축 평가)</li>
                    <li class="section-label">학습 자료</li>
                    <li><span class="check">✓</span> 주 3회 자소서 첨삭</li>
                    <li><span class="check">✓</span> 전체 187문항 퀴즈</li>
                    <li class="section-label">연습 기능</li>
                    <li><span class="check">✓</span> 롤플레잉 (하루 2회)</li>
                    <li><span class="check">✓</span> 토론면접 (하루 1회)</li>
                    <li><span class="check">✓</span> 표정연습 / 기내방송</li>
                    <li class="section-label">스터디 플랜</li>
                    <li><span class="limited">△</span> 스터디 매칭 (무료)</li>
                    <li><span class="limited">△</span> 스터디 기능 (+₩30,000)</li>
                    <li class="section-label">미지원</li>
                    <li><span class="cross">✗</span> 음성 면접 / 영어 면접</li>
                </ul>
                <a target="_self" href="/구독" class="plan-btn plan-btn-primary">구독하기</a>
            </div>
            <div class="pricing-card premium">
                <div class="plan-name">PREMIUM</div>
                <div class="plan-price premium">₩49,000</div>
                <div class="plan-period">월간 구독</div>
                <ul class="plan-features">
                    <li class="section-label">면접 연습</li>
                    <li><span class="check">✓</span> 무제한 모의면접</li>
                    <li><span class="check">✓</span> 모든 시나리오 + 고급</li>
                    <li><span class="check">✓</span> AI 심층 분석 피드백</li>
                    <li class="section-label">PREMIUM 전용</li>
                    <li><span class="check">✓</span> 음성 면접 / 영어 면접</li>
                    <li><span class="check">✓</span> 롤플레잉 / 토론 무제한</li>
                    <li><span class="check">✓</span> 합격자 DB 분석</li>
                    <li class="section-label">커스텀 면접</li>
                    <li><span class="check">✓</span> 에어로케이 맞춤 분석</li>
                    <li class="section-label">스터디 플랜 무료 포함</li>
                    <li><span class="check">✓</span> 스터디 매칭 (무료)</li>
                    <li><span class="check">✓</span> 스터디 기능 (무료)</li>
                    <li><span class="check">✓</span> 다각도 촬영 분석</li>
                    <li class="section-label">추가 혜택</li>
                    <li><span class="check">✓</span> 우선 고객 지원</li>
                </ul>
                <a target="_self" href="/구독" class="plan-btn plan-btn-premium">프리미엄 시작</a>
            </div>
            <div class="pricing-card premium-plus">
                <div class="plan-name">PREMIUM+ CUSTOM</div>
                <div class="plan-price premium-plus">₩69,000</div>
                <div class="plan-period">월간 구독</div>
                <ul class="plan-features">
                    <li class="section-label">PREMIUM 전체 포함</li>
                    <li><span class="check">✓</span> 프리미엄 모든 기능</li>
                    <li><span class="check">✓</span> 스터디 플랜 무료</li>
                    <li class="section-label">10개 항공사 커스텀</li>
                    <li><span class="check">✓</span> 대한항공 맞춤 분석</li>
                    <li><span class="check">✓</span> 아시아나 맞춤 분석</li>
                    <li><span class="check">✓</span> 진에어 맞춤 분석</li>
                    <li><span class="check">✓</span> 티웨이 맞춤 분석</li>
                    <li><span class="check">✓</span> 제주항공 맞춤 분석</li>
                    <li><span class="check">✓</span> 에어부산 맞춤 분석</li>
                    <li><span class="check">✓</span> 에어서울 맞춤 분석</li>
                    <li><span class="check">✓</span> 이스타항공 맞춤 분석</li>
                    <li><span class="check">✓</span> 파라타항공 맞춤 분석</li>
                    <li><span class="check">✓</span> 에어프레미아 맞춤 분석</li>
                    <li class="section-label">전용 혜택</li>
                    <li><span class="check">✓</span> 항공사별 포트폴리오 분석</li>
                    <li><span class="check">✓</span> 1:1 우선 지원</li>
                </ul>
                <a target="_self" href="/구독" class="plan-btn plan-btn-premium-plus">커스텀 시작</a>
            </div>
        </div>
        <p class="feature-note">
            △ 제한된 기능 | ✓ 포함 | ✗ 미지원<br>
            모든 요금제는 언제든지 해지할 수 있습니다.
        </p>
    </div>
</div>
"""
st.markdown(pricing, unsafe_allow_html=True)

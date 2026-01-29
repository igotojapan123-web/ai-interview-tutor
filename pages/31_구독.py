# pages/31_구독.py
# FlyReady Lab - 구독/결제 페이지

import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="구독 플랜 - FlyReady Lab",
    page_icon="✈️",
    layout="wide"
)

# 시스템 import
try:
    from auth_system import AuthManager
    from payment_system import PaymentManager, PRODUCTS
    AUTH_AVAILABLE = True
    PAYMENT_AVAILABLE = True
    auth_manager = AuthManager()
    payment_manager = PaymentManager()
except ImportError as e:
    AUTH_AVAILABLE = False
    PAYMENT_AVAILABLE = False

# CSS
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
* { font-family: 'Pretendard', -apple-system, sans-serif; }
[data-testid="stSidebar"] { display: none; }
.block-container { max-width: 1000px; padding-top: 40px; }

.pricing-header {
    text-align: center;
    margin-bottom: 48px;
}
.pricing-header h1 {
    font-size: 2rem;
    font-weight: 800;
    color: #1e3a5f;
    margin-bottom: 12px;
}
.pricing-header p {
    color: #64748b;
    font-size: 1rem;
}

.pricing-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    margin-bottom: 48px;
}
.pricing-card {
    background: white;
    border-radius: 16px;
    padding: 32px 28px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    border: 2px solid transparent;
    transition: all 0.3s;
    position: relative;
}
.pricing-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.1);
}
.pricing-card.popular {
    border-color: #3b82f6;
    transform: scale(1.02);
}
.popular-badge {
    position: absolute;
    top: -12px;
    left: 50%;
    transform: translateX(-50%);
    background: #3b82f6;
    color: white;
    padding: 4px 16px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
}
.plan-name {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1e3a5f;
    margin-bottom: 8px;
}
.plan-price {
    margin-bottom: 20px;
}
.plan-price .amount {
    font-size: 2.5rem;
    font-weight: 800;
    color: #1e3a5f;
}
.plan-price .period {
    font-size: 0.9rem;
    color: #64748b;
}
.plan-desc {
    font-size: 0.9rem;
    color: #64748b;
    margin-bottom: 24px;
    min-height: 48px;
}
.plan-features {
    list-style: none;
    padding: 0;
    margin: 0 0 28px 0;
}
.plan-features li {
    padding: 8px 0;
    font-size: 0.9rem;
    color: #334155;
    display: flex;
    align-items: center;
    gap: 10px;
}
.plan-features li::before {
    content: '✓';
    color: #10b981;
    font-weight: 700;
}
.plan-features li.disabled {
    color: #94a3b8;
    text-decoration: line-through;
}
.plan-features li.disabled::before {
    content: '✗';
    color: #cbd5e1;
}
.plan-btn {
    display: block;
    width: 100%;
    padding: 14px;
    border-radius: 10px;
    font-size: 0.95rem;
    font-weight: 600;
    text-align: center;
    text-decoration: none;
    transition: all 0.2s;
}
.plan-btn-primary {
    background: #3b82f6;
    color: white;
}
.plan-btn-primary:hover {
    background: #2563eb;
}
.plan-btn-secondary {
    background: #f1f5f9;
    color: #334155;
}
.plan-btn-secondary:hover {
    background: #e2e8f0;
}

.faq-section {
    background: #f8fafc;
    border-radius: 16px;
    padding: 32px;
}
.faq-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1e3a5f;
    margin-bottom: 24px;
}

@media (max-width: 768px) {
    .pricing-grid { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)

# 헤더
st.markdown("""
<div class="pricing-header">
    <h1>나에게 맞는 플랜 선택</h1>
    <p>합격까지 함께하는 FlyReady Lab의 프리미엄 서비스</p>
</div>
""", unsafe_allow_html=True)

# 플랜 카드
st.markdown("""
<div class="pricing-grid">
    <!-- FREE -->
    <div class="pricing-card">
        <div class="plan-name">FREE</div>
        <div class="plan-price">
            <span class="amount">₩0</span>
            <span class="period">/월</span>
        </div>
        <div class="plan-desc">면접 준비를 시작하는 분들을 위한 기본 플랜</div>
        <ul class="plan-features">
            <li>AI 모의면접 일 3회</li>
            <li>기본 학습 콘텐츠</li>
            <li>항공상식 퀴즈</li>
            <li>커뮤니티 접근</li>
            <li class="disabled">자소서 AI 첨삭</li>
            <li class="disabled">1:1 멘토 상담</li>
            <li class="disabled">채용 알림</li>
        </ul>
        <a href="/" class="plan-btn plan-btn-secondary">현재 플랜</a>
    </div>

    <!-- STANDARD (인기) -->
    <div class="pricing-card popular">
        <div class="popular-badge">BEST</div>
        <div class="plan-name">STANDARD</div>
        <div class="plan-price">
            <span class="amount">₩19,900</span>
            <span class="period">/월</span>
        </div>
        <div class="plan-desc">본격적인 면접 준비를 위한 추천 플랜</div>
        <ul class="plan-features">
            <li>AI 모의면접 일 50회</li>
            <li>전체 학습 콘텐츠</li>
            <li>자소서 AI 첨삭 월 10회</li>
            <li>개인화 추천 시스템</li>
            <li>채용 알림 서비스</li>
            <li>합격자 자소서 열람</li>
            <li class="disabled">1:1 멘토 상담</li>
        </ul>
        <a href="#" class="plan-btn plan-btn-primary" id="btn-standard">시작하기</a>
    </div>

    <!-- PREMIUM -->
    <div class="pricing-card">
        <div class="plan-name">PREMIUM</div>
        <div class="plan-price">
            <span class="amount">₩39,900</span>
            <span class="period">/월</span>
        </div>
        <div class="plan-desc">합격을 위한 올인원 프리미엄 플랜</div>
        <ul class="plan-features">
            <li>AI 모의면접 무제한</li>
            <li>전체 학습 콘텐츠</li>
            <li>자소서 AI 첨삭 무제한</li>
            <li>1:1 멘토 상담 월 2회</li>
            <li>프리미엄 채용 알림</li>
            <li>실시간 면접 코칭</li>
            <li>우선 고객 지원</li>
        </ul>
        <a href="#" class="plan-btn plan-btn-primary" id="btn-premium">시작하기</a>
    </div>
</div>
""", unsafe_allow_html=True)

# 결제 처리
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("결제 방법 선택")

    plan = st.selectbox(
        "플랜 선택",
        ["standard_monthly", "standard_yearly", "premium_monthly", "premium_yearly"],
        format_func=lambda x: {
            "standard_monthly": "STANDARD 월간 - ₩19,900/월",
            "standard_yearly": "STANDARD 연간 - ₩149,000/년 (37% 할인)",
            "premium_monthly": "PREMIUM 월간 - ₩39,900/월",
            "premium_yearly": "PREMIUM 연간 - ₩299,000/년 (38% 할인)"
        }.get(x, x)
    )

    payment_method = st.radio(
        "결제 수단",
        ["kakaopay", "toss"],
        format_func=lambda x: "카카오페이" if x == "kakaopay" else "토스페이먼츠",
        horizontal=True
    )

    if st.button("결제하기", type="primary", use_container_width=True):
        user_id = st.session_state.get("user_id")

        if not user_id:
            st.warning("로그인이 필요합니다.")
            st.page_link("pages/30_로그인.py", label="로그인하기")
        elif PAYMENT_AVAILABLE:
            try:
                result = payment_manager.initiate_payment(
                    user_id=user_id,
                    product_id=plan,
                    method=payment_method
                )

                if result.get("success"):
                    st.success("결제 페이지로 이동합니다...")
                    # 실제로는 result['redirect_url']로 리다이렉트
                    st.markdown(f"[결제 페이지로 이동]({result.get('redirect_url', '#')})")
                else:
                    st.error(f"결제 초기화 실패: {result.get('error')}")
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
        else:
            st.info("결제 시스템 준비 중입니다. 곧 서비스됩니다!")

with col2:
    st.subheader("자주 묻는 질문")

    with st.expander("결제 후 바로 이용 가능한가요?"):
        st.write("네, 결제 완료 즉시 모든 기능을 이용하실 수 있습니다.")

    with st.expander("환불 정책은 어떻게 되나요?"):
        st.write("결제 후 7일 이내 미사용시 전액 환불 가능합니다. 이후에는 잔여 기간에 따라 부분 환불됩니다.")

    with st.expander("연간 플랜의 혜택은 무엇인가요?"):
        st.write("연간 플랜은 월간 대비 약 37~38% 할인된 가격으로 이용 가능하며, 멘토 상담 추가 쿠폰이 제공됩니다.")

    with st.expander("플랜 변경이 가능한가요?"):
        st.write("언제든지 상위 플랜으로 업그레이드 가능합니다. 남은 기간은 일할 계산되어 적용됩니다.")

# 하단
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#64748b;font-size:0.85rem;">
    결제 관련 문의: support@flyreadylab.com<br>
    안전한 결제를 위해 카카오페이, 토스페이먼츠를 이용합니다.
</div>
""", unsafe_allow_html=True)

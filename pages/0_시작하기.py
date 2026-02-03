# pages/0_시작하기.py
# FlyReady Lab 시작 가이드 - 간결하고 핵심만

import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sidebar_common import init_page, end_page

init_page(
    title="시작하기",
    current_page="시작하기",
    wide_layout=True
)

# CSS
st.markdown("""
<style>
.guide-card {
    background: linear-gradient(135deg, #f8fafc 0%, #fff 100%);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 16px;
    border: 1px solid #e2e8f0;
    transition: all 0.2s;
}
.guide-card:hover {
    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    transform: translateY(-2px);
}
.guide-number {
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 700;
    font-size: 14px;
    margin-right: 12px;
}
.guide-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #1e293b;
    display: inline;
}
.guide-desc {
    color: #64748b;
    font-size: 0.95rem;
    margin-top: 12px;
    line-height: 1.6;
}
.guide-time {
    background: #f1f5f9;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.8rem;
    color: #64748b;
    margin-top: 12px;
    display: inline-block;
}
.core-principle {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    color: white;
    border-radius: 16px;
    padding: 28px;
    margin: 24px 0;
    text-align: center;
}
.core-principle h3 {
    color: white;
    margin-bottom: 12px;
}
.core-principle p {
    color: #94a3b8;
    font-size: 1rem;
}
.path-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    border: 2px solid #e2e8f0;
    cursor: pointer;
    transition: all 0.2s;
}
.path-card:hover {
    border-color: #2563eb;
}
.path-selected {
    border-color: #2563eb;
    background: #eff6ff;
}
</style>
""", unsafe_allow_html=True)

# 핵심 메시지
st.markdown("""
<div class="core-principle">
    <h3>FlyReady Lab의 핵심</h3>
    <p>"잘 말했는가?" ❌ → "이 사람을 실제 비행에 투입해도 되는가?" ⭕</p>
</div>
""", unsafe_allow_html=True)

# 3단계 가이드 (간결하게)
st.markdown("### 3분 안에 시작하기")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="guide-card">
        <span class="guide-number">1</span>
        <span class="guide-title">목표 항공사 선택</span>
        <p class="guide-desc">지원할 항공사를 선택하면 해당 항공사 인재상에 맞춘 질문과 피드백을 받습니다.</p>
        <span class="guide-time">30초</span>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="guide-card">
        <span class="guide-number">2</span>
        <span class="guide-title">모의면접 시작</span>
        <p class="guide-desc">바로 면접 연습을 시작하세요. 녹음 또는 텍스트로 답변하고 즉시 피드백을 받습니다.</p>
        <span class="guide-time">10분~</span>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="guide-card">
        <span class="guide-number">3</span>
        <span class="guide-title">피드백 확인</span>
        <p class="guide-desc">"투입 가능성 판단" 관점에서 구체적인 피드백과 개선 방향을 확인합니다.</p>
        <span class="guide-time">2분</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 바로 시작 버튼
st.markdown("### 바로 시작하기")

start_col1, start_col2, start_col3, start_col4 = st.columns(4)

with start_col1:
    if st.button("모의면접", type="primary", use_container_width=True):
        st.switch_page("pages/4_모의면접.py")
    st.caption("가장 많이 사용하는 기능")

with start_col2:
    if st.button("롤플레잉", use_container_width=True):
        st.switch_page("pages/1_롤플레잉.py")
    st.caption("기내 상황 대응 연습")

with start_col3:
    if st.button("영어면접", use_container_width=True):
        st.switch_page("pages/2_영어면접.py")
    st.caption("영어 답변 연습")

with start_col4:
    if st.button("자소서 분석", use_container_width=True):
        st.switch_page("pages/20_자소서첨삭.py")
    st.caption("자소서 기반 질문 준비")

st.markdown("---")

# 학습 방향 제안 (자유도 부여)
st.markdown("### 나에게 맞는 학습 방법 선택")
st.caption("아래는 추천 경로입니다. 자유롭게 원하는 기능을 먼저 사용해도 됩니다.")

path_col1, path_col2, path_col3 = st.columns(3)

with path_col1:
    with st.container():
        st.markdown("**처음 시작하는 분**")
        st.markdown("""
        1. 모의면접 1회 체험
        2. 피드백 확인
        3. 부족한 부분 집중 연습
        """)
        if st.button("이 경로로 시작", key="path1", use_container_width=True):
            st.switch_page("pages/4_모의면접.py")

with path_col2:
    with st.container():
        st.markdown("**자소서 완성한 분**")
        st.markdown("""
        1. 자소서 분석
        2. 예상 질문 확인
        3. 자소서 기반 면접 연습
        """)
        if st.button("이 경로로 시작", key="path2", use_container_width=True):
            st.switch_page("pages/20_자소서첨삭.py")

with path_col3:
    with st.container():
        st.markdown("**면접 경험 있는 분**")
        st.markdown("""
        1. 약점 파악 (진도관리)
        2. 약점 집중 연습
        3. 실전 모의면접
        """)
        if st.button("이 경로로 시작", key="path3", use_container_width=True):
            st.switch_page("pages/3_진도관리.py")

st.markdown("---")

# 핵심 팁 (간결하게)
with st.expander("FlyReady Lab 200% 활용 팁", expanded=False):
    st.markdown("""
    **피드백 읽는 법**
    - `[투입 가능성 판단]` 섹션이 가장 중요합니다
    - "추가 확인 필요" = 그 부분을 보완해야 합격 확률 상승
    - 구체적인 상황/숫자를 답변에 포함하면 신뢰도 상승

    **연습 순서 추천**
    - 질문당 3회 반복 → 피드백 패턴 파악
    - 같은 질문, 다른 경험으로 답변 연습
    - 압박 질문은 마지막에 도전

    **시간 관리**
    - 하루 30분이면 충분합니다
    - 매일 조금씩 > 가끔 많이
    """)

# 진도관리 링크
st.info("**학습 기록은 자동 저장됩니다.** 진도 확인: [진도관리 페이지](/진도관리)")

end_page()

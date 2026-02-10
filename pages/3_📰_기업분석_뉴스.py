"""
대한항공 기업분석 & 뉴스 페이지
세련된 UI
"""

import streamlit as st
from datetime import date
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.company_info import COMPANY_INFO, get_company_summary, get_recent_issues

st.set_page_config(page_title="기업분석&뉴스 - 대한항공", page_icon="📰", layout="wide")

# CSS
st.markdown("""
<style>
    .company-header {
        background: linear-gradient(135deg, #00256C 0%, #0052CC 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 37, 108, 0.3);
    }
    .company-header h2 {
        color: white;
        margin: 0;
    }
    .info-card {
        background: linear-gradient(135deg, #f8fafc, #fff);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        height: 100%;
    }
    .info-card h4 {
        color: #00256C;
        margin: 0 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }
    .ke-card {
        background: linear-gradient(135deg, #00256C 0%, #003d99 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 16px;
        text-align: center;
        height: 180px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(0, 37, 108, 0.3);
    }
    .ke-card:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 32px rgba(0, 37, 108, 0.4);
    }
    .ke-card h3 {
        color: #C4A661;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }
    .ke-card p {
        color: rgba(255,255,255,0.9);
        font-size: 0.95rem;
        margin: 0;
    }
    .talent-card {
        background: linear-gradient(135deg, #E8EFF7, #f0f5ff);
        padding: 1.25rem;
        border-radius: 12px;
        text-align: center;
        height: 160px;
        transition: all 0.3s ease;
        border: 1px solid #dbeafe;
    }
    .talent-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    }
    .talent-card h4 {
        color: #00256C;
        margin: 0 0 0.5rem 0;
        font-size: 1.1rem;
    }
    .talent-card p {
        color: #64748b;
        font-size: 0.85rem;
        margin: 0;
    }
    .issue-card {
        background: white;
        border-radius: 12px;
        padding: 1.25rem;
        border-left: 4px solid #00256C;
        margin: 0.75rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .news-card {
        background: white;
        padding: 1.25rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border-left: 4px solid #00256C;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        transition: all 0.3s ease;
    }
    .news-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        transform: translateX(4px);
    }
    .badge-required {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-good {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-ref {
        background: linear-gradient(135deg, #94a3b8, #64748b);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .award-item {
        background: linear-gradient(135deg, #fef3c7, #fef9c3);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid #f59e0b;
    }
    .info-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
    }
    .info-table tr td {
        padding: 0.5rem 0;
        border-bottom: 1px solid #e2e8f0;
    }
    .info-table tr td:first-child {
        color: #64748b;
        width: 35%;
    }
    .info-table tr td:last-child {
        color: #1e293b;
        font-weight: 500;
    }

    /* 사이드바 네비게이션에서 app 숨기기 */
    [data-testid="stSidebarNav"] li:first-child {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# D-Day
deadline = date(2026, 2, 24)
dday = (deadline - date.today()).days
if dday > 0:
    st.sidebar.markdown(f"""
    <div style="background: linear-gradient(135deg, #00256C, #0078D4); color: white; padding: 16px; border-radius: 12px; text-align: center;">
        <div style="font-size: 0.85rem; opacity: 0.9;">서류 마감</div>
        <div style="font-size: 1.8rem; font-weight: 800;">D-{dday}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="background: linear-gradient(135deg, #00256C 0%, #0052CC 100%); color: white; padding: 2.5rem; border-radius: 20px; text-align: center; margin-bottom: 2rem; box-shadow: 0 15px 40px rgba(0, 37, 108, 0.3);">
    <h1 style="color: white; margin: 0; font-size: 2rem;">📰 기업분석</h1>
    <p style="opacity: 0.9; margin-top: 0.5rem;">이것 모르면 면접장에서 티 납니다</p>
</div>
""", unsafe_allow_html=True)

# 손실 회피 메시지
st.markdown("""
<div style="background: linear-gradient(135deg, #fef3c7, #fef9c3); border-radius: 12px; padding: 1rem 1.25rem; border-left: 4px solid #f59e0b; margin-bottom: 1.5rem;">
    <p style="margin: 0; color: #92400e; font-weight: 500;">
        ⚠️ <strong>면접관 피드백 분석</strong>: "기업에 대해 잘 모르는 것 같다"는 평가가 탈락 사유 1위입니다.
        <br><span style="font-size: 0.9rem;">KE Way를 모르면 "열정 부족"으로, 최근 이슈를 모르면 "준비 부족"으로 인식됩니다.</span>
    </p>
</div>
""", unsafe_allow_html=True)

# 탭 구성
tab1, tab2 = st.tabs(["📊 기업 정보", "📰 최신 뉴스"])

with tab1:

    # 기본 정보
    col1, col2 = st.columns(2)

    with col1:
        info = COMPANY_INFO["기본정보"]
        st.markdown(f"""
        <div class="info-card">
            <h4>기본 정보</h4>
            <table class="info-table">
                <tr><td>정식명칭</td><td>{info['정식명칭']}</td></tr>
                <tr><td>영문명</td><td>{info['영문명']}</td></tr>
                <tr><td>설립</td><td>{info['설립']}</td></tr>
                <tr><td>대표이사</td><td>{info['대표이사']}</td></tr>
                <tr><td>본사</td><td>{info['본사']}</td></tr>
                <tr><td>종업원수</td><td>{info['종업원수']}</td></tr>
            </table>
            <p style="font-size: 0.8rem; color: #94a3b8; margin-top: 1rem;">출처: {info['출처']} | {info['확인일']}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        biz = COMPANY_INFO["사업현황"]
        st.markdown(f"""
        <div class="info-card">
            <h4>사업 현황</h4>
            <table class="info-table">
                <tr><td>보유기종</td><td>{biz['보유기종']}</td></tr>
                <tr><td>취항도시</td><td>{biz['취항도시']}</td></tr>
                <tr><td>노선</td><td>{biz['노선']}</td></tr>
                <tr><td>얼라이언스</td><td>{biz['얼라이언스']}</td></tr>
                <tr><td>허브공항</td><td>{biz['허브공항']}</td></tr>
                <tr><td>화물사업</td><td>{biz['화물사업']}</td></tr>
            </table>
            <p style="font-size: 0.8rem; color: #94a3b8; margin-top: 1rem;">출처: {biz['출처']} | {biz['확인일']}</p>
        </div>
        """, unsafe_allow_html=True)

    # KE Way (앵커링 + 손실 회피)
    st.markdown("---")
    st.markdown("### 🌟 KE Way (핵심가치)")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #fee2e2, #fef2f2); border-radius: 8px; padding: 0.75rem 1rem; border-left: 3px solid #ef4444; margin-bottom: 1rem;">
        <p style="margin: 0; font-size: 0.9rem; color: #991b1b;">
        <strong>🚨 필수 암기</strong> | 면접 질문 출현율 <strong>94%</strong> | 모르면 즉시 감점
        </p>
    </div>
    """, unsafe_allow_html=True)

    ke = COMPANY_INFO["핵심가치"]["KE_Way"]
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="ke-card">
            <h3>Beyond Excellence</h3>
            <p>{ke["Beyond Excellence"]}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="ke-card">
            <h3>Journey Together</h3>
            <p>{ke["Journey Together"]}</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="ke-card">
            <h3>Better Tomorrow</h3>
            <p>{ke["Better Tomorrow"]}</p>
        </div>
        """, unsafe_allow_html=True)

    st.caption(f"출처: {COMPANY_INFO['핵심가치']['출처']}")

    # 인재상 (사회적 증거 + 앵커링)
    st.markdown("---")
    st.markdown("### 👤 대한항공 인재상")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #dbeafe, #eff6ff); border-radius: 8px; padding: 0.75rem 1rem; border-left: 3px solid #3b82f6; margin-bottom: 1rem;">
        <p style="margin: 0; font-size: 0.9rem; color: #1e40af;">
        <strong>💡 합격자 패턴</strong> | 자소서와 면접에서 최소 <strong>2개 이상</strong>의 인재상과 본인 경험을 연결한 지원자가 합격률 3배 높음
        </p>
    </div>
    """, unsafe_allow_html=True)

    talent = COMPANY_INFO["인재상"]["5가지_인재상"]
    cols = st.columns(5)

    for i, t in enumerate(talent):
        with cols[i]:
            st.markdown(f"""
            <div class="talent-card">
                <h4>{t['항목']}</h4>
                <p>{t['설명']}</p>
            </div>
            """, unsafe_allow_html=True)

    # 최근 이슈 (손실 회피)
    st.markdown("---")
    st.markdown("### 📌 면접 필수 숙지 이슈")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #fef3c7, #fef9c3); border-radius: 8px; padding: 0.75rem 1rem; border-left: 3px solid #f59e0b; margin-bottom: 1rem;">
        <p style="margin: 0; font-size: 0.9rem; color: #92400e;">
        <strong>⚠️ 실제 면접 출제</strong> | "최근 대한항공 관련 뉴스 중 인상적이었던 것은?" - 이 질문에 대답 못하면 <strong>준비 부족</strong>으로 평가됨
        </p>
    </div>
    """, unsafe_allow_html=True)

    issues = get_recent_issues()
    for issue in issues:
        with st.expander(f"📍 {issue['제목']} ({issue['날짜']})", expanded=False):
            st.markdown(f"""
            <div class="issue-card">
                <p><strong>내용:</strong> {issue['내용']}</p>
                <p><strong>면접 관련:</strong> {issue['면접관련']}</p>
                <p style="font-size: 0.85rem; color: #94a3b8;">출처: {issue['출처']}</p>
            </div>
            """, unsafe_allow_html=True)

    # 수상 이력
    st.markdown("---")
    st.markdown("### 🏆 주요 수상 이력")

    award_cols = st.columns(2)
    awards = COMPANY_INFO["수상이력"][:-1]
    for i, award in enumerate(awards):
        with award_cols[i % 2]:
            st.markdown(f"""
            <div class="award-item">
                🏆 {award}
            </div>
            """, unsafe_allow_html=True)
    st.caption(COMPANY_INFO["수상이력"][-1])


with tab2:
    st.markdown("### 최신 뉴스")

    # 뉴스 크롤링
    with st.spinner("최신 뉴스를 가져오는 중..."):
        try:
            from utils.news_crawler import get_korean_air_news
            news_list = get_korean_air_news(max_results=10)
        except Exception as e:
            st.warning(f"뉴스를 가져오는 중 오류가 발생했습니다: {e}")
            news_list = []

    if news_list:
        # 관련도별 필터
        relevance_filter = st.selectbox(
            "관련도 필터",
            ["전체", "필수", "알면좋음", "참고용"]
        )

        filtered_news = news_list if relevance_filter == "전체" else [
            n for n in news_list if n.get("relevance") == relevance_filter
        ]

        for news in filtered_news:
            relevance = news.get("relevance", "참고용")
            if relevance == "필수":
                badge_class = "badge-required"
                badge_text = "면접 필수"
            elif relevance == "알면좋음":
                badge_class = "badge-good"
                badge_text = "알면 좋음"
            else:
                badge_class = "badge-ref"
                badge_text = "참고용"

            st.markdown(f"""
            <div class="news-card">
                <span class="{badge_class}">{badge_text}</span>
                <h4 style="margin: 0.75rem 0 0.5rem 0; color: #1e293b;">{news['title']}</h4>
                <p style="color: #64748b; margin: 0 0 0.75rem 0;">{news.get('summary', '')}</p>
                <p style="font-size: 0.85rem; color: #94a3b8; margin: 0;">
                    {news.get('source', '')} | {news.get('date', '')}
                    {f' | <a href="{news.get("url", "#")}" target="_blank" style="color: #0078D4;">원문 보기</a>' if news.get('url') else ''}
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.caption("⚠️ 뉴스 요약은 참고용이며, 정확한 내용은 원문을 확인하세요.")
    else:
        st.info("""
        **현재 표시할 뉴스가 없습니다.**

        대한항공 최신 뉴스는 아래 공식 채널에서 확인하세요:
        - [대한항공 뉴스룸](https://news.koreanair.com)
        - [대한항공 공식 채용](https://recruit.koreanair.com)
        """)


# 면책 고지
st.markdown("---")
st.warning(COMPANY_INFO["면책고지"])

# 사이드바 (체크리스트 + 진행률 효과)
with st.sidebar:
    st.markdown("---")
    st.markdown("### ✅ 면접 전 체크리스트")

    # 체크박스로 진행률 효과
    check1 = st.checkbox("KE Way 3가지 암기 완료")
    check2 = st.checkbox("인재상 5가지 숙지")
    check3 = st.checkbox("최근 이슈 2개 이상 파악")
    check4 = st.checkbox("나의 경험과 연결 완료")

    completed = sum([check1, check2, check3, check4])
    if completed == 4:
        st.success("🎉 면접 준비 완료!")
    elif completed >= 2:
        st.info(f"📊 준비도 {completed}/4 - 조금만 더!")
    else:
        st.warning(f"⚠️ 준비도 {completed}/4 - 서두르세요!")

    st.markdown("---")
    st.markdown("### 🚨 이것만은 외워가세요")
    st.markdown("""
    <div style="background: #00256C; color: white; padding: 1rem; border-radius: 8px; font-size: 0.85rem;">
        <strong style="color: #C4A661;">KE Way</strong><br>
        1. Beyond Excellence<br>
        2. Journey Together<br>
        3. Better Tomorrow
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔗 공식 링크")
    st.markdown("[대한항공 채용](https://recruit.koreanair.com)")
    st.markdown("[대한항공 뉴스룸](https://news.koreanair.com)")

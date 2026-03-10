# pages/41_면접예측.py
# 면접 예측 시스템 - 제보 데이터 기반 질문 출현율 계산

# 정식 웹사이트 이전 안내
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from redirect_to_web import show_redirect_and_stop
show_redirect_and_stop()

import os
import sys
import json
import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path

# 상위 디렉토리 import 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AIRLINES
from sidebar_common import init_page, end_page

# 기존 질문 DB (폴백용)
try:
    from airline_questions import (
        get_airline_questions,
        AIRLINE_SPECIFIC_QUESTIONS,
        COMMON_QUESTIONS
    )
    FALLBACK_DB_AVAILABLE = True
except ImportError:
    FALLBACK_DB_AVAILABLE = False

# 제보 시스템 모듈
try:
    from interview_report_system import (
        get_question_stats,
        get_recent_new_questions,
        get_trending_questions,
        get_airline_report_count,
        get_all_stats
    )
    SYSTEM_AVAILABLE = True
except ImportError as e:
    SYSTEM_AVAILABLE = False
    print(f"[41_면접예측] interview_report_system import 실패: {e}")

# 뉴스 데이터 로드 함수
def load_airline_news(airline: str, days: int = 30):
    """실제 크롤링된 뉴스만 로드 - 뉴스가 없으면 빈 리스트 반환"""
    news_file = Path(__file__).parent.parent / "data" / "airline_news.json"

    if not news_file.exists():
        return []

    try:
        with open(news_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        return []

    # 뉴스 데이터 구조: {"news": {"대한항공": [...], ...}}
    all_news = data.get("news", {}).get(airline, [])

    cutoff = datetime.now() - timedelta(days=days)
    filtered = []

    for news in all_news:
        # 날짜 필터
        try:
            news_date = datetime.fromisoformat(news.get("published_at", "2000-01-01"))
            if news_date >= cutoff:
                # 필드명 정규화
                filtered.append({
                    "title": news.get("title", ""),
                    "summary": news.get("summary", ""),
                    "date": news.get("published_at", ""),
                    "source_url": news.get("url", ""),
                    "source_name": news.get("source", "")
                })
        except:
            continue

    # 최신순 정렬
    filtered.sort(key=lambda x: x.get("date", ""), reverse=True)
    return filtered[:5]  # 최대 5개

# 페이지 초기화
init_page(
    title="면접 예측",
    current_page="면접예측",
    wide_layout=True
)

# ============================================
# CSS 스타일
# ============================================
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

.prediction-header {
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
    padding: 2rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 2rem;
}

.prediction-header h1 {
    margin: 0;
    font-size: 1.8rem;
    font-weight: 700;
}

.prediction-header p {
    margin: 0.5rem 0 0 0;
    opacity: 0.9;
}

.stats-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
}

.question-rank {
    display: flex;
    align-items: flex-start;
    padding: 1rem;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin: 0.5rem 0;
}

.rank-number {
    background: linear-gradient(135deg, #3b82f6, #1e40af);
    color: white;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.9rem;
    margin-right: 1rem;
    flex-shrink: 0;
}

.rank-content {
    flex: 1;
}

.rank-question {
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 0.25rem;
}

.rank-stats {
    font-size: 0.85rem;
    color: #64748b;
}

.percentage-bar {
    height: 6px;
    background: #e2e8f0;
    border-radius: 3px;
    margin-top: 0.5rem;
    overflow: hidden;
}

.percentage-fill {
    height: 100%;
    background: linear-gradient(90deg, #3b82f6, #1e40af);
    border-radius: 3px;
}

.insufficient-data {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border: 2px solid #f59e0b;
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
    margin: 2rem 0;
}

.insufficient-data h2 {
    color: #92400e;
    margin: 0 0 1rem 0;
}

.insufficient-data p {
    color: #78350f;
    margin: 0.5rem 0;
}

.trending-badge {
    display: inline-block;
    background: #dc2626;
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-left: 0.5rem;
}

.new-badge {
    display: inline-block;
    background: #16a34a;
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-left: 0.5rem;
}

.news-item {
    padding: 1rem;
    background: #f8fafc;
    border-left: 3px solid #3b82f6;
    margin: 0.5rem 0;
    border-radius: 0 8px 8px 0;
}

.news-date {
    font-size: 0.8rem;
    color: #64748b;
}

.news-title {
    font-weight: 600;
    color: #1e293b;
    margin: 0.25rem 0;
}

.news-link {
    font-size: 0.85rem;
    color: #3b82f6;
}

.warning-box {
    background: #fef3c7;
    border: 1px solid #f59e0b;
    border-radius: 8px;
    padding: 1rem;
    margin-top: 2rem;
    font-size: 0.9rem;
    color: #92400e;
}

.cta-button {
    display: inline-block;
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: white;
    padding: 12px 24px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ============================================
# 헤더
# ============================================
st.markdown("""
<div class="prediction-header">
    <h1>면접 예측</h1>
    <p>실제 면접 제보 데이터를 기반으로 예상 질문을 확인하세요</p>
</div>
""", unsafe_allow_html=True)

if not SYSTEM_AVAILABLE:
    st.error("예측 시스템을 불러올 수 없습니다. 관리자에게 문의하세요.")
    end_page()
    st.stop()

# ============================================
# 항공사 선택
# ============================================
col1, col2 = st.columns([2, 3])

with col1:
    selected_airline = st.selectbox(
        "항공사 선택",
        options=AIRLINES,
        key="prediction_airline"
    )

with col2:
    # 전체 통계
    all_stats = get_all_stats()
    total_reports = all_stats.get("total_reports", 0)
    st.caption(f"전체 제보: {total_reports}건 | 마지막 업데이트: {all_stats.get('last_updated', '-')[:10] if all_stats.get('last_updated') else '-'}")

st.markdown("---")

# ============================================
# 해당 항공사 데이터 분석
# ============================================
stats = get_question_stats(selected_airline, days=30)
report_count = get_airline_report_count(selected_airline)

# 데이터 부족 시 → 기존 DB에서 질문 가져오기
if not stats["sufficient_data"]:
    st.markdown(f"""
    <div class="insufficient-data">
        <h2>제보 데이터 수집 중</h2>
        <p><strong>현재 {selected_airline} 제보: {report_count}건</strong> (목표: 10건)</p>
        <p>제보가 쌓이면 <strong>실시간 출현율</strong>을 보여드립니다!</p>
        <p style="margin-top: 1rem;">면접 다녀오셨다면 제보해주세요!</p>
        <p style="font-size: 0.9rem; opacity: 0.8;">제보하시면 프리미엄 이용권을 드립니다.</p>
        <a href="/면접제보" target="_self" class="cta-button">제보하러 가기</a>
    </div>
    """, unsafe_allow_html=True)

    # 기존 DB에서 질문 보여주기
    st.markdown("---")
    st.markdown(f"### {selected_airline} 예상 질문 (기존 DB)")
    st.caption("FLYREADY 면접 질문 데이터베이스 기반")

    if FALLBACK_DB_AVAILABLE:
        try:
            # 기존 DB에서 질문 8개 가져오기
            fallback_questions = get_airline_questions(selected_airline, count=8)

            if fallback_questions:
                for i, q in enumerate(fallback_questions, 1):
                    st.markdown(f"""
                    <div class="question-rank">
                        <div class="rank-number">{i}</div>
                        <div class="rank-content">
                            <div class="rank-question">"{q}"</div>
                            <div class="rank-stats" style="color: #64748b;">기존 DB 질문</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("""
                <div class="warning-box">
                    <strong>참고:</strong> 위 질문은 FLYREADY 기존 데이터베이스 기반입니다.
                    제보 데이터가 10건 이상 쌓이면 <strong>실제 출현율</strong>을 보여드립니다.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("해당 항공사 질문 데이터가 없습니다.")
        except Exception as e:
            st.error(f"질문 로드 오류: {e}")
    else:
        st.warning("기존 질문 DB를 불러올 수 없습니다.")

    # 다른 항공사 제보 현황 (접을 수 있게)
    with st.expander("다른 항공사 제보 현황", expanded=False):
        airline_counts = []
        for airline in AIRLINES:
            count = get_airline_report_count(airline)
            airline_counts.append((airline, count))

        airline_counts.sort(key=lambda x: x[1], reverse=True)
        for airline, count in airline_counts[:5]:
            if count >= 10:
                st.write(f"- **{airline}**: {count}건 (실시간 예측 가능)")
            elif count > 0:
                st.write(f"- **{airline}**: {count}건 ({10 - count}건 더 필요)")
            else:
                st.write(f"- **{airline}**: 0건")

else:
    # ============================================
    # 예측 결과 표시 (데이터 충분 시)
    # ============================================
    st.markdown(f"### {selected_airline} 면접 예측 (최근 30일)")
    st.caption(f"총 제보: {stats['total_reports']}건")

    # 질문 출현율 TOP
    st.markdown("#### 질문 출현율 TOP (실시간 제보 기반)")

    if stats["questions"]:
        for i, q in enumerate(stats["questions"][:10], 1):
            percentage = q["percentage"]
            count = q["count"]
            total = stats["total_reports"]

            st.markdown(f"""
            <div class="question-rank">
                <div class="rank-number">{i}</div>
                <div class="rank-content">
                    <div class="rank-question">"{q['question']}"</div>
                    <div class="rank-stats">{percentage}% ({total}건 중 {count}건)</div>
                    <div class="percentage-bar">
                        <div class="percentage-fill" style="width: {percentage}%;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("분석할 질문 데이터가 없습니다.")

    st.markdown("---")

    # 급상승 질문
    col_trend, col_new = st.columns(2)

    with col_trend:
        st.markdown("#### 급상승 질문")
        st.caption("전월 대비 +20%p 이상")

        trending = get_trending_questions(selected_airline)
        if trending:
            for t in trending:
                st.markdown(f"""
                <div class="question-rank" style="padding: 0.75rem;">
                    <div class="rank-content">
                        <div class="rank-question">
                            "{t['question']}"
                            <span class="trending-badge">+{t['diff']}%p</span>
                        </div>
                        <div class="rank-stats">현재 {t['current_pct']}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("급상승 질문이 없습니다.")

    with col_new:
        st.markdown("#### 신규 질문")
        st.caption("최근 7일 내 첫 등장")

        new_questions = get_recent_new_questions(selected_airline, days=7)
        if new_questions:
            for nq in new_questions[:5]:
                st.markdown(f"""
                <div class="question-rank" style="padding: 0.75rem;">
                    <div class="rank-content">
                        <div class="rank-question">
                            "{nq['question']}"
                            <span class="new-badge">NEW</span>
                        </div>
                        <div class="rank-stats">{nq['count']}건 제보</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("신규 질문이 없습니다.")

    st.markdown("---")

# 관련 뉴스
st.markdown("#### 면접 전 체크할 뉴스")
st.caption("실제 크롤링된 뉴스만 표시")

news_list = load_airline_news(selected_airline, days=30)

if news_list:
    for news in news_list:
        date_str = news.get("date", "")[:10]
        title = news.get("title", "제목 없음")
        url = news.get("source_url", "")
        source = news.get("source_name", "")

        st.markdown(f"""
        <div class="news-item">
            <div class="news-date">[{date_str}] {source}</div>
            <div class="news-title">{title}</div>
            {f'<a href="{url}" target="_blank" class="news-link">기사 원문 보기</a>' if url else ''}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info(f"최근 30일 내 {selected_airline} 관련 뉴스가 없습니다.")
    st.caption("뉴스 크롤링이 진행되면 여기에 표시됩니다.")

# 경고 문구
st.markdown("""
<div class="warning-box">
    <strong>주의:</strong> 이 예측은 사용자 제보 기반이며, 실제 면접과 다를 수 있습니다.
    모든 출현율은 제보된 데이터에서 계산되었습니다.
</div>
""", unsafe_allow_html=True)

# 제보 유도
st.markdown("")
st.markdown("---")
col_cta1, col_cta2 = st.columns([2, 1])
with col_cta1:
    st.markdown("##### 면접 다녀오셨나요?")
    st.caption("제보하시면 프리미엄 이용권을 드립니다. 더 많은 제보가 쌓일수록 예측 정확도가 올라갑니다!")
with col_cta2:
    if st.button("제보하러 가기", type="primary", use_container_width=True):
        st.switch_page("pages/40_면접제보.py")

# 푸터
end_page()

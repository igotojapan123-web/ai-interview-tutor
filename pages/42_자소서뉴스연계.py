# pages/42_자소서뉴스연계.py
# 자소서 + 뉴스 연계 시스템 - 자소서 내용과 실제 뉴스 매칭

# 정식 웹사이트 이전 안내
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from redirect_to_web import show_redirect_and_stop
show_redirect_and_stop()

import os
import sys
import json
import re
import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# 상위 디렉토리 import 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AIRLINES
from sidebar_common import init_page, end_page

# ============================================
# 키워드 추출 및 뉴스 매칭 로직
# ============================================

# 자소서에서 추출할 핵심 키워드 패턴
KEYWORD_PATTERNS = [
    # 서비스 관련
    "고객", "서비스", "만족", "응대", "친절", "배려", "소통", "경청",
    # 팀워크 관련
    "팀", "협력", "협업", "동료", "조화", "갈등", "해결", "리더",
    # 안전 관련
    "안전", "규정", "절차", "매뉴얼", "점검", "확인",
    # 성장 관련
    "성장", "도전", "목표", "열정", "노력", "배움",
    # 항공 관련
    "승무원", "비행", "객실", "기내", "항공", "여행",
    # 경험 관련
    "경험", "아르바이트", "인턴", "봉사", "활동",
    # 가치 관련
    "책임", "신뢰", "정직", "세심", "꼼꼼",
    # 트렌드 관련
    "디지털", "AI", "친환경", "ESG", "지속가능", "탄소", "MZ세대",
]


def extract_keywords(text: str) -> List[str]:
    """자소서에서 키워드 추출 (실제 텍스트 기반)"""
    found = []
    text_lower = text.lower()

    for keyword in KEYWORD_PATTERNS:
        if keyword in text_lower or keyword in text:
            found.append(keyword)

    # 중복 제거
    return list(set(found))


def load_airline_news(airline: str, days: int = 30) -> List[Dict]:
    """실제 크롤링된 뉴스만 로드"""
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

    return filtered


def count_keyword_matches(keywords: List[str], text: str) -> int:
    """키워드 매칭 수 계산"""
    text_lower = text.lower()
    count = 0
    for keyword in keywords:
        if keyword in text_lower:
            count += 1
    return count


def match_news_to_resume(resume_text: str, airline: str, news_list: List[Dict]) -> Optional[Dict]:
    """
    자소서와 뉴스 매칭

    - 키워드 최소 2개 이상 매칭되어야 함
    - 매칭 없으면 None 반환 (억지 매칭 금지)
    """
    keywords = extract_keywords(resume_text)

    if not keywords:
        return None

    matched = []
    for news in news_list:
        search_text = news.get("title", "") + " " + news.get("summary", "")
        match_count = count_keyword_matches(keywords, search_text)

        if match_count >= 2:  # 최소 2개 매칭
            matched.append({
                "news": news,
                "match_score": match_count,
                "matched_keywords": [k for k in keywords if k in search_text.lower()]
            })

    if not matched:
        return None

    # 가장 관련성 높은 뉴스 반환
    best_match = sorted(matched, key=lambda x: x["match_score"], reverse=True)[0]
    return best_match


def generate_improvement_suggestion(resume_excerpt: str, news: Dict, keywords: List[str]) -> Dict:
    """
    개선 제안 생성

    - AI가 내용을 창작하지 않음
    - 뉴스 정보를 자소서에 연결하는 방법만 제안
    """
    title = news.get("title", "")
    date = news.get("date", "")[:10]

    # 제안 생성 (템플릿 기반, AI 창작 아님)
    suggestion = {
        "original": resume_excerpt[:200] + "..." if len(resume_excerpt) > 200 else resume_excerpt,
        "improved": f"최근 {date} '{title}' 소식을 접하며 회사의 방향성에 공감했습니다. {resume_excerpt[:100]}...",
        "tip": f"면접에서 지원동기 질문 시 이 뉴스를 언급하면 '회사에 관심 있다'는 인상을 줄 수 있습니다.",
        "keywords_used": keywords
    }

    return suggestion


# ============================================
# 페이지 초기화
# ============================================
init_page(
    title="자소서 + 뉴스 연계",
    current_page="자소서뉴스연계",
    wide_layout=True
)

# ============================================
# CSS 스타일
# ============================================
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

.integration-header {
    background: linear-gradient(135deg, #059669 0%, #10b981 100%);
    padding: 2rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 2rem;
}

.integration-header h1 {
    margin: 0;
    font-size: 1.8rem;
    font-weight: 700;
}

.integration-header p {
    margin: 0.5rem 0 0 0;
    opacity: 0.9;
}

.result-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.news-match {
    background: #f0fdf4;
    border: 1px solid #22c55e;
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
}

.news-match h4 {
    color: #15803d;
    margin: 0 0 0.5rem 0;
}

.no-match {
    background: #fef3c7;
    border: 1px solid #f59e0b;
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
}

.no-match h4 {
    color: #92400e;
    margin: 0 0 0.5rem 0;
}

.keyword-tag {
    display: inline-block;
    background: #dbeafe;
    color: #1d4ed8;
    padding: 4px 10px;
    border-radius: 16px;
    font-size: 0.85rem;
    margin: 2px;
}

.improvement-box {
    background: #f8fafc;
    border-left: 4px solid #3b82f6;
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 0 8px 8px 0;
}

.original-text {
    background: #fee2e2;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
}

.improved-text {
    background: #dcfce7;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
}

.tip-box {
    background: #fef9c3;
    border: 1px solid #fbbf24;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
}

.warning-text {
    background: #fef3c7;
    border: 1px solid #f59e0b;
    border-radius: 8px;
    padding: 1rem;
    margin-top: 2rem;
    font-size: 0.9rem;
    color: #92400e;
}
</style>
""", unsafe_allow_html=True)

# ============================================
# 헤더
# ============================================
st.markdown("""
<div class="integration-header">
    <h1>자소서 + 뉴스 연계</h1>
    <p>자소서 내용과 최신 뉴스를 연결하여 차별화된 지원서를 만들어보세요</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# 입력 폼
# ============================================
st.markdown("### 자소서 분석")

col1, col2 = st.columns([3, 1])

with col2:
    selected_airline = st.selectbox(
        "지원 항공사",
        options=AIRLINES,
        key="integration_airline"
    )

with col1:
    resume_text = st.text_area(
        "자소서 내용 입력",
        placeholder="자소서 전체 또는 일부를 붙여넣기 해주세요.\n\n예시:\n저는 고객의 작은 불편함도 놓치지 않는 섬세한 서비스를 추구합니다. 대학 시절 카페 아르바이트를 하며 고객 응대 경험을 쌓았고, 이를 통해 진정한 서비스는 고객의 말에 귀 기울이는 것에서 시작된다는 것을 배웠습니다.",
        height=200,
        key="resume_input"
    )

# 분석 버튼
if st.button("뉴스 연계 분석", type="primary", use_container_width=True):
    if not resume_text.strip():
        st.error("자소서 내용을 입력해주세요.")
    elif len(resume_text.strip()) < 50:
        st.warning("더 많은 내용을 입력하면 정확한 분석이 가능합니다. (최소 50자 권장)")
    else:
        with st.spinner("분석 중..."):
            # 키워드 추출
            keywords = extract_keywords(resume_text)

            # 뉴스 로드
            news_list = load_airline_news(selected_airline, days=30)

            # 매칭 시도
            match_result = match_news_to_resume(resume_text, selected_airline, news_list)

        st.markdown("---")
        st.markdown("### 분석 결과")

        # 추출된 키워드 표시
        st.markdown("#### 추출된 키워드")
        if keywords:
            keyword_html = " ".join([f'<span class="keyword-tag">{k}</span>' for k in keywords])
            st.markdown(f'<div style="margin: 0.5rem 0;">{keyword_html}</div>', unsafe_allow_html=True)
        else:
            st.caption("추출된 키워드가 없습니다.")

        st.markdown("")

        # 매칭 결과
        if match_result:
            news = match_result["news"]
            matched_keywords = match_result["matched_keywords"]

            st.markdown("""
            <div class="news-match">
                <h4>관련 뉴스 발견!</h4>
            </div>
            """, unsafe_allow_html=True)

            # 뉴스 정보
            st.markdown("##### 연결 추천 뉴스")
            st.markdown(f"""
            <div class="result-card">
                <p style="font-size: 0.85rem; color: #64748b;">
                    [{news.get('date', '')[:10]}] {news.get('source_name', '')}
                </p>
                <h4 style="margin: 0.5rem 0; color: #1e293b;">
                    {news.get('title', '제목 없음')}
                </h4>
                <p style="color: #475569; margin: 0.5rem 0;">
                    {news.get('summary', '')[:200]}...
                </p>
                {f'<a href="{news.get("source_url", "")}" target="_blank" style="color: #3b82f6;">기사 원문 보기</a>' if news.get('source_url') else ''}
            </div>
            """, unsafe_allow_html=True)

            # 매칭된 키워드
            st.caption(f"매칭 키워드: {', '.join(matched_keywords)}")

            # 개선 제안
            st.markdown("##### 수정 제안")
            suggestion = generate_improvement_suggestion(resume_text, news, matched_keywords)

            st.markdown(f"""
            <div class="improvement-box">
                <p style="font-weight: 600; margin-bottom: 0.5rem;">[기존]</p>
                <div class="original-text">
                    {suggestion['original']}
                </div>

                <p style="font-weight: 600; margin: 1rem 0 0.5rem 0;">[개선]</p>
                <div class="improved-text">
                    {suggestion['improved']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 면접 활용 팁
            st.markdown(f"""
            <div class="tip-box">
                <strong>면접 활용 팁:</strong> {suggestion['tip']}
            </div>
            """, unsafe_allow_html=True)

        else:
            # 매칭 실패
            st.markdown("""
            <div class="no-match">
                <h4>관련 뉴스 없음</h4>
                <p>최근 30일 내 자소서 내용과 연결할 수 있는 뉴스가 없습니다.</p>
            </div>
            """, unsafe_allow_html=True)

            # 대안 제안
            st.markdown("##### 대안 제안")
            st.info(f"""
            - {selected_airline}의 최근 주요 뉴스를 직접 찾아 자소서에 반영해보세요.
            - 면접 예측 페이지에서 최근 제보된 질문 트렌드를 확인해보세요.
            """)

            # 뉴스 현황
            if news_list:
                st.markdown(f"##### 최근 {selected_airline} 뉴스 ({len(news_list)}건)")
                for n in news_list[:3]:
                    st.markdown(f"- [{n.get('date', '')[:10]}] {n.get('title', '')}")
            else:
                st.caption(f"현재 {selected_airline} 관련 크롤링된 뉴스가 없습니다.")

        # 경고 문구
        st.markdown("""
        <div class="warning-text">
            <strong>주의:</strong> 뉴스 내용을 직접 확인 후 사용하세요.
            모든 뉴스는 실제 크롤링된 데이터이며, AI가 생성한 것이 아닙니다.
        </div>
        """, unsafe_allow_html=True)

# ============================================
# 사용 팁
# ============================================
with st.expander("사용 팁", expanded=False):
    st.markdown("""
    #### 효과적인 뉴스 연계 방법

    1. **지원동기에 활용**: "최근 ~~ 뉴스를 보고 회사의 방향성에 공감했습니다"
    2. **입사 후 포부에 활용**: "회사가 추진 중인 ~~ 사업에 기여하고 싶습니다"
    3. **면접 답변에 활용**: 지원동기 질문 시 뉴스를 언급하면 관심도를 보여줄 수 있습니다

    #### 주의사항

    - 뉴스 내용을 반드시 직접 확인하세요
    - 기사 원문을 읽고 정확한 내용을 파악하세요
    - 억지로 연결하면 오히려 마이너스가 될 수 있습니다
    """)

# 다른 페이지 링크
st.markdown("---")
col_link1, col_link2 = st.columns(2)

with col_link1:
    if st.button("면접 예측 보기", use_container_width=True):
        st.switch_page("pages/41_면접예측.py")

with col_link2:
    if st.button("면접 제보하기", use_container_width=True):
        st.switch_page("pages/40_면접제보.py")

# 푸터
end_page()

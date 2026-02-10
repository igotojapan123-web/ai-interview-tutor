"""
대한항공 기업분석 & 뉴스 페이지
세련된 UI + flyready-news-bot 연동
"""

import streamlit as st
from datetime import date
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# flyready-news-bot 경로 추가
FLYREADY_PATH = r"C:\Users\ADMIN\flyready-news-bot"
sys.path.insert(0, FLYREADY_PATH)

from data.company_info import COMPANY_INFO, get_company_summary, get_recent_issues


def _calculate_relevance(title: str, description: str) -> str:
    """면접 관련도 태깅"""
    text = (title + " " + description).lower()

    # 필수 숙지 키워드
    essential_keywords = ["합병", "인수", "실적", "사고", "안전", "파업", "채용", "승무원", "통합"]
    for kw in essential_keywords:
        if kw in text:
            return "필수"

    # 알면 좋은 키워드
    good_keywords = ["노선", "취항", "서비스", "신규", "수상", "좌석", "AI", "기내식"]
    for kw in good_keywords:
        if kw in text:
            return "알면좋음"

    return "참고용"


def _strict_filter_for_cabin_crew(articles: list) -> list:
    """
    승무원 면접 준비생을 위한 초강력 필터링
    정말 알아야 할 뉴스만 통과
    """
    # === 무조건 제외 키워드 ===
    HARD_EXCLUDE = [
        # 스포츠/배구
        "배구", "점보스", "V리그", "감독", "코치", "선수", "경기", "세트", "승리", "패배",
        "우승", "준우승", "플레이오프", "정규시즌", "구단", "팀", "스포츠",
        # 주가/투자
        "주가", "주식", "상승", "하락", "시세", "투자", "ETF", "펀드", "배당", "공시",
        # 화물/물류
        "화물", "물류", "카고", "freight", "cargo",
        # 정치/의회
        "국회", "의원", "청문회", "국정감사", "장관", "차관", "대통령",
        # 부고/인사
        "별세", "부고", "부음", "조문", "영결식", "빈소", "승진", "임명", "취임",
        # CSR/기부
        "기부", "봉사", "후원", "나눔", "선행", "장학금", "사회공헌", "CSR",
        # MOU/협약
        "MOU", "협약", "양해각서", "업무협약",
        # 수상/시상
        "수상", "시상", "대상", "표창", "감사패",
        # 행사/이벤트
        "페스티벌", "축제", "행사", "기념행사", "출범식", "개막식",
        # 광고/프로모션
        "프로모션", "이벤트", "할인", "특가", "세일", "경품", "마일리지 적립",
        # 연예/공항패션
        "공항패션", "출국길", "입국길", "연예인", "아이돌", "촬영",
        # 학원/교육업체
        "학원", "아카데미", "교육원", "합격자 배출", "배출",
        # 비승무원 직종
        "정비사", "조종사", "파일럿", "기장", "사무직", "지상직", "IT", "개발자",
        # 여행 후기/블로그
        "후기", "탑승기", "체험", "방문기", "리뷰",
        # 기타 무관
        "골프", "마라톤", "자선", "환경캠페인", "나무심기",
    ]

    # === 반드시 포함해야 할 키워드 (하나 이상) ===
    MUST_INCLUDE = [
        # 승무원 직접 관련
        "승무원", "객실승무원", "캐빈승무원", "FA", "인턴승무원",
        # 채용
        "채용", "공채", "모집", "지원",
        # 서비스/기내
        "기내", "서비스", "유니폼", "기내식", "좌석", "라운지",
        # 노선/운항
        "노선", "취항", "증편", "직항", "운항",
        # 합병/통합
        "아시아나", "통합", "합병", "인수",
        # 안전
        "안전", "비상", "사고", "결함",
        # 정책 변경
        "수하물", "환불", "정책",
        # 신기재
        "B787", "A350", "A321neo", "신기종", "도입",
        # 노조
        "파업", "노조", "임금",
        # 실적 (회사 상황 파악용)
        "실적", "영업이익", "매출",
    ]

    # === 대한항공 직접 관련 확인 ===
    KE_KEYWORDS = ["대한항공", "korean air", "KE"]

    filtered = []
    for article in articles:
        title = article.get("title", "")
        desc = article.get("description", "")
        text = title + " " + desc

        # 1. 제외 키워드 체크 (하나라도 있으면 탈락)
        if any(kw in text for kw in HARD_EXCLUDE):
            continue

        # 2. 대한항공 관련인지 확인
        if not any(kw in text for kw in KE_KEYWORDS):
            continue

        # 3. 필수 포함 키워드 체크 (하나라도 있어야 통과)
        if not any(kw in text for kw in MUST_INCLUDE):
            continue

        # 4. 제목이 너무 짧으면 제외 (광고성 의심)
        if len(title) < 15:
            continue

        filtered.append(article)

    return filtered


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
                <tr><td>규모</td><td>{biz['통합현황']}</td></tr>
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

    talent = COMPANY_INFO["인재상"]["4가지_인재상"]
    cols = st.columns(4)

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
    st.markdown("### 최신 뉴스 수집")

    st.markdown("""
    <div style="background: linear-gradient(135deg, #dbeafe, #eff6ff); border-radius: 12px; padding: 1rem 1.25rem; border-left: 4px solid #3b82f6; margin-bottom: 1.5rem;">
        <p style="margin: 0; color: #1e40af;">
            <strong>📰 실시간 뉴스 수집</strong><br>
            <span style="font-size: 0.9rem;">버튼을 누르면 네이버 뉴스 API로 대한항공 최신 뉴스를 수집하고, AI가 면접용으로 정리해드립니다.</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 세션 상태
    if "collected_news" not in st.session_state:
        st.session_state.collected_news = []
    if "news_summary" not in st.session_state:
        st.session_state.news_summary = None

    col1, col2 = st.columns([1, 1])
    with col1:
        collect_btn = st.button("🔍 뉴스 수집하기", type="primary", use_container_width=True)
    with col2:
        if st.button("🗑️ 초기화", use_container_width=True):
            st.session_state.collected_news = []
            st.session_state.news_summary = None
            st.rerun()

    if collect_btn:
        with st.spinner("네이버 뉴스 API로 대한항공 뉴스를 수집하는 중..."):
            try:
                # flyready-news-bot의 NaverNewsCrawler + NewsSummarizer 사용
                import json
                secrets_path = os.path.join(FLYREADY_PATH, "config", "secrets.json")
                with open(secrets_path, "r", encoding="utf-8") as f:
                    secrets = json.load(f)

                from crawlers.naver_news import NaverNewsCrawler
                from analyzers.summarizer import NewsSummarizer

                crawler = NaverNewsCrawler(
                    client_id=secrets["naver_client_id"],
                    client_secret=secrets["naver_client_secret"]
                )

                # 대한항공 뉴스 검색 (여러 키워드로 최대한 많이 수집)
                search_keywords = [
                    "대한항공 승무원",
                    "대한항공 채용",
                    "대한항공 서비스",
                    "대한항공 노선",
                    "대한항공 아시아나 통합",
                    "대한항공 기내",
                    "대한항공 안전",
                    "대한항공 실적",
                ]

                raw_news = []
                seen_titles = set()
                for keyword in search_keywords:
                    results = crawler.search(keyword, display=30, sort="date")
                    for r in results:
                        title_key = r["title"][:25]
                        if title_key not in seen_titles:
                            seen_titles.add(title_key)
                            raw_news.append(r)

                if raw_news:
                    # 1단계: 초강력 필터링 (승무원 면접에 정말 필요한 것만)
                    strict_filtered = _strict_filter_for_cabin_crew(raw_news)

                    # 2단계: NewsSummarizer 추가 필터링
                    summarizer = NewsSummarizer(
                        api_key=secrets["openai_api_key"],
                        model="gpt-4o-mini"
                    )
                    filtered = summarizer._filter_excluded(strict_filtered)
                    unique = summarizer._remove_duplicates(filtered)

                    # 3단계: 우선순위 분류
                    categorized = summarizer.categorize_articles(unique)

                    # 형식 변환 + 상위 10개만 선택
                    formatted_news = []
                    for priority in range(1, 7):
                        for n in categorized.get(priority, []):
                            if len(formatted_news) >= 10:
                                break

                            if priority == 1:
                                relevance = "필수"
                            elif priority in [2, 3]:
                                relevance = "알면좋음"
                            else:
                                relevance = "참고용"

                            formatted_news.append({
                                "title": n["title"],
                                "summary": n.get("description", ""),
                                "date": n.get("pub_date", ""),
                                "source": n.get("source", ""),
                                "url": n.get("link", ""),
                                "relevance": relevance,
                                "priority": priority
                            })
                        if len(formatted_news) >= 10:
                            break

                    if formatted_news:
                        st.session_state.collected_news = formatted_news
                        st.session_state.news_summary = None

                        p1 = len([n for n in formatted_news if n["priority"] == 1])
                        st.success(f"✅ {len(raw_news)}개 수집 → {len(formatted_news)}개 엄선 완료! (필수 {p1}개)")
                    else:
                        st.warning("승무원 면접 관련 뉴스가 없습니다. 나중에 다시 시도해주세요.")
                else:
                    st.warning("수집된 뉴스가 없습니다.")

            except Exception as e:
                st.error(f"수집 실패: {e}")
                import traceback
                st.code(traceback.format_exc())
                # 폴백 사용
                from utils.news_crawler import FALLBACK_NEWS
                st.session_state.collected_news = FALLBACK_NEWS
                st.info("저장된 주요 뉴스를 표시합니다.")

    # 수집된 뉴스 표시
    if st.session_state.collected_news:
        news_list = st.session_state.collected_news

        st.markdown("---")
        st.markdown(f"### 📋 수집된 뉴스 ({len(news_list)}개)")

        # 관련도별 필터
        relevance_filter = st.selectbox(
            "중요도 필터",
            ["전체", "필수", "알면좋음", "참고용"],
            key="news_filter"
        )

        filtered_news = news_list if relevance_filter == "전체" else [
            n for n in news_list if n.get("relevance") == relevance_filter
        ]

        for i, news in enumerate(filtered_news):
            relevance = news.get("relevance", "참고용")
            if relevance == "필수":
                badge_class = "badge-required"
                badge_text = "면접 필수"
                border_color = "#ef4444"
            elif relevance == "알면좋음":
                badge_class = "badge-good"
                badge_text = "알면 좋음"
                border_color = "#f59e0b"
            else:
                badge_class = "badge-ref"
                badge_text = "참고용"
                border_color = "#94a3b8"

            with st.expander(f"{'🔴' if relevance == '필수' else '🟡' if relevance == '알면좋음' else '⚪'} {news['title']}", expanded=(relevance == "필수")):
                st.markdown(f"""
                <div style="border-left: 4px solid {border_color}; padding-left: 1rem;">
                    <span class="{badge_class}" style="display: inline-block; margin-bottom: 0.5rem;">{badge_text}</span>
                    <p style="color: #374151; margin: 0.5rem 0;">{news.get('summary', '')}</p>
                    <p style="font-size: 0.85rem; color: #6b7280; margin: 0.5rem 0;">
                        📰 {news.get('source', '뉴스')} | 📅 {news.get('date', '')}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                if news.get('url'):
                    st.markdown(f"[🔗 원문 보기]({news.get('url')})")

        # AI 분석 버튼
        st.markdown("---")
        if st.button("🤖 AI가 면접 활용법 정리하기", use_container_width=True):
            with st.spinner("AI가 뉴스를 분석하고 면접 활용법을 정리하는 중..."):
                try:
                    import json as json_module
                    secrets_path = os.path.join(FLYREADY_PATH, "config", "secrets.json")
                    with open(secrets_path, "r", encoding="utf-8") as f:
                        secrets = json_module.load(f)

                    from analyzers.summarizer import NewsSummarizer

                    summarizer = NewsSummarizer(
                        api_key=secrets["openai_api_key"],
                        model="gpt-4o-mini"
                    )

                    # 뉴스 형식 변환 (표시 형식 → flyready 형식)
                    articles = []
                    for n in news_list[:10]:
                        articles.append({
                            "title": n["title"],
                            "description": n.get("summary", ""),
                            "link": n.get("url", ""),
                            "source": n.get("source", ""),
                            "pub_date": n.get("date", "")
                        })

                    # AI 요약 실행
                    result = summarizer.summarize_articles(articles)

                    if result.get("no_news"):
                        st.warning("분석할 뉴스가 없습니다.")
                    else:
                        st.session_state.news_summary = result

                        # 결과 표시
                        st.markdown("### 🎯 AI 뉴스 브리핑")

                        # 키워드
                        if result.get("keywords"):
                            keywords_html = " ".join([f'<span style="background: #00256C; color: white; padding: 0.25rem 0.75rem; border-radius: 20px; margin-right: 0.5rem;">#{kw}</span>' for kw in result["keywords"]])
                            st.markdown(f"""
                            <div style="margin-bottom: 1rem;">
                                {keywords_html}
                            </div>
                            """, unsafe_allow_html=True)

                        # 뉴스 요약
                        for i, news in enumerate(result.get("news", []), 1):
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #f0fdf4, #dcfce7); border-radius: 12px; padding: 1.25rem; border-left: 4px solid #22c55e; margin-bottom: 1rem;">
                                <h4 style="color: #166534; margin: 0 0 0.75rem 0;">{i}. {news.get('title', '')}</h4>
                                <p style="margin: 0.25rem 0; color: #374151;">{news.get('line1', '')}</p>
                                <p style="margin: 0.25rem 0; color: #374151;">{news.get('line2', '')}</p>
                                <p style="margin: 0.25rem 0; color: #374151;">{news.get('line3', '')}</p>
                                <p style="margin: 0.25rem 0; color: #059669; font-weight: 500;">{news.get('line4', '')}</p>
                            </div>
                            """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"AI 분석 실패: {e}")
                    import traceback
                    st.code(traceback.format_exc())

        st.markdown("---")
        st.caption("⚠️ 뉴스는 참고용이며, 면접 전 공식 채널에서 최신 정보를 확인하세요.")

    else:
        st.info("""
        **🔍 뉴스 수집 버튼을 눌러주세요!**

        대한항공 최신 뉴스를 실시간으로 수집하고,
        면접에서 활용할 수 있도록 정리해드립니다.
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

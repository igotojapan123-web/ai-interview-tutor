# pages/24_에어로케이.py
# 에어로케이 전용 채용 가이드 - 경험 포트폴리오 컨설팅

# 정식 웹사이트 이전 안내
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from redirect_to_web import show_redirect_and_stop
show_redirect_and_stop()

import os
import sys
import json
import streamlit as st
from datetime import datetime

# 상위 디렉토리 import 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sidebar_common import init_page, end_page

# OpenAI 클라이언트
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# 에어로케이 데이터
try:
    from airline_database import AIRLINE_FULL_DATA
    AEROK_DATA = AIRLINE_FULL_DATA.get("에어로케이", {})
except ImportError:
    AEROK_DATA = {}

# ============================================
# 페이지 초기화
# ============================================
init_page(
    title="에어로케이 채용 가이드",
    page_title="FlyReady Lab - 에어로케이",
    current_page="에어로케이"
)

# ============================================
# CSS 스타일
# ============================================
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

* {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.aerok-hero {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
    padding: 2rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 2rem;
}

.aerok-hero h2 {
    margin: 0 0 0.5rem 0;
    font-size: 1.5rem;
}

.aerok-hero p {
    margin: 0;
    opacity: 0.9;
}

.highlight-box {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
    padding: 1rem 1.5rem;
    border-radius: 12px;
    color: white;
    font-weight: 600;
    margin: 1rem 0;
}

.info-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
}

.good-example {
    background: #ecfdf5;
    border-left: 4px solid #10b981;
    padding: 1rem;
    border-radius: 0 8px 8px 0;
    margin: 0.5rem 0;
}

.bad-example {
    background: #fef2f2;
    border-left: 4px solid #ef4444;
    padding: 1rem;
    border-radius: 0 8px 8px 0;
    margin: 0.5rem 0;
}

.quote-box {
    background: #f1f5f9;
    border-left: 4px solid #2563eb;
    padding: 1rem 1.5rem;
    margin: 1rem 0;
    font-style: italic;
    border-radius: 0 8px 8px 0;
}

.step-badge {
    display: inline-block;
    background: #2563eb;
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 600;
    margin-right: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# ============================================
# Session State 초기화
# ============================================
defaults = {
    "aerok_experiences": [],
    "aerok_chat_history": [],
    "aerok_analysis_result": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ============================================
# OpenAI 클라이언트
# ============================================
def get_openai_client():
    if not OPENAI_AVAILABLE:
        return None
    try:
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except:
        return None

# ============================================
# 시스템 프롬프트
# ============================================
PORTFOLIO_SYSTEM_PROMPT = """당신은 에어로케이 객실승무원 채용 전문 컨설턴트입니다.

## 에어로케이 2026년 채용 특징
- **자기소개서 전면 폐지** (국내 항공사 최초)
- 서류전형: 경험 포트폴리오 (사진 3장 내외) 제출
- AI 대필 방지, 경험의 진정성 평가
- 승무원 = 기내 안전요원 (서비스직 + 안전 역할)

## 경험 포트폴리오란?
- 자소서 대신 제출하는 '사진 3장 내외'
- 본인이 직접 참여한 경험이 담긴 사진
- 면접에서 사진 기반 심층 질문 진행

## 좋은 포트폴리오 예시
- 아르바이트 현장 (카페에서 앞치마 입고 일하는 모습)
- 밤샘 프로젝트 흔적이 남은 책상
- 봉사활동 현장에서 활동하는 모습
- 팀원들과 회의/발표하는 모습
- 마라톤 완주, 운동 중인 모습
- 응급처치, 문제 해결 상황

## 피해야 할 포트폴리오
- 바디프로필 (과도한 신체 강조)
- 승무원 연상 정형화된 복장
- 스튜디오 완벽 프로필 사진
- AI 생성 이미지 (적발 시 합격 취소)
- 타인 사진 도용

## 평가 포인트
사진을 통해 다음을 설명할 수 있어야 함:
1. 당시 어떤 상황이었는가? (Situation)
2. 어떤 판단을 내렸는가? (Thinking)
3. 어떻게 행동했는가? (Action)
4. 어떤 결과/배움이 있었는가? (Result)
5. 승무원 직무와 어떻게 연결되는가? (Connection)

## 에어로케이 인재상
- 안전이라는 타협할 수 없는 가치 존중
- 개인의 개성과 자유 존중
- 수평적 문화에서 창의적 아이디어
- 기내 안전요원으로서의 강인함

## 당신의 역할
1. 사용자의 경험을 듣고 포트폴리오 적합도 분석
2. 사진 촬영 가이드 제공
3. 면접 예상 질문 생성
4. 승무원 직무 연결 포인트 제시

## 절대 원칙
- 경험 창작/추측 금지
- 사실 기반 조언만 제공
- 구체적이고 실행 가능한 가이드 제공
"""

# ============================================
# 경험 분석 함수
# ============================================
def analyze_experience(experience_text: str, experience_type: str) -> dict:
    """경험을 분석하여 포트폴리오 적합도 및 가이드 제공"""
    client = get_openai_client()
    if not client:
        return {"error": "AI 서비스 연결 실패"}

    prompt = f"""다음 경험을 에어로케이 경험 포트폴리오 관점에서 분석해주세요.

## 경험 유형: {experience_type}
## 경험 내용:
{experience_text}

## 분석 요청사항
다음 JSON 형식으로 응답해주세요:
{{
    "적합도": "상/중/하",
    "적합도_이유": "적합도 판단 이유",
    "STAR_분석": {{
        "상황": "추출된 상황 (없으면 '추가 정보 필요')",
        "과제": "추출된 과제/역할",
        "행동": "추출된 구체적 행동",
        "결과": "추출된 결과/배움"
    }},
    "승무원_연결": "이 경험이 승무원/안전요원 직무와 연결되는 포인트",
    "사진_촬영_가이드": ["사진 촬영 시 포인트 1", "포인트 2", "포인트 3"],
    "면접_예상질문": ["예상 질문 1", "예상 질문 2", "예상 질문 3", "예상 질문 4", "예상 질문 5"],
    "개선_제안": "포트폴리오로 활용 시 보완할 점",
    "주의사항": "이 경험 활용 시 주의할 점"
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": PORTFOLIO_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        return {"error": str(e)}


def generate_interview_questions(experiences: list) -> list:
    """경험 기반 면접 예상 질문 생성"""
    client = get_openai_client()
    if not client:
        return []

    exp_text = "\n".join([f"- {e['type']}: {e['content']}" for e in experiences])

    prompt = f"""다음 경험들을 바탕으로 에어로케이 임원면접에서 받을 수 있는 심층 질문을 생성해주세요.

## 지원자 경험:
{exp_text}

## 에어로케이 면접 특징:
- 경험 포트폴리오(사진) 기반 심층 질문
- 상황 판단력, 행동의 이유, 승무원 직무 연결 확인
- 안전요원으로서의 강인함 평가

다음 JSON 형식으로 10개의 질문을 생성해주세요:
{{
    "questions": [
        {{"질문": "질문 내용", "의도": "면접관이 확인하려는 것", "답변_포인트": "답변 시 강조할 점"}},
        ...
    ]
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": PORTFOLIO_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return result.get("questions", [])
    except:
        return []


# ============================================
# 메인 UI
# ============================================

# 히어로 섹션
st.markdown("""
<div class="aerok-hero">
    <h2>✈️ 에어로케이 채용 가이드</h2>
    <p>2026년 국내 항공사 최초 자소서 폐지! 경험 포트폴리오로 승부하세요.</p>
</div>
""", unsafe_allow_html=True)

# 핵심 변화 알림
st.markdown("""
<div class="highlight-box">
    🚨 2026년 핵심 변화: 자기소개서 전면 폐지 → 경험 포트폴리오(사진 3장) 제출
</div>
""", unsafe_allow_html=True)

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 채용 가이드",
    "📸 포트폴리오 컨설팅",
    "🗣️ 토론면접 준비",
    "💬 AI 상담"
])

# ============================================
# TAB 1: 채용 가이드
# ============================================
with tab1:
    st.subheader("에어로케이 2026 채용 전형")

    # 전형 절차
    st.markdown("#### 📌 전형 절차")
    cols = st.columns(5)
    steps = [
        ("1", "서류전형", "경험 포트폴리오"),
        ("2", "토론면접", "팀 토론 + 롤플레이"),
        ("3", "임원면접", "포트폴리오 기반 심층"),
        ("4", "건강검진", "채용 건강검진"),
        ("5", "최종합격", "")
    ]
    for col, (num, title, desc) in zip(cols, steps):
        with col:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: #f1f5f9; border-radius: 12px;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #2563eb;">{num}</div>
                <div style="font-weight: 600; margin: 0.5rem 0;">{title}</div>
                <div style="font-size: 0.8rem; color: #64748b;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 지원 자격
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📋 지원 자격")
        st.markdown("""
        | 항목 | 내용 |
        |------|------|
        | 학력 | 제한 없음 |
        | 나이 | 제한 없음 |
        | 외모규정 | 없음 |
        | 사진 | 서류전형 내 제출 금지 |
        | 시력 | 교정시력 1.0 이상 |
        """)

    with col2:
        st.markdown("#### 🌐 어학 요건 (택1)")
        st.markdown("""
        - TOEIC Speaking **IM2** 이상
        - OPIc **IM1** 이상 (영어/중국어/일본어)
        - 영어권/중화권/일본 **3년 이상** 거주자
        """)

        st.markdown("#### ⭐ 우대사항")
        st.markdown("""
        - 안전분야 관련 자격 보유자
        - 안전분야 관련 종사자
        - 일본어/중국어 등 외국어 능통자
        """)

    st.markdown("---")

    # 경험 포트폴리오 설명
    st.markdown("#### 📸 경험 포트폴리오란?")

    st.markdown("""
    <div class="info-card">
        <strong>정의</strong>: 자소서 대신 제출하는 <strong>'사진 3장 내외'</strong>로 구성된 경험 증빙 자료<br><br>
        <strong>핵심 개념</strong>: AI가 흉내 낼 수 없는 <strong>'경험의 진정성'</strong>에 주목<br><br>
        <strong>활용</strong>: 면접 과정에서 심층 질문의 핵심 자료로 활용
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### ✅ 좋은 포트폴리오 예시")
        good_examples = [
            "카페에서 앞치마 입고 일하는 모습",
            "밤샘 프로젝트 흔적이 남은 책상",
            "봉사활동 현장에서 활동하는 모습",
            "팀원들과 회의/발표하는 모습",
            "마라톤 완주, 운동 중인 모습",
            "응급처치, 문제 해결 상황"
        ]
        for ex in good_examples:
            st.markdown(f'<div class="good-example">✓ {ex}</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("##### ❌ 피해야 할 포트폴리오")
        bad_examples = [
            "바디프로필 (과도한 신체 강조)",
            "승무원 연상 정형화된 복장",
            "스튜디오 완벽 프로필 사진",
            "AI 생성 이미지 (적발 시 합격 취소)",
            "타인 사진 도용 (적발 시 합격 취소)"
        ]
        for ex in bad_examples:
            st.markdown(f'<div class="bad-example">✗ {ex}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # 공식 메시지
    st.markdown("#### 💬 에어로케이 공식 메시지")

    quotes = AEROK_DATA.get("official_quotes", [])
    for quote in quotes:
        st.markdown(f'<div class="quote-box">{quote}</div>', unsafe_allow_html=True)


# ============================================
# TAB 2: 포트폴리오 컨설팅
# ============================================
with tab2:
    st.subheader("📸 경험 포트폴리오 컨설팅")
    st.info("본인의 경험을 입력하면, 에어로케이 포트폴리오 적합도를 분석하고 사진 촬영 가이드와 면접 예상 질문을 제공합니다.")

    # 경험 입력
    st.markdown("#### 경험 입력")

    experience_type = st.selectbox(
        "경험 유형",
        ["아르바이트", "봉사활동", "팀 프로젝트", "동아리 활동", "체력/운동", "위기 대처 경험", "해외 경험", "기타"]
    )

    experience_content = st.text_area(
        "경험 내용을 상세히 작성해주세요",
        placeholder="예: 대학교 2학년 때 카페에서 1년간 아르바이트를 했습니다. 처음에는 음료 제조만 했지만, 3개월 후부터는 오픈/마감 담당으로 맡게 되었습니다. 특히 기억에 남는 건 한 어르신 손님이 메뉴를 오래 고민하고 계셔서 제가 먼저 다가가 추천해드렸더니, 그 후로 단골이 되셨던 일입니다...",
        height=150
    )

    if st.button("🔍 포트폴리오 적합도 분석", type="primary"):
        if experience_content.strip():
            with st.spinner("경험을 분석하고 있습니다..."):
                result = analyze_experience(experience_content, experience_type)

                if "error" in result:
                    st.error(f"분석 실패: {result['error']}")
                else:
                    st.session_state.aerok_analysis_result = result

                    # 경험 저장
                    st.session_state.aerok_experiences.append({
                        "type": experience_type,
                        "content": experience_content,
                        "result": result
                    })
        else:
            st.warning("경험 내용을 입력해주세요.")

    # 분석 결과 표시
    if st.session_state.aerok_analysis_result:
        result = st.session_state.aerok_analysis_result

        st.markdown("---")
        st.markdown("### 📊 분석 결과")

        # 적합도
        적합도 = result.get("적합도", "중")
        적합도_color = {"상": "#10b981", "중": "#f59e0b", "하": "#ef4444"}.get(적합도, "#64748b")

        st.markdown(f"""
        <div style="background: {적합도_color}; color: white; padding: 1rem 2rem; border-radius: 12px; display: inline-block; font-weight: 700; font-size: 1.2rem;">
            포트폴리오 적합도: {적합도}
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"**판단 이유**: {result.get('적합도_이유', '')}")

        # STAR 분석
        st.markdown("#### 📋 STAR 분석")
        star = result.get("STAR_분석", {})
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**S (상황)**: {star.get('상황', '-')}")
            st.markdown(f"**T (과제)**: {star.get('과제', '-')}")
        with col2:
            st.markdown(f"**A (행동)**: {star.get('행동', '-')}")
            st.markdown(f"**R (결과)**: {star.get('결과', '-')}")

        # 승무원 연결
        st.markdown("#### ✈️ 승무원 직무 연결")
        st.info(result.get("승무원_연결", ""))

        # 사진 촬영 가이드
        st.markdown("#### 📸 사진 촬영 가이드")
        for guide in result.get("사진_촬영_가이드", []):
            st.markdown(f"- {guide}")

        # 면접 예상 질문
        st.markdown("#### 🎤 면접 예상 질문")
        for i, q in enumerate(result.get("면접_예상질문", []), 1):
            st.markdown(f"{i}. {q}")

        # 개선 제안
        if result.get("개선_제안"):
            st.markdown("#### 💡 개선 제안")
            st.warning(result.get("개선_제안"))

        # 주의사항
        if result.get("주의사항"):
            st.markdown("#### ⚠️ 주의사항")
            st.error(result.get("주의사항"))

    # 저장된 경험 목록
    if st.session_state.aerok_experiences:
        st.markdown("---")
        st.markdown("### 📁 저장된 경험 목록")

        for i, exp in enumerate(st.session_state.aerok_experiences):
            with st.expander(f"{i+1}. [{exp['type']}] {exp['content'][:50]}..."):
                st.write(exp['content'])
                if exp.get('result'):
                    st.json(exp['result'])

        if st.button("🎯 종합 면접 질문 생성"):
            with st.spinner("면접 질문을 생성하고 있습니다..."):
                questions = generate_interview_questions(st.session_state.aerok_experiences)
                if questions:
                    st.markdown("### 🎤 종합 면접 예상 질문")
                    for i, q in enumerate(questions, 1):
                        st.markdown(f"""
                        **{i}. {q.get('질문', '')}**
                        - 면접관 의도: {q.get('의도', '')}
                        - 답변 포인트: {q.get('답변_포인트', '')}
                        """)


# ============================================
# TAB 3: 토론면접 준비
# ============================================
with tab3:
    st.subheader("🗣️ 토론면접 준비")
    st.info("에어로케이 1차 면접은 팀 단위 토론면접입니다. 유연한 사고와 상황 대처 능력을 평가합니다.")

    st.markdown("#### 토론면접 특징")
    st.markdown("""
    - **형식**: 팀 단위 토론 진행
    - **평가 요소**: 유연한 사고 역량, 롤플레잉 상황 대처 능력
    - **핵심**: 논리적 의견 전개 + 경청 + 협력
    """)

    st.markdown("---")

    # 토론 주제 예시 (토론면접 페이지와 연동 가능한 형식)
    st.markdown("#### 📌 예상 토론 주제")
    st.caption("각 주제를 클릭하면 AI 토론 연습을 바로 시작할 수 있습니다.")

    # 에어로케이 맞춤 토론 주제 (토론면접 페이지 형식)
    aerok_debate_topics = [
        {
            "topic": "기내에서 승객이 마스크 착용을 거부할 경우 어떻게 대응해야 하는가?",
            "category": "safety",
            "background": "에어로케이는 '안전이라는 타협할 수 없는 가치'를 강조합니다. 기내 안전 규정과 고객 서비스 사이에서 승무원은 어떤 판단을 내려야 할까요?",
            "pro_points": [
                "안전 규정은 모든 승객의 건강을 위한 것",
                "규정 위반 시 다른 승객에게 피해 발생",
                "승무원은 기내 안전요원으로서 규정 집행 의무"
            ],
            "con_points": [
                "개인의 선택권 존중 필요",
                "강제 시 더 큰 갈등 유발 가능",
                "상황에 따른 유연한 대응 필요"
            ],
            "유형": "안전 vs 고객 서비스",
            "포인트": "안전 규정 준수와 고객 응대의 균형"
        },
        {
            "topic": "SNS에 항공사 비판 글이 올라왔을 때 승무원이 개인적으로 반박해도 되는가?",
            "category": "ethics",
            "background": "수평적 문화를 강조하는 에어로케이에서, 개인의 표현의 자유와 조직의 대표성 사이의 균형은 어떻게 맞춰야 할까요?",
            "pro_points": [
                "잘못된 정보 바로잡을 의무",
                "개인 표현의 자유 존중",
                "진정성 있는 소통 가능"
            ],
            "con_points": [
                "조직 공식 입장과 충돌 가능",
                "감정적 대응으로 악화 우려",
                "개인 의견이 회사 입장으로 오해받을 수 있음"
            ],
            "유형": "개인 vs 조직",
            "포인트": "조직 대표성과 개인 표현의 자유"
        },
        {
            "topic": "비행 중 아픈 승객이 발생했으나, 의사 승객이 술을 마신 상태다. 도움을 요청해야 하는가?",
            "category": "safety",
            "background": "기내에서 응급 상황 발생 시, 승무원은 빠른 판단이 필요합니다. 의료 전문가의 도움과 환자 안전 사이에서 어떤 결정을 내려야 할까요?",
            "pro_points": [
                "의료 지식이 있는 사람의 도움이 필수",
                "생명이 위급한 상황에서 도움 요청은 당연",
                "음주 상태여도 기본 응급처치 가능"
            ],
            "con_points": [
                "음주 상태에서의 의료 행위는 위험",
                "오진 시 책임 소재 문제",
                "다른 방법(지상 의료팀 연락) 고려 필요"
            ],
            "유형": "위기 상황 판단",
            "포인트": "응급 상황 대응과 책임 소재"
        },
        {
            "topic": "저비용항공사가 프리미엄 서비스를 도입하는 것이 바람직한가?",
            "category": "business",
            "background": "에어로케이는 LCC로서 합리적인 가격과 실용적인 서비스를 제공합니다. LCC가 프리미엄 서비스를 도입하면 정체성에 혼란이 생길까요, 아니면 경쟁력이 강화될까요?",
            "pro_points": [
                "다양한 고객 니즈 충족",
                "추가 수익원 확보",
                "브랜드 가치 상승"
            ],
            "con_points": [
                "LCC 정체성 훼손",
                "기존 고객층 이탈 우려",
                "운영 복잡성 증가"
            ],
            "유형": "비즈니스 전략",
            "포인트": "LCC 정체성과 시장 확대의 균형"
        },
        {
            "topic": "승무원 채용에서 외모 기준을 완전히 폐지해야 하는가?",
            "category": "ethics",
            "background": "에어로케이는 젠더리스 유니폼 도입, 블라인드 채용 등 편견을 타파하는 행보를 보이고 있습니다. 외모 기준 폐지에 대해 어떻게 생각하시나요?",
            "pro_points": [
                "실력 중심 채용으로 공정성 확보",
                "다양성과 포용성 강화",
                "외모 차별 논란 원천 차단"
            ],
            "con_points": [
                "서비스직 특성상 단정한 이미지 필요",
                "브랜드 이미지 일관성 유지 어려움",
                "고객 기대와의 괴리 발생 가능"
            ],
            "유형": "다양성 vs 전통",
            "포인트": "에어로케이 브랜드 철학과의 연결"
        },
    ]

    for i, t in enumerate(aerok_debate_topics):
        with st.expander(f"💬 {t['topic']}", expanded=(i==0)):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**유형**: {t['유형']}")
                st.markdown(f"**핵심 포인트**: {t['포인트']}")
                st.markdown(f"**배경**: {t['background']}")

                st.markdown("**찬성 측 논점**")
                for p in t['pro_points']:
                    st.markdown(f"- {p}")

                st.markdown("**반대 측 논점**")
                for p in t['con_points']:
                    st.markdown(f"- {p}")

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🎯 토론 연습하기", key=f"debate_btn_{i}", type="primary", use_container_width=True):
                    # 토론 주제를 세션에 저장하고 토론면접 페이지로 이동
                    st.session_state.debate_topic = t
                    st.session_state.debate_position = None
                    st.session_state.debate_history = []
                    st.session_state.debate_round = 0
                    st.switch_page("pages/5_토론면접.py")

    st.markdown("---")

    # 토론 발언 구조
    st.markdown("#### 📝 효과적인 발언 구조")
    st.markdown("""
    <div style="background: #f0f9ff; padding: 1.5rem; border-radius: 12px; border-left: 4px solid #2563eb;">
        <ol style="margin: 0; padding-left: 1.5rem;">
            <li><strong>주장</strong>: 저는 ~라고 생각합니다.</li>
            <li><strong>근거</strong>: 왜냐하면 ~이기 때문입니다.</li>
            <li><strong>예시</strong>: 실제로 ~ 경험이 있습니다.</li>
            <li><strong>결론</strong>: 따라서 ~해야 한다고 봅니다.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### ⚠️ 피해야 할 행동")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="bad-example">
        ✗ 다른 사람 말 끊기<br>
        ✗ 공격적인 반박<br>
        ✗ 혼자 너무 오래 말하기<br>
        ✗ 주제에서 벗어나기
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="bad-example">
        ✗ 아예 말을 안 하기<br>
        ✗ 앞 사람 의견 그대로 따라하기<br>
        ✗ 감정적으로 반응하기<br>
        ✗ 결론 없이 말 끝내기
        </div>
        """, unsafe_allow_html=True)


# ============================================
# TAB 4: AI 상담
# ============================================
with tab4:
    # 챗봇 전용 CSS
    st.markdown("""
    <style>
    .chat-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 1.5rem;
        border-radius: 16px 16px 0 0;
        color: white;
        margin-bottom: 0;
    }
    .chat-header h3 {
        margin: 0;
        font-size: 1.2rem;
    }
    .chat-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 0.9rem;
    }
    .quick-questions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 1rem 0;
    }
    .quick-q-btn {
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    .quick-q-btn:hover {
        background: #e2e8f0;
        border-color: #cbd5e1;
    }
    .chat-container {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-top: none;
        border-radius: 0 0 16px 16px;
        padding: 1rem;
        min-height: 400px;
        max-height: 500px;
        overflow-y: auto;
    }
    .ai-features {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin: 1rem 0;
    }
    .ai-feature-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .ai-feature-card .icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }
    .ai-feature-card .title {
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.25rem;
    }
    .ai-feature-card .desc {
        font-size: 0.8rem;
        color: #64748b;
    }
    </style>
    """, unsafe_allow_html=True)

    # 챗봇 헤더
    st.markdown("""
    <div class="chat-header">
        <h3>🤖 에어로케이 채용 AI 컨설턴트</h3>
        <p>경험 포트폴리오, 토론면접, 채용 전형에 대해 무엇이든 물어보세요!</p>
    </div>
    """, unsafe_allow_html=True)

    # AI 기능 소개
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="ai-feature-card">
            <div class="icon">📸</div>
            <div class="title">포트폴리오 조언</div>
            <div class="desc">경험 선정 & 사진 가이드</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="ai-feature-card">
            <div class="icon">🗣️</div>
            <div class="title">면접 준비</div>
            <div class="desc">토론/임원면접 팁</div>
        </div>
        """, unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("""
        <div class="ai-feature-card">
            <div class="icon">✈️</div>
            <div class="title">기업 분석</div>
            <div class="desc">에어로케이 인재상</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class="ai-feature-card">
            <div class="icon">💡</div>
            <div class="title">전략 상담</div>
            <div class="desc">합격 전략 수립</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 빠른 질문 버튼
    st.markdown("**💬 자주 묻는 질문**")
    quick_questions = [
        "경험 포트폴리오 어떻게 준비해야 해?",
        "토론면접에서 어떤 주제가 나올까?",
        "에어로케이 인재상이 뭐야?",
        "자소서 폐지 이후 뭐가 달라졌어?",
        "좋은 포트폴리오 사진 예시 알려줘",
        "임원면접 예상 질문이 뭐야?"
    ]

    # 빠른 질문 버튼 (3열)
    cols = st.columns(3)
    for i, q in enumerate(quick_questions):
        with cols[i % 3]:
            if st.button(q, key=f"quick_q_{i}", use_container_width=True):
                st.session_state.aerok_pending_question = q
                st.rerun()

    st.markdown("---")

    # 대화 초기화 버튼
    col_clear, col_spacer = st.columns([1, 3])
    with col_clear:
        if st.button("🗑️ 대화 초기화", type="secondary"):
            st.session_state.aerok_chat_history = []
            st.rerun()

    # 채팅 히스토리 표시 (개선된 UI)
    if not st.session_state.aerok_chat_history:
        # 초기 환영 메시지
        st.markdown("""
        <div style="background: #ecfdf5; border-radius: 12px; padding: 1rem; margin: 1rem 0;">
            <strong>🤖 AI 컨설턴트</strong><br>
            안녕하세요! 에어로케이 채용 AI 컨설턴트입니다.<br><br>
            저는 다음을 도와드릴 수 있어요:<br>
            • 경험 포트폴리오 구성 조언<br>
            • 토론면접/임원면접 준비 전략<br>
            • 에어로케이 기업문화 및 인재상 분석<br>
            • 합격 전략 수립<br><br>
            위의 버튼을 클릭하거나, 아래에 질문을 입력해주세요!
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.aerok_chat_history:
            if msg["role"] == "user":
                st.markdown(f"""
                <div style="background: #dbeafe; border-radius: 12px; padding: 1rem; margin: 0.5rem 0; margin-left: 2rem;">
                    <strong>👤 나</strong><br>
                    {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: #ecfdf5; border-radius: 12px; padding: 1rem; margin: 0.5rem 0; margin-right: 2rem;">
                    <strong>🤖 AI 컨설턴트</strong><br>
                    {msg["content"]}
                </div>
                """, unsafe_allow_html=True)

    # 빠른 질문 처리
    pending_q = st.session_state.get("aerok_pending_question", None)
    if pending_q:
        st.session_state.aerok_pending_question = None
        user_input = pending_q
    else:
        user_input = st.chat_input("에어로케이 채용에 대해 질문해주세요...")

    if user_input:
        # 사용자 메시지 추가
        st.session_state.aerok_chat_history.append({"role": "user", "content": user_input})

        # AI 응답 생성
        client = get_openai_client()
        if client:
            with st.spinner("🤖 답변 생성 중..."):
                # 고도화된 시스템 프롬프트
                enhanced_prompt = PORTFOLIO_SYSTEM_PROMPT + """

## 추가 지침

### 답변 스타일
- 친근하고 격려하는 톤 사용
- 구체적이고 실행 가능한 조언 제공
- 핵심 포인트는 굵게 또는 리스트로 강조
- 적절한 이모지 사용으로 가독성 향상

### 답변 구조
1. 질문 핵심 파악 및 공감
2. 구체적인 답변/조언
3. 추가 팁 또는 관련 정보
4. 후속 질문 유도 (선택적)

### 에어로케이 특화 정보
- 2026년 자소서 전면 폐지 → 경험 포트폴리오(사진 3장)
- 승무원 = 기내 안전요원 (강인함 강조)
- 젠더리스 유니폼, 수평적 문화
- 블라인드 채용 (사진 제출 금지)
- 토론면접 → 임원면접 순서
"""

                messages = [{"role": "system", "content": enhanced_prompt}]
                for msg in st.session_state.aerok_chat_history[-15:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})

                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=1500
                    )

                    ai_response = response.choices[0].message.content
                    st.session_state.aerok_chat_history.append({"role": "assistant", "content": ai_response})
                    st.rerun()
                except Exception as e:
                    st.error(f"응답 생성 실패: {e}")
        else:
            st.error("AI 서비스에 연결할 수 없습니다.")


# ============================================
# 페이지 종료
# ============================================
end_page()

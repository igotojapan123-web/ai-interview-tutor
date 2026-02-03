# pages/19_자소서작성.py
# AI 자소서 작성 도우미 - 문항 의도 분석 + 고도화 챗봇

import os
import sys
import json
import streamlit as st
from datetime import datetime

# 상위 디렉토리 import 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AIRLINES_WITH_RESUME, AIRLINE_DATA, AIRLINE_VALUES
from sidebar_common import init_page, end_page

# 모듈 import
try:
    from resume_writer_helper import (
        analyze_question_intent,
        generate_chatbot_response,
        get_initial_greeting,
        get_airline_context
    )
    HELPER_AVAILABLE = True
except ImportError as e:
    HELPER_AVAILABLE = False
    print(f"[19_자소서작성] resume_writer_helper import 실패: {e}")

try:
    from news_scraper import get_airline_news
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False

# 페이지 초기화
init_page(
    title="AI 자소서 작성",
    current_page="자소서작성",
    wide_layout=True
)

# ============================================
# Session State 초기화
# ============================================
defaults = {
    "rw_airline": AIRLINES_WITH_RESUME[0] if AIRLINES_WITH_RESUME else "대한항공",
    "rw_questions": [""],
    "rw_analysis_results": [],
    "rw_analyzed": False,
    "rw_chat_history": [],
    "rw_chat_initialized": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================
# CSS 스타일
# ============================================
st.markdown("""
<style>
/* 모든 입력 필드에서 복사/붙여넣기 허용 - 강화된 선택자 */
textarea, input, [contenteditable="true"],
.stTextArea textarea, .stTextInput input,
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input,
div[data-baseweb="textarea"] textarea,
div[data-baseweb="input"] input {
    -webkit-user-select: text !important;
    -moz-user-select: text !important;
    -ms-user-select: text !important;
    user-select: text !important;
    -webkit-user-drag: none !important;
    pointer-events: auto !important;
}

/* 전체 문서에서 텍스트 선택 허용 */
* {
    -webkit-user-select: text !important;
    -moz-user-select: text !important;
    -ms-user-select: text !important;
    user-select: text !important;
}

/* 버튼과 특수 요소는 제외 */
button, .stButton, [role="button"] {
    -webkit-user-select: none !important;
    user-select: none !important;
}

@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

/* 폰트 설정 - user-select와 별도로 */
body, .stApp {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.analysis-card {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
    border: 1px solid #e2e8f0;
}

.analysis-section {
    margin: 16px 0;
    padding: 16px;
    background: white;
    border-radius: 12px;
    border-left: 4px solid #2563eb;
}

.analysis-title {
    font-size: 14px;
    font-weight: 600;
    color: #2563eb;
    margin-bottom: 8px;
}

.analysis-content {
    font-size: 15px;
    color: #334155;
    line-height: 1.7;
}

.keyword-tag {
    display: inline-block;
    background: #2563eb15;
    color: #2563eb;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 13px;
    margin: 4px;
    border: 1px solid #2563eb30;
}

.avoid-tag {
    display: inline-block;
    background: #ef444415;
    color: #ef4444;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 13px;
    margin: 4px;
    border: 1px solid #ef444430;
}

.chat-container {
    background: #f8fafc;
    border-radius: 16px;
    padding: 16px;
    height: 500px;
    overflow-y: auto;
    border: 1px solid #e2e8f0;
}

.chat-message-user {
    background: #2563eb;
    color: white;
    padding: 12px 16px;
    border-radius: 16px 16px 4px 16px;
    margin: 8px 0;
    margin-left: 20%;
    font-size: 14px;
    line-height: 1.6;
}

.chat-message-ai {
    background: white;
    color: #334155;
    padding: 12px 16px;
    border-radius: 16px 16px 16px 4px;
    margin: 8px 0;
    margin-right: 20%;
    font-size: 14px;
    line-height: 1.6;
    border: 1px solid #e2e8f0;
}

.chat-ai-label {
    font-size: 12px;
    color: #64748b;
    margin-bottom: 4px;
}

.question-box {
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
    margin: 12px 0;
    transition: border-color 0.2s;
}

.question-box:hover {
    border-color: #2563eb;
}

.news-item {
    background: #fffbeb;
    border-left: 3px solid #f59e0b;
    padding: 8px 12px;
    margin: 4px 0;
    font-size: 13px;
    border-radius: 0 8px 8px 0;
}

.guideline-item {
    display: flex;
    align-items: flex-start;
    padding: 8px 0;
    border-bottom: 1px solid #f1f5f9;
}

.guideline-number {
    background: #2563eb;
    color: white;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: bold;
    margin-right: 12px;
    flex-shrink: 0;
}

.guideline-text {
    color: #334155;
    font-size: 14px;
    line-height: 1.6;
}

.example-draft {
    background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
    border-radius: 12px;
    padding: 16px;
    margin-top: 12px;
    border: 1px solid #10b98130;
}

.example-draft-label {
    font-size: 12px;
    color: #059669;
    font-weight: 600;
    margin-bottom: 8px;
}

.example-draft-text {
    font-size: 14px;
    color: #065f46;
    line-height: 1.7;
    font-style: italic;
}
</style>
""", unsafe_allow_html=True)


# ============================================
# 헬퍼 함수
# ============================================

def render_chat_message(role: str, content: str):
    """채팅 메시지 렌더링"""
    if role == "user":
        st.markdown(f'<div class="chat-message-user">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-ai-label">AI 컨설턴트</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-message-ai">{content}</div>', unsafe_allow_html=True)


def render_analysis_result(result: dict, index: int):
    """분석 결과 렌더링"""
    question = result.get("question", f"문항 {index + 1}")

    st.markdown(f"### 문항 {index + 1}: {question[:50]}{'...' if len(question) > 50 else ''}")

    # 의도
    st.markdown(f"""
    <div class="analysis-section">
        <div class="analysis-title">문항 의도</div>
        <div class="analysis-content">{result.get('intent', 'N/A')}</div>
    </div>
    """, unsafe_allow_html=True)

    # 숨은 의미
    if result.get('hidden_meaning'):
        st.markdown(f"""
        <div class="analysis-section" style="border-left-color: #7c3aed;">
            <div class="analysis-title" style="color: #7c3aed;">숨은 의도</div>
            <div class="analysis-content">{result.get('hidden_meaning')}</div>
        </div>
        """, unsafe_allow_html=True)

    # 항공사 맞춤 방향
    airline_fit = result.get('airline_fit', [])
    if airline_fit:
        if isinstance(airline_fit, list):
            fit_html = "<ul style='margin:0; padding-left:20px;'>"
            for item in airline_fit:
                fit_html += f"<li style='margin:4px 0; color:#334155;'>{item}</li>"
            fit_html += "</ul>"
        else:
            fit_html = f"<div class='analysis-content'>{airline_fit}</div>"

        st.markdown(f"""
        <div class="analysis-section" style="border-left-color: #059669;">
            <div class="analysis-title" style="color: #059669;">{st.session_state.rw_airline}이 원하는 답변</div>
            {fit_html}
        </div>
        """, unsafe_allow_html=True)

    # 최근 트렌드
    if result.get('news_context'):
        st.markdown(f"""
        <div class="news-item">
            <strong>최근 트렌드:</strong> {result.get('news_context')}
        </div>
        """, unsafe_allow_html=True)

    # 가이드라인
    guidelines = result.get('guidelines', [])
    if guidelines:
        st.markdown("**작성 가이드라인**")
        guidelines_html = ""
        for i, g in enumerate(guidelines, 1):
            guidelines_html += f"""
            <div class="guideline-item">
                <div class="guideline-number">{i}</div>
                <div class="guideline-text">{g}</div>
            </div>
            """
        st.markdown(guidelines_html, unsafe_allow_html=True)

    # 권장 구조
    if result.get('structure'):
        st.info(f"**권장 구조:** {result.get('structure')}")

    # 키워드 & 피해야 할 표현
    col1, col2 = st.columns(2)
    with col1:
        keywords = result.get('keywords', [])
        if keywords:
            keywords_html = " ".join([f'<span class="keyword-tag">{k}</span>' for k in keywords])
            st.markdown(f"**추천 키워드**<br>{keywords_html}", unsafe_allow_html=True)

    with col2:
        avoid = result.get('avoid', [])
        if avoid:
            avoid_html = " ".join([f'<span class="avoid-tag">{a}</span>' for a in avoid])
            st.markdown(f"**피해야 할 표현**<br>{avoid_html}", unsafe_allow_html=True)

    # 예시 초안
    if result.get('example_draft'):
        st.markdown(f"""
        <div class="example-draft">
            <div class="example-draft-label">예시 초안 (참고용 - 본인 경험으로 대체 필수)</div>
            <div class="example-draft-text">"{result.get('example_draft')}"</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")


# ============================================
# 메인 UI
# ============================================

st.markdown("## AI 자소서 작성 도우미")
st.caption("문항의 숨은 의도를 파악하고, AI 컨설턴트와 함께 자소서를 작성하세요.")

st.markdown("---")

if not HELPER_AVAILABLE:
    st.error("자소서 작성 도우미 모듈을 불러올 수 없습니다.")
    st.stop()

# --------------------------------------------
# 항공사 선택
# --------------------------------------------
st.markdown("### 1. 항공사 선택")

col1, col2 = st.columns([2, 3])
with col1:
    selected_airline = st.selectbox(
        "지원 항공사",
        AIRLINES_WITH_RESUME,
        index=AIRLINES_WITH_RESUME.index(st.session_state.rw_airline) if st.session_state.rw_airline in AIRLINES_WITH_RESUME else 0,
        key="airline_selector"
    )

    # 항공사 변경시 초기화
    if selected_airline != st.session_state.rw_airline:
        st.session_state.rw_airline = selected_airline
        st.session_state.rw_analyzed = False
        st.session_state.rw_analysis_results = []
        st.session_state.rw_chat_history = []
        st.session_state.rw_chat_initialized = False

with col2:
    airline_info = AIRLINE_DATA.get(selected_airline, {})
    if airline_info:
        type_badge = {
            'FSC': ('FSC', '#2563eb'),
            'LCC': ('LCC', '#059669'),
            'HSC': ('HSC', '#7c3aed')
        }.get(airline_info.get('type', ''), ('', '#64748b'))

        st.markdown(f"""
        <div style="background:#f8fafc; padding:12px 16px; border-radius:12px; margin-top:8px;">
            <span style="background:{type_badge[1]}; color:white; padding:3px 10px; border-radius:10px; font-size:12px; font-weight:600;">{type_badge[0]}</span>
            <span style="margin-left:12px; color:#64748b; font-size:13px;">{airline_info.get('mission', '')}</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# --------------------------------------------
# 문항 입력
# --------------------------------------------
st.markdown("### 2. 문항 입력")
st.caption("자소서 문항을 입력하세요. 여러 문항을 추가할 수 있습니다.")

# 문항 리스트 관리
questions_to_remove = []

for i, q in enumerate(st.session_state.rw_questions):
    col1, col2 = st.columns([9, 1])

    with col1:
        new_value = st.text_input(
            f"문항 {i+1}",
            value=q,
            placeholder="예: 지원동기를 작성하세요 (500자 이내)",
            key=f"q_input_{i}",
            label_visibility="collapsed"
        )
        st.session_state.rw_questions[i] = new_value

    with col2:
        if len(st.session_state.rw_questions) > 1:
            if st.button("X", key=f"del_q_{i}", help="문항 삭제"):
                questions_to_remove.append(i)

# 삭제 처리
for idx in sorted(questions_to_remove, reverse=True):
    st.session_state.rw_questions.pop(idx)
    if st.session_state.rw_analysis_results and idx < len(st.session_state.rw_analysis_results):
        st.session_state.rw_analysis_results.pop(idx)

if questions_to_remove:
    st.rerun()

# 문항 추가 버튼
if st.button("+ 문항 추가", use_container_width=False):
    st.session_state.rw_questions.append("")
    st.rerun()

st.markdown("---")

# --------------------------------------------
# 분석 버튼
# --------------------------------------------
valid_questions = [q.strip() for q in st.session_state.rw_questions if q.strip()]

if st.button(
    "문항 분석하기",
    type="primary",
    use_container_width=True,
    disabled=len(valid_questions) == 0
):
    with st.spinner("AI가 문항을 분석하고 있습니다..."):
        results = []
        for q in valid_questions:
            result = analyze_question_intent(q, st.session_state.rw_airline)
            results.append(result)

        st.session_state.rw_analysis_results = results
        st.session_state.rw_analyzed = True

        # 챗봇 초기화
        if not st.session_state.rw_chat_initialized:
            greeting = get_initial_greeting(st.session_state.rw_airline)
            st.session_state.rw_chat_history = [
                {"role": "assistant", "content": greeting}
            ]
            st.session_state.rw_chat_initialized = True

    st.rerun()

# --------------------------------------------
# 분석 결과 + 챗봇 (2열 레이아웃)
# --------------------------------------------
if st.session_state.rw_analyzed and st.session_state.rw_analysis_results:
    st.markdown("---")
    st.markdown("### 3. 분석 결과 & 작성 도우미")

    col_analysis, col_chat = st.columns([1, 1])

    # 왼쪽: 분석 결과
    with col_analysis:
        st.markdown("#### 문항 분석")

        for i, result in enumerate(st.session_state.rw_analysis_results):
            with st.expander(f"문항 {i+1} 분석 결과", expanded=(i == 0)):
                render_analysis_result(result, i)

    # 오른쪽: 챗봇
    with col_chat:
        st.markdown("#### AI 작성 도우미")

        # 채팅 히스토리 표시
        for msg in st.session_state.rw_chat_history:
            render_chat_message(msg["role"], msg["content"])

        # 입력창
        user_input = st.chat_input("메시지를 입력하세요...", key="chat_input")

        if user_input:
            # 사용자 메시지 추가
            st.session_state.rw_chat_history.append({
                "role": "user",
                "content": user_input
            })

            # AI 응답 생성
            with st.spinner("AI가 응답을 생성하고 있습니다..."):
                response = generate_chatbot_response(
                    user_input,
                    st.session_state.rw_chat_history[:-1],  # 마지막 메시지 제외
                    st.session_state.rw_airline,
                    valid_questions,
                    st.session_state.rw_analysis_results
                )

            # AI 응답 추가
            st.session_state.rw_chat_history.append({
                "role": "assistant",
                "content": response
            })

            st.rerun()

        # 채팅 초기화 버튼
        if st.button("대화 초기화", key="reset_chat"):
            greeting = get_initial_greeting(st.session_state.rw_airline)
            st.session_state.rw_chat_history = [
                {"role": "assistant", "content": greeting}
            ]
            st.rerun()

# --------------------------------------------
# 뉴스 섹션 (선택사항)
# --------------------------------------------
if NEWS_AVAILABLE and st.session_state.rw_airline:
    with st.expander("최근 뉴스 보기", expanded=False):
        news = get_airline_news(st.session_state.rw_airline, days=90)[:10]

        if news:
            for item in news:
                st.markdown(f"""
                <div class="news-item">
                    <strong>[{item.get('published_at', '날짜 미상')}]</strong>
                    <a href="{item.get('url', '#')}" target="_blank" style="color:#d97706; text-decoration:none;">
                        {item.get('title', '제목 없음')}
                    </a>
                    <span style="color:#92400e; font-size:11px;">({item.get('source', '')})</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("최근 뉴스 정보가 없습니다.")

# 페이지 종료
end_page()

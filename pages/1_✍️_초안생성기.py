"""
대한항공 자소서 초안 생성기
5분 대화 -> 60점 초안 완성
"""

import streamlit as st
from datetime import date
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.draft_generator import DraftGenerator, validate_draft_score
from data.interview_questions import get_question_count
from data.essay_prompts import ESSAY_PROMPTS

st.set_page_config(page_title="초안생성기 - 대한항공", page_icon="✍️", layout="wide")

# 비밀번호 보호 체크
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("먼저 메인 페이지에서 비밀번호를 입력해주세요.")
    if st.button("메인으로 이동"):
        st.switch_page("app.py")
    st.stop()

# CSS
st.markdown("""
<style>
    [data-testid="stSidebarNav"] li:first-child { display: none; }

    .chat-container {
        max-width: 800px;
        margin: 0 auto;
    }

    .question-card {
        background: linear-gradient(135deg, #00256C 0%, #0052CC 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1rem;
    }
    .question-card p { margin: 0; font-size: 1rem; line-height: 1.6; }

    .progress-container {
        background: #f1f5f9;
        border-radius: 20px;
        padding: 1rem 1.5rem;
        margin-bottom: 1.5rem;
    }
    .progress-bar-bg {
        background: #e2e8f0;
        border-radius: 10px;
        height: 10px;
        overflow: hidden;
    }
    .progress-bar-fill {
        background: linear-gradient(90deg, #00256C, #0078D4);
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s ease;
    }

    .draft-result {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        border: 2px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }

    .score-badge {
        display: inline-block;
        background: linear-gradient(135deg, #00256C, #0078D4);
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 1.2rem;
    }

    .char-count {
        font-size: 0.9rem;
        color: #64748b;
        text-align: right;
        margin-top: 0.5rem;
    }

    .btn-group {
        display: flex;
        gap: 1rem;
        margin-top: 1.5rem;
    }

    .intro-card {
        background: linear-gradient(135deg, #f8fafc, #fff);
        border: 2px solid #e2e8f0;
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    .intro-card h3 { color: #00256C; margin-bottom: 1rem; }

    .question-select-btn {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: left;
        cursor: pointer;
        transition: all 0.3s ease;
        margin-bottom: 1rem;
    }
    .question-select-btn:hover {
        border-color: #00256C;
        box-shadow: 0 4px 12px rgba(0, 37, 108, 0.15);
    }
</style>
""", unsafe_allow_html=True)

# D-Day 사이드바
deadline = date(2026, 2, 24)
dday = (deadline - date.today()).days
if dday > 0:
    urgency_color = "#ef4444" if dday <= 7 else "#f59e0b" if dday <= 14 else "#00256C"
    st.sidebar.markdown(f"""
    <div style="background: linear-gradient(135deg, {urgency_color}, #0078D4); color: white; padding: 16px; border-radius: 12px; text-align: center;">
        <div style="font-size: 0.85rem; opacity: 0.9;">{'마감 임박!' if dday <= 7 else '서류 마감'}</div>
        <div style="font-size: 1.8rem; font-weight: 800;">D-{dday}</div>
    </div>
    """, unsafe_allow_html=True)

# 세션 상태 초기화
if "draft_generator" not in st.session_state:
    st.session_state.draft_generator = None
if "draft_messages" not in st.session_state:
    st.session_state.draft_messages = []
if "draft_result" not in st.session_state:
    st.session_state.draft_result = None
if "selected_question" not in st.session_state:
    st.session_state.selected_question = None

# 헤더
st.markdown("""
<div style="background: linear-gradient(135deg, #00256C 0%, #0052CC 100%); color: white; padding: 2rem; border-radius: 20px; text-align: center; margin-bottom: 2rem; box-shadow: 0 15px 40px rgba(0, 37, 108, 0.3);">
    <h1 style="color: white; margin: 0; font-size: 2rem;">✍️ 자소서 초안 생성기</h1>
    <p style="opacity: 0.9; margin-top: 0.5rem;">5분 대화 → 60점 초안 완성</p>
</div>
""", unsafe_allow_html=True)


def reset_generator():
    """생성기 초기화"""
    st.session_state.draft_generator = None
    st.session_state.draft_messages = []
    st.session_state.draft_result = None
    st.session_state.selected_question = None


def start_interview(question_num: int):
    """인터뷰 시작"""
    st.session_state.selected_question = question_num
    st.session_state.draft_generator = DraftGenerator(question_num)
    st.session_state.draft_messages = []
    st.session_state.draft_result = None

    # 첫 질문 추가
    first_q = st.session_state.draft_generator.get_first_question()
    st.session_state.draft_messages.append({
        "role": "assistant",
        "content": first_q
    })


# ═══════════════════════════════════════════════
# 문항 선택 화면
# ═══════════════════════════════════════════════

if st.session_state.selected_question is None:
    st.markdown("""
    <div class="intro-card">
        <h3>자소서, 어디서부터 시작해야 할지 모르겠다면?</h3>
        <p style="color: #64748b;">5분만 대화하면 초안이 완성됩니다.<br>
        빈 종이 앞에서 고민하는 시간, 이제 끝!</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 어떤 문항부터 시작할까요?")

    for i, prompt in enumerate(ESSAY_PROMPTS, 1):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"""
            <div style="background: white; border: 2px solid #e2e8f0; border-radius: 12px; padding: 1.2rem; margin-bottom: 0.5rem;">
                <div style="font-weight: 700; color: #00256C; margin-bottom: 0.5rem;">문항 {i}</div>
                <div style="color: #475569; font-size: 0.95rem;">{prompt['prompt']}</div>
                <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;">질문 {get_question_count(i)}개 | 약 5분 소요</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("시작", key=f"start_q{i}", use_container_width=True):
                start_interview(i)
                st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style="background: #fef3c7; border-radius: 12px; padding: 1rem; border-left: 4px solid #f59e0b;">
        <strong>초안 생성기 특징</strong><br>
        - 학원에서 2시간 걸리는 걸 AI가 5분에<br>
        - 경험은 있는데 글이 안 써지는 사람을 위한<br>
        - 완성된 초안을 첨삭받아 80점까지 올리기
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# 인터뷰 진행 화면
# ═══════════════════════════════════════════════

elif st.session_state.draft_generator and st.session_state.draft_result is None:
    generator = st.session_state.draft_generator
    current, total = generator.get_progress()

    # 문항 정보
    prompt_info = ESSAY_PROMPTS[st.session_state.selected_question - 1]
    st.markdown(f"""
    <div class="question-card">
        <p><strong>문항 {st.session_state.selected_question}</strong></p>
        <p>{prompt_info['prompt']}</p>
    </div>
    """, unsafe_allow_html=True)

    # 진행률
    progress_pct = (current / total) * 100
    st.markdown(f"""
    <div class="progress-container">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="font-weight: 600; color: #00256C;">인터뷰 진행 중</span>
            <span style="color: #64748b;">{current}/{total} 질문 완료</span>
        </div>
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width: {progress_pct}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 채팅 메시지 표시
    for msg in st.session_state.draft_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 사용자 입력
    if user_input := st.chat_input("답변을 입력하세요..."):
        # 사용자 메시지 추가
        st.session_state.draft_messages.append({
            "role": "user",
            "content": user_input
        })

        # 답변 처리
        result = generator.process_answer(user_input)

        if result["type"] == "generate":
            # 초안 생성 시작
            st.session_state.draft_messages.append({
                "role": "assistant",
                "content": result["message"]
            })

            # 초안 생성
            with st.spinner("초안을 생성하고 있어요..."):
                draft, code_score = generator.generate_calibrated_draft()
                validation = validate_draft_score(draft, st.session_state.selected_question)

                st.session_state.draft_result = {
                    "draft": draft,
                    "code_score": code_score,
                    "estimated_score": validation["estimated_total"],
                    "details": validation["details"]
                }

        else:
            # 다음 질문 또는 후속 질문
            st.session_state.draft_messages.append({
                "role": "assistant",
                "content": result["message"]
            })

        st.rerun()

    # 포기 버튼
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button("처음으로", use_container_width=True):
            reset_generator()
            st.rerun()


# ═══════════════════════════════════════════════
# 초안 완성 화면
# ═══════════════════════════════════════════════

elif st.session_state.draft_result:
    result = st.session_state.draft_result
    draft = result["draft"]
    estimated_score = result["estimated_score"]

    st.markdown("### 초안이 완성되었어요!")

    # 점수 표시
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"""
        <div class="draft-result">
            <div style="margin-bottom: 1rem;">
                <span class="score-badge">예상 점수: 약 {estimated_score}점</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 초안 텍스트 (편집 가능)
    st.markdown("#### 생성된 초안")
    char_count = len(draft.replace(" ", "").replace("\n", ""))

    edited_draft = st.text_area(
        "초안 (수정 가능)",
        value=draft,
        height=300,
        label_visibility="collapsed",
        key="draft_text"
    )

    # 수정 후 글자수
    new_char_count = len(edited_draft.replace(" ", "").replace("\n", ""))
    char_color = "#22c55e" if new_char_count <= 600 else "#ef4444"

    st.markdown(f"""
    <div class="char-count" style="color: {char_color};">
        글자수: {new_char_count}/600자 {'(초과!)' if new_char_count > 600 else ''}
    </div>
    """, unsafe_allow_html=True)

    # 버튼들
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("복사하기", use_container_width=True):
            st.code(edited_draft, language=None)
            st.success("위 내용을 복사하세요!")

    with col2:
        if st.button("첨삭받기", type="primary", use_container_width=True):
            # 세션에 초안 저장 후 첨삭 페이지로 이동
            st.session_state.resume_for_review = edited_draft
            st.session_state.review_question_num = st.session_state.selected_question
            st.switch_page("pages/2_📝_자소서첨삭.py")

    with col3:
        if st.button("다시 만들기", use_container_width=True):
            reset_generator()
            st.rerun()

    # 안내 메시지
    st.markdown("---")
    st.markdown("""
    <div style="background: #f0f9ff; border-radius: 12px; padding: 1.5rem; border-left: 4px solid #3b82f6;">
        <strong>다음 단계</strong><br>
        이 초안은 약 60점 수준입니다. 첨삭을 받으면 80점 이상까지 올릴 수 있어요!<br><br>
        <strong>개선 포인트 예시:</strong><br>
        - 첫 문장을 숫자로 시작하기 (앵커링)<br>
        - 인재상 키워드 자연스럽게 추가<br>
        - 마지막 문장을 구체적으로 바꾸기 (피크엔드)
    </div>
    """, unsafe_allow_html=True)

    # 수집된 경험 데이터 (접기)
    with st.expander("수집된 경험 데이터 보기"):
        generator = st.session_state.draft_generator
        if generator:
            for q_id, data in generator.get_collected_answers().items():
                st.markdown(f"**Q: {data['question']}**")
                st.markdown(f"A: {data['answer']}")
                st.markdown("---")


# 사이드바 안내
with st.sidebar:
    st.markdown("---")
    st.markdown("### 초안 생성기 안내")
    st.markdown("""
    **작동 방식**
    1. 문항 선택
    2. 7~9개 질문에 답변
    3. AI가 60점 초안 생성
    4. 첨삭받아 80점까지 상승

    **특징**
    - 사용자 경험만 사용 (창작 X)
    - 탈락 패턴 자동 제거
    - 구조/분량 자동 조절
    """)

    st.markdown("---")
    st.markdown("### 주의사항")
    st.markdown("""
    - 솔직하게 답변하세요
    - 숫자를 기억해두세요
    - 초안은 시작점입니다
    """)

    if st.session_state.draft_generator:
        st.markdown("---")
        if st.button("처음부터 다시", use_container_width=True):
            reset_generator()
            st.rerun()

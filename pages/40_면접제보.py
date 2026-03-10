# pages/40_면접제보.py
# 면접 제보 시스템 - 사용자가 면접 질문 제보 시 보상 지급

# 정식 웹사이트 이전 안내
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from redirect_to_web import show_redirect_and_stop
show_redirect_and_stop()

import os
import sys
import streamlit as st
from datetime import datetime, timedelta

# 상위 디렉토리 import 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AIRLINES
from sidebar_common import init_page, end_page

# 제보 시스템 모듈
try:
    from interview_report_system import (
        submit_report,
        get_reward_display,
        get_airline_report_count,
        check_duplicate_submission,
        generate_user_hash
    )
    SYSTEM_AVAILABLE = True
except ImportError as e:
    SYSTEM_AVAILABLE = False
    print(f"[40_면접제보] interview_report_system import 실패: {e}")

# 페이지 초기화
init_page(
    title="면접 제보",
    current_page="면접제보",
    wide_layout=True
)

# ============================================
# Session State 초기화
# ============================================
defaults = {
    "report_airline": AIRLINES[0] if AIRLINES else "대한항공",
    "report_date": datetime.now().date(),
    "report_stage": "1차",
    "report_questions": [{"question": "", "follow_up": "", "my_answer": ""}],
    "report_mood": None,
    "report_interviewer_count": None,
    "report_duration": None,
    "report_notes": "",
    "report_submitted": False,
    "report_result": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ============================================
# CSS 스타일
# ============================================
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

.report-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 2rem;
}

.report-header h1 {
    margin: 0;
    font-size: 1.8rem;
    font-weight: 700;
}

.report-header p {
    margin: 0.5rem 0 0 0;
    opacity: 0.9;
}

.reward-card {
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
    border-left: 4px solid #667eea;
}

.reward-card.gold {
    background: linear-gradient(135deg, #fff9e6 0%, #ffeaa7 100%);
    border-left-color: #f1c40f;
}

.reward-card.silver {
    background: linear-gradient(135deg, #f8f9fa 0%, #dfe6e9 100%);
    border-left-color: #95a5a6;
}

.reward-card.bronze {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    border-left-color: #e67e22;
}

.question-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
}

.question-number {
    background: #667eea;
    color: white;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.9rem;
    margin-right: 0.5rem;
}

.reward-table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
}

.reward-table th, .reward-table td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #e2e8f0;
}

.reward-table th {
    background: #f8fafc;
    font-weight: 600;
}

.success-message {
    background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
    border: 1px solid #28a745;
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
}

.warning-message {
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ============================================
# 헤더
# ============================================
st.markdown("""
<div class="report-header">
    <h1>면접 제보</h1>
    <p>면접 다녀오셨나요? 질문을 공유하고 프리미엄 이용권을 받으세요!</p>
</div>
""", unsafe_allow_html=True)

if not SYSTEM_AVAILABLE:
    st.error("제보 시스템을 불러올 수 없습니다. 관리자에게 문의하세요.")
    end_page()
    st.stop()

# 이미 제출 완료된 경우
if st.session_state.report_submitted and st.session_state.report_result:
    result = st.session_state.report_result

    if result["success"]:
        reward_info = get_reward_display(result["reward"])

        st.markdown(f"""
        <div class="success-message">
            <h2>제보 완료!</h2>
            <p><strong>보상:</strong> {reward_info['label']}</p>
            <p>소중한 정보 감사합니다. 다른 지원자들에게 큰 도움이 됩니다.</p>
        </div>
        """, unsafe_allow_html=True)

        if result.get("warnings"):
            for warn in result["warnings"]:
                st.warning(warn)

        if st.button("새 제보하기", type="primary"):
            st.session_state.report_submitted = False
            st.session_state.report_result = None
            st.session_state.report_questions = [{"question": "", "follow_up": "", "my_answer": ""}]
            st.rerun()
    else:
        st.error(result["message"])
        if st.button("다시 시도"):
            st.session_state.report_submitted = False
            st.rerun()

    end_page()
    st.stop()

# ============================================
# 보상 안내
# ============================================
with st.expander("보상 기준 안내", expanded=False):
    st.markdown("""
    | 조건 | 보상 |
    |------|------|
    | 질문 8개 이상 + 꼬리질문 + 상세정보 | **프리미엄 14일** |
    | 질문 5개 이상 + 상세정보 | **프리미엄 7일** |
    | 질문 3개 이상 | **프리미엄 3일** |
    | 질문 1개 이상 | **프리미엄 1일** |

    *상세정보 = 면접 분위기 + 소요 시간 입력*
    """)

# ============================================
# 제보 폼
# ============================================
st.markdown("### 기본 정보")

col1, col2, col3 = st.columns(3)

with col1:
    airline = st.selectbox(
        "항공사 *",
        options=AIRLINES,
        index=AIRLINES.index(st.session_state.report_airline) if st.session_state.report_airline in AIRLINES else 0,
        key="input_airline"
    )
    # 현재 제보 수 표시
    report_count = get_airline_report_count(airline)
    st.caption(f"현재 {airline} 제보: {report_count}건")

with col2:
    interview_date = st.date_input(
        "면접 날짜 *",
        value=st.session_state.report_date,
        max_value=datetime.now().date(),
        key="input_date"
    )

with col3:
    stage = st.selectbox(
        "면접 단계 *",
        options=["서류", "1차", "2차", "최종", "영어면접", "그룹토론"],
        index=["서류", "1차", "2차", "최종", "영어면접", "그룹토론"].index(st.session_state.report_stage) if st.session_state.report_stage in ["서류", "1차", "2차", "최종", "영어면접", "그룹토론"] else 1,
        key="input_stage"
    )

st.markdown("---")

# ============================================
# 질문 입력
# ============================================
st.markdown("### 면접 질문 (최소 1개 필수)")
st.caption("기억나는 질문을 모두 입력해주세요. 많이 입력할수록 보상이 커집니다!")

# 질문 추가/삭제 버튼
col_add, col_remove = st.columns([1, 1])
with col_add:
    if st.button("+ 질문 추가"):
        st.session_state.report_questions.append({"question": "", "follow_up": "", "my_answer": ""})
        st.rerun()

with col_remove:
    if len(st.session_state.report_questions) > 1:
        if st.button("- 마지막 질문 삭제"):
            st.session_state.report_questions.pop()
            st.rerun()

# 질문 입력 폼
for i, q in enumerate(st.session_state.report_questions):
    with st.container():
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-top: 1rem;">
            <span class="question-number">{i+1}</span>
            <span style="font-weight: 600;">질문 {i+1}</span>
        </div>
        """, unsafe_allow_html=True)

        q["question"] = st.text_area(
            f"질문 내용 *",
            value=q.get("question", ""),
            key=f"q_{i}_main",
            placeholder="예: 지원동기가 뭐예요?",
            height=80,
            label_visibility="collapsed"
        )

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            q["follow_up"] = st.text_input(
                "꼬리질문 (선택)",
                value=q.get("follow_up", ""),
                key=f"q_{i}_followup",
                placeholder="예: 왜 다른 항공사가 아니라 여기인가요?"
            )
        with col_f2:
            q["my_answer"] = st.text_input(
                "내 답변 요약 (선택)",
                value=q.get("my_answer", ""),
                key=f"q_{i}_answer",
                placeholder="예: 고객 서비스 철학 언급"
            )

st.markdown("---")

# ============================================
# 추가 정보 (선택)
# ============================================
st.markdown("### 추가 정보 (선택)")
st.caption("더 많은 정보를 입력하면 더 큰 보상을 받을 수 있습니다!")

col_opt1, col_opt2, col_opt3 = st.columns(3)

with col_opt1:
    mood = st.selectbox(
        "면접 분위기",
        options=[None, "편안함", "보통", "압박"],
        format_func=lambda x: "선택 안 함" if x is None else x,
        key="input_mood"
    )

with col_opt2:
    interviewer_count = st.number_input(
        "면접관 수",
        min_value=0,
        max_value=10,
        value=0,
        key="input_interviewer_count"
    )
    if interviewer_count == 0:
        interviewer_count = None

with col_opt3:
    duration = st.number_input(
        "소요 시간 (분)",
        min_value=0,
        max_value=120,
        value=0,
        key="input_duration"
    )
    if duration == 0:
        duration = None

additional_notes = st.text_area(
    "기타 특이사항",
    value=st.session_state.report_notes,
    key="input_notes",
    placeholder="예: 뉴스 관련 질문이 많았음, 영어 질문이 갑자기 나옴 등",
    height=100
)

st.markdown("---")

# ============================================
# 예상 보상 미리보기
# ============================================
valid_questions = [q for q in st.session_state.report_questions if q.get("question", "").strip()]
question_count = len(valid_questions)
has_followup = any(q.get("follow_up") for q in valid_questions)
has_details = mood is not None and duration is not None

# 예상 보상 계산
if question_count >= 8 and has_followup and has_details:
    expected_reward = "premium_14days"
elif question_count >= 5 and has_details:
    expected_reward = "premium_7days"
elif question_count >= 3:
    expected_reward = "premium_3days"
elif question_count >= 1:
    expected_reward = "premium_1day"
else:
    expected_reward = None

if expected_reward:
    reward_info = get_reward_display(expected_reward)
    st.info(f"현재 예상 보상: **{reward_info['label']}** (질문 {question_count}개)")

# ============================================
# 제출 버튼
# ============================================
st.markdown("")

if st.button("제보하기", type="primary", use_container_width=True):
    # 유효성 검사
    if question_count == 0:
        st.error("최소 1개 이상의 질문을 입력해주세요.")
    else:
        # 세션 ID (없으면 생성)
        if "user_session_id" not in st.session_state:
            import uuid
            st.session_state.user_session_id = str(uuid.uuid4())

        # 제출
        result = submit_report(
            airline=airline,
            interview_date=str(interview_date),
            interview_stage=stage,
            questions=valid_questions,
            interview_mood=mood,
            interviewer_count=interviewer_count,
            duration_minutes=duration,
            additional_notes=additional_notes,
            user_session_id=st.session_state.user_session_id
        )

        st.session_state.report_submitted = True
        st.session_state.report_result = result
        st.rerun()

# 푸터
end_page()

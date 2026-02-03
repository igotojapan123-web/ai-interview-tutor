# new_features/2_타임어택모드.py
# FlyReady Lab - 타임어택 면접 모드
# 제한 시간 내 빠르게 답변하는 훈련

import os
import sys
import time
import random
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AIRLINES
from sidebar_common import init_page, end_page
from logging_config import get_logger

logger = get_logger(__name__)

# OpenAI API
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False

# =====================
# 타임어택 설정
# =====================

TIME_MODES = {
    "easy": {
        "name": "연습 모드",
        "time_per_question": 60,
        "description": "질문당 60초, 여유롭게 연습",
        "color": "#10b981",
    },
    "normal": {
        "name": "실전 모드",
        "time_per_question": 45,
        "description": "질문당 45초, 실제 면접 속도",
        "color": "#3b82f6",
    },
    "hard": {
        "name": "도전 모드",
        "time_per_question": 30,
        "description": "질문당 30초, 순발력 테스트",
        "color": "#f59e0b",
    },
    "extreme": {
        "name": "극한 모드",
        "time_per_question": 20,
        "description": "질문당 20초, 한계 돌파",
        "color": "#ef4444",
    },
}

# 빠른 답변용 질문 (짧게 답변 가능한 것들)
TIMEATTACK_QUESTIONS = [
    # 자기소개 계열
    "자기소개를 한 문장으로 해주세요.",
    "본인의 강점 3가지를 말해주세요.",
    "본인의 약점 1가지와 극복 방법은?",
    "지원 동기를 한 문장으로 말해주세요.",

    # 가치관 계열
    "승무원에게 가장 중요한 자질은?",
    "서비스란 무엇이라고 생각하시나요?",
    "팀워크가 중요한 이유는?",
    "안전이 왜 최우선인가요?",

    # 상황 대처 계열
    "승객이 화를 내면 첫 마디는?",
    "동료와 의견 충돌 시 어떻게?",
    "긴급 상황 발생 시 첫 행동은?",
    "무리한 요청에 어떻게 거절하나요?",

    # 항공사 계열
    "저희 항공사를 선택한 이유는?",
    "저희 항공사의 강점은 무엇인가요?",
    "경쟁사와의 차이점은?",

    # 개인 경험 계열
    "가장 힘들었던 서비스 경험은?",
    "성공적으로 문제를 해결한 경험은?",
    "팀에서 본인의 역할은 주로 뭔가요?",
    "스트레스 해소 방법은?",

    # 미래 계열
    "5년 후 목표는?",
    "승무원이 안 되면 어떻게 할 건가요?",
    "입사 후 첫 목표는?",
]


def get_timer_component(time_limit: int, question_id: str):
    """실시간 타이머 컴포넌트"""
    return f"""
    <div id="timer-{question_id}" style="
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        padding: 20px;
        border-radius: 12px;
        background: linear-gradient(135deg, #1e3a5f, #3b82f6);
        color: white;
        margin: 20px 0;
    ">
        <div id="time-display-{question_id}">{time_limit}</div>
        <div style="font-size: 0.9rem; opacity: 0.8;">초 남음</div>
    </div>

    <script>
        (function() {{
            let timeLeft = {time_limit};
            const display = document.getElementById('time-display-{question_id}');
            const container = document.getElementById('timer-{question_id}');

            const timer = setInterval(function() {{
                timeLeft--;
                display.textContent = timeLeft;

                // 색상 변경
                if (timeLeft <= 10) {{
                    container.style.background = 'linear-gradient(135deg, #dc2626, #ef4444)';
                    container.style.animation = 'pulse 0.5s infinite';
                }} else if (timeLeft <= 20) {{
                    container.style.background = 'linear-gradient(135deg, #f59e0b, #fbbf24)';
                }}

                if (timeLeft <= 0) {{
                    clearInterval(timer);
                    display.textContent = "시간 초과!";
                }}
            }}, 1000);
        }})();
    </script>

    <style>
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
        }}
    </style>
    """


def evaluate_quick_answer(question: str, answer: str, time_taken: float, time_limit: int) -> dict:
    """빠른 답변 평가"""
    if not API_AVAILABLE:
        # 기본 평가
        word_count = len(answer.split())
        time_score = max(0, 100 - int((time_taken / time_limit) * 50))

        return {
            "content_score": 70,
            "conciseness_score": min(100, word_count * 5),
            "time_score": time_score,
            "feedback": "API 없이 기본 평가를 제공합니다.",
            "time_taken": time_taken,
        }

    system_prompt = """당신은 면접 답변 평가 전문가입니다.
타임어택 모드에서의 빠른 답변을 평가해주세요.

평가 기준:
1. 내용 점수 (0-100): 질문에 적절히 답변했는가
2. 간결성 점수 (0-100): 핵심만 간결하게 전달했는가
3. 시간 점수 (0-100): 제한 시간 대비 적절한 속도인가

JSON 형식으로 응답:
{
    "content_score": 점수,
    "conciseness_score": 점수,
    "time_score": 점수,
    "feedback": "한 줄 피드백",
    "better_answer": "더 나은 답변 예시 (1-2문장)"
}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"질문: {question}\n답변: {answer}\n소요시간: {time_taken:.1f}초 (제한: {time_limit}초)"}
            ],
            temperature=0.3,
            max_tokens=300
        )

        import json
        result = json.loads(response.choices[0].message.content)
        result["time_taken"] = time_taken
        return result
    except Exception as e:
        logger.error(f"타임어택 평가 실패: {e}")
        return {
            "content_score": 70,
            "conciseness_score": 70,
            "time_score": 70,
            "feedback": "평가 중 오류가 발생했습니다.",
            "time_taken": time_taken,
        }


def calculate_final_score(results: list) -> dict:
    """최종 점수 계산"""
    if not results:
        return {"total": 0, "rank": "F", "message": "결과 없음"}

    total_content = sum(r.get("content_score", 0) for r in results)
    total_concise = sum(r.get("conciseness_score", 0) for r in results)
    total_time = sum(r.get("time_score", 0) for r in results)

    avg_content = total_content / len(results)
    avg_concise = total_concise / len(results)
    avg_time = total_time / len(results)

    # 가중 평균 (내용 40%, 간결성 30%, 시간 30%)
    total_score = int(avg_content * 0.4 + avg_concise * 0.3 + avg_time * 0.3)

    # 완료율
    completed = sum(1 for r in results if r.get("time_taken", 999) < 999)
    completion_rate = (completed / len(results)) * 100

    # 랭크 결정
    if total_score >= 90:
        rank, message = "S", "완벽한 순발력! 실전 면접 준비 완료!"
    elif total_score >= 80:
        rank, message = "A", "훌륭해요! 빠른 상황 대처 능력이 있어요."
    elif total_score >= 70:
        rank, message = "B", "좋아요! 조금만 더 연습하면 완벽해요."
    elif total_score >= 60:
        rank, message = "C", "괜찮아요. 핵심 전달 연습이 필요해요."
    else:
        rank, message = "D", "더 연습이 필요해요. 핵심만 말하는 연습을 하세요."

    return {
        "total": total_score,
        "content_avg": int(avg_content),
        "concise_avg": int(avg_concise),
        "time_avg": int(avg_time),
        "completion_rate": int(completion_rate),
        "rank": rank,
        "message": message,
    }


# =====================
# UI
# =====================

def render_timeattack():
    """타임어택 모드 UI"""

    st.markdown("""
    <style>
    .timeattack-header {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 24px;
        text-align: center;
    }
    .timeattack-header h2 {
        margin: 0 0 8px 0;
        font-size: 1.8rem;
    }
    .mode-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 2px solid #e2e8f0;
        transition: all 0.2s;
        cursor: pointer;
    }
    .mode-card:hover {
        border-color: #3b82f6;
        transform: translateY(-2px);
    }
    .mode-card.selected {
        border-color: #3b82f6;
        background: #eff6ff;
    }
    .question-card {
        background: white;
        border-radius: 16px;
        padding: 32px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 24px 0;
    }
    .question-text {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e3a5f;
        text-align: center;
        margin-bottom: 24px;
    }
    .result-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        margin: 12px 0;
        border-left: 4px solid #3b82f6;
    }
    .rank-display {
        font-size: 5rem;
        font-weight: 800;
        text-align: center;
        margin: 24px 0;
    }
    .rank-S { color: #8b5cf6; }
    .rank-A { color: #10b981; }
    .rank-B { color: #3b82f6; }
    .rank-C { color: #f59e0b; }
    .rank-D { color: #ef4444; }
    </style>
    """, unsafe_allow_html=True)

    # 헤더
    st.markdown("""
    <div class="timeattack-header">
        <h2>타임어택 면접</h2>
        <p>제한 시간 안에 핵심만 빠르게! 순발력을 키우세요</p>
    </div>
    """, unsafe_allow_html=True)

    # 세션 상태 초기화
    if "ta_started" not in st.session_state:
        st.session_state.ta_started = False
    if "ta_results" not in st.session_state:
        st.session_state.ta_results = []
    if "ta_q_idx" not in st.session_state:
        st.session_state.ta_q_idx = 0
    if "ta_start_time" not in st.session_state:
        st.session_state.ta_start_time = None

    # 시작 전
    if not st.session_state.ta_started:
        st.markdown("### 모드 선택")

        cols = st.columns(4)
        selected_mode = st.session_state.get("ta_mode", "normal")

        for i, (mode_key, mode_info) in enumerate(TIME_MODES.items()):
            with cols[i]:
                is_selected = selected_mode == mode_key
                if st.button(
                    f"**{mode_info['name']}**\n\n{mode_info['time_per_question']}초",
                    key=f"mode_{mode_key}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    st.session_state.ta_mode = mode_key
                    st.rerun()
                st.caption(mode_info['description'])

        st.markdown("---")

        num_questions = st.slider("질문 수", 5, 15, 10, key="ta_num_q")

        mode_info = TIME_MODES[selected_mode]
        total_time = num_questions * mode_info['time_per_question']

        st.info(f"총 예상 시간: **{total_time // 60}분 {total_time % 60}초** ({num_questions}문제 × {mode_info['time_per_question']}초)")

        if st.button("타임어택 시작!", type="primary", use_container_width=True):
            st.session_state.ta_started = True
            st.session_state.ta_results = []
            st.session_state.ta_q_idx = 0
            st.session_state.ta_questions = random.sample(TIMEATTACK_QUESTIONS, num_questions)
            st.session_state.ta_start_time = None
            st.rerun()

    else:
        # 진행 중
        questions = st.session_state.ta_questions
        q_idx = st.session_state.ta_q_idx
        mode = st.session_state.ta_mode
        mode_info = TIME_MODES[mode]
        time_limit = mode_info['time_per_question']

        # 완료 체크
        if q_idx >= len(questions):
            # 결과 화면
            final = calculate_final_score(st.session_state.ta_results)

            st.markdown(f"""
            <div class="rank-display rank-{final['rank']}">{final['rank']}</div>
            """, unsafe_allow_html=True)

            st.markdown(f"### {final['message']}")

            # 점수 상세
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("종합 점수", f"{final['total']}점")
            with col2:
                st.metric("내용 평균", f"{final['content_avg']}점")
            with col3:
                st.metric("간결성 평균", f"{final['concise_avg']}점")
            with col4:
                st.metric("완료율", f"{final['completion_rate']}%")

            st.markdown("---")
            st.markdown("### 문제별 결과")

            for i, (q, r) in enumerate(zip(questions, st.session_state.ta_results)):
                with st.expander(f"Q{i+1}: {q[:30]}..."):
                    st.markdown(f"**내 답변:** {r.get('answer', 'N/A')}")
                    st.markdown(f"**소요 시간:** {r.get('time_taken', 0):.1f}초")

                    col1, col2, col3 = st.columns(3)
                    col1.metric("내용", f"{r.get('content_score', 0)}점")
                    col2.metric("간결성", f"{r.get('conciseness_score', 0)}점")
                    col3.metric("시간", f"{r.get('time_score', 0)}점")

                    if r.get('better_answer'):
                        st.info(f"**더 나은 답변:** {r['better_answer']}")

            if st.button("다시 도전", type="primary"):
                st.session_state.ta_started = False
                st.rerun()

            return

        # 현재 질문
        current_q = questions[q_idx]

        # 시작 시간 기록
        if st.session_state.ta_start_time is None:
            st.session_state.ta_start_time = time.time()

        # 진행률
        st.progress((q_idx) / len(questions))
        st.markdown(f"**문제 {q_idx + 1} / {len(questions)}**")

        # 타이머
        components.html(get_timer_component(time_limit, f"q{q_idx}"), height=150)

        # 질문
        st.markdown(f"""
        <div class="question-card">
            <div class="question-text">{current_q}</div>
        </div>
        """, unsafe_allow_html=True)

        # 답변 입력
        answer = st.text_area(
            "빠르게 답변하세요!",
            height=100,
            key=f"ta_answer_{q_idx}",
            placeholder="핵심만 간결하게..."
        )

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            if st.button("답변 제출", type="primary", use_container_width=True):
                time_taken = time.time() - st.session_state.ta_start_time

                if answer.strip():
                    # 평가
                    result = evaluate_quick_answer(current_q, answer, time_taken, time_limit)
                    result["answer"] = answer
                    st.session_state.ta_results.append(result)
                else:
                    # 시간 초과 또는 빈 답변
                    st.session_state.ta_results.append({
                        "content_score": 0,
                        "conciseness_score": 0,
                        "time_score": 0,
                        "time_taken": time_taken,
                        "answer": "(답변 없음)",
                        "feedback": "답변을 입력하지 않았습니다."
                    })

                st.session_state.ta_q_idx += 1
                st.session_state.ta_start_time = None
                st.rerun()

        with col2:
            if st.button("스킵 (0점)", use_container_width=True):
                st.session_state.ta_results.append({
                    "content_score": 0,
                    "conciseness_score": 0,
                    "time_score": 0,
                    "time_taken": 999,
                    "answer": "(스킵)",
                    "feedback": "문제를 스킵했습니다."
                })
                st.session_state.ta_q_idx += 1
                st.session_state.ta_start_time = None
                st.rerun()

        with col3:
            if st.button("중단"):
                st.session_state.ta_started = False
                st.rerun()


# 메인 실행
if __name__ == "__main__":
    render_timeattack()

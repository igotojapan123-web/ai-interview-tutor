# new_features/1_압박면접모드.py
# FlyReady Lab - 압박 면접 모드
# 실제 압박 면접 상황을 시뮬레이션하여 멘탈 훈련

import os
import sys
import time
import random
import streamlit as st

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
# 압박 면접 설정
# =====================

PRESSURE_LEVELS = {
    "mild": {
        "name": "가벼운 압박",
        "description": "약간의 추가 질문과 시간 압박",
        "interruption_chance": 0.1,
        "follow_up_chance": 0.3,
        "negative_reaction_chance": 0.1,
        "time_pressure": 45,  # 초
    },
    "moderate": {
        "name": "중간 압박",
        "description": "빈번한 꼬리질문, 무표정 반응",
        "interruption_chance": 0.2,
        "follow_up_chance": 0.5,
        "negative_reaction_chance": 0.3,
        "time_pressure": 30,
    },
    "intense": {
        "name": "강한 압박",
        "description": "끊임없는 추궁, 부정적 반응, 극도의 시간 압박",
        "interruption_chance": 0.3,
        "follow_up_chance": 0.7,
        "negative_reaction_chance": 0.5,
        "time_pressure": 20,
    },
}

# 압박 반응 템플릿
PRESSURE_REACTIONS = {
    "interruption": [
        "잠깐요, 그게 답변인가요?",
        "죄송한데, 요점만 말씀해주세요.",
        "시간이 없어요. 빨리요.",
        "그래서 결론이 뭔가요?",
        "다시 한번 말씀해주세요. 못 알아들었어요.",
    ],
    "negative": [
        "음... 그렇군요.",
        "다른 지원자들은 더 구체적으로 답변하던데요.",
        "그게 전부인가요?",
        "좀 더 깊이 있는 답변을 기대했는데요.",
        "실제 경험이 맞나요?",
    ],
    "follow_up": [
        "왜 그렇게 생각하시나요?",
        "구체적인 예시를 들어주세요.",
        "그래서 결과가 어떻게 됐나요?",
        "다른 방법은 없었나요?",
        "만약 실패했다면 어떻게 하셨을 건가요?",
        "그 경험에서 배운 점이 뭔가요?",
        "같은 상황이 다시 오면 어떻게 하시겠어요?",
    ],
    "time_pressure": [
        "시간이 얼마 안 남았어요.",
        "빨리 마무리해주세요.",
        "30초 안에 답변해주세요.",
        "다음 질문으로 넘어가야 해요.",
    ],
}

# 기본 면접 질문
PRESSURE_QUESTIONS = [
    {
        "question": "자기소개 해주세요.",
        "follow_ups": [
            "1분 안에 다시 해주세요.",
            "핵심만 세 문장으로 요약해주세요.",
            "왜 그게 중요한 건가요?",
        ]
    },
    {
        "question": "왜 승무원이 되고 싶으신가요?",
        "follow_ups": [
            "다른 서비스직도 많은데 왜 꼭 승무원인가요?",
            "승무원이 안 되면 어떻게 하실 건가요?",
            "부모님은 뭐라고 하세요?",
        ]
    },
    {
        "question": "본인의 단점이 뭔가요?",
        "follow_ups": [
            "그게 단점이라고요? 더 솔직하게 말씀해주세요.",
            "그 단점 때문에 실패한 경험이 있나요?",
            "어떻게 고치고 계신가요?",
        ]
    },
    {
        "question": "힘들었던 경험을 말씀해주세요.",
        "follow_ups": [
            "그게 정말 힘든 건가요?",
            "다른 사람들은 더 힘든 일도 겪는데요.",
            "그래서 뭘 배우셨나요?",
        ]
    },
    {
        "question": "팀에서 갈등이 생기면 어떻게 하시나요?",
        "follow_ups": [
            "상대방이 끝까지 안 들으면요?",
            "본인이 틀렸을 수도 있잖아요?",
            "실제로 그렇게 해보신 적 있어요?",
        ]
    },
    {
        "question": "왜 저희 항공사에 지원하셨나요?",
        "follow_ups": [
            "다른 항공사도 지원하셨죠?",
            "거기서 붙으면 어디 가실 건가요?",
            "저희 항공사의 단점은 뭐라고 생각하세요?",
        ]
    },
    {
        "question": "승객이 무리한 요구를 하면 어떻게 하시겠어요?",
        "follow_ups": [
            "그래도 계속 요구하면요?",
            "소리를 지르기 시작하면요?",
            "다른 승객들이 불편해하면요?",
        ]
    },
    {
        "question": "체력적으로 힘든 직업인데 괜찮으시겠어요?",
        "follow_ups": [
            "지금 운동 뭐 하세요?",
            "밤샘 근무 해보신 적 있어요?",
            "시차 적응 어떻게 하실 건가요?",
        ]
    },
]


def get_pressure_response(user_answer: str, question: str, level: str, airline: str) -> dict:
    """AI를 사용하여 압박 면접 반응 생성"""
    if not API_AVAILABLE:
        return {"type": "follow_up", "response": random.choice(PRESSURE_REACTIONS["follow_up"])}

    settings = PRESSURE_LEVELS[level]

    system_prompt = f"""당신은 {airline} 항공사의 압박 면접관입니다.
지원자의 답변을 듣고 압박 질문이나 반응을 해야 합니다.

압박 수준: {settings['name']}
특징: {settings['description']}

규칙:
1. 답변의 약점이나 모호한 부분을 파고드세요
2. 구체적인 예시나 수치를 요구하세요
3. 논리적 허점을 지적하세요
4. 하지만 인격 모독은 하지 마세요
5. 1-2문장으로 짧게 반응하세요

반응 유형:
- 꼬리질문: 더 깊이 파고드는 질문
- 의문 제기: 답변의 진위나 깊이에 의문 표시
- 시간 압박: 빨리 답변하라고 재촉
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"질문: {question}\n\n지원자 답변: {user_answer}\n\n압박 반응을 해주세요."}
            ],
            temperature=0.8,
            max_tokens=150
        )
        return {"type": "ai", "response": response.choices[0].message.content}
    except Exception as e:
        logger.error(f"압박 반응 생성 실패: {e}")
        return {"type": "follow_up", "response": random.choice(PRESSURE_REACTIONS["follow_up"])}


def evaluate_pressure_performance(answers: list, level: str) -> dict:
    """압박 면접 수행 평가"""
    if not API_AVAILABLE or not answers:
        return {
            "mental_score": 70,
            "consistency_score": 70,
            "composure_score": 70,
            "feedback": "API를 사용할 수 없어 기본 평가를 제공합니다."
        }

    answers_text = "\n\n".join([
        f"Q: {a['question']}\n압박: {a.get('pressure', 'N/A')}\nA: {a['answer']}"
        for a in answers
    ])

    system_prompt = """당신은 면접 평가 전문가입니다.
압박 면접에서 지원자의 수행을 평가해주세요.

평가 기준:
1. 멘탈 관리 (0-100): 압박에도 흔들리지 않고 답변했는가
2. 일관성 (0-100): 압박에도 답변의 핵심이 유지되었는가
3. 침착함 (0-100): 당황하지 않고 차분하게 대응했는가

JSON 형식으로 응답:
{
    "mental_score": 점수,
    "consistency_score": 점수,
    "composure_score": 점수,
    "strengths": ["강점1", "강점2"],
    "improvements": ["개선점1", "개선점2"],
    "feedback": "종합 피드백 2-3문장"
}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"압박 수준: {PRESSURE_LEVELS[level]['name']}\n\n면접 내용:\n{answers_text}"}
            ],
            temperature=0.3,
            max_tokens=500
        )

        import json
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        logger.error(f"압박 면접 평가 실패: {e}")
        return {
            "mental_score": 70,
            "consistency_score": 70,
            "composure_score": 70,
            "feedback": "평가 생성 중 오류가 발생했습니다."
        }


# =====================
# UI
# =====================

def render_pressure_interview():
    """압박 면접 모드 UI"""

    st.markdown("""
    <style>
    .pressure-header {
        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    .pressure-header h2 {
        margin: 0 0 8px 0;
        font-size: 1.5rem;
    }
    .pressure-header p {
        margin: 0;
        opacity: 0.9;
    }
    .pressure-reaction {
        background: #fef2f2;
        border-left: 4px solid #dc2626;
        padding: 16px;
        margin: 16px 0;
        border-radius: 0 8px 8px 0;
    }
    .pressure-reaction .interviewer {
        font-weight: 700;
        color: #991b1b;
        margin-bottom: 8px;
    }
    .timer-urgent {
        background: #dc2626;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 700;
        animation: pulse 1s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    .score-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
    }
    .score-value {
        font-size: 2rem;
        font-weight: 800;
        color: #1e3a5f;
    }
    .score-label {
        font-size: 0.9rem;
        color: #64748b;
    }
    </style>
    """, unsafe_allow_html=True)

    # 헤더
    st.markdown("""
    <div class="pressure-header">
        <h2>압박 면접 모드</h2>
        <p>실제 압박 면접 상황을 경험하고 멘탈을 훈련하세요</p>
    </div>
    """, unsafe_allow_html=True)

    # 세션 상태 초기화
    if "pressure_started" not in st.session_state:
        st.session_state.pressure_started = False
    if "pressure_answers" not in st.session_state:
        st.session_state.pressure_answers = []
    if "pressure_q_idx" not in st.session_state:
        st.session_state.pressure_q_idx = 0
    if "pressure_phase" not in st.session_state:
        st.session_state.pressure_phase = "question"  # question, pressure, next

    # 면접 시작 전
    if not st.session_state.pressure_started:
        st.warning("이 모드는 실제 압박 면접을 시뮬레이션합니다. 심리적으로 준비되셨을 때 시작하세요.")

        col1, col2 = st.columns(2)

        with col1:
            airline = st.selectbox(
                "지원 항공사",
                AIRLINES,
                key="pressure_airline"
            )

        with col2:
            level = st.selectbox(
                "압박 강도",
                list(PRESSURE_LEVELS.keys()),
                format_func=lambda x: f"{PRESSURE_LEVELS[x]['name']} - {PRESSURE_LEVELS[x]['description']}",
                key="pressure_level"
            )

        num_questions = st.slider("질문 수", 3, 8, 5, key="pressure_num_q")

        st.markdown("---")

        # 압박 강도 설명
        selected_level = PRESSURE_LEVELS[level]
        st.markdown(f"""
        ### 선택한 압박 강도: {selected_level['name']}

        | 항목 | 설정 |
        |------|------|
        | 답변 시간 제한 | **{selected_level['time_pressure']}초** |
        | 끼어들기 확률 | {int(selected_level['interruption_chance']*100)}% |
        | 꼬리질문 확률 | {int(selected_level['follow_up_chance']*100)}% |
        | 부정적 반응 확률 | {int(selected_level['negative_reaction_chance']*100)}% |
        """)

        if st.button("압박 면접 시작", type="primary", use_container_width=True):
            st.session_state.pressure_started = True
            st.session_state.pressure_answers = []
            st.session_state.pressure_q_idx = 0
            st.session_state.pressure_phase = "question"
            st.session_state.pressure_questions = random.sample(PRESSURE_QUESTIONS, num_questions)
            st.rerun()

    else:
        # 면접 진행 중
        questions = st.session_state.pressure_questions
        q_idx = st.session_state.pressure_q_idx
        level = st.session_state.pressure_level
        airline = st.session_state.pressure_airline
        settings = PRESSURE_LEVELS[level]

        # 면접 완료 체크
        if q_idx >= len(questions):
            # 결과 표시
            st.markdown("## 면접 완료!")

            evaluation = evaluate_pressure_performance(
                st.session_state.pressure_answers,
                level
            )

            # 점수 카드
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div class="score-card">
                    <div class="score-value">{evaluation.get('mental_score', 0)}</div>
                    <div class="score-label">멘탈 관리</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="score-card">
                    <div class="score-value">{evaluation.get('consistency_score', 0)}</div>
                    <div class="score-label">일관성</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="score-card">
                    <div class="score-value">{evaluation.get('composure_score', 0)}</div>
                    <div class="score-label">침착함</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # 피드백
            st.markdown("### 종합 피드백")
            st.info(evaluation.get('feedback', ''))

            if evaluation.get('strengths'):
                st.markdown("**강점:**")
                for s in evaluation['strengths']:
                    st.markdown(f"- {s}")

            if evaluation.get('improvements'):
                st.markdown("**개선점:**")
                for i in evaluation['improvements']:
                    st.markdown(f"- {i}")

            if st.button("다시 시작", type="primary"):
                st.session_state.pressure_started = False
                st.rerun()

            return

        # 현재 질문
        current_q = questions[q_idx]

        # 진행률
        st.progress((q_idx) / len(questions))
        st.markdown(f"**질문 {q_idx + 1} / {len(questions)}**")

        # 타이머 표시
        st.markdown(f"""
        <div style="text-align: right;">
            <span class="timer-urgent">제한 시간: {settings['time_pressure']}초</span>
        </div>
        """, unsafe_allow_html=True)

        # 질문 표시
        st.markdown(f"### {current_q['question']}")

        # 이전 압박 반응 표시
        if st.session_state.pressure_phase == "pressure" and st.session_state.get("last_pressure"):
            st.markdown(f"""
            <div class="pressure-reaction">
                <div class="interviewer">면접관:</div>
                <div>{st.session_state.last_pressure}</div>
            </div>
            """, unsafe_allow_html=True)

        # 답변 입력
        answer = st.text_area(
            "답변을 입력하세요",
            height=150,
            key=f"pressure_answer_{q_idx}_{st.session_state.pressure_phase}",
            placeholder="압박에 흔들리지 말고 침착하게 답변하세요..."
        )

        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button("답변 제출", type="primary", use_container_width=True):
                if answer.strip():
                    # 압박 반응 결정
                    if st.session_state.pressure_phase == "question":
                        # 첫 답변 후 압박할지 결정
                        if random.random() < settings['follow_up_chance']:
                            # 압박 반응 생성
                            pressure = get_pressure_response(answer, current_q['question'], level, airline)
                            st.session_state.last_pressure = pressure['response']
                            st.session_state.pressure_phase = "pressure"
                            st.session_state.first_answer = answer
                            st.rerun()
                        else:
                            # 바로 다음 질문
                            st.session_state.pressure_answers.append({
                                "question": current_q['question'],
                                "answer": answer,
                                "pressure": None
                            })
                            st.session_state.pressure_q_idx += 1
                            st.session_state.pressure_phase = "question"
                            st.rerun()
                    else:
                        # 압박 후 답변 저장
                        st.session_state.pressure_answers.append({
                            "question": current_q['question'],
                            "answer": f"{st.session_state.first_answer}\n\n[압박 후 추가 답변]\n{answer}",
                            "pressure": st.session_state.last_pressure
                        })
                        st.session_state.pressure_q_idx += 1
                        st.session_state.pressure_phase = "question"
                        st.session_state.last_pressure = None
                        st.rerun()
                else:
                    st.warning("답변을 입력해주세요.")

        with col2:
            if st.button("면접 중단"):
                st.session_state.pressure_started = False
                st.rerun()


# 메인 실행
if __name__ == "__main__":
    # 페이지 초기화 (실제 배포시 활성화)
    # init_page(title="압박 면접 모드", current_page="압박면접", wide_layout=True)
    render_pressure_interview()
    # end_page()

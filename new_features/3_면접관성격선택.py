# new_features/3_면접관성격선택.py
# FlyReady Lab - 면접관 성격/스타일 선택
# 다양한 면접관 유형을 경험할 수 있는 기능

import os
import sys
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
# 면접관 성격 유형
# =====================

INTERVIEWER_TYPES = {
    "friendly": {
        "name": "친절한 면접관",
        "icon": "😊",
        "description": "따뜻하고 격려하는 분위기, 초보자에게 추천",
        "difficulty": "초급",
        "color": "#10b981",
        "traits": [
            "긍정적인 반응을 자주 보임",
            "답변을 잘 들어줌",
            "추가 설명 기회를 줌",
            "실수해도 부드럽게 넘어감",
        ],
        "system_prompt": """당신은 친절하고 따뜻한 항공사 면접관입니다.

성격 특성:
- 지원자의 답변에 긍정적으로 반응합니다
- "좋은 답변이네요", "잘 말씀해주셨어요" 같은 격려를 합니다
- 긴장한 지원자를 편안하게 만들어줍니다
- 답변이 부족하면 부드럽게 추가 질문으로 유도합니다
- 미소를 짓는 듯한 따뜻한 말투를 사용합니다

금지사항:
- 날카롭거나 비판적인 말투 사용 금지
- 지원자를 당황하게 하는 질문 금지
"""
    },
    "neutral": {
        "name": "무표정 면접관",
        "icon": "😐",
        "description": "감정 표현 없이 담담하게 진행, 중급자에게 추천",
        "difficulty": "중급",
        "color": "#64748b",
        "traits": [
            "리액션이 거의 없음",
            "표정 변화 없이 질문만 함",
            "답변에 대한 평가를 드러내지 않음",
            "비즈니스적이고 형식적인 진행",
        ],
        "system_prompt": """당신은 무표정하고 담담한 항공사 면접관입니다.

성격 특성:
- 감정을 드러내지 않고 담담하게 질문합니다
- "네", "다음 질문입니다" 같이 짧게 반응합니다
- 답변이 좋든 나쁘든 표정/반응 변화가 없습니다
- 형식적이고 비즈니스적인 말투를 사용합니다
- 추가 설명 없이 다음 질문으로 넘어갑니다

금지사항:
- 긍정적이거나 부정적인 감정 표현 금지
- "좋네요", "아쉽네요" 같은 평가 금지
"""
    },
    "strict": {
        "name": "엄격한 면접관",
        "icon": "😤",
        "description": "깐깐하고 꼼꼼하게 검증, 고급자에게 추천",
        "difficulty": "고급",
        "color": "#f59e0b",
        "traits": [
            "답변의 논리적 허점을 지적",
            "구체적인 예시와 수치를 요구",
            "애매한 답변은 재질문",
            "높은 기준으로 평가",
        ],
        "system_prompt": """당신은 엄격하고 꼼꼼한 항공사 면접관입니다.

성격 특성:
- 답변의 논리적 허점을 바로 지적합니다
- "구체적으로 말씀해주세요", "예시를 들어주세요" 자주 요구
- 애매한 답변에는 "그게 무슨 뜻인가요?" 재질문
- 높은 기준으로 평가하며 쉽게 만족하지 않습니다
- 단호하고 직설적인 말투를 사용합니다

금지사항:
- 인격 모독이나 무례한 말 금지
- 지원자를 무시하는 태도 금지
"""
    },
    "pressure": {
        "name": "압박 면접관",
        "icon": "😠",
        "description": "강한 압박과 도전적 질문, 멘탈 훈련용",
        "difficulty": "최고급",
        "color": "#ef4444",
        "traits": [
            "답변 중간에 끼어듦",
            "부정적 반응을 보임",
            "꼬리에 꼬리를 무는 질문",
            "시간 압박을 줌",
        ],
        "system_prompt": """당신은 압박을 주는 항공사 면접관입니다.

성격 특성:
- 지원자의 답변에 의문을 제기합니다
- "정말요?", "그게 답변인가요?" 같은 반응
- 답변의 약점을 파고드는 꼬리질문을 합니다
- 시간이 없다며 빨리 답변하라고 재촉합니다
- 때로는 한숨을 쉬거나 고개를 젓는 듯한 반응

금지사항:
- 인격 모독이나 비하 발언 금지
- 성별/나이/외모 관련 차별 금지
- 실제 면접에서 불법인 질문 금지
"""
    },
    "foreign": {
        "name": "외국인 면접관",
        "icon": "🌍",
        "description": "영어로 진행, 외항사 준비용",
        "difficulty": "특수",
        "color": "#8b5cf6",
        "traits": [
            "영어로만 대화",
            "문화적 차이를 고려한 질문",
            "글로벌 마인드 평가",
            "영어 표현력 중시",
        ],
        "system_prompt": """You are a foreign airline interviewer conducting the interview in English.

Personality traits:
- Conduct the entire interview in English
- Be professional but friendly
- Ask about international experience and global mindset
- Evaluate English communication skills
- Ask follow-up questions in English

Guidelines:
- Speak naturally, not too formal
- If the candidate struggles with English, give them a chance to try again
- Focus on communication ability, not perfect grammar
"""
    },
}

# 공통 면접 질문
INTERVIEW_QUESTIONS = [
    "Please introduce yourself.",
    "Why do you want to be a flight attendant?",
    "Why did you apply to our airline?",
    "What are your strengths and weaknesses?",
    "Tell me about a time you dealt with a difficult customer.",
    "How do you handle stress?",
    "Where do you see yourself in 5 years?",
    "What does good service mean to you?",
    "How would you handle a conflict with a colleague?",
    "Why should we hire you?",
]

INTERVIEW_QUESTIONS_KR = [
    "자기소개를 해주세요.",
    "왜 승무원이 되고 싶으신가요?",
    "왜 저희 항공사에 지원하셨나요?",
    "본인의 강점과 약점을 말씀해주세요.",
    "어려운 고객을 응대한 경험을 말씀해주세요.",
    "스트레스를 어떻게 관리하시나요?",
    "5년 후 본인의 모습은 어떨 것 같나요?",
    "좋은 서비스란 무엇이라고 생각하시나요?",
    "동료와 갈등이 생기면 어떻게 해결하시나요?",
    "왜 저희가 당신을 뽑아야 하나요?",
]


def generate_interviewer_response(
    interviewer_type: str,
    question: str,
    user_answer: str,
    airline: str = "대한항공"
) -> str:
    """면접관 유형에 맞는 반응 생성"""
    if not API_AVAILABLE:
        return "네, 알겠습니다. 다음 질문으로 넘어가겠습니다."

    interviewer = INTERVIEWER_TYPES[interviewer_type]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": interviewer["system_prompt"]},
                {"role": "user", "content": f"""
항공사: {airline}
질문: {question}
지원자 답변: {user_answer}

위 답변에 대해 당신의 성격에 맞게 반응해주세요. 1-2문장으로 짧게.
그 후 자연스럽게 다음 질문이나 꼬리질문을 해주세요.
"""}
            ],
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"면접관 반응 생성 실패: {e}")
        return "네, 알겠습니다. 다음 질문입니다."


def evaluate_interview(interviewer_type: str, qa_pairs: list, airline: str) -> dict:
    """면접 종합 평가"""
    if not API_AVAILABLE or not qa_pairs:
        return {
            "total_score": 70,
            "feedback": "API를 사용할 수 없어 기본 평가를 제공합니다.",
            "strengths": ["답변을 완료함"],
            "improvements": ["더 구체적인 예시 필요"],
        }

    interviewer = INTERVIEWER_TYPES[interviewer_type]

    qa_text = "\n\n".join([
        f"Q: {qa['question']}\nA: {qa['answer']}"
        for qa in qa_pairs
    ])

    system_prompt = f"""당신은 {airline} 항공사 면접 평가관입니다.
면접관 유형 '{interviewer['name']}'의 관점에서 지원자를 평가해주세요.

JSON 형식으로 응답:
{{
    "total_score": 0-100,
    "communication": 0-100,
    "content": 0-100,
    "attitude": 0-100,
    "strengths": ["강점1", "강점2"],
    "improvements": ["개선점1", "개선점2"],
    "feedback": "종합 피드백 2-3문장",
    "hiring_recommendation": "추천/보류/미추천"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"면접 내용:\n{qa_text}"}
            ],
            temperature=0.3,
            max_tokens=500
        )

        import json
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"면접 평가 실패: {e}")
        return {
            "total_score": 70,
            "feedback": "평가 생성 중 오류가 발생했습니다.",
        }


# =====================
# UI
# =====================

def render_interviewer_selection():
    """면접관 성격 선택 UI"""

    st.markdown("""
    <style>
    .interviewer-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #3b82f6 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    .interviewer-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        border: 2px solid #e2e8f0;
        transition: all 0.2s;
        cursor: pointer;
    }
    .interviewer-card:hover {
        border-color: #3b82f6;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .interviewer-card.selected {
        border-color: #3b82f6;
        background: #eff6ff;
    }
    .interviewer-icon {
        font-size: 3rem;
        margin-bottom: 12px;
    }
    .interviewer-name {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1e3a5f;
    }
    .interviewer-desc {
        font-size: 0.9rem;
        color: #64748b;
        margin: 8px 0;
    }
    .difficulty-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .trait-list {
        font-size: 0.85rem;
        color: #475569;
        margin-top: 12px;
    }
    .chat-bubble {
        padding: 16px;
        border-radius: 12px;
        margin: 12px 0;
        max-width: 80%;
    }
    .chat-interviewer {
        background: #f1f5f9;
        border-bottom-left-radius: 4px;
    }
    .chat-user {
        background: #3b82f6;
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }
    </style>
    """, unsafe_allow_html=True)

    # 헤더
    st.markdown("""
    <div class="interviewer-header">
        <h2 style="margin:0 0 8px 0;">면접관 스타일 선택</h2>
        <p style="margin:0;opacity:0.9;">다양한 유형의 면접관을 경험해보세요</p>
    </div>
    """, unsafe_allow_html=True)

    # 세션 상태
    if "iv_started" not in st.session_state:
        st.session_state.iv_started = False
    if "iv_qa_pairs" not in st.session_state:
        st.session_state.iv_qa_pairs = []
    if "iv_q_idx" not in st.session_state:
        st.session_state.iv_q_idx = 0
    if "iv_chat_history" not in st.session_state:
        st.session_state.iv_chat_history = []

    # 면접 시작 전
    if not st.session_state.iv_started:
        st.markdown("### 면접관 유형을 선택하세요")

        # 면접관 카드들
        cols = st.columns(3)

        for i, (type_key, type_info) in enumerate(INTERVIEWER_TYPES.items()):
            with cols[i % 3]:
                selected = st.session_state.get("iv_type") == type_key

                if st.button(
                    f"{type_info['icon']} {type_info['name']}",
                    key=f"select_{type_key}",
                    use_container_width=True,
                    type="primary" if selected else "secondary"
                ):
                    st.session_state.iv_type = type_key
                    st.rerun()

                st.caption(type_info['description'])
                st.markdown(f"난이도: **{type_info['difficulty']}**")

        st.markdown("---")

        # 선택된 면접관 상세 정보
        if st.session_state.get("iv_type"):
            selected_type = INTERVIEWER_TYPES[st.session_state.iv_type]

            st.markdown(f"### {selected_type['icon']} {selected_type['name']} 상세")

            st.markdown("**특징:**")
            for trait in selected_type['traits']:
                st.markdown(f"- {trait}")

        # 항공사 선택
        col1, col2 = st.columns(2)
        with col1:
            airline = st.selectbox("지원 항공사", AIRLINES, key="iv_airline")
        with col2:
            num_q = st.slider("질문 수", 3, 10, 5, key="iv_num_q")

        if st.button("면접 시작", type="primary", use_container_width=True,
                    disabled=not st.session_state.get("iv_type")):
            st.session_state.iv_started = True
            st.session_state.iv_qa_pairs = []
            st.session_state.iv_q_idx = 0
            st.session_state.iv_chat_history = []

            # 질문 선택 (영어 면접관이면 영어 질문)
            if st.session_state.iv_type == "foreign":
                st.session_state.iv_questions = random.sample(INTERVIEW_QUESTIONS, num_q)
            else:
                st.session_state.iv_questions = random.sample(INTERVIEW_QUESTIONS_KR, num_q)

            st.rerun()

    else:
        # 면접 진행 중
        interviewer_type = st.session_state.iv_type
        interviewer = INTERVIEWER_TYPES[interviewer_type]
        questions = st.session_state.iv_questions
        q_idx = st.session_state.iv_q_idx
        airline = st.session_state.iv_airline

        # 완료 체크
        if q_idx >= len(questions):
            st.markdown("## 면접 완료!")

            # 평가
            evaluation = evaluate_interview(
                interviewer_type,
                st.session_state.iv_qa_pairs,
                airline
            )

            # 점수 표시
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("종합 점수", f"{evaluation.get('total_score', 0)}점")
            with col2:
                st.metric("커뮤니케이션", f"{evaluation.get('communication', 0)}점")
            with col3:
                st.metric("내용", f"{evaluation.get('content', 0)}점")
            with col4:
                st.metric("태도", f"{evaluation.get('attitude', 0)}점")

            # 채용 추천
            rec = evaluation.get('hiring_recommendation', '보류')
            rec_color = {"추천": "#10b981", "보류": "#f59e0b", "미추천": "#ef4444"}.get(rec, "#64748b")
            st.markdown(f"### 채용 추천: <span style='color:{rec_color}'>{rec}</span>", unsafe_allow_html=True)

            # 피드백
            st.markdown("### 종합 피드백")
            st.info(evaluation.get('feedback', ''))

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**강점**")
                for s in evaluation.get('strengths', []):
                    st.markdown(f"✓ {s}")
            with col2:
                st.markdown("**개선점**")
                for i in evaluation.get('improvements', []):
                    st.markdown(f"△ {i}")

            if st.button("다시 시작", type="primary"):
                st.session_state.iv_started = False
                st.rerun()

            return

        # 현재 진행
        current_q = questions[q_idx]

        # 면접관 정보 표시
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
            <span style="font-size:2rem;">{interviewer['icon']}</span>
            <div>
                <div style="font-weight:700;color:#1e3a5f;">{interviewer['name']}</div>
                <div style="font-size:0.85rem;color:#64748b;">{airline} 면접관</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 진행률
        st.progress((q_idx) / len(questions))
        st.caption(f"질문 {q_idx + 1} / {len(questions)}")

        # 채팅 히스토리 표시
        for chat in st.session_state.iv_chat_history:
            if chat['role'] == 'interviewer':
                st.markdown(f"""
                <div class="chat-bubble chat-interviewer">
                    <strong>면접관:</strong> {chat['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-bubble chat-user">
                    {chat['content']}
                </div>
                """, unsafe_allow_html=True)

        # 현재 질문 (히스토리에 없으면 추가)
        if not st.session_state.iv_chat_history or \
           st.session_state.iv_chat_history[-1]['content'] != current_q:
            st.markdown(f"""
            <div class="chat-bubble chat-interviewer">
                <strong>면접관:</strong> {current_q}
            </div>
            """, unsafe_allow_html=True)

        # 답변 입력
        answer = st.text_area(
            "답변을 입력하세요",
            height=120,
            key=f"iv_answer_{q_idx}",
            placeholder="면접관의 성격에 맞춰 답변해보세요..."
        )

        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button("답변 제출", type="primary", use_container_width=True):
                if answer.strip():
                    # 채팅 히스토리에 추가
                    st.session_state.iv_chat_history.append({
                        "role": "interviewer",
                        "content": current_q
                    })
                    st.session_state.iv_chat_history.append({
                        "role": "user",
                        "content": answer
                    })

                    # QA 쌍 저장
                    st.session_state.iv_qa_pairs.append({
                        "question": current_q,
                        "answer": answer
                    })

                    # 면접관 반응 생성 (다음 질문 전환)
                    if q_idx < len(questions) - 1:
                        response = generate_interviewer_response(
                            interviewer_type, current_q, answer, airline
                        )
                        st.session_state.iv_chat_history.append({
                            "role": "interviewer",
                            "content": response
                        })

                    st.session_state.iv_q_idx += 1
                    st.rerun()
                else:
                    st.warning("답변을 입력해주세요.")

        with col2:
            if st.button("면접 중단"):
                st.session_state.iv_started = False
                st.rerun()


# 메인 실행
if __name__ == "__main__":
    render_interviewer_selection()

# pages/2_영어면접.py
# 영어 면접 연습 시스템 - 음성 녹음 및 리스닝 기능 포함

import os
import random
import streamlit as st
import requests

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import LLM_MODEL_NAME, LLM_API_URL, LLM_TIMEOUT_SEC
from english_interview_data import (
    ENGLISH_QUESTIONS, ADVANCED_QUESTIONS, ENGLISH_INTERVIEW_TIPS,
    get_questions_by_category, get_all_categories, get_random_questions
)

# 음성 유틸리티 import
try:
    from voice_utils import (
        generate_tts_audio, get_audio_player_html, transcribe_audio, get_loud_audio_component
    )
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# 점수 자동 저장 유틸리티
try:
    from score_utils import save_practice_score, parse_evaluation_score
    SCORE_UTILS_AVAILABLE = True
except ImportError:
    SCORE_UTILS_AVAILABLE = False

st.set_page_config(
    page_title="영어면접 연습",
    page_icon="🌍",
    layout="wide"
)

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="영어면접")
except ImportError:
    pass

# 사용량 제한 시스템
try:
    from usage_limiter import check_and_use, get_remaining
    USAGE_LIMITER_AVAILABLE = True
except ImportError:
    USAGE_LIMITER_AVAILABLE = False

# =====================
# 세션 상태 초기화
# =====================

defaults = {
    "eng_mode": None,  # "practice" or "mock"
    "eng_questions": [],
    "eng_current_idx": 0,
    "eng_answers": {},
    "eng_feedback": {},
    "eng_completed": False,
    "eng_show_text": {},  # 질문 텍스트 표시 여부
    "eng_audio_played": {},  # 오디오 재생 여부
    "eng_listening_mode": True,  # 리스닝 모드 (음성 먼저)
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =====================
# LLM 함수
# =====================

def get_api_key():
    return (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENAI_APIKEY")
        or os.getenv("OPENAI_KEY")
        or ""
    )


def evaluate_english_answer(question: str, answer: str, key_points: list = None) -> dict:
    """영어 답변 평가"""
    api_key = get_api_key()
    if not api_key:
        return {"error": "API 키 없음"}

    key_points_text = ", ".join(key_points) if key_points else "N/A"

    system_prompt = """You are a STRICT airline interview examiner evaluating a candidate's English response.
You must be very strict about grammar and spelling errors.
Provide feedback in Korean. Be honest and direct - do not give undeserved high scores."""

    user_prompt = f"""## Interview Question
{question}

## Candidate's Answer
{answer}

## Key Points to Cover
{key_points_text}

## STRICT Evaluation Criteria (엄격한 평가 기준)

### 점수 산정 기준 (10점 만점)
- **문법/철자 오류 1개당 -1점** (기본 점수 10점에서 차감)
- 내용이 부실하면 추가 -1~2점
- 답변이 너무 짧으면 추가 -1점
- 질문과 관련 없는 답변이면 추가 -2점

### 엄격하게 체크해야 할 항목
1. **Grammar (문법)** - 시제, 주어-동사 일치, 관사(a/an/the), 전치사 오류 모두 체크
2. **Spelling (철자)** - 모든 철자 오류 체크
3. **Sentence Structure (문장 구조)** - 불완전한 문장, 어색한 어순
4. **Vocabulary (어휘)** - 부적절한 단어 사용

### 점수 가이드
- 10점: 문법/철자 오류 0개, 내용 우수
- 8-9점: 문법/철자 오류 1-2개, 내용 양호
- 6-7점: 문법/철자 오류 3-4개, 내용 보통
- 4-5점: 문법/철자 오류 5개 이상, 내용 부실
- 3점 이하: 심각한 오류 다수, 의사소통 불가 수준

## Output Format (Korean)
### 점수: X/10

### 발견된 오류 목록
1. (오류 원문) → (수정) : [문법/철자/어휘]
2. ...

### 문법 & 어휘 평가
- (구체적 평가)

### 내용 & 구성 평가
- (구체적 평가)

### 개선할 점
- (구체적으로, 친절하게)

### 수정된 모범 답변
"(오류를 모두 수정한 영어 답변)"
"""

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": LLM_MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.5,
            "max_tokens": 800,
        }

        r = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=LLM_TIMEOUT_SEC)
        r.raise_for_status()
        resp = r.json()

        choices = resp.get("choices", [])
        if choices:
            return {"result": choices[0].get("message", {}).get("content", "").strip()}
        return {"error": "평가 생성 실패"}

    except Exception as e:
        return {"error": str(e)}


def generate_followup_question(original_question: str, user_answer: str) -> str:
    """꼬리질문 생성"""
    api_key = get_api_key()
    if not api_key:
        return None

    system_prompt = """You are an airline interviewer. Based on the candidate's answer,
generate one follow-up question in English. Keep it natural and conversational.
Output only the question, nothing else."""

    user_prompt = f"""Original Question: {original_question}
Candidate's Answer: {user_answer}

Generate a natural follow-up question:"""

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": LLM_MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 100,
        }

        r = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=LLM_TIMEOUT_SEC)
        r.raise_for_status()
        resp = r.json()

        choices = resp.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()
        return None

    except Exception:
        return None


# =====================
# UI
# =====================

st.title("🌍 영어면접 연습")
st.caption("항공사 영어면접을 준비하세요. 질문에 영어로 답변하고 피드백을 받으세요.")

# 모드 선택
if st.session_state.eng_mode is None:
    st.subheader("연습 모드 선택")

    # 남은 사용량 표시
    if USAGE_LIMITER_AVAILABLE:
        remaining = get_remaining("영어면접")
        st.markdown(f"오늘 남은 횟수: **{remaining}회**")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📚 카테고리별 연습")
        st.write("원하는 카테고리의 질문을 선택해서 연습합니다.")
        st.write("- 모범 답변 참고 가능")
        st.write("- 질문별 즉시 피드백")
        if st.button("카테고리별 연습 시작", use_container_width=True, type="primary"):
            if USAGE_LIMITER_AVAILABLE and not check_and_use("영어면접"):
                st.stop()
            st.session_state.eng_mode = "practice"
            st.rerun()

    with col2:
        st.markdown("### 🎯 모의면접")
        st.write("실제 면접처럼 랜덤 질문 5개를 답변합니다.")
        st.write("- 모범 답변 숨김")
        st.write("- 전체 완료 후 종합 피드백")

        # 리스닝 모드 옵션
        if VOICE_AVAILABLE:
            listening_mode = st.checkbox(
                "🎧 리스닝 모드 (질문을 음성으로 먼저 듣기)",
                value=True,
                help="질문이 영어 음성으로 먼저 재생됩니다. 텍스트를 보려면 버튼을 클릭하세요."
            )
            st.session_state.eng_listening_mode = listening_mode

        if st.button("모의면접 시작", use_container_width=True):
            if USAGE_LIMITER_AVAILABLE and not check_and_use("영어면접"):
                st.stop()
            st.session_state.eng_mode = "mock"
            st.session_state.eng_questions = get_random_questions(5)
            st.session_state.eng_current_idx = 0
            st.session_state.eng_answers = {}
            st.session_state.eng_feedback = {}
            st.session_state.eng_completed = False
            st.session_state.eng_show_text = {}
            st.session_state.eng_audio_played = {}
            st.rerun()

    # 면접 팁
    st.divider()
    with st.expander("💡 영어면접 Tips", expanded=False):
        for tip in ENGLISH_INTERVIEW_TIPS:
            st.write(f"• {tip}")

# 카테고리별 연습 모드
elif st.session_state.eng_mode == "practice":
    # 뒤로가기
    if st.button("← 모드 선택으로"):
        st.session_state.eng_mode = None
        st.rerun()

    st.subheader("카테고리별 연습")

    # 카테고리 선택
    categories = get_all_categories()
    cat_names = [f"{c['name']} ({c['name_en']})" for c in categories]
    cat_keys = [c['key'] for c in categories]

    col_cat, col_mode = st.columns([2, 1])
    with col_cat:
        selected_cat_idx = st.selectbox(
            "카테고리 선택",
            range(len(cat_names)),
            format_func=lambda x: cat_names[x]
        )
    selected_cat_key = cat_keys[selected_cat_idx]

    # 리스닝 모드 옵션
    with col_mode:
        if VOICE_AVAILABLE:
            practice_listening = st.checkbox(
                "🎧 리스닝 모드",
                value=True,  # 기본값 True로 변경
                help="질문을 음성으로 먼저 듣고, 필요시 텍스트를 볼 수 있습니다."
            )
        else:
            practice_listening = False

    questions = get_questions_by_category(selected_cat_key)

    # 리스닝 모드 안내
    if practice_listening:
        st.info("🎧 **리스닝 모드**: 질문을 먼저 듣고, '텍스트 보기'를 클릭하면 영어 텍스트가 표시됩니다.")

    st.divider()

    for i, q in enumerate(questions):
        question_text = q['question']
        answer_key = f"practice_{selected_cat_key}_{i}"
        show_text_key = f"show_text_practice_{selected_cat_key}_{i}"
        transcription_key = f"transcription_{answer_key}"

        # 세션 상태 초기화
        if transcription_key not in st.session_state:
            st.session_state[transcription_key] = ""

        # 리스닝 모드면 텍스트 숨김, 아니면 표시
        show_text = not practice_listening or st.session_state.get(show_text_key, False)

        # expander 제목 (리스닝 모드면 질문 텍스트 완전히 숨김)
        if practice_listening:
            # 텍스트를 본 경우에만 질문 표시
            if st.session_state.get(show_text_key, False):
                expander_title = f"Q{i+1}: {question_text}"
            else:
                expander_title = f"🎧 Question {i+1} - 듣기"
        else:
            expander_title = f"Q{i+1}: {question_text}"

        with st.expander(expander_title, expanded=(i == 0 and not practice_listening)):

            # 리스닝 모드: 음성 먼저
            if practice_listening and VOICE_AVAILABLE:
                col_audio1, col_audio2 = st.columns([1, 1])
                with col_audio1:
                    if st.button("🔊 질문 듣기", key=f"play_practice_q_{selected_cat_key}_{i}", use_container_width=True):
                        with st.spinner("음성 생성 중..."):
                            audio = generate_tts_audio(question_text, voice="alloy", speed=0.85, use_clova=False)
                            if audio:
                                get_loud_audio_component(audio, autoplay=True, gain=5.0)
                            else:
                                st.error("음성 생성 실패")

                with col_audio2:
                    if st.button("📝 텍스트 보기", key=f"show_text_btn_{selected_cat_key}_{i}", use_container_width=True):
                        st.session_state[show_text_key] = True
                        st.rerun()

                # 텍스트 표시 (버튼 클릭 후에만)
                if st.session_state.get(show_text_key, False):
                    st.markdown(f"**🎤 {question_text}**")
                    st.caption(f"💡 힌트: {q['korean_hint']}")
                # 텍스트 보기 전에는 아무것도 표시하지 않음

            else:
                # 일반 모드: 텍스트 바로 표시
                st.caption(f"💡 힌트: {q['korean_hint']}")

                # 질문 듣기 버튼 (선택적)
                if VOICE_AVAILABLE:
                    if st.button("🔊 질문 듣기", key=f"play_q_practice_{selected_cat_key}_{i}"):
                        with st.spinner("음성 생성 중..."):
                            audio = generate_tts_audio(question_text, voice="alloy", speed=0.85, use_clova=False)
                            if audio:
                                get_loud_audio_component(audio, autoplay=True, gain=5.0)

            # 핵심 포인트
            st.markdown("**핵심 포인트:** " + ", ".join(q.get("key_points", [])))

            st.divider()

            # 답변 입력 (텍스트 또는 음성)
            answer = None

            if VOICE_AVAILABLE:
                input_mode = st.radio(
                    "답변 방식",
                    ["⌨️ 텍스트 입력", "🎤 음성 녹음"],
                    horizontal=True,
                    key=f"input_mode_practice_{selected_cat_key}_{i}"
                )

                if input_mode == "🎤 음성 녹음":
                    st.markdown("**🎤 음성으로 답변하기**")
                    st.caption("영어로 답변을 녹음하세요. 발음이 명확할수록 인식률이 높아집니다.")

                    try:
                        audio_data = st.audio_input("음성 녹음", key=f"voice_practice_{selected_cat_key}_{i}")

                        if audio_data is not None:
                            st.audio(audio_data, format="audio/wav")

                            if st.button("📤 음성 변환", key=f"submit_voice_practice_{selected_cat_key}_{i}", type="primary"):
                                with st.spinner("음성 인식 중..."):
                                    transcription = transcribe_audio(audio_data.getvalue(), language="en")
                                    if transcription and transcription.get("text"):
                                        recognized_text = transcription["text"]
                                        st.session_state[transcription_key] = recognized_text
                                    else:
                                        st.error("음성 인식 실패. 다시 시도해주세요.")

                        # 인식된 텍스트 표시 (항상 표시)
                        if st.session_state[transcription_key]:
                            st.markdown("---")
                            st.markdown("**📝 인식된 답변 (발음 확인):**")
                            st.success(st.session_state[transcription_key])
                            st.caption("위 텍스트가 실제로 말한 내용과 다르면, 발음을 더 명확히 해보세요.")
                            answer = st.session_state[transcription_key]

                    except Exception as e:
                        st.warning("음성 녹음을 사용할 수 없습니다. 텍스트로 답변해주세요.")

                    # 텍스트 폴백
                    st.markdown("---")
                    st.caption("또는 텍스트로 입력:")
                    text_answer = st.text_area(
                        "Your Answer",
                        key=f"ans_fallback_{answer_key}",
                        height=100,
                        placeholder="Type your answer in English...",
                        value=st.session_state.get(transcription_key, "")
                    )
                    if text_answer and not answer:
                        answer = text_answer
                else:
                    # 텍스트 입력
                    answer = st.text_area(
                        "Your Answer (영어로 답변하세요)",
                        key=f"ans_{answer_key}",
                        height=120,
                        placeholder="Type your answer in English..."
                    )
            else:
                # 음성 기능 없을 때
                answer = st.text_area(
                    "Your Answer (영어로 답변하세요)",
                    key=f"ans_{answer_key}",
                    height=120,
                    placeholder="Type your answer in English..."
                )

            col1, col2 = st.columns([1, 1])

            with col1:
                if st.button("피드백 받기", key=f"fb_{answer_key}", disabled=not (answer and answer.strip())):
                    with st.spinner("답변 평가 중..."):
                        feedback = evaluate_english_answer(
                            q["question"],
                            answer,
                            q.get("key_points", [])
                        )
                        st.session_state.eng_feedback[answer_key] = feedback

                        # 자동 점수 저장
                        if SCORE_UTILS_AVAILABLE and "result" in feedback:
                            parsed = parse_evaluation_score(feedback["result"], "영어면접")
                            if parsed.get("total", 0) > 0:
                                save_practice_score(
                                    practice_type="영어면접",
                                    total_score=parsed["total"],
                                    detailed_scores=parsed.get("detailed"),
                                    scenario=q.get("question", "")[:50]
                                )

            with col2:
                show_sample = st.checkbox("모범 답변 보기", key=f"sample_{answer_key}")

            # 피드백 표시
            if answer_key in st.session_state.eng_feedback:
                fb = st.session_state.eng_feedback[answer_key]
                if "error" in fb:
                    st.error(fb["error"])
                else:
                    st.markdown("---")
                    st.markdown("#### 📝 피드백")
                    st.markdown(fb.get("result", ""))

            # 모범 답변
            if show_sample:
                st.markdown("---")
                st.markdown("#### ✅ Sample Answer")
                st.info(q.get("sample_answer", ""))

                # 모범 답변 듣기
                if VOICE_AVAILABLE:
                    if st.button("🔊 모범 답변 듣기", key=f"play_sample_{selected_cat_key}_{i}"):
                        with st.spinner("음성 생성 중..."):
                            sample_audio = generate_tts_audio(q.get("sample_answer", ""), voice="alloy", speed=0.85, use_clova=False)
                            if sample_audio:
                                get_loud_audio_component(sample_audio, autoplay=True, gain=5.0)

# 모의면접 모드
elif st.session_state.eng_mode == "mock":
    if not st.session_state.eng_completed:
        # 진행 중
        current_idx = st.session_state.eng_current_idx
        total = len(st.session_state.eng_questions)

        # 진행률
        st.progress((current_idx) / total)
        st.subheader(f"Question {current_idx + 1} of {total}")

        if current_idx < total:
            q = st.session_state.eng_questions[current_idx]
            question_text = q['question']

            # =====================
            # 리스닝 모드: 음성 먼저, 텍스트는 버튼 클릭 후
            # =====================
            if st.session_state.eng_listening_mode and VOICE_AVAILABLE:
                st.markdown("### 🎧 Listen to the question")

                # 질문 음성 재생 버튼
                col_audio1, col_audio2 = st.columns([1, 1])
                with col_audio1:
                    if st.button("🔊 질문 듣기", key=f"play_q_{current_idx}", use_container_width=True):
                        with st.spinner("음성 생성 중..."):
                            # 영어 TTS (미국 원어민 발음)
                            audio = generate_tts_audio(
                                question_text,
                                voice="alloy",
                                speed=0.85,
                                use_clova=False  # 영어는 OpenAI 사용
                            )
                            if audio:
                                st.session_state.eng_audio_played[current_idx] = True
                                get_loud_audio_component(audio, autoplay=True, gain=5.0)
                            else:
                                st.error("음성 생성에 실패했습니다.")

                with col_audio2:
                    # 텍스트 보기 버튼
                    if st.button("📝 텍스트 보기", key=f"show_text_{current_idx}", use_container_width=True):
                        st.session_state.eng_show_text[current_idx] = True

                # 텍스트 표시 (버튼 클릭 후에만)
                if st.session_state.eng_show_text.get(current_idx, False):
                    st.markdown(f"### 🎤 {question_text}")
                    st.caption(f"힌트: {q['korean_hint']}")
                else:
                    st.info("질문을 먼저 듣고, 필요하면 '텍스트 보기'를 클릭하세요.")

                st.caption(f"카테고리: {q.get('category', '')}")

            else:
                # 일반 모드: 텍스트 바로 표시
                st.markdown(f"### 🎤 {question_text}")
                st.caption(f"힌트: {q['korean_hint']}")
                st.caption(f"카테고리: {q.get('category', '')}")

                # 음성 듣기 옵션 (선택적)
                if VOICE_AVAILABLE:
                    if st.button("🔊 질문 듣기", key=f"play_q_normal_{current_idx}"):
                        with st.spinner("음성 생성 중..."):
                            audio = generate_tts_audio(question_text, voice="alloy", speed=0.85, use_clova=False)
                            if audio:
                                get_loud_audio_component(audio, autoplay=True, gain=5.0)

            st.divider()

            # =====================
            # 답변 입력 (텍스트 또는 음성)
            # =====================
            answer = None
            mock_transcription_key = f"mock_transcription_{current_idx}"

            # 세션 상태 초기화
            if mock_transcription_key not in st.session_state:
                st.session_state[mock_transcription_key] = ""

            if VOICE_AVAILABLE:
                input_mode = st.radio(
                    "답변 방식",
                    ["⌨️ 텍스트", "🎤 음성"],
                    horizontal=True,
                    key=f"input_mode_{current_idx}"
                )

                if input_mode == "🎤 음성":
                    st.markdown("**🎤 음성으로 답변하기**")
                    st.caption("영어로 답변을 녹음하세요. 발음이 명확할수록 인식률이 높아집니다.")

                    try:
                        audio_data = st.audio_input("음성 녹음", key=f"voice_ans_{current_idx}")

                        if audio_data is not None:
                            st.audio(audio_data, format="audio/wav")

                            if st.button("📤 음성 변환", key=f"submit_voice_{current_idx}", type="primary"):
                                with st.spinner("음성 인식 중..."):
                                    transcription = transcribe_audio(audio_data.getvalue(), language="en")
                                    if transcription and transcription.get("text"):
                                        recognized_text = transcription["text"]
                                        st.session_state[mock_transcription_key] = recognized_text
                                    else:
                                        st.error("음성 인식에 실패했습니다. 다시 시도해주세요.")

                        # 인식된 텍스트 표시 (항상 표시)
                        if st.session_state[mock_transcription_key]:
                            st.markdown("---")
                            st.markdown("**📝 인식된 답변 (발음 확인):**")
                            st.success(st.session_state[mock_transcription_key])
                            st.caption("위 텍스트가 실제로 말한 내용과 다르면, 발음을 더 명확히 해보세요.")
                            answer = st.session_state[mock_transcription_key]

                    except Exception as e:
                        st.warning("음성 녹음을 사용할 수 없습니다. 텍스트로 답변해주세요.")

                    # 텍스트 폴백
                    st.markdown("---")
                    st.caption("또는 텍스트로 입력:")
                    text_answer = st.text_area(
                        "Your Answer",
                        key=f"mock_ans_fallback_{current_idx}",
                        height=100,
                        placeholder="Type your answer in English...",
                        value=st.session_state.get(mock_transcription_key, "")
                    )
                    if text_answer and not answer:
                        answer = text_answer
                else:
                    # 텍스트 입력
                    answer = st.text_area(
                        "Your Answer",
                        key=f"mock_ans_{current_idx}",
                        height=150,
                        placeholder="Type your answer in English..."
                    )
            else:
                # 음성 기능 없을 때
                answer = st.text_area(
                    "Your Answer",
                    key=f"mock_ans_{current_idx}",
                    height=150,
                    placeholder="Type your answer in English..."
                )

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("다음 질문 →", disabled=not (answer and answer.strip()), type="primary"):
                    # 답변 저장
                    st.session_state.eng_answers[current_idx] = {
                        "question": q["question"],
                        "answer": answer,
                        "key_points": q.get("key_points", [])
                    }

                    if current_idx + 1 >= total:
                        st.session_state.eng_completed = True
                    else:
                        st.session_state.eng_current_idx += 1
                        # 다음 질문을 위해 텍스트 표시 초기화
                        st.session_state.eng_show_text[current_idx + 1] = False

                    st.rerun()

            with col2:
                if st.button("모의면접 중단"):
                    st.session_state.eng_mode = None
                    st.session_state.eng_questions = []
                    st.session_state.eng_answers = {}
                    st.rerun()

    else:
        # 완료 - 결과 표시
        st.subheader("🎉 모의면접 완료!")

        # 전체 답변 평가
        if "mock_final_feedback" not in st.session_state:
            with st.spinner("전체 답변을 평가하고 있습니다..."):
                all_feedback = {}
                total_scores = []
                for idx, data in st.session_state.eng_answers.items():
                    fb = evaluate_english_answer(
                        data["question"],
                        data["answer"],
                        data.get("key_points", [])
                    )
                    all_feedback[idx] = fb

                    # 점수 파싱
                    if SCORE_UTILS_AVAILABLE and "result" in fb:
                        parsed = parse_evaluation_score(fb["result"], "영어면접")
                        if parsed.get("total", 0) > 0:
                            total_scores.append(parsed["total"])

                st.session_state.mock_final_feedback = all_feedback

                # 모의면접 평균 점수 저장
                if SCORE_UTILS_AVAILABLE and total_scores:
                    avg_score = sum(total_scores) / len(total_scores)
                    save_practice_score(
                        practice_type="영어면접",
                        total_score=round(avg_score),
                        detailed_scores=None,
                        scenario="모의면접 (5문항 평균)"
                    )

        # 결과 표시
        for idx, data in st.session_state.eng_answers.items():
            with st.expander(f"Q{idx+1}: {data['question']}", expanded=False):
                st.markdown("**Your Answer:**")
                st.write(data["answer"])

                st.markdown("---")
                st.markdown("**Feedback:**")
                fb = st.session_state.mock_final_feedback.get(idx, {})
                if "error" in fb:
                    st.error(fb["error"])
                else:
                    st.markdown(fb.get("result", ""))

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("다시 도전하기", use_container_width=True, type="primary"):
                st.session_state.eng_questions = get_random_questions(5)
                st.session_state.eng_current_idx = 0
                st.session_state.eng_answers = {}
                st.session_state.eng_feedback = {}
                st.session_state.eng_completed = False
                if "mock_final_feedback" in st.session_state:
                    del st.session_state.mock_final_feedback
                st.rerun()

        with col2:
            if st.button("모드 선택으로", use_container_width=True):
                st.session_state.eng_mode = None
                st.session_state.eng_questions = []
                st.session_state.eng_answers = {}
                if "mock_final_feedback" in st.session_state:
                    del st.session_state.mock_final_feedback
                st.rerun()

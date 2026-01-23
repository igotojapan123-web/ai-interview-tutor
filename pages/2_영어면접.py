# pages/2_영어면접.py
# 영어 면접 연습 시스템 - 음성 분석 및 PDF 리포트 포함

import os
import random
import streamlit as st
import requests

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import LLM_MODEL_NAME, LLM_API_URL, LLM_TIMEOUT_SEC
from english_interview_data import (
    ENGLISH_QUESTIONS, ADVANCED_QUESTIONS, ENGLISH_INTERVIEW_TIPS,
    get_questions_by_category, get_all_categories, get_random_questions,
    get_questions_count
)

# 음성 유틸리티 import
try:
    from voice_utils import (
        generate_tts_audio, get_audio_player_html, transcribe_audio,
        get_loud_audio_component, analyze_voice_complete
    )
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# PDF 리포트 import
try:
    from english_interview_report import (
        generate_english_interview_report, get_english_report_filename,
        get_weakness_recommendations_english
    )
    REPORT_AVAILABLE = True
except ImportError:
    REPORT_AVAILABLE = False

# 점수 자동 저장 유틸리티
try:
    from score_utils import save_practice_score, parse_evaluation_score
    SCORE_UTILS_AVAILABLE = True
except ImportError:
    SCORE_UTILS_AVAILABLE = False

from sidebar_common import render_sidebar

st.set_page_config(
    page_title="영어면접 연습",
    page_icon="🌍",
    layout="wide"
)
render_sidebar("영어면접")



# =====================
# 세션 상태 초기화
# =====================

defaults = {
    "eng_mode": None,
    "eng_questions": [],
    "eng_current_idx": 0,
    "eng_answers": {},
    "eng_feedback": {},
    "eng_completed": False,
    "eng_show_text": {},
    "eng_audio_played": {},
    "eng_listening_mode": True,
    # 음성 분석용
    "eng_audio_bytes_list": [],
    "eng_voice_analysis": None,
    "eng_processed_audio_id": None,
    "eng_response_times": [],
    "eng_question_start_time": None,
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
    """영어 답변 평가 (발음 피드백 강화)"""
    api_key = get_api_key()
    if not api_key:
        return {"error": "API 키 없음"}

    # 최소 답변 길이 체크 - 너무 짧으면 즉시 낮은 점수
    answer_stripped = answer.strip() if answer else ""
    if len(answer_stripped) < 5:
        return {
            "result": f"""### 점수: 1/10

### 발견된 오류 목록
1. 답변이 너무 짧거나 유효하지 않습니다. ("{answer_stripped}")

### 문법 & 어휘 평가
- 답변이 없거나 의미 없는 입력입니다. 영어 문장으로 답변해주세요.

### 내용 & 구성 평가
- 질문에 대한 답변이 전혀 이루어지지 않았습니다.

### 개선할 점
- 최소 2-3문장 이상의 영어 답변을 작성하세요.
- 질문의 핵심을 파악하고 구체적인 경험이나 의견을 영어로 표현하세요.

### 수정된 모범 답변
"(답변을 영어로 작성해주세요)"
"""
        }

    key_points_text = ", ".join(key_points) if key_points else "N/A"

    system_prompt = """You are a VERY STRICT airline interview examiner evaluating a candidate's English response.
You must be extremely strict. Do NOT give undeserved scores.
Provide feedback in Korean. Be honest and harsh when needed.

CRITICAL SCORING RULES:
- If the answer is NOT in English: maximum 2/10
- If the answer has NO relation to the question: maximum 3/10
- If the answer is just random characters or meaningless: 1/10
- If the answer is too short (under 2 sentences): maximum 5/10
- Only give 8+ when the answer is genuinely good with proper grammar and content

IMPORTANT: Since this is spoken English transcribed by speech recognition, pay special attention to:
1. Words that might be mispronounced (transcribed incorrectly)
2. Unclear pronunciation patterns visible in the transcription
3. Common Korean-speaker pronunciation issues (L/R, V/B, F/P, TH sounds)"""

    user_prompt = f"""## Interview Question
{question}

## Candidate's Answer (Transcribed from speech)
{answer}

## Key Points to Cover
{key_points_text}

## STRICT Evaluation Criteria

### 점수 산정 기준 (10점 만점) - 엄격 적용!
- 의미 없는 답변 (숫자, 무관한 텍스트): 1-2점
- 질문과 무관한 답변: 최대 3점
- 짧은 답변 (2문장 미만): 최대 5점
- **문법/철자 오류 1개당 -1점** (기본 점수에서 차감)
- 내용이 부실하면 추가 -1~2점
- 완벽한 답변만 9-10점 가능

### 엄격하게 체크해야 할 항목
1. **Grammar (문법)** - 시제, 주어-동사 일치, 관사(a/an/the), 전치사 오류 모두 체크
2. **Spelling/Pronunciation (철자/발음)** - STT 오류는 발음 문제 가능성, 명확히 지적
3. **Sentence Structure (문장 구조)** - 불완전한 문장, 어색한 어순
4. **Vocabulary (어휘)** - 부적절한 단어 사용, 항공 관련 전문 어휘

### 발음 분석 (STT 기반)
- 인식된 텍스트에서 발음 오류 가능성 분석
- 한국인이 자주 틀리는 발음 패턴 확인 (R/L, V/B, F/P, TH)
- 단어 누락/왜곡은 발음 불명확 가능성

## Output Format (Korean)
### 점수: X/10

### 발견된 오류 목록
1. (오류 원문) → (수정) : [문법/발음/어휘]
2. ...

### 문법 & 어휘 평가
- (구체적 평가)

### 발음 분석 (STT 기반)
- (인식된 텍스트 기반 발음 분석)
- (한국인 특유 발음 오류 패턴 체크)
- (발음 개선이 필요한 단어 목록)

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
            "max_tokens": 1000,
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
st.caption(f"항공사 영어면접을 준비하세요. 총 {get_questions_count()}개 질문 | 음성 분석 & PDF 리포트")

# 모드 선택
if st.session_state.eng_mode is None:
    st.subheader("연습 모드 선택")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📚 카테고리별 연습")
        st.write("원하는 카테고리의 질문을 선택해서 연습합니다.")
        st.write("- 모범 답변 참고 가능")
        st.write("- 질문별 즉시 피드백")
        st.write("- 발음 분석 포함")
        if st.button("카테고리별 연습 시작", use_container_width=True, type="primary"):
            st.session_state.eng_mode = "practice"
            st.rerun()

    with col2:
        st.markdown("### 🎯 모의면접")
        st.write("실제 면접처럼 랜덤 질문 5개를 답변합니다.")
        st.write("- 모범 답변 숨김")
        st.write("- 전체 완료 후 종합 피드백")
        st.write("- 음성 분석 & PDF 리포트")

        if VOICE_AVAILABLE:
            listening_mode = st.checkbox(
                "🎧 리스닝 모드 (질문을 음성으로 먼저 듣기)",
                value=True,
                help="질문이 영어 음성으로 먼저 재생됩니다."
            )
            st.session_state.eng_listening_mode = listening_mode

        if st.button("모의면접 시작", use_container_width=True):
            st.session_state.eng_mode = "mock"
            st.session_state.eng_questions = get_random_questions(5)
            st.session_state.eng_current_idx = 0
            st.session_state.eng_answers = {}
            st.session_state.eng_feedback = {}
            st.session_state.eng_completed = False
            st.session_state.eng_show_text = {}
            st.session_state.eng_audio_played = {}
            st.session_state.eng_audio_bytes_list = []
            st.session_state.eng_voice_analysis = None
            st.session_state.eng_processed_audio_id = None
            st.session_state.eng_response_times = []
            st.session_state.eng_question_start_time = None
            st.rerun()

    st.divider()
    with st.expander("💡 영어면접 Tips", expanded=False):
        for tip in ENGLISH_INTERVIEW_TIPS:
            st.write(f"• {tip}")

# 카테고리별 연습 모드
elif st.session_state.eng_mode == "practice":
    if st.button("← 모드 선택으로"):
        st.session_state.eng_mode = None
        st.rerun()

    st.subheader("카테고리별 연습")

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

    with col_mode:
        if VOICE_AVAILABLE:
            practice_listening = st.checkbox(
                "🎧 리스닝 모드",
                value=True,
                help="질문을 음성으로 먼저 듣기"
            )
        else:
            practice_listening = False

    questions = get_questions_by_category(selected_cat_key)

    if practice_listening:
        st.info("🎧 **리스닝 모드**: 질문을 먼저 듣고, '텍스트 보기'를 클릭하면 영어 텍스트가 표시됩니다.")

    st.divider()

    for i, q in enumerate(questions):
        question_text = q['question']
        answer_key = f"practice_{selected_cat_key}_{i}"
        show_text_key = f"show_text_practice_{selected_cat_key}_{i}"
        transcription_key = f"transcription_{answer_key}"
        processed_audio_key = f"processed_audio_{answer_key}"

        if transcription_key not in st.session_state:
            st.session_state[transcription_key] = ""
        if processed_audio_key not in st.session_state:
            st.session_state[processed_audio_key] = None

        show_text = not practice_listening or st.session_state.get(show_text_key, False)

        if practice_listening:
            if st.session_state.get(show_text_key, False):
                expander_title = f"Q{i+1}: {question_text}"
            else:
                expander_title = f"🎧 Question {i+1} - 듣기"
        else:
            expander_title = f"Q{i+1}: {question_text}"

        with st.expander(expander_title, expanded=(i == 0 and not practice_listening)):

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

                if st.session_state.get(show_text_key, False):
                    st.markdown(f"**🎤 {question_text}**")
                    st.caption(f"💡 힌트: {q['korean_hint']}")

            else:
                st.caption(f"💡 힌트: {q['korean_hint']}")

                if VOICE_AVAILABLE:
                    if st.button("🔊 질문 듣기", key=f"play_q_practice_{selected_cat_key}_{i}"):
                        with st.spinner("음성 생성 중..."):
                            audio = generate_tts_audio(question_text, voice="alloy", speed=0.85, use_clova=False)
                            if audio:
                                get_loud_audio_component(audio, autoplay=True, gain=5.0)

            st.markdown("**핵심 포인트:** " + ", ".join(q.get("key_points", [])))

            st.divider()

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
                            audio_id = f"{audio_data.name}_{audio_data.size}"

                            if audio_id != st.session_state[processed_audio_key]:
                                st.audio(audio_data, format="audio/wav")

                                if st.button("📤 음성 변환", key=f"submit_voice_practice_{selected_cat_key}_{i}", type="primary"):
                                    with st.spinner("음성 인식 중..."):
                                        transcription = transcribe_audio(audio_data.getvalue(), language="en")
                                        if transcription and transcription.get("text"):
                                            recognized_text = transcription["text"]
                                            st.session_state[transcription_key] = recognized_text
                                            st.session_state[processed_audio_key] = audio_id
                                            st.rerun()
                                        else:
                                            st.error("음성 인식 실패. 다시 시도해주세요.")
                            else:
                                st.audio(audio_data, format="audio/wav")

                        if st.session_state[transcription_key]:
                            st.markdown("---")
                            st.markdown("**📝 인식된 답변 (발음 확인):**")
                            st.success(st.session_state[transcription_key])
                            st.caption("위 텍스트가 실제로 말한 내용과 다르면, 발음을 더 명확히 해보세요.")
                            answer = st.session_state[transcription_key]

                    except Exception as e:
                        st.warning("음성 녹음을 사용할 수 없습니다. 텍스트로 답변해주세요.")

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
                    answer = st.text_area(
                        "Your Answer (영어로 답변하세요)",
                        key=f"ans_{answer_key}",
                        height=120,
                        placeholder="Type your answer in English..."
                    )
            else:
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

            if answer_key in st.session_state.eng_feedback:
                fb = st.session_state.eng_feedback[answer_key]
                if "error" in fb:
                    st.error(fb["error"])
                else:
                    st.markdown("---")
                    st.markdown("#### 📝 피드백")
                    st.markdown(fb.get("result", ""))

            if show_sample:
                st.markdown("---")
                st.markdown("#### ✅ Sample Answer")
                st.info(q.get("sample_answer", ""))

                if VOICE_AVAILABLE:
                    if st.button("🔊 모범 답변 듣기", key=f"play_sample_{selected_cat_key}_{i}"):
                        with st.spinner("음성 생성 중..."):
                            sample_audio = generate_tts_audio(q.get("sample_answer", ""), voice="alloy", speed=0.85, use_clova=False)
                            if sample_audio:
                                get_loud_audio_component(sample_audio, autoplay=True, gain=5.0)

# 모의면접 모드
elif st.session_state.eng_mode == "mock":
    import time

    if not st.session_state.eng_completed:
        current_idx = st.session_state.eng_current_idx
        total = len(st.session_state.eng_questions)

        st.progress((current_idx) / total)
        st.subheader(f"Question {current_idx + 1} of {total}")

        if current_idx < total:
            q = st.session_state.eng_questions[current_idx]
            question_text = q['question']

            # 질문 시작 시간 기록
            if st.session_state.eng_question_start_time is None:
                st.session_state.eng_question_start_time = time.time()

            if st.session_state.eng_listening_mode and VOICE_AVAILABLE:
                st.markdown("### 🎧 Listen to the question")

                col_audio1, col_audio2 = st.columns([1, 1])
                with col_audio1:
                    if st.button("🔊 질문 듣기", key=f"play_q_{current_idx}", use_container_width=True):
                        with st.spinner("음성 생성 중..."):
                            audio = generate_tts_audio(
                                question_text,
                                voice="alloy",
                                speed=0.85,
                                use_clova=False
                            )
                            if audio:
                                st.session_state.eng_audio_played[current_idx] = True
                                get_loud_audio_component(audio, autoplay=True, gain=5.0)
                            else:
                                st.error("음성 생성에 실패했습니다.")

                with col_audio2:
                    if st.button("📝 텍스트 보기", key=f"show_text_{current_idx}", use_container_width=True):
                        st.session_state.eng_show_text[current_idx] = True

                if st.session_state.eng_show_text.get(current_idx, False):
                    st.markdown(f"### 🎤 {question_text}")
                    st.caption(f"힌트: {q['korean_hint']}")
                else:
                    st.info("질문을 먼저 듣고, 필요하면 '텍스트 보기'를 클릭하세요.")

                st.caption(f"카테고리: {q.get('category', '')}")

            else:
                st.markdown(f"### 🎤 {question_text}")
                st.caption(f"힌트: {q['korean_hint']}")
                st.caption(f"카테고리: {q.get('category', '')}")

                if VOICE_AVAILABLE:
                    if st.button("🔊 질문 듣기", key=f"play_q_normal_{current_idx}"):
                        with st.spinner("음성 생성 중..."):
                            audio = generate_tts_audio(question_text, voice="alloy", speed=0.85, use_clova=False)
                            if audio:
                                get_loud_audio_component(audio, autoplay=True, gain=5.0)

            st.divider()

            answer = None
            mock_transcription_key = f"mock_transcription_{current_idx}"
            mock_processed_audio_key = f"mock_processed_audio_{current_idx}"

            if mock_transcription_key not in st.session_state:
                st.session_state[mock_transcription_key] = ""
            if mock_processed_audio_key not in st.session_state:
                st.session_state[mock_processed_audio_key] = None

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
                            audio_id = f"{audio_data.name}_{audio_data.size}"

                            if audio_id != st.session_state[mock_processed_audio_key]:
                                st.audio(audio_data, format="audio/wav")

                                if st.button("📤 음성 변환", key=f"submit_voice_{current_idx}", type="primary"):
                                    with st.spinner("음성 인식 중..."):
                                        transcription = transcribe_audio(audio_data.getvalue(), language="en")
                                        if transcription and transcription.get("text"):
                                            recognized_text = transcription["text"]
                                            st.session_state[mock_transcription_key] = recognized_text
                                            st.session_state[mock_processed_audio_key] = audio_id

                                            # 음성 데이터 저장 (종합 분석용)
                                            if len(st.session_state.eng_audio_bytes_list) <= current_idx:
                                                st.session_state.eng_audio_bytes_list.append(audio_data.getvalue())

                                            st.rerun()
                                        else:
                                            st.error("음성 인식에 실패했습니다. 다시 시도해주세요.")
                            else:
                                st.audio(audio_data, format="audio/wav")

                        if st.session_state[mock_transcription_key]:
                            st.markdown("---")
                            st.markdown("**📝 인식된 답변 (발음 확인):**")
                            st.success(st.session_state[mock_transcription_key])
                            st.caption("위 텍스트가 실제로 말한 내용과 다르면, 발음을 더 명확히 해보세요.")
                            answer = st.session_state[mock_transcription_key]

                    except Exception as e:
                        st.warning("음성 녹음을 사용할 수 없습니다. 텍스트로 답변해주세요.")

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
                    answer = st.text_area(
                        "Your Answer",
                        key=f"mock_ans_{current_idx}",
                        height=150,
                        placeholder="Type your answer in English..."
                    )
            else:
                answer = st.text_area(
                    "Your Answer",
                    key=f"mock_ans_{current_idx}",
                    height=150,
                    placeholder="Type your answer in English..."
                )

            col1, col_sp, col2 = st.columns([2, 1, 2])

            with col1:
                if st.button("다음 질문 →", disabled=not (answer and answer.strip()), type="primary", use_container_width=True):
                    # 응답 시간 기록
                    if st.session_state.eng_question_start_time:
                        response_time = time.time() - st.session_state.eng_question_start_time
                        st.session_state.eng_response_times.append(response_time)

                    st.session_state.eng_answers[current_idx] = {
                        "question": q["question"],
                        "answer": answer,
                        "key_points": q.get("key_points", [])
                    }

                    if current_idx + 1 >= total:
                        st.session_state.eng_completed = True
                    else:
                        st.session_state.eng_current_idx += 1
                        st.session_state.eng_show_text[current_idx + 1] = False
                        st.session_state.eng_question_start_time = None

                    st.rerun()

            with col2:
                if st.button("모의면접 중단", use_container_width=True):
                    st.session_state.eng_mode = None
                    st.session_state.eng_questions = []
                    st.session_state.eng_answers = {}
                    st.session_state.eng_question_start_time = None
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

                    if SCORE_UTILS_AVAILABLE and "result" in fb:
                        parsed = parse_evaluation_score(fb["result"], "영어면접")
                        if parsed.get("total", 0) > 0:
                            total_scores.append(parsed["total"])

                st.session_state.mock_final_feedback = all_feedback

                if SCORE_UTILS_AVAILABLE and total_scores:
                    avg_score = sum(total_scores) / len(total_scores)
                    save_practice_score(
                        practice_type="영어면접",
                        total_score=round(avg_score),
                        detailed_scores=None,
                        scenario="모의면접 (5문항 평균)"
                    )

        # 음성 분석 (음성 데이터가 있을 때만)
        if VOICE_AVAILABLE and st.session_state.eng_audio_bytes_list and st.session_state.eng_voice_analysis is None:
            with st.spinner("음성 전달력을 분석하고 있습니다..."):
                try:
                    # 마지막 음성 데이터로 분석
                    last_audio = st.session_state.eng_audio_bytes_list[-1]
                    voice_result = analyze_voice_complete(
                        audio_bytes=last_audio,
                        transcription=None,
                        expected_duration_range=(10, 90),
                        response_times=st.session_state.eng_response_times
                    )
                    st.session_state.eng_voice_analysis = voice_result
                except Exception as e:
                    st.warning(f"음성 분석 중 오류: {e}")

        # 종합 점수 표시
        # 텍스트 기반 평균 점수 계산 (음성 분석 없을 때 사용)
        text_avg_score = 0
        if "mock_final_feedback" in st.session_state:
            _scores = []
            for _fb in st.session_state.mock_final_feedback.values():
                if "result" in _fb:
                    import re as _re
                    _match = _re.search(r'점수[:\s]*(\d+)\s*/\s*10', _fb["result"])
                    if _match:
                        _scores.append(int(_match.group(1)) * 10)
            if _scores:
                text_avg_score = sum(_scores) // len(_scores)

        # 표시할 점수/등급 결정
        if st.session_state.eng_voice_analysis:
            display_score = st.session_state.eng_voice_analysis.get("total_score", 0)
            display_grade = st.session_state.eng_voice_analysis.get("grade", "N/A")
            display_summary = st.session_state.eng_voice_analysis.get("summary", "")
            display_improvements = st.session_state.eng_voice_analysis.get("top_improvements", [])
        elif text_avg_score > 0:
            display_score = text_avg_score
            if display_score >= 90: display_grade = "S"
            elif display_score >= 80: display_grade = "A"
            elif display_score >= 70: display_grade = "B"
            elif display_score >= 60: display_grade = "C"
            else: display_grade = "D"
            display_summary = f"영어 답변 평균 {display_score}점 (텍스트 평가 기준)"
            display_improvements = []
        else:
            display_score = 0
            display_grade = "N/A"
            display_summary = ""
            display_improvements = []

        if display_score > 0:
            col_score1, col_score2 = st.columns([1, 2])

            with col_score1:
                grade_colors = {"S": "#FFD700", "A": "#4CAF50", "B": "#2196F3", "C": "#FF9800", "D": "#F44336"}
                color = grade_colors.get(display_grade, "#888")

                st.markdown(f"""
                <div style="text-align:center; padding:20px; background:linear-gradient(135deg, {color}22, {color}44); border-radius:15px; border:2px solid {color};">
                    <h1 style="color:{color}; margin:0; font-size:3em;">{display_grade}</h1>
                    <p style="font-size:1.5em; margin:5px 0;">{display_score}점</p>
                </div>
                """, unsafe_allow_html=True)

            with col_score2:
                st.markdown(f"**{display_summary}**")

                if display_improvements:
                    st.markdown("**🔧 우선 개선 포인트:**")
                    for imp in display_improvements[:3]:
                        st.write(f"• {imp}")

                if not st.session_state.eng_voice_analysis:
                    st.caption("💡 음성 녹음 모드를 사용하면 발음/음성 전달력 분석도 제공됩니다.")

        # PDF 다운로드 버튼
        if REPORT_AVAILABLE:
            st.divider()

            questions_answers = [st.session_state.eng_answers[idx] for idx in sorted(st.session_state.eng_answers.keys())]

            try:
                pdf_bytes = generate_english_interview_report(
                    questions_answers=questions_answers,
                    feedbacks=st.session_state.mock_final_feedback,
                    voice_analysis=st.session_state.eng_voice_analysis,
                    mode="mock",
                    user_name="Candidate"
                )

                st.download_button(
                    label="📄 PDF 리포트 다운로드",
                    data=pdf_bytes,
                    file_name=get_english_report_filename(),
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"PDF 생성 오류: {e}")

        # 약점 기반 추천 (음성 분석 없어도 텍스트 피드백 기반으로 추천)
        if REPORT_AVAILABLE:
            # 전체 피드백 텍스트 결합 (약점 키워드 추출용)
            combined_feedback = ""
            if "mock_final_feedback" in st.session_state:
                for _fb in st.session_state.mock_final_feedback.values():
                    if "result" in _fb:
                        combined_feedback += _fb["result"] + "\n"

            recommendations = get_weakness_recommendations_english(
                st.session_state.eng_voice_analysis,
                combined_feedback,
                3
            )

            if recommendations:
                st.divider()
                st.markdown("### 🎯 약점 기반 추천 질문")

                for i, rec in enumerate(recommendations, 1):
                    with st.expander(f"{i}. [{rec['weakness']}] 개선 - {rec['category']}"):
                        st.markdown(f"**Q:** {rec['question']}")
                        st.caption(f"힌트: {rec['korean_hint']}")
                        st.info(f"💡 {rec['tip']}")

        # 결과 상세 표시
        st.divider()
        st.markdown("### 📋 질문별 상세 결과")

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
                st.session_state.eng_audio_bytes_list = []
                st.session_state.eng_voice_analysis = None
                st.session_state.eng_response_times = []
                st.session_state.eng_question_start_time = None
                if "mock_final_feedback" in st.session_state:
                    del st.session_state.mock_final_feedback
                st.rerun()

        with col2:
            if st.button("모드 선택으로", use_container_width=True):
                st.session_state.eng_mode = None
                st.session_state.eng_questions = []
                st.session_state.eng_answers = {}
                st.session_state.eng_audio_bytes_list = []
                st.session_state.eng_voice_analysis = None
                st.session_state.eng_response_times = []
                if "mock_final_feedback" in st.session_state:
                    del st.session_state.mock_final_feedback
                st.rerun()

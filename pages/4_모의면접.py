# pages/4_모의면접.py
# 실전 모의면접 - AI 영상 면접관 + 음성 답변 + 음성/내용 평가

import os
import time
import random
import base64
import json
import streamlit as st
import streamlit.components.v1 as components
import requests

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import LLM_MODEL_NAME, LLM_API_URL, LLM_TIMEOUT_SEC, AIRLINES, AIRLINE_TYPE
from auth_utils import check_tester_password
from env_config import OPENAI_API_KEY

# 음성/영상 유틸리티 import
try:
    from video_utils import (
        check_did_api_available,
        create_interviewer_video,
        get_video_html,
        get_fallback_avatar_html,
    )
    from voice_utils import (
        transcribe_audio,
        analyze_voice_quality,
        evaluate_answer_content,
        generate_tts_audio,
        get_audio_player_html,
        get_loud_audio_component,
    )
    VIDEO_UTILS_AVAILABLE = True
except ImportError:
    VIDEO_UTILS_AVAILABLE = False

# 점수 자동 저장 유틸리티
try:
    from score_utils import save_practice_score, parse_evaluation_score
    SCORE_UTILS_AVAILABLE = True
except ImportError:
    SCORE_UTILS_AVAILABLE = False

# 사용량 제한 시스템
try:
    from usage_limiter import check_and_use, show_usage_status, render_beta_banner, get_remaining
    USAGE_LIMITER_AVAILABLE = True
except ImportError:
    USAGE_LIMITER_AVAILABLE = False

st.set_page_config(
    page_title="모의면접",
    page_icon="🎙️",
    layout="wide"
)

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="모의면접")
except ImportError:
    pass

# 구글 번역 방지
st.markdown(
    """
    <meta name="google" content="notranslate">
    <style>html { translate: no; }</style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# 비밀번호 보호
# ----------------------------
check_tester_password()

# =====================
# 면접 질문 풀
# =====================

INTERVIEW_QUESTIONS = {
    "common": [
        "간단하게 자기소개 해주세요.",
        "왜 승무원이 되고 싶으신가요?",
        "저희 항공사에 왜 지원하셨나요?",
        "본인의 강점과 약점을 말씀해주세요.",
        "승무원에게 가장 중요한 자질은 무엇이라고 생각하시나요?",
    ],
    "experience": [
        "팀워크를 발휘했던 경험을 말씀해주세요.",
        "어려운 고객을 응대한 경험이 있나요?",
        "갈등을 해결했던 경험을 말씀해주세요.",
        "실패했던 경험과 그로부터 배운 점은 무엇인가요?",
        "리더십을 발휘한 경험을 말씀해주세요.",
    ],
    "situational": [
        "기내에서 승객이 쓰러지면 어떻게 하시겠습니까?",
        "승객이 무리한 요구를 하면 어떻게 대응하시겠습니까?",
        "동료와 의견 충돌이 생기면 어떻게 하시겠습니까?",
        "비행 중 공황 상태의 승객을 어떻게 도우시겠습니까?",
        "안전규정을 거부하는 승객을 어떻게 설득하시겠습니까?",
    ],
    "personality": [
        "스트레스를 어떻게 관리하시나요?",
        "주변에서 본인을 어떻게 평가하나요?",
        "10년 후 본인의 모습은 어떨 것 같나요?",
        "왜 다른 직업이 아닌 승무원인가요?",
        "이 직업의 어려운 점은 무엇이라고 생각하시나요?",
    ],
}

# =====================
# 세션 상태 초기화
# =====================

defaults = {
    "mock_started": False,
    "mock_questions": [],
    "mock_current_idx": 0,
    "mock_answers": [],
    "mock_transcriptions": [],
    "mock_times": [],
    "mock_voice_analyses": [],
    "mock_content_analyses": [],
    "mock_completed": False,
    "mock_airline": "",
    "mock_mode": "text",  # text / voice
    "mock_evaluation": None,
    "answer_start_time": None,
    "timer_running": False,
    "recorded_audio": None,
    "video_generated": False,
    "current_video_url": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =====================
# 헬퍼 함수
# =====================

def get_api_key():
    return os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY") or ""


def generate_questions(airline: str, count: int = 6) -> list:
    """면접 질문 생성 - count에 맞춰 동적으로 생성"""
    questions = []

    # count에 따라 각 카테고리에서 뽑을 개수 결정
    if count <= 4:
        # 4개: common 2, experience 1, situational 1
        questions.extend(random.sample(INTERVIEW_QUESTIONS["common"], 2))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["experience"], 1))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["situational"], 1))
    elif count <= 6:
        # 5-6개: common 2, experience 1, situational 2, personality 1
        questions.extend(random.sample(INTERVIEW_QUESTIONS["common"], 2))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["experience"], 1))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["situational"], 2))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["personality"], 1))
    else:
        # 7-8개: common 2, experience 2, situational 2, personality 2
        questions.extend(random.sample(INTERVIEW_QUESTIONS["common"], 2))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["experience"], 2))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["situational"], 2))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["personality"], 2))

    random.shuffle(questions)
    return questions[:count]


def evaluate_interview_combined(
    airline: str,
    questions: list,
    answers: list,
    times: list,
    voice_analyses: list,
    content_analyses: list,
) -> dict:
    """음성 + 내용 종합 평가"""
    api_key = get_api_key()
    if not api_key:
        return {"error": "API 키 없음"}

    # 각 질문별 점수 요약
    qa_summary = ""
    total_voice_score = 0
    total_content_score = 0

    for i, (q, a, t) in enumerate(zip(questions, answers, times), 1):
        voice = voice_analyses[i-1] if i-1 < len(voice_analyses) else {}
        content = content_analyses[i-1] if i-1 < len(content_analyses) else {}

        voice_score = voice.get("total_score", 0)
        content_score = content.get("total_score", 0)
        total_voice_score += voice_score
        total_content_score += content_score

        qa_summary += f"\n### 질문 {i}: {q}\n"
        qa_summary += f"- 답변 (소요시간: {t}초): {a[:200]}...\n" if len(a) > 200 else f"- 답변 (소요시간: {t}초): {a}\n"
        qa_summary += f"- 음성 점수: {voice_score}/100\n"
        qa_summary += f"- 내용 점수: {content_score}/100\n"

    avg_voice = total_voice_score // max(len(questions), 1)
    avg_content = total_content_score // max(len(questions), 1)

    system_prompt = """당신은 엄격한 항공사 면접관입니다.
음성 평가와 내용 평가를 종합하여 최종 피드백을 제공하세요.
한국어로 상세하게 작성하세요."""

    user_prompt = f"""## 지원 항공사: {airline}

## 면접 내용 및 개별 평가
{qa_summary}

## 평균 점수
- 음성 평균: {avg_voice}/100
- 내용 평균: {avg_content}/100
- 종합 점수: {(avg_voice + avg_content) // 2}/100

## 종합 평가를 작성해주세요

### 출력 형식

#### 종합 점수: X/100

#### 음성 전달력 총평
(말 속도, 필러 단어, 발음 등)

#### 답변 내용 총평
(구체성, STAR 구조, 논리성 등)

#### 가장 잘한 점 (2-3개)
- ...

#### 반드시 개선해야 할 점 (3-4개)
- ...

#### 합격 가능성
(솔직하게)

#### 다음 연습 때 집중할 것
(구체적인 액션 아이템)"""

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
            "max_tokens": 1500,
        }

        r = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        resp = r.json()

        choices = resp.get("choices", [])
        if choices:
            return {
                "result": choices[0].get("message", {}).get("content", "").strip(),
                "avg_voice": avg_voice,
                "avg_content": avg_content,
            }
        return {"error": "평가 생성 실패"}

    except Exception as e:
        return {"error": str(e)}


# =====================
# 음성 녹음 컴포넌트 (JavaScript)
# =====================

def get_audio_recorder_html():
    """JavaScript 기반 음성 녹음 컴포넌트"""
    return """
    <div id="recorder-container" style="text-align: center; padding: 20px;">
        <div id="status" style="margin-bottom: 15px; font-size: 18px; color: #333;">
            🎤 녹음 준비 완료
        </div>
        <div id="timer" style="font-size: 48px; font-weight: bold; color: #28a745; margin: 20px 0;">
            00:00
        </div>
        <div style="margin: 20px 0;">
            <button id="startBtn" onclick="startRecording()"
                style="padding: 15px 40px; font-size: 18px; background: #28a745; color: white; border: none; border-radius: 25px; cursor: pointer; margin: 5px;">
                🎬 녹음 시작
            </button>
            <button id="stopBtn" onclick="stopRecording()" disabled
                style="padding: 15px 40px; font-size: 18px; background: #dc3545; color: white; border: none; border-radius: 25px; cursor: pointer; margin: 5px;">
                ⏹️ 녹음 종료
            </button>
        </div>
        <div id="audioContainer" style="margin-top: 20px;"></div>
    </div>

    <script>
    let mediaRecorder;
    let audioChunks = [];
    let startTime;
    let timerInterval;

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const audioUrl = URL.createObjectURL(audioBlob);

                // 오디오 플레이어 표시
                document.getElementById('audioContainer').innerHTML =
                    '<audio controls src="' + audioUrl + '" style="width: 100%;"></audio>';

                // Streamlit에 데이터 전송
                const reader = new FileReader();
                reader.onloadend = () => {
                    const base64data = reader.result.split(',')[1];
                    window.parent.postMessage({
                        type: 'audio_data',
                        data: base64data
                    }, '*');
                };
                reader.readAsDataURL(audioBlob);
            };

            mediaRecorder.start();
            startTime = Date.now();

            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            document.getElementById('status').innerHTML = '🔴 녹음 중...';
            document.getElementById('status').style.color = '#dc3545';

            // 타이머 시작
            timerInterval = setInterval(() => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                const mins = Math.floor(elapsed / 60);
                const secs = elapsed % 60;
                const timerEl = document.getElementById('timer');
                timerEl.textContent = String(mins).padStart(2, '0') + ':' + String(secs).padStart(2, '0');

                // 색상 변경
                if (elapsed < 60) {
                    timerEl.style.color = '#28a745';
                } else if (elapsed < 90) {
                    timerEl.style.color = '#ffc107';
                } else {
                    timerEl.style.color = '#dc3545';
                }
            }, 1000);

        } catch (err) {
            alert('마이크 접근 권한이 필요합니다: ' + err.message);
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());

            clearInterval(timerInterval);

            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            document.getElementById('status').innerHTML = '✅ 녹음 완료';
            document.getElementById('status').style.color = '#28a745';
        }
    }
    </script>
    """


# =====================
# UI
# =====================

st.title("🎙️ 실전 모의면접")
st.caption("AI 면접관과 함께하는 실전 연습 (음성/텍스트 선택 가능)")

# D-ID API 상태 확인
did_available = VIDEO_UTILS_AVAILABLE and check_did_api_available() if VIDEO_UTILS_AVAILABLE else False

if not st.session_state.mock_started:
    # =====================
    # 면접 설정 화면
    # =====================
    st.subheader("면접 설정")

    col1, col2, col3 = st.columns(3)

    with col1:
        airline = st.selectbox("지원 항공사", AIRLINES)
        airline_type = AIRLINE_TYPE.get(airline, "LCC")

    with col2:
        question_count = st.slider("질문 개수", 4, 8, 6)

    with col3:
        answer_mode = st.radio(
            "답변 방식",
            ["텍스트 입력", "음성 녹음"],
            help="음성 녹음 시 마이크 권한이 필요합니다"
        )

    st.divider()

    # 안내 박스
    if answer_mode == "음성 녹음":
        st.info("""
        ### 🎤 음성 모의면접
        1. **AI 면접관**이 질문을 읽어줍니다
        2. **마이크**로 답변을 녹음합니다
        3. **음성 분석**: 말 속도, 필러 단어, 발음 등 평가
        4. **내용 분석**: STAR 구조, 구체성, 논리성 평가
        5. **종합 피드백**: 음성 + 내용 통합 평가
        """)
    else:
        st.info("""
        ### 📝 텍스트 모의면접
        1. 질문이 표시되면 **타이머**가 시작됩니다
        2. 실제 면접처럼 **60-90초** 내에 답변하세요
        3. **내용 분석**: STAR 구조, 구체성, 논리성 평가
        """)

    # 남은 사용량 표시
    if USAGE_LIMITER_AVAILABLE:
        remaining = get_remaining("모의면접")
        st.markdown(f"오늘 남은 횟수: **{remaining}회**")

    # 시작 버튼
    if st.button("모의면접 시작", type="primary", use_container_width=True):
        # 사용량 체크
        if USAGE_LIMITER_AVAILABLE and not check_and_use("모의면접"):
            st.stop()

        st.session_state.mock_started = True
        st.session_state.mock_questions = generate_questions(airline, question_count)
        st.session_state.mock_current_idx = 0
        st.session_state.mock_answers = []
        st.session_state.mock_transcriptions = []
        st.session_state.mock_times = []
        st.session_state.mock_voice_analyses = []
        st.session_state.mock_content_analyses = []
        st.session_state.mock_completed = False
        st.session_state.mock_airline = airline
        st.session_state.mock_mode = "voice" if answer_mode == "음성 녹음" else "text"
        st.session_state.mock_evaluation = None
        st.session_state.answer_start_time = None
        st.session_state.timer_running = False
        st.session_state.recorded_audio = None
        st.rerun()


elif not st.session_state.mock_completed:
    # =====================
    # 면접 진행 화면
    # =====================
    current_idx = st.session_state.mock_current_idx
    total = len(st.session_state.mock_questions)
    question = st.session_state.mock_questions[current_idx]
    airline = st.session_state.mock_airline
    airline_type = AIRLINE_TYPE.get(airline, "LCC")

    # 진행률
    st.progress((current_idx) / total)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"질문 {current_idx + 1} / {total}")
    with col2:
        if st.button("면접 중단"):
            st.session_state.mock_started = False
            st.session_state.timer_running = False
            st.rerun()

    # 면접관 표시 영역
    st.markdown("---")

    # 면접관 아바타/영상
    if did_available:
        # D-ID 영상 (실제 구현 시)
        st.markdown(get_fallback_avatar_html(question, "interviewer", is_speaking=True), unsafe_allow_html=True)
        st.caption("🎬 AI 면접관이 질문합니다")
    else:
        # 폴백 아바타
        st.markdown(get_fallback_avatar_html(question, "interviewer", is_speaking=True), unsafe_allow_html=True)

    # TTS로 질문 읽기 (옵션)
    if st.session_state.mock_mode == "voice" and VIDEO_UTILS_AVAILABLE:
        if st.button("🔊 질문 다시 듣기"):
            with st.spinner("음성 생성 중..."):
                audio_bytes = generate_tts_audio(question, voice="alloy", speed=0.85)
                if audio_bytes:
                    get_loud_audio_component(audio_bytes, autoplay=True, gain=5.0)

    st.markdown("---")

    # =====================
    # 답변 입력 영역
    # =====================

    if st.session_state.mock_mode == "voice":
        # 음성 녹음 모드
        st.subheader("🎤 음성으로 답변하세요")

        # 음성 녹음 컴포넌트
        components.html(get_audio_recorder_html(), height=300)

        st.warning("⚠️ 녹음 후 '답변 제출' 버튼을 눌러주세요")

        # 텍스트 폴백 (음성 인식 실패 시)
        with st.expander("📝 텍스트로 입력하기 (음성 인식 실패 시)"):
            fallback_answer = st.text_area(
                "답변을 직접 입력하세요",
                height=150,
                key=f"fallback_{current_idx}"
            )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("답변 제출", type="primary", use_container_width=True):
                # 현재는 폴백 텍스트 사용 (실제 구현 시 음성 데이터 처리)
                answer = fallback_answer.strip() if fallback_answer else "[음성 답변]"

                # 시간 기록 (임시)
                elapsed = 60  # 실제로는 녹음 시간

                # 음성 분석 (데모용 더미 데이터)
                voice_analysis = {
                    "speech_rate": {"wpm": 135, "score": 8, "feedback": "적절한 말 속도"},
                    "filler_words": {"count": 2, "score": 8, "feedback": "추임새 적음"},
                    "pauses": {"count": 1, "score": 9, "feedback": "자연스러운 흐름"},
                    "duration": {"seconds": elapsed, "score": 10, "feedback": "적절한 시간"},
                    "clarity": {"score": 8, "feedback": "발음 명확"},
                    "total_score": 82,
                    "total_feedback": "음성 전달력이 우수합니다."
                }

                # 내용 분석
                if VIDEO_UTILS_AVAILABLE and answer != "[음성 답변]":
                    with st.spinner("답변 분석 중..."):
                        content_analysis = evaluate_answer_content(
                            question, answer, airline, airline_type
                        )
                else:
                    content_analysis = {"total_score": 0, "error": "분석 불가"}

                st.session_state.mock_answers.append(answer)
                st.session_state.mock_times.append(elapsed)
                st.session_state.mock_voice_analyses.append(voice_analysis)
                st.session_state.mock_content_analyses.append(content_analysis)

                if current_idx + 1 >= total:
                    st.session_state.mock_completed = True
                else:
                    st.session_state.mock_current_idx += 1

                st.rerun()

        with col2:
            if st.button("패스 (답변 못함)", use_container_width=True):
                st.session_state.mock_answers.append("[답변 못함]")
                st.session_state.mock_times.append(0)
                st.session_state.mock_voice_analyses.append({"total_score": 0})
                st.session_state.mock_content_analyses.append({"total_score": 0})

                if current_idx + 1 >= total:
                    st.session_state.mock_completed = True
                else:
                    st.session_state.mock_current_idx += 1

                st.rerun()

    else:
        # 텍스트 입력 모드 (기존 방식)
        if not st.session_state.timer_running:
            st.info("💡 준비가 되면 '답변 시작' 버튼을 눌러주세요.")

            if st.button("🎬 답변 시작", type="primary", use_container_width=True):
                st.session_state.timer_running = True
                st.session_state.answer_start_time = time.time()
                st.rerun()

        else:
            # 타이머 실행 중
            start_time = st.session_state.answer_start_time

            timer_html = f"""
            <div style="text-align: center; margin: 20px 0;">
                <div id="timer" style="font-size: 48px; font-weight: bold; color: #28a745;">⏱️ 00:00</div>
                <div style="font-size: 14px; color: #666; margin-top: 5px;">적정 답변 시간: 60~90초</div>
            </div>
            <script>
                const startTime = {start_time * 1000};
                function updateTimer() {{
                    const elapsed = Math.floor((Date.now() - startTime) / 1000);
                    const mins = Math.floor(elapsed / 60);
                    const secs = elapsed % 60;
                    const el = document.getElementById('timer');
                    if (el) {{
                        el.textContent = '⏱️ ' + String(mins).padStart(2, '0') + ':' + String(secs).padStart(2, '0');
                        el.style.color = elapsed < 60 ? '#28a745' : elapsed < 90 ? '#ffc107' : '#dc3545';
                    }}
                }}
                updateTimer();
                setInterval(updateTimer, 1000);
            </script>
            """
            components.html(timer_html, height=120)

            answer = st.text_area(
                "답변을 입력하세요",
                height=200,
                key=f"answer_{current_idx}",
                placeholder="실제 면접에서 말하듯이 작성해주세요..."
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("답변 제출", type="primary", disabled=not answer.strip(), use_container_width=True):
                    elapsed = int(time.time() - st.session_state.answer_start_time)

                    # 내용 분석
                    if VIDEO_UTILS_AVAILABLE:
                        with st.spinner("답변 분석 중..."):
                            content_analysis = evaluate_answer_content(
                                question, answer.strip(), airline, airline_type
                            )
                    else:
                        content_analysis = {"total_score": 0}

                    st.session_state.mock_answers.append(answer.strip())
                    st.session_state.mock_times.append(elapsed)
                    st.session_state.mock_voice_analyses.append({})  # 텍스트 모드는 음성 분석 없음
                    st.session_state.mock_content_analyses.append(content_analysis)
                    st.session_state.timer_running = False

                    if current_idx + 1 >= total:
                        st.session_state.mock_completed = True
                    else:
                        st.session_state.mock_current_idx += 1

                    st.rerun()

            with col2:
                if st.button("패스 (답변 못함)", use_container_width=True):
                    elapsed = int(time.time() - st.session_state.answer_start_time)
                    st.session_state.mock_answers.append("[답변 못함]")
                    st.session_state.mock_times.append(elapsed)
                    st.session_state.mock_voice_analyses.append({})
                    st.session_state.mock_content_analyses.append({"total_score": 0})
                    st.session_state.timer_running = False

                    if current_idx + 1 >= total:
                        st.session_state.mock_completed = True
                    else:
                        st.session_state.mock_current_idx += 1

                    st.rerun()


else:
    # =====================
    # 면접 완료 - 종합 평가
    # =====================
    st.subheader("🎉 모의면접 완료!")

    st.markdown(f"**지원 항공사:** {st.session_state.mock_airline}")
    st.markdown(f"**답변 방식:** {'음성' if st.session_state.mock_mode == 'voice' else '텍스트'}")
    st.markdown(f"**총 질문 수:** {len(st.session_state.mock_questions)}개")

    total_time = sum(st.session_state.mock_times)
    st.markdown(f"**총 소요 시간:** {total_time // 60}분 {total_time % 60}초")

    st.divider()

    # 질문별 결과 탭
    tab1, tab2, tab3 = st.tabs(["📊 질문별 분석", "🎤 음성 평가", "📝 종합 평가"])

    with tab1:
        for i, (q, a, t) in enumerate(zip(
            st.session_state.mock_questions,
            st.session_state.mock_answers,
            st.session_state.mock_times
        ), 1):
            content = st.session_state.mock_content_analyses[i-1] if i-1 < len(st.session_state.mock_content_analyses) else {}

            with st.expander(f"Q{i}. {q[:50]}...", expanded=False):
                st.markdown(f"**답변:** {a}")
                st.caption(f"소요 시간: {t}초")

                if content and "total_score" in content:
                    st.markdown(f"**내용 점수:** {content.get('total_score', 0)}/100")

                    # STAR 체크
                    star = content.get("star_check", {})
                    if star:
                        cols = st.columns(4)
                        for j, (key, label) in enumerate([
                            ("situation", "S"), ("task", "T"), ("action", "A"), ("result", "R")
                        ]):
                            with cols[j]:
                                if star.get(key):
                                    st.success(f"✅ {label}")
                                else:
                                    st.error(f"❌ {label}")

                    # 개선점
                    improvements = content.get("improvements", [])
                    if improvements:
                        st.markdown("**개선점:**")
                        for imp in improvements:
                            st.markdown(f"- {imp}")

    with tab2:
        if st.session_state.mock_mode == "voice":
            for i, voice in enumerate(st.session_state.mock_voice_analyses, 1):
                if voice and voice.get("total_score", 0) > 0:
                    with st.expander(f"질문 {i} 음성 분석", expanded=False):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.metric("말 속도", f"{voice.get('speech_rate', {}).get('wpm', 0)} WPM")
                            st.caption(voice.get('speech_rate', {}).get('feedback', ''))

                        with col2:
                            st.metric("필러 단어", f"{voice.get('filler_words', {}).get('count', 0)}개")
                            st.caption(voice.get('filler_words', {}).get('feedback', ''))

                        st.metric("음성 점수", f"{voice.get('total_score', 0)}/100")
        else:
            st.info("텍스트 모드에서는 음성 평가가 제공되지 않습니다.")

    with tab3:
        if st.session_state.mock_evaluation is None:
            with st.spinner("종합 평가 생성 중... (최대 1분)"):
                evaluation = evaluate_interview_combined(
                    st.session_state.mock_airline,
                    st.session_state.mock_questions,
                    st.session_state.mock_answers,
                    st.session_state.mock_times,
                    st.session_state.mock_voice_analyses,
                    st.session_state.mock_content_analyses,
                )
                st.session_state.mock_evaluation = evaluation

                # 자동 점수 저장
                if SCORE_UTILS_AVAILABLE and "error" not in evaluation:
                    # 평가 결과에서 점수 파싱 시도
                    if "result" in evaluation:
                        parsed = parse_evaluation_score(evaluation["result"], "모의면접")
                        total_score = parsed.get("total", 0)
                    else:
                        total_score = 0

                    # 평균 점수로 대체 (파싱 실패 시)
                    if total_score == 0 and "avg_voice" in evaluation and "avg_content" in evaluation:
                        total_score = (evaluation["avg_voice"] + evaluation["avg_content"]) // 2

                    if total_score > 0:
                        save_practice_score(
                            practice_type="모의면접",
                            total_score=total_score,
                            detailed_scores=parsed.get("detailed") if "parsed" in dir() else None,
                            scenario=f"{st.session_state.mock_airline} 모의면접 ({len(st.session_state.mock_questions)}문항)"
                        )
            st.rerun()
        else:
            eval_result = st.session_state.mock_evaluation
            if "error" in eval_result:
                st.error(f"평가 오류: {eval_result['error']}")
            else:
                # 점수 표시
                if "avg_voice" in eval_result and "avg_content" in eval_result:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("음성 평균", f"{eval_result['avg_voice']}/100")
                    with col2:
                        st.metric("내용 평균", f"{eval_result['avg_content']}/100")
                    with col3:
                        combined = (eval_result['avg_voice'] + eval_result['avg_content']) // 2
                        st.metric("종합 점수", f"{combined}/100")

                st.markdown("---")
                st.markdown(eval_result.get("result", ""))

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("다시 도전하기", type="primary", use_container_width=True):
            st.session_state.mock_started = False
            st.session_state.mock_evaluation = None
            st.rerun()

    with col2:
        if st.button("처음으로", use_container_width=True):
            for key in defaults:
                st.session_state[key] = defaults[key]
            st.rerun()

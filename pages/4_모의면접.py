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
        analyze_voice_complete,
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

# 항공사별 맞춤 질문 import
try:
    from airline_questions import (
        get_airline_questions,
        get_airline_values,
        get_airline_keywords,
        AIRLINE_VALUES,
    )
    AIRLINE_QUESTIONS_AVAILABLE = True
except ImportError:
    AIRLINE_QUESTIONS_AVAILABLE = False

# PDF 리포트 생성 import
try:
    from mock_interview_report import (
        generate_mock_interview_report,
        get_mock_interview_report_filename,
    )
    REPORT_AVAILABLE = True
except ImportError:
    REPORT_AVAILABLE = False


from sidebar_common import render_sidebar

st.set_page_config(
    page_title="모의면접",
    page_icon="🎙️",
    layout="wide"
)
render_sidebar("모의면접")



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

# =====================
# 면접 질문 풀 (폴백용 기본 질문)
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

# 항공사별 핵심가치 요약 (UI 표시용)
AIRLINE_VALUE_SUMMARY = {
    "대한항공": "KE Way: Beyond Excellence, Journey Together, Better Tomorrow | 인재상: 진취성, 국제감각, 서비스정신, 성실, 팀워크",
    "아시아나항공": "Beautiful People | 핵심가치: 안전, 서비스, 지속가능성 | ESG: Better flight, Better tomorrow",
    "제주항공": "Fun & Fly | 7C 정신 | 핵심가치: 안전, 저비용, 신뢰, 팀워크, 도전",
    "진에어": "Fly, better fly | 5 JINISM: JINIABLE, JINIFUL, JINIVELY, JINISH, JINIQUE",
    "티웨이항공": "I want T'way | 5S: Safety, Smart, Satisfaction, Sharing, Sustainability",
    "에어부산": "FLY SMART | 안전운항, 지역친화, 효율성",
    "에어서울": "It's mint time | 최고안전, 행복서비스, 신뢰",
    "이스타항공": "Fly with EASTAR | 항공여행 대중화, 사회공익, 글로벌 국민항공사",
    "에어로케이": "새로운 하늘길 | 도전정신, 유연성, 성장지향",
    "에어프레미아": "Premium for all | HSC (Hybrid Service Carrier) | 프리미엄 서비스, 글로벌역량",
    "파라타항공": "Fly new | 핵심가치: 안전과 정시성, 투명함, 쾌적함, 고객가치 최우선 | 인재상: 신뢰 구축, 변화 적응력, 도전",
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
    # 음성 분석용 추가 변수
    "mock_audio_bytes_list": [],  # 각 질문별 음성 데이터 저장
    "mock_combined_voice_analysis": None,  # 종합 음성 분석 결과
    "mock_processed_audio_id": None,  # 오디오 중복 처리 방지
    "mock_response_times": [],  # 각 질문별 응답 시간
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
    """면접 질문 생성 - 항공사별 맞춤 질문 사용"""
    # 항공사별 맞춤 질문 모듈이 있으면 사용
    if AIRLINE_QUESTIONS_AVAILABLE:
        return get_airline_questions(airline, count)

    # 폴백: 기존 공통 질문 사용
    questions = []

    if count <= 4:
        questions.extend(random.sample(INTERVIEW_QUESTIONS["common"], 2))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["experience"], 1))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["situational"], 1))
    elif count <= 6:
        questions.extend(random.sample(INTERVIEW_QUESTIONS["common"], 2))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["experience"], 1))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["situational"], 2))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["personality"], 1))
    else:
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

    # 항공사별 평가 기준 추가
    airline_criteria = ""
    if AIRLINE_QUESTIONS_AVAILABLE and airline in AIRLINE_VALUES:
        values = AIRLINE_VALUES[airline]
        인재상 = values.get("인재상", [])
        keywords = values.get("keywords", [])
        if 인재상:
            airline_criteria = f"\n\n이 항공사의 인재상: {', '.join(인재상)}"
        if keywords:
            airline_criteria += f"\n핵심 키워드: {', '.join(keywords)}"

    system_prompt = f"""당신은 엄격한 항공사 면접관입니다.
음성 평가와 내용 평가를 종합하여 최종 피드백을 제공하세요.
해당 항공사의 인재상과 핵심가치에 맞는지도 평가해주세요.{airline_criteria}
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

#### {airline} 인재상 부합도
(해당 항공사의 인재상/핵심가치와 얼마나 맞는지 평가)

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

    # 항공사 핵심가치 표시
    if airline in AIRLINE_VALUE_SUMMARY:
        st.info(f"**{airline} 핵심가치**\n\n{AIRLINE_VALUE_SUMMARY[airline]}")

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

    # 시작 버튼
    if st.button("모의면접 시작", type="primary", use_container_width=True):
        # 사용량 체크

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
        # 음성 분석용 변수 초기화
        st.session_state.mock_audio_bytes_list = []
        st.session_state.mock_combined_voice_analysis = None
        st.session_state.mock_processed_audio_id = None
        st.session_state.mock_response_times = []
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

        # 타이머 시작 (음성 모드에서도 시간 측정)
        if st.session_state.answer_start_time is None:
            st.session_state.answer_start_time = time.time()

        # 경과 시간 표시
        elapsed_display = int(time.time() - st.session_state.answer_start_time) if st.session_state.answer_start_time else 0
        timer_color = "#28a745" if elapsed_display < 60 else "#ffc107" if elapsed_display < 90 else "#dc3545"
        st.markdown(f"""
        <div style="text-align: center; margin: 15px 0;">
            <div style="font-size: 36px; font-weight: bold; color: {timer_color};">
                ⏱️ {elapsed_display // 60:02d}:{elapsed_display % 60:02d}
            </div>
            <div style="font-size: 12px; color: #666;">적정 답변 시간: 60~90초</div>
        </div>
        """, unsafe_allow_html=True)

        # 음성 녹음 (st.audio_input 사용 - 롤플레잉과 동일)
        col_rec1, col_rec2 = st.columns([2, 1])

        with col_rec1:
            try:
                # 처리된 오디오 ID 추적 (중복 처리 방지)
                if "mock_processed_audio_id" not in st.session_state:
                    st.session_state.mock_processed_audio_id = None

                audio_data = st.audio_input("🎤 녹음 버튼을 클릭하고 답변하세요", key=f"voice_input_{current_idx}")

                if audio_data:
                    # 오디오 ID로 중복 체크
                    audio_id = f"{audio_data.name}_{audio_data.size}"

                    if audio_id != st.session_state.mock_processed_audio_id:
                        with st.spinner("🔊 음성 인식 중..."):
                            # 음성 데이터 읽기
                            audio_bytes = audio_data.read()

                            # STT (음성 → 텍스트)
                            result = transcribe_audio(audio_bytes, language="ko")

                            if result and result.get("text"):
                                transcribed_text = result["text"]
                                st.success(f"✅ 인식됨: {transcribed_text[:100]}{'...' if len(transcribed_text) > 100 else ''}")

                                # 응답 시간 계산
                                elapsed = int(time.time() - st.session_state.answer_start_time) if st.session_state.answer_start_time else 60

                                # 음성 데이터 저장 (종합 분석용)
                                st.session_state.mock_audio_bytes_list.append(audio_bytes)
                                st.session_state.mock_response_times.append(elapsed)

                                # 개별 음성 분석
                                try:
                                    voice_analysis = analyze_voice_quality(result, expected_duration_range=(30, 90))
                                except Exception as e:
                                    voice_analysis = {"total_score": 70, "error": str(e)}

                                # 내용 분석
                                if VIDEO_UTILS_AVAILABLE:
                                    content_analysis = evaluate_answer_content(
                                        question, transcribed_text, airline, airline_type
                                    )
                                else:
                                    content_analysis = {"total_score": 0, "error": "분석 불가"}

                                # 세션에 저장
                                st.session_state.mock_answers.append(transcribed_text)
                                st.session_state.mock_transcriptions.append(result)
                                st.session_state.mock_times.append(elapsed)
                                st.session_state.mock_voice_analyses.append(voice_analysis)
                                st.session_state.mock_content_analyses.append(content_analysis)

                                # 처리 완료 표시
                                st.session_state.mock_processed_audio_id = audio_id
                                st.session_state.answer_start_time = None  # 타이머 리셋

                                # 다음 질문으로
                                if current_idx + 1 >= total:
                                    st.session_state.mock_completed = True
                                else:
                                    st.session_state.mock_current_idx += 1
                                    st.session_state.mock_processed_audio_id = None  # 다음 질문용 리셋

                                st.rerun()
                            else:
                                st.error("❌ 음성 인식 실패 - 다시 녹음하거나 아래 텍스트로 입력하세요")
                                st.session_state.mock_processed_audio_id = audio_id
            except Exception as e:
                st.warning(f"음성 입력 기능을 사용할 수 없습니다: {e}")

        with col_rec2:
            st.markdown("""
            **💡 녹음 팁**
            - 🎙️ 마이크 아이콘 클릭 → 답변 → 정지
            - 조용한 환경에서 녹음
            - 60~90초 내 답변 권장
            """)

        st.divider()

        # 텍스트 폴백 (음성 인식 실패 시)
        with st.expander("📝 텍스트로 직접 입력하기"):
            fallback_answer = st.text_area(
                "음성 인식이 안 될 경우 여기에 입력하세요",
                height=150,
                key=f"fallback_{current_idx}"
            )

            if st.button("텍스트 답변 제출", type="secondary", use_container_width=True):
                if fallback_answer.strip():
                    elapsed = int(time.time() - st.session_state.answer_start_time) if st.session_state.answer_start_time else 60

                    # 텍스트 모드는 음성 분석 없음
                    voice_analysis = {"total_score": 0, "note": "텍스트 입력 (음성 분석 없음)"}

                    # 내용 분석
                    if VIDEO_UTILS_AVAILABLE:
                        with st.spinner("답변 분석 중..."):
                            content_analysis = evaluate_answer_content(
                                question, fallback_answer.strip(), airline, airline_type
                            )
                    else:
                        content_analysis = {"total_score": 0, "error": "분석 불가"}

                    st.session_state.mock_answers.append(fallback_answer.strip())
                    st.session_state.mock_times.append(elapsed)
                    st.session_state.mock_voice_analyses.append(voice_analysis)
                    st.session_state.mock_content_analyses.append(content_analysis)
                    st.session_state.answer_start_time = None

                    if current_idx + 1 >= total:
                        st.session_state.mock_completed = True
                    else:
                        st.session_state.mock_current_idx += 1

                    st.rerun()
                else:
                    st.warning("답변을 입력해주세요.")

        # 패스 버튼
        st.divider()
        if st.button("⏭️ 이 질문 패스", use_container_width=True):
            st.session_state.mock_answers.append("[답변 못함]")
            st.session_state.mock_times.append(0)
            st.session_state.mock_voice_analyses.append({"total_score": 0})
            st.session_state.mock_content_analyses.append({"total_score": 0})
            st.session_state.answer_start_time = None

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

    # 종합 음성 분석 수행 (음성 모드이고, 음성 데이터가 있는 경우)
    if st.session_state.mock_mode == "voice" and st.session_state.mock_audio_bytes_list and VIDEO_UTILS_AVAILABLE:
        if st.session_state.mock_combined_voice_analysis is None:
            try:
                with st.spinner("🎤 종합 음성 분석 중..."):
                    # 모든 음성 데이터 합쳐서 분석
                    combined_audio = b''.join(st.session_state.mock_audio_bytes_list)
                    voice_result = analyze_voice_complete(
                        combined_audio,
                        response_times=st.session_state.mock_response_times
                    )
                    st.session_state.mock_combined_voice_analysis = voice_result
            except Exception as e:
                st.session_state.mock_combined_voice_analysis = {"error": str(e)}

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
            # 종합 음성 분석 결과 표시
            voice_analysis = st.session_state.mock_combined_voice_analysis

            if voice_analysis and "error" not in voice_analysis:
                # 종합 점수 표시
                total_score = voice_analysis.get("total_score", 0)
                grade = voice_analysis.get("grade", "N/A")

                grade_colors = {"S": "#FFD700", "A": "#4CAF50", "B": "#2196F3", "C": "#FF9800", "D": "#F44336"}
                grade_color = grade_colors.get(grade, "#666")

                st.markdown(f"""
                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #1e3a5f, #2d5a87); border-radius: 15px; margin-bottom: 20px;">
                    <div style="font-size: 48px; font-weight: bold; color: {grade_color};">{grade}</div>
                    <div style="font-size: 24px; color: #fff;">{total_score}/100점</div>
                    <div style="font-size: 14px; color: #ccc; margin-top: 10px;">{voice_analysis.get('summary', '')}</div>
                </div>
                """, unsafe_allow_html=True)

                # 텍스트 분석 (말 속도, 필러, 휴지, 발음)
                st.subheader("📝 텍스트 분석")
                text_analysis = voice_analysis.get("text_analysis", {})

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    rate = text_analysis.get("speech_rate", {})
                    st.metric("말 속도", f"{rate.get('wpm', 0)} WPM", help="적정: 120-150 WPM")
                    st.progress(min(rate.get("score", 0) / 10, 1.0))
                    st.caption(rate.get("feedback", ""))

                with col2:
                    filler = text_analysis.get("filler_words", {})
                    st.metric("필러 단어", f"{filler.get('count', 0)}개", help="음, 어, 그 등")
                    st.progress(min(filler.get("score", 0) / 10, 1.0))
                    st.caption(filler.get("feedback", ""))

                with col3:
                    pauses = text_analysis.get("pauses", {})
                    st.metric("긴 휴지", f"{pauses.get('long_pauses', 0)}회", help="2초 이상 멈춤")
                    st.progress(min(pauses.get("score", 0) / 10, 1.0))
                    st.caption(pauses.get("feedback", ""))

                with col4:
                    clarity = text_analysis.get("clarity", {})
                    st.metric("발음 명확도", f"{clarity.get('score', 0)}/10")
                    st.progress(min(clarity.get("score", 0) / 10, 1.0))
                    st.caption(clarity.get("feedback", ""))

                st.divider()

                # 음성 분석 (떨림, 말끝, 억양, 서비스톤)
                st.subheader("🎤 음성 전달력 분석")
                voice_detail = voice_analysis.get("voice_analysis", {})

                col1, col2 = st.columns(2)

                with col1:
                    tremor = voice_detail.get("tremor", {})
                    st.markdown(f"**목소리 떨림**: {tremor.get('level', 'N/A')}")
                    st.progress(min(tremor.get("score", 0) / 10, 1.0))
                    st.caption(tremor.get("feedback", ""))

                    pitch = voice_detail.get("pitch_variation", {})
                    st.markdown(f"**억양 변화**: {pitch.get('type', 'N/A')}")
                    st.progress(min(pitch.get("score", 0) / 10, 1.0))
                    st.caption(pitch.get("feedback", ""))

                with col2:
                    ending = voice_detail.get("ending_clarity", {})
                    st.markdown(f"**말끝 처리**: {ending.get('issue', 'N/A')}")
                    st.progress(min(ending.get("score", 0) / 10, 1.0))
                    st.caption(ending.get("feedback", ""))

                    service = voice_detail.get("service_tone", {})
                    st.markdown(f"**서비스 톤**: {'밝음' if service.get('greeting_bright') else '개선 필요'}")
                    st.progress(min(service.get("score", 0) / 10, 1.0))
                    st.caption(service.get("feedback", ""))

                # 응답 시간 분석
                rt_analysis = voice_analysis.get("response_time_analysis", {})
                if rt_analysis:
                    st.divider()
                    st.subheader("⏱️ 응답 시간 분석")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("평균 응답 시간", f"{rt_analysis.get('avg_time', 0):.1f}초")
                    with col2:
                        st.metric("응답 시간 점수", f"{rt_analysis.get('score', 0)}/10")
                    with col3:
                        st.caption(rt_analysis.get("feedback", ""))

                # 개선 포인트
                improvements = voice_analysis.get("top_improvements", [])
                if improvements:
                    st.divider()
                    st.subheader("🎯 우선 개선 포인트")
                    for i, imp in enumerate(improvements, 1):
                        st.markdown(f"{i}. {imp}")

            elif voice_analysis and "error" in voice_analysis:
                st.warning(f"음성 분석 오류: {voice_analysis.get('error')}")

            elif not st.session_state.mock_audio_bytes_list:
                st.info("💡 음성 모드로 녹음한 데이터가 없습니다. 텍스트 입력을 사용한 경우 음성 분석이 제공되지 않습니다.")

            # 질문별 음성 분석 (개별)
            st.divider()
            st.subheader("📋 질문별 음성 분석")
            for i, voice in enumerate(st.session_state.mock_voice_analyses, 1):
                if voice and voice.get("total_score", 0) > 0:
                    with st.expander(f"질문 {i} 음성 분석", expanded=False):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("말 속도", f"{voice.get('speech_rate', {}).get('wpm', 0)} WPM")
                            st.caption(voice.get('speech_rate', {}).get('feedback', ''))

                        with col2:
                            st.metric("필러 단어", f"{voice.get('filler_words', {}).get('count', 0)}개")
                            st.caption(voice.get('filler_words', {}).get('feedback', ''))

                        with col3:
                            st.metric("음성 점수", f"{voice.get('total_score', 0)}/100")

        else:
            st.info("텍스트 모드에서는 음성 평가가 제공되지 않습니다. 음성 모드로 면접을 진행하면 상세한 음성 분석을 받을 수 있습니다.")

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

    # =====================
    # PDF 리포트 다운로드
    # =====================
    if REPORT_AVAILABLE:
        st.divider()
        st.subheader("📄 리포트 다운로드")

        col_pdf1, col_pdf2 = st.columns([2, 1])
        with col_pdf1:
            st.caption("면접 결과를 PDF로 저장하여 나중에 확인하거나 멘토에게 공유할 수 있습니다.")
        with col_pdf2:
            try:
                pdf_bytes = generate_mock_interview_report(
                    airline=st.session_state.mock_airline,
                    questions=st.session_state.mock_questions,
                    answers=st.session_state.mock_answers,
                    times=st.session_state.mock_times,
                    voice_analyses=st.session_state.mock_voice_analyses,
                    content_analyses=st.session_state.mock_content_analyses,
                    combined_voice_analysis=st.session_state.mock_combined_voice_analysis,
                    evaluation_result=st.session_state.mock_evaluation,
                )
                filename = get_mock_interview_report_filename(st.session_state.mock_airline)

                st.download_button(
                    label="📥 PDF 다운로드",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
            except Exception as e:
                st.error(f"PDF 생성 오류: {e}")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("다시 도전하기", type="primary", use_container_width=True):
            st.session_state.mock_started = False
            st.session_state.mock_evaluation = None
            # 음성 분석 변수도 초기화
            st.session_state.mock_audio_bytes_list = []
            st.session_state.mock_combined_voice_analysis = None
            st.session_state.mock_processed_audio_id = None
            st.session_state.mock_response_times = []
            st.rerun()

    with col2:
        if st.button("처음으로", use_container_width=True):
            for key in defaults:
                st.session_state[key] = defaults[key]
            st.rerun()

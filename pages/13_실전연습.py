# pages/13_실전연습.py
# 실전 면접 연습 - 동영상으로 답변 + 음성/표정/내용 종합 분석

import streamlit as st
import streamlit.components.v1 as components
import os
import sys
import json
import base64
import random
import tempfile
import requests
from typing import Optional, Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import AIRLINES, AIRLINE_TYPE
from auth_utils import check_tester_password
from env_config import OPENAI_API_KEY

st.set_page_config(page_title="실전 면접 연습", page_icon="🎯", layout="wide")

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="실전연습")
except ImportError:
    pass

st.markdown('<meta name="google" content="notranslate"><style>html{translate:no;}</style>', unsafe_allow_html=True)
st.markdown('<div translate="no" class="notranslate">', unsafe_allow_html=True)

# 비밀번호
check_tester_password()

# API
OPENAI_API_URL = "https://api.openai.com/v1"

# 동영상 모듈
try:
    from video_recorder import get_video_recorder_html, extract_frames_from_video, extract_audio_from_video, check_ffmpeg_available
    VIDEO_AVAILABLE = True
except ImportError:
    VIDEO_AVAILABLE = False

# 질문
INTERVIEW_QUESTIONS = {
    "common": ["간단하게 자기소개 해주세요.", "왜 승무원이 되고 싶으신가요?", "저희 항공사에 왜 지원하셨나요?", "본인의 강점과 약점을 말씀해주세요.", "승무원에게 가장 중요한 자질은 무엇이라고 생각하시나요?"],
    "experience": ["팀워크를 발휘했던 경험을 말씀해주세요.", "어려운 고객을 응대한 경험이 있나요?", "갈등을 해결했던 경험을 말씀해주세요.", "실패했던 경험과 그로부터 배운 점은 무엇인가요?", "리더십을 발휘한 경험을 말씀해주세요."],
    "situational": ["기내에서 승객이 쓰러지면 어떻게 하시겠습니까?", "승객이 무리한 요구를 하면 어떻게 대응하시겠습니까?", "동료와 의견 충돌이 생기면 어떻게 하시겠습니까?", "안전규정을 거부하는 승객을 어떻게 설득하시겠습니까?"],
    "personality": ["스트레스를 어떻게 관리하시나요?", "주변에서 본인을 어떻게 평가하나요?", "10년 후 본인의 모습은 어떨 것 같나요?", "왜 다른 직업이 아닌 승무원인가요?"],
}
QUESTION_CATEGORIES = {"common": "기본 질문", "experience": "경험 질문", "situational": "상황 대처", "personality": "인성 질문"}

# 세션
for k, v in {"practice_started": False, "question": None, "category": None, "airline": "", "result": None, "history": []}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# API 함수들
def transcribe_audio(audio_bytes: bytes) -> Optional[Dict]:
    if not OPENAI_API_KEY:
        return None

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio_bytes)
        path = f.name

    try:
        with open(path, "rb") as af:
            r = requests.post(
                f"{OPENAI_API_URL}/audio/transcriptions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                files={"file": ("audio.mp3", af, "audio/mp3")},
                data={"model": "whisper-1", "language": "ko", "response_format": "verbose_json"},
                timeout=60
            )
            r.raise_for_status()
            res = r.json()
            return {"text": res.get("text", ""), "duration": res.get("duration", 0)}
    except Exception as e:
        st.error(f"음성 인식 오류: {e}")
        return None
    finally:
        os.unlink(path) if os.path.exists(path) else None


def analyze_voice(transcription: Dict) -> Dict:
    import re
    text, duration = transcription.get("text", ""), transcription.get("duration", 0)

    # 말 속도
    wpm = int((len(text.split()) / max(duration, 1)) * 60) if duration > 0 else 0
    if 120 <= wpm <= 160:
        rate = {"wpm": wpm, "score": 10, "feedback": "적절한 속도"}
    elif wpm < 100:
        rate = {"wpm": wpm, "score": 4, "feedback": "너무 느립니다"}
    elif wpm > 180:
        rate = {"wpm": wpm, "score": 4, "feedback": "너무 빠릅니다"}
    else:
        rate = {"wpm": wpm, "score": 7, "feedback": "약간 조절 필요"}

    # 추임새
    filler = sum(len(re.findall(p, text, re.I)) for p in [r'\b음+\b', r'\b어+\b', r'\b그+\b', r'\b약간\b', r'\b그냥\b'])
    filler_score = 10 if filler <= 3 else (7 if filler <= 6 else 4)

    # 시간
    if 30 <= duration <= 90:
        dur = {"seconds": int(duration), "score": 10, "feedback": "적절한 시간"}
    elif duration < 15:
        dur = {"seconds": int(duration), "score": 3, "feedback": "너무 짧습니다"}
    else:
        dur = {"seconds": int(duration), "score": 6, "feedback": "시간 조절 필요"}

    total = int((rate["score"] + filler_score + dur["score"]) / 3 * 10)
    return {"speech_rate": rate, "filler": {"count": filler, "score": filler_score}, "duration": dur, "total_score": total}


def analyze_content(question: str, answer: str, airline: str, atype: str) -> Dict:
    if not OPENAI_API_KEY or not answer:
        return {"error": "API 키가 없거나 답변이 비어있습니다."}

    prompt = f"""항공사 면접관입니다. {airline}({atype}) 지원자 답변을 평가하세요.
JSON만 응답: {{"content_score": 0-40, "content_feedback": "...", "structure_score": 0-30, "structure_feedback": "...", "relevance_score": 0-30, "relevance_feedback": "...", "strengths": ["..."], "improvements": ["..."], "sample_answer": "..."}}"""

    try:
        r = requests.post(f"{OPENAI_API_URL}/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": f"질문: {question}\n답변: {answer}"}], "temperature": 0.3, "response_format": {"type": "json_object"}},
            timeout=30)

        # 안전한 응답 파싱
        if r.status_code != 200:
            return {"error": f"API 오류 (HTTP {r.status_code})"}

        data = r.json()
        choices = data.get("choices", [])
        if not choices:
            return {"error": "API 응답이 비어있습니다."}

        content = choices[0].get("message", {}).get("content", "")
        if not content:
            return {"error": "API 응답 내용이 없습니다."}

        res = json.loads(content)
        res["total_score"] = res.get("content_score", 0) + res.get("structure_score", 0) + res.get("relevance_score", 0)
        return res
    except json.JSONDecodeError as e:
        return {"error": f"JSON 파싱 오류: {e}"}
    except requests.Timeout:
        return {"error": "요청 시간 초과. 다시 시도해주세요."}
    except requests.ConnectionError:
        return {"error": "인터넷 연결을 확인해주세요."}
    except Exception as e:
        return {"error": str(e)}


def analyze_expression(frames: List[str], context: str) -> Optional[Dict]:
    if not OPENAI_API_KEY or not frames:
        st.warning("API 키가 없거나 프레임이 없습니다.")
        return None

    prompt = """면접 코칭 전문가입니다. 프레임들의 표정/자세를 분석하세요.
JSON만 응답: {"expression": {"score": 1-10, "smile": "좋음/보통/부족", "feedback": "..."}, "posture": {"score": 1-10, "feedback": "..."}, "impression": {"score": 1-10, "confidence": "높음/보통/낮음", "feedback": "..."}, "time_analysis": {"start": "...", "end": "...", "feedback": "..."}, "overall_score": 1-100, "strengths": ["..."], "improvements": ["..."]}"""

    msg_content = [{"type": "text", "text": f"{context} 면접 동영상 프레임입니다. 분석해주세요."}]
    for f in frames[:5]:
        msg_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{f}", "detail": "low"}})

    try:
        r = requests.post(f"{OPENAI_API_URL}/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": "gpt-4o", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": msg_content}], "temperature": 0.3, "max_tokens": 1500},
            timeout=90)

        # 안전한 응답 파싱
        if r.status_code != 200:
            st.error(f"표정 분석 API 오류 (HTTP {r.status_code})")
            return None

        data = r.json()
        choices = data.get("choices", [])
        if not choices:
            st.error("표정 분석 API 응답이 비어있습니다.")
            return None

        c = choices[0].get("message", {}).get("content", "")
        if not c:
            st.error("표정 분석 결과가 없습니다.")
            return None

        # JSON 추출
        if "```json" in c:
            c = c.split("```json")[1].split("```")[0]
        return json.loads(c.strip())

    except json.JSONDecodeError as e:
        st.error(f"표정 분석 결과 파싱 오류: {e}")
        return None
    except requests.Timeout:
        st.error("표정 분석 요청 시간 초과. 다시 시도해주세요.")
        return None
    except requests.ConnectionError:
        st.error("인터넷 연결을 확인해주세요.")
        return None
    except Exception as e:
        st.error(f"표정 분석 오류: {e}")
        return None


def calc_total(voice: Dict, content: Dict, expr: Dict) -> Dict:
    v = voice.get("total_score", 0) if voice else 0
    c = content.get("total_score", 0) if content and not content.get("error") else 0
    e = expr.get("overall_score", 0) if expr else 0

    total = int(c * 0.5 + e * 0.3 + v * 0.2)

    if total >= 85:
        return {"total_score": total, "grade": "S", "grade_text": "탁월함", "color": "#667eea", "breakdown": {"voice": v, "content": c, "expression": e}}
    elif total >= 75:
        return {"total_score": total, "grade": "A", "grade_text": "우수", "color": "#28a745", "breakdown": {"voice": v, "content": c, "expression": e}}
    elif total >= 65:
        return {"total_score": total, "grade": "B", "grade_text": "양호", "color": "#17a2b8", "breakdown": {"voice": v, "content": c, "expression": e}}
    elif total >= 50:
        return {"total_score": total, "grade": "C", "grade_text": "보통", "color": "#ffc107", "breakdown": {"voice": v, "content": c, "expression": e}}
    else:
        return {"total_score": total, "grade": "D", "grade_text": "개선필요", "color": "#dc3545", "breakdown": {"voice": v, "content": c, "expression": e}}


def get_directions(voice: Dict, content: Dict, expr: Dict) -> List[str]:
    d = []
    if voice and voice.get("speech_rate", {}).get("score", 10) < 7:
        d.append(f"🎤 **말 속도**: {voice['speech_rate'].get('feedback', '')}")
    if content and not content.get("error"):
        for i in content.get("improvements", [])[:2]:
            d.append(f"📝 {i}")
    if expr and expr.get("expression", {}).get("score", 10) < 7:
        d.append(f"😊 **표정**: {expr['expression'].get('feedback', '')}")
    if len(d) < 3:
        d.extend(["🎯 핵심 키워드를 정리하고 답변하세요.", "👀 카메라를 바라보며 답변하세요."])
    return d[:5]


# ========================================
# 메인
# ========================================

st.title("🎯 실전 면접 연습")
st.markdown("동영상으로 답변하고 **음성 + 표정 + 내용** 종합 분석!")

if not OPENAI_API_KEY:
    st.error("OpenAI API 키가 필요합니다.")
    st.stop()

st.markdown("---")

if not st.session_state.practice_started:
    # 설정
    st.markdown("### ✈️ 연습 설정")
    c1, c2 = st.columns(2)
    with c1:
        airline = st.selectbox("항공사", AIRLINES, format_func=lambda x: f"{x} ({AIRLINE_TYPE.get(x, 'LCC')})")
    with c2:
        cat = st.selectbox("질문 유형", list(QUESTION_CATEGORIES.keys()), format_func=lambda x: QUESTION_CATEGORIES[x])

    st.markdown("---")
    st.markdown("### 📋 질문 예시")
    for i, q in enumerate(INTERVIEW_QUESTIONS[cat][:3], 1):
        st.caption(f"{i}. {q}")

    if st.button("🚀 연습 시작", type="primary", use_container_width=True):
        st.session_state.question = random.choice(INTERVIEW_QUESTIONS[cat])
        st.session_state.category = cat
        st.session_state.airline = airline
        st.session_state.practice_started = True
        st.session_state.result = None
        st.rerun()

else:
    q = st.session_state.question
    airline = st.session_state.airline
    atype = AIRLINE_TYPE.get(airline, "LCC")

    # 질문 표시
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 20px; padding: 30px; margin-bottom: 30px;">
        <div style="font-size: 14px; opacity: 0.8;">{airline} ({atype}) | {QUESTION_CATEGORIES.get(st.session_state.category, '')}</div>
        <div style="font-size: 24px; font-weight: bold; margin-top: 10px;">"{q}"</div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.result:
        # 동영상 녹화
        st.markdown("### 🎬 동영상으로 답변하기")
        st.info("💡 질문을 읽고, 카메라를 보며 답변하세요. 녹화 완료 후 '영상 저장' → 업로드")

        if VIDEO_AVAILABLE:
            components.html(get_video_recorder_html(duration=60), height=720)

        st.markdown("---")

        # 업로드
        st.markdown("### 📤 녹화한 영상 업로드")
        video_file = st.file_uploader("영상 파일 업로드", type=["webm", "mp4", "mov"], key="video")

        if video_file:
            st.video(video_file)
            st.success("✅ 영상 업로드됨")

            if st.button("🔍 분석하기", type="primary", use_container_width=True):
                with st.spinner("🤖 종합 분석 중... (1-2분 소요)"):
                    video_bytes = video_file.getvalue()

                    # 1. 프레임 추출
                    st.info("📽️ 동영상에서 프레임 추출 중...")
                    frames = []
                    if VIDEO_AVAILABLE and check_ffmpeg_available():
                        frames = extract_frames_from_video(video_bytes, num_frames=5)
                        if frames:
                            st.success(f"✅ {len(frames)}개 프레임 추출")
                    else:
                        st.warning("ffmpeg 미설치로 프레임 추출 불가")

                    # 2. 오디오 추출
                    st.info("🎤 동영상에서 음성 추출 중...")
                    audio_bytes = None
                    if VIDEO_AVAILABLE and check_ffmpeg_available():
                        audio_bytes = extract_audio_from_video(video_bytes)
                        if audio_bytes:
                            st.success("✅ 음성 추출 완료")
                    else:
                        st.warning("ffmpeg 미설치로 음성 추출 불가")

                    # 3. 음성 분석
                    voice_analysis = {}
                    answer_text = ""
                    if audio_bytes:
                        st.info("🎤 음성 인식 중...")
                        transcription = transcribe_audio(audio_bytes)
                        if transcription and transcription.get("text"):
                            answer_text = transcription["text"]
                            st.success("✅ 음성 인식 완료")
                            voice_analysis = analyze_voice(transcription)

                    # 4. 내용 분석
                    content_analysis = {}
                    if answer_text:
                        st.info("📝 답변 내용 분석 중...")
                        content_analysis = analyze_content(q, answer_text, airline, atype)
                        if not content_analysis.get("error"):
                            st.success("✅ 내용 분석 완료")

                    # 5. 표정 분석
                    expr_analysis = {}
                    if frames:
                        st.info("😊 표정/자세 분석 중...")
                        expr_analysis = analyze_expression(frames, f"{airline} {atype}")
                        if expr_analysis:
                            st.success("✅ 표정 분석 완료")

                    # 6. 종합
                    total = calc_total(voice_analysis, content_analysis, expr_analysis)
                    directions = get_directions(voice_analysis, content_analysis, expr_analysis)

                    st.session_state.result = {
                        "question": q,
                        "answer": answer_text,
                        "voice": voice_analysis,
                        "content": content_analysis,
                        "expression": expr_analysis,
                        "total": total,
                        "directions": directions,
                    }
                    st.session_state.history.append(st.session_state.result)
                    st.rerun()

    else:
        # 결과 표시
        r = st.session_state.result
        t = r["total"]

        st.markdown("### 📊 종합 분석 결과")
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {t['color']}20, {t['color']}10); border: 3px solid {t['color']}; border-radius: 25px; padding: 40px; text-align: center; margin-bottom: 30px;">
            <div style="font-size: 80px;">{t['grade']}</div>
            <div style="font-size: 48px; font-weight: bold; color: {t['color']};">{t['total_score']}점</div>
            <div style="font-size: 22px; color: #666;">{t['grade_text']}</div>
        </div>
        """, unsafe_allow_html=True)

        # 영역별 점수
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("📝 답변 내용 (50%)", f"{t['breakdown']['content']}점")
        with c2:
            st.metric("😊 표정/자세 (30%)", f"{t['breakdown']['expression']}점")
        with c3:
            st.metric("🎤 음성 전달 (20%)", f"{t['breakdown']['voice']}점")

        # 인식된 답변
        if r.get("answer"):
            st.markdown("### 🎤 인식된 답변")
            st.markdown(f"""<div style="background: #f8f9fa; border-left: 4px solid #667eea; padding: 20px; border-radius: 0 10px 10px 0;">{r['answer']}</div>""", unsafe_allow_html=True)

        st.markdown("---")

        # 개선 방향
        st.markdown("### 🎯 개선 방향")
        for d in r.get("directions", []):
            st.markdown(d)

        st.markdown("---")

        # 상세 분석
        st.markdown("### 📋 상세 분석")
        tab1, tab2, tab3 = st.tabs(["📝 답변", "😊 표정", "🎤 음성"])

        with tab1:
            c = r.get("content", {})
            if c and not c.get("error"):
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("내용", f"{c.get('content_score', 0)}/40")
                    st.caption(c.get('content_feedback', ''))
                    st.metric("구조", f"{c.get('structure_score', 0)}/30")
                    st.caption(c.get('structure_feedback', ''))
                with c2:
                    for s in c.get("strengths", []):
                        st.success(f"✓ {s}")
                    for i in c.get("improvements", []):
                        st.warning(f"△ {i}")
                if c.get("sample_answer"):
                    st.info(f"💡 모범답변: {c['sample_answer']}")

        with tab2:
            e = r.get("expression", {})
            if e:
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("표정", f"{e.get('expression', {}).get('score', 0)}/10")
                    st.caption(e.get('expression', {}).get('feedback', ''))
                with c2:
                    st.metric("인상", f"{e.get('impression', {}).get('score', 0)}/10")
                    st.caption(e.get('impression', {}).get('feedback', ''))

        with tab3:
            v = r.get("voice", {})
            if v:
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("말 속도", f"{v.get('speech_rate', {}).get('wpm', 0)} WPM")
                with c2:
                    st.metric("추임새", f"{v.get('filler', {}).get('count', 0)}회")
                with c3:
                    st.metric("답변 시간", f"{v.get('duration', {}).get('seconds', 0)}초")

        st.markdown("---")

        # 버튼
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔄 같은 질문 다시"):
                st.session_state.result = None
                st.rerun()
        with c2:
            if st.button("➡️ 다음 질문"):
                st.session_state.question = random.choice(INTERVIEW_QUESTIONS[st.session_state.category])
                st.session_state.result = None
                st.rerun()
        with c3:
            if st.button("🏠 처음으로"):
                st.session_state.practice_started = False
                st.session_state.result = None
                st.rerun()

# 기록
if st.session_state.history:
    st.markdown("---")
    with st.expander(f"📊 연습 기록 ({len(st.session_state.history)}회)"):
        scores = [h["total"]["total_score"] for h in st.session_state.history]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("평균", f"{sum(scores)/len(scores):.0f}점")
        with c2:
            st.metric("최고", f"{max(scores)}점")
        with c3:
            st.metric("횟수", f"{len(scores)}회")

st.markdown('</div>', unsafe_allow_html=True)

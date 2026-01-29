# pages/13_실전연습.py
# 실전 면접 연습 - 동영상/텍스트 답변 + 음성/표정/내용 종합 분석
# 기능: 꼬리질문, 연속질문모드, 누적기록, 텍스트모드, 답변리라이트

import streamlit as st
import os
import sys
import json
import base64
import random
import tempfile
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import AIRLINES, AIRLINE_TYPE
from env_config import OPENAI_API_KEY

from sidebar_common import init_page, end_page

init_page(
    title="실전 면접 연습",
    current_page="실전연습",
    wide_layout=True
)


st.markdown("""
<meta name="google" content="notranslate">
<meta http-equiv="Content-Language" content="ko">
<style>
html, body, .stApp, .main, [data-testid="stAppViewContainer"] {
    translate: no !important;
}
.notranslate, [translate="no"] {
    translate: no !important;
}
</style>
""", unsafe_allow_html=True)
st.markdown('<div translate="no" class="notranslate" lang="ko">', unsafe_allow_html=True)

# API
OPENAI_API_URL = "https://api.openai.com/v1"

# 누적 기록 파일 경로
HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "practice_history.json")


# 질문 DB (확장)
INTERVIEW_QUESTIONS = {
    "common": [
        "간단하게 자기소개 해주세요.",
        "왜 승무원이 되고 싶으신가요?",
        "저희 항공사에 왜 지원하셨나요?",
        "본인의 강점과 약점을 말씀해주세요.",
        "승무원에게 가장 중요한 자질은 무엇이라고 생각하시나요?",
        "지원 전 어떤 준비를 하셨나요?",
        "본인만의 서비스 철학이 있다면 말씀해주세요.",
        "이 직업을 통해 이루고 싶은 목표는 무엇인가요?",
    ],
    "experience": [
        "팀워크를 발휘했던 경험을 말씀해주세요.",
        "어려운 고객을 응대한 경험이 있나요?",
        "갈등을 해결했던 경험을 말씀해주세요.",
        "실패했던 경험과 그로부터 배운 점은 무엇인가요?",
        "리더십을 발휘한 경험을 말씀해주세요.",
        "서비스업에서 감동을 받았던 경험이 있나요?",
        "예상치 못한 상황에 대처한 경험을 말씀해주세요.",
        "다문화 환경에서 소통한 경험이 있나요?",
    ],
    "situational": [
        "기내에서 승객이 쓰러지면 어떻게 하시겠습니까?",
        "승객이 무리한 요구를 하면 어떻게 대응하시겠습니까?",
        "동료와 의견 충돌이 생기면 어떻게 하시겠습니까?",
        "안전규정을 거부하는 승객을 어떻게 설득하시겠습니까?",
        "비행 중 난기류가 발생하면 어떻게 승객을 안심시키겠습니까?",
        "만취 승객이 다른 승객에게 불쾌감을 주면 어떻게 하시겠습니까?",
        "기내에서 승객 간 다툼이 발생하면 어떻게 중재하시겠습니까?",
        "갓난아이를 동반한 승객이 도움을 요청하면 어떻게 하시겠습니까?",
    ],
    "personality": [
        "스트레스를 어떻게 관리하시나요?",
        "주변에서 본인을 어떻게 평가하나요?",
        "10년 후 본인의 모습은 어떨 것 같나요?",
        "왜 다른 직업이 아닌 승무원인가요?",
        "본인이 가장 소중하게 생각하는 가치는 무엇인가요?",
        "체력 관리는 어떻게 하고 계신가요?",
        "외국어 능력은 어느 정도이며, 어떻게 준비하셨나요?",
        "불규칙한 근무에 대해 어떻게 생각하시나요?",
    ],
}
QUESTION_CATEGORIES = {"common": "기본 질문", "experience": "경험 질문", "situational": "상황 대처", "personality": "인성 질문"}


# ========================================
# 누적 기록 관리
# ========================================
def load_history() -> List[Dict]:
    try:
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_history(history: List[Dict]):
    try:
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.warning(f"기록 저장 실패: {e}")


# ========================================
# 세션 초기화
# ========================================
DEFAULT_STATE = {
    "practice_started": False,
    "practice_mode": "single",
    "answer_mode": "text",
    "question": None,
    "category": None,
    "airline": "",
    "result": None,
    "history": [],
    "continuous_questions": [],
    "continuous_results": [],
    "continuous_index": 0,
    "continuous_count": 3,
    "continuous_done": False,
    "followup_question": None,
    "followup_result": None,
    "followup_depth": 0,
}
for k, v in DEFAULT_STATE.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "persistent_history" not in st.session_state:
    st.session_state.persistent_history = load_history()


# ========================================
# API 함수들
# ========================================
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
        if os.path.exists(path):
            os.unlink(path)


def analyze_voice(transcription: Dict) -> Dict:
    import re
    text, duration = transcription.get("text", ""), transcription.get("duration", 0)
    wpm = int((len(text.split()) / max(duration, 1)) * 60) if duration > 0 else 0
    if 120 <= wpm <= 160:
        rate = {"wpm": wpm, "score": 10, "feedback": "적절한 속도"}
    elif wpm < 100:
        rate = {"wpm": wpm, "score": 4, "feedback": "너무 느립니다"}
    elif wpm > 180:
        rate = {"wpm": wpm, "score": 4, "feedback": "너무 빠릅니다"}
    else:
        rate = {"wpm": wpm, "score": 7, "feedback": "약간 조절 필요"}

    filler = sum(len(re.findall(p, text, re.I)) for p in [r'\b음+\b', r'\b어+\b', r'\b그+\b', r'\b약간\b', r'\b그냥\b'])
    filler_score = 10 if filler <= 3 else (7 if filler <= 6 else 4)

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
        if r.status_code != 200:
            return None
        data = r.json()
        choices = data.get("choices", [])
        if not choices:
            return None
        c = choices[0].get("message", {}).get("content", "")
        if not c:
            return None
        if "```json" in c:
            c = c.split("```json")[1].split("```")[0]
        return json.loads(c.strip())
    except Exception:
        return None


def generate_followup_question(question: str, answer: str, airline: str, depth: int = 0) -> Optional[str]:
    """답변 기반으로 꼬리질문 생성"""
    if not OPENAI_API_KEY or not answer:
        return None
    depth_context = ""
    if depth > 0:
        depth_context = f"이것은 {depth+1}번째 꼬리질문입니다. 이전 답변을 더 깊이 파고드세요."

    prompt = f"""당신은 {airline} 항공사 면접관입니다. 지원자의 답변을 듣고 꼬리질문을 해야 합니다.
{depth_context}

규칙:
- 지원자의 답변에서 구체적이지 않은 부분, 더 알고 싶은 부분을 파고드세요
- 답변의 진위를 확인하거나, 더 깊은 경험을 끌어내는 질문을 하세요
- 자연스러운 면접 대화처럼 한 문장으로 질문하세요
- 압박보다는 관심을 보이는 톤으로 질문하세요

질문만 출력하세요. 다른 설명 없이 질문 한 문장만."""

    try:
        r = requests.post(f"{OPENAI_API_URL}/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"원래 질문: {question}\n지원자 답변: {answer}"}
            ], "temperature": 0.7, "max_tokens": 200},
            timeout=15)
        if r.status_code != 200:
            return None
        data = r.json()
        choices = data.get("choices", [])
        if not choices:
            return None
        return choices[0].get("message", {}).get("content", "").strip().strip('"')
    except Exception:
        return None


def rewrite_answer(question: str, answer: str, airline: str, atype: str, feedback: Dict) -> Optional[str]:
    """유저 답변을 기반으로 개선된 버전 생성"""
    if not OPENAI_API_KEY or not answer:
        return None

    improvements = feedback.get("improvements", [])
    strengths = feedback.get("strengths", [])

    prompt = f"""당신은 항공사 면접 코치입니다. 지원자의 답변을 개선해주세요.

항공사: {airline} ({atype})
지원자의 강점: {', '.join(strengths)}
개선할 점: {', '.join(improvements)}

규칙:
- 지원자의 원래 경험과 내용을 최대한 살리면서 구조와 표현만 개선하세요
- STAR 기법(상황-과제-행동-결과)을 자연스럽게 적용하세요
- 60-90초 분량으로 작성하세요 (약 200-300자)
- 지원자의 개성을 유지하면서 면접에 적합한 톤으로 다듬으세요
- 개선된 답변만 출력하세요"""

    try:
        r = requests.post(f"{OPENAI_API_URL}/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"질문: {question}\n원래 답변: {answer}"}
            ], "temperature": 0.5, "max_tokens": 500},
            timeout=20)
        if r.status_code != 200:
            return None
        data = r.json()
        choices = data.get("choices", [])
        if not choices:
            return None
        return choices[0].get("message", {}).get("content", "").strip()
    except Exception:
        return None


def calc_total(voice: Dict, content: Dict, expr: Dict, mode: str = "text") -> Dict:
    v = voice.get("total_score", 0) if voice else 0
    c = content.get("total_score", 0) if content and not content.get("error") else 0

    if mode == "text":
        total = c
    else:
        total = int(c * 0.7 + v * 0.3)

    if total >= 85:
        return {"total_score": total, "grade": "S", "grade_text": "탁월함", "color": "#667eea", "breakdown": {"voice": v, "content": c}}
    elif total >= 75:
        return {"total_score": total, "grade": "A", "grade_text": "우수", "color": "#28a745", "breakdown": {"voice": v, "content": c}}
    elif total >= 65:
        return {"total_score": total, "grade": "B", "grade_text": "양호", "color": "#17a2b8", "breakdown": {"voice": v, "content": c}}
    elif total >= 50:
        return {"total_score": total, "grade": "C", "grade_text": "보통", "color": "#ffc107", "breakdown": {"voice": v, "content": c}}
    else:
        return {"total_score": total, "grade": "D", "grade_text": "개선필요", "color": "#dc3545", "breakdown": {"voice": v, "content": c}}


def get_directions(voice: Dict, content: Dict, expr: Dict) -> List[str]:
    d = []
    if voice and voice.get("speech_rate", {}).get("score", 10) < 7:
        d.append(f" **말 속도**: {voice['speech_rate'].get('feedback', '')}")
    if voice and voice.get("filler", {}).get("score", 10) < 7:
        d.append(f" **추임새**: '음', '어' 등을 줄여보세요.")
    if content and not content.get("error"):
        for i in content.get("improvements", [])[:2]:
            d.append(f" {i}")
    if len(d) < 3:
        d.extend([" 핵심 키워드를 정리하고 답변하세요.", "⏱️ 60~90초 내 답변을 완성하세요."])
    return d[:5]


def run_analysis(question: str, airline: str, atype: str, audio_bytes=None, text_answer: str = "", mode: str = "text") -> Dict:
    """통합 분석 실행"""
    voice_analysis = {}
    content_analysis = {}
    answer_text = text_answer

    if mode == "voice" and audio_bytes:
        st.info("음성 인식 중...")
        transcription = transcribe_audio(audio_bytes)
        if transcription and transcription.get("text"):
            answer_text = transcription["text"]
            voice_analysis = analyze_voice(transcription)

    if answer_text:
        st.info("내용 분석 중...")
        content_analysis = analyze_content(question, answer_text, airline, atype)

    total = calc_total(voice_analysis, content_analysis, {}, mode)
    directions = get_directions(voice_analysis, content_analysis, {})

    return {
        "question": question,
        "answer": answer_text,
        "voice": voice_analysis,
        "content": content_analysis,
        "total": total,
        "directions": directions,
        "mode": mode,
        "timestamp": datetime.now().isoformat(),
        "airline": airline,
    }


def display_result(r: Dict, show_followup: bool = True, show_rewrite: bool = True, key_prefix: str = ""):
    """결과 표시 공통 함수"""
    t = r["total"]

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {t['color']}20, {t['color']}10); border: 3px solid {t['color']}; border-radius: 25px; padding: 40px; text-align: center; margin-bottom: 30px;">
        <div style="font-size: 80px;">{t['grade']}</div>
        <div style="font-size: 48px; font-weight: bold; color: {t['color']};">{t['total_score']}점</div>
        <div style="font-size: 22px; color: #666;">{t['grade_text']}</div>
    </div>
    """, unsafe_allow_html=True)

    if r.get("mode") == "text":
        st.metric(" 답변 내용", f"{t['breakdown']['content']}점")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.metric(" 답변 내용 (70%)", f"{t['breakdown']['content']}점")
        with c2:
            st.metric(" 음성 전달 (30%)", f"{t['breakdown']['voice']}점")

    if r.get("answer"):
        st.markdown("#### 인식된 답변")
        st.markdown(f"""<div style="background: #f8f9fa; border-left: 4px solid #667eea; padding: 20px; border-radius: 0 10px 10px 0;">{r['answer']}</div>""", unsafe_allow_html=True)

    st.markdown("#### 개선 방향")
    for d in r.get("directions", []):
        st.markdown(d)

    # 상세 분석
    st.markdown("#### 상세 분석")
    content_data = r.get("content", {})
    if r.get("mode") == "text":
        if content_data and not content_data.get("error"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("내용", f"{content_data.get('content_score', 0)}/40")
                st.caption(content_data.get('content_feedback', ''))
                st.metric("구조", f"{content_data.get('structure_score', 0)}/30")
                st.caption(content_data.get('structure_feedback', ''))
                st.metric("관련성", f"{content_data.get('relevance_score', 0)}/30")
                st.caption(content_data.get('relevance_feedback', ''))
            with col2:
                for s in content_data.get("strengths", []):
                    st.success(f" {s}")
                for i in content_data.get("improvements", []):
                    st.warning(f"△ {i}")
            if content_data.get("sample_answer"):
                st.info(f" 모범답변: {content_data['sample_answer']}")
    else:
        tab_a, tab_b = st.tabs([" 답변", " 음성"])
        with tab_a:
            if content_data and not content_data.get("error"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("내용", f"{content_data.get('content_score', 0)}/40")
                    st.caption(content_data.get('content_feedback', ''))
                    st.metric("구조", f"{content_data.get('structure_score', 0)}/30")
                    st.caption(content_data.get('structure_feedback', ''))
                with col2:
                    for s in content_data.get("strengths", []):
                        st.success(f" {s}")
                    for i in content_data.get("improvements", []):
                        st.warning(f"△ {i}")
                if content_data.get("sample_answer"):
                    st.info(f" 모범답변: {content_data['sample_answer']}")
        with tab_b:
            v = r.get("voice", {})
            if v:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("말 속도", f"{v.get('speech_rate', {}).get('wpm', 0)} WPM")
                with col2:
                    st.metric("추임새", f"{v.get('filler', {}).get('count', 0)}회")
                with col3:
                    st.metric("답변 시간", f"{v.get('duration', {}).get('seconds', 0)}초")
            else:
                st.caption("음성 분석 데이터 없음")

    # 답변 리라이트
    if show_rewrite and r.get("answer") and content_data and not content_data.get("error"):
        st.markdown("---")
        if st.button("내 답변 개선 버전 보기", key=f"{key_prefix}_rewrite_btn"):
            with st.spinner("답변을 다듬고 있습니다..."):
                rewritten = rewrite_answer(
                    r["question"], r["answer"],
                    r.get("airline", st.session_state.airline),
                    AIRLINE_TYPE.get(r.get("airline", st.session_state.airline), "LCC"),
                    content_data
                )
                if rewritten:
                    st.session_state[f"{key_prefix}_rewritten"] = rewritten

        if st.session_state.get(f"{key_prefix}_rewritten"):
            st.markdown("#### 개선된 답변")
            st.markdown(f"""<div style="background: #e8f5e9; border-left: 4px solid #4caf50; padding: 20px; border-radius: 0 10px 10px 0;">
                <strong>Before (원래 답변):</strong><br>{r['answer']}<br><br>
                <strong>After (개선 버전):</strong><br>{st.session_state[f"{key_prefix}_rewritten"]}
            </div>""", unsafe_allow_html=True)
            st.caption(" 개선 버전은 참고용입니다. 본인의 경험과 스타일을 유지하면서 구조만 참고하세요.")

    # 꼬리질문 버튼
    if show_followup and r.get("answer"):
        st.markdown("---")
        if st.button("꼬리질문 받기", key=f"{key_prefix}_followup_btn"):
            with st.spinner("면접관이 꼬리질문을 생각하고 있습니다..."):
                followup = generate_followup_question(
                    r["question"], r["answer"],
                    r.get("airline", st.session_state.airline),
                    st.session_state.followup_depth
                )
                if followup:
                    st.session_state.followup_question = followup
                    st.session_state.followup_result = None
                    st.session_state.followup_depth += 1
                    st.rerun()


# ========================================
# 메인 UI
# ========================================
st.title("실전 면접 연습")
st.markdown("텍스트 또는 음성으로 답변하고 **AI 종합 분석** + **꼬리질문** + **답변 개선**까지!")

if not OPENAI_API_KEY:
    st.error("OpenAI API 키가 필요합니다.")
    st.stop()

st.markdown("---")

# ========================================
# 연습 시작 전 설정
# ========================================
if not st.session_state.practice_started:
    st.markdown("### ️ 연습 설정")

    col1, col2 = st.columns(2)
    with col1:
        airline = st.selectbox("항공사", AIRLINES, format_func=lambda x: f"{x} ({AIRLINE_TYPE.get(x, 'LCC')})")
    with col2:
        cat = st.selectbox("질문 유형", list(QUESTION_CATEGORIES.keys()), format_func=lambda x: QUESTION_CATEGORIES[x])

    st.markdown("---")

    st.markdown("### 연습 모드")
    mode_col1, mode_col2 = st.columns(2)
    with mode_col1:
        practice_mode = st.radio(
            "연습 방식",
            ["single", "continuous"],
            format_func=lambda x: "단일 질문" if x == "single" else "연속 질문 모드",
            horizontal=True
        )
    with mode_col2:
        answer_mode = st.radio(
            "답변 방식",
            ["text", "voice"],
            format_func=lambda x: "⌨️ 텍스트 입력" if x == "text" else " 음성 녹음",
            horizontal=True
        )

    if practice_mode == "continuous":
        continuous_count = st.slider("연속 질문 수", min_value=3, max_value=5, value=3)
        st.caption(" 연속 모드: 여러 질문에 연달아 답변 후 종합 리포트를 받습니다.")
    else:
        continuous_count = 1

    st.markdown("---")
    st.markdown("### 질문 예시")
    for i, q in enumerate(INTERVIEW_QUESTIONS[cat][:3], 1):
        st.caption(f"{i}. {q}")

    if st.button("연습 시작", type="primary", use_container_width=True):
        if practice_mode == "continuous":
            questions = random.sample(INTERVIEW_QUESTIONS[cat], min(continuous_count, len(INTERVIEW_QUESTIONS[cat])))
            st.session_state.continuous_questions = questions
            st.session_state.continuous_results = []
            st.session_state.continuous_index = 0
            st.session_state.continuous_count = continuous_count
            st.session_state.continuous_done = False
            st.session_state.question = questions[0]
        else:
            st.session_state.question = random.choice(INTERVIEW_QUESTIONS[cat])

        st.session_state.category = cat
        st.session_state.airline = airline
        st.session_state.practice_mode = practice_mode
        st.session_state.answer_mode = answer_mode
        st.session_state.practice_started = True
        st.session_state.result = None
        st.session_state.followup_question = None
        st.session_state.followup_result = None
        st.session_state.followup_depth = 0
        st.rerun()

# ========================================
# 연습 진행 중
# ========================================
else:
    q = st.session_state.question
    airline = st.session_state.airline
    atype = AIRLINE_TYPE.get(airline, "LCC")
    mode = st.session_state.answer_mode

    # 연속 모드 진행 표시
    if st.session_state.practice_mode == "continuous" and not st.session_state.continuous_done:
        idx = st.session_state.continuous_index
        total_q = st.session_state.continuous_count
        st.progress((idx) / total_q, text=f"질문 {idx + 1} / {total_q}")

    # 질문 표시
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 20px; padding: 30px; margin-bottom: 30px;">
        <div style="font-size: 14px; opacity: 0.8;">{airline} ({atype}) | {QUESTION_CATEGORIES.get(st.session_state.category, '')} | {'텍스트 모드' if mode == 'text' else '음성 모드'}</div>
        <div style="font-size: 24px; font-weight: bold; margin-top: 10px;">"{q}"</div>
    </div>
    """, unsafe_allow_html=True)

    # ========================================
    # 연속 모드 종합 리포트
    # ========================================
    if st.session_state.practice_mode == "continuous" and st.session_state.continuous_done:
        st.markdown("## 연속 면접 종합 리포트")
        results = st.session_state.continuous_results

        avg_score = sum(r["total"]["total_score"] for r in results) / len(results)
        avg_total = calc_total(
            {"total_score": int(sum(r["total"]["breakdown"]["voice"] for r in results) / len(results))},
            {"total_score": int(sum(r["total"]["breakdown"]["content"] for r in results) / len(results))},
            {},
            mode
        )

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {avg_total['color']}20, {avg_total['color']}10); border: 3px solid {avg_total['color']}; border-radius: 25px; padding: 40px; text-align: center; margin-bottom: 30px;">
            <div style="font-size: 20px; color: #666;">종합 평균</div>
            <div style="font-size: 80px;">{avg_total['grade']}</div>
            <div style="font-size: 48px; font-weight: bold; color: {avg_total['color']};">{avg_score:.0f}점</div>
            <div style="font-size: 18px; color: #666;">{len(results)}개 질문 완료</div>
        </div>
        """, unsafe_allow_html=True)

        # 질문별 점수 차트
        st.markdown("### 질문별 점수")
        import pandas as pd
        chart_data = pd.DataFrame({
            "질문": [f"Q{i+1}" for i in range(len(results))],
            "점수": [r["total"]["total_score"] for r in results]
        })
        st.bar_chart(chart_data.set_index("질문"))

        # 각 질문 상세
        for i, r in enumerate(results):
            with st.expander(f"Q{i+1}: {r['question'][:30]}... ({r['total']['grade']} - {r['total']['total_score']}점)"):
                display_result(r, show_followup=False, show_rewrite=True, key_prefix=f"cont_{i}")

        # 종합 피드백
        st.markdown("### 종합 코칭")
        all_improvements = []
        all_strengths = []
        for r in results:
            c = r.get("content", {})
            if c and not c.get("error"):
                all_improvements.extend(c.get("improvements", []))
                all_strengths.extend(c.get("strengths", []))

        if all_strengths:
            st.success("**강점:**" + " / ".join(list(dict.fromkeys(all_strengths))[:5]))
        if all_improvements:
            st.warning("**개선점:**" + " / ".join(list(dict.fromkeys(all_improvements))[:5]))

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("다시 연습", use_container_width=True):
                st.session_state.practice_started = False
                st.session_state.continuous_done = False
                st.session_state.continuous_results = []
                st.rerun()
        with col2:
            if st.button("처음으로", use_container_width=True):
                for k, v in DEFAULT_STATE.items():
                    st.session_state[k] = v
                st.rerun()

    # ========================================
    # 답변 입력
    # ========================================
    elif not st.session_state.result:
        if mode == "text":
            st.markdown("### ⌨️ 텍스트로 답변하기")
            st.caption(" 실제 면접에서 말할 내용을 그대로 작성해보세요. 60~90초 분량(200~300자)이 적당합니다.")
            text_answer = st.text_area(
                "답변 입력",
                height=200,
                placeholder="여기에 답변을 작성하세요...",
                key="text_answer_input"
            )
            char_count = len(text_answer) if text_answer else 0
            if char_count > 0:
                color = "#28a745" if 150 <= char_count <= 350 else "#ffc107" if char_count < 150 else "#dc3545"
                st.markdown(f"<span style='color:{color};'>{char_count}자</span> (권장: 200~300자)", unsafe_allow_html=True)

            if text_answer and st.button("분석하기", type="primary", use_container_width=True):
                with st.spinner(" 답변 분석 중..."):
                    result = run_analysis(q, airline, atype, text_answer=text_answer, mode="text")
                    st.session_state.result = result
                    st.session_state.history.append(result)
                    st.session_state.persistent_history.append({
                        "question": q, "score": result["total"]["total_score"],
                        "grade": result["total"]["grade"], "mode": "text",
                        "airline": airline, "category": st.session_state.category,
                        "timestamp": result["timestamp"]
                    })
                    save_history(st.session_state.persistent_history)
                    st.rerun()
        else:
            st.markdown("### 음성으로 답변하기")
            st.caption(" 질문을 읽고, 마이크 버튼을 눌러 답변을 녹음하세요. 60~90초가 적당합니다.")

            audio_value = st.audio_input("️ 녹음하기", key="voice_answer_input")

            if audio_value:
                st.audio(audio_value)
                if st.button("분석하기", type="primary", use_container_width=True):
                    with st.spinner(" 음성 분석 중..."):
                        audio_bytes = audio_value.getvalue()
                        result = run_analysis(q, airline, atype, audio_bytes=audio_bytes, mode="voice")
                        st.session_state.result = result
                        st.session_state.history.append(result)
                        st.session_state.persistent_history.append({
                            "question": q, "score": result["total"]["total_score"],
                            "grade": result["total"]["grade"], "mode": "voice",
                            "airline": airline, "category": st.session_state.category,
                            "timestamp": result["timestamp"]
                        })
                        save_history(st.session_state.persistent_history)
                        st.rerun()

    # ========================================
    # 결과 + 꼬리질문
    # ========================================
    else:
        st.markdown("### 분석 결과")
        display_result(st.session_state.result, show_followup=True, show_rewrite=True, key_prefix="main")

        # 꼬리질문 답변 UI
        if st.session_state.followup_question:
            st.markdown("---")
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #ff6b6b, #ee5a24); color: white; border-radius: 20px; padding: 25px; margin: 20px 0;">
                <div style="font-size: 14px; opacity: 0.8;">꼬리질문 (깊이 {st.session_state.followup_depth})</div>
                <div style="font-size: 20px; font-weight: bold; margin-top: 8px;">"{st.session_state.followup_question}"</div>
            </div>
            """, unsafe_allow_html=True)

            if not st.session_state.followup_result:
                if mode == "text":
                    followup_answer = st.text_area(
                        "꼬리질문 답변",
                        height=150,
                        placeholder="꼬리질문에 대한 답변을 작성하세요...",
                        key="followup_text"
                    )
                    if followup_answer and st.button("꼬리질문 답변 분석", type="primary", key="followup_analyze"):
                        with st.spinner("분석 중..."):
                            followup_result = run_analysis(
                                st.session_state.followup_question, airline, atype,
                                text_answer=followup_answer, mode="text"
                            )
                            st.session_state.followup_result = followup_result
                            st.rerun()
                else:
                    st.markdown("#####  꼬리질문 음성 답변")
                    followup_audio = st.audio_input("️ 녹음하기", key="followup_audio")
                    if followup_audio and st.button("꼬리질문 답변 분석", type="primary", key="followup_analyze"):
                        with st.spinner("분석 중..."):
                            followup_result = run_analysis(
                                st.session_state.followup_question, airline, atype,
                                audio_bytes=followup_audio.getvalue(), mode="voice"
                            )
                            st.session_state.followup_result = followup_result
                            st.rerun()
            else:
                st.markdown("#### 꼬리질문 분석 결과")
                display_result(st.session_state.followup_result, show_followup=True, show_rewrite=True, key_prefix="followup")

        st.markdown("---")

        # 하단 버튼
        if st.session_state.practice_mode == "continuous":
            idx = st.session_state.continuous_index
            total_q = st.session_state.continuous_count

            if idx + 1 < total_q:
                if st.button(f"️ 다음 질문 ({idx + 2}/{total_q})", type="primary", use_container_width=True):
                    st.session_state.continuous_results.append(st.session_state.result)
                    st.session_state.continuous_index += 1
                    st.session_state.question = st.session_state.continuous_questions[st.session_state.continuous_index]
                    st.session_state.result = None
                    st.session_state.followup_question = None
                    st.session_state.followup_result = None
                    st.session_state.followup_depth = 0
                    st.rerun()
            else:
                if st.button("종합 리포트 보기", type="primary", use_container_width=True):
                    st.session_state.continuous_results.append(st.session_state.result)
                    st.session_state.continuous_done = True
                    st.session_state.result = None
                    st.rerun()
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("같은 질문 다시"):
                    st.session_state.result = None
                    st.session_state.followup_question = None
                    st.session_state.followup_result = None
                    st.session_state.followup_depth = 0
                    st.rerun()
            with col2:
                if st.button("️ 다음 질문"):
                    st.session_state.question = random.choice(INTERVIEW_QUESTIONS[st.session_state.category])
                    st.session_state.result = None
                    st.session_state.followup_question = None
                    st.session_state.followup_result = None
                    st.session_state.followup_depth = 0
                    st.rerun()
            with col3:
                if st.button("처음으로"):
                    for k, v in DEFAULT_STATE.items():
                        st.session_state[k] = v
                    st.rerun()

# ========================================
# 하단: 성장 추이 + 누적 기록
# ========================================
st.markdown("---")

persistent = st.session_state.persistent_history
if persistent:
    st.markdown("### 나의 성장 기록")

    col1, col2, col3, col4 = st.columns(4)
    scores = [h["score"] for h in persistent]
    with col1:
        st.metric("총 연습 횟수", f"{len(persistent)}회")
    with col2:
        st.metric("평균 점수", f"{sum(scores)/len(scores):.0f}점")
    with col3:
        st.metric("최고 점수", f"{max(scores)}점")
    with col4:
        recent = scores[-5:]
        prev = scores[-10:-5] if len(scores) > 5 else scores[:len(scores)//2] if len(scores) > 1 else scores
        delta = sum(recent)/len(recent) - sum(prev)/len(prev) if prev else 0
        st.metric("최근 추세", f"{sum(recent)/len(recent):.0f}점", delta=f"{delta:+.0f}" if delta != 0 else None)

    if len(persistent) >= 2:
        import pandas as pd
        chart_df = pd.DataFrame({
            "회차": list(range(1, len(persistent) + 1)),
            "점수": scores
        })
        st.line_chart(chart_df.set_index("회차"))

    with st.expander("상세 통계"):
        cat_stats = {}
        for h in persistent:
            cat = h.get("category", "unknown")
            if cat not in cat_stats:
                cat_stats[cat] = []
            cat_stats[cat].append(h["score"])

        for cat, cat_scores in cat_stats.items():
            cat_name = QUESTION_CATEGORIES.get(cat, cat)
            avg = sum(cat_scores) / len(cat_scores)
            st.markdown(f"**{cat_name}**: 평균 {avg:.0f}점 ({len(cat_scores)}회)")

        st.markdown("---")
        st.markdown("**최근 10회 기록**")
        for h in reversed(persistent[-10:]):
            ts = h.get("timestamp", "")[:10]
            mode_icon = "⌨️" if h.get("mode") == "text" else ""
            st.caption(f"{ts} | {mode_icon} {h.get('airline', '')} | {QUESTION_CATEGORIES.get(h.get('category', ''), '')} | {h['grade']} ({h['score']}점)")

elif st.session_state.history:
    with st.expander(f" 이번 세션 기록 ({len(st.session_state.history)}회)"):
        scores = [h["total"]["total_score"] for h in st.session_state.history]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("평균", f"{sum(scores)/len(scores):.0f}점")
        with col2:
            st.metric("최고", f"{max(scores)}점")
        with col3:
            st.metric("횟수", f"{len(scores)}회")

st.markdown('</div>', unsafe_allow_html=True)

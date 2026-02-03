# pages/5_토론면접.py
# 그룹 토론면접 시뮬레이션 - 아바타/음성 기능 추가

import os
import hashlib

from logging_config import get_logger
logger = get_logger(__name__)
import random
import streamlit as st
import streamlit.components.v1 as components
import requests

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 안전한 API 유틸리티
try:
    from safe_api import get_audio_hash, validate_dict, safe_execute
    SAFE_API_AVAILABLE = True
except ImportError:
    SAFE_API_AVAILABLE = False
    def get_audio_hash(data):
        return hashlib.md5(data).hexdigest() if data else ""

from config import LLM_MODEL_NAME, LLM_API_URL, LLM_TIMEOUT_SEC
from env_config import OPENAI_API_KEY

# 음성 유틸리티 import
try:
    from voice_utils import (
        generate_tts_audio,
        get_audio_player_html,
        get_loud_audio_component,
        transcribe_audio,
        analyze_voice_quality,
        analyze_voice_complete,
    )
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# 애니메이션 컴포넌트 import
try:
    from animation_components import (
        render_debate_table,
        render_animated_debater,
        render_user_debate
    )
    ANIMATION_AVAILABLE = True
except ImportError:
    ANIMATION_AVAILABLE = False

# 점수 자동 저장 유틸리티
try:
    from score_utils import save_practice_score, parse_evaluation_score
    SCORE_UTILS_AVAILABLE = True
except ImportError:
    SCORE_UTILS_AVAILABLE = False

# 토론 주제 데이터
try:
    from debate_topics import (
        ALL_DEBATE_TOPICS,
        DEBATE_CATEGORIES,
        get_topics_by_category,
        get_category_info,
    )
    DEBATE_TOPICS_AVAILABLE = True
except ImportError:
    DEBATE_TOPICS_AVAILABLE = False

# PDF 리포트
try:
    from debate_report import generate_debate_report, get_debate_report_filename
    DEBATE_REPORT_AVAILABLE = True
except ImportError:
    DEBATE_REPORT_AVAILABLE = False

# 토론 고도화 모듈 (Phase B4)
try:
    from debate_enhancer import (
        EnhancedDebateAnalyzer,
        analyze_debate_answer,
        get_argument_feedback,
        get_debate_analysis_complete,
    )
    DEBATE_ENHANCER_AVAILABLE = True
except ImportError:
    DEBATE_ENHANCER_AVAILABLE = False

from sidebar_common import init_page, end_page

# 공용 유틸리티 (Stage 2)
try:
    from shared_utils import get_api_key, load_json, save_json
except ImportError:
    pass

init_page(
    title="토론면접",
    current_page="토론면접",
    wide_layout=True
)



# 구글 번역 방지
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

# ----------------------------
# 비밀번호 보호
# ----------------------------

# =====================
# 토론 주제 (폴백용)
# =====================

# 새 모듈이 있으면 사용, 없으면 기본 주제 사용
if DEBATE_TOPICS_AVAILABLE:
    DEBATE_TOPICS = ALL_DEBATE_TOPICS
else:
    DEBATE_TOPICS = [
        {
            "topic": "승무원에게 외모가 중요한가?",
            "background": "항공사 승무원 채용에서 외모 기준에 대한 논란이 있습니다.",
            "pro_points": ["첫인상의 중요성", "브랜드 이미지", "고객 기대"],
            "con_points": ["능력 중심 평가", "다양성 존중", "외모 차별 문제"],
            "category": "aviation",
        },
        {
            "topic": "기내에서 휴대폰 사용을 전면 허용해야 하는가?",
            "background": "기술 발전으로 비행기 모드가 일반화되었습니다.",
            "pro_points": ["기술 발전으로 안전 문제 해결", "승객 편의", "트렌드"],
            "con_points": ["안전 규정 준수", "다른 승객 배려", "비상시 집중력"],
            "category": "service",
        },
    ]
    DEBATE_CATEGORIES = {
        "all": {"name": "전체", "icon": "", "color": "#6b7280"},
    }

# AI 토론자 페르소나 (아바타 추가)
DEBATERS = {
    "pro": {
        "name": "김찬성",
        "style": "논리적이고 데이터 중심으로 주장",
        "emoji": "",
        "color": "#3b82f6",
        "voice": "onyx",  # OpenAI TTS 남성 음성
    },
    "con": {
        "name": "이반대",
        "style": "감성적이고 사례 중심으로 반박",
        "emoji": "",
        "color": "#ef4444",
        "voice": "nova",  # OpenAI TTS 여성 음성
    },
    "neutral": {
        "name": "박중립",
        "style": "양측 의견을 조율하며 균형 잡힌 시각 제시",
        "emoji": "",
        "color": "#8b5cf6",
        "voice": "shimmer",  # OpenAI TTS 여성 음성
    },
}


# =====================
# 아바타 HTML 함수
# =====================

def get_debater_avatar_html(
    message: str,
    position: str,
    name: str,
    is_speaking: bool = False
) -> str:
    """토론자 아바타 HTML 생성"""
    debater = DEBATERS.get(position, DEBATERS["neutral"])
    position_kr = {"pro": "찬성", "con": "반대", "neutral": "중립"}[position]

    speaking_style = ""
    if is_speaking:
        speaking_style = """
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
            50% { box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
        }
        animation: pulse 1.5s infinite;
        """

    return f"""
    <div style="
        display: flex;
        align-items: flex-start;
        gap: 15px;
        padding: 15px 20px;
        background: linear-gradient(135deg, {debater['color']}15 0%, {debater['color']}08 100%);
        border-left: 4px solid {debater['color']};
        border-radius: 12px;
        margin: 10px 0;
        {speaking_style}
    ">
        <div style="
            min-width: 50px;
            text-align: center;
        ">
            <div style="
                font-size: 40px;
                background: white;
                width: 55px;
                height: 55px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            ">{debater['emoji']}</div>
        </div>
        <div style="flex: 1;">
            <div style="
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 8px;
            ">
                <span style="
                    font-weight: bold;
                    color: {debater['color']};
                    font-size: 15px;
                ">{name}</span>
                <span style="
                    background: {debater['color']}20;
                    color: {debater['color']};
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 11px;
                    font-weight: bold;
                ">{position_kr}</span>
            </div>
            <div style="
                background: white;
                padding: 12px 16px;
                border-radius: 10px;
                font-size: 15px;
                color: #333;
                line-height: 1.6;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            ">
                {message}
            </div>
        </div>
    </div>
    """


def get_user_debate_html(message: str, position: str) -> str:
    """사용자 토론 발언 HTML"""
    position_kr = {"pro": "찬성", "con": "반대", "neutral": "중립"}[position]

    return f"""
    <div style="
        display: flex;
        align-items: flex-start;
        gap: 15px;
        padding: 15px 20px;
        background: linear-gradient(135deg, #10b98115 0%, #10b98108 100%);
        border-right: 4px solid #10b981;
        border-radius: 12px;
        margin: 10px 0;
        flex-direction: row-reverse;
    ">
        <div style="
            min-width: 50px;
            text-align: center;
        ">
            <div style="
                font-size: 40px;
                background: white;
                width: 55px;
                height: 55px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            ">️</div>
        </div>
        <div style="flex: 1; text-align: right;">
            <div style="
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 8px;
                justify-content: flex-end;
            ">
                <span style="
                    font-weight: bold;
                    color: #10b981;
                    font-size: 15px;
                ">나 (지원자)</span>
                <span style="
                    background: #10b98120;
                    color: #10b981;
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 11px;
                    font-weight: bold;
                ">{position_kr}</span>
            </div>
            <div style="
                background: white;
                padding: 12px 16px;
                border-radius: 10px;
                font-size: 15px;
                color: #333;
                line-height: 1.6;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                display: inline-block;
                text-align: left;
            ">
                {message}
            </div>
        </div>
    </div>
    """


# =====================
# 세션 상태 초기화
# =====================

defaults = {
    "debate_topic": None,
    "debate_position": None,
    "debate_history": [],
    "debate_round": 0,
    "debate_completed": False,
    "debate_evaluation": None,
    "debate_voice_mode": False,
    # 음성 분석 관련
    "debate_audio_bytes_list": [],
    "debate_voice_analyses": [],
    "debate_combined_voice_analysis": None,
    "debate_response_times": [],
    "debate_input_mode": "text",  # "text" or "voice"
    "debate_processed_audio_hash": None,
    # Phase B4 고도화: 논리력 분석
    "debate_enhanced_analysis": None,
    "debate_realtime_feedback": [],
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


def generate_debater_response(topic: dict, position: str, history: list, user_message: str = None) -> str:
    """AI 토론자 발언 생성"""
    api_key = get_api_key()
    if not api_key:
        return "[API 키 없음]"

    debater = DEBATERS[position]
    position_kr = {"pro": "찬성", "con": "반대", "neutral": "중립"}[position]

    points = topic.get(f"{position}_points", []) if position != "neutral" else []
    points_text = ", ".join(points) if points else "양측 의견 조율"

    system_prompt = f"""당신은 그룹 토론에 참여한 {debater['name']}입니다.
입장: {position_kr}
스타일: {debater['style']}
주요 논점: {points_text}

토론 규칙:
1. 한국어로 자연스럽게 발언하세요.
2. 2~3문장으로 간결하게 말하세요.
3. 다른 참가자의 발언에 반응하며 토론하세요.
4. 당신의 입장을 일관되게 유지하세요.
5. 존댓말을 사용하세요.

출력: 발언만 출력하세요. 이름이나 설명 없이."""

    messages = [{"role": "system", "content": system_prompt}]

    context = f"토론 주제: {topic['topic']}\n배경: {topic['background']}\n\n"
    if history:
        context += "지금까지의 토론:\n"
        for h in history[-6:]:
            context += f"- {h['speaker']}: {h['content']}\n"

    if user_message:
        context += f"\n[사용자(지원자)의 발언]: {user_message}\n\n이에 대해 {position_kr} 입장에서 발언하세요."
    else:
        context += f"\n{position_kr} 입장에서 토론을 시작하거나 이어가세요."

    messages.append({"role": "user", "content": context})

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": LLM_MODEL_NAME,
            "messages": messages,
            "temperature": 0.8,
            "max_tokens": 200,
        }

        r = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=LLM_TIMEOUT_SEC)
        r.raise_for_status()
        resp = r.json()

        choices = resp.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()
        return "[응답 실패]"

    except Exception as e:
        return f"[오류: {str(e)}]"


def evaluate_debate(topic: dict, user_position: str, history: list, voice_analyses: list = None) -> dict:
    """토론 평가 - 음성 분석 포함"""
    api_key = get_api_key()
    if not api_key:
        return {"error": "API 키 없음"}

    user_statements = [h for h in history if h.get("is_user")]
    position_kr = {"pro": "찬성", "con": "반대", "neutral": "중립"}[user_position]

    # 발언 내용 구성
    user_text = ""
    for i, h in enumerate(user_statements):
        user_text += f"\n[발언 {i+1}]: {h['content']}"

    # 전체 토론 맥락 구성
    debate_context = ""
    for h in history:
        if h.get("is_user"):
            debate_context += f"\n[지원자 - {position_kr}]: {h['content']}"
        else:
            debate_context += f"\n[{h['speaker']}]: {h['content']}"

    # 음성 분석 데이터 요약
    voice_summary = ""
    if voice_analyses:
        total_wpm = []
        total_fillers = 0
        total_scores = []

        for va in voice_analyses:
            if va:
                text_analysis = va.get("text_analysis", {})
                wpm = text_analysis.get("words_per_minute", 0)
                if wpm > 0:
                    total_wpm.append(wpm)
                total_fillers += text_analysis.get("filler_count", 0)
                score = va.get("overall_score", 0)
                if score > 0:
                    total_scores.append(score)

        avg_wpm = sum(total_wpm) / len(total_wpm) if total_wpm else 0
        avg_score = sum(total_scores) / len(total_scores) if total_scores else 0

        voice_summary = f"""
## 음성 분석 데이터
- 평균 말 속도: {avg_wpm:.0f} WPM (적정: 120-150)
- 총 필러 단어 사용: {total_fillers}회
- 음성 전달력 평균 점수: {avg_score:.0f}/100
"""

    system_prompt = """당신은 항공사 그룹면접 전문 평가자입니다.
토론면접에서 지원자의 발언을 종합적으로 평가해주세요.

평가 시 중요 포인트:
1. 항공사 면접에서는 논리력뿐 아니라 협력적 태도가 중요합니다
2. 상대방 의견을 경청하고 존중하면서도 자신의 주장을 명확히 전달하는지 확인하세요
3. 결론보다 과정(어떻게 토론에 참여했는가)을 중시하세요
4. 실제 면접관 시선에서 구체적이고 실용적인 피드백을 제공하세요

한국어로 상세하고 친절하게 피드백해주세요."""

    user_prompt = f"""## 토론 주제
{topic['topic']}

## 주제 배경
{topic.get('background', '')}

## 지원자 입장
{position_kr}

## 전체 토론 흐름
{debate_context}

## 지원자 발언만 추출
{user_text}
{voice_summary}

## 평가 기준 (각 항목 20점, 총 100점)
1. 논리성 (20점): 주장에 근거가 있고 일관성이 있는가
2. 경청력 (20점): 상대 발언을 듣고 적절히 반응했는가
3. 표현력 (20점): 명확하고 설득력 있게 전달했는가
4. 태도 (20점): 존중하고 협력적인 자세인가
5. 리더십 (20점): 토론을 이끌거나 정리하는 모습이 있는가

## 출력 형식 (반드시 이 형식을 따르세요)

### 종합 점수: X/100

### 등급: [S/A/B/C/D]
(90점 이상 S, 80점 이상 A, 70점 이상 B, 60점 이상 C, 그 미만 D)

---

###  항목별 평가

#### 1. 논리성 (X/20점)
**평가:** (구체적인 분석)
**근거:** (지원자 발언에서 구체적 예시 인용)

#### 2. 경청력 (X/20점)
**평가:** (구체적인 분석)
**근거:** (상대 발언에 어떻게 반응했는지)

#### 3. 표현력 (X/20점)
**평가:** (구체적인 분석)
**근거:** (표현 방식, 문장 구조 분석)

#### 4. 태도 (X/20점)
**평가:** (구체적인 분석)
**근거:** (말투, 표현에서 드러나는 태도)

#### 5. 리더십 (X/20점)
**평가:** (구체적인 분석)
**근거:** (토론 진행에 기여한 부분)

---

###  잘한 점 (3가지)
1. (구체적으로 - 발언 인용 포함)
2. (구체적으로)
3. (구체적으로)

### ️ 개선할 점 (3가지)
1. (구체적으로 - 어떻게 고치면 좋을지 포함)
2. (구체적으로)
3. (구체적으로)

---

###  면접관 코멘트
(실제 면접관 시선에서 종합 평가 2-3문장)

###  다음 토론을 위한 팁
(구체적이고 실천 가능한 조언 2-3가지)
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
            "temperature": 0.4,
            "max_tokens": 1500,
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


# =====================
# UI
# =====================

st.title("토론면접 시뮬레이션")
st.caption("AI 토론자들과 함께 그룹 토론을 연습하세요.")

if st.session_state.debate_topic is None:
    # 토론면접 가이드
    st.info("""
    **토론면접 연습 가이드**

    1. **주제 선택**: 아래에서 토론 주제를 선택하세요.
    2. **입장 선택**: 찬성/반대/중립 중 하나를 선택합니다.
    3. **토론 진행**: AI 토론자들(김찬성, 이반대, 박중립)과 4라운드 토론을 합니다.
    4. **평가 받기**: 토론 종료 후 AI가 당신의 논리력, 경청, 표현력을 평가합니다.

    **평가 기준:**
    - 논리적 주장: 근거와 예시를 들어 설득력 있게
    - 경청과 반박: 상대 의견을 듣고 적절히 대응
    - 표현력: 명확하고 간결한 의사 전달
    - 태도: 존중하면서도 자신감 있는 자세
    """)

    # 음성 모드 선택
    if VOICE_AVAILABLE:
        voice_mode = st.checkbox(" 음성 모드 (토론자 발언을 음성으로 듣기)", value=False)
        st.session_state.debate_voice_mode = voice_mode

    # 토론자 소개
    st.markdown("### AI 토론자 소개")
    cols = st.columns(3)
    for i, (key, debater) in enumerate(DEBATERS.items()):
        with cols[i]:
            position_kr = {"pro": " 찬성", "con": " 반대", "neutral": "️ 중립"}[key]
            st.markdown(f"""
            <div style="
                text-align: center;
                padding: 15px;
                background: {debater['color']}10;
                border-radius: 10px;
                border: 2px solid {debater['color']}30;
            ">
                <div style="font-size: 40px;">{debater['emoji']}</div>
                <div style="font-weight: bold; color: {debater['color']};">{debater['name']}</div>
                <div style="font-size: 12px; color: #666;">{position_kr}</div>
                <div style="font-size: 11px; color: #888; margin-top: 5px;">{debater['style']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 카테고리 필터
    st.subheader(" 토론 주제 선택")

    if DEBATE_TOPICS_AVAILABLE:
        # 카테고리 탭
        category_cols = st.columns(5)

        # 세션 상태에 선택된 카테고리 저장
        if "selected_category" not in st.session_state:
            st.session_state.selected_category = "all"

        with category_cols[0]:
            if st.button("전체", use_container_width=True,
                        type="primary" if st.session_state.selected_category == "all" else "secondary"):
                st.session_state.selected_category = "all"
                st.rerun()

        for idx, (cat_id, cat_info) in enumerate(DEBATE_CATEGORIES.items()):
            with category_cols[idx + 1]:
                btn_type = "primary" if st.session_state.selected_category == cat_id else "secondary"
                if st.button(f"{cat_info['icon']} {cat_info['name']}", use_container_width=True, type=btn_type):
                    st.session_state.selected_category = cat_id
                    st.rerun()

        # 선택된 카테고리의 주제 필터링
        if st.session_state.selected_category == "all":
            filtered_topics = DEBATE_TOPICS
        else:
            filtered_topics = get_topics_by_category(st.session_state.selected_category)

        st.caption(f"총 {len(filtered_topics)}개 주제")
    else:
        filtered_topics = DEBATE_TOPICS

    # 주제 목록 표시
    for i, topic in enumerate(filtered_topics):
        cat_info = DEBATE_CATEGORIES.get(topic.get("category", ""), {})
        cat_badge = f"{cat_info.get('icon', '')} {cat_info.get('name', '')}" if cat_info else ""

        with st.expander(f" {topic['topic']}", expanded=(i == 0)):
            if cat_badge:
                st.markdown(f"""
                <span style="
                    background: {cat_info.get('color', '#6b7280')}20;
                    color: {cat_info.get('color', '#6b7280')};
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 12px;
                ">{cat_badge}</span>
                """, unsafe_allow_html=True)

            st.write(topic["background"])

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("** 찬성 측 논점**")
                for p in topic["pro_points"]:
                    st.write(f"• {p}")
            with col2:
                st.markdown("** 반대 측 논점**")
                for p in topic["con_points"]:
                    st.write(f"• {p}")

            if st.button("이 주제로 토론하기", key=f"select_{i}_{topic['topic'][:10]}", type="primary", use_container_width=True):
                st.session_state.debate_topic = topic
                st.rerun()

elif st.session_state.debate_position is None:
    # 입장 선택
    topic = st.session_state.debate_topic

    st.subheader(f" {topic['topic']}")
    st.write(topic["background"])

    st.divider()
    st.subheader("당신의 입장을 선택하세요")

    # 남은 사용량 표시

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: #3b82f610; border-radius: 15px; border: 2px solid #3b82f630;">
            <div style="font-size: 50px;"></div>
            <h3 style="color: #3b82f6;">찬성</h3>
        </div>
        """, unsafe_allow_html=True)
        for p in topic["pro_points"]:
            st.write(f"• {p}")
        if st.button("찬성으로 참여", use_container_width=True, type="primary"):
            st.session_state.debate_position = "pro"
            st.session_state.debate_history = []
            st.session_state.debate_round = 0
            st.rerun()

    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: #ef444410; border-radius: 15px; border: 2px solid #ef444430;">
            <div style="font-size: 50px;"></div>
            <h3 style="color: #ef4444;">반대</h3>
        </div>
        """, unsafe_allow_html=True)
        for p in topic["con_points"]:
            st.write(f"• {p}")
        if st.button("반대로 참여", use_container_width=True, type="primary"):
            st.session_state.debate_position = "con"
            st.session_state.debate_history = []
            st.session_state.debate_round = 0
            st.rerun()

    with col3:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: #8b5cf610; border-radius: 15px; border: 2px solid #8b5cf630;">
            <div style="font-size: 50px;">️</div>
            <h3 style="color: #8b5cf6;">중립</h3>
        </div>
        """, unsafe_allow_html=True)
        st.write("• 양측 의견 조율")
        st.write("• 균형 잡힌 시각")
        if st.button("중립으로 참여", use_container_width=True):
            st.session_state.debate_position = "neutral"
            st.session_state.debate_history = []
            st.session_state.debate_round = 0
            st.rerun()

    if st.button("← 주제 다시 선택"):
        st.session_state.debate_topic = None
        st.rerun()

elif not st.session_state.debate_completed:
    # 토론 진행
    topic = st.session_state.debate_topic
    position = st.session_state.debate_position
    position_kr = {"pro": "찬성", "con": "반대", "neutral": "중립"}[position]

    # 상단 정보
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.subheader(f" {topic['topic']}")
    with col2:
        st.metric("라운드", f"{st.session_state.debate_round + 1}/4")
    with col3:
        st.info(f"내 입장: {position_kr}")

    st.divider()

    # 토론 테이블 장면 표시 (애니메이션 - components.html 사용)
    if ANIMATION_AVAILABLE:
        # 현재 발언자 찾기
        current_speaker = ""
        if st.session_state.debate_history:
            last_msg = st.session_state.debate_history[-1]
            if last_msg.get("is_user"):
                current_speaker = "user"
            else:
                current_speaker = last_msg.get("speaker", "")

        render_debate_table(current_speaker, position)

    # 토론 내용 표시 (애니메이션 적용)
    for idx, h in enumerate(st.session_state.debate_history):
        is_last = (idx == len(st.session_state.debate_history) - 1)

        if h.get("is_user"):
            if ANIMATION_AVAILABLE:
                render_user_debate(h['content'], position)
            else:
                st.markdown(get_user_debate_html(h['content'], position), unsafe_allow_html=True)
        else:
            debater = DEBATERS.get(h.get('position', 'neutral'))

            if ANIMATION_AVAILABLE:
                render_animated_debater(
                    h['content'],
                    h['speaker'],
                    h.get('position', 'neutral'),
                    debater.get('emoji', ''),
                    debater.get('color', '#6b7280'),
                    is_speaking=is_last
                )
            else:
                st.markdown(
                    get_debater_avatar_html(
                        h['content'],
                        h.get('position', 'neutral'),
                        h['speaker'],
                        is_speaking=False
                    ),
                    unsafe_allow_html=True
                )

            # 음성 재생 버튼 (CLOVA TTS)
            if st.session_state.debate_voice_mode and VOICE_AVAILABLE:
                if st.button(f" 듣기", key=f"listen_{idx}_{h['content'][:10]}"):
                    with st.spinner("음성 생성 중..."):
                        audio = generate_tts_audio(h['content'], voice=debater.get('voice', 'nova'))
                        if audio:
                            get_loud_audio_component(audio, autoplay=True, gain=5.0)

    # 첫 라운드면 AI가 먼저 시작
    if st.session_state.debate_round == 0 and not st.session_state.debate_history:
        with st.spinner("토론을 시작합니다..."):
            pro_response = generate_debater_response(topic, "pro", [])
            st.session_state.debate_history.append({
                "speaker": DEBATERS["pro"]["name"],
                "content": pro_response,
                "position": "pro",
                "is_user": False,
            })
        st.rerun()

    # 사용자 입력
    st.markdown("---")

    if st.session_state.debate_round < 4:
        # 입력 모드 선택
        input_col1, input_col2 = st.columns([1, 3])
        with input_col1:
            input_mode = st.radio(
                "입력 방식",
                ["텍스트", "음성"],
                horizontal=True,
                key="debate_input_mode_radio",
                label_visibility="collapsed"
            )
            st.session_state.debate_input_mode = "voice" if input_mode == "음성" else "text"

        user_input = None
        voice_analysis = None

        if st.session_state.debate_input_mode == "voice" and VOICE_AVAILABLE:
            # 음성 입력 모드
            st.info("녹음 버튼을 클릭하고 토론 발언을 하세요. (30초~2분 권장)")

            audio_data = st.audio_input(
                " 녹음하기",
                key=f"debate_voice_{st.session_state.debate_round}"
            )

            if audio_data:
                # 오디오 바이트 먼저 읽기
                audio_bytes = audio_data.read()

                # 해시 기반 중복 체크 (id() 대신 - 더 정확함)
                audio_hash = get_audio_hash(audio_bytes)

                if st.session_state.debate_processed_audio_hash != audio_hash:
                    st.session_state.debate_processed_audio_hash = audio_hash

                    with st.spinner("음성을 분석하고 있습니다..."):

                        # 음성 인식 (STT)
                        import time
                        start_time = time.time()
                        stt_result = transcribe_audio(audio_bytes, language="ko")
                        response_time = int(time.time() - start_time)

                        if stt_result.get("success") and stt_result.get("text"):
                            user_input = stt_result["text"]

                            # 음성 품질 분석
                            voice_analysis = analyze_voice_quality(
                                stt_result,
                                expected_duration_range=(30, 120)
                            )

                            # 저장
                            st.session_state.debate_audio_bytes_list.append(audio_bytes)
                            st.session_state.debate_voice_analyses.append(voice_analysis)
                            st.session_state.debate_response_times.append(response_time)

                            st.success(f" 인식된 발언: {user_input[:100]}...")

                            # 음성 분석 결과 미리보기
                            if voice_analysis:
                                with st.expander("음성 분석 결과", expanded=False):
                                    v_cols = st.columns(4)
                                    text_analysis = voice_analysis.get("text_analysis", {})
                                    with v_cols[0]:
                                        wpm = text_analysis.get("words_per_minute", 0)
                                        st.metric("말 속도", f"{wpm} WPM")
                                    with v_cols[1]:
                                        fillers = text_analysis.get("filler_count", 0)
                                        st.metric("필러 단어", f"{fillers}회")
                                    with v_cols[2]:
                                        clarity = voice_analysis.get("voice_quality", {}).get("pronunciation_clarity", 0)
                                        st.metric("발음 명확도", f"{clarity}%")
                                    with v_cols[3]:
                                        overall = voice_analysis.get("overall_score", 0)
                                        st.metric("종합 점수", f"{overall}점")
                        else:
                            st.error("음성 인식에 실패했습니다. 다시 시도해주세요.")
                            user_input = None

            # 텍스트 폴백 입력
            with st.expander("텍스트로 직접 입력", expanded=False):
                fallback_input = st.text_area(
                    "음성 인식이 안 될 경우 여기에 입력하세요",
                    key=f"debate_fallback_{st.session_state.debate_round}"
                )
                if st.button("텍스트로 제출", key=f"submit_fallback_{st.session_state.debate_round}"):
                    if fallback_input:
                        user_input = fallback_input
        else:
            # 텍스트 입력 모드
            user_input = st.chat_input("토론에 참여하세요...")

        # 발언 처리
        if user_input:
            # 히스토리에 추가 (음성 분석 정보 포함)
            history_entry = {
                "speaker": f"나 ({position_kr})",
                "content": user_input,
                "position": position,
                "is_user": True,
            }
            if voice_analysis:
                history_entry["voice_analysis"] = voice_analysis

            st.session_state.debate_history.append(history_entry)

            with st.spinner("다른 참가자들이 발언 중..."):
                if position == "pro":
                    opponent = "con"
                elif position == "con":
                    opponent = "pro"
                else:
                    opponent = random.choice(["pro", "con"])

                response = generate_debater_response(
                    topic, opponent,
                    st.session_state.debate_history,
                    user_input
                )
                st.session_state.debate_history.append({
                    "speaker": DEBATERS[opponent]["name"],
                    "content": response,
                    "position": opponent,
                    "is_user": False,
                })

                if random.random() > 0.5:
                    neutral_response = generate_debater_response(
                        topic, "neutral",
                        st.session_state.debate_history
                    )
                    st.session_state.debate_history.append({
                        "speaker": DEBATERS["neutral"]["name"],
                        "content": neutral_response,
                        "position": "neutral",
                        "is_user": False,
                    })

            st.session_state.debate_round += 1
            st.session_state.debate_processed_audio_hash = None  # 리셋

            if st.session_state.debate_round >= 4:
                st.session_state.debate_completed = True

            st.rerun()

        if st.session_state.debate_round >= 2:
            if st.button("토론 종료하기", type="primary", use_container_width=True):
                st.session_state.debate_completed = True
                st.rerun()

else:
    # 토론 완료 - 평가
    st.subheader(" 토론 완료!")

    # 종합 음성 분석 (음성 입력이 있었다면)
    if st.session_state.debate_audio_bytes_list and st.session_state.debate_combined_voice_analysis is None:
        with st.spinner("음성 데이터를 종합 분석하고 있습니다..."):
            try:
                combined_audio = b''.join(st.session_state.debate_audio_bytes_list)
                voice_result = analyze_voice_complete(
                    combined_audio,
                    response_times=st.session_state.debate_response_times
                )
                st.session_state.debate_combined_voice_analysis = voice_result
            except Exception as e:
                st.session_state.debate_combined_voice_analysis = {"error": str(e)}

    if st.session_state.debate_evaluation is None:
        with st.spinner("토론 내용을 평가하고 있습니다..."):
            evaluation = evaluate_debate(
                st.session_state.debate_topic,
                st.session_state.debate_position,
                st.session_state.debate_history,
                voice_analyses=st.session_state.debate_voice_analyses
            )
            st.session_state.debate_evaluation = evaluation

            # 자동 점수 저장
            if SCORE_UTILS_AVAILABLE and "result" in evaluation:
                parsed = parse_evaluation_score(evaluation["result"], "토론면접")
                if parsed.get("total", 0) > 0:
                    save_practice_score(
                        practice_type="토론면접",
                        total_score=parsed["total"],
                        detailed_scores=parsed.get("detailed"),
                        scenario=st.session_state.debate_topic.get("topic", "")
                    )

            # Phase B4: 고도화된 논리력 분석
            if DEBATE_ENHANCER_AVAILABLE and st.session_state.debate_enhanced_analysis is None:
                user_statements = [
                    h['content'] for h in st.session_state.debate_history if h.get('is_user')
                ]
                if user_statements:
                    enhanced = get_debate_analysis_complete(
                        user_statements=user_statements,
                        all_history=st.session_state.debate_history,
                        topic=st.session_state.debate_topic.get('topic', ''),
                        user_position=st.session_state.debate_position
                    )
                    st.session_state.debate_enhanced_analysis = enhanced

        st.rerun()
    else:
        # 결과 탭
        tab_labels = [" 종합 평가", " 음성 분석", " 토론 내용"]
        if DEBATE_ENHANCER_AVAILABLE:
            tab_labels.insert(1, " 논리력 분석")
        result_tabs = st.tabs(tab_labels)

        # 탭 인덱스 동적 관리
        tab_idx = {"eval": 0}
        if DEBATE_ENHANCER_AVAILABLE:
            tab_idx["logic"] = 1
            tab_idx["voice"] = 2
            tab_idx["content"] = 3
        else:
            tab_idx["voice"] = 1
            tab_idx["content"] = 2

        with result_tabs[tab_idx["eval"]]:
            eval_result = st.session_state.debate_evaluation
            if "error" in eval_result:
                st.error(f"평가 오류: {eval_result['error']}")
            else:
                st.markdown(eval_result.get("result", ""))

        # Phase B4: 논리력 분석 탭
        if DEBATE_ENHANCER_AVAILABLE and "logic" in tab_idx:
            with result_tabs[tab_idx["logic"]]:
                enhanced = st.session_state.debate_enhanced_analysis
                if enhanced:
                    # 등급 및 종합 점수 표시
                    grade = enhanced.get('grade', 'N/A')
                    total_score = enhanced.get('total_score', 0)
                    grade_colors = {"S": "#FFD700", "A": "#4CAF50", "B": "#2196F3", "C": "#FF9800", "D": "#f44336"}
                    grade_color = grade_colors.get(grade, "#6b7280")

                    st.markdown(f"""
                    <div style="text-align: center; padding: 20px; background: {grade_color}15; border-radius: 15px; margin-bottom: 20px;">
                        <div style="font-size: 60px; font-weight: bold; color: {grade_color};">{grade}</div>
                        <div style="color: #666; font-size: 14px;">논리력 종합 등급</div>
                        <div style="font-size: 24px; color: #333; margin-top: 5px;">{total_score}점</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 세부 점수
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        logic_score = enhanced.get('logic_score', 0)
                        st.metric("논리력", f"{logic_score}점", help="논증 구조, 논리적 오류, 반박 효과성")
                    with col2:
                        persuasion_score = enhanced.get('persuasion_score', 0)
                        st.metric("설득력", f"{persuasion_score}점", help="PREP 구조, 전략 일관성")
                    with col3:
                        contrib_score = enhanced.get('contribution_score', 0)
                        st.metric("기여도", f"{contrib_score}점", help="참여율, 주제 연관성, 새 논점")

                    st.divider()

                    # 논증 구조 분석
                    st.markdown("### 논증 구조 분석")
                    arg_analyses = enhanced.get('argument_analyses', [])
                    if arg_analyses:
                        for i, arg in enumerate(arg_analyses):
                            structure_type = arg.get('structure_type', '불명')
                            strength = arg.get('strength', 0)
                            has_claim = "O" if arg.get('has_claim') else "X"
                            has_reason = "O" if arg.get('has_reason') else "X"
                            has_example = "O" if arg.get('has_example') else "X"

                            color = "#4CAF50" if strength >= 70 else "#FF9800" if strength >= 50 else "#f44336"

                            with st.expander(f"발언 {i+1}: {arg.get('statement', '')}", expanded=(i==0)):
                                st.markdown(f"""
                                <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                                    <div style="background: {color}15; padding: 10px 15px; border-radius: 8px; text-align: center;">
                                        <div style="font-size: 12px; color: #666;">구조 유형</div>
                                        <div style="font-weight: bold; color: {color};">{structure_type}</div>
                                    </div>
                                    <div style="background: #f0f0f0; padding: 10px 15px; border-radius: 8px; text-align: center;">
                                        <div style="font-size: 12px; color: #666;">논증 강도</div>
                                        <div style="font-weight: bold;">{strength}점</div>
                                    </div>
                                    <div style="background: #f0f0f0; padding: 10px 15px; border-radius: 8px; text-align: center;">
                                        <div style="font-size: 12px; color: #666;">주장</div>
                                        <div style="font-weight: bold;">{has_claim}</div>
                                    </div>
                                    <div style="background: #f0f0f0; padding: 10px 15px; border-radius: 8px; text-align: center;">
                                        <div style="font-size: 12px; color: #666;">근거</div>
                                        <div style="font-weight: bold;">{has_reason}</div>
                                    </div>
                                    <div style="background: #f0f0f0; padding: 10px 15px; border-radius: 8px; text-align: center;">
                                        <div style="font-size: 12px; color: #666;">예시</div>
                                        <div style="font-weight: bold;">{has_example}</div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                        avg_strength = enhanced.get('avg_argument_strength', 0)
                        st.info(f"평균 논증 강도: **{avg_strength}점** / 100")

                    # 논리적 오류 감지
                    st.markdown("### 논리적 오류 감지")
                    fallacies = enhanced.get('fallacies', [])
                    if fallacies:
                        for f in fallacies:
                            severity_color = {"high": "#f44336", "medium": "#FF9800", "low": "#4CAF50"}.get(f.get('severity'), "#6b7280")
                            severity_kr = {"high": "심각", "medium": "주의", "low": "경미"}.get(f.get('severity'), "")
                            st.markdown(f"""
                            <div style="background: {severity_color}10; border-left: 4px solid {severity_color}; padding: 12px 15px; border-radius: 8px; margin: 10px 0;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-weight: bold; color: {severity_color};">{f.get('type', '').replace('_', ' ').title()}</span>
                                    <span style="font-size: 11px; background: {severity_color}20; color: {severity_color}; padding: 2px 8px; border-radius: 10px;">{severity_kr}</span>
                                </div>
                                <div style="font-size: 13px; color: #666; margin-top: 5px;">{f.get('description', '')}</div>
                                <div style="font-size: 13px; color: #333; margin-top: 5px;"><b>개선 제안:</b> {f.get('suggestion', '')}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.success("논리적 오류가 감지되지 않았습니다!")

                    # 반박 효과성
                    st.markdown("### 반박 효과성")
                    rebuttals = enhanced.get('rebuttal_analyses', [])
                    if rebuttals:
                        for r in rebuttals:
                            eff = r.get('effectiveness', 0)
                            eff_color = "#4CAF50" if eff >= 70 else "#FF9800" if eff >= 50 else "#f44336"
                            addr = "O" if r.get('addresses_opponent') else "X"
                            counter = "O" if r.get('provides_counter') else "X"
                            respect = "O" if r.get('maintains_respect') else "X"

                            st.markdown(f"""
                            <div style="background: #f8f9fa; padding: 12px 15px; border-radius: 8px; margin: 8px 0;">
                                <div style="font-weight: bold; margin-bottom: 8px;">발언 {r.get('statement_index', 0)}</div>
                                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                                    <span style="font-size: 12px;">효과성: <b style="color: {eff_color};">{eff}점</b></span>
                                    <span style="font-size: 12px;">상대 언급: <b>{addr}</b></span>
                                    <span style="font-size: 12px;">반론 제시: <b>{counter}</b></span>
                                    <span style="font-size: 12px;">존중 유지: <b>{respect}</b></span>
                                </div>
                                <div style="font-size: 12px; color: #666; margin-top: 5px;">{r.get('feedback', '')}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        avg_rebuttal = enhanced.get('avg_rebuttal_score', 0)
                        st.info(f"평균 반박 효과성: **{avg_rebuttal}점** / 100")
                    else:
                        st.info("반박 분석 데이터가 없습니다.")

                    # 토론 전략
                    st.markdown("### 토론 전략 분석")
                    strategy = enhanced.get('strategy', {})
                    dominant = strategy.get('dominant', 'balanced')
                    strategy_kr = {
                        'logical': '논리적 접근',
                        'emotional': '감성적 접근',
                        'data_driven': '데이터 중심',
                        'example_based': '사례 중심',
                        'balanced': '균형 잡힌 접근'
                    }.get(dominant, dominant)

                    st.markdown(f"""
                    <div style="background: #e3f2fd; padding: 15px; border-radius: 10px;">
                        <div style="font-weight: bold; color: #1976d2; font-size: 16px;">주요 전략: {strategy_kr}</div>
                        <div style="color: #666; margin-top: 8px;">{strategy.get('recommendation', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 개선 우선순위
                    st.markdown("### 개선 우선순위")
                    priorities = enhanced.get('improvement_priorities', [])
                    for i, p in enumerate(priorities):
                        st.markdown(f"**{i+1}.** {p}")

                    # 종합 피드백
                    st.divider()
                    st.markdown("### 종합 피드백")
                    st.info(enhanced.get('overall_feedback', ''))

                else:
                    st.info("논리력 분석 데이터를 불러오는 중...")

        with result_tabs[tab_idx["voice"]]:
            if st.session_state.debate_voice_analyses:
                st.subheader(" 음성 전달력 분석")

                # 종합 음성 분석
                combined = st.session_state.debate_combined_voice_analysis
                if combined and "error" not in combined:
                    # 등급 표시
                    grade = combined.get("grade", "N/A")
                    grade_colors = {"S": "#FFD700", "A": "#4CAF50", "B": "#2196F3", "C": "#FF9800", "D": "#f44336"}
                    grade_color = grade_colors.get(grade, "#6b7280")

                    st.markdown(f"""
                    <div style="text-align: center; padding: 20px; background: {grade_color}15; border-radius: 15px; margin-bottom: 20px;">
                        <div style="font-size: 60px; font-weight: bold; color: {grade_color};">{grade}</div>
                        <div style="color: #666;">음성 전달력 등급</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 세부 점수
                    col1, col2, col3, col4 = st.columns(4)
                    text_analysis = combined.get("text_analysis", {})
                    voice_quality = combined.get("voice_quality", {})

                    with col1:
                        wpm = text_analysis.get("words_per_minute", 0)
                        st.metric("말 속도", f"{wpm:.0f} WPM", delta="적정" if 120 <= wpm <= 150 else "조절 필요")

                    with col2:
                        fillers = text_analysis.get("filler_count", 0)
                        st.metric("필러 단어", f"{fillers}회", delta="좋음" if fillers < 5 else "줄이기 필요")

                    with col3:
                        clarity = voice_quality.get("pronunciation_clarity", 0)
                        st.metric("발음 명확도", f"{clarity}%")

                    with col4:
                        overall = combined.get("overall_score", 0)
                        st.metric("종합 점수", f"{overall}점")

                    # 개선 포인트
                    improvements = combined.get("priority_improvements", [])
                    if improvements:
                        st.markdown("### 우선 개선 포인트")
                        for imp in improvements[:3]:
                            st.markdown(f"- {imp}")

                # 발언별 음성 분석
                st.markdown("### 발언별 분석")
                user_statements = [h for h in st.session_state.debate_history if h.get("is_user")]
                for i, (stmt, va) in enumerate(zip(user_statements, st.session_state.debate_voice_analyses)):
                    with st.expander(f"발언 {i+1}: {stmt['content'][:50]}...", expanded=False):
                        if va:
                            ta = va.get("text_analysis", {})
                            vq = va.get("voice_quality", {})
                            cols = st.columns(4)
                            with cols[0]:
                                st.metric("말 속도", f"{ta.get('words_per_minute', 0):.0f} WPM")
                            with cols[1]:
                                st.metric("필러", f"{ta.get('filler_count', 0)}회")
                            with cols[2]:
                                st.metric("발음", f"{vq.get('pronunciation_clarity', 0)}%")
                            with cols[3]:
                                st.metric("점수", f"{va.get('overall_score', 0)}점")
            else:
                st.info("음성 입력을 사용하지 않아 음성 분석 데이터가 없습니다.")

        with result_tabs[tab_idx["content"]]:
            for h in st.session_state.debate_history:
                if h.get("is_user"):
                    st.markdown(get_user_debate_html(h['content'], st.session_state.debate_position), unsafe_allow_html=True)
                else:
                    st.markdown(
                        get_debater_avatar_html(
                            h['content'],
                            h.get('position', 'neutral'),
                            h['speaker']
                        ),
                        unsafe_allow_html=True
                    )

        # PDF 다운로드
        st.divider()
        if DEBATE_REPORT_AVAILABLE:
            position_kr = {"pro": "찬성", "con": "반대", "neutral": "중립"}[st.session_state.debate_position]
            try:
                pdf_bytes = generate_debate_report(
                    topic=st.session_state.debate_topic,
                    position=position_kr,
                    history=st.session_state.debate_history,
                    voice_analyses=st.session_state.debate_voice_analyses,
                    combined_voice_analysis=st.session_state.debate_combined_voice_analysis,
                    evaluation_result=st.session_state.debate_evaluation.get("result", "")
                )
                filename = get_debate_report_filename(st.session_state.debate_topic.get("topic", "토론"))

                st.download_button(
                    label= " PDF 리포트 다운로드",
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
        if st.button("같은 주제 다시 하기", use_container_width=True):
            st.session_state.debate_position = None
            st.session_state.debate_history = []
            st.session_state.debate_round = 0
            st.session_state.debate_completed = False
            st.session_state.debate_evaluation = None
            st.session_state.debate_audio_bytes_list = []
            st.session_state.debate_voice_analyses = []
            st.session_state.debate_combined_voice_analysis = None
            st.session_state.debate_response_times = []
            st.session_state.debate_enhanced_analysis = None
            st.session_state.debate_realtime_feedback = []
            st.rerun()

    with col2:
        if st.button("다른 주제 선택", type="primary", use_container_width=True):
            st.session_state.debate_topic = None
            st.session_state.debate_position = None
            st.session_state.debate_history = []
            st.session_state.debate_completed = False
            st.session_state.debate_evaluation = None
            st.session_state.debate_audio_bytes_list = []
            st.session_state.debate_voice_analyses = []
            st.session_state.debate_combined_voice_analysis = None
            st.session_state.debate_response_times = []
            st.session_state.debate_enhanced_analysis = None
            st.session_state.debate_realtime_feedback = []
            st.rerun()

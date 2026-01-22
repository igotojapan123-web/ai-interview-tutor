# pages/5_토론면접.py
# 그룹 토론면접 시뮬레이션 - 아바타/음성 기능 추가

import os
import random
import streamlit as st
import streamlit.components.v1 as components
import requests

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import LLM_MODEL_NAME, LLM_API_URL, LLM_TIMEOUT_SEC
from auth_utils import check_tester_password
from env_config import OPENAI_API_KEY

# 음성 유틸리티 import
try:
    from voice_utils import generate_tts_audio, get_audio_player_html, get_loud_audio_component
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

# 사용량 제한 시스템
try:
    from usage_limiter import check_and_use, get_remaining
    USAGE_LIMITER_AVAILABLE = True
except ImportError:
    USAGE_LIMITER_AVAILABLE = False

st.set_page_config(
    page_title="토론면접",
    page_icon="💬",
    layout="wide"
)

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="토론면접")
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
# 토론 주제
# =====================

DEBATE_TOPICS = [
    {
        "topic": "승무원에게 외모가 중요한가?",
        "background": "항공사 승무원 채용에서 외모 기준에 대한 논란이 있습니다. 서비스 직업의 특성상 단정한 외모가 필요하다는 의견과, 능력 중심으로 평가해야 한다는 의견이 있습니다.",
        "pro_points": ["첫인상의 중요성", "브랜드 이미지", "고객 기대"],
        "con_points": ["능력 중심 평가", "다양성 존중", "외모 차별 문제"],
    },
    {
        "topic": "기내에서 휴대폰 사용을 전면 허용해야 하는가?",
        "background": "기술 발전으로 비행기 모드가 일반화되었고, 일부 항공사는 Wi-Fi를 제공합니다. 하지만 여전히 안전 우려와 다른 승객 배려 문제가 있습니다.",
        "pro_points": ["기술 발전으로 안전 문제 해결", "승객 편의", "트렌드"],
        "con_points": ["안전 규정 준수", "다른 승객 배려", "비상시 집중력"],
    },
    {
        "topic": "LCC가 FSC를 대체할 수 있는가?",
        "background": "저가항공사(LCC)가 성장하면서 기존 대형항공사(FSC)의 입지가 줄어들고 있습니다. 가격 경쟁력과 서비스 품질 사이의 균형에 대한 논의가 필요합니다.",
        "pro_points": ["가격 경쟁력", "효율적 운영", "시장 점유율 증가"],
        "con_points": ["서비스 품질 차이", "장거리 노선 한계", "안전 투자"],
    },
    {
        "topic": "승무원 정년을 연장해야 하는가?",
        "background": "고령화 사회에서 정년 연장이 화두입니다. 경험 많은 승무원의 가치와 체력적 한계, 젊은 인력 채용 기회 사이의 균형이 필요합니다.",
        "pro_points": ["경험과 노하우", "고용 안정", "고령화 대응"],
        "con_points": ["체력적 한계", "신규 채용 기회", "서비스 활력"],
    },
    {
        "topic": "기내 서비스를 자동화해야 하는가?",
        "background": "AI와 로봇 기술의 발전으로 서비스 자동화가 가능해지고 있습니다. 효율성과 인간적 서비스 사이의 균형에 대한 논의가 필요합니다.",
        "pro_points": ["효율성 향상", "비용 절감", "일관된 서비스"],
        "con_points": ["인간적 교감", "유연한 대응", "일자리 감소"],
    },
    {
        "topic": "승무원이 SNS를 자유롭게 해도 되는가?",
        "background": "개인의 표현의 자유와 회사 이미지 관리 사이의 균형이 필요합니다. 일부 항공사는 SNS 가이드라인을 엄격히 적용합니다.",
        "pro_points": ["표현의 자유", "개인 브랜딩", "소통 채널"],
        "con_points": ["회사 이미지", "기밀 유지", "사생활 노출 위험"],
    },
    {
        "topic": "항공사는 환경보호를 위해 운항을 줄여야 하는가?",
        "background": "기후변화와 탄소 배출 문제로 항공 산업에 대한 비판이 있습니다. 지속가능한 항공과 경제적 현실 사이의 균형이 필요합니다.",
        "pro_points": ["환경 책임", "지속가능성", "사회적 요구"],
        "con_points": ["경제적 영향", "대안 부재", "다른 산업과 형평성"],
    },
    {
        "topic": "기내식을 유료화해야 하는가?",
        "background": "LCC는 이미 기내식을 유료로 제공하고 있으며, FSC도 일부 노선에서 유료화를 검토하고 있습니다.",
        "pro_points": ["비용 절감", "선택의 자유", "음식 낭비 감소"],
        "con_points": ["서비스 하락", "고객 불만", "차별화 요소 상실"],
    },
    {
        "topic": "승무원에게 외국어 능력이 필수인가?",
        "background": "글로벌 항공사의 경우 영어는 기본이고, 제2외국어까지 요구하는 경우가 있습니다. 언어 능력의 중요성에 대한 논의입니다.",
        "pro_points": ["글로벌 서비스", "안전 커뮤니케이션", "경쟁력"],
        "con_points": ["다른 역량도 중요", "국내선 위주", "번역 기술 발전"],
    },
    {
        "topic": "승객 블랙리스트 제도가 필요한가?",
        "background": "기내 난동, 성희롱 등 문제 승객에 대한 탑승 제한 제도에 대한 논의입니다. 안전과 인권 사이의 균형이 필요합니다.",
        "pro_points": ["승무원 보호", "다른 승객 안전", "재발 방지"],
        "con_points": ["인권 침해 우려", "기준 모호", "남용 가능성"],
    },
    {
        "topic": "비즈니스석과 이코노미석 서비스 차이가 정당한가?",
        "background": "같은 비행기에서 좌석에 따라 서비스 품질이 크게 다릅니다. 이러한 차등 서비스에 대한 논의입니다.",
        "pro_points": ["수익 구조", "고객 선택권", "프리미엄 서비스 가치"],
        "con_points": ["차별 느낌", "기본 서비스 저하", "사회적 위화감"],
    },
    {
        "topic": "코로나 이후 마스크 착용을 의무화해야 하는가?",
        "background": "팬데믹 이후 기내 위생과 건강에 대한 관심이 높아졌습니다. 개인 자유와 공중 보건 사이의 균형이 필요합니다.",
        "pro_points": ["감염 예방", "취약 승객 보호", "안심감 제공"],
        "con_points": ["개인 자유", "불편함", "과학적 근거"],
    },
]

# AI 토론자 페르소나 (아바타 추가)
DEBATERS = {
    "pro": {
        "name": "김찬성",
        "style": "논리적이고 데이터 중심으로 주장",
        "emoji": "👨‍💼",
        "color": "#3b82f6",
        "voice": "onyx",  # OpenAI TTS 남성 음성
    },
    "con": {
        "name": "이반대",
        "style": "감성적이고 사례 중심으로 반박",
        "emoji": "👩‍💼",
        "color": "#ef4444",
        "voice": "nova",  # OpenAI TTS 여성 음성
    },
    "neutral": {
        "name": "박중립",
        "style": "양측 의견을 조율하며 균형 잡힌 시각 제시",
        "emoji": "🧑‍💼",
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
            ">✈️</div>
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


def evaluate_debate(topic: dict, user_position: str, history: list) -> dict:
    """토론 평가"""
    api_key = get_api_key()
    if not api_key:
        return {"error": "API 키 없음"}

    user_statements = [h for h in history if h.get("is_user")]
    user_text = "\n".join([f"- {h['content']}" for h in user_statements])

    position_kr = {"pro": "찬성", "con": "반대", "neutral": "중립"}[user_position]

    system_prompt = """당신은 항공사 그룹면접 평가자입니다. 토론에서 지원자의 발언을 평가해주세요.
한국어로 상세하게 피드백해주세요."""

    user_prompt = f"""## 토론 주제
{topic['topic']}

## 지원자 입장
{position_kr}

## 지원자 발언 내용
{user_text}

## 평가 기준
1. 논리성: 주장이 논리적이고 일관성 있는가
2. 경청: 다른 의견을 경청하고 반응했는가
3. 표현력: 명확하고 설득력 있게 표현했는가
4. 태도: 토론 태도가 협력적이고 존중하는가
5. 리더십: 토론을 이끌거나 정리하는 모습이 있는가

## 출력 형식
### 종합 점수: X/100

### 항목별 평가
#### 논리성
- (평가)

#### 경청 & 반응
- (평가)

#### 표현력
- (평가)

#### 토론 태도
- (평가)

### 잘한 점
- (구체적으로)

### 개선할 점
- (구체적으로)

### 팁
(다음 토론을 위한 조언)
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


# =====================
# UI
# =====================

st.title("💬 토론면접 시뮬레이션")
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
        voice_mode = st.checkbox("🔊 음성 모드 (토론자 발언을 음성으로 듣기)", value=False)
        st.session_state.debate_voice_mode = voice_mode

    # 토론자 소개
    st.markdown("### 👥 AI 토론자 소개")
    cols = st.columns(3)
    for i, (key, debater) in enumerate(DEBATERS.items()):
        with cols[i]:
            position_kr = {"pro": "👍 찬성", "con": "👎 반대", "neutral": "⚖️ 중립"}[key]
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

    # 주제 선택
    st.subheader(f"📌 토론 주제 선택 ({len(DEBATE_TOPICS)}개)")

    for i, topic in enumerate(DEBATE_TOPICS):
        with st.expander(f"💬 {topic['topic']}", expanded=(i == 0)):
            st.write(topic["background"])

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**👍 찬성 측 논점**")
                for p in topic["pro_points"]:
                    st.write(f"• {p}")
            with col2:
                st.markdown("**👎 반대 측 논점**")
                for p in topic["con_points"]:
                    st.write(f"• {p}")

            if st.button("이 주제로 토론하기", key=f"select_{i}", type="primary", use_container_width=True):
                st.session_state.debate_topic = topic
                st.rerun()

elif st.session_state.debate_position is None:
    # 입장 선택
    topic = st.session_state.debate_topic

    st.subheader(f"📌 {topic['topic']}")
    st.write(topic["background"])

    st.divider()
    st.subheader("당신의 입장을 선택하세요")

    # 남은 사용량 표시
    if USAGE_LIMITER_AVAILABLE:
        remaining = get_remaining("토론면접")
        st.markdown(f"오늘 남은 횟수: **{remaining}회**")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: #3b82f610; border-radius: 15px; border: 2px solid #3b82f630;">
            <div style="font-size: 50px;">👍</div>
            <h3 style="color: #3b82f6;">찬성</h3>
        </div>
        """, unsafe_allow_html=True)
        for p in topic["pro_points"]:
            st.write(f"• {p}")
        if st.button("찬성으로 참여", use_container_width=True, type="primary"):
            if USAGE_LIMITER_AVAILABLE and not check_and_use("토론면접"):
                st.stop()
            st.session_state.debate_position = "pro"
            st.session_state.debate_history = []
            st.session_state.debate_round = 0
            st.rerun()

    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: #ef444410; border-radius: 15px; border: 2px solid #ef444430;">
            <div style="font-size: 50px;">👎</div>
            <h3 style="color: #ef4444;">반대</h3>
        </div>
        """, unsafe_allow_html=True)
        for p in topic["con_points"]:
            st.write(f"• {p}")
        if st.button("반대로 참여", use_container_width=True, type="primary"):
            if USAGE_LIMITER_AVAILABLE and not check_and_use("토론면접"):
                st.stop()
            st.session_state.debate_position = "con"
            st.session_state.debate_history = []
            st.session_state.debate_round = 0
            st.rerun()

    with col3:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: #8b5cf610; border-radius: 15px; border: 2px solid #8b5cf630;">
            <div style="font-size: 50px;">⚖️</div>
            <h3 style="color: #8b5cf6;">중립</h3>
        </div>
        """, unsafe_allow_html=True)
        st.write("• 양측 의견 조율")
        st.write("• 균형 잡힌 시각")
        if st.button("중립으로 참여", use_container_width=True):
            if USAGE_LIMITER_AVAILABLE and not check_and_use("토론면접"):
                st.stop()
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
        st.subheader(f"📌 {topic['topic']}")
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
                    debater.get('emoji', '👤'),
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
                if st.button(f"🔊 듣기", key=f"listen_{idx}_{h['content'][:10]}"):
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
        user_input = st.chat_input("토론에 참여하세요...")

        if user_input:
            st.session_state.debate_history.append({
                "speaker": f"나 ({position_kr})",
                "content": user_input,
                "position": position,
                "is_user": True,
            })

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

            if st.session_state.debate_round >= 4:
                st.session_state.debate_completed = True

            st.rerun()

        if st.session_state.debate_round >= 2:
            if st.button("토론 종료하기", type="primary", use_container_width=True):
                st.session_state.debate_completed = True
                st.rerun()

else:
    # 토론 완료 - 평가
    st.subheader("🎉 토론 완료!")

    if st.session_state.debate_evaluation is None:
        with st.spinner("토론 내용을 평가하고 있습니다..."):
            evaluation = evaluate_debate(
                st.session_state.debate_topic,
                st.session_state.debate_position,
                st.session_state.debate_history
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
        st.rerun()
    else:
        with st.expander("📜 토론 내용 보기", expanded=False):
            for h in st.session_state.debate_history:
                if h.get("is_user"):
                    st.markdown(f"**나**: {h['content']}")
                else:
                    st.markdown(f"**{h['speaker']}**: {h['content']}")
                st.divider()

        st.subheader("📊 평가 결과")
        eval_result = st.session_state.debate_evaluation
        if "error" in eval_result:
            st.error(f"평가 오류: {eval_result['error']}")
        else:
            st.markdown(eval_result.get("result", ""))

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("같은 주제 다시 하기", use_container_width=True):
            st.session_state.debate_position = None
            st.session_state.debate_history = []
            st.session_state.debate_round = 0
            st.session_state.debate_completed = False
            st.session_state.debate_evaluation = None
            st.rerun()

    with col2:
        if st.button("다른 주제 선택", type="primary", use_container_width=True):
            st.session_state.debate_topic = None
            st.session_state.debate_position = None
            st.session_state.debate_history = []
            st.session_state.debate_completed = False
            st.session_state.debate_evaluation = None
            st.rerun()

# pages/1_롤플레잉.py
# flyready_lab - 롤플레잉 시뮬레이션 (Premium Version)

import os

from logging_config import get_logger
logger = get_logger(__name__)
import json
import time
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
import requests

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import LLM_MODEL_NAME, LLM_API_URL, LLM_TIMEOUT_SEC
from env_config import OPENAI_API_KEY
from roleplay_scenarios import (
    SCENARIO_CATEGORIES, SCENARIOS,
    get_scenarios_by_category, get_scenario_by_id, get_all_scenarios
)

# 음성/영상 유틸리티 import
try:
    from video_utils import get_fallback_avatar_html
    from voice_utils import (
        generate_tts_audio, get_audio_player_html,
        get_voice_for_persona, transcribe_audio,
        generate_tts_for_passenger, is_clova_available,
        get_loud_audio_component, analyze_voice_complete,
    )
    from animation_components import (
        render_animated_passenger,
        render_animated_crew,
        render_roleplay_scene
    )
    UTILS_AVAILABLE = True
    ANIMATION_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
    ANIMATION_AVAILABLE = False

# 점수 자동 저장 유틸리티
try:
    from score_utils import save_practice_score, parse_evaluation_score
    SCORE_UTILS_AVAILABLE = True
except ImportError:
    SCORE_UTILS_AVAILABLE = False

# PDF 리포트 및 추천 유틸리티
try:
    from roleplay_report import (
        generate_roleplay_report, get_report_filename,
        get_weakness_recommendations
    )
    REPORT_AVAILABLE = True
except ImportError:
    REPORT_AVAILABLE = False


from sidebar_common import render_sidebar

st.set_page_config(
    page_title="롤플레잉 시뮬레이션 | FlyReady Lab",
    page_icon="✈️",
    layout="wide"
)
render_sidebar("롤플레잉")



# 구글 번역 방지
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# CSS 스타일
CSS_STYLES = """
<style>
html{translate:no}
.emotion-gauge-container{background:#fff;border-radius:15px;padding:20px;box-shadow:0 4px 15px rgba(0,0,0,0.1);margin-bottom:20px}
.emotion-gauge{height:12px;background:linear-gradient(90deg,#10b981 0%,#f59e0b 50%,#ef4444 100%);border-radius:6px;position:relative;margin:15px 0}
.emotion-indicator{position:absolute;top:-8px;width:28px;height:28px;background:#fff;border-radius:50%;box-shadow:0 2px 8px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;font-size:16px;transition:left 0.5s ease}
.emotion-labels{display:flex;justify-content:space-between;font-size:12px;color:#666}
.hint-box{background:linear-gradient(135deg,#fef3c7,#fde68a);border-left:4px solid #f59e0b;border-radius:10px;padding:15px 20px;margin:15px 0}
.timer-container{background:linear-gradient(135deg,#1e3a5f,#2d5a87);border-radius:15px;padding:15px 25px;text-align:center;color:#fff}
.timer-display{font-size:2.5rem;font-weight:bold;font-family:'Courier New',monospace}
.progress-container{background:#f0f0f0;border-radius:10px;height:8px;overflow:hidden;margin:10px 0}
.progress-bar{height:100%;background:linear-gradient(90deg,#2563eb,#3b82f6);border-radius:10px;transition:width 0.3s ease}
.premium-badge{background:linear-gradient(135deg,#f59e0b,#fbbf24);color:#fff;font-size:10px;padding:3px 8px;border-radius:10px;font-weight:bold}
</style>
"""
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# ----------------------------
# 비밀번호 보호
# ----------------------------

# =====================
# 프리미엄 기능 체크
# =====================
def is_premium_user():
    """프리미엄 사용자 여부 체크"""
    return st.session_state.get("is_premium", True)  # 개발 중이므로 True

def get_daily_usage():
    """일일 사용량 체크"""
    today = datetime.now().strftime("%Y-%m-%d")
    usage_key = f"rp_usage_{today}"
    return st.session_state.get(usage_key, 0)

def increment_usage():
    """사용량 증가"""
    today = datetime.now().strftime("%Y-%m-%d")
    usage_key = f"rp_usage_{today}"
    st.session_state[usage_key] = st.session_state.get(usage_key, 0) + 1

# =====================
# 진행률 관리
# =====================
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "roleplay_progress.json")

def load_progress():
    """진행률 로드"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.debug(f"진행률 로드 실패: {e}")
            return {"completed": [], "scores": {}, "history": []}
    return {"completed": [], "scores": {}, "history": []}

def save_progress(progress):
    """진행률 저장"""
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"진행률 저장 실패: {e}")

def mark_completed(scenario_id, score, conversation):
    """시나리오 완료 표시"""
    progress = load_progress()
    if scenario_id not in progress["completed"]:
        progress["completed"].append(scenario_id)
    progress["scores"][scenario_id] = max(progress["scores"].get(scenario_id, 0), score)

    # 히스토리 저장 (최대 20개)
    history_entry = {
        "scenario_id": scenario_id,
        "score": score,
        "timestamp": datetime.now().isoformat(),
        "conversation": conversation[-6:] if len(conversation) > 6 else conversation  # 최근 6개 메시지만
    }
    progress["history"].insert(0, history_entry)
    progress["history"] = progress["history"][:20]

    save_progress(progress)

# =====================
# 감정 게이지 컴포넌트
# =====================
def render_emotion_gauge(level: int, previous_level: int = None):
    """감정 게이지 렌더링"""
    percent = level * 50
    emojis = {0: "😊", 1: "😤", 2: "😡"}
    labels = {0: ("평온", "#10b981"), 1: ("짜증", "#f59e0b"), 2: ("분노", "#ef4444")}
    current_emoji = emojis.get(level, "😊")
    label, color = labels.get(level, labels[0])

    # 감정 변화 표시
    if previous_level is not None and previous_level != level:
        if level > previous_level:
            st.error("승객이 더 화났습니다!")
        else:
            st.success("승객이 진정되었습니다")

    # 감정 게이지를 Streamlit 기본 컴포넌트로 표현
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.markdown(f"**승객 감정**")
    with col2:
        st.progress(percent / 100)
    with col3:
        st.markdown(f"<span style='font-size:28px'>{current_emoji}</span> **{label}**", unsafe_allow_html=True)

# =====================
# 힌트 시스템
# =====================
def get_hint(scenario: dict, escalation_level: int, turn: int) -> str:
    """상황에 맞는 힌트 생성"""
    keywords = scenario.get("ideal_response_keywords", [])
    criteria = scenario.get("evaluation_criteria", {})

    hints = []

    # 감정 레벨별 힌트
    if escalation_level == 0:
        hints.append("먼저 승객의 요청에 공감을 표현해보세요")
    elif escalation_level == 1:
        hints.append("승객이 짜증을 내고 있어요. 진심 어린 사과와 함께 대안을 제시해보세요")
    else:
        hints.append("승객이 많이 화났습니다! 차분하게 경청하고 구체적인 해결책을 제시하세요")

    # 키워드 기반 힌트
    if keywords:
        keyword_hint = f"핵심 포인트: {', '.join(keywords[:3])}"
        hints.append(keyword_hint)

    # 턴별 힌트
    if turn == 0:
        hints.append("첫 응대가 중요합니다. 인사와 함께 어떻게 도와드릴지 물어보세요")
    elif turn >= 3:
        hints.append("마무리 단계입니다. 승객이 만족할 수 있는 결론을 지어보세요")

    return hints[turn % len(hints)] if hints else "승객의 말을 경청하고 공감해보세요"

def render_hint_box(hint: str, show_hint: bool):
    """힌트 박스 렌더링"""
    if show_hint and is_premium_user():
        st.info(f"**힌트:** {hint}")

# =====================
# 타이머 컴포넌트 (실시간 카운트다운)
# =====================
def render_realtime_timer(total_seconds: int = 30, timer_start: float = None, is_paused: bool = False):
    """실시간 카운트다운 타이머 - 일시정지 지원"""
    if timer_start is None:
        timer_start = time.time()

    elapsed = time.time() - timer_start
    remaining = max(0, total_seconds - int(elapsed))

    if is_paused:
        # 일시정지 상태 - 타이머 멈춤
        timer_html = f'''
        <div style="background:linear-gradient(135deg,#6b7280,#9ca3af);border-radius:15px;padding:15px 25px;text-align:center;color:#fff;margin:10px 0">
            <div style="font-size:12px;margin-bottom:5px">⏸️ 일시정지</div>
            <div style="font-size:2.5rem;font-weight:bold;font-family:Courier New,monospace">{remaining:02d}</div>
            <div style="background:rgba(255,255,255,0.2);height:6px;border-radius:3px;margin-top:10px;overflow:hidden">
                <div style="height:100%;background:#9ca3af;border-radius:3px;width:{(remaining/total_seconds)*100}%"></div>
            </div>
            <div style="font-size:10px;margin-top:5px;opacity:0.8">음성 재생 중...</div>
        </div>
        '''
        components.html(timer_html, height=130)
    else:
        # 실시간 카운트다운
        # 색상 결정
        if remaining <= 5:
            bg_color = "linear-gradient(135deg,#dc2626,#ef4444)"
            bar_color = "#ef4444"
            text_color = "#fff"
        elif remaining <= 10:
            bg_color = "linear-gradient(135deg,#d97706,#f59e0b)"
            bar_color = "#f59e0b"
            text_color = "#fff"
        else:
            bg_color = "linear-gradient(135deg,#1e3a5f,#2d5a87)"
            bar_color = "#10b981"
            text_color = "#fff"

        timer_html = f'''
        <div id="timer-container" style="background:{bg_color};border-radius:15px;padding:15px 25px;text-align:center;color:{text_color};margin:10px 0">
            <div style="font-size:12px;margin-bottom:5px">⏱️ 응답 시간</div>
            <div id="timer-display" style="font-size:2.5rem;font-weight:bold;font-family:Courier New,monospace">{remaining:02d}</div>
            <div style="background:rgba(255,255,255,0.2);height:6px;border-radius:3px;margin-top:10px;overflow:hidden">
                <div id="timer-bar" style="height:100%;background:{bar_color};border-radius:3px;transition:width 1s linear;width:{(remaining/total_seconds)*100}%"></div>
            </div>
        </div>
        <script>
            (function() {{
                var remaining = {remaining};
                var total = {total_seconds};
                var display = document.getElementById('timer-display');
                var bar = document.getElementById('timer-bar');
                var container = document.getElementById('timer-container');
                if (!display || !bar || !container) return;

                function updateTimer() {{
                    if (remaining <= 0) {{
                        display.textContent = '00';
                        display.style.color = '#fff';
                        container.style.background = 'linear-gradient(135deg,#dc2626,#ef4444)';
                        return;
                    }}
                    remaining--;
                    display.textContent = remaining.toString().padStart(2, '0');
                    bar.style.width = ((remaining / total) * 100) + '%';

                    if (remaining <= 5) {{
                        container.style.background = 'linear-gradient(135deg,#dc2626,#ef4444)';
                        bar.style.background = '#ef4444';
                    }} else if (remaining <= 10) {{
                        container.style.background = 'linear-gradient(135deg,#d97706,#f59e0b)';
                        bar.style.background = '#f59e0b';
                    }}
                }}
                setInterval(updateTimer, 1000);
            }})();
        </script>
        '''
        components.html(timer_html, height=120)

def render_response_time(seconds: int):
    """응답에 걸린 시간 표시"""
    if seconds < 10:
        color = "#10b981"
        label = "빠른 응답"
    elif seconds < 20:
        color = "#f59e0b"
        label = "적절한 응답"
    else:
        color = "#ef4444"
        label = "느린 응답"
    st.markdown(f'<span style="color:{color};font-size:12px">⏱️ {seconds}초 ({label})</span>', unsafe_allow_html=True)

# =====================
# 모범 답안 생성
# =====================
def generate_ideal_response(scenario: dict, conversation: list, user_message: str) -> str:
    """해당 상황의 모범 답안 생성"""
    api_key = get_api_key()
    if not api_key:
        return ""

    keywords = scenario.get("ideal_response_keywords", [])
    criteria = scenario.get("evaluation_criteria", {})

    system_prompt = f"""당신은 10년차 베테랑 항공 승무원입니다.
주어진 상황에서 가장 이상적인 응대를 1-2문장으로 작성하세요.

## 상황
{scenario['situation']}

## 승객
{scenario['passenger_persona']}

## 핵심 포인트
{', '.join(keywords)}

## 평가 기준
{json.dumps(criteria, ensure_ascii=False)}

## 규칙
1. 실제 승무원이 말하는 것처럼 자연스럽게
2. 공감 + 해결책을 모두 포함
3. 1-2문장으로 간결하게
4. 괄호나 설명 없이 대사만
"""

    # 대화 컨텍스트
    conv_text = "\n".join([f"{'승객' if m['role']=='passenger' else '승무원'}: {m['content']}" for m in conversation[-4:]])

    user_prompt = f"""최근 대화:
{conv_text}

지원자의 응답: {user_message}

위 상황에서 베테랑 승무원이라면 어떻게 응대했을지 모범 답안을 작성하세요.
대사만 출력하세요."""

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
            "max_tokens": 150,
        }

        r = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=LLM_TIMEOUT_SEC)
        r.raise_for_status()
        resp = r.json()

        choices = resp.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()
        return ""
    except Exception as e:
        logger.debug(f"모범 답안 생성 실패: {e}")
        return ""

# =====================
# 승객 아바타 함수
# =====================
def get_persona_emoji(persona: str) -> str:
    """페르소나에서 나이/성별에 맞는 이모지 반환"""
    if '임산부' in persona:
        return "🤰"
    if '어린이' in persona or '아이' in persona or '아동' in persona:
        return "👧"
    if '어린이 동반' in persona or '아이 동반' in persona:
        return "👨‍👧"
    if '외국인' in persona:
        return "🧑‍🦰"
    if '장애인' in persona or '휠체어' in persona:
        return "🧑‍🦽"
    if '사업가' in persona or 'VIP' in persona:
        return "👨‍💼"

    is_female = any(kw in persona for kw in ['여성', '엄마', '할머니', '여자', '부인', '아줌마', '언니'])
    is_male = any(kw in persona for kw in ['남성', '아빠', '할아버지', '남자', '아저씨']) and not is_female

    is_elderly = any(kw in persona for kw in ['60대', '70대', '80대', '어르신', '할머니', '할아버지', '노인'])
    is_middle_aged = any(kw in persona for kw in ['50대', '40대'])
    is_young = any(kw in persona for kw in ['20대', '30대', '대학생', '직장인', '젊은'])

    if is_elderly:
        return "👵" if is_female else "👴"
    elif is_middle_aged:
        return "👩" if is_female else "👨"
    elif is_young:
        return "👩‍💼" if is_female and '직장인' in persona else "👩" if is_female else "🧑"
    return "👩" if is_female else "👨" if is_male else "🧑"


def get_passenger_avatar_html(message: str, persona: str, escalation_level: int = 0, is_speaking: bool = False) -> str:
    """승객 캐릭터 아바타 HTML 생성"""
    level_config = {0: ("#3b82f6", "평온", "😊"), 1: ("#f59e0b", "짜증", "😤"), 2: ("#ef4444", "분노", "😡")}
    color, mood, emoji = level_config.get(escalation_level, level_config[0])
    icon = get_persona_emoji(persona)
    return f'<div style="display:flex;gap:15px;padding:20px;background:linear-gradient(135deg,{color}22,{color}11);border-left:5px solid {color};border-radius:15px;margin:15px 0"><div style="font-size:50px;min-width:70px;text-align:center"><div>{icon}</div><div style="font-size:28px;margin-top:5px">{emoji}</div></div><div style="flex:1"><div style="font-size:12px;color:{color};font-weight:bold;margin-bottom:8px">승객 <span style="background:{color}22;padding:3px 10px;border-radius:10px;font-size:11px">{mood}</span></div><div style="background:white;padding:18px 22px;border-radius:15px;font-size:16px;color:#333;box-shadow:0 3px 10px rgba(0,0,0,0.1);line-height:1.7">{message}</div></div></div>'


def get_crew_response_html(message: str) -> str:
    """승무원 응답 HTML 생성"""
    return f'<div style="display:flex;gap:15px;padding:20px;background:linear-gradient(135deg,#10b98122,#10b98111);border-right:5px solid #10b981;border-radius:15px;margin:15px 0;flex-direction:row-reverse"><div style="font-size:50px;min-width:70px;text-align:center"><div>👩‍✈️</div><div style="font-size:12px;color:#10b981;margin-top:5px">승무원</div></div><div style="flex:1;text-align:right"><div style="font-size:12px;color:#10b981;font-weight:bold;margin-bottom:8px">✈️ 당신 (승무원)</div><div style="background:white;padding:18px 22px;border-radius:15px;font-size:16px;color:#333;box-shadow:0 3px 10px rgba(0,0,0,0.1);line-height:1.7;display:inline-block;text-align:left">{message}</div></div></div>'


# =====================
# 세션 상태 초기화
# =====================
defaults = {
    "rp_scenario": None,
    "rp_ready": False,  # 설정 완료 후 시작 여부
    "rp_messages": [],
    "rp_turn": 0,
    "rp_ended": False,
    "rp_evaluation": None,
    "rp_escalation_level": 0,
    "rp_previous_level": 0,
    "rp_voice_mode": False,
    "rp_passenger_voice": False,  # 승객 음성 재생 여부 (별도)
    "rp_last_transcription": None,
    "rp_show_hint": True,
    "rp_timer_enabled": True,  # 기본 활성화
    "rp_timer_start": None,
    "rp_timer_paused_at": None,  # 타이머 일시정지 시점
    "rp_audio_playing": False,  # 오디오 재생 중 여부
    "rp_ideal_responses": [],
    "rp_filter_category": "전체",
    "rp_filter_difficulty": "전체",
    "rp_response_times": [],  # 각 응답별 소요 시간 저장
    "rp_audio_bytes_list": [],  # 각 응답별 음성 데이터 저장
    "rp_voice_analysis": None,  # 음성 분석 결과
    "rp_processed_audio_id": None,  # 처리된 오디오 ID (중복 방지)
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =====================
# LLM 호출 함수
# =====================
def get_api_key():
    return (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENAI_APIKEY")
        or os.getenv("OPENAI_KEY")
        or ""
    )


def generate_passenger_response(scenario: dict, conversation: list, user_message: str, escalation_level: int) -> str:
    """AI 승객 응답 생성"""
    api_key = get_api_key()
    if not api_key:
        return "[API 키가 설정되지 않았습니다]"

    persona = scenario['passenger_persona']

    # 나이대별 한국인 특성 정의
    if any(x in persona for x in ['60대', '70대', '어르신', '할머니', '할아버지']):
        age_character = '''
## 🧓 60-70대 한국인 어르신 특징
- **기본적으로 반말 섞어 씀** (존댓말이다가 갑자기 반말)
- 말이 길고 사연을 붙임
- "아이고", "휴", "어휴" 많이 씀
- 화나면 "아니 이게 뭐야", "도대체" 이런 표현

### 감정별 말투:
**평상시**: "아이고, 저기요... 이게요, 내가 비행기를 처음 타봐서 그러는데요..."
**짜증날 때**: "아니 근데요, 내가 이 나이에... 어휴..."
**화났을 때**: "아니 이게 뭐야! 손님한테 이렇게 하면 어떡해!"'''

    elif any(x in persona for x in ['50대']) and any(x in persona for x in ['여성', '엄마', '아줌마']):
        age_character = '''
## 👩 50대 한국 아줌마 특징
- 말 빠르고 감정 표현 직접적
- "아니 근데요", "그러니까요" 자주 씀

### 감정별 말투:
**평상시**: "저기요, 잠깐만요..."
**짜증날 때**: "아니 그러니까요, 왜 안 되는 건데요?"
**화났을 때**: "아니 진짜 어이가 없네!"'''

    elif any(x in persona for x in ['40대', '사업가', 'VIP']):
        age_character = '''
## 👔 40대 사업가/VIP 특징
- 자신감 있고 당당함
- 빠른 해결 요구

### 감정별 말투:
**평상시**: "확인 좀 해주세요."
**짜증날 때**: "이 정도 요청은 들어줘야 하는 거 아닙니까?"
**화났을 때**: "고객 서비스가 이게 뭡니까?"'''

    elif any(x in persona for x in ['30대', '직장인']):
        age_character = '''
## 👩‍💼 30대 직장인 특징
- 논리적이고 이성적
- 기본 예의는 있지만 불만은 표현

### 감정별 말투:
**평상시**: "혹시... 가능할까요?"
**짜증날 때**: "근데요, 정말 방법이 없는 건가요?"
**화났을 때**: "하아... 진짜 답답하네요."'''

    elif any(x in persona for x in ['20대', '대학생']):
        age_character = '''
## 🧑 20대 젊은이 특징
- 솔직하고 직설적
- 존댓말 쓰지만 캐주얼

### 감정별 말투:
**평상시**: "저기요, 혹시... 가능해요?"
**짜증날 때**: "아... 진짜요? 왜 안 되는 거예요?"
**화났을 때**: "아 진짜... 이건 좀 아니지 않아요?"'''

    else:
        age_character = '''
## 일반 성인 특징
- 기본 존댓말
- 불만은 있지만 참으려 함'''

    emotion_guide = {
        0: "**지금 감정: 기본 상태** - 정중하게 요청하는 중",
        1: "**지금 감정: 짜증남** - 답답하고 불만 표출 시작. 한숨, '아니 근데요' 표현",
        2: "**지금 감정: 화남** - 확실히 화난 상태. 목소리 높이고 직접적 불만",
    }

    system_prompt = f"""당신은 실제 한국인 항공기 승객입니다.

## 상황
{scenario['situation']}

## 캐릭터
{scenario['passenger_persona']}

{age_character}

---

## 🔥 {emotion_guide.get(escalation_level, emotion_guide[0])}

---

## ⚠️ 절대 규칙
1. **감정 레벨에 맞게 말해!**
2. **1~2문장만!** 길게 쓰지 마.
3. **괄호, 설명, 지문 절대 쓰지 마!** 대사만!

## 출력
승객 대사만. 지금 감정 상태에 맞게!"""

    messages = [{"role": "system", "content": system_prompt}]

    for msg in conversation:
        role = "assistant" if msg["role"] == "passenger" else "user"
        messages.append({"role": role, "content": msg["content"]})

    messages.append({"role": "user", "content": f"[승무원이 말합니다]: {user_message}"})

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
        return "[응답 생성 실패]"

    except Exception as e:
        return f"[오류: {str(e)}]"


def evaluate_conversation(scenario: dict, conversation: list) -> dict:
    """대화 내용 평가"""
    api_key = get_api_key()
    if not api_key:
        return {"error": "API 키 없음"}

    crew_messages = [msg["content"] for msg in conversation if msg["role"] == "crew"]
    crew_text = "\n".join([f"- {m}" for m in crew_messages])

    criteria = scenario.get("evaluation_criteria", {})
    criteria_text = "\n".join([f"- {k}: {v}" for k, v in criteria.items()])
    keywords = ", ".join(scenario.get("ideal_response_keywords", []))

    system_prompt = """당신은 10년차 항공사 객실 승무원 출신 면접관입니다.
지원자의 롤플레잉 대응을 실제 기내 상황 기준으로 엄격하게 평가합니다.

## ⚠️ 평가 원칙
1. **절대 후한 점수를 주지 마세요.** 실제 면접처럼 냉정하게.
2. **평균 점수는 50~60점대가 정상.** 80점 이상은 정말 잘한 경우만."""

    user_prompt = f"""## 시나리오
{scenario['situation']}

## 평가 기준
{criteria_text}

## 이상적인 대응 키워드
{keywords}

## 지원자(승무원)의 대응
{crew_text}

---

## 평가 형식

### 종합 점수
**100점 만점에 ??점**

### 항목별 평가
| 항목 | 점수 | 이유 |
|------|------|------|
| 공감 표현 | ?/25 | (이유) |
| 해결책 제시 | ?/25 | (이유) |
| 전문성 | ?/25 | (이유) |
| 태도/말투 | ?/25 | (이유) |

### 💚 잘한 점
- (구체적으로)

### 🔴 개선할 점
- (구체적으로)

### 📝 모범 답안
"(이렇게 말했으면 좋았을 대사)"
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


def check_escalation(scenario: dict, user_message: str, current_level: int) -> int:
    """에스컬레이션 레벨 체크 - 더 민감하게"""
    message_lower = user_message.lower()

    # 매우 나쁜 응대 (즉시 분노)
    very_bad_patterns = ["꺼져", "닥쳐", "시끄러", "짜증", "귀찮", "알아서", "니가", "네가 알아서", "그건 니 문제", "내 알 바"]
    very_bad_count = sum(1 for bp in very_bad_patterns if bp in message_lower)
    if very_bad_count > 0:
        return 2  # 즉시 분노

    # 나쁜 응대 패턴 (확장)
    bad_patterns = [
        "안 돼", "안돼", "안됩니다", "불가능", "규정상", "못 해", "못해", "못합니다",
        "참으세요", "어쩔 수 없", "어쩔수없", "기다리세요", "기다려", "나중에",
        "제가 뭘", "왜요", "그건 안", "그게 왜", "원래 그래", "다 그래",
        "모르겠", "글쎄요", "잘 모르", "저도 모", "안 되는데", "힘들"
    ]
    bad_count = sum(1 for bp in bad_patterns if bp in message_lower)

    # 무성의한 응대 (짧은 응답)
    if len(user_message.strip()) < 10:
        bad_count += 1

    # 공감 표현 체크
    empathy_patterns = ["죄송", "불편", "이해", "공감", "힘드시", "걱정", "안심", "감사", "말씀", "어려우시", "미안", "송구"]
    empathy_count = sum(1 for ep in empathy_patterns if ep in message_lower)

    # 해결책 제시 체크
    solution_patterns = ["확인", "알아보", "찾아", "다른", "대신", "방법", "해결", "도와드", "준비", "가져다", "바로"]
    solution_count = sum(1 for sp in solution_patterns if sp in message_lower)

    # 존댓말 체크
    polite_endings = ["요", "니다", "세요", "십시오", "습니다", "드릴", "겠습"]
    polite_count = sum(1 for pe in polite_endings if message_lower.endswith(pe) or pe in message_lower)

    # 레벨 조정 (더 엄격하게)
    if empathy_count >= 2 and solution_count >= 1 and polite_count >= 1:
        return max(0, current_level - 1)  # 감정 완화 (공감 + 해결책 + 존댓말)
    elif empathy_count >= 1 and solution_count >= 1:
        return current_level  # 유지 (적절한 응대)
    elif bad_count >= 1:
        return min(2, current_level + 1)  # 감정 악화 (나쁜 표현 1개만 있어도)
    elif empathy_count == 0 and solution_count == 0:
        return min(2, current_level + 1)  # 감정 악화 (공감도 해결책도 없음)
    elif polite_count == 0:
        return min(2, current_level + 1)  # 감정 악화 (반말)

    return current_level


# =====================
# UI 시작
# =====================
st.title("롤플레잉 시뮬레이션")
st.caption("AI 승객과 대화하며 기내 상황 대응 연습을 해보세요")

# 상단 상태 표시
progress = load_progress()
completed_count = len(progress.get("completed", []))
total_count = len(SCENARIOS)

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.markdown(f"**진행률:** {completed_count}/{total_count} 시나리오 완료")
    st.markdown(f'<div class="progress-container"><div class="progress-bar" style="width:{(completed_count/total_count)*100}%"></div></div>', unsafe_allow_html=True)
with col2:
    if not is_premium_user():
        daily = get_daily_usage()
        st.warning(f"오늘 {daily}/3회 사용")
with col3:
    if not is_premium_user():
        st.markdown('<span class="premium-badge">프리미엄으로 무제한</span>', unsafe_allow_html=True)

st.divider()

# 시나리오 선택 또는 진행 중
if st.session_state.rp_scenario is None:
    # 필터
    col1, col2 = st.columns(2)
    with col1:
        category_options = ["전체"] + SCENARIO_CATEGORIES
        st.session_state.rp_filter_category = st.selectbox(
            "카테고리",
            category_options,
            index=category_options.index(st.session_state.rp_filter_category)
        )
    with col2:
        difficulty_options = ["전체", "⭐ 쉬움", "⭐⭐ 보통", "⭐⭐⭐ 어려움", "⭐⭐⭐⭐ 매우 어려움"]
        st.session_state.rp_filter_difficulty = st.selectbox(
            "난이도",
            difficulty_options
        )

    # 시나리오 목록
    st.subheader("시나리오 선택")

    all_scenarios = get_all_scenarios()

    # 필터 적용
    filtered = all_scenarios
    if st.session_state.rp_filter_category != "전체":
        filtered = [s for s in filtered if s["category"] == st.session_state.rp_filter_category]
    if st.session_state.rp_filter_difficulty != "전체":
        diff_level = difficulty_options.index(st.session_state.rp_filter_difficulty)
        filtered = [s for s in filtered if s["difficulty"] == diff_level]

    # 시나리오 카드 표시
    for sc in filtered:
        is_completed = sc["id"] in progress.get("completed", [])
        best_score = progress.get("scores", {}).get(sc["id"], 0)

        difficulty_stars = "⭐" * sc["difficulty"]
        completed_badge = "✅ 완료" if is_completed else ""
        score_badge = f"최고 {best_score}점" if best_score > 0 else ""

        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                status_badges = " | ".join(filter(None, [completed_badge, score_badge]))
                st.markdown(f"**{sc['title']}** {difficulty_stars}")
                if status_badges:
                    st.caption(status_badges)
                st.caption(f"📂 {sc['category']} | 🎭 {sc['passenger_persona']}")
                st.caption(f"{sc['situation'][:80]}...")

            with col2:
                btn_label = "다시하기" if is_completed else "선택"
                if st.button(btn_label, key=f"start_{sc['id']}", use_container_width=True):
                    # 무료 사용자 제한 체크
                    if not is_premium_user() and get_daily_usage() >= 3:
                        st.error("오늘 무료 사용량을 모두 사용했습니다. 프리미엄으로 업그레이드하세요!")
                    else:
                        # 시나리오만 선택, 아직 시작 안함
                        st.session_state.rp_scenario = sc
                        st.session_state.rp_ready = False
                        st.rerun()

            st.markdown("---")

    # 복습 섹션
    if progress.get("history") and is_premium_user():
        st.subheader("최근 연습 기록")
        for i, hist in enumerate(progress["history"][:5]):
            sc_id = hist.get("scenario_id", "")
            sc_info = get_scenario_by_id(sc_id)
            if sc_info:
                with st.expander(f"{sc_info['title']} - {hist.get('score', 0)}점 ({hist.get('timestamp', '')[:10]})"):
                    for msg in hist.get("conversation", []):
                        role = "승객" if msg.get("role") == "passenger" else "승무원"
                        st.markdown(f"**{role}:** {msg.get('content', '')}")

elif not st.session_state.rp_ready:
    # =====================
    # 설정 화면 (시나리오 선택 후, 시작 전)
    # =====================
    scenario = st.session_state.rp_scenario

    st.markdown(f'<div style="background:linear-gradient(135deg,#1e3a5f,#2d5a87);padding:25px;border-radius:15px;margin-bottom:20px"><h2 style="color:#fff;margin:0 0 15px 0">🎬 {scenario["title"]}</h2><p style="color:#e0e0e0;margin:0;line-height:1.6">{scenario["situation"]}</p></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**난이도:** {'⭐' * scenario['difficulty']}")
    with col2:
        st.markdown(f"**승객:** {scenario['passenger_persona']}")

    st.divider()

    # 연습 설정 (잘 보이게)
    st.subheader("연습 설정")
    st.caption("연습 방식을 선택하세요")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 입력 방식")
        input_mode = st.radio(
            "응답 입력 방식 선택",
            ["타자 입력", "음성 입력"],
            label_visibility="collapsed",
            help="타자로 입력하거나 음성으로 말할 수 있습니다"
        )
        st.session_state.rp_voice_mode = (input_mode == "음성 입력") and UTILS_AVAILABLE

        if input_mode == "음성 입력" and not UTILS_AVAILABLE:
            st.warning("음성 기능이 현재 사용 불가합니다")

    with col2:
        st.markdown("##### 승객 음성")
        passenger_voice = st.checkbox(
            "승객 대사를 음성으로 듣기",
            value=st.session_state.get("rp_passenger_voice", False),
            help="AI 승객의 말을 음성으로 들을 수 있습니다"
        )
        if UTILS_AVAILABLE:
            st.session_state.rp_passenger_voice = passenger_voice

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 타이머")
        st.session_state.rp_timer_enabled = st.checkbox(
            "30초 응답 제한 타이머",
            value=st.session_state.rp_timer_enabled,
            help="각 응답마다 30초 제한이 있습니다"
        )

    with col2:
        st.markdown("##### 힌트")
        st.session_state.rp_show_hint = st.checkbox(
            "상황별 힌트 표시",
            value=st.session_state.rp_show_hint,
            help="응답에 도움이 되는 힌트를 보여줍니다"
        )

    st.divider()

    # 남은 사용량 표시

    # 시작 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("다른 시나리오", use_container_width=True):
            st.session_state.rp_scenario = None
            st.session_state.rp_ready = False
            st.rerun()

    with col2:
        if st.button("연습 시작", type="primary", use_container_width=True):
            # 사용량 체크

            # 초기화 및 첫 대사 생성
            st.session_state.rp_messages = []
            st.session_state.rp_turn = 0
            st.session_state.rp_ended = False
            st.session_state.rp_evaluation = None
            st.session_state.rp_escalation_level = 0
            st.session_state.rp_previous_level = 0
            st.session_state.rp_ideal_responses = []
            st.session_state.rp_response_times = []
            st.session_state.rp_timer_start = time.time()
            st.session_state.rp_timer_paused_at = None
            st.session_state.rp_audio_playing = False
            st.session_state.rp_audio_bytes_list = []  # 음성 데이터 초기화
            st.session_state.rp_voice_analysis = None  # 음성 분석 결과 초기화
            st.session_state.rp_processed_audio_id = None  # 오디오 중복 방지 초기화

            with st.spinner("승객이 다가옵니다..."):
                first_msg = generate_passenger_response(
                    scenario, [], "[상황 시작: 승객이 승무원에게 다가옵니다]", 0
                )
                st.session_state.rp_messages.append({
                    "role": "passenger",
                    "content": first_msg,
                    "level": 0
                })

            st.session_state.rp_ready = True
            increment_usage()
            st.rerun()

else:
    # 롤플레잉 진행 중
    scenario = st.session_state.rp_scenario

    # 상단 정보 바
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        st.subheader(f"🎬 {scenario['title']}")
    with col2:
        st.metric("턴", f"{st.session_state.rp_turn}/5")
    with col3:
        difficulty_stars = "⭐" * scenario["difficulty"]
        st.markdown(f"**난이도**  \n{difficulty_stars}")
    with col4:
        if st.button("나가기", type="secondary"):
            st.session_state.rp_scenario = None
            st.session_state.rp_ready = False
            st.session_state.rp_messages = []
            st.session_state.rp_turn = 0
            st.session_state.rp_ended = False
            st.session_state.rp_evaluation = None
            st.session_state.rp_escalation_level = 0
            st.session_state.rp_audio_bytes_list = []  # 음성 데이터 초기화
            st.session_state.rp_voice_analysis = None  # 음성 분석 결과 초기화
            st.session_state.rp_processed_audio_id = None  # 오디오 중복 방지 초기화
            st.rerun()

    # 감정 게이지
    render_emotion_gauge(
        st.session_state.rp_escalation_level,
        st.session_state.rp_previous_level
    )

    # 상황 설명
    st.markdown(f'<div style="background:linear-gradient(135deg,#1e3a5f,#2d5a87);padding:20px;border-radius:15px;margin:20px 0"><h4 style="color:#fff;margin:0 0 10px 0">📍 현재 상황</h4><p style="color:#e0e0e0;margin:0;line-height:1.6">{scenario["situation"]}</p></div>', unsafe_allow_html=True)

    # 역할 안내
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"**✈️ 당신 = 승무원**")
    with col2:
        st.warning(f"**👤 AI = {scenario['passenger_persona']}**")

    st.divider()

    # 대화 표시
    for msg_idx, msg in enumerate(st.session_state.rp_messages):
        if msg["role"] == "passenger":
            level = msg.get("level", 0)
            st.markdown(
                get_passenger_avatar_html(
                    msg["content"],
                    scenario["passenger_persona"],
                    level,
                    is_speaking=(msg_idx == len(st.session_state.rp_messages) - 1)
                ),
                unsafe_allow_html=True
            )

            # 음성 재생
            if st.session_state.get("rp_passenger_voice", False) and UTILS_AVAILABLE:
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    if not st.session_state.get("rp_audio_playing", False):
                        if st.button("🔊 듣기", key=f"listen_{msg_idx}"):
                            # 타이머 일시정지 설정
                            st.session_state.rp_audio_playing = True
                            if st.session_state.rp_timer_start:
                                st.session_state.rp_timer_paused_at = time.time()
                            st.rerun()
                    else:
                        # 오디오 재생 중 - 음성 생성 및 재생 (CLOVA TTS)
                        with st.spinner("🔊 음성 생성 중..."):
                            audio = generate_tts_for_passenger(
                                text=msg["content"],
                                persona=scenario["passenger_persona"],
                                escalation_level=level
                            )
                            if audio:
                                get_loud_audio_component(audio, autoplay=True, gain=5.0)
                        st.info("🔊 음성 재생 중 - 타이머 일시정지됨")

                with col_b:
                    if st.session_state.get("rp_audio_playing", False):
                        if st.button("▶️ 타이머 재개", key=f"resume_{msg_idx}", type="primary"):
                            # 타이머 재개 (일시정지한 시간만큼 시작 시간 조정)
                            if st.session_state.rp_timer_paused_at:
                                paused_duration = time.time() - st.session_state.rp_timer_paused_at
                                if st.session_state.rp_timer_start:
                                    st.session_state.rp_timer_start += paused_duration
                                st.session_state.rp_timer_paused_at = None
                            st.session_state.rp_audio_playing = False
                            st.rerun()
        else:
            st.markdown(get_crew_response_html(msg["content"]), unsafe_allow_html=True)

            # 응답 소요 시간 표시
            response_idx = msg_idx // 2
            if response_idx < len(st.session_state.rp_response_times):
                render_response_time(st.session_state.rp_response_times[response_idx])

            # 모범 답안 비교 (프리미엄)
            if is_premium_user() and msg_idx < len(st.session_state.rp_ideal_responses):
                ideal = st.session_state.rp_ideal_responses[msg_idx // 2] if msg_idx // 2 < len(st.session_state.rp_ideal_responses) else None
                if ideal:
                    with st.expander("📝 모범 답안 비교"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**내 응답:**")
                            st.info(msg["content"])
                        with col2:
                            st.markdown("**모범 답안:**")
                            st.success(ideal)

    # 입력 또는 평가
    if not st.session_state.rp_ended:
        st.markdown("---")

        # 타이머 + 힌트를 입력창 바로 위에 배치
        col1, col2 = st.columns([3, 1])

        with col1:
            # 힌트 표시 (입력창 바로 위)
            if st.session_state.rp_show_hint:
                hint = get_hint(scenario, st.session_state.rp_escalation_level, st.session_state.rp_turn)
                render_hint_box(hint, True)

        with col2:
            # 실시간 타이머 (오디오 재생 중이면 일시정지)
            if st.session_state.rp_timer_enabled and st.session_state.rp_timer_start:
                is_paused = st.session_state.get("rp_audio_playing", False)
                render_realtime_timer(30, st.session_state.rp_timer_start, is_paused)

        # 입력 (타자 또는 음성)
        user_input = None

        if st.session_state.get("rp_voice_mode", False) and UTILS_AVAILABLE:
            # 음성 입력 모드
            st.markdown("##### 🎤 음성으로 답변하세요")

            # 녹음 상태 관리
            if "rp_recording" not in st.session_state:
                st.session_state.rp_recording = False

            col_rec1, col_rec2 = st.columns([1, 1])

            with col_rec1:
                # 음성 녹음 시도 (st.audio_input 사용 - Streamlit 1.33+)
                try:
                    # 처리된 오디오 ID 추적 (중복 처리 방지)
                    if "rp_processed_audio_id" not in st.session_state:
                        st.session_state.rp_processed_audio_id = None

                    audio_data = st.audio_input("🎤 말하기 (녹음 버튼 클릭)", key="voice_input")
                    if audio_data:
                        # 오디오 ID로 중복 체크 (파일 크기 + 이름 조합)
                        audio_id = f"{audio_data.name}_{audio_data.size}"

                        # 이미 처리된 오디오면 건너뛰기
                        if audio_id != st.session_state.rp_processed_audio_id:
                            with st.spinner("🔊 음성 인식 중..."):
                                # 타이머 일시정지
                                if st.session_state.rp_timer_start and not st.session_state.rp_timer_paused_at:
                                    st.session_state.rp_timer_paused_at = time.time()

                                # 음성 데이터 읽기 (분석용으로 저장)
                                audio_bytes = audio_data.read()
                                result = transcribe_audio(audio_bytes, language="ko")
                                if result and result.get("text"):
                                    user_input = result["text"]
                                    st.success(f"✅ 인식됨: {user_input}")

                                    # 음성 데이터 저장 (나중에 분석용)
                                    st.session_state.rp_audio_bytes_list.append(audio_bytes)

                                    # 처리 완료 표시
                                    st.session_state.rp_processed_audio_id = audio_id

                                    # 타이머 재개
                                    if st.session_state.rp_timer_paused_at:
                                        paused = time.time() - st.session_state.rp_timer_paused_at
                                        if st.session_state.rp_timer_start:
                                            st.session_state.rp_timer_start += paused
                                        st.session_state.rp_timer_paused_at = None
                                else:
                                    st.error("음성 인식 실패 - 다시 시도하거나 아래 텍스트로 입력하세요")
                                    st.session_state.rp_processed_audio_id = audio_id  # 실패해도 중복 처리 방지
                except Exception as e:
                    st.warning("음성 입력 기능을 사용할 수 없습니다. 텍스트로 입력해주세요.")

            with col_rec2:
                st.caption("💡 음성 인식 팁:")
                st.caption("• 조용한 환경에서 녹음")
                st.caption("• 마이크 가까이 말하기")
                st.caption("• 천천히 또박또박 발음")

            # 텍스트 폴백
            with st.expander("📝 텍스트로 입력 (음성 인식 실패 시)"):
                text_fallback = st.text_input("직접 입력:", key="text_fallback")
                if st.button("텍스트 전송", key="send_text"):
                    if text_fallback:
                        user_input = text_fallback
        else:
            # 타자 입력 모드
            user_input = st.chat_input("승무원으로서 응대하세요...")

        if user_input:
            # 응답 시간 계산 및 저장
            if st.session_state.rp_timer_start:
                response_time = int(time.time() - st.session_state.rp_timer_start)
                st.session_state.rp_response_times.append(response_time)

            # 이전 레벨 저장
            st.session_state.rp_previous_level = st.session_state.rp_escalation_level

            # 승무원 메시지 추가
            st.session_state.rp_messages.append({
                "role": "crew",
                "content": user_input
            })
            st.session_state.rp_turn += 1

            # 모범 답안 생성 (프리미엄)
            if is_premium_user():
                ideal = generate_ideal_response(
                    scenario,
                    st.session_state.rp_messages[:-1],
                    user_input
                )
                if ideal:
                    st.session_state.rp_ideal_responses.append(ideal)

            # 에스컬레이션 체크
            new_level = check_escalation(
                scenario,
                user_input,
                st.session_state.rp_escalation_level
            )
            st.session_state.rp_escalation_level = new_level

            # 타이머 리셋
            st.session_state.rp_timer_start = time.time()

            # 5턴 이상이면 종료
            if st.session_state.rp_turn >= 5:
                st.session_state.rp_ended = True
            else:
                # 승객 응답 생성
                with st.spinner("승객 반응 중..."):
                    passenger_response = generate_passenger_response(
                        scenario,
                        st.session_state.rp_messages,
                        user_input,
                        st.session_state.rp_escalation_level
                    )

                st.session_state.rp_messages.append({
                    "role": "passenger",
                    "content": passenger_response,
                    "level": st.session_state.rp_escalation_level
                })

            st.rerun()

        # 조기 종료 버튼
        if st.session_state.rp_turn >= 3:
            if st.button("대화 종료 및 평가받기", type="primary", use_container_width=True):
                st.session_state.rp_ended = True
                st.rerun()

    else:
        # 평가 단계
        st.divider()
        st.subheader("대응 평가")

        if st.session_state.rp_evaluation is None:
            with st.spinner("대응을 평가하고 있습니다..."):
                evaluation = evaluate_conversation(scenario, st.session_state.rp_messages)
                st.session_state.rp_evaluation = evaluation

                # 음성 분석 수행 (음성 데이터가 있는 경우)
                if st.session_state.rp_audio_bytes_list and UTILS_AVAILABLE:
                    try:
                        # 모든 음성 데이터 합쳐서 분석
                        combined_audio = b''.join(st.session_state.rp_audio_bytes_list)
                        voice_result = analyze_voice_complete(
                            combined_audio,
                            response_times=st.session_state.rp_response_times
                        )
                        st.session_state.rp_voice_analysis = voice_result
                    except Exception as e:
                        st.session_state.rp_voice_analysis = {"error": str(e)}

                # 점수 파싱 및 저장
                if "result" in evaluation:
                    # 점수 추출 시도
                    import re
                    score_match = re.search(r'(\d+)점', evaluation["result"])
                    score = int(score_match.group(1)) if score_match else 0

                    # 진행률 저장
                    mark_completed(
                        scenario["id"],
                        score,
                        st.session_state.rp_messages
                    )

                    # 성장그래프 저장
                    if SCORE_UTILS_AVAILABLE:
                        parsed = parse_evaluation_score(evaluation["result"], "롤플레잉")
                        if parsed.get("total", 0) > 0:
                            save_practice_score(
                                practice_type="롤플레잉",
                                total_score=parsed["total"],
                                detailed_scores=parsed.get("detailed"),
                                scenario=scenario.get("title", "")
                            )

            st.rerun()
        else:
            eval_result = st.session_state.rp_evaluation

            if "error" in eval_result:
                st.error(f"평가 오류: {eval_result['error']}")
            else:
                st.markdown(eval_result.get("result", ""))

                # 감정 변화 요약
                levels = [m.get("level", 0) for m in st.session_state.rp_messages if m["role"] == "passenger"]
                if levels:
                    start_level = levels[0]
                    end_level = levels[-1]

                    if end_level < start_level:
                        st.success("승객의 감정을 진정시키는 데 성공했습니다!")
                    elif end_level > start_level:
                        st.warning("승객의 감정이 더 악화되었습니다. 공감과 해결책 제시를 연습해보세요.")
                    else:
                        st.info("승객의 감정이 유지되었습니다.")

                if SCORE_UTILS_AVAILABLE:
                    st.success("점수가 성장그래프에 자동 저장되었습니다.")

                # 음성 분석 결과 표시
                voice_analysis = st.session_state.get("rp_voice_analysis")
                if voice_analysis and "error" not in voice_analysis:
                    st.divider()
                    st.subheader("음성 전달력 분석")

                    # 종합 점수
                    total_score = voice_analysis.get("total_score", 0)
                    grade = voice_analysis.get("grade", "N/A")

                    col_score1, col_score2 = st.columns([1, 2])
                    with col_score1:
                        grade_colors = {"S": "#FFD700", "A": "#4CAF50", "B": "#2196F3", "C": "#FF9800", "D": "#f44336"}
                        grade_color = grade_colors.get(grade, "#666")
                        st.markdown(f"""
                        <div style='text-align:center; padding:20px; background:linear-gradient(135deg, {grade_color}22, {grade_color}11); border-radius:15px; border:2px solid {grade_color};'>
                            <div style='font-size:48px; font-weight:bold; color:{grade_color};'>{grade}</div>
                            <div style='font-size:24px; color:#333;'>{total_score}점</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_score2:
                        st.markdown(f"**{voice_analysis.get('summary', '')}**")

                        # 개선 포인트
                        improvements = voice_analysis.get("top_improvements", [])
                        if improvements:
                            st.markdown("**🔧 우선 개선 포인트:**")
                            for imp in improvements:
                                st.markdown(f"- {imp}")

                    # 상세 분석
                    with st.expander("📋 상세 음성 분석 보기", expanded=True):
                        voice_detail = voice_analysis.get("voice_analysis", {})
                        text_detail = voice_analysis.get("text_analysis", {})

                        col_v1, col_v2 = st.columns(2)

                        with col_v1:
                            st.markdown("**🗣️ 음성 품질**")

                            # 목소리 떨림
                            tremor = voice_detail.get("tremor", {})
                            tremor_score = tremor.get("score", 0)
                            st.markdown(f"**목소리 안정성**: {tremor.get('level', 'N/A')} ({tremor_score}/10)")
                            st.progress(tremor_score / 10)
                            st.caption(tremor.get("feedback", ""))

                            # 말끝 흐림
                            ending = voice_detail.get("ending_clarity", {})
                            ending_score = ending.get("score", 0)
                            st.markdown(f"**말끝 명확성**: {ending.get('issue', 'N/A')} ({ending_score}/10)")
                            st.progress(ending_score / 10)
                            st.caption(ending.get("feedback", ""))

                            # 피치 변화
                            pitch = voice_detail.get("pitch_variation", {})
                            pitch_score = pitch.get("score", 0)
                            st.markdown(f"**억양 변화**: {pitch.get('type', 'N/A')} ({pitch_score}/10)")
                            st.progress(pitch_score / 10)
                            st.caption(pitch.get("feedback", ""))

                            # 에너지 일관성
                            energy = voice_detail.get("energy_consistency", {})
                            energy_score = energy.get("score", 0)
                            st.markdown(f"**에너지 일관성**: ({energy_score}/10)")
                            st.progress(energy_score / 10)
                            st.caption(energy.get("feedback", ""))

                            # 서비스 톤
                            service = voice_detail.get("service_tone", {})
                            service_score = service.get("score", 0)
                            greeting = "✓" if service.get("greeting_bright") else "✗"
                            ending_s = "✓" if service.get("ending_soft") else "✗"
                            st.markdown(f"**서비스 톤**: 인사{greeting} 마무리{ending_s} ({service_score}/10)")
                            st.progress(service_score / 10)
                            st.caption(service.get("feedback", ""))

                            # 침착함
                            composure = voice_detail.get("composure", {})
                            composure_score = composure.get("score", 0)
                            st.markdown(f"**침착함**: ({composure_score}/10)")
                            st.progress(composure_score / 10)
                            st.caption(composure.get("feedback", ""))

                        with col_v2:
                            st.markdown("**📝 말하기 습관**")

                            # 말 속도
                            rate = text_detail.get("speech_rate", {})
                            rate_score = rate.get("score", 0)
                            wpm = rate.get("wpm", 0)
                            st.markdown(f"**말 속도**: {wpm} WPM ({rate_score}/10)")
                            st.progress(rate_score / 10)
                            st.caption(rate.get("feedback", ""))

                            # 필러 단어
                            filler = text_detail.get("filler_words", {})
                            filler_score = filler.get("score", 0)
                            filler_count = filler.get("count", 0)
                            st.markdown(f"**추임새(음, 어)**: {filler_count}회 ({filler_score}/10)")
                            st.progress(filler_score / 10)
                            st.caption(filler.get("feedback", ""))

                            # 휴지
                            pauses = text_detail.get("pauses", {})
                            pause_score = pauses.get("score", 0)
                            st.markdown(f"**휴지/끊김**: ({pause_score}/10)")
                            st.progress(pause_score / 10)
                            st.caption(pauses.get("feedback", ""))

                            # 발음 명확성
                            clarity = text_detail.get("clarity", {})
                            clarity_score = clarity.get("score", 0)
                            st.markdown(f"**발음 명확성**: ({clarity_score}/10)")
                            st.progress(clarity_score / 10)
                            st.caption(clarity.get("feedback", ""))

                            # 응답 시간
                            rt_detail = voice_analysis.get("response_time_analysis", {})
                            rt_score = rt_detail.get("score", 0)
                            avg_time = rt_detail.get("avg_time", 0)
                            st.markdown(f"**응답 시간**: 평균 {avg_time}초 ({rt_score}/10)")
                            st.progress(rt_score / 10)
                            st.caption(rt_detail.get("feedback", ""))

                elif voice_analysis and "error" in voice_analysis:
                    st.warning(f"음성 분석 오류: {voice_analysis.get('error')}")
                elif not st.session_state.rp_audio_bytes_list:
                    st.info("음성 모드로 응답하면 목소리 떨림, 말끝 흐림 등 상세 분석을 받을 수 있습니다.")

                # 맞춤 추천 시나리오
                if REPORT_AVAILABLE and voice_analysis:
                    recommendations = get_weakness_recommendations(
                        voice_analysis,
                        eval_result.get("result", ""),
                        max_recommendations=3
                    )

                    if recommendations:
                        st.divider()
                        st.subheader("약점 기반 맞춤 추천")
                        st.caption("분석 결과를 바탕으로 개선이 필요한 부분을 연습할 수 있는 시나리오를 추천합니다.")

                        for rec in recommendations:
                            with st.container():
                                col_r1, col_r2 = st.columns([3, 1])
                                with col_r1:
                                    st.markdown(f"**[{rec['weakness']}]** {rec['scenario_title']}")
                                    st.caption(f"{rec['category']} | {'⭐' * rec['difficulty']} | 💡 {rec['tip']}")
                                with col_r2:
                                    if st.button("연습하기", key=f"rec_{rec['scenario_id']}", use_container_width=True):
                                        # 추천 시나리오로 이동
                                        from roleplay_scenarios import get_scenario_by_id
                                        new_scenario = get_scenario_by_id(rec['scenario_id'])
                                        if new_scenario:
                                            st.session_state.rp_scenario = new_scenario
                                            st.session_state.rp_ready = True
                                            st.session_state.rp_messages = []
                                            st.session_state.rp_turn = 0
                                            st.session_state.rp_ended = False
                                            st.session_state.rp_evaluation = None
                                            st.session_state.rp_audio_bytes_list = []
                                            st.session_state.rp_voice_analysis = None
                                            st.session_state.rp_processed_audio_id = None
                                            st.rerun()

                # PDF 리포트 다운로드
                if REPORT_AVAILABLE:
                    st.divider()
                    st.subheader("리포트 다운로드")

                    col_pdf1, col_pdf2 = st.columns([2, 1])
                    with col_pdf1:
                        st.caption("분석 결과를 PDF로 저장하여 나중에 확인하거나 공유할 수 있습니다.")
                    with col_pdf2:
                        try:
                            pdf_bytes = generate_roleplay_report(
                                scenario=scenario,
                                messages=st.session_state.rp_messages,
                                text_evaluation=eval_result.get("result", ""),
                                voice_analysis=voice_analysis,
                                user_name="사용자"
                            )
                            filename = get_report_filename(scenario.get("title", ""))

                            st.download_button(
                                label="PDF 리포트 다운로드",
                                data=pdf_bytes,
                                file_name=filename,
                                mime="application/pdf",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"PDF 생성 오류: {e}")

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("같은 시나리오 다시하기", use_container_width=True):
                sc = st.session_state.rp_scenario
                st.session_state.rp_messages = []
                st.session_state.rp_turn = 0
                st.session_state.rp_ended = False
                st.session_state.rp_evaluation = None
                st.session_state.rp_escalation_level = 0
                st.session_state.rp_previous_level = 0
                st.session_state.rp_ideal_responses = []
                st.session_state.rp_response_times = []
                st.session_state.rp_timer_start = time.time()
                st.session_state.rp_timer_paused_at = None
                st.session_state.rp_audio_playing = False
                st.session_state.rp_audio_bytes_list = []  # 음성 데이터 초기화
                st.session_state.rp_voice_analysis = None  # 음성 분석 결과 초기화
                st.session_state.rp_processed_audio_id = None  # 오디오 중복 방지 초기화

                first_msg = generate_passenger_response(
                    sc, [], "[상황 시작: 승객이 승무원에게 다가옵니다]", 0
                )
                st.session_state.rp_messages.append({
                    "role": "passenger",
                    "content": first_msg,
                    "level": 0
                })
                increment_usage()
                st.rerun()

        with col2:
            if st.button("다른 시나리오 선택", type="primary", use_container_width=True):
                st.session_state.rp_scenario = None
                st.session_state.rp_ready = False
                st.session_state.rp_messages = []
                st.session_state.rp_turn = 0
                st.session_state.rp_ended = False
                st.session_state.rp_evaluation = None
                st.session_state.rp_escalation_level = 0
                st.session_state.rp_previous_level = 0
                st.session_state.rp_ideal_responses = []
                st.session_state.rp_response_times = []
                st.session_state.rp_audio_playing = False
                st.session_state.rp_audio_bytes_list = []  # 음성 데이터 초기화
                st.session_state.rp_voice_analysis = None  # 음성 분석 결과 초기화
                st.session_state.rp_processed_audio_id = None  # 오디오 중복 방지 초기화
                st.rerun()

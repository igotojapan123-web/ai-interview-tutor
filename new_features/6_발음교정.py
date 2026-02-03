# new_features/6_발음교정.py
# FlyReady Lab - 발음/억양 교정 (영어)
# 원어민 발음과 비교하여 교정

import os
import sys
import random
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sidebar_common import init_page, end_page
from logging_config import get_logger

logger = get_logger(__name__)

# 음성 유틸리티
try:
    from voice_utils import transcribe_audio, generate_tts_audio
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# OpenAI API
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False


# =====================
# 발음 연습 데이터
# =====================

PRONUNCIATION_SETS = {
    "greetings": {
        "name": "인사 & 환영",
        "icon": "👋",
        "sentences": [
            {
                "text": "Welcome aboard. My name is ____, and I'll be your flight attendant today.",
                "korean": "탑승을 환영합니다. 저는 ____이고, 오늘 귀하를 담당할 승무원입니다.",
                "key_sounds": ["Welcome", "aboard", "flight attendant"],
                "difficulty": "easy",
            },
            {
                "text": "Good morning, ladies and gentlemen. Please take your seats.",
                "korean": "안녕하세요, 승객 여러분. 좌석에 착석해 주세요.",
                "key_sounds": ["Good morning", "ladies", "gentlemen"],
                "difficulty": "easy",
            },
            {
                "text": "Thank you for choosing our airline. We hope you have a pleasant flight.",
                "korean": "저희 항공사를 선택해 주셔서 감사합니다. 즐거운 비행이 되시길 바랍니다.",
                "key_sounds": ["choosing", "airline", "pleasant"],
                "difficulty": "medium",
            },
        ]
    },
    "safety": {
        "name": "안전 안내",
        "icon": "🦺",
        "sentences": [
            {
                "text": "Please fasten your seatbelt and remain seated.",
                "korean": "안전벨트를 착용하시고 착석해 주세요.",
                "key_sounds": ["fasten", "seatbelt", "remain"],
                "difficulty": "easy",
            },
            {
                "text": "In case of an emergency, please follow the instructions of the crew.",
                "korean": "비상시에는 승무원의 지시를 따라주세요.",
                "key_sounds": ["emergency", "instructions", "crew"],
                "difficulty": "medium",
            },
            {
                "text": "The emergency exits are located at the front, middle, and rear of the aircraft.",
                "korean": "비상구는 항공기 앞쪽, 중간, 뒤쪽에 위치해 있습니다.",
                "key_sounds": ["emergency exits", "located", "aircraft"],
                "difficulty": "hard",
            },
        ]
    },
    "service": {
        "name": "기내 서비스",
        "icon": "☕",
        "sentences": [
            {
                "text": "Would you like something to drink?",
                "korean": "음료를 드시겠습니까?",
                "key_sounds": ["Would", "something", "drink"],
                "difficulty": "easy",
            },
            {
                "text": "We have coffee, tea, orange juice, and water available.",
                "korean": "커피, 차, 오렌지 주스, 물이 있습니다.",
                "key_sounds": ["coffee", "orange juice", "available"],
                "difficulty": "easy",
            },
            {
                "text": "I'll be right back with your beverage.",
                "korean": "음료를 바로 가져다 드리겠습니다.",
                "key_sounds": ["right back", "beverage"],
                "difficulty": "medium",
            },
            {
                "text": "Is there anything else I can help you with?",
                "korean": "다른 도움이 필요하신 것이 있으신가요?",
                "key_sounds": ["anything else", "help"],
                "difficulty": "medium",
            },
        ]
    },
    "interview": {
        "name": "면접 답변",
        "icon": "🎤",
        "sentences": [
            {
                "text": "I have always dreamed of becoming a flight attendant.",
                "korean": "저는 항상 승무원이 되는 것을 꿈꿔왔습니다.",
                "key_sounds": ["always", "dreamed", "flight attendant"],
                "difficulty": "easy",
            },
            {
                "text": "I believe my communication skills and passion for service make me a great fit.",
                "korean": "저의 의사소통 능력과 서비스에 대한 열정이 적합하다고 생각합니다.",
                "key_sounds": ["communication", "passion", "service"],
                "difficulty": "hard",
            },
            {
                "text": "I am a team player who enjoys working with diverse groups of people.",
                "korean": "저는 다양한 사람들과 일하는 것을 즐기는 팀 플레이어입니다.",
                "key_sounds": ["team player", "diverse", "groups"],
                "difficulty": "medium",
            },
        ]
    },
    "difficult": {
        "name": "발음 어려운 단어",
        "icon": "🔤",
        "sentences": [
            {
                "text": "The turbulence should subside shortly.",
                "korean": "난기류가 곧 잦아들 것입니다.",
                "key_sounds": ["turbulence", "subside", "shortly"],
                "difficulty": "hard",
            },
            {
                "text": "We apologize for the inconvenience.",
                "korean": "불편을 드려 죄송합니다.",
                "key_sounds": ["apologize", "inconvenience"],
                "difficulty": "hard",
            },
            {
                "text": "Your cooperation is greatly appreciated.",
                "korean": "협조에 감사드립니다.",
                "key_sounds": ["cooperation", "greatly", "appreciated"],
                "difficulty": "hard",
            },
        ]
    },
}

# 발음 팁
PRONUNCIATION_TIPS = {
    "th": "혀를 윗니와 아랫니 사이에 살짝 내밀어 발음하세요 (think, this)",
    "r": "혀를 말지 않고 뒤로 약간 당기면서 발음하세요",
    "l": "혀끝을 윗니 뒤 잇몸에 대고 발음하세요",
    "v": "윗니로 아랫입술을 가볍게 물고 발음하세요",
    "f": "v와 비슷하지만 성대 진동 없이 바람만 내세요",
    "w": "입술을 둥글게 모아서 'ㅜ'처럼 시작하세요",
    "short_vowels": "영어 단모음은 한국어보다 짧게 발음하세요",
    "stress": "강세가 있는 음절을 더 길고 높게 발음하세요",
}


def analyze_pronunciation(original: str, user_text: str) -> dict:
    """발음 분석 (AI 사용)"""
    if not API_AVAILABLE:
        # 간단한 문자열 비교
        original_words = original.lower().split()
        user_words = user_text.lower().split()

        correct = sum(1 for o, u in zip(original_words, user_words) if o == u)
        accuracy = int((correct / len(original_words)) * 100) if original_words else 0

        return {
            "accuracy": accuracy,
            "feedback": "AI 없이 기본 분석을 제공합니다.",
            "issues": [],
            "tips": [],
        }

    system_prompt = """당신은 영어 발음 교정 전문가입니다.
사용자가 말한 영어와 원문을 비교하여 발음을 평가해주세요.

JSON 형식으로 응답:
{
    "accuracy": 0-100 (정확도 점수),
    "issues": [
        {"word": "문제 단어", "user_said": "사용자 발음", "correct": "올바른 발음", "tip": "교정 팁"}
    ],
    "feedback": "전반적인 피드백 1-2문장",
    "tips": ["개선 팁1", "개선 팁2"]
}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"원문: {original}\n사용자 발음: {user_text}"}
            ],
            temperature=0.3,
            max_tokens=500
        )

        import json
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"발음 분석 실패: {e}")
        return {
            "accuracy": 70,
            "feedback": "분석 중 오류가 발생했습니다.",
            "issues": [],
            "tips": [],
        }


def get_audio_recorder_component():
    """음성 녹음 컴포넌트"""
    return """
    <div id="recorder-container" style="text-align:center;padding:20px;">
        <button id="record-btn" onclick="toggleRecording()" style="
            padding: 16px 32px;
            font-size: 1.1rem;
            font-weight: 700;
            border: none;
            border-radius: 12px;
            background: #3b82f6;
            color: white;
            cursor: pointer;
            transition: all 0.2s;
        ">🎤 녹음 시작</button>

        <div id="status" style="margin-top:12px;color:#64748b;"></div>

        <audio id="audio-playback" controls style="display:none;margin-top:16px;width:100%;"></audio>
    </div>

    <script>
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

    async function toggleRecording() {
        const btn = document.getElementById('record-btn');
        const status = document.getElementById('status');
        const audio = document.getElementById('audio-playback');

        if (!isRecording) {
            // 녹음 시작
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = (e) => {
                    audioChunks.push(e.data);
                };

                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    audio.src = audioUrl;
                    audio.style.display = 'block';
                };

                mediaRecorder.start();
                isRecording = true;
                btn.textContent = '⏹ 녹음 중지';
                btn.style.background = '#ef4444';
                status.textContent = '녹음 중...';
            } catch (err) {
                status.textContent = '마이크 접근 권한이 필요합니다.';
            }
        } else {
            // 녹음 중지
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
            isRecording = false;
            btn.textContent = '🎤 다시 녹음';
            btn.style.background = '#3b82f6';
            status.textContent = '녹음 완료! 재생해서 확인하세요.';
        }
    }
    </script>
    """


# =====================
# UI
# =====================

def render_pronunciation():
    """발음 교정 UI"""

    st.markdown("""
    <style>
    .pron-header {
        background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    .sentence-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .english-text {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e3a5f;
        margin-bottom: 12px;
        line-height: 1.6;
    }
    .korean-text {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 16px;
    }
    .key-sound {
        display: inline-block;
        background: #eff6ff;
        color: #3b82f6;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 4px;
    }
    .difficulty-badge {
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .difficulty-easy { background: #dcfce7; color: #16a34a; }
    .difficulty-medium { background: #fef3c7; color: #d97706; }
    .difficulty-hard { background: #fee2e2; color: #dc2626; }
    .tip-card {
        background: #f0fdf4;
        border-left: 4px solid #10b981;
        padding: 16px;
        border-radius: 0 8px 8px 0;
        margin: 12px 0;
    }
    .accuracy-score {
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
    }
    .accuracy-high { color: #10b981; }
    .accuracy-medium { color: #f59e0b; }
    .accuracy-low { color: #ef4444; }
    </style>
    """, unsafe_allow_html=True)

    # 헤더
    st.markdown("""
    <div class="pron-header">
        <h2 style="margin:0 0 8px 0;">🗣 영어 발음 교정</h2>
        <p style="margin:0;opacity:0.9;">원어민 발음을 듣고 따라하며 교정하세요</p>
    </div>
    """, unsafe_allow_html=True)

    # 세션 상태
    if "pron_current" not in st.session_state:
        st.session_state.pron_current = None
    if "pron_result" not in st.session_state:
        st.session_state.pron_result = None

    # 카테고리 선택
    st.markdown("### 연습할 카테고리 선택")

    cols = st.columns(5)
    for i, (cat_key, cat_data) in enumerate(PRONUNCIATION_SETS.items()):
        with cols[i % 5]:
            if st.button(
                f"{cat_data['icon']}\n{cat_data['name']}",
                key=f"cat_{cat_key}",
                use_container_width=True
            ):
                st.session_state.pron_category = cat_key
                st.session_state.pron_current = random.choice(cat_data["sentences"])
                st.session_state.pron_result = None
                st.rerun()

    st.markdown("---")

    # 현재 문장 연습
    if st.session_state.pron_current:
        sentence = st.session_state.pron_current

        # 난이도 표시
        diff_class = f"difficulty-{sentence['difficulty']}"
        diff_text = {"easy": "쉬움", "medium": "보통", "hard": "어려움"}[sentence['difficulty']]

        st.markdown(f"""
        <div class="sentence-card">
            <span class="difficulty-badge {diff_class}">{diff_text}</span>
            <div class="english-text">{sentence['text']}</div>
            <div class="korean-text">{sentence['korean']}</div>
            <div>
                <strong>핵심 발음:</strong>
                {''.join([f'<span class="key-sound">{s}</span>' for s in sentence['key_sounds']])}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 원어민 발음 듣기 (TTS)
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔊 원어민 발음 듣기", use_container_width=True):
                if VOICE_AVAILABLE:
                    audio_data = generate_tts_audio(sentence['text'], voice="alloy")
                    if audio_data:
                        st.audio(audio_data, format="audio/mp3")
                else:
                    st.warning("TTS 기능을 사용할 수 없습니다.")

        with col2:
            speed = st.select_slider(
                "속도",
                options=["느리게", "보통", "빠르게"],
                value="보통"
            )

        st.markdown("---")

        # 내 발음 녹음
        st.markdown("### 내 발음 녹음하기")

        # 녹음 컴포넌트
        components.html(get_audio_recorder_component(), height=180)

        # 또는 텍스트로 입력 (STT 대안)
        st.markdown("**또는 발음한 내용을 텍스트로 입력하세요:**")

        user_text = st.text_input(
            "내가 발음한 내용",
            placeholder="위 문장을 발음하고 들린 대로 입력하세요...",
            key="pron_user_input"
        )

        if st.button("발음 분석하기", type="primary", use_container_width=True):
            if user_text.strip():
                with st.spinner("발음 분석 중..."):
                    result = analyze_pronunciation(sentence['text'], user_text)
                    st.session_state.pron_result = result
                st.rerun()
            else:
                st.warning("발음한 내용을 입력해주세요.")

        # 분석 결과
        if st.session_state.pron_result:
            result = st.session_state.pron_result

            # 정확도 점수
            accuracy = result.get("accuracy", 0)
            if accuracy >= 80:
                acc_class = "accuracy-high"
            elif accuracy >= 60:
                acc_class = "accuracy-medium"
            else:
                acc_class = "accuracy-low"

            st.markdown(f"""
            <div class="accuracy-score {acc_class}">{accuracy}%</div>
            <div style="text-align:center;color:#64748b;">발음 정확도</div>
            """, unsafe_allow_html=True)

            # 피드백
            st.markdown("### 피드백")
            st.info(result.get("feedback", ""))

            # 문제점
            issues = result.get("issues", [])
            if issues:
                st.markdown("### 교정이 필요한 부분")
                for issue in issues:
                    st.markdown(f"""
                    <div class="tip-card">
                        <strong>"{issue.get('word', '')}"</strong><br>
                        내 발음: {issue.get('user_said', '')} → 올바른 발음: {issue.get('correct', '')}<br>
                        💡 {issue.get('tip', '')}
                    </div>
                    """, unsafe_allow_html=True)

            # 개선 팁
            tips = result.get("tips", [])
            if tips:
                st.markdown("### 개선 팁")
                for tip in tips:
                    st.markdown(f"- {tip}")

        # 다음 문장
        if st.button("다음 문장 연습", use_container_width=True):
            cat_key = st.session_state.get("pron_category", "greetings")
            sentences = PRONUNCIATION_SETS[cat_key]["sentences"]
            st.session_state.pron_current = random.choice(sentences)
            st.session_state.pron_result = None
            st.rerun()

    else:
        st.info("위에서 카테고리를 선택하면 연습을 시작합니다.")

    # 발음 팁 섹션
    st.markdown("---")
    with st.expander("📚 영어 발음 기본 팁"):
        for sound, tip in PRONUNCIATION_TIPS.items():
            st.markdown(f"**{sound}**: {tip}")


# 메인 실행
if __name__ == "__main__":
    render_pronunciation()

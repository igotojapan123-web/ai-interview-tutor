# new_features/8_긴장관리모드.py
# FlyReady Lab - 긴장 관리 모드
# 면접 전 호흡, 명상, 마음 준비

import os
import sys
import time
import random
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sidebar_common import init_page, end_page
from logging_config import get_logger

logger = get_logger(__name__)


# =====================
# 긴장 관리 콘텐츠
# =====================

BREATHING_EXERCISES = {
    "4-7-8": {
        "name": "4-7-8 호흡법",
        "description": "가장 효과적인 긴장 완화 호흡법",
        "duration": "2분",
        "steps": [
            {"action": "들숨", "duration": 4, "instruction": "코로 천천히 숨을 들이쉬세요"},
            {"action": "참기", "duration": 7, "instruction": "숨을 참으세요"},
            {"action": "날숨", "duration": 8, "instruction": "입으로 천천히 내쉬세요"},
        ],
        "cycles": 4,
    },
    "box": {
        "name": "박스 호흡법",
        "description": "균형 잡힌 호흡으로 마음 안정",
        "duration": "3분",
        "steps": [
            {"action": "들숨", "duration": 4, "instruction": "숨을 들이쉬세요"},
            {"action": "참기", "duration": 4, "instruction": "숨을 참으세요"},
            {"action": "날숨", "duration": 4, "instruction": "숨을 내쉬세요"},
            {"action": "비우기", "duration": 4, "instruction": "잠시 비워두세요"},
        ],
        "cycles": 4,
    },
    "calming": {
        "name": "진정 호흡",
        "description": "빠른 긴장 완화",
        "duration": "1분",
        "steps": [
            {"action": "들숨", "duration": 3, "instruction": "깊게 들이쉬세요"},
            {"action": "날숨", "duration": 6, "instruction": "천천히 내쉬세요"},
        ],
        "cycles": 5,
    },
}

AFFIRMATIONS = [
    "나는 충분히 준비되어 있다.",
    "나는 이 자리에 있을 자격이 있다.",
    "긴장은 나를 더 집중하게 해준다.",
    "나는 내 이야기를 진심으로 전할 수 있다.",
    "면접관도 나의 성공을 원한다.",
    "실수해도 괜찮다. 완벽할 필요 없다.",
    "나는 미소 지을 수 있다.",
    "나의 경험과 열정은 가치 있다.",
    "심호흡 한 번이면 충분하다.",
    "나는 할 수 있다.",
]

VISUALIZATION_SCRIPTS = {
    "success": {
        "name": "성공 시각화",
        "duration": "3분",
        "script": """
눈을 감고 편안한 자세를 취하세요.

지금 당신은 면접장 앞에 서 있습니다.
문이 열리고, 면접관들이 따뜻하게 맞이합니다.

당신은 자신감 있게 인사하고 자리에 앉습니다.
면접관이 첫 질문을 합니다.

당신의 목소리는 차분하고 또렷합니다.
준비한 내용이 자연스럽게 흘러나옵니다.

면접관들이 고개를 끄덕이며 경청합니다.
당신의 진심이 전해지고 있습니다.

마지막 질문이 끝나고,
면접관이 미소 지으며 말합니다.
"좋은 이야기 감사합니다."

당신은 당당하게 일어나 인사합니다.
"감사합니다. 좋은 하루 되세요."

문을 나서며 생각합니다.
"나는 최선을 다했다. 잘 했어."
""",
    },
    "calm": {
        "name": "평화로운 장소",
        "duration": "5분",
        "script": """
눈을 감고 깊게 숨을 쉬세요.

당신이 가장 평화롭다고 느끼는 장소를 떠올려보세요.
따뜻한 햇살이 내리쬐는 해변일 수도 있고,
조용한 숲 속 오솔길일 수도 있습니다.

그곳의 소리를 들어보세요.
파도 소리, 새소리, 바람 소리...

그곳의 냄새를 맡아보세요.
상쾌한 공기, 꽃향기, 바다 내음...

그곳에서 당신은 완전히 안전합니다.
모든 걱정이 사라집니다.

이 평화로움을 가슴에 담아두세요.
면접장에서도 이 느낌을 불러올 수 있습니다.

천천히 현실로 돌아옵니다.
하지만 평화로움은 남아있습니다.
""",
    },
}

QUICK_TIPS = [
    {"tip": "면접 30분 전 도착", "reason": "여유있게 마음을 정리할 시간 확보"},
    {"tip": "대기실에서 심호흡 3번", "reason": "심박수를 낮추고 집중력 향상"},
    {"tip": "어깨를 펴고 미소 짓기", "reason": "자세가 자신감에 영향을 줌"},
    {"tip": "면접관 눈 사이를 보기", "reason": "눈 맞춤 부담 없이 시선 처리"},
    {"tip": "천천히 말하기", "reason": "긴장하면 빨라지므로 의식적으로 천천히"},
    {"tip": "질문 후 2초 쉬기", "reason": "생각할 시간 확보, 차분해 보임"},
    {"tip": "손은 무릎 위에", "reason": "안정감 있고 단정해 보임"},
    {"tip": "모르면 솔직하게", "reason": "억지 답변보다 정직함이 좋은 인상"},
]

ANXIETY_LEVELS = {
    1: {"level": "매우 낮음", "color": "#10b981", "advice": "좋은 컨디션이에요! 그대로 면접에 임하세요."},
    2: {"level": "낮음", "color": "#22c55e", "advice": "적당한 긴장감이에요. 집중력이 좋을 거예요."},
    3: {"level": "보통", "color": "#84cc16", "advice": "정상적인 긴장이에요. 심호흡으로 관리하세요."},
    4: {"level": "약간 높음", "color": "#eab308", "advice": "호흡 운동을 추천해요. 2-3분이면 충분해요."},
    5: {"level": "높음", "color": "#f59e0b", "advice": "잠시 눈을 감고 4-7-8 호흡을 해보세요."},
    6: {"level": "꽤 높음", "color": "#f97316", "advice": "가벼운 스트레칭과 호흡 운동을 함께 하세요."},
    7: {"level": "매우 높음", "color": "#ef4444", "advice": "시각화 명상과 호흡 운동을 병행하세요."},
}


def get_breathing_animation(exercise_key: str):
    """호흡 운동 애니메이션 컴포넌트"""
    exercise = BREATHING_EXERCISES[exercise_key]
    steps = exercise["steps"]
    cycles = exercise["cycles"]

    # 스텝 데이터를 JSON으로
    steps_json = str(steps).replace("'", '"')

    return f"""
    <div id="breathing-container" style="text-align:center;padding:40px;">
        <div id="breath-circle" style="
            width: 200px;
            height: 200px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            margin: 0 auto 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 1s ease-in-out;
        ">
            <span id="breath-text" style="color:white;font-size:1.5rem;font-weight:700;">시작</span>
        </div>

        <div id="instruction" style="font-size:1.2rem;color:#1e3a5f;font-weight:600;margin-bottom:16px;">
            준비되면 시작을 누르세요
        </div>

        <div id="timer" style="font-size:2rem;font-weight:800;color:#3b82f6;margin-bottom:24px;">
            -
        </div>

        <div id="cycle-info" style="color:#64748b;margin-bottom:24px;">
            사이클: <span id="current-cycle">0</span> / {cycles}
        </div>

        <button id="start-btn" onclick="startBreathing()" style="
            padding: 16px 48px;
            font-size: 1.1rem;
            font-weight: 700;
            border: none;
            border-radius: 12px;
            background: #3b82f6;
            color: white;
            cursor: pointer;
        ">시작하기</button>
    </div>

    <script>
    const steps = {steps_json};
    const totalCycles = {cycles};
    let currentStep = 0;
    let currentCycle = 1;
    let timer;
    let countdown;
    let isRunning = false;

    const circle = document.getElementById('breath-circle');
    const text = document.getElementById('breath-text');
    const instruction = document.getElementById('instruction');
    const timerDisplay = document.getElementById('timer');
    const cycleDisplay = document.getElementById('current-cycle');
    const startBtn = document.getElementById('start-btn');

    function startBreathing() {{
        if (isRunning) {{
            stopBreathing();
            return;
        }}

        isRunning = true;
        currentStep = 0;
        currentCycle = 1;
        startBtn.textContent = '중지';
        startBtn.style.background = '#ef4444';
        runStep();
    }}

    function stopBreathing() {{
        isRunning = false;
        clearInterval(timer);
        clearTimeout(countdown);
        startBtn.textContent = '시작하기';
        startBtn.style.background = '#3b82f6';
        text.textContent = '시작';
        instruction.textContent = '준비되면 시작을 누르세요';
        timerDisplay.textContent = '-';
        circle.style.transform = 'scale(1)';
    }}

    function runStep() {{
        if (!isRunning) return;

        const step = steps[currentStep];
        let timeLeft = step.duration;

        text.textContent = step.action;
        instruction.textContent = step.instruction;
        cycleDisplay.textContent = currentCycle;

        // 애니메이션
        if (step.action === '들숨') {{
            circle.style.transform = 'scale(1.3)';
            circle.style.background = 'linear-gradient(135deg, #10b981, #3b82f6)';
        }} else if (step.action === '날숨') {{
            circle.style.transform = 'scale(0.8)';
            circle.style.background = 'linear-gradient(135deg, #8b5cf6, #ec4899)';
        }} else {{
            circle.style.background = 'linear-gradient(135deg, #f59e0b, #f97316)';
        }}

        timerDisplay.textContent = timeLeft;

        timer = setInterval(() => {{
            timeLeft--;
            timerDisplay.textContent = timeLeft;

            if (timeLeft <= 0) {{
                clearInterval(timer);
                nextStep();
            }}
        }}, 1000);
    }}

    function nextStep() {{
        currentStep++;

        if (currentStep >= steps.length) {{
            currentStep = 0;
            currentCycle++;

            if (currentCycle > totalCycles) {{
                // 완료
                isRunning = false;
                text.textContent = '완료!';
                instruction.textContent = '수고하셨습니다. 마음이 편안해졌나요?';
                timerDisplay.textContent = '🎉';
                circle.style.transform = 'scale(1)';
                circle.style.background = 'linear-gradient(135deg, #10b981, #22c55e)';
                startBtn.textContent = '다시 시작';
                startBtn.style.background = '#3b82f6';
                return;
            }}
        }}

        runStep();
    }}
    </script>
    """


# =====================
# UI
# =====================

def render_anxiety_management():
    """긴장 관리 UI"""

    st.markdown("""
    <style>
    .calm-header {
        background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 24px;
        text-align: center;
    }
    .exercise-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        cursor: pointer;
        transition: all 0.2s;
        border: 2px solid transparent;
    }
    .exercise-card:hover {
        border-color: #3b82f6;
        transform: translateY(-2px);
    }
    .affirmation-card {
        background: linear-gradient(135deg, #fef3c7, #fde68a);
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        font-size: 1.3rem;
        font-weight: 600;
        color: #92400e;
        margin: 16px 0;
    }
    .tip-card {
        background: #f0fdf4;
        border-left: 4px solid #10b981;
        padding: 16px;
        border-radius: 0 8px 8px 0;
        margin: 12px 0;
    }
    .anxiety-slider {
        margin: 24px 0;
    }
    .visualization-text {
        background: #f8fafc;
        border-radius: 12px;
        padding: 24px;
        font-size: 1.1rem;
        line-height: 2;
        color: #334155;
        white-space: pre-line;
    }
    </style>
    """, unsafe_allow_html=True)

    # 헤더
    st.markdown("""
    <div class="calm-header">
        <h2 style="margin:0 0 8px 0;">🧘 긴장 관리 모드</h2>
        <p style="margin:0;opacity:0.9;">면접 전 마음을 가라앉히고 자신감을 높이세요</p>
    </div>
    """, unsafe_allow_html=True)

    # 현재 긴장도 체크
    st.markdown("### 현재 긴장 상태는 어떤가요?")

    anxiety_level = st.slider(
        "긴장도를 선택하세요",
        1, 7, 4,
        key="anxiety_level",
        help="1: 매우 편안함 ~ 7: 매우 긴장됨"
    )

    level_info = ANXIETY_LEVELS[anxiety_level]
    st.markdown(f"""
    <div style="
        background: {level_info['color']}20;
        border-left: 4px solid {level_info['color']};
        padding: 16px;
        border-radius: 0 8px 8px 0;
        margin: 16px 0;
    ">
        <strong style="color:{level_info['color']};">{level_info['level']}</strong><br>
        {level_info['advice']}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 탭으로 기능 분리
    tab1, tab2, tab3, tab4 = st.tabs(["🌬 호흡 운동", "💭 긍정 확언", "🎬 시각화", "💡 빠른 팁"])

    with tab1:
        st.markdown("### 호흡 운동 선택")

        col1, col2, col3 = st.columns(3)

        exercises = list(BREATHING_EXERCISES.items())

        for i, (key, exercise) in enumerate(exercises):
            with [col1, col2, col3][i]:
                if st.button(
                    f"**{exercise['name']}**\n\n{exercise['duration']}",
                    key=f"breath_{key}",
                    use_container_width=True
                ):
                    st.session_state.selected_breathing = key
                    st.rerun()

                st.caption(exercise['description'])

        # 선택된 호흡 운동 표시
        if st.session_state.get("selected_breathing"):
            ex_key = st.session_state.selected_breathing
            exercise = BREATHING_EXERCISES[ex_key]

            st.markdown(f"### {exercise['name']}")
            st.markdown(f"**{exercise['cycles']}번 반복** | 총 약 {exercise['duration']}")

            # 애니메이션 컴포넌트
            components.html(get_breathing_animation(ex_key), height=450)

    with tab2:
        st.markdown("### 오늘의 긍정 확언")

        # 랜덤 확언 3개
        selected_affirmations = random.sample(AFFIRMATIONS, 3)

        for affirmation in selected_affirmations:
            st.markdown(f"""
            <div class="affirmation-card">
                "{affirmation}"
            </div>
            """, unsafe_allow_html=True)

        if st.button("새로운 확언 보기", key="new_affirmation"):
            st.rerun()

        st.markdown("---")
        st.markdown("### 나만의 확언 만들기")

        custom_affirmation = st.text_input(
            "자신에게 하고 싶은 말을 적어보세요",
            placeholder="나는 ..."
        )

        if custom_affirmation:
            st.markdown(f"""
            <div class="affirmation-card" style="background: linear-gradient(135deg, #dbeafe, #bfdbfe);">
                "{custom_affirmation}"
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.markdown("### 시각화 명상")
        st.caption("눈을 감고 천천히 읽으며 상상해보세요")

        viz_choice = st.radio(
            "시각화 유형",
            ["success", "calm"],
            format_func=lambda x: VISUALIZATION_SCRIPTS[x]["name"],
            horizontal=True
        )

        viz = VISUALIZATION_SCRIPTS[viz_choice]

        st.markdown(f"**{viz['name']}** ({viz['duration']})")

        st.markdown(f"""
        <div class="visualization-text">
            {viz['script']}
        </div>
        """, unsafe_allow_html=True)

        # 오디오 가이드 (TTS 사용 가능시)
        st.caption("💡 조용한 장소에서 눈을 감고 천천히 읽어보세요")

    with tab4:
        st.markdown("### 면접 직전 빠른 팁")

        for tip_item in QUICK_TIPS:
            st.markdown(f"""
            <div class="tip-card">
                <strong>✓ {tip_item['tip']}</strong><br>
                <span style="color:#64748b;font-size:0.9rem;">{tip_item['reason']}</span>
            </div>
            """, unsafe_allow_html=True)

        # 5분 전 체크리스트
        st.markdown("---")
        st.markdown("### ⏱ 면접 5분 전 체크")

        checks = [
            "심호흡 3번 했다",
            "미소 짓고 있다",
            "어깨가 펴져 있다",
            "핸드폰 무음/진동 확인",
            "자기소개 한번 더 떠올렸다",
        ]

        for check in checks:
            st.checkbox(check, key=f"final_{check}")


# 메인 실행
if __name__ == "__main__":
    render_anxiety_management()

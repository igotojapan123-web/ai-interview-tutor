"""
FLYREADY 신규 사용자 튜토리얼 컴포넌트
- 첫 방문 시 자동 표시
- 단계별 안내
- 추천 학습 경로
"""

import os
import json
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional

# 데이터 파일 경로
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(DATA_DIR, "data", "user_settings.json")


# ============================================================
# 설정 저장/로드
# ============================================================

def load_user_settings() -> Dict:
    """사용자 설정 로드"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {}


def save_user_settings(settings: Dict) -> bool:
    """사용자 설정 저장"""
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False


def is_tutorial_completed() -> bool:
    """튜토리얼 완료 여부 확인"""
    settings = load_user_settings()
    return settings.get("tutorial_completed", False)


def mark_tutorial_completed():
    """튜토리얼 완료로 표시"""
    settings = load_user_settings()
    settings["tutorial_completed"] = True
    settings["tutorial_completed_at"] = datetime.now().isoformat()
    save_user_settings(settings)


def reset_tutorial():
    """튜토리얼 다시 보기"""
    settings = load_user_settings()
    settings["tutorial_completed"] = False
    save_user_settings(settings)


# ============================================================
# 튜토리얼 스타일
# ============================================================

TUTORIAL_STYLES = """
<style>
.tutorial-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 9998;
}
.tutorial-modal {
    background: white;
    border-radius: 20px;
    padding: 32px;
    max-width: 600px;
    margin: 50px auto;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
    position: relative;
    z-index: 9999;
}
.tutorial-header {
    text-align: center;
    margin-bottom: 24px;
}
.tutorial-header h2 {
    color: #1e293b;
    margin-bottom: 8px;
}
.tutorial-step {
    background: #f8fafc;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    border-left: 4px solid #2563eb;
}
.tutorial-step.active {
    background: #eff6ff;
    border-left-color: #2563eb;
}
.tutorial-step.completed {
    background: #ecfdf5;
    border-left-color: #10b981;
}
.tutorial-step-number {
    display: inline-block;
    width: 28px;
    height: 28px;
    background: #2563eb;
    color: white;
    border-radius: 50%;
    text-align: center;
    line-height: 28px;
    font-weight: 700;
    margin-right: 12px;
}
.tutorial-step.completed .tutorial-step-number {
    background: #10b981;
}
.tutorial-path-card {
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
    cursor: pointer;
    transition: all 0.2s;
    text-align: center;
}
.tutorial-path-card:hover {
    border-color: #2563eb;
    background: #eff6ff;
}
.tutorial-path-card.selected {
    border-color: #2563eb;
    background: #eff6ff;
}
.tutorial-path-icon {
    font-size: 2rem;
    margin-bottom: 8px;
}
.tutorial-progress {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-bottom: 24px;
}
.tutorial-progress-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #e2e8f0;
}
.tutorial-progress-dot.active {
    background: #2563eb;
}
.tutorial-progress-dot.completed {
    background: #10b981;
}
</style>
"""


# ============================================================
# 튜토리얼 데이터
# ============================================================

AIRLINES = [
    "대한항공", "아시아나", "제주항공", "진에어", "티웨이",
    "에어부산", "에어서울", "이스타항공", "에어로케이", "기타"
]

PREP_STAGES = [
    {"id": "resume", "name": "서류 준비", "icon": "📝"},
    {"id": "first", "name": "1차 면접", "icon": "🎙️"},
    {"id": "second", "name": "2차 면접", "icon": "🏆"},
]

LEARNING_PATHS = {
    "resume": {
        "title": "서류 준비 중",
        "description": "자소서 작성과 예상 질문 준비에 집중하세요",
        "steps": [
            {"page": "pages/19_자소서작성.py", "name": "자소서 작성", "icon": "📝"},
            {"page": "pages/20_자소서첨삭.py", "name": "자소서 첨삭", "icon": "✍️"},
            {"page": "pages/17_자소서기반질문.py", "name": "예상 질문 생성", "icon": "❓"},
        ]
    },
    "first": {
        "title": "1차 면접 준비",
        "description": "실전 면접 연습으로 감각을 키우세요",
        "steps": [
            {"page": "pages/4_모의면접.py", "name": "모의면접", "icon": "🎙️"},
            {"page": "pages/1_롤플레잉.py", "name": "롤플레잉", "icon": "✈️"},
            {"page": "pages/2_영어면접.py", "name": "영어면접", "icon": "🌍"},
        ]
    },
    "second": {
        "title": "2차 면접 준비",
        "description": "심화 면접과 토론 능력을 기르세요",
        "steps": [
            {"page": "pages/13_실전연습.py", "name": "실전연습", "icon": "🎯"},
            {"page": "pages/5_토론면접.py", "name": "토론면접", "icon": "💬"},
            {"page": "pages/37_그룹면접.py", "name": "그룹면접", "icon": "👥"},
        ]
    },
}


# ============================================================
# 튜토리얼 UI
# ============================================================

def show_tutorial():
    """튜토리얼 표시"""
    st.markdown(TUTORIAL_STYLES, unsafe_allow_html=True)

    # 세션 상태 초기화
    if "tutorial_step" not in st.session_state:
        st.session_state.tutorial_step = 1
    if "tutorial_airline" not in st.session_state:
        st.session_state.tutorial_airline = ""
    if "tutorial_dday" not in st.session_state:
        st.session_state.tutorial_dday = None
    if "tutorial_stage" not in st.session_state:
        st.session_state.tutorial_stage = ""

    step = st.session_state.tutorial_step

    # 진행 상태 표시
    progress_html = '<div class="tutorial-progress">'
    for i in range(1, 6):
        if i < step:
            progress_html += '<div class="tutorial-progress-dot completed"></div>'
        elif i == step:
            progress_html += '<div class="tutorial-progress-dot active"></div>'
        else:
            progress_html += '<div class="tutorial-progress-dot"></div>'
    progress_html += '</div>'
    st.markdown(progress_html, unsafe_allow_html=True)

    # Step 1: 환영 메시지
    if step == 1:
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 4rem;">✈️</div>
            <h1 style="color: #1e293b; margin: 16px 0;">FLYREADY에 오신 걸 환영합니다!</h1>
            <p style="color: #64748b; font-size: 1.1rem;">
                AI와 함께 승무원 면접을 준비하는 가장 스마트한 방법입니다.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("시작하기", type="primary", use_container_width=True):
                st.session_state.tutorial_step = 2
                st.rerun()

    # Step 2: 항공사 선택
    elif step == 2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 24px;">
            <h2>지원할 항공사를 선택하세요</h2>
            <p style="color: #64748b;">항공사별 맞춤 면접 준비를 도와드려요</p>
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(5)
        for i, airline in enumerate(AIRLINES):
            with cols[i % 5]:
                selected = st.session_state.tutorial_airline == airline
                btn_type = "primary" if selected else "secondary"
                if st.button(airline, key=f"airline_{i}", use_container_width=True,
                           type=btn_type if selected else "secondary"):
                    st.session_state.tutorial_airline = airline
                    st.rerun()

        if st.session_state.tutorial_airline:
            st.success(f"선택: **{st.session_state.tutorial_airline}**")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("이전", use_container_width=True):
                    st.session_state.tutorial_step = 1
                    st.rerun()
            with col2:
                if st.button("다음", type="primary", use_container_width=True):
                    st.session_state.tutorial_step = 3
                    st.rerun()

    # Step 3: D-Day 설정
    elif step == 3:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 24px;">
            <h2>면접 예정일을 알려주세요</h2>
            <p style="color: #64748b;">목표 날짜를 설정하면 학습 계획을 세워드려요</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            dday = st.date_input("면접 예정일", value=None, key="tutorial_dday_input")
            st.session_state.tutorial_dday = dday

            skip = st.checkbox("아직 모르겠어요 (나중에 설정)")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("이전", use_container_width=True):
                st.session_state.tutorial_step = 2
                st.rerun()
        with col2:
            if st.button("다음", type="primary", use_container_width=True):
                st.session_state.tutorial_step = 4
                st.rerun()

    # Step 4: 준비 단계 선택
    elif step == 4:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 24px;">
            <h2>현재 준비 단계는 어디인가요?</h2>
            <p style="color: #64748b;">단계에 맞는 학습 경로를 추천해드려요</p>
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(3)
        for i, stage in enumerate(PREP_STAGES):
            with cols[i]:
                selected = st.session_state.tutorial_stage == stage["id"]
                st.markdown(f"""
                <div class="tutorial-path-card {'selected' if selected else ''}"
                     style="margin-bottom: 12px;">
                    <div class="tutorial-path-icon">{stage['icon']}</div>
                    <div style="font-weight: 600;">{stage['name']}</div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"선택", key=f"stage_{stage['id']}", use_container_width=True,
                           type="primary" if selected else "secondary"):
                    st.session_state.tutorial_stage = stage["id"]
                    st.rerun()

        if st.session_state.tutorial_stage:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("이전", use_container_width=True):
                    st.session_state.tutorial_step = 3
                    st.rerun()
            with col2:
                if st.button("다음", type="primary", use_container_width=True):
                    st.session_state.tutorial_step = 5
                    st.rerun()

    # Step 5: 추천 학습 경로
    elif step == 5:
        stage = st.session_state.tutorial_stage or "first"
        path = LEARNING_PATHS.get(stage, LEARNING_PATHS["first"])

        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 24px;">
            <h2>추천 학습 경로</h2>
            <p style="color: #64748b;">{path['description']}</p>
        </div>
        """, unsafe_allow_html=True)

        # 추천 순서 표시
        for i, step_info in enumerate(path["steps"], 1):
            st.markdown(f"""
            <div class="tutorial-step">
                <span class="tutorial-step-number">{i}</span>
                <span style="font-weight: 600;">{step_info['icon']} {step_info['name']}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 설정 저장 및 완료
        col1, col2 = st.columns(2)
        with col1:
            if st.button("이전", use_container_width=True):
                st.session_state.tutorial_step = 4
                st.rerun()
        with col2:
            if st.button("시작하기", type="primary", use_container_width=True):
                # 설정 저장
                settings = load_user_settings()
                settings["tutorial_completed"] = True
                settings["tutorial_completed_at"] = datetime.now().isoformat()
                settings["target_airline"] = st.session_state.tutorial_airline
                settings["target_dday"] = str(st.session_state.tutorial_dday) if st.session_state.tutorial_dday else None
                settings["prep_stage"] = st.session_state.tutorial_stage
                save_user_settings(settings)

                # 세션 초기화
                st.session_state.tutorial_step = 1
                st.toast("튜토리얼 완료! 학습을 시작하세요!", icon="🎉")
                st.rerun()

        # 다시 보지 않기
        st.markdown("<br>", unsafe_allow_html=True)
        if st.checkbox("다음부터 튜토리얼 건너뛰기"):
            mark_tutorial_completed()


def show_tutorial_button():
    """튜토리얼 다시 보기 버튼"""
    if st.button("튜토리얼 다시 보기", key="show_tutorial_btn"):
        reset_tutorial()
        st.session_state.tutorial_step = 1
        st.rerun()


# ============================================================
# 메인 함수
# ============================================================

def render_tutorial_if_needed():
    """필요한 경우 튜토리얼 표시"""
    if not is_tutorial_completed():
        show_tutorial()
        return True
    return False


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    st.set_page_config(page_title="튜토리얼 테스트", page_icon="📚")
    st.title("튜토리얼 테스트")

    # 리셋 버튼
    if st.button("튜토리얼 리셋"):
        reset_tutorial()
        st.session_state.tutorial_step = 1
        st.rerun()

    show_tutorial()

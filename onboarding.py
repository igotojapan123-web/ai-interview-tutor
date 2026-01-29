# onboarding.py
# FlyReady Lab - 온보딩 튜토리얼 시스템
# 첫 방문자를 위한 가이드 투어

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

# ============================================
# 온보딩 상태 관리
# ============================================
ONBOARDING_VERSION = "1.0"  # 버전 변경시 다시 표시

def init_onboarding():
    """온보딩 상태 초기화"""
    if "onboarding_completed" not in st.session_state:
        st.session_state.onboarding_completed = False
    if "onboarding_step" not in st.session_state:
        st.session_state.onboarding_step = 0
    if "onboarding_version" not in st.session_state:
        st.session_state.onboarding_version = ""


def should_show_onboarding() -> bool:
    """온보딩 표시 여부 확인"""
    init_onboarding()
    # 버전이 다르거나 완료하지 않은 경우 표시
    return (
        not st.session_state.onboarding_completed or
        st.session_state.onboarding_version != ONBOARDING_VERSION
    )


def complete_onboarding():
    """온보딩 완료 처리"""
    st.session_state.onboarding_completed = True
    st.session_state.onboarding_version = ONBOARDING_VERSION
    st.session_state.onboarding_step = 0


def skip_onboarding():
    """온보딩 건너뛰기"""
    complete_onboarding()


def reset_onboarding():
    """온보딩 리셋 (디버깅/테스트용)"""
    st.session_state.onboarding_completed = False
    st.session_state.onboarding_step = 0
    st.session_state.onboarding_version = ""


# ============================================
# 온보딩 스텝 정의
# ============================================
ONBOARDING_STEPS = [
    {
        "title": "FlyReady Lab에 오신 것을 환영합니다",
        "content": "AI와 함께하는 승무원 면접 준비 서비스입니다. 모의면접, 롤플레잉, 자소서 첨삭 등 다양한 기능을 제공합니다.",
        "image": "welcome",
        "highlight": None,
    },
    {
        "title": "AI 모의면접",
        "content": "실제 면접처럼 AI 면접관과 대화하며 연습하세요. 음성 또는 텍스트로 답변하고, 즉각적인 피드백을 받을 수 있습니다.",
        "image": "interview",
        "highlight": "모의면접",
        "link": "/모의면접",
    },
    {
        "title": "기내 롤플레잉",
        "content": "실제 기내 상황을 시뮬레이션합니다. AI 승객과 대화하며 다양한 상황 대응 능력을 키워보세요.",
        "image": "roleplay",
        "highlight": "롤플레잉",
        "link": "/롤플레잉",
    },
    {
        "title": "자소서 AI 첨삭",
        "content": "자기소개서를 붙여넣으면 AI가 분석하여 개선점을 제안합니다. 항공사별 맞춤 피드백도 제공됩니다.",
        "image": "document",
        "highlight": "자소서첨삭",
        "link": "/자소서첨삭",
    },
    {
        "title": "성장 그래프",
        "content": "연습할 때마다 점수가 자동으로 기록됩니다. 시간에 따른 실력 향상을 그래프로 확인하세요.",
        "image": "chart",
        "highlight": "성장그래프",
        "link": "/성장그래프",
    },
    {
        "title": "준비 완료!",
        "content": "이제 FlyReady Lab의 모든 기능을 자유롭게 사용하실 수 있습니다. 합격을 향해 함께 달려봅시다!",
        "image": "ready",
        "highlight": None,
    },
]


# ============================================
# 온보딩 UI 컴포넌트
# ============================================
def get_onboarding_css():
    """온보딩 CSS 스타일"""
    return """
<style>
/* 온보딩 오버레이 */
.fr-onboarding-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(4px);
    z-index: 9998;
    display: flex;
    align-items: center;
    justify-content: center;
    animation: fr-fade-in 0.3s ease-out;
}

/* 온보딩 모달 */
.fr-onboarding-modal {
    background: white;
    border-radius: 20px;
    max-width: 520px;
    width: 90%;
    max-height: 90vh;
    overflow: hidden;
    box-shadow: 0 25px 50px rgba(0,0,0,0.25);
    animation: fr-scale-in 0.3s ease-out;
}

@keyframes fr-fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes fr-scale-in {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
}

/* 온보딩 헤더 */
.fr-onboarding-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #3b82f6 100%);
    padding: 32px 32px 40px 32px;
    text-align: center;
    color: white;
}

.fr-onboarding-illustration {
    width: 100px;
    height: 100px;
    margin: 0 auto 16px auto;
    background: rgba(255,255,255,0.15);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.fr-onboarding-title {
    font-size: 1.5rem;
    font-weight: 800;
    margin: 0;
}

/* 온보딩 바디 */
.fr-onboarding-body {
    padding: 32px;
}

.fr-onboarding-content {
    color: #334155;
    font-size: 1rem;
    line-height: 1.7;
    text-align: center;
    margin-bottom: 24px;
}

/* 진행률 도트 */
.fr-onboarding-dots {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-bottom: 24px;
}

.fr-onboarding-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #e2e8f0;
    transition: all 0.3s ease;
}

.fr-onboarding-dot.active {
    background: #3b82f6;
    width: 24px;
    border-radius: 5px;
}

.fr-onboarding-dot.completed {
    background: #10b981;
}

/* 온보딩 버튼 */
.fr-onboarding-actions {
    display: flex;
    gap: 12px;
}

.fr-onboarding-btn {
    flex: 1;
    padding: 14px 24px;
    border-radius: 10px;
    font-weight: 600;
    font-size: 0.95rem;
    cursor: pointer;
    transition: all 0.2s ease;
    border: none;
    text-align: center;
    text-decoration: none;
}

.fr-onboarding-btn-primary {
    background: #3b82f6;
    color: white;
}

.fr-onboarding-btn-primary:hover {
    background: #2563eb;
    transform: translateY(-2px);
}

.fr-onboarding-btn-secondary {
    background: #f1f5f9;
    color: #64748b;
}

.fr-onboarding-btn-secondary:hover {
    background: #e2e8f0;
}

/* 건너뛰기 링크 */
.fr-onboarding-skip {
    display: block;
    text-align: center;
    margin-top: 16px;
    color: #94a3b8;
    font-size: 0.85rem;
    cursor: pointer;
    text-decoration: none;
}

.fr-onboarding-skip:hover {
    color: #64748b;
    text-decoration: underline;
}
</style>
"""


def get_step_illustration(image_type: str) -> str:
    """스텝별 일러스트레이션 SVG"""
    illustrations = {
        "welcome": '''<svg width="60" height="60" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M30 5L35 20H50L38 30L43 45L30 35L17 45L22 30L10 20H25L30 5Z" fill="white"/>
        </svg>''',
        "interview": '''<svg width="60" height="60" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="20" y="10" width="20" height="30" rx="10" fill="white" fill-opacity="0.9"/>
            <path d="M15 35v3a15 15 0 0030 0v-3" stroke="white" stroke-width="3" fill="none"/>
            <line x1="30" y1="50" x2="30" y2="55" stroke="white" stroke-width="3"/>
        </svg>''',
        "roleplay": '''<svg width="60" height="60" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="22" cy="22" r="10" fill="white" fill-opacity="0.9"/>
            <circle cx="38" cy="22" r="10" fill="white" fill-opacity="0.7"/>
            <path d="M15 45c0-8 6-12 15-12s15 4 15 12" fill="white" fill-opacity="0.9"/>
        </svg>''',
        "document": '''<svg width="60" height="60" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="15" y="8" width="30" height="44" rx="3" fill="white" fill-opacity="0.9"/>
            <line x1="22" y1="20" x2="38" y2="20" stroke="#3b82f6" stroke-width="2"/>
            <line x1="22" y1="28" x2="38" y2="28" stroke="#3b82f6" stroke-width="2"/>
            <line x1="22" y1="36" x2="32" y2="36" stroke="#3b82f6" stroke-width="2"/>
        </svg>''',
        "chart": '''<svg width="60" height="60" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="12" y="35" width="10" height="15" rx="2" fill="white" fill-opacity="0.7"/>
            <rect x="25" y="25" width="10" height="25" rx="2" fill="white" fill-opacity="0.85"/>
            <rect x="38" y="15" width="10" height="35" rx="2" fill="white"/>
        </svg>''',
        "ready": '''<svg width="60" height="60" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="30" cy="30" r="22" stroke="white" stroke-width="4" fill="none"/>
            <polyline points="20,30 27,37 40,24" stroke="white" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
    }
    return illustrations.get(image_type, illustrations["welcome"])


def render_onboarding_step(step_index: int):
    """온보딩 스텝 렌더링"""
    if step_index >= len(ONBOARDING_STEPS):
        complete_onboarding()
        return

    step = ONBOARDING_STEPS[step_index]
    total_steps = len(ONBOARDING_STEPS)

    # 도트 인디케이터 생성
    dots_html = ""
    for i in range(total_steps):
        if i < step_index:
            dots_html += '<div class="fr-onboarding-dot completed"></div>'
        elif i == step_index:
            dots_html += '<div class="fr-onboarding-dot active"></div>'
        else:
            dots_html += '<div class="fr-onboarding-dot"></div>'

    # 버튼 텍스트
    if step_index == 0:
        prev_btn = ""
        next_text = "시작하기"
    elif step_index == total_steps - 1:
        prev_btn = '<button class="fr-onboarding-btn fr-onboarding-btn-secondary" onclick="window.prevStep()">이전</button>'
        next_text = "완료"
    else:
        prev_btn = '<button class="fr-onboarding-btn fr-onboarding-btn-secondary" onclick="window.prevStep()">이전</button>'
        next_text = "다음"

    illustration = get_step_illustration(step["image"])

    modal_html = f'''
    {get_onboarding_css()}
    <div class="fr-onboarding-overlay">
        <div class="fr-onboarding-modal">
            <div class="fr-onboarding-header">
                <div class="fr-onboarding-illustration">{illustration}</div>
                <h2 class="fr-onboarding-title">{step["title"]}</h2>
            </div>
            <div class="fr-onboarding-body">
                <p class="fr-onboarding-content">{step["content"]}</p>
                <div class="fr-onboarding-dots">{dots_html}</div>
                <div class="fr-onboarding-actions">
                    {prev_btn}
                    <button class="fr-onboarding-btn fr-onboarding-btn-primary" onclick="window.nextStep()">{next_text}</button>
                </div>
                <a class="fr-onboarding-skip" onclick="window.skipOnboarding()">건너뛰기</a>
            </div>
        </div>
    </div>
    '''

    return modal_html


def show_onboarding():
    """온보딩 표시 (Streamlit 네이티브 방식)"""
    init_onboarding()

    if not should_show_onboarding():
        return False

    step_index = st.session_state.onboarding_step
    total_steps = len(ONBOARDING_STEPS)

    if step_index >= total_steps:
        complete_onboarding()
        return False

    step = ONBOARDING_STEPS[step_index]

    # 모달 스타일 오버레이
    st.markdown("""
    <style>
    .fr-modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(15, 23, 42, 0.85);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)

    # 팝업 컨테이너
    with st.container():
        st.markdown(f"""
        <div style="
            background: white;
            border-radius: 20px;
            max-width: 500px;
            margin: 40px auto;
            overflow: hidden;
            box-shadow: 0 25px 50px rgba(0,0,0,0.25);
        ">
            <div style="
                background: linear-gradient(135deg, #1e3a5f 0%, #3b82f6 100%);
                padding: 32px;
                text-align: center;
                color: white;
            ">
                <div style="
                    width: 80px;
                    height: 80px;
                    margin: 0 auto 16px auto;
                    background: rgba(255,255,255,0.15);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    {get_step_illustration(step["image"])}
                </div>
                <h2 style="font-size: 1.4rem; font-weight: 800; margin: 0;">{step["title"]}</h2>
            </div>
            <div style="padding: 28px;">
                <p style="color: #334155; font-size: 1rem; line-height: 1.7; text-align: center; margin-bottom: 20px;">
                    {step["content"]}
                </p>
                <div style="display: flex; justify-content: center; gap: 6px; margin-bottom: 20px;">
                    {"".join([f'<div style="width: {"24px" if i == step_index else "10px"}; height: 10px; border-radius: 5px; background: {"#3b82f6" if i == step_index else ("#10b981" if i < step_index else "#e2e8f0")}; transition: all 0.3s;"></div>' for i in range(total_steps)])}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 버튼 영역
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if step_index > 0:
                if st.button("이전", key="onboarding_prev", use_container_width=True):
                    st.session_state.onboarding_step -= 1
                    st.rerun()

        with col2:
            btn_text = "시작하기" if step_index == 0 else ("완료" if step_index == total_steps - 1 else "다음")
            if st.button(btn_text, key="onboarding_next", type="primary", use_container_width=True):
                if step_index == total_steps - 1:
                    complete_onboarding()
                else:
                    st.session_state.onboarding_step += 1
                st.rerun()

        with col3:
            if st.button("건너뛰기", key="onboarding_skip", use_container_width=True):
                skip_onboarding()
                st.rerun()

    return True


# ============================================
# 헬프 툴팁 컴포넌트
# ============================================
def render_help_tooltip(text: str, tooltip: str):
    """헬프 툴팁이 있는 텍스트 렌더링"""
    st.markdown(f'''
    <span style="display:inline-flex;align-items:center;gap:4px;">
        {text}
        <span style="cursor:help;color:#94a3b8;" title="{tooltip}">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                <path d="M12 17h.01"/>
            </svg>
        </span>
    </span>
    ''', unsafe_allow_html=True)


def render_feature_highlight(title: str, description: str, link: str = ""):
    """기능 하이라이트 카드"""
    link_html = ""
    if link:
        link_html = f'<a href="{link}" style="color:#3b82f6;font-size:0.85rem;text-decoration:none;font-weight:600;">자세히 보기 →</a>'

    st.markdown(f'''
    <div style="
        background: linear-gradient(135deg, #eff6ff, #dbeafe);
        border: 1px solid #93c5fd;
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
    ">
        <div style="font-weight: 700; color: #1e40af; margin-bottom: 8px;">{title}</div>
        <div style="color: #334155; font-size: 0.9rem; line-height: 1.5; margin-bottom: 8px;">{description}</div>
        {link_html}
    </div>
    ''', unsafe_allow_html=True)

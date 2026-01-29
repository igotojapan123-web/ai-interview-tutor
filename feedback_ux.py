# feedback_ux.py
# 대기업 수준 사용자 피드백 UX 시스템
# FlyReady Lab - Enterprise User Feedback Module

import streamlit as st
import time
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass
from enum import Enum
import uuid

# =============================================================================
# 로딩 메시지 표준화
# =============================================================================

class LoadingType(Enum):
    """로딩 유형"""
    GENERAL = "general"
    AI_ANALYSIS = "ai_analysis"
    VOICE = "voice"
    VIDEO = "video"
    FILE = "file"
    NETWORK = "network"
    SAVE = "save"


# 표준화된 로딩 메시지
LOADING_MESSAGES: Dict[LoadingType, Dict[str, str]] = {
    LoadingType.GENERAL: {
        "start": "처리 중입니다",
        "progress": "잠시만 기다려 주세요",
        "finish": "완료되었습니다"
    },
    LoadingType.AI_ANALYSIS: {
        "start": "AI가 분석하고 있습니다",
        "progress": "답변을 생성하고 있습니다",
        "finish": "분석이 완료되었습니다"
    },
    LoadingType.VOICE: {
        "start": "음성을 처리하고 있습니다",
        "progress": "음성을 변환하고 있습니다",
        "finish": "음성 처리가 완료되었습니다"
    },
    LoadingType.VIDEO: {
        "start": "영상을 처리하고 있습니다",
        "progress": "프레임을 분석하고 있습니다",
        "finish": "영상 처리가 완료되었습니다"
    },
    LoadingType.FILE: {
        "start": "파일을 처리하고 있습니다",
        "progress": "데이터를 읽고 있습니다",
        "finish": "파일 처리가 완료되었습니다"
    },
    LoadingType.NETWORK: {
        "start": "서버와 통신 중입니다",
        "progress": "데이터를 가져오고 있습니다",
        "finish": "데이터 수신이 완료되었습니다"
    },
    LoadingType.SAVE: {
        "start": "저장 중입니다",
        "progress": "데이터를 기록하고 있습니다",
        "finish": "저장이 완료되었습니다"
    }
}


def get_loading_message(loading_type: LoadingType, stage: str = "start") -> str:
    """로딩 메시지 반환"""
    messages = LOADING_MESSAGES.get(loading_type, LOADING_MESSAGES[LoadingType.GENERAL])
    return messages.get(stage, messages["start"])


# =============================================================================
# 스피너 컴포넌트 (개선된 버전)
# =============================================================================

def loading_spinner(
    loading_type: LoadingType = LoadingType.GENERAL,
    custom_message: Optional[str] = None
):
    """표준화된 로딩 스피너

    Args:
        loading_type: 로딩 유형
        custom_message: 커스텀 메시지 (선택)

    Returns:
        Streamlit spinner context manager
    """
    message = custom_message or get_loading_message(loading_type, "start")
    return st.spinner(message)


def render_loading_overlay(
    loading_type: LoadingType = LoadingType.GENERAL,
    show_progress: bool = False,
    progress_value: float = 0
):
    """로딩 오버레이 렌더링"""
    message = get_loading_message(loading_type, "progress" if show_progress else "start")

    overlay_html = f"""
    <div class="fr-loading-overlay" style="
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    ">
        <div class="fr-loading-spinner" style="
            width: 48px;
            height: 48px;
            border: 3px solid #e2e8f0;
            border-top: 3px solid #2563eb;
            border-radius: 50%;
            animation: fr-spin 1s linear infinite;
        "></div>
        <p style="margin-top: 16px; color: #334155; font-size: 16px; font-weight: 500;">
            {message}
        </p>
        {f'<div style="width: 200px; height: 4px; background: #e2e8f0; border-radius: 2px; margin-top: 12px;"><div style="width: {progress_value * 100}%; height: 100%; background: #2563eb; border-radius: 2px; transition: width 0.3s ease;"></div></div>' if show_progress else ''}
    </div>
    <style>
        @keyframes fr-spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
    """
    st.markdown(overlay_html, unsafe_allow_html=True)


# =============================================================================
# 스켈레톤 로더
# =============================================================================

def render_skeleton(
    count: int = 3,
    show_avatar: bool = False,
    line_height: int = 20,
    spacing: int = 12
):
    """스켈레톤 로더 렌더링

    Args:
        count: 스켈레톤 줄 수
        show_avatar: 아바타 표시 여부
        line_height: 줄 높이 (px)
        spacing: 줄 간격 (px)
    """
    skeleton_css = """
    <style>
    @keyframes fr-skeleton-pulse {
        0% { opacity: 1; }
        50% { opacity: 0.4; }
        100% { opacity: 1; }
    }
    .fr-skeleton {
        background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
        background-size: 200% 100%;
        animation: fr-skeleton-pulse 1.5s ease-in-out infinite;
        border-radius: 4px;
    }
    </style>
    """

    avatar_html = f"""
        <div class="fr-skeleton" style="
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 12px;
            flex-shrink: 0;
        "></div>
    """ if show_avatar else ""

    lines_html = ""
    widths = [100, 80, 60, 90, 70]  # 다양한 너비

    for i in range(count):
        width = widths[i % len(widths)]
        lines_html += f"""
        <div class="fr-skeleton" style="
            height: {line_height}px;
            width: {width}%;
            margin-bottom: {spacing}px;
        "></div>
        """

    skeleton_html = f"""
    {skeleton_css}
    <div style="display: flex; align-items: flex-start;">
        {avatar_html}
        <div style="flex: 1;">
            {lines_html}
        </div>
    </div>
    """

    st.markdown(skeleton_html, unsafe_allow_html=True)


def render_card_skeleton(count: int = 3):
    """카드 스켈레톤 렌더링"""
    cards_html = ""

    for _ in range(count):
        cards_html += """
        <div style="
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        ">
            <div class="fr-skeleton" style="height: 24px; width: 60%; margin-bottom: 12px;"></div>
            <div class="fr-skeleton" style="height: 16px; width: 100%; margin-bottom: 8px;"></div>
            <div class="fr-skeleton" style="height: 16px; width: 80%; margin-bottom: 16px;"></div>
            <div style="display: flex; gap: 8px;">
                <div class="fr-skeleton" style="height: 32px; width: 80px; border-radius: 6px;"></div>
                <div class="fr-skeleton" style="height: 32px; width: 80px; border-radius: 6px;"></div>
            </div>
        </div>
        """

    skeleton_css = """
    <style>
    @keyframes fr-skeleton-pulse {
        0% { opacity: 1; }
        50% { opacity: 0.4; }
        100% { opacity: 1; }
    }
    .fr-skeleton {
        background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
        background-size: 200% 100%;
        animation: fr-skeleton-pulse 1.5s ease-in-out infinite;
        border-radius: 4px;
    }
    </style>
    """

    st.markdown(skeleton_css + cards_html, unsafe_allow_html=True)


# =============================================================================
# 진행률 표시
# =============================================================================

@dataclass
class ProgressState:
    """진행 상태"""
    current: int = 0
    total: int = 100
    message: str = ""
    sub_message: str = ""


def render_progress_indicator(
    state: ProgressState,
    show_percentage: bool = True,
    show_eta: bool = False,
    eta_seconds: Optional[int] = None
):
    """진행률 인디케이터 렌더링"""
    percentage = min(100, max(0, (state.current / state.total * 100))) if state.total > 0 else 0

    progress_html = f"""
    <div style="margin: 16px 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-weight: 500; color: #334155;">{state.message}</span>
            {'<span style="color: #64748b;">' + f'{percentage:.0f}%' + '</span>' if show_percentage else ''}
        </div>

        <div style="
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
        ">
            <div style="
                width: {percentage}%;
                height: 100%;
                background: linear-gradient(90deg, #2563eb, #3b82f6);
                border-radius: 4px;
                transition: width 0.3s ease;
            "></div>
        </div>

        <div style="display: flex; justify-content: space-between; margin-top: 4px;">
            <span style="font-size: 13px; color: #64748b;">{state.sub_message}</span>
            {'<span style="font-size: 13px; color: #64748b;">예상 시간: ' + str(eta_seconds) + '초</span>' if show_eta and eta_seconds else ''}
        </div>
    </div>
    """

    st.markdown(progress_html, unsafe_allow_html=True)


def create_progress_tracker(total: int, message: str = "처리 중"):
    """진행률 트래커 생성

    Args:
        total: 전체 항목 수
        message: 메시지

    Returns:
        progress_bar, update_func
    """
    progress_bar = st.progress(0, text=message)
    start_time = time.time()

    def update(current: int, sub_message: str = ""):
        percentage = current / total if total > 0 else 0
        elapsed = time.time() - start_time

        # ETA 계산
        if current > 0:
            eta = (elapsed / current) * (total - current)
            eta_text = f" (예상 {int(eta)}초 남음)" if eta > 1 else ""
        else:
            eta_text = ""

        text = f"{message}: {current}/{total}{eta_text}"
        if sub_message:
            text += f" - {sub_message}"

        progress_bar.progress(percentage, text=text)

    def finish():
        progress_bar.progress(1.0, text=f"{message}: 완료")
        time.sleep(0.5)
        progress_bar.empty()

    return progress_bar, update, finish


# =============================================================================
# 토스트 알림
# =============================================================================

class ToastType(Enum):
    """토스트 유형"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


TOAST_STYLES = {
    ToastType.SUCCESS: {
        "bg": "#ecfdf5",
        "border": "#34d399",
        "icon_color": "#059669",
        "text_color": "#065f46",
        "icon": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>"""
    },
    ToastType.ERROR: {
        "bg": "#fef2f2",
        "border": "#f87171",
        "icon_color": "#dc2626",
        "text_color": "#991b1b",
        "icon": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>"""
    },
    ToastType.WARNING: {
        "bg": "#fffbeb",
        "border": "#fbbf24",
        "icon_color": "#d97706",
        "text_color": "#92400e",
        "icon": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>"""
    },
    ToastType.INFO: {
        "bg": "#eff6ff",
        "border": "#60a5fa",
        "icon_color": "#2563eb",
        "text_color": "#1e40af",
        "icon": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>"""
    }
}


def show_toast(
    message: str,
    toast_type: ToastType = ToastType.INFO,
    duration: int = 3000,
    dismissible: bool = True
):
    """토스트 알림 표시

    Args:
        message: 알림 메시지
        toast_type: 토스트 유형
        duration: 표시 시간 (ms)
        dismissible: 닫기 버튼 표시
    """
    style = TOAST_STYLES[toast_type]
    toast_id = f"toast_{uuid.uuid4().hex[:8]}"

    dismiss_button = f"""
        <button onclick="document.getElementById('{toast_id}').remove()"
                style="background:none;border:none;cursor:pointer;padding:4px;color:{style['icon_color']};">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
        </button>
    """ if dismissible else ""

    toast_html = f"""
    <div id="{toast_id}" class="fr-toast" style="
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 14px 18px;
        background: {style['bg']};
        border: 1px solid {style['border']};
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        animation: fr-toast-slide-in 0.3s ease;
        max-width: 400px;
    ">
        <span style="color: {style['icon_color']}; flex-shrink: 0;">
            {style['icon']}
        </span>
        <span style="color: {style['text_color']}; font-size: 14px; flex: 1;">
            {message}
        </span>
        {dismiss_button}
    </div>

    <style>
        @keyframes fr-toast-slide-in {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        @keyframes fr-toast-slide-out {{
            from {{ transform: translateX(0); opacity: 1; }}
            to {{ transform: translateX(100%); opacity: 0; }}
        }}
    </style>

    <script>
        setTimeout(function() {{
            var toast = document.getElementById('{toast_id}');
            if (toast) {{
                toast.style.animation = 'fr-toast-slide-out 0.3s ease forwards';
                setTimeout(function() {{ toast.remove(); }}, 300);
            }}
        }}, {duration});
    </script>
    """

    st.markdown(toast_html, unsafe_allow_html=True)


# 편의 함수
def toast_success(message: str, duration: int = 3000):
    """성공 토스트"""
    show_toast(message, ToastType.SUCCESS, duration)


def toast_error(message: str, duration: int = 5000):
    """에러 토스트"""
    show_toast(message, ToastType.ERROR, duration)


def toast_warning(message: str, duration: int = 4000):
    """경고 토스트"""
    show_toast(message, ToastType.WARNING, duration)


def toast_info(message: str, duration: int = 3000):
    """정보 토스트"""
    show_toast(message, ToastType.INFO, duration)


# =============================================================================
# 재시도 UI
# =============================================================================

def render_retry_button(
    callback: Callable,
    error_message: str = "오류가 발생했습니다",
    retry_text: str = "다시 시도",
    button_key: Optional[str] = None
):
    """재시도 버튼 렌더링

    Args:
        callback: 재시도 시 호출할 함수
        error_message: 에러 메시지
        retry_text: 버튼 텍스트
        button_key: 버튼 키
    """
    col1, col2 = st.columns([3, 1])

    with col1:
        st.error(error_message)

    with col2:
        key = button_key or f"retry_{uuid.uuid4().hex[:8]}"
        if st.button(retry_text, key=key, type="primary"):
            callback()
            st.rerun()


def with_retry_ui(
    func: Callable,
    loading_type: LoadingType = LoadingType.GENERAL,
    error_message: str = "처리 중 오류가 발생했습니다",
    max_retries: int = 3
) -> Any:
    """재시도 UI가 포함된 함수 실행

    Args:
        func: 실행할 함수
        loading_type: 로딩 유형
        error_message: 에러 메시지
        max_retries: 최대 재시도 횟수

    Returns:
        함수 실행 결과 또는 None
    """
    retry_key = f"retry_count_{id(func)}"

    if retry_key not in st.session_state:
        st.session_state[retry_key] = 0

    try:
        with loading_spinner(loading_type):
            result = func()

        # 성공 시 재시도 카운트 초기화
        st.session_state[retry_key] = 0
        return result

    except Exception as e:
        st.session_state[retry_key] += 1

        if st.session_state[retry_key] < max_retries:
            def retry():
                st.session_state[retry_key] = 0

            render_retry_button(
                retry,
                f"{error_message} ({st.session_state[retry_key]}/{max_retries})",
                "다시 시도"
            )
        else:
            st.error(f"{error_message} - 최대 재시도 횟수를 초과했습니다.")
            if st.button("처음부터 다시 시도", key=f"reset_{id(func)}"):
                st.session_state[retry_key] = 0
                st.rerun()

        return None


# =============================================================================
# 빈 상태 화면
# =============================================================================

def render_empty_state(
    title: str,
    description: str,
    icon_svg: Optional[str] = None,
    action_label: Optional[str] = None,
    action_callback: Optional[Callable] = None
):
    """빈 상태 화면 렌더링

    Args:
        title: 제목
        description: 설명
        icon_svg: 아이콘 SVG
        action_label: 액션 버튼 텍스트
        action_callback: 액션 버튼 콜백
    """
    default_icon = """
    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
        <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
        <line x1="12" y1="22.08" x2="12" y2="12"/>
    </svg>
    """

    icon = icon_svg or default_icon

    empty_html = f"""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px 20px;
        text-align: center;
    ">
        <div style="margin-bottom: 24px; opacity: 0.8;">
            {icon}
        </div>
        <h3 style="
            color: #334155;
            font-size: 18px;
            font-weight: 600;
            margin: 0 0 8px 0;
        ">{title}</h3>
        <p style="
            color: #64748b;
            font-size: 14px;
            margin: 0;
            max-width: 300px;
            line-height: 1.5;
        ">{description}</p>
    </div>
    """

    st.markdown(empty_html, unsafe_allow_html=True)

    if action_label and action_callback:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(action_label, key=f"empty_action_{uuid.uuid4().hex[:8]}", type="primary"):
                action_callback()


# =============================================================================
# 작업 완료 화면
# =============================================================================

def render_completion_screen(
    title: str = "완료되었습니다",
    description: str = "",
    show_confetti: bool = True,
    next_action_label: Optional[str] = None,
    next_action_callback: Optional[Callable] = None
):
    """작업 완료 화면 렌더링"""
    confetti_animation = """
    <style>
    @keyframes fr-confetti-fall {
        0% { transform: translateY(-100vh) rotate(0deg); opacity: 1; }
        100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
    }
    .fr-confetti {
        position: fixed;
        top: 0;
        width: 10px;
        height: 10px;
        animation: fr-confetti-fall 3s ease-in-out forwards;
        z-index: 9999;
        pointer-events: none;
    }
    </style>
    <script>
    (function() {
        const colors = ['#2563eb', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'fr-confetti';
            confetti.style.left = Math.random() * 100 + 'vw';
            confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.animationDelay = Math.random() * 2 + 's';
            document.body.appendChild(confetti);
            setTimeout(() => confetti.remove(), 5000);
        }
    })();
    </script>
    """ if show_confetti else ""

    completion_html = f"""
    {confetti_animation}
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px 20px;
        text-align: center;
    ">
        <div style="
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 24px;
        ">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
        </div>
        <h2 style="
            color: #065f46;
            font-size: 24px;
            font-weight: 700;
            margin: 0 0 12px 0;
        ">{title}</h2>
        <p style="
            color: #047857;
            font-size: 16px;
            margin: 0;
            max-width: 400px;
            line-height: 1.5;
        ">{description}</p>
    </div>
    """

    st.markdown(completion_html, unsafe_allow_html=True)

    if next_action_label and next_action_callback:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(next_action_label, key="completion_next", type="primary"):
                next_action_callback()


# =============================================================================
# 확인 다이얼로그
# =============================================================================

def confirm_dialog(
    title: str,
    message: str,
    confirm_label: str = "확인",
    cancel_label: str = "취소",
    danger: bool = False,
    dialog_key: str = "confirm_dialog"
) -> Optional[bool]:
    """확인 다이얼로그

    Args:
        title: 제목
        message: 메시지
        confirm_label: 확인 버튼 텍스트
        cancel_label: 취소 버튼 텍스트
        danger: 위험 동작 여부 (빨간색 버튼)
        dialog_key: 다이얼로그 키

    Returns:
        True (확인), False (취소), None (대기 중)
    """
    result_key = f"{dialog_key}_result"

    # 결과 확인
    if result_key in st.session_state:
        result = st.session_state[result_key]
        del st.session_state[result_key]
        return result

    # 다이얼로그 렌더링
    with st.container():
        st.markdown(f"""
        <div style="
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 24px;
            margin: 16px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        ">
            <h4 style="margin: 0 0 12px 0; color: #1e293b;">{title}</h4>
            <p style="margin: 0 0 20px 0; color: #64748b;">{message}</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button(
                cancel_label,
                key=f"{dialog_key}_cancel",
                type="secondary"
            ):
                st.session_state[result_key] = False
                st.rerun()

        with col2:
            button_type = "primary" if not danger else "primary"
            if st.button(
                confirm_label,
                key=f"{dialog_key}_confirm",
                type=button_type
            ):
                st.session_state[result_key] = True
                st.rerun()

    return None


# =============================================================================
# 단계 표시기
# =============================================================================

def render_step_indicator(
    steps: List[str],
    current_step: int,
    completed_steps: Optional[List[int]] = None
):
    """단계 표시기 렌더링

    Args:
        steps: 단계 목록
        current_step: 현재 단계 (0-indexed)
        completed_steps: 완료된 단계 목록
    """
    completed_steps = completed_steps or []

    steps_html = '<div style="display: flex; justify-content: space-between; align-items: center; margin: 24px 0;">'

    for i, step in enumerate(steps):
        # 상태 결정
        if i < current_step or i in completed_steps:
            status = "completed"
            bg_color = "#059669"
            text_color = "#065f46"
            border_color = "#059669"
        elif i == current_step:
            status = "current"
            bg_color = "#2563eb"
            text_color = "#1e40af"
            border_color = "#2563eb"
        else:
            status = "pending"
            bg_color = "#e2e8f0"
            text_color = "#94a3b8"
            border_color = "#e2e8f0"

        # 체크 아이콘
        check_icon = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>' if status == "completed" else str(i + 1)

        step_html = f"""
        <div style="display: flex; flex-direction: column; align-items: center; flex: 1;">
            <div style="
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background: {bg_color};
                color: {'white' if status != 'pending' else text_color};
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                font-size: 14px;
                margin-bottom: 8px;
            ">{check_icon}</div>
            <span style="
                font-size: 13px;
                color: {text_color};
                text-align: center;
                font-weight: {'600' if status == 'current' else '400'};
            ">{step}</span>
        </div>
        """

        # 연결선 (마지막 제외)
        if i < len(steps) - 1:
            line_color = "#059669" if i < current_step else "#e2e8f0"
            step_html += f"""
            <div style="
                flex: 1;
                height: 2px;
                background: {line_color};
                margin: 0 8px;
                margin-bottom: 28px;
            "></div>
            """

        steps_html += step_html

    steps_html += '</div>'

    st.markdown(steps_html, unsafe_allow_html=True)

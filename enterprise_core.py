# enterprise_core.py
# 대기업 수준 시스템 통합 코어
# FlyReady Lab - Enterprise Core Module
# Stage 2 모든 기능의 중앙 진입점

import streamlit as st
from typing import Optional

# =============================================================================
# Stage 1 모듈 Import
# =============================================================================

try:
    from ui_config import COLORS, NAV_MENU, get_sidebar_css
    UI_CONFIG_AVAILABLE = True
except ImportError:
    UI_CONFIG_AVAILABLE = False

try:
    from ui_components import get_icon, get_interaction_css, get_loading_css
    UI_COMPONENTS_AVAILABLE = True
except ImportError:
    UI_COMPONENTS_AVAILABLE = False

try:
    from onboarding import show_onboarding, should_show_onboarding
    ONBOARDING_AVAILABLE = True
except ImportError:
    ONBOARDING_AVAILABLE = False

# =============================================================================
# Stage 2 모듈 Import
# =============================================================================

try:
    from error_handler import (
        ErrorType, ErrorSeverity, AppError,
        show_error, show_warning, show_info, show_success,
        with_error_handling, with_retry,
        get_circuit_breaker, safe_api_call,
        init_error_state, render_error_report_button
    )
    ERROR_HANDLER_AVAILABLE = True
except ImportError:
    ERROR_HANDLER_AVAILABLE = False

try:
    from accessibility import (
        init_accessibility, get_accessibility_css,
        render_skip_links, render_main_content_start,
        aria_hidden_icon, render_accessible_button,
        render_live_region, accessible_table, accessible_progress,
        check_color_contrast, ACCESSIBLE_COLORS
    )
    ACCESSIBILITY_AVAILABLE = True
except ImportError:
    ACCESSIBILITY_AVAILABLE = False

try:
    from security_utils import (
        escape_html, sanitize_html, sanitize_attribute,
        create_safe_html, safe_css,
        validate_text_input, validate_email, validate_url, validate_file_upload,
        generate_csrf_token, validate_csrf_token, render_csrf_field,
        SecureAuth, render_admin_login,
        RateLimiter, api_rate_limiter, upload_rate_limiter, rate_limited,
        render_security_headers, log_security_event, mask_sensitive,
        safe_render_markdown
    )
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

try:
    from performance_utils import (
        LRUCache, get_api_cache, get_data_cache,
        paginate, render_pagination_controls, PaginationState,
        virtual_list, debounce, throttle,
        batch_process, LazyLoader, lazy_load,
        PerformanceMetrics, get_metrics, timed_operation,
        optimize_dataframe, cleanup_session,
        render_performance_dashboard
    )
    PERFORMANCE_AVAILABLE = True
except ImportError:
    PERFORMANCE_AVAILABLE = False

try:
    from feedback_ux import (
        LoadingType, LOADING_MESSAGES, get_loading_message,
        loading_spinner, render_loading_overlay,
        render_skeleton, render_card_skeleton,
        ProgressState, render_progress_indicator, create_progress_tracker,
        ToastType, show_toast, toast_success, toast_error, toast_warning, toast_info,
        render_retry_button, with_retry_ui,
        render_empty_state, render_completion_screen,
        confirm_dialog, render_step_indicator
    )
    FEEDBACK_UX_AVAILABLE = True
except ImportError:
    FEEDBACK_UX_AVAILABLE = False

try:
    from responsive_design import (
        BREAKPOINTS, Breakpoint,
        get_responsive_css, get_viewport_meta,
        responsive_columns, render_responsive_grid,
        render_bottom_navigation, DEFAULT_BOTTOM_NAV,
        render_responsive_card, render_responsive_table,
        init_responsive_design, inject_device_detection
    )
    RESPONSIVE_AVAILABLE = True
except ImportError:
    RESPONSIVE_AVAILABLE = False


# =============================================================================
# 시스템 상태 확인
# =============================================================================

def get_system_status() -> dict:
    """시스템 모듈 상태 확인"""
    return {
        "stage1": {
            "ui_config": UI_CONFIG_AVAILABLE,
            "ui_components": UI_COMPONENTS_AVAILABLE,
            "onboarding": ONBOARDING_AVAILABLE,
        },
        "stage2": {
            "error_handler": ERROR_HANDLER_AVAILABLE,
            "accessibility": ACCESSIBILITY_AVAILABLE,
            "security": SECURITY_AVAILABLE,
            "performance": PERFORMANCE_AVAILABLE,
            "feedback_ux": FEEDBACK_UX_AVAILABLE,
            "responsive": RESPONSIVE_AVAILABLE,
        }
    }


def render_system_status():
    """시스템 상태 렌더링 (관리자용)"""
    status = get_system_status()

    st.markdown("### 시스템 모듈 상태")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Stage 1 모듈**")
        for module, available in status["stage1"].items():
            icon = "OK" if available else "X"
            color = "green" if available else "red"
            st.markdown(f":{color}[{icon}] {module}")

    with col2:
        st.markdown("**Stage 2 모듈**")
        for module, available in status["stage2"].items():
            icon = "OK" if available else "X"
            color = "green" if available else "red"
            st.markdown(f":{color}[{icon}] {module}")

    # 전체 상태
    all_available = all(status["stage1"].values()) and all(status["stage2"].values())
    if all_available:
        st.success("모든 모듈이 정상 작동 중입니다.")
    else:
        st.warning("일부 모듈이 비활성화되었습니다.")


# =============================================================================
# 통합 초기화 함수
# =============================================================================

def init_enterprise_features(
    enable_accessibility: bool = True,
    enable_responsive: bool = True,
    enable_security: bool = True,
    enable_performance: bool = True,
    enable_onboarding: bool = True,
    page_title: Optional[str] = None
):
    """대기업 수준 기능 통합 초기화

    Args:
        enable_accessibility: 접근성 기능 활성화
        enable_responsive: 반응형 디자인 활성화
        enable_security: 보안 기능 활성화
        enable_performance: 성능 최적화 활성화
        enable_onboarding: 온보딩 시스템 활성화
        page_title: 페이지 제목 (브라우저 탭)

    Usage:
        # 페이지 시작 부분에서 호출
        from enterprise_core import init_enterprise_features
        init_enterprise_features()
    """
    # 세션 상태 초기화
    if "enterprise_initialized" not in st.session_state:
        st.session_state.enterprise_initialized = False

    # 이미 초기화되었으면 스킵
    if st.session_state.enterprise_initialized:
        return

    # Stage 1: UI 컴포넌트
    if UI_COMPONENTS_AVAILABLE:
        st.markdown(get_interaction_css(), unsafe_allow_html=True)
        st.markdown(get_loading_css(), unsafe_allow_html=True)

    # Stage 2: 접근성
    if enable_accessibility and ACCESSIBILITY_AVAILABLE:
        init_accessibility()

    # Stage 2: 반응형 디자인
    if enable_responsive and RESPONSIVE_AVAILABLE:
        init_responsive_design()
        inject_device_detection()

    # Stage 2: 보안
    if enable_security and SECURITY_AVAILABLE:
        render_security_headers()
        SecureAuth.init_session()

    # Stage 2: 성능
    if enable_performance and PERFORMANCE_AVAILABLE:
        cleanup_session()

    # Stage 2: 에러 핸들링
    if ERROR_HANDLER_AVAILABLE:
        init_error_state()

    # 온보딩 (첫 방문 시)
    if enable_onboarding and ONBOARDING_AVAILABLE:
        if should_show_onboarding():
            show_onboarding()

    st.session_state.enterprise_initialized = True


def reset_enterprise_init():
    """초기화 상태 리셋 (디버그용)"""
    st.session_state.enterprise_initialized = False


# =============================================================================
# 래퍼 함수들 (폴백 포함)
# =============================================================================

def safe_show_error(error, **kwargs):
    """안전한 에러 표시"""
    if ERROR_HANDLER_AVAILABLE:
        show_error(error, **kwargs)
    else:
        st.error(str(error))


def safe_show_success(message, title=None):
    """안전한 성공 메시지"""
    if ERROR_HANDLER_AVAILABLE:
        show_success(message, title)
    else:
        st.success(message)


def safe_show_warning(message, action=None):
    """안전한 경고 메시지"""
    if ERROR_HANDLER_AVAILABLE:
        show_warning(message, action)
    else:
        st.warning(message)


def safe_show_info(message, title=None):
    """안전한 정보 메시지"""
    if ERROR_HANDLER_AVAILABLE:
        show_info(message, title)
    else:
        st.info(message)


def safe_toast(message, toast_type="info"):
    """안전한 토스트 알림"""
    if FEEDBACK_UX_AVAILABLE:
        if toast_type == "success":
            toast_success(message)
        elif toast_type == "error":
            toast_error(message)
        elif toast_type == "warning":
            toast_warning(message)
        else:
            toast_info(message)
    else:
        st.info(message)


def safe_loading_spinner(loading_type=None, message=None):
    """안전한 로딩 스피너"""
    if FEEDBACK_UX_AVAILABLE and loading_type:
        return loading_spinner(loading_type, message)
    else:
        return st.spinner(message or "처리 중...")


def safe_paginate(items, page_size=20, state_key="pagination"):
    """안전한 페이지네이션"""
    if PERFORMANCE_AVAILABLE:
        return paginate(items, page_size, state_key)
    else:
        # 폴백: 단순 슬라이싱
        class SimplePagination:
            def __init__(self, total):
                self.current_page = 1
                self.total_pages = 1
                self.total_items = total
                self.has_prev = False
                self.has_next = False

        return items[:page_size], SimplePagination(len(items))


def safe_validate_input(text, min_length=0, max_length=10000):
    """안전한 입력 검증"""
    if SECURITY_AVAILABLE:
        return validate_text_input(text, min_length, max_length)
    else:
        # 폴백: 기본 검증
        if not text:
            return True, "", None
        cleaned = str(text).strip()
        if len(cleaned) < min_length:
            return False, cleaned, f"최소 {min_length}자 이상"
        if len(cleaned) > max_length:
            return False, cleaned[:max_length], f"최대 {max_length}자"
        return True, cleaned, None


def safe_escape_html(text):
    """안전한 HTML 이스케이프"""
    if SECURITY_AVAILABLE:
        return escape_html(text)
    else:
        import html
        return html.escape(str(text)) if text else ""


# =============================================================================
# 관리자 대시보드 통합
# =============================================================================

def render_admin_dashboard():
    """통합 관리자 대시보드"""
    st.title("관리자 대시보드")

    tabs = st.tabs(["시스템 상태", "성능", "보안", "에러 로그"])

    with tabs[0]:
        render_system_status()

    with tabs[1]:
        if PERFORMANCE_AVAILABLE:
            render_performance_dashboard()
        else:
            st.info("성능 모듈이 비활성화되었습니다.")

    with tabs[2]:
        if SECURITY_AVAILABLE:
            st.markdown("### 보안 설정")
            st.info("보안 모듈 활성화됨")

            # 레이트 리미터 상태
            st.markdown("**API 레이트 리미터**")
            st.write(f"설정: {api_rate_limiter.max_requests}회/{api_rate_limiter.window_seconds}초")

            st.markdown("**업로드 레이트 리미터**")
            st.write(f"설정: {upload_rate_limiter.max_requests}회/{upload_rate_limiter.window_seconds}초")
        else:
            st.info("보안 모듈이 비활성화되었습니다.")

    with tabs[3]:
        if ERROR_HANDLER_AVAILABLE:
            render_error_report_button()
        else:
            st.info("에러 핸들러 모듈이 비활성화되었습니다.")


# =============================================================================
# 버전 정보
# =============================================================================

VERSION = "2.0.0"
STAGE = "Stage 2"

def get_version_info() -> dict:
    """버전 정보 반환"""
    return {
        "version": VERSION,
        "stage": STAGE,
        "modules": get_system_status()
    }

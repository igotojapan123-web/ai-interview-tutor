# page_template.py
# 대기업 수준 페이지 템플릿
# FlyReady Lab - Enterprise Page Template
#
# 이 파일은 새 페이지 생성 또는 기존 페이지 업그레이드 시 참고하세요.
# Stage 1 + Stage 2 모든 기능이 통합되어 있습니다.

import os
import sys
import streamlit as st

# 경로 설정 (pages/ 폴더에서 실행 시)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =============================================================================
# Stage 1 & 2 모듈 Import
# =============================================================================

# 사이드바 (자동으로 Stage 2 기능 적용)
from sidebar_common import render_sidebar

# 공용 유틸리티 (중복 코드 방지)
from shared_utils import (
    get_api_key,
    load_json, save_json,
    init_session_state,
    sanitize_text,
    format_datetime,
    log_user_action,
    get_cached,
)

# 상수 및 메시지
from constants import (
    APP_NAME,
    Messages,
    ButtonLabels,
    COLORS,
    Limits,
)

# 에러 핸들링 (필요시)
try:
    from error_handler import (
        show_error, show_warning, show_info, show_success,
        with_error_handling, with_retry,
        safe_api_call,
    )
    ERROR_HANDLER_AVAILABLE = True
except ImportError:
    ERROR_HANDLER_AVAILABLE = False
    # 폴백 함수
    def show_error(e, **kwargs): st.error(str(e))
    def show_warning(msg, action=None): st.warning(msg)
    def show_info(msg, title=None): st.info(msg)
    def show_success(msg, title=None): st.success(msg)

# 사용자 피드백 UX (필요시)
try:
    from feedback_ux import (
        loading_spinner, LoadingType,
        render_skeleton, render_card_skeleton,
        create_progress_tracker,
        toast_success, toast_error, toast_warning, toast_info,
        render_empty_state, render_completion_screen,
        render_step_indicator, confirm_dialog,
    )
    FEEDBACK_UX_AVAILABLE = True
except ImportError:
    FEEDBACK_UX_AVAILABLE = False

# 성능 최적화 (필요시)
try:
    from performance_utils import (
        paginate, render_pagination_controls,
        timed_operation, get_metrics,
    )
    PERFORMANCE_AVAILABLE = True
except ImportError:
    PERFORMANCE_AVAILABLE = False

# 보안 유틸리티 (필요시)
try:
    from security_utils import (
        escape_html, sanitize_html,
        validate_text_input, validate_file_upload,
    )
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False


# =============================================================================
# 페이지 설정
# =============================================================================

# 현재 페이지 이름 (사이드바 하이라이트용)
CURRENT_PAGE = "페이지이름"

st.set_page_config(
    page_title=f"{CURRENT_PAGE} | {APP_NAME}",
    page_icon="✈️",
    layout="wide"
)

# 사이드바 렌더링 (Stage 2 기능 자동 적용)
render_sidebar(CURRENT_PAGE)


# =============================================================================
# 세션 상태 초기화
# =============================================================================

def init_page_state():
    """페이지 세션 상태 초기화"""
    init_session_state({
        f"{CURRENT_PAGE}_initialized": False,
        f"{CURRENT_PAGE}_data": None,
        f"{CURRENT_PAGE}_step": 0,
        # 페이지별 추가 상태...
    })


init_page_state()


# =============================================================================
# 데이터 로딩 함수 (캐싱 적용)
# =============================================================================

@st.cache_data(ttl=300)
def load_page_data():
    """페이지 데이터 로드 (5분 캐시)"""
    # 실제 데이터 로딩 로직
    return {"items": [], "total": 0}


def load_data_with_feedback():
    """피드백과 함께 데이터 로드"""
    if FEEDBACK_UX_AVAILABLE:
        with loading_spinner(LoadingType.NETWORK, "데이터를 불러오는 중..."):
            return load_page_data()
    else:
        with st.spinner("데이터를 불러오는 중..."):
            return load_page_data()


# =============================================================================
# API 호출 함수 (에러 핸들링 적용)
# =============================================================================

def call_api_with_handling(prompt: str):
    """에러 핸들링이 적용된 API 호출"""
    if ERROR_HANDLER_AVAILABLE:
        # 에러 핸들링 데코레이터 사용
        @with_error_handling(show_ui=True, default_return=None)
        @with_retry(max_retries=3, delay=1.0)
        def _call():
            # 실제 API 호출 로직
            api_key = get_api_key()
            if not api_key:
                raise ValueError("API 키가 설정되지 않았습니다.")

            # API 호출...
            return {"result": "success"}

        return _call()
    else:
        # 폴백 - 기본 에러 처리
        try:
            api_key = get_api_key()
            if not api_key:
                st.error("API 키가 설정되지 않았습니다.")
                return None
            return {"result": "success"}
        except Exception as e:
            st.error(f"API 호출 실패: {e}")
            return None


# =============================================================================
# 입력 검증 함수
# =============================================================================

def validate_user_input(text: str) -> tuple[bool, str, str]:
    """사용자 입력 검증

    Returns:
        (유효여부, 정제된텍스트, 에러메시지)
    """
    if SECURITY_AVAILABLE:
        return validate_text_input(
            text,
            min_length=10,
            max_length=Limits.MAX_INPUT_LENGTH,
            allow_empty=False
        )
    else:
        # 폴백 검증
        text = text.strip() if text else ""
        if not text:
            return False, "", "내용을 입력해 주세요."
        if len(text) < 10:
            return False, text, "최소 10자 이상 입력해 주세요."
        return True, text, ""


# =============================================================================
# 메인 UI
# =============================================================================

def render_header():
    """페이지 헤더 렌더링"""
    st.title(CURRENT_PAGE)
    st.markdown("페이지 설명을 여기에 작성합니다.")


def render_main_content():
    """메인 콘텐츠 렌더링"""

    # 데이터 로드
    data = load_data_with_feedback()

    if not data or not data.get("items"):
        # 빈 상태 화면
        if FEEDBACK_UX_AVAILABLE:
            render_empty_state(
                title="아직 데이터가 없습니다",
                description="새로운 항목을 추가해 보세요.",
                action_label="항목 추가",
                action_callback=lambda: st.session_state.update({"show_add_form": True})
            )
        else:
            st.info("아직 데이터가 없습니다.")
        return

    # 페이지네이션 적용
    if PERFORMANCE_AVAILABLE:
        items, pagination = paginate(data["items"], page_size=10)
        render_pagination_controls(pagination)
    else:
        items = data["items"][:10]

    # 아이템 렌더링
    for item in items:
        render_item(item)


def render_item(item):
    """개별 아이템 렌더링"""
    with st.container():
        st.markdown(f"""
        <div style="
            background: white;
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
        ">
            <h4 style="margin: 0 0 8px 0; color: {COLORS['text_primary']};">
                {escape_html(item.get('title', '')) if SECURITY_AVAILABLE else item.get('title', '')}
            </h4>
            <p style="margin: 0; color: {COLORS['text_secondary']};">
                {escape_html(item.get('description', '')) if SECURITY_AVAILABLE else item.get('description', '')}
            </p>
        </div>
        """, unsafe_allow_html=True)


def render_form():
    """입력 폼 렌더링"""
    st.subheader("새 항목 추가")

    with st.form("add_item_form"):
        title = st.text_input("제목", placeholder=Messages.PLACEHOLDER_TEXT)
        description = st.text_area("설명", placeholder=Messages.PLACEHOLDER_TEXT)

        submitted = st.form_submit_button(ButtonLabels.SUBMIT)

        if submitted:
            # 입력 검증
            is_valid, cleaned_title, error = validate_user_input(title)

            if not is_valid:
                if ERROR_HANDLER_AVAILABLE:
                    show_warning(error)
                else:
                    st.warning(error)
                return

            # 저장 처리
            handle_save(cleaned_title, description)


def handle_save(title: str, description: str):
    """저장 처리"""
    if FEEDBACK_UX_AVAILABLE:
        with loading_spinner(LoadingType.SAVE, Messages.LOADING_SAVE):
            # 저장 로직...
            success = True

        if success:
            toast_success(Messages.SUCCESS_SAVE)
            log_user_action("item_added", {"title": title})
        else:
            toast_error(Messages.ERROR_GENERAL)
    else:
        with st.spinner(Messages.LOADING_SAVE):
            success = True

        if success:
            st.success(Messages.SUCCESS_SAVE)
        else:
            st.error(Messages.ERROR_GENERAL)


def render_sidebar_content():
    """사이드바 추가 콘텐츠 (필요시)"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 도움말")
        st.markdown("이 페이지에서는...")


# =============================================================================
# 단계별 진행 UI (필요시)
# =============================================================================

def render_multi_step_ui():
    """다단계 진행 UI 예시"""
    steps = ["설정", "입력", "확인", "완료"]
    current_step = st.session_state.get(f"{CURRENT_PAGE}_step", 0)

    # 단계 표시기
    if FEEDBACK_UX_AVAILABLE:
        render_step_indicator(steps, current_step)

    # 단계별 콘텐츠
    if current_step == 0:
        render_step_setup()
    elif current_step == 1:
        render_step_input()
    elif current_step == 2:
        render_step_confirm()
    elif current_step == 3:
        render_step_complete()


def render_step_setup():
    st.subheader("1단계: 설정")
    # 설정 UI...
    if st.button(ButtonLabels.NEXT):
        st.session_state[f"{CURRENT_PAGE}_step"] = 1
        st.rerun()


def render_step_input():
    st.subheader("2단계: 입력")
    # 입력 UI...
    col1, col2 = st.columns(2)
    with col1:
        if st.button(ButtonLabels.PREV):
            st.session_state[f"{CURRENT_PAGE}_step"] = 0
            st.rerun()
    with col2:
        if st.button(ButtonLabels.NEXT):
            st.session_state[f"{CURRENT_PAGE}_step"] = 2
            st.rerun()


def render_step_confirm():
    st.subheader("3단계: 확인")
    # 확인 UI...
    col1, col2 = st.columns(2)
    with col1:
        if st.button(ButtonLabels.PREV):
            st.session_state[f"{CURRENT_PAGE}_step"] = 1
            st.rerun()
    with col2:
        if st.button(ButtonLabels.SUBMIT):
            st.session_state[f"{CURRENT_PAGE}_step"] = 3
            st.rerun()


def render_step_complete():
    if FEEDBACK_UX_AVAILABLE:
        render_completion_screen(
            title="완료되었습니다!",
            description="모든 단계가 성공적으로 완료되었습니다.",
            next_action_label="처음으로",
            next_action_callback=lambda: st.session_state.update({f"{CURRENT_PAGE}_step": 0})
        )
    else:
        st.success("완료되었습니다!")
        if st.button("처음으로"):
            st.session_state[f"{CURRENT_PAGE}_step"] = 0
            st.rerun()


# =============================================================================
# 메인 실행
# =============================================================================

def main():
    """메인 함수"""
    render_header()

    # 탭 구조 예시
    tab1, tab2, tab3 = st.tabs(["목록", "추가", "설정"])

    with tab1:
        render_main_content()

    with tab2:
        render_form()

    with tab3:
        st.subheader("설정")
        st.info("설정 옵션을 여기에 추가합니다.")


# 실행
if __name__ == "__main__":
    main()
else:
    main()

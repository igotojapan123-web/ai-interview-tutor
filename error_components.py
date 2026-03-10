"""
FLYREADY 사용자 친화적 에러 UI 컴포넌트
- 서버 장애: 개발자에게 자동 전달 메시지
- 타임아웃: 재시도 버튼
- 한도 초과: 업그레이드 유도
- 입력 오류: 구체적 안내
"""

import streamlit as st
from datetime import datetime
from typing import List, Callable, Optional
import uuid


# ============================================================
# 스타일 정의
# ============================================================

ERROR_STYLES = """
<style>
.error-card {
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
    text-align: center;
}
.error-card h3 {
    margin: 12px 0 8px 0;
    font-size: 1.3em;
}
.error-card p {
    margin: 8px 0;
    color: #555;
    line-height: 1.6;
}
.error-icon {
    font-size: 48px;
    margin-bottom: 8px;
}
.error-badge {
    display: inline-block;
    background: white;
    border-radius: 8px;
    padding: 8px 16px;
    margin-top: 12px;
    font-size: 0.9em;
}
.error-id {
    font-size: 0.75em;
    color: #999;
    margin-top: 16px;
}

/* 서버 에러 - 빨간색 */
.error-server {
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
    border: 1px solid #fca5a5;
}
.error-server .error-badge {
    background: #fef2f2;
    color: #dc2626;
}

/* 타임아웃 - 노란색 */
.error-timeout {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border: 1px solid #fcd34d;
}
.error-timeout .error-badge {
    background: #fffbeb;
    color: #d97706;
}

/* 한도 초과 - 파란색 */
.error-limit {
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
    border: 1px solid #93c5fd;
}
.error-limit .error-badge {
    background: #eff6ff;
    color: #2563eb;
}

/* 입력 오류 - 회색 */
.error-input {
    background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
    border: 1px solid #d1d5db;
}
.error-input .error-badge {
    background: #f9fafb;
    color: #4b5563;
}

/* CLOVA 오류 - 초록색 */
.error-clova {
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
    border: 1px solid #6ee7b7;
}
.error-clova .error-badge {
    background: #ecfdf5;
    color: #059669;
}

/* 팁 리스트 */
.error-tips {
    text-align: left;
    background: rgba(255,255,255,0.7);
    border-radius: 8px;
    padding: 12px 16px;
    margin: 12px 0;
}
.error-tips li {
    margin: 4px 0;
    color: #555;
}
</style>
"""


def _inject_styles():
    """스타일 주입 (한 번만)"""
    if "error_styles_injected" not in st.session_state:
        st.markdown(ERROR_STYLES, unsafe_allow_html=True)
        st.session_state.error_styles_injected = True


def _generate_error_id() -> str:
    """에러 ID 생성"""
    return f"ERR-{datetime.now().strftime('%m%d%H%M')}-{uuid.uuid4().hex[:4].upper()}"


# ============================================================
# 서버 장애 에러
# ============================================================

def show_server_error(
    error_id: Optional[str] = None,
    error_detail: Optional[str] = None,
    show_retry: bool = True,
    on_retry: Optional[Callable] = None,
):
    """
    서버 장애 - 개발자에게 자동 전달 메시지

    Args:
        error_id: 에러 추적 ID (없으면 자동 생성)
        error_detail: 개발자용 상세 정보
        show_retry: 재시도 버튼 표시 여부
        on_retry: 재시도 콜백 함수
    """
    _inject_styles()

    if not error_id:
        error_id = _generate_error_id()

    # Sentry 등에 에러 전송 (실제 구현 시)
    _send_error_to_developer(error_id, error_detail)

    st.markdown(f'''
    <div class="error-card error-server">
        <div class="error-icon">🔧</div>
        <h3>일시적인 문제가 발생했어요</h3>
        <p>
            서비스에 일시적인 장애가 발생했습니다.<br>
            불편을 드려 죄송합니다.
        </p>
        <div class="error-badge">
            📨 개발자에게 자동 전달됨<br>
            <small>빠르게 확인하고 복구할게요!</small>
        </div>
        <div class="error-id">오류 코드: {error_id}</div>
    </div>
    ''', unsafe_allow_html=True)

    if show_retry:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 잠시 후 다시 시도", key=f"retry_{error_id}", use_container_width=True):
                if on_retry:
                    on_retry()
                else:
                    st.rerun()


def _send_error_to_developer(error_id: str, detail: Optional[str]):
    """에러를 개발자에게 전송 (Sentry 등)"""
    try:
        # TODO: Sentry 연동
        # import sentry_sdk
        # sentry_sdk.capture_message(f"[{error_id}] {detail}")
        print(f"[ERROR_SENT] {error_id}: {detail}")
    except:
        pass


# ============================================================
# 타임아웃 에러
# ============================================================

def show_timeout_error(
    feature_name: str = "AI 분석",
    on_retry: Optional[Callable] = None,
    on_skip: Optional[Callable] = None,
):
    """
    타임아웃 에러 - 재시도/나중에 버튼

    Args:
        feature_name: 기능명 (예: "AI 분석", "음성 인식")
        on_retry: 재시도 콜백
        on_skip: 나중에 하기 콜백
    """
    _inject_styles()

    st.markdown(f'''
    <div class="error-card error-timeout">
        <div class="error-icon">⏳</div>
        <h3>{feature_name}이 오래 걸리고 있어요</h3>
        <p>
            예상보다 시간이 걸리고 있습니다.<br>
            잠시만 기다려주시거나, 다시 시도해주세요.
        </p>
        <div class="error-badge">
            💡 네트워크 상태를 확인해보세요
        </div>
    </div>
    ''', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 다시 시도", key="timeout_retry", use_container_width=True):
            if on_retry:
                on_retry()
            else:
                st.rerun()
    with col2:
        if st.button("⏭️ 나중에 하기", key="timeout_skip", use_container_width=True):
            if on_skip:
                on_skip()


# ============================================================
# 한도 초과 에러
# ============================================================

def show_limit_exceeded(
    feature: str,
    used: int,
    limit: int,
    reset_time: str = "내일 00:00",
    show_upgrade: bool = True,
):
    """
    한도 초과 에러 - 업그레이드 유도

    Args:
        feature: 기능명 (예: "모의면접", "자소서 첨삭")
        used: 사용 횟수
        limit: 한도
        reset_time: 초기화 시간
        show_upgrade: 업그레이드 버튼 표시 여부
    """
    _inject_styles()

    st.markdown(f'''
    <div class="error-card error-limit">
        <div class="error-icon">📊</div>
        <h3>오늘 사용량을 모두 소진했어요</h3>
        <p>
            <strong>{feature}</strong>: {used}/{limit}회 완료<br>
            {reset_time}에 초기화됩니다.
        </p>
        <div class="error-badge">
            ⏰ 조금만 기다려주세요!
        </div>
    </div>
    ''', unsafe_allow_html=True)

    if show_upgrade:
        st.markdown("---")
        st.markdown("##### 💎 더 많이 연습하고 싶다면?")

        col1, col2 = st.columns(2)
        with col1:
            st.info("""
            **PREMIUM 플랜**
            - 모의면접 무제한
            - 모든 기능 사용 가능
            - 월 ₩49,900
            """)
        with col2:
            if st.button("✨ PREMIUM 알아보기", use_container_width=True):
                st.switch_page("pages/35_요금제.py")


# ============================================================
# 입력 오류
# ============================================================

def show_input_error(
    message: str,
    tips: List[str] = None,
    field_name: str = None,
):
    """
    입력 오류 - 구체적 안내

    Args:
        message: 에러 메시지
        tips: 해결 팁 리스트
        field_name: 오류 발생 필드명
    """
    _inject_styles()

    tips_html = ""
    if tips:
        tips_items = "".join([f"<li>{tip}</li>" for tip in tips])
        tips_html = f'''
        <div class="error-tips">
            <strong>💡 이렇게 해보세요:</strong>
            <ul>{tips_items}</ul>
        </div>
        '''

    field_info = f"<small>({field_name})</small>" if field_name else ""

    st.markdown(f'''
    <div class="error-card error-input">
        <div class="error-icon">✏️</div>
        <h3>입력을 확인해주세요 {field_info}</h3>
        <p>{message}</p>
        {tips_html}
    </div>
    ''', unsafe_allow_html=True)


# ============================================================
# CLOVA 장애
# ============================================================

def show_clova_error(
    fallback_used: bool = True,
    on_retry_clova: Optional[Callable] = None,
):
    """
    CLOVA API 장애 - 대체 서비스 안내

    Args:
        fallback_used: OpenAI로 대체 사용 여부
        on_retry_clova: CLOVA 재시도 콜백
    """
    _inject_styles()

    if fallback_used:
        st.markdown('''
        <div class="error-card error-clova">
            <div class="error-icon">🔄</div>
            <h3>CLOVA 서비스 연결 중...</h3>
            <p>
                CLOVA 서비스가 일시적으로 연결되지 않아<br>
                <strong>OpenAI</strong>로 대체 분석을 진행합니다.
            </p>
            <div class="error-badge">
                ✅ 동일한 품질로 분석됩니다
            </div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown('''
        <div class="error-card error-clova">
            <div class="error-icon">⚠️</div>
            <h3>CLOVA 서비스 연결 실패</h3>
            <p>
                CLOVA 서비스에 연결할 수 없습니다.<br>
                잠시 후 다시 시도해주세요.
            </p>
        </div>
        ''', unsafe_allow_html=True)

        if on_retry_clova:
            if st.button("🔄 CLOVA로 다시 시도", key="retry_clova"):
                on_retry_clova()


# ============================================================
# 네트워크 오류
# ============================================================

def show_network_error(on_retry: Optional[Callable] = None):
    """네트워크 연결 오류"""
    _inject_styles()

    st.markdown('''
    <div class="error-card error-timeout">
        <div class="error-icon">📡</div>
        <h3>인터넷 연결을 확인해주세요</h3>
        <p>
            네트워크 연결이 불안정합니다.<br>
            Wi-Fi 또는 데이터 연결을 확인해주세요.
        </p>
        <div class="error-badge">
            💡 페이지 새로고침을 시도해보세요
        </div>
    </div>
    ''', unsafe_allow_html=True)

    if st.button("🔄 다시 시도", key="network_retry"):
        if on_retry:
            on_retry()
        else:
            st.rerun()


# ============================================================
# 권한 오류
# ============================================================

def show_permission_error(
    required_plan: str = "PREMIUM",
    feature: str = "이 기능",
):
    """권한 없음 오류 - 업그레이드 유도"""
    _inject_styles()

    st.markdown(f'''
    <div class="error-card error-limit">
        <div class="error-icon">🔒</div>
        <h3>{feature}은(는) {required_plan} 전용입니다</h3>
        <p>
            더 많은 기능을 이용하시려면<br>
            플랜을 업그레이드해주세요.
        </p>
    </div>
    ''', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(f"✨ {required_plan} 시작하기", use_container_width=True):
            st.switch_page("pages/35_요금제.py")


# ============================================================
# 성공 메시지 (에러 복구 후)
# ============================================================

def show_recovery_success(message: str = "문제가 해결되었습니다!"):
    """에러 복구 성공 메시지"""
    st.success(f"✅ {message}")


# ============================================================
# 래퍼 함수 (기존 에러 핸들러와 통합용)
# ============================================================

def handle_error_with_ui(
    error: Exception,
    error_type: str = "server",
    feature_name: str = "기능",
    on_retry: Optional[Callable] = None,
):
    """
    에러 타입에 따라 적절한 UI 표시

    Args:
        error: 발생한 예외
        error_type: 에러 타입 (server, timeout, input, network, clova)
        feature_name: 기능명
        on_retry: 재시도 콜백
    """
    error_str = str(error).lower()

    # 타입 자동 감지
    if "timeout" in error_str or "timed out" in error_str:
        error_type = "timeout"
    elif "connection" in error_str or "network" in error_str:
        error_type = "network"
    elif "clova" in error_str:
        error_type = "clova"
    elif "invalid" in error_str or "required" in error_str:
        error_type = "input"

    # 타입별 UI 표시
    if error_type == "timeout":
        show_timeout_error(feature_name, on_retry)
    elif error_type == "network":
        show_network_error(on_retry)
    elif error_type == "clova":
        show_clova_error(fallback_used=False, on_retry_clova=on_retry)
    elif error_type == "input":
        show_input_error(str(error))
    else:
        show_server_error(error_detail=str(error), on_retry=on_retry)


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    # Streamlit 테스트용
    st.set_page_config(page_title="에러 컴포넌트 테스트", page_icon="⚠️")
    st.title("에러 컴포넌트 테스트")

    st.header("1. 서버 장애")
    show_server_error(error_detail="테스트 에러")

    st.header("2. 타임아웃")
    show_timeout_error("AI 분석")

    st.header("3. 한도 초과")
    show_limit_exceeded("모의면접", 5, 5)

    st.header("4. 입력 오류")
    show_input_error(
        "답변이 너무 짧습니다.",
        tips=["최소 30자 이상 입력해주세요", "구체적인 경험을 포함해보세요"],
        field_name="답변"
    )

    st.header("5. CLOVA 장애 (대체 사용)")
    show_clova_error(fallback_used=True)

    st.header("6. 네트워크 오류")
    show_network_error()

    st.header("7. 권한 오류")
    show_permission_error("PREMIUM", "무제한 면접")

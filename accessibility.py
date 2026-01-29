# accessibility.py
# 대기업 수준 접근성 시스템
# FlyReady Lab - Enterprise Accessibility (WCAG 2.1 AA 준수)

import streamlit as st
from typing import Optional, Dict, List
import html

# =============================================================================
# WCAG 색상 대비 검증
# =============================================================================

# 색상 대비 비율 (WCAG 2.1 AA 기준)
# - 일반 텍스트: 최소 4.5:1
# - 대형 텍스트(18pt+): 최소 3:1
# - UI 컴포넌트: 최소 3:1

ACCESSIBLE_COLORS = {
    # 텍스트 색상 (배경 #ffffff 기준)
    "text_primary": "#1e293b",      # 대비 12.6:1
    "text_secondary": "#475569",    # 대비 7.5:1
    "text_muted": "#64748b",        # 대비 5.4:1

    # 링크 색상
    "link": "#2563eb",              # 대비 4.6:1
    "link_hover": "#1d4ed8",        # 대비 5.8:1

    # 상태 색상 (배경 포함)
    "success_text": "#065f46",      # 대비 7.0:1
    "success_bg": "#d1fae5",
    "warning_text": "#92400e",      # 대비 6.3:1
    "warning_bg": "#fef3c7",
    "error_text": "#991b1b",        # 대비 8.1:1
    "error_bg": "#fee2e2",
    "info_text": "#1e40af",         # 대비 8.6:1
    "info_bg": "#dbeafe",

    # 버튼 색상
    "button_primary_bg": "#2563eb",
    "button_primary_text": "#ffffff",  # 대비 4.6:1
    "button_secondary_bg": "#f1f5f9",
    "button_secondary_text": "#334155", # 대비 8.5:1

    # 포커스 표시
    "focus_ring": "#2563eb",
    "focus_ring_offset": "#ffffff",
}


# =============================================================================
# 접근성 CSS
# =============================================================================

def get_accessibility_css() -> str:
    """접근성 향상 CSS 반환"""
    return """
    <style>
    /* =================================
       스크린 리더 전용 텍스트
       ================================= */
    .sr-only {
        position: absolute !important;
        width: 1px !important;
        height: 1px !important;
        padding: 0 !important;
        margin: -1px !important;
        overflow: hidden !important;
        clip: rect(0, 0, 0, 0) !important;
        white-space: nowrap !important;
        border: 0 !important;
    }

    .sr-only-focusable:focus,
    .sr-only-focusable:active {
        position: static !important;
        width: auto !important;
        height: auto !important;
        overflow: visible !important;
        clip: auto !important;
        white-space: normal !important;
    }

    /* =================================
       포커스 스타일 (키보드 네비게이션)
       ================================= */
    *:focus {
        outline: 2px solid #2563eb !important;
        outline-offset: 2px !important;
    }

    *:focus:not(:focus-visible) {
        outline: none !important;
    }

    *:focus-visible {
        outline: 2px solid #2563eb !important;
        outline-offset: 2px !important;
        border-radius: 4px;
    }

    /* 버튼 포커스 */
    button:focus-visible,
    [role="button"]:focus-visible {
        outline: 3px solid #2563eb !important;
        outline-offset: 2px !important;
        box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.2) !important;
    }

    /* 입력 필드 포커스 */
    input:focus-visible,
    textarea:focus-visible,
    select:focus-visible {
        outline: 2px solid #2563eb !important;
        outline-offset: 0 !important;
        border-color: #2563eb !important;
    }

    /* 링크 포커스 */
    a:focus-visible {
        outline: 2px solid #2563eb !important;
        outline-offset: 2px !important;
        border-radius: 2px;
    }

    /* =================================
       건너뛰기 링크 (Skip to content)
       ================================= */
    .skip-link {
        position: fixed;
        top: -100px;
        left: 16px;
        z-index: 10000;
        padding: 12px 24px;
        background: #1e293b;
        color: #ffffff !important;
        text-decoration: none;
        font-weight: 600;
        border-radius: 0 0 8px 8px;
        transition: top 0.2s ease;
    }

    .skip-link:focus {
        top: 0;
        outline: none;
    }

    /* =================================
       키보드 네비게이션 인디케이터
       ================================= */
    .keyboard-nav-active *:focus {
        outline: 3px solid #2563eb !important;
        outline-offset: 2px !important;
    }

    /* =================================
       터치 타겟 크기 (최소 44x44px)
       ================================= */
    button,
    [role="button"],
    a,
    input[type="checkbox"],
    input[type="radio"] {
        min-height: 44px;
        min-width: 44px;
    }

    /* Streamlit 버튼 조정 */
    .stButton > button {
        min-height: 44px !important;
        padding: 10px 20px !important;
    }

    /* =================================
       텍스트 가독성
       ================================= */
    /* 최소 폰트 크기 */
    body {
        font-size: 16px;
        line-height: 1.5;
    }

    /* 단락 간격 */
    p {
        margin-bottom: 1em;
    }

    /* 제목 계층 */
    h1, h2, h3, h4, h5, h6 {
        margin-top: 1.5em;
        margin-bottom: 0.5em;
        line-height: 1.3;
    }

    /* =================================
       색상 대비 보장
       ================================= */
    /* 텍스트 */
    .text-primary { color: #1e293b !important; }
    .text-secondary { color: #475569 !important; }
    .text-muted { color: #64748b !important; }

    /* 링크 */
    a {
        color: #2563eb;
        text-decoration: underline;
    }

    a:hover {
        color: #1d4ed8;
    }

    /* =================================
       모션 감소 (Prefers Reduced Motion)
       ================================= */
    @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
        }
    }

    /* =================================
       고대비 모드 지원
       ================================= */
    @media (prefers-contrast: high) {
        * {
            border-color: currentColor !important;
        }

        button,
        [role="button"] {
            border: 2px solid currentColor !important;
        }

        a {
            text-decoration: underline !important;
        }
    }

    /* =================================
       다크 모드 대비 조정
       ================================= */
    @media (prefers-color-scheme: dark) {
        .fr-error-container,
        .fr-warning-container,
        .fr-info-container,
        .fr-success-container {
            border-width: 2px !important;
        }
    }

    /* =================================
       라이브 리전 (동적 콘텐츠 알림)
       ================================= */
    [aria-live="polite"],
    [aria-live="assertive"] {
        position: relative;
    }

    .live-region {
        position: absolute;
        left: -10000px;
        width: 1px;
        height: 1px;
        overflow: hidden;
    }

    /* =================================
       테이블 접근성
       ================================= */
    table {
        border-collapse: collapse;
        width: 100%;
    }

    th {
        background-color: #f1f5f9;
        font-weight: 600;
        text-align: left;
        padding: 12px;
    }

    td {
        padding: 12px;
        border-bottom: 1px solid #e2e8f0;
    }

    /* 줄무늬 */
    tr:nth-child(even) {
        background-color: #f8fafc;
    }

    /* 호버 */
    tr:hover {
        background-color: #f1f5f9;
    }

    /* =================================
       폼 레이블 가시성
       ================================= */
    label {
        display: block;
        margin-bottom: 4px;
        font-weight: 500;
        color: #334155;
    }

    /* 필수 표시 */
    .required::after {
        content: " *";
        color: #dc2626;
    }

    /* 도움말 텍스트 */
    .help-text {
        font-size: 14px;
        color: #64748b;
        margin-top: 4px;
    }

    /* 에러 메시지 */
    .error-message {
        font-size: 14px;
        color: #dc2626;
        margin-top: 4px;
    }
    </style>
    """


# =============================================================================
# 건너뛰기 링크 (Skip Links)
# =============================================================================

def render_skip_links(main_content_id: str = "main-content"):
    """건너뛰기 링크 렌더링

    Args:
        main_content_id: 메인 콘텐츠 영역 ID
    """
    skip_html = f"""
    <a href="#{main_content_id}" class="skip-link">
        본문으로 건너뛰기
    </a>
    """
    st.markdown(skip_html, unsafe_allow_html=True)


def render_main_content_start(content_id: str = "main-content"):
    """메인 콘텐츠 시작점 마커"""
    st.markdown(f'<div id="{content_id}" tabindex="-1"></div>', unsafe_allow_html=True)


# =============================================================================
# ARIA 컴포넌트
# =============================================================================

def aria_label(label: str) -> str:
    """ARIA 라벨 속성 생성"""
    return f'aria-label="{html.escape(label)}"'


def aria_describedby(element_id: str) -> str:
    """ARIA describedby 속성 생성"""
    return f'aria-describedby="{html.escape(element_id)}"'


def aria_hidden_icon(svg_content: str, label: Optional[str] = None) -> str:
    """접근성 있는 아이콘 생성

    Args:
        svg_content: SVG 내용
        label: 스크린 리더용 라벨 (None이면 장식용으로 처리)
    """
    if label:
        return f'''
        <span role="img" aria-label="{html.escape(label)}">
            {svg_content}
        </span>
        '''
    else:
        return f'''
        <span aria-hidden="true">
            {svg_content}
        </span>
        '''


def render_accessible_button(
    text: str,
    icon_svg: Optional[str] = None,
    aria_label: Optional[str] = None,
    disabled: bool = False,
    button_type: str = "primary"
) -> str:
    """접근성 있는 버튼 HTML 생성

    Args:
        text: 버튼 텍스트
        icon_svg: 아이콘 SVG (선택)
        aria_label: 스크린 리더용 라벨 (선택)
        disabled: 비활성화 여부
        button_type: 버튼 타입 (primary, secondary, danger)
    """
    label = aria_label or text
    icon_html = f'<span aria-hidden="true">{icon_svg}</span>' if icon_svg else ''
    disabled_attr = 'disabled aria-disabled="true"' if disabled else ''

    button_styles = {
        "primary": "background:#2563eb;color:#fff;",
        "secondary": "background:#f1f5f9;color:#334155;",
        "danger": "background:#dc2626;color:#fff;"
    }

    style = button_styles.get(button_type, button_styles["primary"])

    return f'''
    <button
        type="button"
        aria-label="{html.escape(label)}"
        style="{style}padding:10px 20px;border:none;border-radius:8px;
               font-weight:500;cursor:pointer;min-height:44px;
               display:inline-flex;align-items:center;gap:8px;"
        {disabled_attr}
    >
        {icon_html}
        <span>{html.escape(text)}</span>
    </button>
    '''


def render_accessible_link(
    text: str,
    href: str,
    new_tab: bool = False,
    aria_label: Optional[str] = None
) -> str:
    """접근성 있는 링크 HTML 생성"""
    label = aria_label or text
    new_tab_attrs = 'target="_blank" rel="noopener noreferrer"' if new_tab else ''
    new_tab_indicator = ' (새 창에서 열림)' if new_tab else ''

    return f'''
    <a
        href="{html.escape(href)}"
        aria-label="{html.escape(label + new_tab_indicator)}"
        {new_tab_attrs}
        style="color:#2563eb;text-decoration:underline;"
    >
        {html.escape(text)}
    </a>
    '''


# =============================================================================
# 라이브 리전 (동적 콘텐츠 알림)
# =============================================================================

def render_live_region(region_id: str = "live-announcer", politeness: str = "polite"):
    """라이브 리전 컨테이너 생성

    Args:
        region_id: 리전 ID
        politeness: 알림 긴급도 (polite, assertive)
    """
    st.markdown(f'''
    <div
        id="{region_id}"
        aria-live="{politeness}"
        aria-atomic="true"
        class="sr-only"
    ></div>
    ''', unsafe_allow_html=True)


def announce_to_screen_reader(message: str, region_id: str = "live-announcer"):
    """스크린 리더에 메시지 알림

    Args:
        message: 알림 메시지
        region_id: 라이브 리전 ID
    """
    # JavaScript로 라이브 리전 업데이트
    st.markdown(f'''
    <script>
    (function() {{
        var region = document.getElementById('{region_id}');
        if (region) {{
            region.textContent = '{html.escape(message)}';
        }}
    }})();
    </script>
    ''', unsafe_allow_html=True)


# =============================================================================
# 폼 접근성
# =============================================================================

def render_form_field(
    field_id: str,
    label: str,
    field_type: str = "text",
    required: bool = False,
    help_text: Optional[str] = None,
    error_message: Optional[str] = None,
    placeholder: Optional[str] = None
) -> str:
    """접근성 있는 폼 필드 HTML 생성

    Args:
        field_id: 필드 ID
        label: 라벨 텍스트
        field_type: 필드 타입 (text, email, password, etc.)
        required: 필수 여부
        help_text: 도움말 텍스트
        error_message: 에러 메시지
        placeholder: 플레이스홀더
    """
    required_class = 'required' if required else ''
    required_attr = 'required aria-required="true"' if required else ''
    help_id = f"{field_id}-help" if help_text else None
    error_id = f"{field_id}-error" if error_message else None

    describedby_ids = []
    if help_id:
        describedby_ids.append(help_id)
    if error_id:
        describedby_ids.append(error_id)
    describedby_attr = f'aria-describedby="{" ".join(describedby_ids)}"' if describedby_ids else ''

    invalid_attr = 'aria-invalid="true"' if error_message else ''
    placeholder_attr = f'placeholder="{html.escape(placeholder)}"' if placeholder else ''

    help_html = f'<div id="{help_id}" class="help-text">{html.escape(help_text)}</div>' if help_text else ''
    error_html = f'<div id="{error_id}" class="error-message" role="alert">{html.escape(error_message)}</div>' if error_message else ''

    return f'''
    <div class="form-field" style="margin-bottom:16px;">
        <label for="{field_id}" class="{required_class}" style="display:block;margin-bottom:4px;font-weight:500;color:#334155;">
            {html.escape(label)}
        </label>
        <input
            type="{field_type}"
            id="{field_id}"
            name="{field_id}"
            {required_attr}
            {describedby_attr}
            {invalid_attr}
            {placeholder_attr}
            style="width:100%;padding:10px 12px;border:1px solid {'#dc2626' if error_message else '#d1d5db'};
                   border-radius:8px;font-size:16px;min-height:44px;"
        />
        {help_html}
        {error_html}
    </div>
    '''


# =============================================================================
# 키보드 네비게이션
# =============================================================================

def get_keyboard_navigation_js() -> str:
    """키보드 네비게이션 JavaScript"""
    return """
    <script>
    (function() {
        // 키보드 사용 감지
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-nav-active');
            }
        });

        // 마우스 클릭 시 키보드 모드 해제
        document.addEventListener('mousedown', function() {
            document.body.classList.remove('keyboard-nav-active');
        });

        // Escape 키로 모달/드롭다운 닫기
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                // 열린 모달이나 드롭다운 닫기
                var openModals = document.querySelectorAll('[data-modal-open="true"]');
                openModals.forEach(function(modal) {
                    modal.style.display = 'none';
                    modal.setAttribute('data-modal-open', 'false');
                });
            }
        });

        // 포커스 트랩 (모달 내)
        function trapFocus(element) {
            var focusableElements = element.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            var firstFocusable = focusableElements[0];
            var lastFocusable = focusableElements[focusableElements.length - 1];

            element.addEventListener('keydown', function(e) {
                if (e.key !== 'Tab') return;

                if (e.shiftKey) {
                    if (document.activeElement === firstFocusable) {
                        lastFocusable.focus();
                        e.preventDefault();
                    }
                } else {
                    if (document.activeElement === lastFocusable) {
                        firstFocusable.focus();
                        e.preventDefault();
                    }
                }
            });
        }

        // 글로벌 함수로 노출
        window.trapFocus = trapFocus;
    })();
    </script>
    """


# =============================================================================
# 접근성 초기화
# =============================================================================

def init_accessibility():
    """접근성 기능 초기화 (페이지 시작 시 호출)"""
    # CSS 적용
    st.markdown(get_accessibility_css(), unsafe_allow_html=True)

    # 건너뛰기 링크
    render_skip_links()

    # 라이브 리전
    render_live_region()

    # 키보드 네비게이션
    st.markdown(get_keyboard_navigation_js(), unsafe_allow_html=True)

    # 메인 콘텐츠 시작점
    render_main_content_start()


# =============================================================================
# 접근성 검사 도구 (개발용)
# =============================================================================

def check_color_contrast(foreground: str, background: str) -> dict:
    """색상 대비 검사

    Args:
        foreground: 전경색 (hex)
        background: 배경색 (hex)

    Returns:
        대비 비율 및 WCAG 준수 여부
    """
    def hex_to_rgb(hex_color: str) -> tuple:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def get_luminance(rgb: tuple) -> float:
        r, g, b = [x / 255 for x in rgb]
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    fg_rgb = hex_to_rgb(foreground)
    bg_rgb = hex_to_rgb(background)

    fg_lum = get_luminance(fg_rgb)
    bg_lum = get_luminance(bg_rgb)

    lighter = max(fg_lum, bg_lum)
    darker = min(fg_lum, bg_lum)

    ratio = (lighter + 0.05) / (darker + 0.05)

    return {
        "ratio": round(ratio, 2),
        "aa_normal": ratio >= 4.5,      # 일반 텍스트
        "aa_large": ratio >= 3.0,       # 대형 텍스트
        "aaa_normal": ratio >= 7.0,     # AAA 일반
        "aaa_large": ratio >= 4.5       # AAA 대형
    }


def render_accessibility_checklist():
    """접근성 체크리스트 (개발자용)"""
    checklist = """
    ### 접근성 체크리스트 (WCAG 2.1 AA)

    #### 인지 가능 (Perceivable)
    - [ ] 모든 이미지에 대체 텍스트(alt) 제공
    - [ ] 색상만으로 정보 전달하지 않음
    - [ ] 텍스트 대비 비율 4.5:1 이상
    - [ ] 텍스트 200% 확대 시 내용 손실 없음

    #### 조작 가능 (Operable)
    - [ ] 모든 기능 키보드로 접근 가능
    - [ ] 포커스 표시 명확함
    - [ ] 건너뛰기 링크 제공
    - [ ] 깜빡임 콘텐츠 없음 (3회/초 미만)

    #### 이해 가능 (Understandable)
    - [ ] 페이지 언어 명시 (lang 속성)
    - [ ] 일관된 네비게이션
    - [ ] 입력 오류 명확히 설명
    - [ ] 레이블 또는 지시사항 제공

    #### 견고함 (Robust)
    - [ ] 유효한 HTML 마크업
    - [ ] ARIA 속성 올바르게 사용
    - [ ] 보조 기술과 호환
    """
    st.markdown(checklist)


# =============================================================================
# 편의 함수
# =============================================================================

def accessible_table(
    headers: List[str],
    rows: List[List[str]],
    caption: Optional[str] = None
) -> str:
    """접근성 있는 테이블 HTML 생성

    Args:
        headers: 헤더 목록
        rows: 행 데이터 목록
        caption: 테이블 설명 (선택)
    """
    caption_html = f'<caption class="sr-only">{html.escape(caption)}</caption>' if caption else ''

    header_cells = ''.join([f'<th scope="col">{html.escape(h)}</th>' for h in headers])

    body_rows = ''
    for row in rows:
        cells = ''.join([f'<td>{html.escape(str(cell))}</td>' for cell in row])
        body_rows += f'<tr>{cells}</tr>'

    return f'''
    <table role="table" style="width:100%;border-collapse:collapse;">
        {caption_html}
        <thead>
            <tr>{header_cells}</tr>
        </thead>
        <tbody>
            {body_rows}
        </tbody>
    </table>
    '''


def accessible_progress(
    value: int,
    max_value: int = 100,
    label: str = "진행률"
) -> str:
    """접근성 있는 진행 표시줄"""
    percentage = min(100, max(0, int((value / max_value) * 100)))

    return f'''
    <div
        role="progressbar"
        aria-valuenow="{value}"
        aria-valuemin="0"
        aria-valuemax="{max_value}"
        aria-label="{html.escape(label)}: {percentage}%"
        style="width:100%;height:8px;background:#e2e8f0;border-radius:4px;overflow:hidden;"
    >
        <div style="width:{percentage}%;height:100%;background:#2563eb;transition:width 0.3s ease;"></div>
    </div>
    <span class="sr-only">{label}: {percentage}%</span>
    '''

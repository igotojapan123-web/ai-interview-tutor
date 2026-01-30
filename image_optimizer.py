# image_optimizer.py
# 이미지 최적화 및 레이지 로딩 유틸리티

import base64
from typing import Optional
import streamlit as st

try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# ============================================================
# 레이지 로딩 CSS
# ============================================================

LAZY_LOADING_CSS = """
<style>
/* 레이지 로딩 이미지 스타일 */
.lazy-image {
    opacity: 0;
    transition: opacity 0.3s ease-in-out;
}

.lazy-image.loaded {
    opacity: 1;
}

/* 이미지 플레이스홀더 */
.image-placeholder {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 8px;
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

/* 아바타 이미지 최적화 */
.avatar-optimized {
    width: 100%;
    height: auto;
    object-fit: cover;
    border-radius: 50%;
}

/* 썸네일 최적화 */
.thumbnail-optimized {
    width: 100%;
    height: auto;
    object-fit: cover;
    border-radius: 8px;
}

/* 반응형 이미지 */
.responsive-image {
    max-width: 100%;
    height: auto;
}
</style>
"""

LAZY_LOADING_JS = """
<script>
// 레이지 로딩 JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const lazyImages = document.querySelectorAll('img.lazy-image');

    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.add('loaded');
                    observer.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });

        lazyImages.forEach(img => imageObserver.observe(img));
    } else {
        // 폴백: IntersectionObserver 미지원 브라우저
        lazyImages.forEach(img => {
            img.src = img.dataset.src;
            img.classList.add('loaded');
        });
    }
});
</script>
"""


# ============================================================
# 이미지 최적화 함수
# ============================================================

def inject_lazy_loading_styles() -> None:
    """레이지 로딩 스타일 주입 (페이지 상단에서 1회 호출)"""
    st.markdown(LAZY_LOADING_CSS, unsafe_allow_html=True)
    st.markdown(LAZY_LOADING_JS, unsafe_allow_html=True)


def get_lazy_image_html(
    src: str,
    alt: str = "",
    width: Optional[int] = None,
    height: Optional[int] = None,
    css_class: str = "",
    placeholder_color: str = "#f0f0f0"
) -> str:
    """
    레이지 로딩 이미지 HTML 생성

    Args:
        src: 이미지 URL
        alt: 대체 텍스트
        width: 너비 (픽셀)
        height: 높이 (픽셀)
        css_class: 추가 CSS 클래스
        placeholder_color: 플레이스홀더 배경색
    """
    size_style = ""
    if width:
        size_style += f"width: {width}px; "
    if height:
        size_style += f"height: {height}px; "

    # 작은 투명 플레이스홀더 이미지 (1x1 픽셀)
    placeholder = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

    return f'''
    <div class="image-placeholder" style="{size_style}background-color: {placeholder_color};">
        <img
            class="lazy-image {css_class}"
            src="{placeholder}"
            data-src="{src}"
            alt="{alt}"
            style="{size_style}"
            loading="lazy"
        />
    </div>
    '''


def get_optimized_avatar_html(
    src: str,
    name: str = "",
    size: int = 80
) -> str:
    """
    최적화된 아바타 이미지 HTML

    Args:
        src: 이미지 URL 또는 base64
        name: 사용자 이름 (대체 텍스트용)
        size: 아바타 크기 (픽셀)
    """
    # 이니셜 폴백
    initial = name[0].upper() if name else "?"

    return f'''
    <div style="
        width: {size}px;
        height: {size}px;
        border-radius: 50%;
        overflow: hidden;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: {size // 2}px;
    ">
        <img
            src="{src}"
            alt="{name}"
            class="avatar-optimized"
            style="width: 100%; height: 100%; object-fit: cover;"
            loading="lazy"
            onerror="this.style.display='none'; this.parentElement.innerHTML='{initial}';"
        />
    </div>
    '''


def get_thumbnail_html(
    src: str,
    alt: str = "",
    width: int = 200,
    height: int = 150,
    border_radius: int = 8
) -> str:
    """
    최적화된 썸네일 HTML

    Args:
        src: 이미지 URL
        alt: 대체 텍스트
        width: 너비
        height: 높이
        border_radius: 모서리 둥글기
    """
    return f'''
    <div style="
        width: {width}px;
        height: {height}px;
        border-radius: {border_radius}px;
        overflow: hidden;
        background: #f0f0f0;
    ">
        <img
            src="{src}"
            alt="{alt}"
            class="thumbnail-optimized"
            style="width: 100%; height: 100%; object-fit: cover;"
            loading="lazy"
            onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22{width}%22 height=%22{height}%22><rect fill=%22%23f0f0f0%22 width=%22100%%22 height=%22100%%22/><text x=%2250%%22 y=%2250%%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%23999%22>No Image</text></svg>';"
        />
    </div>
    '''


def optimize_base64_image(base64_data: str, max_size_kb: int = 100) -> str:
    """
    Base64 이미지 최적화 (크기 확인)

    Args:
        base64_data: Base64 인코딩된 이미지 데이터
        max_size_kb: 최대 허용 크기 (KB)

    Returns:
        원본 또는 경고 메시지
    """
    try:
        # Base64 크기 계산 (대략적)
        size_bytes = len(base64_data) * 3 / 4
        size_kb = size_bytes / 1024

        if size_kb > max_size_kb:
            logger.warning(f"이미지 크기 초과: {size_kb:.1f}KB > {max_size_kb}KB")

        return base64_data

    except Exception as e:
        logger.error(f"이미지 최적화 오류: {e}")
        return base64_data


# ============================================================
# Streamlit 컴포넌트
# ============================================================

def st_lazy_image(
    src: str,
    caption: str = "",
    width: Optional[int] = None
) -> None:
    """Streamlit 레이지 로딩 이미지 컴포넌트"""
    html = get_lazy_image_html(src, alt=caption, width=width)
    st.markdown(html, unsafe_allow_html=True)
    if caption:
        st.caption(caption)


def st_avatar(
    src: str,
    name: str = "",
    size: int = 80
) -> None:
    """Streamlit 아바타 컴포넌트"""
    html = get_optimized_avatar_html(src, name, size)
    st.markdown(html, unsafe_allow_html=True)


def st_thumbnail(
    src: str,
    caption: str = "",
    width: int = 200,
    height: int = 150
) -> None:
    """Streamlit 썸네일 컴포넌트"""
    html = get_thumbnail_html(src, alt=caption, width=width, height=height)
    st.markdown(html, unsafe_allow_html=True)
    if caption:
        st.caption(caption)


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=== Image Optimizer ===")
    print("Functions available:")
    print("  - inject_lazy_loading_styles()")
    print("  - get_lazy_image_html()")
    print("  - get_optimized_avatar_html()")
    print("  - get_thumbnail_html()")
    print("  - st_lazy_image(), st_avatar(), st_thumbnail()")
    print("Ready!")

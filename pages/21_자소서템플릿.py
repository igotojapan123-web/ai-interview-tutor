# pages/21_자소서템플릿.py
# Phase C3: 자소서 템플릿 페이지
# FlyReady Lab Enhancement

import streamlit as st
import sys
import os

# 상위 디렉토리 import 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 페이지 초기화
from sidebar_common import init_page, end_page
init_page(
    title="자소서 템플릿",
    current_page="자소서템플릿",
    wide_layout=True
)

# 구글 번역 방지
st.markdown("""
<meta name="google" content="notranslate">
<meta http-equiv="Content-Language" content="ko">
<style>
html, body, .stApp, .main, [data-testid="stAppViewContainer"] {
    translate: no !important;
}
</style>
""", unsafe_allow_html=True)

# 모듈 임포트
try:
    from resume_template import (
        get_resume_template,
        get_keyword_recommendations,
        check_keyword_usage,
        get_airline_characteristics,
        get_all_airlines,
        get_all_item_types,
    )
    TEMPLATE_AVAILABLE = True
except ImportError as e:
    TEMPLATE_AVAILABLE = False
    st.error(f"템플릿 모듈 로드 실패: {e}")

# =====================
# 메인 UI
# =====================

st.title("자소서 템플릿")
st.caption("항공사별 맞춤 자소서 템플릿과 키워드 추천")

if not TEMPLATE_AVAILABLE:
    st.error("템플릿 모듈을 불러올 수 없습니다.")
    st.stop()

# =====================
# 설정 섹션
# =====================

st.markdown("### 1. 항공사 & 항목 선택")

col1, col2 = st.columns(2)

with col1:
    airlines = get_all_airlines()
    selected_airline = st.selectbox(
        "지원 항공사",
        airlines,
        key="template_airline"
    )

with col2:
    item_types = get_all_item_types()
    selected_item = st.selectbox(
        "자소서 항목",
        item_types,
        key="template_item"
    )

# 항공사 특성 표시
if selected_airline:
    characteristics = get_airline_characteristics(selected_airline)

    with st.expander("선택 항공사 특성 보기", expanded=True):
        char_col1, char_col2 = st.columns(2)

        with char_col1:
            st.markdown(f"**항공사 유형**: {characteristics.get('type', 'N/A')}")
            st.markdown("**핵심 가치**")
            for value in characteristics.get("core_values", []):
                st.markdown(f"- {value}")

        with char_col2:
            st.markdown("**인재상 키워드**")
            keywords_html = " ".join([
                f"<span style='background:#e8f4f8;padding:4px 10px;border-radius:12px;margin:2px;display:inline-block;'>{kw}</span>"
                for kw in characteristics.get("talent_keywords", [])
            ])
            st.markdown(keywords_html, unsafe_allow_html=True)

            st.markdown(f"**면접 스타일**: {characteristics.get('interview_style', 'N/A')}")

        # 강조/회피 포인트
        st.markdown("---")
        em_col, av_col = st.columns(2)

        with em_col:
            st.markdown("**강조할 포인트**")
            for em in characteristics.get("emphasis", []):
                st.markdown(f"- {em}")

        with av_col:
            if characteristics.get("avoid"):
                st.markdown("**피해야 할 표현**")
                for av in characteristics.get("avoid", []):
                    st.markdown(f"- {av}")

st.divider()

# =====================
# 템플릿 섹션
# =====================

st.markdown("### 2. 맞춤 템플릿")

if st.button("템플릿 생성", type="primary", use_container_width=True):
    template = get_resume_template(selected_airline, selected_item)
    st.session_state["current_template"] = template

if "current_template" in st.session_state:
    template = st.session_state["current_template"]

    # 기본 정보
    st.info(f"**권장 분량**: {template['char_limit'][0]}~{template['char_limit'][1]}자")

    # 아웃라인
    st.markdown("#### 작성 아웃라인")
    st.code(template.get("outline", ""), language=None)

    # 섹션별 가이드
    st.markdown("#### 섹션별 작성 가이드")

    for i, section in enumerate(template.get("sections", []), 1):
        with st.expander(f"[{i}] {section['title']}", expanded=True):
            st.markdown(f"**설명**: {section['description']}")
            st.markdown(f"**권장 분량**: {section['char_limit'][0]}~{section['char_limit'][1]}자")

            if section.get("example"):
                st.markdown("**예시 시작**")
                st.markdown(f"> {section['example']}")

            if section.get("keywords"):
                st.markdown("**포함할 키워드**")
                kw_html = " ".join([
                    f"<span style='background:#fff3cd;padding:3px 8px;border-radius:8px;margin:2px;font-size:13px;'>{kw}</span>"
                    for kw in section["keywords"]
                ])
                st.markdown(kw_html, unsafe_allow_html=True)

            if section.get("tips"):
                st.markdown("**작성 팁**")
                for tip in section["tips"]:
                    st.markdown(f"- {tip}")

    # 필수/회피 키워드
    st.markdown("---")
    must_col, avoid_col = st.columns(2)

    with must_col:
        st.markdown("**반드시 포함할 요소**")
        for item in template.get("must_include", []):
            st.markdown(f"- {item}")

    with avoid_col:
        if template.get("avoid"):
            st.markdown("**피해야 할 표현**")
            for item in template.get("avoid", []):
                st.markdown(f"- {item}")

st.divider()

# =====================
# 키워드 체크 섹션
# =====================

st.markdown("### 3. 내 자소서 키워드 체크")

user_text = st.text_area(
    "자소서 내용을 붙여넣으세요",
    height=200,
    placeholder="여기에 작성한 자소서를 붙여넣으면 키워드 사용 현황을 분석해드립니다...",
    key="template_user_text"
)

if user_text and len(user_text) >= 50:
    check_result = check_keyword_usage(user_text, selected_airline, selected_item)

    # 점수 표시
    score = check_result.get("usage_score", 0)
    score_color = "green" if score >= 70 else "orange" if score >= 40 else "red"

    st.markdown(f"""
    <div style='text-align:center;padding:20px;background:#f8f9fa;border-radius:10px;margin:10px 0;'>
        <h2 style='color:{score_color};margin:0;'>키워드 활용도: {score}점</h2>
        <p style='margin:5px 0 0 0;'>{check_result.get('recommendation', '')}</p>
    </div>
    """, unsafe_allow_html=True)

    # 사용/미사용 키워드
    used_col, missing_col = st.columns(2)

    with used_col:
        st.markdown("**사용된 키워드**")
        used = check_result.get("used_keywords", [])
        if used:
            used_html = " ".join([
                f"<span style='background:#d4edda;padding:4px 10px;border-radius:12px;margin:2px;display:inline-block;'>{kw}</span>"
                for kw in used
            ])
            st.markdown(used_html, unsafe_allow_html=True)
        else:
            st.info("아직 사용된 추천 키워드가 없습니다.")

    with missing_col:
        st.markdown("**추가 권장 키워드**")
        missing = check_result.get("missing_keywords", [])
        if missing:
            missing_html = " ".join([
                f"<span style='background:#fff3cd;padding:4px 10px;border-radius:12px;margin:2px;display:inline-block;'>{kw}</span>"
                for kw in missing
            ])
            st.markdown(missing_html, unsafe_allow_html=True)
        else:
            st.success("모든 핵심 키워드를 잘 활용하고 있습니다!")

elif user_text:
    st.warning("최소 50자 이상 입력해주세요.")

st.divider()

# =====================
# 추천 키워드 전체 보기
# =====================

st.markdown("### 4. 추천 키워드 전체 보기")

with st.expander("키워드 목록 펼치기"):
    keywords = get_keyword_recommendations(selected_airline, selected_item)

    for category, kw_list in keywords.items():
        category_names = {
            "airline_core": "항공사 핵심 가치",
            "airline_talent": "인재상 키워드",
            "type_keywords": "항공사 유형별 키워드",
            "item_keywords": "항목별 필수 키워드",
            "common_keywords": "공통 서비스 키워드",
        }

        st.markdown(f"**{category_names.get(category, category)}**")
        if kw_list:
            kw_html = " ".join([
                f"<span style='background:#e8f4f8;padding:4px 10px;border-radius:12px;margin:2px;display:inline-block;'>{kw}</span>"
                for kw in kw_list
            ])
            st.markdown(kw_html, unsafe_allow_html=True)
        else:
            st.caption("-")
        st.markdown("")

# 페이지 종료
end_page()

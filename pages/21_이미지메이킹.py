# pages/21_이미지메이킹.py
# 항공사 면접 이미지메이킹 가이드

import streamlit as st
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_utils import check_tester_password

st.set_page_config(
    page_title="이미지메이킹",
    page_icon="👗",
    layout="wide"
)

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="이미지메이킹")
except ImportError:
    pass


check_tester_password()

# ----------------------------
# 데이터
# ----------------------------

# 항공사별 이미지 특징
AIRLINE_IMAGE = {
    "대한항공": {
        "color": "#0F4C81",
        "style": "클래식 & 단정",
        "makeup": "자연스러운 누드톤, 깔끔한 아이라인, 코랄/핑크 립",
        "hair": "단정한 업스타일, 쪽머리, 망사망 사용",
        "outfit": "네이비/화이트 조합, 정장 스커트",
        "keywords": ["단정함", "신뢰감", "프로페셔널"],
        "tip": "가장 보수적인 이미지. 과한 메이크업 지양"
    },
    "아시아나항공": {
        "color": "#C4161C",
        "style": "우아함 & 세련됨",
        "makeup": "레드/코랄 립 강조, 깔끔한 눈매, 자연스러운 피부",
        "hair": "깔끔한 업스타일, 낮은 쪽머리",
        "outfit": "그레이/화이트 정장, 여성스러운 라인",
        "keywords": ["우아함", "세련됨", "아름다운 사람들"],
        "tip": "브랜드 슬로건처럼 '아름다운 사람들' 이미지"
    },
    "에어프레미아": {
        "color": "#00A0B0",
        "style": "모던 & 프레시",
        "makeup": "자연스럽고 깨끗한 피부, 생기있는 메이크업",
        "hair": "깔끔한 포니테일 또는 단발",
        "outfit": "깔끔한 비즈니스 캐주얼 가능",
        "keywords": ["신선함", "젊음", "프리미엄"],
        "tip": "HSC 특성상 조금 더 유연한 이미지 가능"
    },
    "진에어": {
        "color": "#F15A29",
        "style": "발랄 & 활기",
        "makeup": "밝은 톤, 오렌지/코랄 계열, 생기있는 피부",
        "hair": "깔끔한 포니테일, 반묶음 가능",
        "outfit": "밝은 색상 포인트 가능",
        "keywords": ["Fun", "Young", "Dynamic"],
        "tip": "LCC 중에서도 젊고 활기찬 이미지 강조"
    },
    "제주항공": {
        "color": "#FF6600",
        "style": "밝음 & 친근",
        "makeup": "화사한 피부, 자연스러운 눈, 오렌지/코랄 립",
        "hair": "깔끔한 정리, 포니테일 OK",
        "outfit": "오렌지 포인트, 밝은 분위기",
        "keywords": ["친근함", "밝음", "긍정"],
        "tip": "시그니처 오렌지 컬러와 어울리는 이미지"
    },
    "티웨이항공": {
        "color": "#E31937",
        "style": "밝음 & 친절",
        "makeup": "깨끗한 피부, 레드/핑크 립",
        "hair": "단정한 정리",
        "outfit": "레드 포인트 악세서리 가능",
        "keywords": ["즐거움", "친절", "여행"],
        "tip": "친근하고 밝은 이미지"
    },
    "에어부산": {
        "color": "#00AEEF",
        "style": "상쾌 & 친근",
        "makeup": "깔끔하고 자연스러운 메이크업",
        "hair": "단정한 정리",
        "outfit": "블루 계열 포인트",
        "keywords": ["부산", "바다", "친근"],
        "tip": "부산의 상쾌한 이미지와 연결"
    },
}

# 메이크업 기본 가이드
MAKEUP_GUIDE = {
    "베이스": {
        "steps": [
            "1. 스킨케어로 촉촉한 피부 준비",
            "2. 프라이머로 모공 정리",
            "3. 파운데이션은 본인 피부톤과 동일하게",
            "4. 컨실러로 다크서클, 잡티 커버",
            "5. 파우더로 가볍게 세팅"
        ],
        "tips": [
            "너무 하얀 화장 X (목과 경계선 주의)",
            "매트보다는 세미매트 추천",
            "면접장 조명 아래서 확인 필수"
        ]
    },
    "눈": {
        "steps": [
            "1. 아이브로우: 자연스러운 아치형",
            "2. 아이섀도우: 베이지~브라운 그라데이션",
            "3. 아이라인: 가늘게, 눈꼬리 살짝 빼기",
            "4. 마스카라: 깔끔하게 한두 겹"
        ],
        "tips": [
            "글리터/펄 아이섀도우 지양",
            "속눈썹 연장은 자연스러운 정도만",
            "눈 밑 펄 하이라이터 X"
        ]
    },
    "입술": {
        "steps": [
            "1. 립밤으로 각질 정리",
            "2. 립라이너로 입술선 정리 (선택)",
            "3. 립스틱 바르기",
            "4. 티슈로 가볍게 눌러 지속력 UP"
        ],
        "tips": [
            "FSC: 코랄, 핑크, MLBB 추천",
            "LCC: 오렌지, 레드 포인트 가능",
            "너무 진한 레드/다크톤 지양"
        ]
    },
    "치크": {
        "steps": [
            "1. 미소 지었을 때 볼록한 부분에",
            "2. 브러시로 가볍게 터치",
            "3. 자연스럽게 블렌딩"
        ],
        "tips": [
            "피부톤에 맞는 코랄/피치 계열",
            "너무 진하게 X",
            "하이라이터는 C존에만 살짝"
        ]
    }
}

# 헤어스타일 가이드
HAIR_GUIDE = {
    "쪽머리 (Bun)": {
        "description": "가장 클래식한 승무원 헤어스타일",
        "suitable": ["대한항공", "아시아나항공"],
        "steps": [
            "1. 머리를 깔끔하게 빗어 뒤로 모으기",
            "2. 높이는 귀 윗선~정수리 중간",
            "3. 고무줄로 단단히 묶기",
            "4. 돌돌 말아서 쪽 만들기",
            "5. 헤어핀으로 고정",
            "6. 망사망으로 감싸 마무리",
            "7. 스프레이로 잔머리 정리"
        ],
        "tips": ["잔머리 정리 필수", "망사망 색상은 머리색과 동일하게"]
    },
    "포니테일": {
        "description": "깔끔하고 활동적인 느낌",
        "suitable": ["진에어", "제주항공", "에어프레미아"],
        "steps": [
            "1. 머리를 빗어 뒤로 모으기",
            "2. 귀 윗선 높이에서 묶기",
            "3. 고무줄을 머리카락으로 감싸기",
            "4. 스프레이로 잔머리 정리"
        ],
        "tips": ["너무 높거나 낮지 않게", "머리끝은 깔끔하게 정리"]
    },
    "반묶음 (하프업)": {
        "description": "부드럽고 여성스러운 느낌",
        "suitable": ["LCC 일부"],
        "steps": [
            "1. 윗머리만 뒤로 모으기",
            "2. 귀 윗선에서 단정하게 묶기",
            "3. 아랫머리는 깔끔하게 정리"
        ],
        "tips": ["단발~중단발에 적합", "FSC는 피하는 것이 좋음"]
    },
    "단발": {
        "description": "깔끔하고 세련된 느낌",
        "suitable": ["에어프레미아", "LCC"],
        "steps": [
            "1. 깔끔하게 손질된 단발",
            "2. 헤어핀으로 귀 뒤로 넘기기",
            "3. 스프레이로 고정"
        ],
        "tips": ["어깨 위 길이", "앞머리는 이마가 보이게 정리"]
    }
}

# 복장 가이드
OUTFIT_GUIDE = {
    "정장 상의": {
        "do": [
            "몸에 맞는 사이즈 (너무 크거나 작지 않게)",
            "네이비, 그레이, 블랙 등 무난한 색상",
            "싱글 버튼 자켓 추천",
            "어깨선이 딱 맞는 것"
        ],
        "dont": [
            "화려한 패턴이나 색상",
            "너무 짧은 자켓",
            "과한 장식이 있는 것"
        ]
    },
    "스커트": {
        "do": [
            "무릎 위 3~5cm (H라인 추천)",
            "편하게 앉을 수 있는 핏",
            "상의와 세트 또는 어울리는 색상"
        ],
        "dont": [
            "너무 짧은 미니스커트",
            "너무 타이트한 핏",
            "슬릿이 깊은 디자인"
        ]
    },
    "블라우스": {
        "do": [
            "화이트, 베이비블루, 연핑크 등 밝은 색상",
            "깔끔한 카라 디자인",
            "목선이 적당히 오픈된 것"
        ],
        "dont": [
            "시스루 소재",
            "과한 프릴이나 장식",
            "너무 깊은 브이넥"
        ]
    },
    "구두": {
        "do": [
            "베이지 또는 블랙 단색",
            "5~7cm 굽 (너무 높지 않게)",
            "앞코가 막힌 펌프스"
        ],
        "dont": [
            "오픈토, 슬링백",
            "화려한 장식",
            "굽이 너무 높거나 낮은 것"
        ]
    },
    "악세서리": {
        "do": [
            "작은 진주/골드 귀걸이",
            "심플한 목걸이 (선택)",
            "깔끔한 손목시계"
        ],
        "dont": [
            "큰 후프 귀걸이",
            "화려한 목걸이",
            "팔찌, 반지 여러 개"
        ]
    }
}


# ----------------------------
# UI
# ----------------------------
st.title("👗 이미지메이킹 가이드")
st.caption("항공사 면접을 위한 메이크업, 헤어, 복장 가이드")

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["🎨 메이크업", "💇 헤어스타일", "👔 복장", "✈️ 항공사별"])

# ========== 탭1: 메이크업 ==========
with tab1:
    st.subheader("🎨 면접 메이크업 가이드")

    for part, info in MAKEUP_GUIDE.items():
        with st.expander(f"💄 {part} 메이크업", expanded=(part == "베이스")):
            col1, col2 = st.columns([3, 2])

            with col1:
                st.markdown("**순서:**")
                for step in info["steps"]:
                    st.markdown(step)

            with col2:
                st.markdown("**주의사항:**")
                for tip in info["tips"]:
                    st.info(tip)

    st.markdown("---")
    st.success("""
    **핵심 포인트**
    - 자연스럽고 깨끗한 피부 표현
    - 과하지 않은 눈 화장
    - 건강하고 밝은 입술
    - 전체적으로 '단정하고 신뢰감 있는' 인상
    """)


# ========== 탭2: 헤어스타일 ==========
with tab2:
    st.subheader("💇 면접 헤어스타일 가이드")

    for style, info in HAIR_GUIDE.items():
        with st.expander(f"💇‍♀️ {style}"):
            st.markdown(f"**{info['description']}**")
            st.caption(f"추천 항공사: {', '.join(info['suitable'])}")

            st.markdown("---")

            col1, col2 = st.columns([3, 2])

            with col1:
                st.markdown("**방법:**")
                for step in info["steps"]:
                    st.markdown(step)

            with col2:
                st.markdown("**팁:**")
                for tip in info["tips"]:
                    st.info(tip)

    st.markdown("---")
    st.warning("""
    **공통 주의사항**
    - 염색은 자연스러운 갈색까지만 (탈색 X)
    - 잔머리 정리 필수 (왁스/스프레이 활용)
    - 앞머리는 이마가 보이게 정리
    - 면접 전날 미용실에서 정리 추천
    """)


# ========== 탭3: 복장 ==========
with tab3:
    st.subheader("👔 면접 복장 가이드")

    for item, info in OUTFIT_GUIDE.items():
        with st.expander(f"👗 {item}"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**✅ DO**")
                for do in info["do"]:
                    st.success(do)

            with col2:
                st.markdown("**❌ DON'T**")
                for dont in info["dont"]:
                    st.error(dont)

    st.markdown("---")

    st.info("""
    **면접 전 체크리스트**
    - [ ] 정장에 보풀/먼지 제거
    - [ ] 구두 광택
    - [ ] 스타킹 여분 준비
    - [ ] 옷에서 냄새나지 않는지 확인
    - [ ] 전신 거울로 뒷모습까지 확인
    """)


# ========== 탭4: 항공사별 ==========
with tab4:
    st.subheader("✈️ 항공사별 이미지 가이드")

    selected = st.selectbox(
        "항공사 선택",
        list(AIRLINE_IMAGE.keys())
    )

    info = AIRLINE_IMAGE[selected]

    # 색상 헤더
    st.markdown(f"""
    <div style="background: {info['color']}; padding: 20px; border-radius: 10px; color: white; text-align: center;">
        <h2 style="margin: 0; color: white;">{selected}</h2>
        <p style="margin: 5px 0 0 0; opacity: 0.9;">{info['style']}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    # 키워드
    keyword_html = " ".join([f'<span style="background: {info["color"]}20; color: {info["color"]}; padding: 5px 15px; border-radius: 20px; margin-right: 5px; font-weight: 600;">#{kw}</span>' for kw in info["keywords"]])
    st.markdown(keyword_html, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🎨 메이크업**")
        st.write(info["makeup"])

    with col2:
        st.markdown("**💇 헤어**")
        st.write(info["hair"])

    with col3:
        st.markdown("**👔 복장**")
        st.write(info["outfit"])

    st.markdown("---")

    st.info(f"💡 **TIP:** {info['tip']}")

    # 전체 비교표
    st.markdown("---")
    st.markdown("### 📊 전체 항공사 비교")

    comparison_data = []
    for airline, data in AIRLINE_IMAGE.items():
        comparison_data.append({
            "항공사": airline,
            "스타일": data["style"],
            "키워드": ", ".join(data["keywords"])
        })

    st.dataframe(comparison_data, use_container_width=True, hide_index=True)

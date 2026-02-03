# pages/15_국민체력.py
# 국민체력100 - 등급 계산기 + 훈련 트래커 + 맞춤 플랜 + D-Day + 합격자 후기

import streamlit as st
import os
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sidebar_common import init_page, end_page

# 공용 유틸리티 (Stage 2)
try:
    from shared_utils import get_api_key, load_json, save_json
except ImportError:
    pass

init_page(
    title="국민체력 가이드",
    current_page="국민체력",
    wide_layout=True
)


st.markdown("""
<meta name="google" content="notranslate">
<meta http-equiv="Content-Language" content="ko">
<style>
html, body, .stApp, .main, [data-testid="stAppViewContainer"] {
    translate: no !important;
}
.notranslate, [translate="no"] {
    translate: no !important;
}
</style>
""", unsafe_allow_html=True)
st.markdown('<div translate="no" class="notranslate" lang="ko">', unsafe_allow_html=True)

# ========================================
# 데이터 저장 경로
# ========================================
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
FITNESS_HISTORY_FILE = os.path.join(DATA_DIR, "fitness_history.json")
FITNESS_DDAY_FILE = os.path.join(DATA_DIR, "fitness_dday.json")


@st.cache_data(ttl=300)
def load_json(filepath):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_json(filepath, data):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        load_json.clear()  # 캐시 무효화
    except Exception:
        pass


@st.cache_data(ttl=60)
def load_dday():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(FITNESS_DDAY_FILE):
            with open(FITNESS_DDAY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def save_dday(data):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(FITNESS_DDAY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        load_dday.clear()  # 캐시 무효화
    except Exception:
        pass


# ========================================
# 등급 기준 데이터 (20대 여성)
# ========================================
GRADE_CRITERIA = {
    "악력": {
        "unit": "kg",
        "direction": "higher",  # 높을수록 좋음
        "grade1": 31.5,
        "grade2": 26.5,
        "grade3": 22.5,
    },
    "윗몸일으키기": {
        "unit": "회/60초",
        "direction": "higher",
        "grade1": 43,
        "grade2": 33,
        "grade3": 23,
    },
    "유연성": {
        "unit": "cm",
        "direction": "higher",
        "grade1": 19.5,
        "grade2": 13.5,
        "grade3": 7.5,
    },
    "왕복오래달리기": {
        "unit": "회",
        "direction": "higher",
        "grade1": 52,
        "grade2": 37,
        "grade3": 22,
    },
    "제자리멀리뛰기": {
        "unit": "cm",
        "direction": "higher",
        "grade1": 190,
        "grade2": 165,
        "grade3": 140,
    },
    "10m왕복달리기": {
        "unit": "초",
        "direction": "lower",  # 낮을수록 좋음
        "grade1": 7.9,
        "grade2": 8.6,
        "grade3": 9.3,
    },
    "BMI": {
        "unit": "kg/m²",
        "direction": "range",
        "grade1_low": 18.5,
        "grade1_high": 22.9,
        "grade2_low": 17.0,
        "grade2_high": 24.9,
    },
}


def calc_item_grade(item_name, value):
    """항목별 등급 계산"""
    criteria = GRADE_CRITERIA[item_name]

    if criteria["direction"] == "range":  # BMI
        if criteria["grade1_low"] <= value <= criteria["grade1_high"]:
            return 1
        elif criteria["grade2_low"] <= value <= criteria["grade2_high"]:
            return 2
        else:
            return 3
    elif criteria["direction"] == "higher":
        if value >= criteria["grade1"]:
            return 1
        elif value >= criteria["grade2"]:
            return 2
        elif value >= criteria["grade3"]:
            return 3
        else:
            return 4  # 등급 외
    else:  # lower (10m왕복달리기)
        if value <= criteria["grade1"]:
            return 1
        elif value <= criteria["grade2"]:
            return 2
        elif value <= criteria["grade3"]:
            return 3
        else:
            return 4


def calc_overall_grade(grades):
    """종합 등급 계산 (평균 기반)"""
    valid = [g for g in grades if g <= 3]
    if not valid:
        return 4
    avg = sum(valid) / len(valid)
    if avg <= 1.5:
        return 1
    elif avg <= 2.3:
        return 2
    elif avg <= 3.0:
        return 3
    return 4


# ========================================
# 운동 가이드 데이터
# ========================================
EXERCISE_GUIDES = {
    "악력": {
        "target": "30kg 이상",
        "exercises": [
            "악력기 사용 (하루 3세트 × 20회)",
            "수건 짜기 운동",
            "손가락 벌리기 + 고무밴드 저항",
            "매달리기 (30초 × 3세트)",
            "암벽등반 (보울더링)",
        ],
        "tips": "양손 균형있게 훈련! 매일 5분이면 충분합니다.",
        "weekly": 7,
    },
    "윗몸일으키기": {
        "target": "43회/60초 이상",
        "exercises": [
            "크런치 (20회 × 3세트)",
            "플랭크 (1분 × 3세트)",
            "레그레이즈 (15회 × 3세트)",
            "러시안 트위스트 (20회 × 3세트)",
            "시저크런치 (속도 훈련)",
        ],
        "tips": "반동 없이 복근 힘만으로! 속도 훈련도 병행하세요.",
        "weekly": 4,
    },
    "유연성": {
        "target": "19.5cm 이상",
        "exercises": [
            "햄스트링 스트레칭 (아침/저녁 각 30초)",
            "고관절 스트레칭",
            "요가 다운독, 전굴 자세",
            "폼롤러 마사지",
            "나비자세 스트레칭",
        ],
        "tips": "따뜻한 상태에서 효과적! 샤워 후 스트레칭 추천!",
        "weekly": 7,
    },
    "왕복오래달리기": {
        "target": "52회 이상",
        "exercises": [
            "인터벌 달리기 (30초 전력 + 30초 휴식) × 10",
            "계단 오르기 (10층 × 3회)",
            "점프 스쿼트 (20회 × 3세트)",
            "버피테스트 (10회 × 3세트)",
            "줄넘기 3분 × 5세트",
        ],
        "tips": "심폐지구력은 최소 4주! 점진적으로 강도 높이세요.",
        "weekly": 3,
    },
    "제자리멀리뛰기": {
        "target": "190cm 이상",
        "exercises": [
            "스쿼트 점프 (15회 × 3세트)",
            "런지 점프 (10회 × 3세트)",
            "박스 점프",
            "줄넘기 이중 뛰기",
            "전력 질주 30m × 5회",
        ],
        "tips": "팔 스윙으로 추진력! 착지 시 무릎 살짝 굽히기!",
        "weekly": 3,
    },
    "10m왕복달리기": {
        "target": "7.9초 이하",
        "exercises": [
            "래더 드릴 (사다리 훈련)",
            "콘 터치 훈련",
            "셔플 스텝 좌우 반복",
            "방향 전환 연습",
            "스프린트 + 급정거 반복",
        ],
        "tips": "방향 전환 시 무게 중심 낮추기! 발을 빠르게!",
        "weekly": 3,
    },
}


# ========================================
# 수영 가이드 데이터
# ========================================
SWIMMING_GUIDE = {
    "준비물": [
        "수영복 (원피스형 추천)",
        "수영모 (실리콘 추천)",
        "물안경",
        "수건",
        "여분 속옷",
        "드라이기 (탈의실에 없을 수 있음)"
    ],
    "자유형 기본": [
        "1. 스트림라인 자세로 벽 차고 출발",
        "2. 팔 돌리기: 물 밖으로 손 빼서 앞으로 던지기",
        "3. 발차기: 허벅지부터 작게 빠르게",
        "4. 호흡: 3스트로크마다 옆으로 고개 돌려 호흡",
        "5. 25m 완영이 목표 (속도보다 완주)"
    ],
    "초보자 팁": [
        "처음엔 킥판 잡고 발차기 연습",
        "호흡이 어려우면 2스트로크마다 해도 OK",
        "긴장하면 몸이 가라앉으니 릴렉스",
        "중간에 쉬어도 되니 포기하지 말 것",
        "실제 테스트는 수영장 얕은 곳에서 진행"
    ],
    "연습 계획": {
        "1주차": "물 적응, 발차기 연습 (킥판)",
        "2주차": "팔 동작 추가, 호흡 연습",
        "3주차": "전체 동작 연결, 10m 완영",
        "4주차": "25m 완영 도전, 속도 조절"
    }
}

SWIMMING_AIRLINES = {
    "대한항공": {
        "required": True,
        "distance": "25m",
        "style": "자유형",
        "time_limit": "제한 없음 (완영 필수)",
        "note": "물안경, 수영모 착용 가능. 체력검정 단계에서 실시",
        "stage": "체력검정 단계"
    },
    "아시아나항공": {
        "required": True,
        "distance": "25m",
        "style": "자유형 또는 배영",
        "time_limit": "제한 없음",
        "note": "최종 면접 단계 (건강검진/수영Test)에서 실시",
        "stage": "건강검진/수영Test 단계"
    },
}


# ========================================
# 합격자 후기 데이터
# ========================================
SUCCESS_STORIES = [
    {
        "airline": "에어프레미아",
        "author": "2025 하반기 합격자 A",
        "grade": "1등급",
        "period": "3개월 준비",
        "content": """에어프레미아는 자체 체력측정이 있어서 국민체력100과는 좀 달라요.
버피테스트가 핵심이에요! 1분에 15개 이상은 해야 안심할 수 있습니다.
제가 한 건: 매일 아침 버피 10개로 시작 → 2주마다 5개씩 추가.
3개월 차에는 1분에 20개 가능했어요. 악력도 중요한데, 저는 악력기를
회사 다니면서 틈틈이 했더니 28kg → 33kg으로 올랐습니다.""",
        "tips": ["버피테스트 매일 연습 필수", "악력기 항상 가지고 다니기", "유연성은 샤워 후 스트레칭으로"],
    },
    {
        "airline": "파라타항공",
        "author": "2025 상반기 합격자 B",
        "grade": "2등급",
        "period": "2개월 준비",
        "content": """파라타항공은 국민체력100 결과서를 서류에 제출해야 해요.
저는 처음에 3등급이었는데 2개월 만에 2등급 받았어요.
가장 어려웠던 건 왕복오래달리기(셔틀런)! 처음에 25회밖에 못했는데
인터벌 달리기를 주 3회 하니까 45회까지 올랐습니다.
유연성이 제일 쉬워요. 매일 스트레칭만 하면 2주 만에 1등급 가능!""",
        "tips": ["셔틀런은 인터벌 달리기로 준비", "유연성은 가성비 최고", "악력기 + 매달리기 병행"],
    },
    {
        "airline": "이스타항공",
        "author": "2025 하반기 합격자 C",
        "grade": "자체 측정 통과",
        "period": "6주 준비",
        "content": """이스타항공은 오래달리기, 높이뛰기, 목소리 데시벨을 봐요.
오래달리기는 1.2km를 7분 안에 뛰어야 했어요.
저는 원래 운동을 안 해서 처음엔 9분 걸렸는데, 매일 조깅 + 주 2회 인터벌로
6주 만에 6분 30초까지 줄였습니다.
높이뛰기는 제자리멀리뛰기와 비슷해서 점프 운동 하시면 됩니다.""",
        "tips": ["매일 조깅 30분 필수", "인터벌로 심폐 능력 향상", "발성 연습도 함께"],
    },
    {
        "airline": "대한항공",
        "author": "2025 상반기 합격자 D",
        "grade": "수영 25m 완영",
        "period": "2개월 수영 배움",
        "content": """대한항공은 수영 25m만 하면 돼요. 근데 이게 수영 못하는 사람한테는 진짜 벽이에요.
저는 완전 물 무서워하는 사람이었는데, 동네 수영장에서 2개월 배웠어요.
첫 달: 물 적응 + 호흡법, 둘째 달: 자유형 25m 연습.
팁은 '킥보드 많이 하기'예요. 다리가 안 가라앉으면 반은 성공입니다.
면접 당일에는 긴장돼서 좀 버벅거렸는데 완주만 하면 통과입니다.""",
        "tips": ["물 적응이 1순위", "킥보드로 하체 킥 연습", "완주가 목표 (속도 무관)"],
    },
    {
        "airline": "아시아나항공",
        "author": "2024 하반기 합격자 E",
        "grade": "수영 테스트 통과",
        "period": "3개월 수영 연습",
        "content": """아시아나도 수영이 있어요. 대한항공이랑 비슷한데
건강검진 단계에서 갑자기 하라고 해서 당황하는 분들이 많아요.
미리 준비하세요! 자유형이든 배영이든 25m만 가면 됩니다.
저는 배영으로 했는데, 얼굴 안 담그니까 호흡이 편했어요.
체력인증은 따로 안 보지만, 면접에서 '체력 관리 어떻게 하세요?' 질문은 나와요.
국민체력100 인증 있으면 어필하기 좋습니다!""",
        "tips": ["배영도 가능 (호흡 편함)", "미리 연습 필수", "면접에서 체력 관리 질문 대비"],
    },
    {
        "airline": "일반 체력 준비",
        "author": "2등급 달성 후기 F",
        "grade": "3등급 → 1등급",
        "period": "4개월 준비",
        "content": """처음 측정했을 때 3등급이었어요. 악력 22kg, 셔틀런 20회, 유연성 8cm...
4개월 계획을 세웠어요:
1개월차: 기초체력 (매일 30분 운동 습관 만들기)
2개월차: 약한 항목 집중 (셔틀런, 악력)
3개월차: 전체 항목 고루 훈련
4개월차: 모의 테스트 + 컨디션 조절

결과: 악력 34kg, 셔틀런 55회, 유연성 22cm → 1등급!
핵심은 '매일 조금씩'이에요. 한 번에 많이 하면 다음 날 못 해요.""",
        "tips": ["매일 30분 습관화가 핵심", "약한 항목 먼저 집중", "무리하지 말고 꾸준히"],
    },
]


# ========================================
# CSS
# ========================================
st.markdown("""
<style>
.grade-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    margin: 10px 0;
}
.grade-1 { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.grade-2 { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
.grade-3 { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
.exercise-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    border-left: 4px solid #667eea;
}
.airline-req {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 16px;
    margin: 8px 0;
}
.story-card {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
    border-left: 4px solid #f093fb;
}
.result-good { color: #28a745; font-weight: bold; }
.result-warn { color: #ffc107; font-weight: bold; }
.result-bad { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ========================================
# 메인
# ========================================
st.title("국민체력100 가이드")
st.markdown("체력 등급 계산부터 맞춤 훈련, 합격자 후기까지 한 곳에서!")

st.info("**국민체력100**은 국민체육진흥공단에서 운영하는 체력인증 시스템입니다. 전국 인증센터에서 무료 측정 가능!")

# 탭 구성
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
 " 등급 계산기",
 "️ 맞춤 훈련",
 " 훈련 기록",
 "⏰ D-Day 플랜",
 " 합격자 후기",
 "️ 항공사 요구사항",
 " 수영 준비",
])


# ========================================
# 탭1: 등급 계산기
# ========================================
with tab1:
    st.markdown("### 내 체력 등급 계산기")
    st.markdown("현재 수치를 입력하면 항목별 등급과 종합 등급을 바로 확인할 수 있어요!")

    st.markdown("---")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("#### 내 수치 입력 (20대 여성 기준)")

        cols = st.columns(2)
        with cols[0]:
            v_grip = st.number_input(" 악력 (kg)", min_value=0.0, max_value=80.0, value=25.0, step=0.5, key="calc_grip")
            v_situp = st.number_input(" 윗몸일으키기 (회/60초)", min_value=0, max_value=100, value=30, step=1, key="calc_situp")
            v_flex = st.number_input(" 유연성 (cm)", min_value=-20.0, max_value=50.0, value=12.0, step=0.5, key="calc_flex")
            v_bmi = st.number_input("️ BMI (kg/m²)", min_value=10.0, max_value=50.0, value=21.0, step=0.1, key="calc_bmi")

        with cols[1]:
            v_shuttle = st.number_input(" 왕복오래달리기 (회)", min_value=0, max_value=150, value=35, step=1, key="calc_shuttle")
            v_jump = st.number_input(" 제자리멀리뛰기 (cm)", min_value=0, max_value=350, value=160, step=1, key="calc_jump")
            v_agility = st.number_input(" 10m왕복달리기 (초)", min_value=5.0, max_value=20.0, value=8.5, step=0.1, key="calc_agility")

        if st.button("등급 계산하기", type="primary", use_container_width=True):
            values = {
                "악력": v_grip,
                "윗몸일으키기": v_situp,
                "유연성": v_flex,
                "왕복오래달리기": v_shuttle,
                "제자리멀리뛰기": v_jump,
                "10m왕복달리기": v_agility,
                "BMI": v_bmi,
            }

            grades = {}
            for item, val in values.items():
                grades[item] = calc_item_grade(item, val)

            overall = calc_overall_grade(list(grades.values()))
            st.session_state.calc_result = {"values": values, "grades": grades, "overall": overall}

    with col_right:
        st.markdown("#### 등급 기준")
        st.caption("20~24세 여성 기준")
        st.markdown("""
        | 항목 | 1등급 | 2등급 |
        |------|-------|-------|
        | 악력 | ≥31.5 | ≥26.5 |
        | 윗몸 | ≥43회 | ≥33회 |
        | 유연성 | ≥19.5 | ≥13.5 |
        | 셔틀런 | ≥52회 | ≥37회 |
        | 멀리뛰기 | ≥190 | ≥165 |
        | 10m달리기 | ≤7.9초 | ≤8.6초 |
        | BMI | 18.5~22.9 | 17~24.9 |
        """)

    # 결과 표시
    if "calc_result" in st.session_state:
        result = st.session_state.calc_result
        grades = result["grades"]
        overall = result["overall"]

        st.markdown("---")
        st.markdown("### 측정 결과")

        # 종합 등급
        grade_colors = {1: "#f093fb", 2: "#4facfe", 3: "#43e97b", 4: "#dc3545"}
        grade_names = {1: "1등급 (매우 우수)", 2: "2등급 (우수)", 3: "3등급 (보통)", 4: "등급 외"}
        grade_emoji = {1: "", 2: "", 3: "", 4: ""}

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {grade_colors[overall]}40, {grade_colors[overall]}20);
                    border: 3px solid {grade_colors[overall]}; border-radius: 20px; padding: 30px; text-align: center; margin: 10px 0;">
            <div style="font-size: 50px;">{grade_emoji[overall]}</div>
            <div style="font-size: 24px; font-weight: bold;">종합 {grade_names[overall]}</div>
        </div>
        """, unsafe_allow_html=True)

        # 항목별 결과
        st.markdown("#### 항목별 상세")
        items = list(grades.items())
        cols = st.columns(4)
        for i, (item, grade) in enumerate(items):
            with cols[i % 4]:
                color = grade_colors[grade]
                val = result["values"][item]
                unit = GRADE_CRITERIA[item]["unit"]
                st.markdown(f"""
                <div style="background: {color}20; border: 2px solid {color}; border-radius: 12px;
                            padding: 12px; text-align: center; margin: 5px 0; min-height: 110px;">
                    <div style="font-size: 12px; color: #666;">{item}</div>
                    <div style="font-size: 20px; font-weight: bold;">{val}{unit}</div>
                    <div style="font-size: 14px; color: {color}; font-weight: bold;">{grade}등급</div>
                </div>
                """, unsafe_allow_html=True)

        # 부족한 항목 안내
        weak_items = [item for item, grade in grades.items() if grade >= 3]
        if weak_items:
            st.markdown("---")
            st.warning(f"️ **집중 필요 항목:** {', '.join(weak_items)}")
            for item in weak_items:
                criteria = GRADE_CRITERIA[item]
                current = result["values"][item]
                if criteria["direction"] == "higher":
                    target = criteria["grade2"]
                    diff = target - current
                    st.caption(f"  → {item}: 현재 {current} → 2등급까지 **{diff:.1f}** 더 필요")
                elif criteria["direction"] == "lower":
                    target = criteria["grade2"]
                    diff = current - target
                    st.caption(f"  → {item}: 현재 {current}초 → 2등급까지 **{diff:.1f}초** 줄여야 함")
        else:
            st.success("모든 항목이 양호합니다! 1등급을 목표로 더 노력해보세요!")

        # 기록 저장 버튼
        if st.button("이 결과를 훈련 기록에 저장", use_container_width=True):
            history = load_json(FITNESS_HISTORY_FILE)
            record = {
                "type": "measurement",
                "values": result["values"],
                "grades": grades,
                "overall": overall,
                "timestamp": datetime.now().isoformat()
            }
            history.append(record)
            save_json(FITNESS_HISTORY_FILE, history)
            st.success("기록이 저장되었습니다! '훈련 기록' 탭에서 확인하세요.")


# ========================================
# 탭2: 맞춤 훈련 계획
# ========================================
with tab2:
    st.markdown("### ️ 맞춤 훈련 계획")

    # 약한 항목 기반 추천
    if "calc_result" in st.session_state:
        grades = st.session_state.calc_result["grades"]
        weak = [(item, grade) for item, grade in grades.items() if grade >= 2 and item != "BMI"]
        weak.sort(key=lambda x: x[1], reverse=True)

        if weak:
            st.success("등급 계산 결과를 바탕으로 약한 항목 순서대로 훈련을 추천합니다!")
            priority_items = [item for item, _ in weak]
        else:
            st.info("모든 항목이 1등급입니다! 유지 훈련을 추천합니다.")
            priority_items = list(EXERCISE_GUIDES.keys())
    else:
        st.info("'등급 계산기' 탭에서 먼저 수치를 입력하면 맞춤 추천을 받을 수 있어요!")
        priority_items = list(EXERCISE_GUIDES.keys())

    st.markdown("---")

    # 집중 훈련 항목 선택
    selected_items = st.multiselect(
        " 집중 훈련할 항목 선택",
        options=list(EXERCISE_GUIDES.keys()),
        default=priority_items[:3] if len(priority_items) >= 3 else priority_items,
    )

    if selected_items:
        st.markdown("---")

        for item in selected_items:
            guide = EXERCISE_GUIDES[item]
            emoji_map = {"악력": "", "윗몸일으키기": "", "유연성": "",
                         "왕복오래달리기": "‍️", "제자리멀리뛰기": "", "10m왕복달리기": ""}
            emoji = emoji_map.get(item, "️")

            with st.expander(f"{emoji} {item} (목표: {guide['target']}, 주 {guide['weekly']}회)", expanded=True):
                st.markdown(f"**추천 운동:**")
                for ex in guide["exercises"]:
                    st.markdown(f"- {ex}")
                st.info(f" **팁:** {guide['tips']}")

        # 주간 스케줄 생성
        st.markdown("---")
        st.markdown("#### 맞춤 주간 스케줄")

        days = ["월", "화", "수", "목", "금", "토", "일"]
        schedule = {d: [] for d in days}

        # 선택 항목을 요일에 분배
        daily_items = ["유연성"] if "유연성" in selected_items else []
        weekly_items = [i for i in selected_items if i != "유연성"]

        for d in days:
            if d == "일":
                schedule[d] = ["완전 휴식"]
            elif d == "수":
                schedule[d] = ["가벼운 스트레칭 + 휴식"]
            else:
                schedule[d] = daily_items.copy()

        # 나머지 항목을 분배
        workout_days = ["월", "화", "목", "금", "토"]
        for idx, item in enumerate(weekly_items):
            target_days = [workout_days[i % len(workout_days)] for i in range(idx, idx + min(EXERCISE_GUIDES[item]["weekly"], 3))]
            for d in target_days:
                if item not in schedule[d]:
                    schedule[d].append(item)

        cols = st.columns(7)
        for i, day in enumerate(days):
            with cols[i]:
                items_str = "\n".join([f"• {x}" for x in schedule[day]])
                is_rest = "휴식" in " ".join(schedule[day])
                bg = "#f0f0f0" if is_rest else "#667eea20"
                st.markdown(f"""
                <div style="background: {bg}; border-radius: 10px; padding: 10px; text-align: center; min-height: 120px;">
                    <div style="font-weight: bold; margin-bottom: 5px;">{day}</div>
                    <div style="font-size: 11px; text-align: left;">{'<br>'.join(['• '+x for x in schedule[day]])}</div>
                </div>
                """, unsafe_allow_html=True)

    # 전체 운동 가이드 (기존 내용)
    st.markdown("---")
    st.markdown("#### 전체 운동 가이드")

    with st.expander("에어프레미아 체력측정 대비 (버피테스트)"):
        st.markdown("""
        **버피테스트 동작 순서:**
        1. 서서 시작
        2. 스쿼트 자세로 손 바닥 짚기
        3. 플랭크 자세로 점프
        4. 푸시업 1회
        5. 다리 당겨 스쿼트 자세
        6. 점프하며 손 위로

        **훈련:** 1분에 15개 목표로 매일 3세트!
        """)

    with st.expander("주간 운동 계획 예시 (기본형)"):
        st.markdown("""
        | 요일 | 운동 내용 | 시간 |
        |------|----------|------|
        | **월** | 근력 (악력, 윗몸일으키기) + 유연성 | 40분 |
        | **화** | 심폐지구력 (인터벌 달리기) | 30분 |
        | **수** | 휴식 + 가벼운 스트레칭 | 20분 |
        | **목** | 순발력 (점프 운동) + 민첩성 | 40분 |
        | **금** | 심폐지구력 (셔틀런 연습) | 30분 |
        | **토** | 전체 항목 모의 테스트 | 60분 |
        | **일** | 완전 휴식 | - |
        """)


# ========================================
# 탭3: 훈련 기록 트래커
# ========================================
with tab3:
    st.markdown("### 훈련 기록 트래커")
    st.markdown("운동 기록을 남기고 성장 과정을 확인하세요!")

    # 운동 기록 입력
    st.markdown("#### ️ 오늘의 운동 기록")

    record_type = st.radio("기록 유형", ["운동 기록", "체력 측정 결과"], horizontal=True, key="record_type")

    if record_type == "운동 기록":
        cols = st.columns(2)
        with cols[0]:
            ex_items = st.multiselect("운동한 항목", list(EXERCISE_GUIDES.keys()), key="ex_items")
            ex_duration = st.number_input("운동 시간 (분)", min_value=5, max_value=300, value=30, step=5, key="ex_dur")
        with cols[1]:
            ex_intensity = st.select_slider("운동 강도", options=["가볍게", "보통", "열심히", "최대"], value="보통", key="ex_int")
            ex_memo = st.text_input("메모 (선택)", key="ex_memo", placeholder="오늘 느낀 점이나 특이사항...")

        if st.button("운동 기록 저장", use_container_width=True, key="save_exercise"):
            if ex_items:
                history = load_json(FITNESS_HISTORY_FILE)
                record = {
                    "type": "exercise",
                    "items": ex_items,
                    "duration": ex_duration,
                    "intensity": ex_intensity,
                    "memo": ex_memo,
                    "timestamp": datetime.now().isoformat()
                }
                history.append(record)
                save_json(FITNESS_HISTORY_FILE, history)
                st.success("운동 기록이 저장되었습니다!")
            else:
                st.warning("운동한 항목을 선택해주세요.")

    else:  # 체력 측정 결과
        st.caption("실제 측정한 수치를 입력하세요.")
        cols = st.columns(3)
        with cols[0]:
            m_grip = st.number_input("악력 (kg)", min_value=0.0, max_value=80.0, value=25.0, step=0.5, key="m_grip")
            m_situp = st.number_input("윗몸일으키기 (회)", min_value=0, max_value=100, value=30, step=1, key="m_situp")
        with cols[1]:
            m_flex = st.number_input("유연성 (cm)", min_value=-20.0, max_value=50.0, value=12.0, step=0.5, key="m_flex")
            m_shuttle = st.number_input("셔틀런 (회)", min_value=0, max_value=150, value=35, step=1, key="m_shuttle")
        with cols[2]:
            m_jump = st.number_input("멀리뛰기 (cm)", min_value=0, max_value=350, value=160, step=1, key="m_jump")
            m_agility = st.number_input("10m달리기 (초)", min_value=5.0, max_value=20.0, value=8.5, step=0.1, key="m_agility")

        if st.button("측정 결과 저장", use_container_width=True, key="save_measurement"):
            values = {
                "악력": m_grip, "윗몸일으키기": m_situp, "유연성": m_flex,
                "왕복오래달리기": m_shuttle, "제자리멀리뛰기": m_jump, "10m왕복달리기": m_agility,
            }
            grades = {item: calc_item_grade(item, val) for item, val in values.items()}
            overall = calc_overall_grade(list(grades.values()))

            history = load_json(FITNESS_HISTORY_FILE)
            record = {
                "type": "measurement",
                "values": values,
                "grades": grades,
                "overall": overall,
                "timestamp": datetime.now().isoformat()
            }
            history.append(record)
            save_json(FITNESS_HISTORY_FILE, history)
            st.success(f" 측정 결과가 저장되었습니다! (종합 {overall}등급)")

    # 기록 대시보드
    st.markdown("---")
    st.markdown("#### 나의 훈련 현황")

    history = load_json(FITNESS_HISTORY_FILE)

    if history:
        exercises = [h for h in history if h["type"] == "exercise"]
        measurements = [h for h in history if h["type"] == "measurement"]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 운동 횟수", f"{len(exercises)}회")
        with col2:
            total_min = sum(h.get("duration", 0) for h in exercises)
            st.metric("총 운동 시간", f"{total_min}분")
        with col3:
            st.metric("체력 측정", f"{len(measurements)}회")
        with col4:
            if measurements:
                latest = measurements[-1]
                st.metric("최근 종합등급", f"{latest['overall']}등급")

        # 측정 추이 그래프
        if len(measurements) >= 2:
            st.markdown("#####  체력 측정 추이")
            import pandas as pd

            chart_data = []
            for m in measurements:
                row = {"날짜": m["timestamp"][:10]}
                for item, val in m["values"].items():
                    row[item] = val
                chart_data.append(row)

            df = pd.DataFrame(chart_data)
            df["날짜"] = pd.to_datetime(df["날짜"])
            df = df.set_index("날짜")

            # 등급이 높을수록 좋은 항목만 표시 (10m달리기 제외)
            show_cols = [c for c in df.columns if c != "10m왕복달리기"]
            if show_cols:
                st.line_chart(df[show_cols])

        # 최근 기록
        with st.expander("최근 기록 (최근 20건)"):
            for h in reversed(history[-20:]):
                ts = h.get("timestamp", "")[:10]
                if h["type"] == "exercise":
                    items = ", ".join(h.get("items", []))
                    dur = h.get("duration", 0)
                    intensity = h.get("intensity", "")
                    memo = h.get("memo", "")
                    memo_str = f" | {memo}" if memo else ""
                    st.caption(f" {ts} | {items} | {dur}분 | {intensity}{memo_str}")
                else:
                    overall = h.get("overall", "?")
                    st.caption(f" {ts} | 체력 측정 | 종합 {overall}등급")
    else:
        st.info("아직 기록이 없습니다. 위에서 운동 기록이나 측정 결과를 입력해보세요!")


# ========================================
# 탭4: D-Day 기반 주간 목표
# ========================================
with tab4:
    st.markdown("### ⏰ D-Day 훈련 플랜")
    st.markdown("체력 시험일을 설정하고, 남은 기간에 맞는 단계별 플랜을 받으세요!")

    # D-Day 설정
    dday_data = load_dday()

    col1, col2 = st.columns([2, 1])
    with col1:
        target_date = st.date_input(
            " 체력 시험 예정일",
            value=datetime.now().date() + timedelta(days=60),
            min_value=datetime.now().date(),
            key="dday_date"
        )
        target_airline = st.selectbox(
            "️ 목표 항공사",
            ["파라타항공 (국민체력100 필수)", "에어프레미아 (자체 측정)", "이스타항공 (자체 체력시험)",
             "대한항공 (수영)", "아시아나항공 (수영)", "기타 (일반 체력 준비)"],
            key="dday_airline"
        )
        target_grade = st.selectbox(" 목표 등급", ["1등급", "2등급"], key="dday_grade")

    with col2:
        if st.button("D-Day 저장", use_container_width=True, type="primary"):
            dday_info = {
                "target_date": str(target_date),
                "airline": target_airline,
                "grade": target_grade,
                "created": datetime.now().isoformat()
            }
            save_dday(dday_info)
            dday_data = dday_info
            st.success("D-Day가 설정되었습니다!")

    # D-Day 표시
    if dday_data:
        target_dt = datetime.strptime(dday_data["target_date"], "%Y-%m-%d").date()
        remaining = (target_dt - datetime.now().date()).days

        if remaining > 0:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white;
                        border-radius: 20px; padding: 30px; text-align: center; margin: 20px 0;">
                <div style="font-size: 18px;"> {dday_data.get('airline', '')}</div>
                <div style="font-size: 60px; font-weight: bold;">D-{remaining}</div>
                <div style="font-size: 16px;">{dday_data['target_date']} | 목표: {dday_data.get('grade', '2등급')}</div>
            </div>
            """, unsafe_allow_html=True)

            # 단계별 플랜 생성
            st.markdown("---")
            st.markdown("#### 단계별 훈련 플랜")

            if remaining >= 90:
                phases = [
                    {"name": "1단계: 기초 체력 (4주)", "desc": "운동 습관 만들기. 매일 30분 가벼운 운동으로 시작", "focus": "유연성, 가벼운 근력 운동"},
                    {"name": "2단계: 약점 집중 (4주)", "desc": "가장 약한 항목 2~3개를 집중 훈련", "focus": "약한 항목 집중 + 심폐지구력"},
                    {"name": "3단계: 전체 강화 (3주)", "desc": "모든 항목을 고루 훈련. 강도 높이기", "focus": "전체 항목 균형 훈련"},
                    {"name": "4단계: 실전 대비 (2주)", "desc": "모의 테스트 주 2회. 컨디션 조절", "focus": "모의 테스트 + 충분한 휴식"},
                ]
            elif remaining >= 60:
                phases = [
                    {"name": "1단계: 기초+약점 (3주)", "desc": "기초 체력 만들면서 약한 항목 파악", "focus": "약한 항목 2개 + 매일 유연성"},
                    {"name": "2단계: 집중 강화 (3주)", "desc": "약한 항목 집중! 강도 높이기", "focus": "약한 항목 강화 + 심폐지구력"},
                    {"name": "3단계: 실전 대비 (2주)", "desc": "모의 테스트 + 컨디션 조절", "focus": "전체 모의 테스트 + 휴식 관리"},
                ]
            elif remaining >= 30:
                phases = [
                    {"name": "1단계: 집중 훈련 (2주)", "desc": "약한 항목 최우선! 매일 40분 이상", "focus": "가장 약한 2개 항목 집중"},
                    {"name": "2단계: 마무리 (1주)", "desc": "전체 항목 모의 테스트 + 컨디션 관리", "focus": "모의 테스트 + 충분한 수면"},
                    {"name": "D-3~D-1", "desc": "가벼운 스트레칭만. 무리하지 않기!", "focus": "컨디션 최적화"},
                ]
            else:
                phases = [
                    {"name": "집중 훈련기", "desc": f"남은 {remaining}일, 매일 30~40분 약한 항목 집중!", "focus": "가장 약한 항목에 올인"},
                    {"name": "D-3~D-1", "desc": "가벼운 스트레칭만. 충분한 수면!", "focus": "컨디션 최적화"},
                ]

            for i, phase in enumerate(phases):
                col_icon = "" if i == 0 else "" if i < len(phases) - 1 else ""
                st.markdown(f"""
                <div style="background: #f8f9fa; border-radius: 12px; padding: 16px; margin: 8px 0; border-left: 4px solid #667eea;">
                    <div style="font-weight: bold;">{col_icon} {phase['name']}</div>
                    <div style="margin: 5px 0; color: #555;">{phase['desc']}</div>
                    <div style="font-size: 13px; color: #667eea;"> 핵심: {phase['focus']}</div>
                </div>
                """, unsafe_allow_html=True)

            # 이번 주 할 일
            st.markdown("---")
            st.markdown("#### 이번 주 할 일")

            current_phase = 0
            if remaining >= 90:
                week_in = (90 - remaining) // 7
                if week_in < 4:
                    current_phase = 0
                elif week_in < 8:
                    current_phase = 1
                elif week_in < 11:
                    current_phase = 2
                else:
                    current_phase = 3

            weekly_tasks = [
                f"유연성 스트레칭 매일 10분",
                f"선택 항목 훈련 주 4회 (각 30분)",
                f"심폐지구력 운동 주 2회",
                f"충분한 수면 (7시간 이상)",
                f"단백질 식단 관리",
            ]

            for task in weekly_tasks:
                st.checkbox(task, key=f"weekly_{task}")

        elif remaining == 0:
            st.success("오늘이 시험일입니다! 파이팅!")
        else:
            st.info("시험일이 지났습니다. 새로운 D-Day를 설정해보세요.")
    else:
        st.info("위에서 체력 시험 예정일을 설정하고 'D-Day 저장' 버튼을 눌러주세요!")


# ========================================
# 탭5: 합격자 체력 후기
# ========================================
with tab5:
    st.markdown("### 합격자 체력 준비 후기")
    st.markdown("실제 합격자들의 체력 준비 경험을 참고하세요!")

    # 필터
    airlines = list(set(s["airline"] for s in SUCCESS_STORIES))
    filter_airline = st.selectbox("️ 항공사 필터", ["전체"] + airlines, key="story_filter")

    st.markdown("---")

    filtered = SUCCESS_STORIES if filter_airline == "전체" else [s for s in SUCCESS_STORIES if s["airline"] == filter_airline]

    for story in filtered:
        with st.expander(f"️ {story['airline']} | {story['author']} | {story['grade']} ({story['period']})"):
            st.markdown(f"""
            <div class="story-card">
                <div style="white-space: pre-wrap; line-height: 1.8;">{story['content']}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("** 핵심 팁:**")
            for tip in story["tips"]:
                st.markdown(f"- {tip}")

    st.markdown("---")
    st.caption("※ 위 후기는 실제 합격자 경험을 바탕으로 재구성한 내용입니다. 개인차가 있을 수 있습니다.")


# ========================================
# 탭6: 항공사별 요구사항 + 인증센터
# ========================================
with tab6:
    st.markdown("### ️ 항공사별 체력 요구사항")

    st.warning("️ 체력 기준은 채용 시기마다 변경될 수 있습니다. 반드시 공식 채용공고를 확인하세요.")

    # 체력 필수 항공사
    st.markdown("#### ️ 체력측정 필수 항공사")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="airline-req">
            <h4> 파라타항공</h4>
            <p><strong>요구사항:</strong> 국민체력100 체력평가 결과서 제출 <span style="color: #dc3545; font-weight: bold;">필수</span></p>
            <p><strong>제출 시기:</strong> 서류전형 시</p>
            <p><strong>권장 등급:</strong> 2등급 이상</p>
            <hr>
            <small> 신생 항공사로 체력 기준을 엄격하게 적용</small>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="airline-req">
            <h4> 에어프레미아</h4>
            <p><strong>요구사항:</strong> 자체 체력측정 실시</p>
            <p><strong>측정 항목:</strong> 악력, 윗몸일으키기, 버피테스트, 유연성, 암리치</p>
            <p><strong>측정 시기:</strong> 컬처핏 면접 시</p>
            <hr>
            <small> 장거리 노선 특화로 체력 중시</small>
        </div>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="airline-req">
            <h4> 이스타항공</h4>
            <p><strong>요구사항:</strong> 자체 체력시험 실시</p>
            <p><strong>측정 항목:</strong> 오래달리기, 높이뛰기, 목소리 데시벨</p>
            <p><strong>측정 시기:</strong> 체력TEST 단계</p>
            <hr>
            <small> 2025년부터 채용 절차에 체력시험 도입</small>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="airline-req">
            <h4> 대한항공</h4>
            <p><strong>요구사항:</strong> 수영 25m 완영 <span style="color: #dc3545; font-weight: bold;">필수</span></p>
            <p><strong>측정 시기:</strong> 건강검진 단계</p>
            <p><strong>기타:</strong> 별도 체력인증 불필요</p>
            <hr>
            <small> 수영 능력만 별도 검증</small>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 체력 권장 항공사
    st.markdown("#### 체력 우수자 우대 항공사")

    st.markdown("""
    | 항공사 | 체력 관련 사항 | 비고 |
    |--------|---------------|------|
    | 아시아나항공 | 수영 테스트 포함 | 건강검진 단계 |
    | 진에어 | 별도 체력측정 없음 | 기본 체력 권장 |
    | 제주항공 | 별도 체력측정 없음 | 기본 체력 권장 |
    | 티웨이항공 | 별도 체력측정 없음 | 기본 체력 권장 |
    | 에어부산 | 별도 체력측정 없음 | 기본 체력 권장 |
    | 에어서울 | 별도 체력측정 없음 | 기본 체력 권장 |
    | 에어로케이 | 안전분야 자격 우대 | 체력 관련 자격 우대 |
    """)

    st.success("**팁:** 체력측정이 필수가 아니더라도, 국민체력100 인증을 받아두면 자기소개서와 면접에서 어필할 수 있습니다!")

    # 인증센터 정보
    st.markdown("---")
    st.markdown("#### 국민체력100 인증센터")

    st.info("전국 300여개 인증센터에서 **무료**로 체력측정이 가능합니다!")

    with st.expander("측정 절차 및 센터 정보"):
        st.markdown("""
        ####  측정 절차
        1. **예약**: 국민체력100 홈페이지/앱에서 가까운 센터 예약
        2. **방문**: 예약 시간에 센터 방문 (운동복, 실내화 지참)
        3. **측정**: 7개 항목 체력측정 (약 1시간)
        4. **결과**: 측정 후 즉시 결과 확인 + 인증서 발급

        ####  비용
        - **무료** (1회/연)
        - 추가 측정 시 소정의 비용 발생할 수 있음

        #### ️ 주요 지역 인증센터
        - **서울**: 서울올림픽기념국민체육진흥공단, 각 구민체육센터
        - **경기**: 수원시체육회관, 성남시민체육관, 고양시체육관
        - **인천**: 인천시체육회, 계양체육관
        - **부산**: 부산시체육회, 해운대스포츠센터
        - **대구**: 대구시체육회, 수성구체육관
        """)

    st.link_button(" 국민체력100 공식 사이트 바로가기", "https://nfa.kspo.or.kr/", use_container_width=True)


# ========================================
# 탭7: 수영 준비 가이드
# ========================================
with tab7:
    st.markdown("### 수영 준비 가이드")
    st.markdown("대한항공, 아시아나항공 지원자 필수! 25m 완영 준비를 도와드립니다.")

    # 수영 필수 항공사 안내
    st.markdown("#### ️ 수영 테스트 실시 항공사")

    col1, col2 = st.columns(2)
    for idx, (airline, info) in enumerate(SWIMMING_AIRLINES.items()):
        with [col1, col2][idx]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4facfe20, #00f2fe10);
                        border: 2px solid #4facfe; border-radius: 14px; padding: 20px; margin: 5px 0;">
                <div style="font-size: 18px; font-weight: bold;">️ {airline}</div>
                <div style="margin: 10px 0;">
                    <span style="background: #dc354520; color: #dc3545; padding: 3px 8px; border-radius: 8px; font-weight: bold;">필수</span>
                    <span style="margin-left: 10px;">{info['distance']} {info['style']}</span>
                </div>
                <div style="font-size: 13px; color: #555;">⏱️ 시간: {info['time_limit']}</div>
                <div style="font-size: 13px; color: #555;"> 단계: {info['stage']}</div>
                <div style="font-size: 12px; color: #888; margin-top: 8px;"> {info['note']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 준비물 + 4주 계획
    st.markdown("#### 준비물 & 연습 계획")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**필요한 준비물:**")
        for item in SWIMMING_GUIDE["준비물"]:
            st.checkbox(item, key=f"swim_prep_{item}")

    with col2:
        st.markdown("**4주 연습 계획:**")
        for week, plan in SWIMMING_GUIDE["연습 계획"].items():
            week_colors = {"1주차": "#4facfe", "2주차": "#43e97b", "3주차": "#f093fb", "4주차": "#f5576c"}
            color = week_colors.get(week, "#667eea")
            st.markdown(f"""
            <div style="background: {color}15; border-left: 4px solid {color}; padding: 10px 15px; margin: 8px 0; border-radius: 0 8px 8px 0;">
                <strong>{week}</strong>: {plan}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 자유형 기본 동작
    st.markdown("#### 자유형 기본 동작")

    for i, step in enumerate(SWIMMING_GUIDE["자유형 기본"]):
        step_num = i + 1
        colors = ["#4facfe", "#00f2fe", "#43e97b", "#667eea", "#f093fb"]
        color = colors[i % len(colors)]
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin: 8px 0;">
            <div style="background: {color}; color: white; width: 30px; height: 30px; border-radius: 50%;
                        display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 12px; flex-shrink: 0;">
                {step_num}
            </div>
            <div style="background: {color}10; border: 1px solid {color}40; padding: 10px 15px; border-radius: 10px; flex: 1;">
                {step[3:]}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 초보자 팁
    st.markdown("#### 초보자를 위한 팁")

    for tip in SWIMMING_GUIDE["초보자 팁"]:
        st.success(f" {tip}")

    st.markdown("---")

    # 격려 메시지
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea20, #764ba220);
                border: 2px solid #667eea; border-radius: 16px; padding: 24px; text-align: center; margin: 20px 0;">
        <div style="font-size: 24px; margin-bottom: 10px;">‍️</div>
        <div style="font-size: 18px; font-weight: bold; color: #667eea;">수영 못해도 괜찮아요!</div>
        <div style="margin-top: 10px; color: #555; line-height: 1.8;">
            25m 완영은 <strong>1-2개월</strong>이면 충분합니다.<br>
            성인 초보반 수강 추천! 킥보드부터 시작하세요.<br>
            <strong>속도는 상관없습니다. 완주만 하면 통과!</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 수영장 찾기
    st.markdown("---")
    st.markdown("#### 수영 연습하기")

    st.info("""
    **수영장 찾는 방법:**
    1. 네이버/카카오맵에서 '수영장' 검색
    2. 구/시민 체육관 수영장 (가격 저렴)
    3. 성인 초보반 등록 (보통 주 2~3회, 월 5~8만원)
    4. 새벽/점심 자유수영으로 추가 연습
    """)

    st.caption(" 대부분의 합격자가 1~2개월 수영 배우고 통과했습니다. 지금 시작하면 충분합니다!")

st.markdown('</div>', unsafe_allow_html=True)

# pages/8_면접꿀팁.py
# 면접 꿀팁 모음 페이지 - 2026 채용 트렌드 및 합격 노하우 + 자가진단

import streamlit as st
import os
import sys
import json
from datetime import datetime

from logging_config import get_logger
logger = get_logger(__name__)
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sidebar_common import init_page, end_page

init_page(
    title="면접 꿀팁",
    current_page="면접꿀팁",
    wide_layout=True
)




st.markdown(
    """
    <meta name="google" content="notranslate">
    <meta name="robots" content="notranslate">
    <style>
      html {
        translate: no;
      }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown('<div translate="no" class="notranslate">', unsafe_allow_html=True)

# config에서 면접 팁 데이터 import
from config import (
    INTERVIEW_TIPS,
    FSC_VS_LCC_INTERVIEW,
    COMMON_INTERVIEW_MISTAKES,
    CREW_ESSENTIAL_QUALITIES,
    HIRING_TRENDS_2026,
    AIRLINE_PREFERRED_TYPE,
    ENGLISH_INTERVIEW_AIRLINES,
)

# =====================
# 데이터 경로 및 유틸리티
# =====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSESSMENT_FILE = os.path.join(DATA_DIR, "interview_assessment.json")

def load_assessment():
    if os.path.exists(ASSESSMENT_FILE):
        try:
            with open(ASSESSMENT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.debug(f'Exception occurred: {e}')
            pass
    return {"results": [], "bookmarks": []}

def save_assessment(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ASSESSMENT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 오늘의 팁 데이터 (매일 다른 팁 표시)
DAILY_TIPS = [
    {"category": "첫인상", "tip": "면접관과 눈을 마주치며 인사할 때, 고개를 15도만 숙이세요. 너무 깊은 인사는 오히려 자신감 없어 보입니다.", "icon": "️"},
    {"category": "목소리", "tip": "답변 시작 전 0.5초 멈추고 시작하세요. 급하게 시작하면 긴장해 보이고, 잠깐의 여유가 프로페셔널한 인상을 줍니다.", "icon": ""},
    {"category": "답변법", "tip": "답변은 30초~1분이 적정합니다. 타이머로 연습해보세요. 너무 짧으면 준비 부족, 너무 길면 핵심 전달력이 떨어집니다.", "icon": "⏱️"},
    {"category": "서류", "tip": "자소서에 쓴 경험은 반드시 면접에서 물어봅니다. 자소서를 외우지 말고, 그 경험의 '감정'을 기억하세요.", "icon": ""},
    {"category": "영어", "tip": "영어면접에서 'I think...'보다 'In my experience...'로 시작하면 더 구체적이고 설득력 있는 답변이 됩니다.", "icon": ""},
    {"category": "이미지", "tip": "면접 당일 옷은 전날 밤에 완벽히 준비하세요. 아침에 허둥대면 컨디션과 표정에 그대로 드러납니다.", "icon": ""},
    {"category": "체력", "tip": "면접 전날 가벼운 스트레칭과 30분 산책을 추천합니다. 과한 운동은 피로감을, 적당한 활동은 자신감을 줍니다.", "icon": "️"},
    {"category": "긴장관리", "tip": "대기실에서 손을 따뜻하게 유지하세요. 차가운 손은 긴장의 신호입니다. 핫팩이나 손 비비기가 도움됩니다.", "icon": ""},
    {"category": "태도", "tip": "면접관의 질문을 듣다가 끄덕이세요. 경청하는 태도는 소통 능력의 첫 번째 증거입니다.", "icon": ""},
    {"category": "마무리", "tip": "면접 마지막 '하고 싶은 말' 기회를 절대 놓치지 마세요. 30초짜리 클로징 멘트를 미리 준비하세요.", "icon": ""},
    {"category": "FSC", "tip": "대한항공/아시아나 면접에서는 '글로벌 서비스 마인드'를 강조하세요. FSC는 '품격'있는 서비스를 원합니다.", "icon": "️"},
    {"category": "LCC", "tip": "LCC 면접에서는 '밝은 에너지'와 '팀워크'를 강조하세요. LCC는 적극적이고 활기찬 승무원을 원합니다.", "icon": "️"},
    {"category": "그룹면접", "tip": "그룹면접에서 다른 지원자 답변 시 적절히 고개를 끄덕이세요. 경쟁자가 아닌 동료로 보는 시선이 좋은 인상을 줍니다.", "icon": ""},
    {"category": "꼬리질문", "tip": "꼬리질문은 당신의 답변에 관심이 있다는 신호입니다. 당황하지 말고 '좋은 질문 감사합니다'하고 차분히 답하세요.", "icon": ""},
    {"category": "실수대처", "tip": "답변 중 실수했을 때 '다시 정리해서 말씀드리겠습니다'라고 자연스럽게 리커버리하세요. 당황하는 것보다 대처력이 중요합니다.", "icon": ""},
]

# 자가진단 항목
ASSESSMENT_CATEGORIES = {
    "image": {
        "name": "이미지/첫인상",
        "icon": "",
        "items": [
            "면접 복장(정장/블라우스)을 완벽히 준비했다",
            "헤어스타일을 단정하게 정돈할 수 있다",
            "자연스러운 미소 연습을 꾸준히 하고 있다",
            "바른 자세와 워킹 연습을 했다",
            "메이크업/그루밍 스타일을 결정했다",
        ]
    },
    "answer": {
        "name": "답변 준비",
        "icon": "",
        "items": [
            "자기소개를 1분 내로 자연스럽게 할 수 있다",
            "지원동기를 구체적으로 설명할 수 있다",
            "STAR 기법으로 경험을 정리했다 (3개 이상)",
            "상황별 대처 답변을 준비했다 (5개 이상)",
            "꼬리질문에 당황하지 않고 대응할 수 있다",
        ]
    },
    "english": {
        "name": "영어 면접",
        "icon": "",
        "items": [
            "영어 자기소개를 2분 내로 할 수 있다",
            "기본 영어 질문 5개 이상 답변을 준비했다",
            "영어 발음과 억양 연습을 하고 있다",
            "영어 기내방송문을 읽을 수 있다",
            "서비스 관련 영어 표현을 10개 이상 알고 있다",
        ]
    },
    "fitness": {
        "name": "체력/수영",
        "icon": "️",
        "items": [
            "국민체력100 종목별 기준을 알고 있다",
            "현재 체력 등급이 3등급 이상이다",
            "수영 25m를 완주할 수 있다 (해당 시)",
            "꾸준한 운동 루틴이 있다 (주 3회 이상)",
            "체력시험 당일 복장과 준비물을 알고 있다",
        ]
    },
    "knowledge": {
        "name": "항공 지식",
        "icon": "️",
        "items": [
            "지원 항공사의 인재상을 정확히 알고 있다",
            "FSC와 LCC의 차이점을 설명할 수 있다",
            "최근 항공 업계 뉴스를 3개 이상 알고 있다",
            "기내 안전장비의 종류와 위치를 알고 있다",
            "지원 항공사의 취항 노선을 알고 있다",
        ]
    },
}

# ----------------------------
# 커스텀 CSS
# ----------------------------
st.markdown("""
<style>
/* 카드 스타일 */
.tip-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    border-radius: 15px;
    color: white;
    margin: 10px 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.info-card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    border-left: 5px solid #667eea;
    margin: 10px 0;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.warning-card {
    background: #fff5f5;
    padding: 15px 20px;
    border-radius: 10px;
    border-left: 5px solid #e53e3e;
    margin: 10px 0;
}

.success-card {
    background: #f0fff4;
    padding: 15px 20px;
    border-radius: 10px;
    border-left: 5px solid #38a169;
    margin: 10px 0;
}

/* 섹션 헤더 */
.section-header {
    background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
    padding: 15px 20px;
    border-radius: 10px;
    margin: 20px 0 15px 0;
    border-left: 4px solid #667eea;
}

/* 숫자 뱃지 */
.number-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 50%;
    font-weight: bold;
    margin-right: 10px;
}

/* 체크리스트 아이템 */
.checklist-item {
    padding: 10px 15px;
    background: #f8f9fa;
    border-radius: 8px;
    margin: 5px 0;
    display: flex;
    align-items: center;
}

.checklist-item:hover {
    background: #e9ecef;
}

/* 비교 카드 */
.compare-card {
    padding: 20px;
    border-radius: 12px;
    height: 100%;
}

.fsc-card {
    background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
    color: white;
}

.lcc-card {
    background: linear-gradient(135deg, #744210 0%, #c05621 100%);
    color: white;
}

/* STAR 카드 */
.star-card {
    text-align: center;
    padding: 20px;
    border-radius: 12px;
    height: 100%;
}

.star-s { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; }
.star-t { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; }
.star-a { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: white; }
.star-r { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white; }

/* 복장 가이드 카드 */
.dress-card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 2px 15px rgba(0,0,0,0.08);
    margin: 10px 0;
    text-align: center;
}

/* 긴장 관리 팁 카드 */
.calm-tip {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    padding: 15px 20px;
    border-radius: 12px;
    margin: 8px 0;
}

/* 영어 표현 카드 */
.english-phrase {
    background: #edf2f7;
    padding: 15px;
    border-radius: 10px;
    margin: 8px 0;
    border-left: 4px solid #3182ce;
}

/* 메라비언 그래프 */
.merabian-bar {
    height: 30px;
    border-radius: 15px;
    display: flex;
    align-items: center;
    padding: 0 15px;
    color: white;
    font-weight: bold;
    margin: 5px 0;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# 페이지 제목
# ----------------------------
st.markdown("""
<div style="text-align: center; padding: 20px 0;">
    <h1 style="background: linear-gradient(90deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.5rem;">
         면접 꿀팁 모음
    </h1>
    <p style="color: #666; font-size: 1.1rem;">2026 항공사 채용 트렌드 및 합격 노하우</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ----------------------------
# 오늘의 팁 (매일 다른 팁 표시)
# ----------------------------
today_idx = datetime.now().timetuple().tm_yday % len(DAILY_TIPS)
daily_tip = DAILY_TIPS[today_idx]

st.markdown(f"""
<div style="background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); border: 2px solid #667eea40; border-radius: 16px; padding: 20px 25px; margin-bottom: 20px; display: flex; align-items: center; gap: 15px;">
    <div style="font-size: 2.5rem;">{daily_tip["icon"]}</div>
    <div>
        <div style="font-size: 0.75rem; color: #667eea; font-weight: 700; margin-bottom: 4px;">TODAY'S TIP - {daily_tip["category"]}</div>
        <div style="font-size: 0.95rem; color: #334155; font-weight: 500; line-height: 1.5;">{daily_tip["tip"]}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------
# 탭 구성 (14개 탭)
# ----------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14 = st.tabs([
 " 첫인상",
 " 복장가이드",
 " 빈출질문",
 "⭐ STAR기법",
 "️ 영어면접",
 " 그룹면접",
 "️ FSC/LCC",
 "️ 탈락사유",
 " 긴장관리",
 " 트렌드",
 " AI면접",
 " 영상면접",
 " 항공사별",
 " 자가진단"
])

# ----------------------------
# 탭 1: 메라비언 법칙 & 첫인상
# ----------------------------
with tab1:
    st.markdown('<div class="section-header"><h2> 메라비언 법칙 - 첫인상의 과학</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="tip-card">
        <h3 style="margin:0;"> 면접의 승패는 첫 3초에 결정됩니다</h3>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">화려한 스펙보다 첫인상이 훨씬 중요합니다. 메라비언 법칙을 이해하고 준비하세요.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    # 메라비언 시각화
    merabian = INTERVIEW_TIPS.get("merabian_law", {})

    st.markdown(f"""
    <div style="margin: 20px 0;">
        <div class="merabian-bar" style="background: linear-gradient(90deg, #e53e3e, #fc8181); width: 100%;">
            ️ 시각 (이미지/비주얼) - {merabian.get('image', 55)}%
        </div>
        <div class="merabian-bar" style="background: linear-gradient(90deg, #3182ce, #63b3ed); width: 70%;">
             청각 (목소리 톤) - {merabian.get('voice', 38)}%
        </div>
        <div class="merabian-bar" style="background: linear-gradient(90deg, #38a169, #68d391); width: 15%;">
             내용 - {merabian.get('content', 7)}%
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ️ 시각 55% - 이미지 관리")
        st.markdown("""
        <div class="info-card">
            <p><strong>첫인상을 결정짓는 핵심 요소들</strong></p>
        </div>
        """, unsafe_allow_html=True)

        image_tips = [
            " 밝고 자연스러운 미소 (치아 살짝 보이게)",
            " 면접관과 자연스러운 눈 맞춤",
            " 바른 자세 - 어깨 펴고 턱 살짝 당기기",
            " 자신감 있는 워킹 - 너무 빠르지 않게",
            " 적절한 제스처 - 과하지 않게",
            " 의자에 등 대지 않고 단정하게 앉기"
        ]
        for tip in image_tips:
            st.markdown(f'<div class="checklist-item">{tip}</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("### 청각 38% - 목소리 관리")
        st.markdown("""
        <div class="info-card">
            <p><strong>목소리로 전달되는 자신감</strong></p>
        </div>
        """, unsafe_allow_html=True)

        voice_tips = [
            " 적당한 크기 - 자신감 있지만 시끄럽지 않게",
            "⏱️ 적절한 속도 - 1분에 250~300자",
            " 톤 변화 - 단조롭지 않게 강약 조절",
            " 떨리지 않는 목소리 - 호흡 조절",
            " 또렷한 발음 - 웅얼거리지 않기",
            "⏸️ 적절한 쉼 - 생각하며 말하기"
        ]
        for tip in voice_tips:
            st.markdown(f'<div class="checklist-item">{tip}</div>', unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 내용 7% - 하지만 무시하면 안 됩니다!")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="success-card">
            <strong> 두괄식 답변</strong><br/>
            결론 먼저, 이유는 나중에
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="success-card">
            <strong> 구체적 경험</strong><br/>
            숫자와 사례로 뒷받침
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="success-card">
            <strong> 진정성</strong><br/>
            외운 티 나지 않게
        </div>
        """, unsafe_allow_html=True)

# ----------------------------
# 탭 2: 복장/이미지 가이드
# ----------------------------
with tab2:
    st.markdown('<div class="section-header"><h2> 면접 복장 & 이미지 가이드</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="tip-card">
        <h3 style="margin:0;"> 승무원 면접은 '이미지 면접'입니다</h3>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">청결하고 단정한 이미지가 가장 중요합니다. 항공사마다 선호하는 스타일이 다르니 확인하세요.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 여성 / 남성 탭
    gender_tab1, gender_tab2 = st.tabs([" 여성 지원자", " 남성 지원자"])

    with gender_tab1:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div class="dress-card">
                <div style="font-size: 50px;"></div>
                <h4>복장</h4>
                <hr style="margin: 10px 0;">
                <p style="text-align: left; font-size: 14px;">
                • <strong>블라우스:</strong> 흰색/아이보리 기본<br/>
                • <strong>스커트:</strong> 검정/네이비 H라인<br/>
                • <strong>길이:</strong> 무릎 위 5~10cm<br/>
                • <strong>스타킹:</strong> 살색 (울 없는 것)<br/>
                • <strong>구두:</strong> 검정 펌프스 5~7cm<br/>
                • <strong>주의:</strong> 화려한 색상/무늬 
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="dress-card">
                <div style="font-size: 50px;"></div>
                <h4>메이크업</h4>
                <hr style="margin: 10px 0;">
                <p style="text-align: left; font-size: 14px;">
                • <strong>베이스:</strong> 깨끗하고 자연스럽게<br/>
                • <strong>눈:</strong> 브라운 계열 내추럴<br/>
                • <strong>속눈썹:</strong> 자연스러운 펌/연장<br/>
                • <strong>블러셔:</strong> 코랄/피치 톤<br/>
                • <strong>립:</strong> MLBB or 코랄 핑크<br/>
                • <strong>주의:</strong> 스모키/진한 립 
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class="dress-card">
                <div style="font-size: 50px;">‍️</div>
                <h4>헤어스타일</h4>
                <hr style="margin: 10px 0;">
                <p style="text-align: left; font-size: 14px;">
                • <strong>기본:</strong> 깔끔한 올림머리<br/>
                • <strong>샤기컷:</strong> 단정히 정리<br/>
                • <strong>앞머리:</strong> 이마 보이게<br/>
                • <strong>잔머리:</strong> 헤어스프레이로 정리<br/>
                • <strong>색상:</strong> 자연스러운 다크브라운<br/>
                • <strong>주의:</strong> 밝은 염색/파마 
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("### 세부 체크리스트")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **네일 & 손**
            -  깔끔한 누드/연핑크 매니큐어
            -  손톱 길이 적당히 (너무 길지 않게)
            -  손 보습 관리
            -  네일아트, 긴 손톱, 어두운 색상

            **액세서리**
            -  작은 진주/골드 귀걸이 (원터치)
            -  심플한 시계
            -  목걸이, 팔찌, 화려한 귀걸이
            """)

        with col2:
            st.markdown("""
            **향수 & 기타**
            -  은은한 향수 또는 무향
            -  깨끗한 치아 (미백 관리)
            -  깔끔한 피부 관리
            -  진한 향수, 강한 체취

            **가방 & 서류**
            -  심플한 A4 서류가방
            -  서류 클리어파일로 정리
            -  브랜드 로고 큰 가방
            """)

    with gender_tab2:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div class="dress-card">
                <div style="font-size: 50px;"></div>
                <h4>복장</h4>
                <hr style="margin: 10px 0;">
                <p style="text-align: left; font-size: 14px;">
                • <strong>정장:</strong> 네이비/차콜 수트<br/>
                • <strong>셔츠:</strong> 흰색 드레스 셔츠<br/>
                • <strong>넥타이:</strong> 네이비/와인 무지<br/>
                • <strong>구두:</strong> 검정 옥스포드<br/>
                • <strong>벨트:</strong> 검정 가죽<br/>
                • <strong>양말:</strong> 검정 (발목 안 보이게)
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="dress-card">
                <div style="font-size: 50px;">‍️</div>
                <h4>헤어 & 그루밍</h4>
                <hr style="margin: 10px 0;">
                <p style="text-align: left; font-size: 14px;">
                • <strong>헤어:</strong> 짧고 단정하게<br/>
                • <strong>이마:</strong> 보이게 정리<br/>
                • <strong>면도:</strong> 깔끔하게<br/>
                • <strong>눈썹:</strong> 자연스럽게 정리<br/>
                • <strong>피부:</strong> 기초 관리<br/>
                • <strong>손톱:</strong> 짧고 깨끗하게
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class="dress-card">
                <div style="font-size: 50px;">️</div>
                <h4>주의사항</h4>
                <hr style="margin: 10px 0;">
                <p style="text-align: left; font-size: 14px;">
                •  긴 머리, 파마<br/>
                •  수염, 구레나룻<br/>
                •  화려한 넥타이<br/>
                •  향수 과다 사용<br/>
                •  액세서리 (시계 외)<br/>
                •  검정 정장 (장례식 느낌)
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 항공사별 이미지
    st.markdown("### ️ 항공사별 선호 이미지")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="info-card">
            <h4>️ FSC (대형 항공사)</h4>
            <p><strong>대한항공:</strong> 품격 있고 우아한 이미지, 클래식한 스타일</p>
            <p><strong>아시아나:</strong> 세련되고 따뜻한 이미지, 부드러운 미소</p>
            <p style="color: #666; font-size: 13px;">→ 보수적이고 단정한 스타일 선호</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card">
            <h4>️ LCC (저비용 항공사)</h4>
            <p><strong>제주항공:</strong> 밝고 활기찬 이미지</p>
            <p><strong>진에어:</strong> 젊고 트렌디한 이미지</p>
            <p><strong>티웨이:</strong> 친근하고 건강한 이미지</p>
            <p style="color: #666; font-size: 13px;">→ 활발하고 에너지 넘치는 스타일 선호</p>
        </div>
        """, unsafe_allow_html=True)

# ----------------------------
# 탭 3: 자주 나오는 질문
# ----------------------------
with tab3:
    st.markdown('<div class="section-header"><h2> 자주 나오는 면접 질문 TOP 10</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="tip-card">
        <h3 style="margin:0;"> 이 질문들은 반드시 준비하세요!</h3>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">합격자들이 실제로 받은 질문들입니다. 각 질문에 대한 나만의 답변을 미리 준비해두세요.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 질문 데이터
    common_questions = [
        {
            "q": "자기소개 해주세요",
            "category": "기본",
            "color": "#e53e3e",
            "tip": "1분 내외로 준비. 이름-학교-지원동기-강점 순서로 구성",
            "example": "안녕하세요, OO항공 객실승무원에 지원한 OOO입니다. 저는 서비스 직무 경험을 통해..."
        },
        {
            "q": "왜 승무원이 되고 싶나요?",
            "category": "기본",
            "color": "#e53e3e",
            "tip": "진정성 있는 계기 + 승무원이어야만 하는 이유",
            "example": "어린 시절 가족여행에서 만난 승무원분의 따뜻한 서비스가 계기가 되었습니다..."
        },
        {
            "q": "왜 저희 항공사인가요?",
            "category": "기본",
            "color": "#e53e3e",
            "tip": "해당 항공사만의 특징 + 나의 가치관과 연결",
            "example": "OO항공의 '고객 최우선' 가치관이 제가 추구하는 서비스 철학과 일치합니다..."
        },
        {
            "q": "본인의 강점과 약점은?",
            "category": "인성",
            "color": "#3182ce",
            "tip": "강점은 승무원 업무와 연결, 약점은 개선 노력과 함께",
            "example": "저의 강점은 공감 능력입니다. 약점인 완벽주의는 우선순위를 정해 개선 중입니다..."
        },
        {
            "q": "팀워크 경험을 말해주세요",
            "category": "경험",
            "color": "#38a169",
            "tip": "STAR 기법으로 구체적 사례, 본인 역할 강조",
            "example": "대학 축제 기획 때 갈등이 생겼지만, 중재 역할을 하며 성공적으로 마무리했습니다..."
        },
        {
            "q": "어려운 고객 응대 경험",
            "category": "경험",
            "color": "#38a169",
            "tip": "해결 과정과 배운 점 강조, 감정적 대응 ",
            "example": "카페 아르바이트 중 컴플레인 고객을 만났을 때, 먼저 공감하고 해결책을 제시했습니다..."
        },
        {
            "q": "기내 비상상황 대처법",
            "category": "상황",
            "color": "#805ad5",
            "tip": "침착함 + 매뉴얼 숙지 + 승객 안전 우선",
            "example": "먼저 상황을 파악하고, 매뉴얼에 따라 대처하며, 승객 안전을 최우선으로 하겠습니다..."
        },
        {
            "q": "10년 후 본인의 모습",
            "category": "비전",
            "color": "#d69e2e",
            "tip": "승무원으로서의 성장 비전 (사무장/트레이너 등)",
            "example": "10년 후에는 후배 승무원들에게 귀감이 되는 선배 승무원이 되고 싶습니다..."
        },
        {
            "q": "스트레스 관리 방법",
            "category": "인성",
            "color": "#3182ce",
            "tip": "건강한 해소법, 업무에 지장 없음을 어필",
            "example": "운동과 음악 감상으로 스트레스를 해소하며, 긍정적인 마인드를 유지합니다..."
        },
        {
            "q": "마지막으로 하고 싶은 말",
            "category": "기본",
            "color": "#e53e3e",
            "tip": "열정 + 준비된 모습 어필 + 감사 인사",
            "example": "오늘 이 자리에 서기까지 많은 준비를 해왔습니다. 꼭 OO항공과 함께하고 싶습니다..."
        },
    ]

    for i, item in enumerate(common_questions, 1):
        with st.expander(f"**{i}. {item['q']}** [{item['category']}]", expanded=(i <= 3)):
            col1, col2 = st.columns([2, 3])
            with col1:
                st.markdown(f"""
                <div style="background: {item['color']}15; padding: 15px; border-radius: 10px; border-left: 4px solid {item['color']};">
                    <strong> 답변 포인트</strong><br/>
                    {item['tip']}
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="background: #f7fafc; padding: 15px; border-radius: 10px;">
                    <strong> 예시 답변 시작</strong><br/>
                    <span style="color: #666; font-style: italic;">"{item['example']}"</span>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    st.info("**팁:** 예시 답변을 그대로 외우지 마세요! 본인만의 경험과 언어로 재구성하세요.")

# ----------------------------
# 탭 4: STAR 기법
# ----------------------------
with tab4:
    st.markdown('<div class="section-header"><h2>⭐ STAR 기법 - 경험 답변의 정석</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="tip-card">
        <h3 style="margin:0;">경험을 물어볼 때는 STAR로 답하세요!</h3>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">논리적이고 설득력 있는 답변 구조입니다. 모든 경험 질문에 적용하세요.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    # STAR 시각화
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="star-card star-s">
            <h1 style="margin:0;">S</h1>
            <h3>Situation</h3>
            <p><strong>상황 설명</strong></p>
            <hr style="border-color: rgba(255,255,255,0.3);">
            <p style="font-size: 14px;">
            언제?<br/>
            어디서?<br/>
            어떤 상황?
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="star-card star-t">
            <h1 style="margin:0;">T</h1>
            <h3>Task</h3>
            <p><strong>역할/과제</strong></p>
            <hr style="border-color: rgba(255,255,255,0.3);">
            <p style="font-size: 14px;">
            무엇을 해야 했나?<br/>
            나의 역할은?<br/>
            목표는?
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="star-card star-a">
            <h1 style="margin:0;">A</h1>
            <h3>Action</h3>
            <p><strong>구체적 행동</strong></p>
            <hr style="border-color: rgba(255,255,255,0.3);">
            <p style="font-size: 14px;">
            무엇을 했나?<br/>
            어떻게 했나?<br/>
            왜 그렇게?
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="star-card star-r">
            <h1 style="margin:0;">R</h1>
            <h3>Result</h3>
            <p><strong>결과/교훈</strong></p>
            <hr style="border-color: rgba(255,255,255,0.3);">
            <p style="font-size: 14px;">
            결과는?<br/>
            배운 점은?<br/>
            성장한 부분?
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # STAR 예시
    st.markdown("### STAR 기법 적용 예시")

    st.markdown("""
    <div class="info-card">
        <h4> 질문: "팀워크 경험을 말해주세요"</h4>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ** 나쁜 예시**
        > "저는 팀워크를 잘합니다. 대학교 때 조별과제도 많이 했고, 아르바이트할 때도 팀원들과 잘 지냈습니다. 팀워크가 중요하다고 생각합니다."

        *→ 구체적인 상황이 없고, 추상적인 표현만 나열*
        """)

    with col2:
        st.markdown("""
        ** 좋은 예시 (STAR)**
        > **[S]** "대학 3학년 때 마케팅 공모전에 5명이 팀을 이뤄 참가했습니다."
        >
        > **[T]** "저는 팀장으로서 일정 관리와 팀원 간 의견 조율을 맡았습니다."
        >
        > **[A]** "의견 충돌이 생겼을 때 각자의 의견을 경청하고 장단점을 분석해 절충안을 제시했습니다."
        >
        > **[R]** "결과적으로 우수상을 수상했고, 소통의 중요성을 배웠습니다."
        """)

    st.markdown("---")

    # STAR 템플릿
    st.markdown("### 나만의 STAR 스토리 만들기")

    st.info("아래 경험들에 대해 각각 STAR 스토리를 미리 준비해두세요!")

    experiences = [
        "팀워크/협업 경험",
        "갈등 해결 경험",
        "어려운 고객 응대 경험",
        "리더십 발휘 경험",
        "실패를 극복한 경험",
        "목표를 달성한 경험",
        "새로운 것을 배운 경험",
        "창의적으로 문제를 해결한 경험"
    ]

    col1, col2 = st.columns(2)
    for i, exp in enumerate(experiences):
        with col1 if i % 2 == 0 else col2:
            st.markdown(f'<div class="checklist-item"> {exp}</div>', unsafe_allow_html=True)

# ----------------------------
# 탭 5: 영어면접 꿀팁
# ----------------------------
with tab5:
    st.markdown('<div class="section-header"><h2>️ 영어 면접 완벽 대비</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="tip-card">
        <h3 style="margin:0;">영어 면접은 유창함보다 자신감!</h3>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">완벽한 문법보다 당당한 태도와 명확한 전달이 중요합니다.</p>
    </div>
    """, unsafe_allow_html=True)

    # 영어 면접 있는 항공사
    st.markdown("---")
    eng_airlines = ", ".join(ENGLISH_INTERVIEW_AIRLINES) if ENGLISH_INTERVIEW_AIRLINES else "대한항공, 아시아나항공, 에어프레미아"
    st.info(f"️ **영어 면접 전형 있는 항공사:** {eng_airlines}")

    st.markdown("---")

    # 자주 나오는 영어 질문
    st.markdown("### 자주 나오는 영어 질문 & 표현")

    english_questions = [
        {
            "question": "Please introduce yourself.",
            "korean": "자기소개 해주세요",
            "answer": "Hello, my name is [이름]. I'm [나이] years old and I graduated from [학교] with a major in [전공]. I'm passionate about providing excellent customer service, and I believe my experience in [경험] has prepared me well for this position.",
            "tip": "30초~1분 내외로, 이름-학교-경험-지원이유 순서"
        },
        {
            "question": "Why do you want to be a flight attendant?",
            "korean": "왜 승무원이 되고 싶나요?",
            "answer": "I've always been passionate about traveling and meeting people from diverse backgrounds. Being a flight attendant would allow me to combine my love for service with my desire to explore the world while ensuring passengers have a safe and comfortable journey.",
            "tip": "진정성 있는 동기 + 승무원 업무 이해도"
        },
        {
            "question": "Why did you apply to our airline?",
            "korean": "왜 저희 항공사에 지원했나요?",
            "answer": "I admire [항공사]'s commitment to [가치/특징]. Your airline's reputation for [특징] aligns perfectly with my personal values of [나의 가치]. I would be honored to be part of such a respected team.",
            "tip": "항공사 특징 조사 필수!"
        },
        {
            "question": "What are your strengths and weaknesses?",
            "korean": "강점과 약점은?",
            "answer": "My strength is my ability to remain calm under pressure. For example, [구체적 예시]. As for my weakness, I tend to be a perfectionist, but I've learned to prioritize tasks and manage my time more effectively.",
            "tip": "약점은 개선 노력과 함께!"
        },
        {
            "question": "How would you handle a difficult passenger?",
            "korean": "어려운 승객 대처법",
            "answer": "I would first listen to the passenger's concerns with empathy and patience. Then, I would apologize for any inconvenience and try to find a solution within company guidelines. Maintaining a calm and professional attitude is key.",
            "tip": "공감 → 사과 → 해결 순서"
        },
    ]

    for item in english_questions:
        with st.expander(f" {item['question']}"):
            st.markdown(f"**한글:** {item['korean']}")
            st.markdown("---")
            st.markdown(f"""
            <div class="english-phrase">
                <strong> 예시 답변:</strong><br/>
                <p style="margin: 10px 0; line-height: 1.8;">{item['answer']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.caption(f" **팁:** {item['tip']}")

    st.markdown("---")

    # 유용한 영어 표현
    st.markdown("### 유용한 영어 표현")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**답변 시작할 때**")
        phrases1 = [
            ("That's a great question.", "좋은 질문이네요"),
            ("I believe that...", "저는 ~라고 생각합니다"),
            ("In my experience...", "제 경험상..."),
            ("To be honest...", "솔직히 말씀드리면..."),
        ]
        for eng, kor in phrases1:
            st.markdown(f"""
            <div class="english-phrase">
                <strong>{eng}</strong><br/>
                <span style="color: #666;">{kor}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("**경험 말할 때**")
        phrases2 = [
            ("When I was working at...", "~에서 일할 때"),
            ("I had an opportunity to...", "~할 기회가 있었습니다"),
            ("Through this experience, I learned...", "이 경험을 통해 배웠습니다"),
        ]
        for eng, kor in phrases2:
            st.markdown(f"""
            <div class="english-phrase">
                <strong>{eng}</strong><br/>
                <span style="color: #666;">{kor}</span>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("**잘 못 들었을 때**")
        phrases3 = [
            ("Could you please repeat that?", "다시 말씀해 주시겠어요?"),
            ("I'm sorry, I didn't catch that.", "죄송합니다, 못 들었습니다"),
            ("Could you speak more slowly?", "천천히 말씀해 주시겠어요?"),
        ]
        for eng, kor in phrases3:
            st.markdown(f"""
            <div class="english-phrase">
                <strong>{eng}</strong><br/>
                <span style="color: #666;">{kor}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("**마무리할 때**")
        phrases4 = [
            ("Thank you for this opportunity.", "이런 기회를 주셔서 감사합니다"),
            ("I'm confident that...", "저는 ~할 자신이 있습니다"),
            ("I would be honored to join your team.", "귀사에 합류하게 되면 영광이겠습니다"),
        ]
        for eng, kor in phrases4:
            st.markdown(f"""
            <div class="english-phrase">
                <strong>{eng}</strong><br/>
                <span style="color: #666;">{kor}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("""
    <div class="warning-card">
        <strong>️ 영어 면접 주의사항</strong>
        <ul style="margin: 10px 0;">
            <li>모르는 단어는 쉬운 표현으로 돌려 말하기</li>
            <li>너무 빠르게 말하지 않기 (긴장하면 빨라짐)</li>
            <li>Um, Uh 줄이기 (대신 잠시 생각하는 것이 나음)</li>
            <li>한국어 억양 너무 신경쓰지 않기 (내용이 더 중요)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------
# 탭 6: 그룹/토론 면접
# ----------------------------
with tab6:
    st.markdown('<div class="section-header"><h2> 그룹 면접 & 토론 면접 공략</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="tip-card">
        <h3 style="margin:0;">그룹 면접에서는 '협력'이 핵심입니다</h3>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">혼자 돋보이려 하지 말고, 팀 전체가 빛나도록 하세요.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 그룹 면접 유형
    st.markdown("### 그룹 면접 유형")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="dress-card">
            <div style="font-size: 40px;"></div>
            <h4>그룹 질의응답</h4>
            <hr/>
            <p style="font-size: 14px; text-align: left;">
            • 3~5명이 같은 질문에 순서대로 답변<br/>
            • 앞사람과 겹치지 않게 준비<br/>
            • 다른 지원자 답변 시 경청
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="dress-card">
            <div style="font-size: 40px;">️</div>
            <h4>그룹 토론</h4>
            <hr/>
            <p style="font-size: 14px; text-align: left;">
            • 주어진 주제에 대해 토론<br/>
            • 찬반 의견 나누기<br/>
            • 결론 도출하기
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="dress-card">
            <div style="font-size: 40px;"></div>
            <h4>역할극/상황극</h4>
            <hr/>
            <p style="font-size: 14px; text-align: left;">
            • 기내 상황 시뮬레이션<br/>
            • 승무원-승객 역할 수행<br/>
            • 문제 해결 과정 보여주기
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # DO's and DON'Ts
    st.markdown("### DO's & DON'Ts")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="success-card">
            <h4> 이렇게 하세요 (DO's)</h4>
            <ul style="margin: 10px 0;">
                <li><strong>경청하기</strong> - 다른 사람 말할 때 끄덕이며 듣기</li>
                <li><strong>연결하기</strong> - "OO님 말씀에 덧붙이면..."</li>
                <li><strong>배려하기</strong> - 말 못한 사람에게 기회 주기</li>
                <li><strong>정리하기</strong> - 논의 내용 요약해서 말하기</li>
                <li><strong>미소 유지</strong> - 말 안 할 때도 표정 관리</li>
                <li><strong>균형 있게</strong> - 적절한 발언 횟수 유지</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="warning-card">
            <h4> 이것만은 피하세요 (DON'Ts)</h4>
            <ul style="margin: 10px 0;">
                <li><strong>끼어들기</strong> - 남의 말 끊지 않기</li>
                <li><strong>독점하기</strong> - 혼자 너무 오래 말하지 않기</li>
                <li><strong>무시하기</strong> - 다른 의견 비난하지 않기</li>
                <li><strong>공격하기</strong> - "그건 틀렸어요" </li>
                <li><strong>침묵하기</strong> - 아예 발언 안 하면 감점</li>
                <li><strong>눈치 없이</strong> - 분위기 파악 못하기</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 토론 면접 전략
    st.markdown("### 토론 면접 역할별 전략")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="info-card" style="border-left-color: #e53e3e;">
            <h4> 리더/사회자</h4>
            <p style="font-size: 14px;">
            • 토론 시작과 마무리<br/>
            • 시간 관리 및 진행<br/>
            • 의견 정리 및 결론 도출<br/>
            • <span style="color: #e53e3e;">️ 독단적이면 감점!</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card" style="border-left-color: #3182ce;">
            <h4> 아이디어맨</h4>
            <p style="font-size: 14px;">
            • 창의적인 의견 제시<br/>
            • 새로운 관점 소개<br/>
            • 예시와 근거 제시<br/>
            • <span style="color: #3182ce;"> 구체적 사례가 핵심</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="info-card" style="border-left-color: #38a169;">
            <h4> 조율자</h4>
            <p style="font-size: 14px;">
            • 의견 갈등 시 중재<br/>
            • 공통점 찾아 연결<br/>
            • 침묵하는 사람 참여 유도<br/>
            • <span style="color: #38a169;"> 협력 강조하면 가산점</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 유용한 표현
    st.markdown("### 토론에서 유용한 표현")

    expressions = {
        "동의할 때": [
            "OO님 의견에 동의합니다. 덧붙이자면...",
            "좋은 의견이네요. 저도 비슷한 생각인데...",
            "말씀하신 부분이 핵심인 것 같습니다."
        ],
        "다른 의견 제시할 때": [
            "조금 다른 관점에서 보면...",
            "한편으로는 이런 측면도 있을 것 같습니다.",
            "추가로 고려해볼 점이 있는데요..."
        ],
        "정리할 때": [
            "지금까지 나온 의견을 정리하면...",
            "공통적으로 중요하게 생각하는 부분은...",
            "결론적으로 저희 팀은..."
        ],
        "참여 유도할 때": [
            "OO님은 어떻게 생각하시나요?",
            "다른 분들 의견도 들어보면 좋을 것 같습니다.",
            "아직 말씀 안 하신 분도 계신 것 같은데..."
        ]
    }

    col1, col2 = st.columns(2)
    for i, (category, phrases) in enumerate(expressions.items()):
        with col1 if i % 2 == 0 else col2:
            st.markdown(f"**{category}**")
            for phrase in phrases:
                st.markdown(f'<div class="checklist-item" style="font-size: 14px;">{phrase}</div>', unsafe_allow_html=True)

# ----------------------------
# 탭 7: FSC vs LCC
# ----------------------------
with tab7:
    st.markdown('<div class="section-header"><h2>️ FSC vs LCC 면접 스타일 차이</h2></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    fsc_info = FSC_VS_LCC_INTERVIEW.get("FSC", {})
    lcc_info = FSC_VS_LCC_INTERVIEW.get("LCC", {})

    with col1:
        st.markdown(f"""
        <div class="compare-card fsc-card">
            <h2 style="margin:0;">️ FSC</h2>
            <h4>대형 항공사</h4>
            <p>대한항공, 아시아나항공</p>
            <hr style="border-color: rgba(255,255,255,0.3);">
            <p><strong>선호 스타일:</strong> {fsc_info.get('preferred_style', '품격 있고 우아한')}</p>
            <p><strong>답변 방식:</strong> {fsc_info.get('answer_style', '차분하고 논리적인')}</p>
            <p><strong>이미지:</strong> {fsc_info.get('image', '클래식하고 단정한')}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        st.markdown("**핵심 키워드**")
        for focus in fsc_info.get("focus", ["품격", "전문성", "글로벌 역량"]):
            st.markdown(f"• {focus}")

        st.markdown("**면접 팁**")
        for tip in fsc_info.get("tips", []):
            st.markdown(f"• {tip}")

    with col2:
        st.markdown(f"""
        <div class="compare-card lcc-card">
            <h2 style="margin:0;">️ LCC</h2>
            <h4>저비용 항공사</h4>
            <p>제주항공, 진에어, 티웨이 등</p>
            <hr style="border-color: rgba(255,255,255,0.3);">
            <p><strong>선호 스타일:</strong> {lcc_info.get('preferred_style', '밝고 활기찬')}</p>
            <p><strong>답변 방식:</strong> {lcc_info.get('answer_style', '솔직하고 에너지 넘치는')}</p>
            <p><strong>이미지:</strong> {lcc_info.get('image', '젊고 친근한')}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        st.markdown("**핵심 키워드**")
        for focus in lcc_info.get("focus", ["친근함", "효율성", "팀워크"]):
            st.markdown(f"• {focus}")

        st.markdown("**면접 팁**")
        for tip in lcc_info.get("tips", []):
            st.markdown(f"• {tip}")

    st.markdown("---")

    # 비교 표
    st.markdown("### 한눈에 비교하기")

    comparison_data = {
        "항목": ["면접 분위기", "답변 길이", "미소", "자세", "목소리", "어필 포인트"],
        "FSC (대형)": ["차분하고 격식 있음", "충분히 설명", "단아한 미소", "반듯하고 우아하게", "차분하고 또렷하게", "품격, 전문성, 어학"],
        "LCC (저비용)": ["활기차고 편안함", "간결하게", "환한 미소", "에너지 넘치게", "밝고 활기차게", "친화력, 체력, 열정"]
    }

    st.table(comparison_data)

    st.markdown("---")

    # 이직 정보
    st.markdown("### FSC ↔ LCC 이직 시 주의점")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="info-card">
            <h4>FSC → LCC 이직 시</h4>
            <p>"왜 대형항공사를 두고 저비용항공을 선택했나요?"</p>
            <ul style="font-size: 14px;">
                <li>LCC의 성장 가능성에 대한 관심 표현</li>
                <li>유연성과 적응력 강조</li>
                <li>새로운 도전에 대한 열정</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card">
            <h4>LCC → FSC 이직 시</h4>
            <p>"LCC에서의 경험이 어떻게 도움이 될까요?"</p>
            <ul style="font-size: 14px;">
                <li>LCC 경험의 강점 연결</li>
                <li>서비스 품질에 대한 높은 기준 강조</li>
                <li>장기적인 커리어 비전 제시</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ----------------------------
# 탭 8: 탈락 사유
# ----------------------------
with tab8:
    st.markdown('<div class="section-header"><h2>️ 실제 탈락 사유 분석</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="warning-card">
        <h3 style="margin:0; color: #c53030;">이런 실수는 절대 하지 마세요!</h3>
        <p style="margin: 10px 0 0 0;">합격자 후기에서 추출한 실제 탈락 원인들입니다.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    category_icons = {
        "답변 실수": "",
        "태도 실수": "",
        "이미지 실수": "️",
        "그룹/디스커션 실수": "",
    }

    category_colors = {
        "답변 실수": "#e53e3e",
        "태도 실수": "#d69e2e",
        "이미지 실수": "#805ad5",
        "그룹/디스커션 실수": "#3182ce",
    }

    for item in COMMON_INTERVIEW_MISTAKES:
        category = item.get("category", "기타")
        mistakes = item.get("mistakes", [])
        icon = category_icons.get(category, "️")
        color = category_colors.get(category, "#666")

        st.markdown(f"""
        <div style="background: {color}10; padding: 15px 20px; border-radius: 12px; border-left: 5px solid {color}; margin: 10px 0;">
            <h4 style="margin: 0 0 10px 0;">{icon} {category}</h4>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        for i, mistake in enumerate(mistakes):
            with col1 if i % 2 == 0 else col2:
                st.markdown(f"• {mistake}")

        st.markdown("")

    st.markdown("---")

    # 탈락 후 성장법
    st.markdown("### 탈락 후 성장하는 법")

    col1, col2 = st.columns(2)

    with col1:
        steps = [
            ("1. 면접 일기 쓰기", "면접 직후 느낀 기분, 표정, 답변, 질문 등 상세히 기록"),
            ("2. 객관적 분석", "일기를 통해 자신의 보완점과 약한 질문 유형 파악"),
        ]
        for title, desc in steps:
            st.markdown(f"""
            <div class="info-card">
                <strong>{title}</strong><br/>
                <span style="color: #666;">{desc}</span>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        steps = [
            ("3. 블로그 작성 추천", "경험을 정리하면 다음 면접에 큰 도움"),
            ("4. 자책 금지", "어이없는 이유로 탈락할 수도 있음, 본인 장점을 알아봐 주는 항공사를 기다리기"),
        ]
        for title, desc in steps:
            st.markdown(f"""
            <div class="info-card">
                <strong>{title}</strong><br/>
                <span style="color: #666;">{desc}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div class="success-card">
        <strong> 기억하세요!</strong><br/>
        대부분의 합격자들도 여러 번의 탈락을 경험했습니다. 포기하지 않는 것이 가장 중요합니다!
    </div>
    """, unsafe_allow_html=True)

# ----------------------------
# 탭 9: 긴장 관리
# ----------------------------
with tab9:
    st.markdown('<div class="section-header"><h2> 면접 긴장 관리 & 멘탈 케어</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="tip-card">
        <h3 style="margin:0;">긴장은 자연스러운 것입니다</h3>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">완전히 없애려 하지 말고, 긍정적인 에너지로 전환하세요.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 면접 전날
    st.markdown("### 면접 전날")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("** 해야 할 것**")
        before_dos = [
            " 일찍 자기 (최소 7시간 수면)",
            " 준비물 미리 챙기기",
            "️ 면접장 위치/교통 확인",
            " 면접 복장 미리 준비",
            " 알람 여러 개 설정",
        ]
        for item in before_dos:
            st.markdown(f'<div class="calm-tip">{item}</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("** 피해야 할 것**")
        before_donts = [
            " 음주, 야식",
            " 늦게까지 영상 시청",
            " 새벽까지 벼락치기",
            " 과도한 카페인 섭취",
            " SNS로 다른 지원자 비교",
        ]
        for item in before_donts:
            st.markdown(f'<div class="checklist-item">{item}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # 면접 당일 아침
    st.markdown("### ️ 면접 당일 아침")

    morning_tips = [
        (" 가벼운 아침", "소화 잘 되는 음식으로, 배부르게 먹지 않기"),
        (" 물 충분히", "목이 마르지 않도록, 화장실 가기 편한 시간 계산"),
        (" 가벼운 스트레칭", "몸을 깨우고 긴장 풀기"),
        (" 거울 보며 미소 연습", "표정 근육 풀어주기"),
        ("⏰ 여유 있게 출발", "30분~1시간 일찍 도착하기"),
    ]

    col1, col2 = st.columns(2)
    for i, (title, desc) in enumerate(morning_tips):
        with col1 if i % 2 == 0 else col2:
            st.markdown(f"""
            <div class="calm-tip">
                <strong>{title}</strong><br/>
                <span style="font-size: 14px; color: #666;">{desc}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 긴장 풀기 기법
    st.markdown("### 긴장 풀기 기법 (면접 직전)")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="dress-card">
            <div style="font-size: 40px;">️</div>
            <h4>4-7-8 호흡법</h4>
            <hr/>
            <p style="font-size: 14px; text-align: left;">
            1. 4초간 코로 숨 들이쉬기<br/>
            2. 7초간 숨 참기<br/>
            3. 8초간 입으로 내쉬기<br/>
            4. 3~4회 반복
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="dress-card">
            <div style="font-size: 40px;"></div>
            <h4>파워포즈</h4>
            <hr/>
            <p style="font-size: 14px; text-align: left;">
            1. 화장실에서 2분간<br/>
            2. 양손 허리에 올리고<br/>
            3. 어깨 펴고 당당하게<br/>
            4. 자신감 호르몬 ↑
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="dress-card">
            <div style="font-size: 40px;"></div>
            <h4>긍정 확언</h4>
            <hr/>
            <p style="font-size: 14px; text-align: left;">
            • "나는 충분히 준비했다"<br/>
            • "나는 합격할 자격이 있다"<br/>
            • "긴장은 나를 더 빛나게 한다"<br/>
            • 마음속으로 반복
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 면접 중 긴장 관리
    st.markdown("### 면접 중 긴장 관리")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="success-card">
            <h4> 머리가 하얘질 때</h4>
            <ul style="font-size: 14px;">
                <li>"잠시만요, 생각을 정리하겠습니다"</li>
                <li>물 한 모금 마시기</li>
                <li>질문을 한 번 더 확인 요청</li>
                <li>관련 키워드부터 천천히</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="success-card">
            <h4> 손/목소리가 떨릴 때</h4>
            <ul style="font-size: 14px;">
                <li>손은 무릎 위에 자연스럽게</li>
                <li>테이블 아래서 주먹 쥐었다 펴기</li>
                <li>천천히, 또박또박 말하기</li>
                <li>미소 지으며 말하면 떨림 감소</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.info("**기억하세요:** 면접관도 여러분이 긴장하는 것을 알고 있습니다. 적당한 긴장감은 오히려 진지함으로 보일 수 있어요!")

# ----------------------------
# 탭 10: 2026 트렌드
# ----------------------------
with tab10:
    st.markdown('<div class="section-header"><h2> 2026 채용 트렌드</h2></div>', unsafe_allow_html=True)

    trends = HIRING_TRENDS_2026

    st.markdown(f"""
    <div class="tip-card">
        <h3 style="margin:0;"> 2026 키워드: {trends.get('summary', '속도전과 다양성 존중')}</h3>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">최신 채용 트렌드를 파악하고 전략적으로 준비하세요.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 전반적 특징
    st.markdown("### 2026 채용 전반적 특징")

    col1, col2 = st.columns(2)

    characteristics = trends.get("characteristics", [])
    half = len(characteristics) // 2

    with col1:
        for char in characteristics[:half]:
            st.markdown(f"""
            <div class="info-card">
                <p style="margin: 0;">️ {char}</p>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        for char in characteristics[half:]:
            st.markdown(f"""
            <div class="info-card">
                <p style="margin: 0;">️ {char}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 합격생 공통 성공 요인
    st.markdown("### 합격생 공통 성공 요인")

    success_factors = trends.get("success_factors", [])

    cols = st.columns(3)
    for i, factor in enumerate(success_factors):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="success-card" style="text-align: center;">
                <p style="margin: 0;">⭐ {factor}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 남성 지원자 정보
    st.markdown("### 남성 지원자 참고")

    male_info = trends.get("male_applicant", {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="info-card">
            <h4> 기본 스펙</h4>
            <p><strong>기준 학점:</strong> {male_info.get('gpa_baseline', 3.5)} 이상</p>
            <p><strong>참고:</strong> {male_info.get('note', '')}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="success-card">
            <h4> 합격 팁</h4>
            <p>{male_info.get('tip', '차별화된 경험과 확실한 지원동기가 중요')}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 항공사별 인재상
    st.markdown("### 항공사별 선호 인재상")

    col1, col2 = st.columns(2)

    fsc_airlines = ["대한항공", "아시아나항공"]
    lcc_airlines = ["제주항공", "진에어", "티웨이항공", "에어부산", "에어프레미아"]

    with col1:
        st.markdown("**️ FSC**")
        for airline in fsc_airlines:
            if airline in AIRLINE_PREFERRED_TYPE:
                info = AIRLINE_PREFERRED_TYPE[airline]
                st.markdown(f"""
                <div class="info-card">
                    <strong>️ {airline}</strong>: {info.get('nickname', '')}
                </div>
                """, unsafe_allow_html=True)

    with col2:
        st.markdown("**️ LCC**")
        for airline in lcc_airlines:
            if airline in AIRLINE_PREFERRED_TYPE:
                info = AIRLINE_PREFERRED_TYPE[airline]
                st.markdown(f"""
                <div class="info-card">
                    <strong>️ {airline}</strong>: {info.get('nickname', '')}
                </div>
                """, unsafe_allow_html=True)

# ----------------------------
# 탭 11: AI면접 대비
# ----------------------------
with tab11:
    st.markdown('<div class="section-header"><h2> AI 면접 완벽 대비</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="tip-card">
        <h3 style="margin:0;">AI 면접, 두려워하지 마세요!</h3>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">AI 면접은 공정한 기회입니다. 핵심 포인트만 알면 충분히 준비할 수 있습니다.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # AI 면접 도입 항공사
    st.info("️ **AI 면접 도입 항공사:** 대한항공, 아시아나항공, 제주항공, 진에어, 티웨이항공 등 대부분의 항공사가 1차 면접에 AI 역량 검사 도입")

    st.markdown("---")

    # AI 면접 유형
    st.markdown("### AI 면접 유형")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="dress-card">
            <div style="font-size: 40px;"></div>
            <h4>음성 답변형</h4>
            <hr/>
            <p style="font-size: 14px; text-align: left;">
            • 주어진 질문에 음성으로 답변<br/>
            • 1~2분 내외 답변 시간<br/>
            • 목소리 톤/속도/명확성 분석<br/>
            • 대표 플랫폼: 마이다스인, 뷰인터HR
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="dress-card">
            <div style="font-size: 40px;"></div>
            <h4>게임형 역량검사</h4>
            <hr/>
            <p style="font-size: 14px; text-align: left;">
            • 미니 게임 형태의 인지 능력 검사<br/>
            • 집중력, 판단력, 기억력 측정<br/>
            • 스트레스 상황 대처 능력<br/>
            • 대표: NCS게임, 역량게임
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="dress-card">
            <div style="font-size: 40px;"></div>
            <h4>상황판단형</h4>
            <hr/>
            <p style="font-size: 14px; text-align: left;">
            • 기내 상황 시나리오 제시<br/>
            • 최적의 대처 방안 선택<br/>
            • 서비스 마인드/협업 능력<br/>
            • 정답보다 일관성이 중요
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # AI 분석 항목
    st.markdown("### AI가 분석하는 항목")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="info-card">
            <h4> 표정 분석</h4>
            <ul style="font-size: 14px; margin: 10px 0;">
                <li>자연스러운 미소 유지</li>
                <li>눈 깜빡임 빈도 (너무 잦으면 긴장)</li>
                <li>시선 처리 (카메라 응시)</li>
                <li>표정 변화의 자연스러움</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="info-card">
            <h4> 음성 분석</h4>
            <ul style="font-size: 14px; margin: 10px 0;">
                <li>말의 속도 (너무 빠르거나 느림)</li>
                <li>목소리 크기와 안정성</li>
                <li>발음의 명확성</li>
                <li>침묵 시간 (Um, 어... 줄이기)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card">
            <h4> 내용 분석</h4>
            <ul style="font-size: 14px; margin: 10px 0;">
                <li>답변의 논리적 구조</li>
                <li>핵심 키워드 포함 여부</li>
                <li>구체적 사례 유무</li>
                <li>질문과의 연관성</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="info-card">
            <h4> 성향 분석</h4>
            <ul style="font-size: 14px; margin: 10px 0;">
                <li>외향성 / 내향성</li>
                <li>안정성 / 민감성</li>
                <li>성실성 / 유연성</li>
                <li>조직 적합도</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # AI 면접 핵심 팁
    st.markdown("### AI 면접 핵심 팁")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="success-card">
            <h4> 이렇게 하세요</h4>
            <ul style="margin: 10px 0;">
                <li><strong>카메라 정면 응시</strong> - 렌즈가 면접관 눈</li>
                <li><strong>밝은 조명</strong> - 얼굴이 잘 보이게</li>
                <li><strong>단정한 배경</strong> - 흰 벽 or 정리된 공간</li>
                <li><strong>헤드셋 사용</strong> - 음질 향상</li>
                <li><strong>미소 유지</strong> - 말 안 해도 표정 관리</li>
                <li><strong>두괄식 답변</strong> - 결론부터 명확하게</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="warning-card">
            <h4> 이것만은 피하세요</h4>
            <ul style="margin: 10px 0;">
                <li><strong>화면 외 시선</strong> - 대본 보는 듯한 인상</li>
                <li><strong>역광 조명</strong> - 얼굴 어두워짐</li>
                <li><strong>어지러운 배경</strong> - 집중도 저하</li>
                <li><strong>내장 마이크</strong> - 음질 불량</li>
                <li><strong>무표정</strong> - 성의 없어 보임</li>
                <li><strong>장황한 답변</strong> - 핵심이 묻힘</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 환경 체크리스트
    st.markdown("### ️ AI 면접 환경 체크리스트")

    env_checks = [
        (" 노트북/PC", "카메라 눈높이에 위치, 배터리 충분히 충전"),
        (" 인터넷", "유선 연결 권장, Wi-Fi는 안정적인지 확인"),
        (" 조명", "얼굴 정면에서 밝게, 역광 절대 금지"),
        (" 소음", "조용한 공간, 알람/알림 모두 끄기"),
        (" 오디오", "헤드셋 or 이어폰 권장, 마이크 테스트 필수"),
        (" 복장", "상의는 면접 복장, 하의도 만약을 대비해"),
    ]

    col1, col2 = st.columns(2)
    for i, (item, desc) in enumerate(env_checks):
        with col1 if i % 2 == 0 else col2:
            st.markdown(f"""
            <div class="calm-tip">
                <strong>{item}</strong><br/>
                <span style="font-size: 14px; color: #666;">{desc}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    st.info("**팁:** AI 면접 전에 해당 플랫폼의 연습 모드를 꼭 활용하세요! 실전처럼 여러 번 연습하면 훨씬 자연스러워집니다.")

# ----------------------------
# 탭 12: 영상면접 팁
# ----------------------------
with tab12:
    st.markdown('<div class="section-header"><h2> 영상 면접 완벽 가이드</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="tip-card">
        <h3 style="margin:0;">화면 속에서도 빛나는 법!</h3>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">비대면 면접은 대면보다 준비가 더 중요합니다. 기술적인 부분까지 완벽히 준비하세요.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 영상 면접 유형
    st.markdown("### 영상 면접 유형")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="dress-card">
            <div style="font-size: 40px;"></div>
            <h4>실시간 화상 면접</h4>
            <hr/>
            <p style="font-size: 14px; text-align: left;">
            • Zoom, Teams, Google Meet 등 활용<br/>
            • 면접관과 실시간 소통<br/>
            • 대면과 유사한 형태<br/>
            • 즉각적인 반응과 대화 필요<br/>
            <br/>
            <strong>특징:</strong> 긴장감 높지만 소통 가능
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="dress-card">
            <div style="font-size: 40px;">⏺️</div>
            <h4>녹화형 면접</h4>
            <hr/>
            <p style="font-size: 14px; text-align: left;">
            • 질문이 화면에 표시되면 답변 녹화<br/>
            • 준비 시간 + 답변 시간 제한<br/>
            • 1회 기회 (재촬영 불가가 대부분)<br/>
            • AI 분석과 함께 진행되기도<br/>
            <br/>
            <strong>특징:</strong> 혼자서 카메라에 말하는 연습 필수
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 카메라 앵글 가이드
    st.markdown("### 완벽한 카메라 앵글")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="success-card">
            <h4> Good</h4>
            <p style="font-size: 14px;">
            • 카메라가 눈높이<br/>
            • 얼굴~가슴 상단 보임<br/>
            • 머리 위 여백 적당히<br/>
            • 정면 또는 살짝 각도
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="warning-card">
            <h4> 위에서 내려다봄</h4>
            <p style="font-size: 14px;">
            • 이마가 커보임<br/>
            • 턱이 돌출되어 보임<br/>
            • 자신감 없어 보임<br/>
            • 노트북 기본 위치 주의!
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="warning-card">
            <h4> 아래에서 올려다봄</h4>
            <p style="font-size: 14px;">
            • 콧구멍이 보임<br/>
            • 턱살이 강조됨<br/>
            • 위압적으로 보일 수 있음<br/>
            • 스마트폰 손에 들고 X
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-card">
        <strong> 꿀팁:</strong> 노트북은 책이나 박스 위에 올려 카메라가 눈높이에 오도록 하세요.
        스마트폰의 경우 삼각대 사용을 권장합니다.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 조명 가이드
    st.markdown("### 조명 세팅 가이드")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="success-card">
            <h4> 좋은 조명</h4>
            <ul style="font-size: 14px;">
                <li><strong>3점 조명:</strong> 정면 + 양옆 45도</li>
                <li><strong>자연광:</strong> 창문을 정면에 두기</li>
                <li><strong>링라이트:</strong> 카메라 뒤에 설치</li>
                <li><strong>밝기:</strong> 얼굴이 환하게</li>
                <li><strong>색온도:</strong> 따뜻한 빛 (너무 푸르면 창백)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="warning-card">
            <h4> 나쁜 조명</h4>
            <ul style="font-size: 14px;">
                <li><strong>역광:</strong> 창문을 등 뒤에 두면 실루엣만</li>
                <li><strong>위에서만:</strong> 눈 밑 그림자 생김</li>
                <li><strong>한쪽만:</strong> 얼굴 반이 어두움</li>
                <li><strong>형광등:</strong> 피부가 창백해 보임</li>
                <li><strong>너무 밝음:</strong> 하얗게 날아감</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 배경 가이드
    st.markdown("### ️ 배경 세팅")

    bg_options = [
        (" 흰 벽", "가장 무난하고 깔끔한 선택"),
        (" 정돈된 책장", "지적인 이미지, 단 너무 화려하지 않게"),
        (" 단색 커튼", "깔끔하고 집중도 높음"),
        (" 침대/이불", "비전문적인 이미지"),
        (" 지저분한 방", "정리정돈 능력 의심"),
        (" 가상 배경", "부자연스러움, 움직이면 깨짐"),
    ]

    col1, col2 = st.columns(2)
    for i, (item, desc) in enumerate(bg_options):
        with col1 if i < 3 else col2:
            is_good = item.startswith("")
            card_class = "success-card" if is_good else "warning-card"
            st.markdown(f"""
            <div class="{card_class}" style="padding: 10px 15px; margin: 5px 0;">
                <strong>{item}</strong>: {desc}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 영상 면접 체크리스트
    st.markdown("### 영상 면접 D-1 체크리스트")

    checklist = [
        "카메라/마이크 테스트 완료",
        "인터넷 속도 확인 (업로드 최소 10Mbps)",
        "면접 플랫폼 설치 및 로그인 테스트",
        "배경 정리 및 조명 세팅",
        "복장 준비 (상하의 모두)",
        "스마트폰 무음/방해금지 설정",
        "가족에게 면접 시간 알리기",
        "비상 연락처 (채용담당자) 확인",
    ]

    col1, col2 = st.columns(2)
    for i, item in enumerate(checklist):
        with col1 if i % 2 == 0 else col2:
            st.markdown(f'<div class="checklist-item"> {item}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # 비상 상황 대처
    st.markdown("### 🆘 비상 상황 대처법")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="info-card">
            <h4> 인터넷이 끊겼을 때</h4>
            <ul style="font-size: 14px;">
                <li>당황하지 말고 재접속 시도</li>
                <li>스마트폰 테더링으로 전환</li>
                <li>채팅창에 상황 설명</li>
                <li>안 되면 전화로 연락</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card">
            <h4> 소음이 발생했을 때</h4>
            <ul style="font-size: 14px;">
                <li>"죄송합니다, 잠시만요"</li>
                <li>마이크 일시 음소거</li>
                <li>소음 제거 후 재개</li>
                <li>사과하고 답변 이어가기</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.info("**핵심:** 기술적 문제가 생겨도 침착하게 대처하는 모습이 오히려 플러스가 될 수 있습니다!")

# ----------------------------
# 탭 13: 항공사별 특화 정보
# ----------------------------
with tab13:
    st.markdown('<div class="section-header"><h2> 항공사별 면접 특화 정보</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="tip-card">
        <h3 style="margin:0;">항공사마다 원하는 인재상이 다릅니다!</h3>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">지원하는 항공사의 특성을 파악하고 맞춤 전략을 세우세요.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 항공사 선택
    airline_choice = st.selectbox(
        "항공사를 선택하세요",
        ["대한항공", "아시아나항공", "제주항공", "진에어", "티웨이항공", "에어부산", "에어서울", "이스타항공", "에어프레미아", "에어로케이", "파라타항공"]
    )

    st.markdown("---")

    # 항공사별 상세 정보
    airline_data = {
        "대한항공": {
            "type": "FSC",
            "slogan": "Excellence in Flight",
            "values": ["안전", "신뢰", "품격", "혁신"],
            "image": "품격 있고 우아한 이미지, 클래식한 스타일",
            "process": ["서류전형", "1차 면접 (AI역량검사)", "2차 면접 (실무진)", "3차 면접 (임원)", "신체검사/신원조회"],
            "questions": [
                "대한항공 승무원이 갖춰야 할 가장 중요한 자질은?",
                "글로벌 항공사로서 대한항공의 경쟁력은?",
                "외국어 능력을 활용한 경험이 있나요?",
                "팀에서 갈등이 생겼을 때 어떻게 해결했나요?"
            ],
            "tips": [
                "품격과 전문성을 강조하는 답변 준비",
                "글로벌 마인드와 어학 능력 어필",
                "차분하고 논리적인 답변 스타일",
                "대한항공 최근 뉴스/이슈 숙지 필수"
            ],
            "color": "#003876"
        },
        "아시아나항공": {
            "type": "FSC",
            "slogan": "Always with you",
            "values": ["안전", "고객감동", "신뢰", "도전"],
            "image": "따뜻하고 세련된 이미지, 부드러운 미소",
            "process": ["서류전형", "1차 면접 (AI/인적성)", "2차 면접 (실무진)", "3차 면접 (임원)", "신체검사"],
            "questions": [
                "아시아나항공을 선택한 이유는?",
                "고객 감동 서비스 경험을 말해주세요",
                "힘든 상황에서 어떻게 극복했나요?",
                "아시아나의 서비스 특징은 무엇이라 생각하나요?"
            ],
            "tips": [
                "따뜻한 서비스 마인드 강조",
                "'고객감동' 키워드 활용",
                "친근하면서도 프로페셔널한 태도",
                "아시아나의 서비스 차별점 숙지"
            ],
            "color": "#ED1C24"
        },
        "제주항공": {
            "type": "LCC",
            "slogan": "New Paradigm Airline",
            "values": ["안전", "효율", "고객중심", "혁신"],
            "image": "밝고 활기찬 이미지, 환한 미소",
            "process": ["서류전형", "1차 면접 (AI역량)", "2차 면접 (실무+임원)", "신체검사"],
            "questions": [
                "LCC를 선택한 이유는?",
                "제주항공의 강점은 무엇이라 생각하나요?",
                "체력 관리는 어떻게 하시나요?",
                "스트레스 상황에서 어떻게 대처하나요?"
            ],
            "tips": [
                "밝고 에너지 넘치는 모습 어필",
                "LCC의 특성과 장점 이해",
                "체력과 긍정적 마인드 강조",
                "효율적인 서비스 마인드"
            ],
            "color": "#FF6600"
        },
        "진에어": {
            "type": "LCC",
            "slogan": "Fly, better fly JIN AIR",
            "values": ["안전", "젊음", "도전", "즐거움"],
            "image": "젊고 트렌디한 이미지, 자유로운 분위기",
            "process": ["서류전형", "1차 면접 (인적성/AI)", "2차 면접 (실무+임원)", "신체검사"],
            "questions": [
                "진에어의 이미지는 어떻다고 생각하나요?",
                "젊은 감각을 살린 서비스 아이디어가 있나요?",
                "팀원들과 즐겁게 일한 경험은?",
                "SNS나 트렌드에 관심이 많으신가요?"
            ],
            "tips": [
                "젊고 트렌디한 이미지 강조",
                "창의적인 아이디어 준비",
                "팀워크와 유연성 어필",
                "진에어 SNS 콘텐츠 확인"
            ],
            "color": "#00A651"
        },
        "티웨이항공": {
            "type": "LCC",
            "slogan": "함께라서 행복한 하늘길",
            "values": ["안전", "친근함", "신뢰", "함께"],
            "image": "친근하고 건강한 이미지, 따뜻한 미소",
            "process": ["서류전형", "1차 면접 (AI역량)", "2차 면접 (실무+임원)", "신체검사"],
            "questions": [
                "티웨이항공의 슬로건에 대해 어떻게 생각하나요?",
                "고객에게 친근함을 줄 수 있는 방법은?",
                "건강 관리는 어떻게 하시나요?",
                "함께 일하고 싶은 동료상은?"
            ],
            "tips": [
                "친근하고 따뜻한 이미지 강조",
                "'함께'라는 가치 어필",
                "건강하고 활기찬 모습",
                "티웨이의 가족적인 분위기 이해"
            ],
            "color": "#E4002B"
        },
        "에어부산": {
            "type": "LCC",
            "slogan": "Fun & Fresh",
            "values": ["안전", "즐거움", "신선함", "부산"],
            "image": "발랄하고 시원한 이미지, 부산 느낌",
            "process": ["서류전형", "1차 면접", "2차 면접 (최종)", "신체검사"],
            "questions": [
                "부산에 대해 얼마나 알고 계신가요?",
                "에어부산만의 특색은 무엇이라 생각하나요?",
                "Fun & Fresh를 어떻게 표현할 수 있을까요?",
                "지방 기반 항공사의 장점은?"
            ],
            "tips": [
                "부산/지역 연고에 대한 이해",
                "발랄하고 시원한 이미지",
                "아시아나 계열사 특성 파악",
                "부산 사투리 친근하게 활용 가능"
            ],
            "color": "#0066B3"
        },
        "에어서울": {
            "type": "LCC",
            "slogan": "Always Fresh",
            "values": ["안전", "신선함", "세련됨", "글로벌"],
            "image": "세련되고 신선한 이미지",
            "process": ["서류전형", "1차 면접", "2차 면접 (최종)", "신체검사"],
            "questions": [
                "에어서울의 노선 특징을 알고 계신가요?",
                "젊은 여행객 대상 서비스 아이디어는?",
                "세련된 서비스란 무엇이라 생각하나요?",
                "아시아나항공과의 차이점은?"
            ],
            "tips": [
                "아시아나 계열 특성 이해",
                "세련되고 도시적인 이미지",
                "동남아 단거리 노선 특화",
                "젊은 층 타겟 마케팅 이해"
            ],
            "color": "#FF69B4"
        },
        "이스타항공": {
            "type": "LCC",
            "slogan": "희망의 날개",
            "values": ["안전", "희망", "도전", "성장"],
            "image": "희망차고 도전적인 이미지",
            "process": ["서류전형", "면접 (통합)", "신체검사"],
            "questions": [
                "이스타항공에 대해 알고 있는 것은?",
                "회사가 어려운 시기를 겪었을 때 어떻게 대처했나요?",
                "새로운 시작에 대한 각오는?",
                "이스타항공의 미래 전망은?"
            ],
            "tips": [
                "회사 현황과 재도약 상황 파악",
                "도전 정신과 긍정적 마인드",
                "함께 성장하겠다는 의지",
                "진정성 있는 지원동기"
            ],
            "color": "#0033A0"
        },
        "에어프레미아": {
            "type": "HSC",
            "slogan": "합리적인 프리미엄",
            "values": ["안전", "합리", "프리미엄", "혁신"],
            "image": "세련되고 전문적인 이미지",
            "process": ["서류전형", "1차 면접 (실무)", "2차 면접 (임원)", "신체검사"],
            "questions": [
                "HSC(하이브리드 항공사)의 특징은?",
                "에어프레미아의 차별점은 무엇이라 생각하나요?",
                "합리적인 프리미엄 서비스란?",
                "중장거리 노선의 어려움은?"
            ],
            "tips": [
                "HSC 컨셉 명확히 이해",
                "중장거리 노선 특화",
                "합리적 프리미엄 개념",
                "경영진 인터뷰/뉴스 확인"
            ],
            "color": "#1E3A5F"
        },
        "에어로케이": {
            "type": "LCC",
            "slogan": "K-Spirit Airline",
            "values": ["안전", "한국", "청춘", "도전"],
            "image": "젊고 한국적인 이미지",
            "process": ["서류전형", "면접", "신체검사"],
            "questions": [
                "신생 항공사에 지원한 이유는?",
                "K-Spirit을 어떻게 표현할 수 있을까요?",
                "청주 기반 항공사의 장점은?",
                "새로운 항공사와 함께 성장하고 싶은 이유는?"
            ],
            "tips": [
                "신생 항공사 특성 이해",
                "도전 정신과 성장 의지",
                "청주/충청권 이해",
                "한국적 서비스 아이디어"
            ],
            "color": "#003DA5"
        },
        "파라타항공": {
            "type": "LCC",
            "slogan": "Paradise in the Sky",
            "values": ["안전", "휴양", "프리미엄", "새로움"],
            "image": "프리미엄 휴양지 느낌, 세련된 이미지",
            "process": ["서류전형", "면접", "신체검사"],
            "questions": [
                "신생 항공사인 파라타항공에 지원한 이유는?",
                "파라타항공의 컨셉에 대해 어떻게 생각하나요?",
                "휴양지 노선 특화 서비스 아이디어가 있나요?",
                "새로운 항공사와 함께 성장할 각오는?"
            ],
            "tips": [
                "신생 항공사 특성과 비전 이해",
                "휴양지/리조트 서비스 마인드",
                "프리미엄 서비스에 대한 이해",
                "함께 성장하겠다는 의지 표현"
            ],
            "color": "#00CED1"
        }
    }

    data = airline_data.get(airline_choice, airline_data["대한항공"])

    # 기본 정보
    col1, col2 = st.columns([1, 2])

    with col1:
        type_color = {"FSC": "#003876", "LCC": "#FF6600", "HSC": "#1E3A5F"}.get(data["type"], "#666")
        st.markdown(f"""
        <div style="background: {data['color']}; padding: 30px; border-radius: 15px; color: white; text-align: center;">
            <h2 style="margin: 0;">️ {airline_choice}</h2>
            <p style="font-size: 14px; opacity: 0.9; margin: 10px 0;">{data['slogan']}</p>
            <span style="background: white; color: {data['color']}; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold;">{data['type']}</span>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="info-card">
            <h4> 인재상</h4>
            <p>{', '.join(data['values'])}</p>
            <h4> 선호 이미지</h4>
            <p>{data['image']}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 면접 프로세스
    st.markdown(f"###  {airline_choice} 면접 프로세스")

    process_cols = st.columns(len(data['process']))
    for i, step in enumerate(data['process']):
        with process_cols[i]:
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background: {'#f0f0f0' if i % 2 == 0 else '#e8e8e8'}; border-radius: 10px;">
                <div style="background: {data['color']}; color: white; width: 30px; height: 30px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: bold;">{i+1}</div>
                <p style="margin: 10px 0 0 0; font-size: 13px;">{step}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 예상 질문
    st.markdown(f"###  {airline_choice} 예상 질문")

    for i, q in enumerate(data['questions'], 1):
        st.markdown(f"""
        <div class="info-card" style="border-left-color: {data['color']};">
            <strong>Q{i}.</strong> {q}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 면접 팁
    st.markdown(f"###  {airline_choice} 면접 팁")

    col1, col2 = st.columns(2)
    for i, tip in enumerate(data['tips']):
        with col1 if i % 2 == 0 else col2:
            st.markdown(f"""
            <div class="success-card">
                 {tip}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    st.info(f" **최종 팁:** {airline_choice}의 공식 홈페이지, 인스타그램, 최근 뉴스를 반드시 확인하세요. 면접관은 지원자가 회사에 대해 얼마나 알고 있는지 궁금해합니다!")

# ----------------------------
# 탭 14: 자가진단
# ----------------------------
with tab14:
    st.markdown('<div class="section-header"><h2> 면접 준비도 자가진단</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="tip-card">
        <h3 style="margin:0;"> 나의 면접 준비 수준을 체크해보세요</h3>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">5개 분야별로 준비 상태를 점검하고, 부족한 부분을 집중 보강하세요.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    # 이전 진단 결과 로드
    assessment_data = load_assessment()

    # 분야별 체크리스트
    st.markdown("### 분야별 준비도 체크")
    st.markdown("각 항목을 읽고 현재 준비 상태에 체크하세요.")

    results = {}
    for cat_key, cat_info in ASSESSMENT_CATEGORIES.items():
        with st.expander(f"{cat_info['icon']} {cat_info['name']}", expanded=False):
            checked = 0
            for i, item in enumerate(cat_info["items"]):
                key = f"assess_{cat_key}_{i}"
                if st.checkbox(item, key=key):
                    checked += 1
            results[cat_key] = {
                "name": cat_info["name"],
                "checked": checked,
                "total": len(cat_info["items"]),
                "pct": int((checked / len(cat_info["items"])) * 100)
            }

    # 결과 분석
    st.markdown("---")
    st.markdown("### 진단 결과")

    total_checked = sum(r["checked"] for r in results.values())
    total_items = sum(r["total"] for r in results.values())
    overall_pct = int((total_checked / total_items) * 100) if total_items > 0 else 0

    # 종합 점수
    if overall_pct >= 80:
        grade = "A"
        grade_color = "#10b981"
        grade_msg = "훌륭합니다! 면접 준비가 잘 되어 있어요."
    elif overall_pct >= 60:
        grade = "B"
        grade_color = "#3b82f6"
        grade_msg = "좋습니다! 조금만 더 보강하면 완벽해요."
    elif overall_pct >= 40:
        grade = "C"
        grade_color = "#f59e0b"
        grade_msg = "기본기는 있지만, 약한 분야 보강이 필요해요."
    else:
        grade = "D"
        grade_color = "#ef4444"
        grade_msg = "아직 준비할 것이 많아요. 하나씩 차근차근!"

    st.markdown(f"""
    <div style="background: white; border-radius: 16px; padding: 25px; box-shadow: 0 2px 15px rgba(0,0,0,0.05); text-align: center; margin-bottom: 20px;">
        <div style="font-size: 3rem; font-weight: 800; color: {grade_color};">{grade}</div>
        <div style="font-size: 1.5rem; font-weight: 700; color: #1e3a5f; margin: 5px 0;">종합 준비도 {overall_pct}%</div>
        <div style="font-size: 0.9rem; color: #64748b;">{grade_msg}</div>
        <div style="margin-top: 15px; height: 12px; background: #e2e8f0; border-radius: 6px; overflow: hidden;">
            <div style="height: 100%; width: {overall_pct}%; background: {grade_color}; border-radius: 6px;"></div>
        </div>
        <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 8px;">{total_checked}/{total_items} 항목 완료</div>
    </div>
    """, unsafe_allow_html=True)

    # 분야별 결과 바
    cols = st.columns(5)
    for idx, (cat_key, result) in enumerate(results.items()):
        with cols[idx]:
            pct = result["pct"]
            cat_info = ASSESSMENT_CATEGORIES[cat_key]
            if pct >= 80:
                bar_color = "#10b981"
            elif pct >= 60:
                bar_color = "#3b82f6"
            elif pct >= 40:
                bar_color = "#f59e0b"
            else:
                bar_color = "#ef4444"

            st.markdown(f"""
            <div style="text-align: center; padding: 15px 5px;">
                <div style="font-size: 1.5rem;">{cat_info["icon"]}</div>
                <div style="font-size: 0.75rem; font-weight: 600; color: #334155; margin: 5px 0;">{cat_info["name"]}</div>
                <div style="height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden;">
                    <div style="height: 100%; width: {pct}%; background: {bar_color}; border-radius: 4px;"></div>
                </div>
                <div style="font-size: 0.8rem; font-weight: 700; color: {bar_color}; margin-top: 5px;">{pct}%</div>
            </div>
            """, unsafe_allow_html=True)

    # 약점 분석 + 추천
    st.markdown("---")
    st.markdown("### 맞춤 보강 추천")

    weak_areas = [(k, v) for k, v in results.items() if v["pct"] < 60]
    if weak_areas:
        weak_areas.sort(key=lambda x: x[1]["pct"])
        recommendations_map = {
            "image": {"page": "이미지메이킹", "tip": "이미지메이킹 페이지에서 셀프체크와 NG사례를 확인하세요"},
            "answer": {"page": "모의면접", "tip": "모의면접으로 실전 답변 연습을 해보세요"},
            "english": {"page": "영어면접", "tip": "영어면접 페이지에서 카테고리별 질문을 연습하세요"},
            "fitness": {"page": "국민체력", "tip": "국민체력 페이지에서 종목별 기준과 운동법을 확인하세요"},
            "knowledge": {"page": "항공사퀴즈", "tip": "항공 상식 퀴즈로 기본 지식을 점검하세요"},
        }
        for cat_key, result in weak_areas:
            rec = recommendations_map.get(cat_key, {})
            cat_info = ASSESSMENT_CATEGORIES[cat_key]
            st.markdown(f"""
            <div style="background: #fef2f2; border-left: 4px solid #ef4444; border-radius: 10px; padding: 15px 20px; margin: 8px 0; display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 1.5rem;">{cat_info["icon"]}</div>
                <div>
                    <div style="font-weight: 600; color: #991b1b;">{cat_info["name"]} - {result["pct"]}% (보강 필요)</div>
                    <div style="font-size: 0.85rem; color: #64748b; margin-top: 3px;">{rec.get("tip", "해당 분야를 집중 연습하세요")}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: #f0fff4; border-left: 4px solid #38a169; border-radius: 10px; padding: 15px 20px;">
            <div style="font-weight: 600; color: #22543d;"> 모든 분야가 60% 이상! 골고루 잘 준비하고 있어요.</div>
            <div style="font-size: 0.85rem; color: #64748b; margin-top: 3px;">약한 분야 없이 균형잡힌 준비 상태입니다. 실전 모의면접으로 마무리하세요!</div>
        </div>
        """, unsafe_allow_html=True)

    # 진단 결과 저장
    st.markdown("---")
    if st.button("진단 결과 저장", use_container_width=True):
        save_record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "overall_pct": overall_pct,
            "grade": grade,
            "details": {k: v["pct"] for k, v in results.items()}
        }
        assessment_data["results"].append(save_record)
        # 최근 20개만 유지
        assessment_data["results"] = assessment_data["results"][-20:]
        save_assessment(assessment_data)
        st.success("진단 결과가 저장되었습니다!")

    # 이전 진단 기록
    if assessment_data.get("results"):
        with st.expander("이전 진단 기록"):
            for record in reversed(assessment_data["results"][-5:]):
                date = record.get("date", "")
                pct = record.get("overall_pct", 0)
                g = record.get("grade", "-")
                details = record.get("details", {})
                detail_str = " | ".join([f"{ASSESSMENT_CATEGORIES[k]['icon']}{v}%" for k, v in details.items()])
                st.markdown(f"**{date}** - 등급 **{g}** ({pct}%) - {detail_str}")

# div 닫기
st.markdown('</div>', unsafe_allow_html=True)

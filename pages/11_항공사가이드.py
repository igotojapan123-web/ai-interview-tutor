# pages/11_항공사가이드.py
# 항공사별 면접 가이드 - 사실 기반 정보 (국내 11개 항공사)

import streamlit as st

# 구글 번역 방지
st.set_page_config(page_title="항공사 가이드", page_icon="✈️", layout="wide")

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="항공사 가이드")
except ImportError:
    pass


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

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AIRLINES, AIRLINE_TYPE
from auth_utils import check_tester_password

# ----------------------------
# 비밀번호 보호
# ----------------------------
check_tester_password()

# ----------------------------
# CSS 스타일링
# ----------------------------
st.markdown("""
<style>
.info-card {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
    border-left: 4px solid #667eea;
}

.process-step {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    padding: 12px;
    text-align: center;
    margin: 4px;
}

.step-number {
    font-size: 20px;
    font-weight: bold;
}

.step-name {
    font-size: 11px;
}

.source-box {
    background: #f1f3f4;
    border-radius: 8px;
    padding: 12px;
    font-size: 12px;
    color: #5f6368;
}

.airline-card {
    background: white;
    border-radius: 12px;
    padding: 16px;
    margin: 8px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border-left: 4px solid #667eea;
}

.airline-card.fsc {
    border-left-color: #667eea;
}

.airline-card.lcc {
    border-left-color: #f59e0b;
}

.airline-card.hsc {
    border-left-color: #10b981;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# 채용 페이지 URL (실제 확인된 URL)
# ----------------------------
AIRLINE_CAREER_URLS = {
    "대한항공": "https://koreanair.recruiter.co.kr/",
    "아시아나항공": "https://flyasiana.recruiter.co.kr/",
    "진에어": "https://jinair.recruiter.co.kr/",
    "제주항공": "https://jejuair.recruiter.co.kr/",
    "티웨이항공": "https://twayair.recruiter.co.kr/",
    "에어부산": "https://airbusan.recruiter.co.kr/",
    "에어서울": "https://flyairseoul.com/",
    "이스타항공": "https://www.eastarjet.com/",
    "에어로케이": "https://aerok-recruiter.career.greetinghr.com/",
    "에어프레미아": "https://airpremia.career.greetinghr.com/",
    "파라타항공": "https://parataair.recruiter.co.kr/",
}

# ----------------------------
# 사실 기반 항공사별 면접 가이드 데이터 (11개 항공사)
# (출처: 각 항공사 공식 채용공고, 뉴스 보도)
# ----------------------------
AIRLINE_INTERVIEW_GUIDE = {
    "대한항공": {
        "type": "FSC",
        "slogan": "Excellence in Flight",
        "process": [
            {"name": "서류전형", "detail": "자기소개서 3개 항목 (600자 이내)"},
            {"name": "1차면접 (온라인)", "detail": "7~8인 1조, 면접관 2명, 20분, Standing 진행"},
            {"name": "2차면접 / 영어구술Test", "detail": "영어 구술 능력 평가"},
            {"name": "3차면접 / 인성검사", "detail": "인성 평가"},
            {"name": "건강검진 / 수영Test", "detail": "수영 25m 완영 필수"},
            {"name": "최종합격", "detail": ""},
        ],
        "requirements": {
            "학력": "기졸업자 또는 졸업예정자",
            "영어": "TOEIC 550점 / TOEIC Speaking IM / OPIc IM 이상",
            "시력": "교정시력 1.0 이상",
            "수영": "25m 완영 필수",
            "기타": "병역필 또는 면제자, 해외여행 결격사유 없는 자",
        },
        "interview_tips": [
            "1차 면접은 Standing으로 진행, 회사 및 객실승무직 이해도/지원동기 중심 질의",
            "자기소개서는 1차/2차/3차 모든 면접에서 면접관이 참고",
            "통합 항공사 출범 대비 글로벌 역량 강조",
        ],
        "source": "대한항공 뉴스룸, 대한항공 채용 홈페이지 (2025년 9월 공고)",
        "source_url": "https://news.koreanair.com/",
    },
    "아시아나항공": {
        "type": "FSC",
        "slogan": "아름다운 사람들",
        "process": [
            {"name": "서류전형", "detail": "입사지원서 접수"},
            {"name": "1차면접", "detail": ""},
            {"name": "2차면접", "detail": ""},
            {"name": "3차면접", "detail": ""},
            {"name": "건강검진 / 수영Test", "detail": "수영 테스트 포함"},
            {"name": "최종합격", "detail": "인턴 24개월 후 정규직 전환 가능"},
        ],
        "requirements": {
            "학력": "학력 무관",
            "영어": "TOEIC 550점 / TOEIC Speaking IM1 / OPIc IM 이상 (2023.11.01 이후 성적)",
            "시력": "교정시력 1.0 이상",
            "기타": "기졸업자 또는 졸업예정자, 해외여행 결격사유 없는 자",
        },
        "interview_tips": [
            "대한항공 채용 절차와 유사하게 개편됨",
            "인턴 24개월 근무 후 심사를 거쳐 정규직 전환",
            "통합 항공사 출범 예정",
        ],
        "source": "아시아나항공 채용 홈페이지 (2025년 11월 공고)",
        "source_url": "https://flyasiana.recruiter.co.kr/",
    },
    "진에어": {
        "type": "LCC",
        "slogan": "Fun, Young, Dynamic",
        "process": [
            {"name": "서류전형", "detail": "입사지원서 접수"},
            {"name": "영상전형", "detail": "영상 제출"},
            {"name": "1차면접", "detail": ""},
            {"name": "2차면접", "detail": ""},
            {"name": "건강검진", "detail": ""},
            {"name": "최종합격", "detail": "약 9주간 교육 후 실무 투입"},
        ],
        "requirements": {
            "학력": "기졸업자 또는 졸업예정자 (8월 이내)",
            "영어": "TOEIC 550점 / TOEIC Speaking IM1 / OPIc IM 이상",
            "시력": "교정시력 1.0 이상",
            "기타": "해외여행 결격사유 없는 자",
        },
        "preferred": ["일본어 우수자", "중국어 우수자"],
        "interview_tips": [
            "서울/부산 지역별 채용 진행",
            "2027년 통합 LCC 출범 대비 부산 거점 별도 모집",
            "최종 합격자는 약 9주간 교육 과정 이수 후 실무 투입",
        ],
        "source": "진에어 공식 발표 (2026년 1월), 헤럴드경제",
        "source_url": "https://jinair.recruiter.co.kr/",
    },
    "제주항공": {
        "type": "LCC",
        "slogan": "Fly, Better Fly",
        "process": [
            {"name": "서류전형", "detail": ""},
            {"name": "온라인 역량검사", "detail": "역량검사"},
            {"name": "영상면접", "detail": ""},
            {"name": "1차면접", "detail": ""},
            {"name": "2차면접", "detail": ""},
            {"name": "채용검진", "detail": ""},
            {"name": "최종합격", "detail": ""},
        ],
        "requirements": {
            "학력": "학력 제한 없음",
            "영어": "TOEIC 600점 / TOEIC Speaking IM1 / OPIc IM1 이상",
            "시력": "교정시력 1.0 이상",
            "기타": "해외여행 결격사유 없는 자",
        },
        "preferred": ["일본어 특기자 (언어특기전형)", "중국어 특기자 (언어특기전형)"],
        "interview_tips": [
            "온라인 역량검사와 영상 면접 진행",
            "일본어/중국어 특기자는 '언어특기전형' 별도 지원 가능",
            "학력 제한 없음 (열린 채용)",
        ],
        "source": "제주항공 채용 홈페이지 (2025년 하반기 공고)",
        "source_url": "https://jejuair.recruiter.co.kr/",
    },
    "티웨이항공": {
        "type": "LCC",
        "slogan": "즐거운 여행의 시작",
        "process": [
            {"name": "서류전형", "detail": ""},
            {"name": "역량검사 / 영상면접", "detail": ""},
            {"name": "1차면접", "detail": ""},
            {"name": "2차면접", "detail": ""},
            {"name": "채용검진", "detail": ""},
            {"name": "최종합격", "detail": "인턴 1년 후 정규직 전환"},
        ],
        "requirements": {
            "학력": "기졸업자 또는 졸업예정자",
            "영어": "TOEIC 600점 / TOEIC Speaking IM / OPIc IM 이상",
            "시력": "교정시력 1.0 이상",
            "기타": "해외여행 결격사유 없는 자",
        },
        "preferred": ["일본어 능력 우수자", "중국어 능력 우수자", "관련 자격증 소지자"],
        "interview_tips": [
            "최종 합격자는 인턴사원으로 1년 근무 후 심사를 거쳐 정규직 전환",
            "대구/부산 지역 채용 별도 진행",
            "외국어 능력 우수자 우대",
        ],
        "source": "티웨이항공 채용 공고 (2025년), 부산일보, 서울경제",
        "source_url": "https://twayair.recruiter.co.kr/",
    },
    "에어부산": {
        "type": "LCC",
        "slogan": "부산의 자부심",
        "process": [
            {"name": "서류 / 영상전형", "detail": ""},
            {"name": "1차면접 (토론)", "detail": "그룹 토론 면접"},
            {"name": "역량검사 (온라인)", "detail": ""},
            {"name": "2차면접", "detail": ""},
            {"name": "건강검진", "detail": ""},
            {"name": "최종합격", "detail": ""},
        ],
        "requirements": {
            "학력": "학력 무관",
            "시력": "교정시력 1.0 이상",
            "기타": "해외여행 결격사유 없는 자",
        },
        "preferred": ["부산/경남 거주자"],
        "interview_tips": [
            "1차 면접은 그룹 토론 형식으로 진행",
            "부산 거점 항공사로 지역 거주자 우대",
            "아시아나항공 자회사",
        ],
        "source": "에어부산 채용 공고 (2025년 7월)",
        "source_url": "https://airbusan.recruiter.co.kr/",
    },
    "에어서울": {
        "type": "LCC",
        "slogan": "프리미엄 LCC",
        "process": [
            {"name": "서류전형", "detail": "입사지원서 접수"},
            {"name": "1차면접 (토론)", "detail": "토론 면접"},
            {"name": "역량검사 (온라인)", "detail": ""},
            {"name": "2차면접 / 영어면접", "detail": "영어 면접 포함"},
            {"name": "건강검진", "detail": ""},
            {"name": "최종합격", "detail": "인턴 2년 후 정규직 전환 가능"},
        ],
        "requirements": {
            "학력": "기졸업자 또는 졸업예정자",
            "영어": "TOEIC 550점 / TOEIC Speaking IM1 / OPIc IM1 이상 (2023.12.02 이후 성적)",
            "시력": "교정시력 1.0 이상",
            "기타": "해외여행 결격사유 없는 자",
        },
        "preferred": ["중국어 우수자", "일본어 우수자"],
        "interview_tips": [
            "아시아나항공 자회사",
            "인턴 2년 근무 후 심사를 거쳐 정규직 전환",
            "아시아 노선 중심으로 제2외국어 우대",
        ],
        "source": "에어서울 채용 공고 (2025년 12월), airnews.co.kr",
        "source_url": "https://flyairseoul.com/",
    },
    "이스타항공": {
        "type": "LCC",
        "slogan": "새로운 도약",
        "process": [
            {"name": "서류전형", "detail": "합격자 비율 기존 대비 약 2배 확대"},
            {"name": "상황대처면접", "detail": "롤플레잉, 그룹미션, 개인평가"},
            {"name": "체력TEST", "detail": "오래달리기, 높이뛰기, 목소리 데시벨 체크"},
            {"name": "임원면접", "detail": ""},
            {"name": "채용검진", "detail": ""},
            {"name": "최종합격", "detail": "인턴 승무원으로 입사"},
        ],
        "requirements": {
            "학력": "기졸업자 또는 졸업예정자",
            "영어": "TOEIC 670점 / TOEIC Speaking IM3 / OPIc IM2 이상 (2년 이내 성적)",
            "시력": "교정시력 1.0 이상",
            "기타": "병역필 또는 면제자, 해외여행 결격사유 없는 자",
        },
        "preferred": ["간호학 전공자 (응급 구조 역할 중요성)"],
        "physical_test": {
            "오래달리기": "지구력 측정",
            "높이뛰기": "순발력 측정",
            "목소리 데시벨": "기내 안내방송 능력",
        },
        "interview_tips": [
            "2025년부터 채용 절차 전면 개편 - 체력시험 도입",
            "상황대처면접: 롤플레잉으로 협업역량, 유연적 사고 평가",
            "체력 검증 전문 기관과 협력해 체육관에서 체력시험 진행",
            "기내 난동 승객 제압, 비상 탈출 지휘 등 안전 업무 수행 능력 검증",
        ],
        "source": "이스타항공 공식 발표 (2025년), 헤럴드경제, 경향신문",
        "source_url": "https://www.eastarjet.com/",
    },
    "에어로케이": {
        "type": "LCC",
        "slogan": "새로운 하늘길",
        "process": [
            {"name": "서류전형", "detail": ""},
            {"name": "1차 토론/실무면접", "detail": "토론 및 실무 면접"},
            {"name": "2차 임원면접", "detail": ""},
            {"name": "신체검사", "detail": ""},
            {"name": "최종합격", "detail": ""},
        ],
        "requirements": {
            "학력": "학력 제한 없음",
            "영어": "TOEIC Speaking IM1 / OPIc IM1 이상 (영어/중국어/일본어)",
            "시력": "교정시력 1.0 이상",
            "기타": "나이 제한 없음, 외모 규정 없음",
        },
        "preferred": ["안전분야 관련 자격 보유자", "영어권/중국/일본 3년 이상 거주자"],
        "interview_tips": [
            "학력, 나이, 외모 제한 없는 열린 채용",
            "1차 면접은 토론과 실무면접 병행",
            "안전분야 관련 자격 보유자 우대",
            "근무지: 충북 청주시 (청주국제공항)",
        ],
        "source": "에어로케이 채용 홈페이지 (2025년), 전북일보",
        "source_url": "https://aerok-recruiter.career.greetinghr.com/",
    },
    "에어프레미아": {
        "type": "HSC",
        "slogan": "New Way to Fly",
        "process": [
            {"name": "서류전형", "detail": ""},
            {"name": "실무면접 / 상황판단검사", "detail": "상황판단검사 약 15분"},
            {"name": "컬처핏면접 / 체력측정", "detail": "악력, 윗몸일으키기, 버피테스트 등"},
            {"name": "채용 건강검진", "detail": ""},
            {"name": "최종합격", "detail": ""},
        ],
        "requirements": {
            "학력": "졸업예정자 포함 (8월 졸업예정자 가능)",
            "영어": "TOEIC 600점 / TOEIC Speaking IM / OPIc IM 이상 (2024.01.18 이후 성적)",
            "시력": "교정시력 1.0 이상",
            "기타": "입사 시점에 근무 가능, 해외여행 결격사유 없는 자",
        },
        "preferred": ["외국어 구사 능력 우수자", "안전/간호 관련 자격 또는 경력 보유자"],
        "physical_test": {
            "악력": "기본 악력 측정",
            "유연성": "앉아 윗몸 앞으로 굽히기",
            "암리치": "팔 길이 측정",
            "윗몸일으키기": "복근 운동 능력",
            "버피테스트": "전신 체력 측정",
        },
        "interview_tips": [
            "2025년부터 체력측정 새롭게 도입 - 기내 비상 상황 대응 능력 검증",
            "상황판단검사: 실제 기내 상황 바탕 대응 역량 평가 (약 15분)",
            "장거리 노선 특화 항공사로 영어 능력 중요",
            "체력측정 항목: 악력, 유연성, 암리치, 윗몸일으키기, 버피테스트",
        ],
        "source": "에어프레미아 공식 발표 (2026년 1월), 한국경제, 헤럴드경제",
        "source_url": "https://airpremia.career.greetinghr.com/",
    },
    "파라타항공": {
        "type": "LCC",
        "slogan": "새로운 하늘, 새로운 가치",
        "process": [
            {"name": "서류전형", "detail": "체력평가 결과서 제출 의무"},
            {"name": "1차면접", "detail": ""},
            {"name": "2차면접", "detail": ""},
            {"name": "건강검진", "detail": ""},
            {"name": "최종합격", "detail": ""},
        ],
        "requirements": {
            "학력": "학력 무관",
            "영어": "TOEIC 650점 / TOEIC Speaking IM / OPIc IM 이상",
            "시력": "교정시력 1.0 이상",
            "기타": "국민체력100 체력인증센터 체력평가 결과서 제출 필수",
        },
        "preferred": ["외국어 능력자 우대"],
        "interview_tips": [
            "'국민체력100 체력인증센터' 체력평가 결과서 제출 의무화",
            "기내 안전요원으로서 직무 수행 가능성 검증 강화",
            "외국어 능력자 우대",
            "신생 항공사로 성장 가능성 강조",
        ],
        "source": "파라타항공 공식 발표 (2025년 12월), 한국경제, 헤럴드경제, 뉴스1",
        "source_url": "https://parataair.recruiter.co.kr/",
    },
}

# ----------------------------
# 페이지 제목
# ----------------------------
st.title("✈️ 항공사별 면접 가이드")
st.caption("국내 11개 항공사 | 사실 기반 정보 | 각 항공사 공식 채용공고 및 뉴스 보도 기준")

st.warning("⚠️ 본 정보는 각 항공사의 공식 채용공고 및 뉴스 보도를 기반으로 작성되었습니다. 정확한 정보는 반드시 각 항공사 공식 채용 페이지에서 확인하세요.")

st.markdown("---")

# ----------------------------
# 항공사 유형별 분류
# ----------------------------
st.markdown("### ✈️ 국내 항공사 현황")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🏛️ FSC (대형항공사)**")
    st.caption("Full Service Carrier")
    fsc_airlines = [a for a in AIRLINE_INTERVIEW_GUIDE.keys() if AIRLINE_INTERVIEW_GUIDE[a]["type"] == "FSC"]
    for a in fsc_airlines:
        st.markdown(f"• {a}")

with col2:
    st.markdown("**✈️ LCC (저비용항공사)**")
    st.caption("Low Cost Carrier")
    lcc_airlines = [a for a in AIRLINE_INTERVIEW_GUIDE.keys() if AIRLINE_INTERVIEW_GUIDE[a]["type"] == "LCC"]
    for a in lcc_airlines:
        st.markdown(f"• {a}")

with col3:
    st.markdown("**🌟 HSC (하이브리드)**")
    st.caption("Hybrid Service Carrier")
    hsc_airlines = [a for a in AIRLINE_INTERVIEW_GUIDE.keys() if AIRLINE_INTERVIEW_GUIDE[a]["type"] == "HSC"]
    for a in hsc_airlines:
        st.markdown(f"• {a}")

st.markdown("---")

# ----------------------------
# 항공사 선택
# ----------------------------
airline_options = list(AIRLINE_INTERVIEW_GUIDE.keys())
selected_airline = st.selectbox(
    "항공사 선택",
    airline_options,
    format_func=lambda x: f"✈️ {x} ({AIRLINE_INTERVIEW_GUIDE[x]['type']}) - {AIRLINE_INTERVIEW_GUIDE[x].get('slogan', '')}"
)

guide = AIRLINE_INTERVIEW_GUIDE.get(selected_airline, {})

if guide:
    # 헤더
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"## ✈️ {selected_airline}")
        st.caption(f"{guide['type']} | {guide.get('slogan', '')}")
    with col2:
        url = AIRLINE_CAREER_URLS.get(selected_airline, "")
        if url:
            st.link_button("🔗 공식 채용 페이지", url, use_container_width=True)

    st.markdown("---")

    # ----------------------------
    # 탭 구성
    # ----------------------------
    tab1, tab2, tab3 = st.tabs(["📊 전형 절차", "📋 지원 자격", "💡 면접 팁"])

    # 탭 1: 전형 절차
    with tab1:
        st.subheader("📊 채용 전형 절차")

        process = guide.get("process", [])
        if process:
            # 프로세스 시각화
            num_steps = len(process)
            if num_steps <= 6:
                cols = st.columns(num_steps)
            else:
                cols = st.columns(6)  # 최대 6개까지만 한 줄에 표시

            for i, step in enumerate(process):
                col_idx = i % 6
                with cols[col_idx]:
                    st.markdown(f"""
                    <div class="process-step">
                        <div class="step-number">{i+1}</div>
                        <div class="step-name">{step['name']}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("")

            # 상세 설명
            st.markdown("### 단계별 상세")
            for i, step in enumerate(process):
                if step.get("detail"):
                    st.info(f"**{i+1}. {step['name']}**: {step['detail']}")
                else:
                    st.caption(f"**{i+1}. {step['name']}**")

        # 체력측정 항목 (해당되는 항공사만)
        if guide.get("physical_test"):
            st.markdown("---")
            st.markdown("### 🏋️ 체력측정 항목")

            physical = guide.get("physical_test", {})
            cols = st.columns(min(len(physical), 5))
            for i, (item, desc) in enumerate(physical.items()):
                with cols[i % 5]:
                    st.metric(item, "")
                    st.caption(desc)

    # 탭 2: 지원 자격
    with tab2:
        st.subheader("📋 지원 자격 요건")

        requirements = guide.get("requirements", {})
        if requirements:
            for key, val in requirements.items():
                st.info(f"**{key}**: {val}")

        # 우대사항
        preferred = guide.get("preferred", [])
        if preferred:
            st.markdown("### ⭐ 우대사항")
            for p in preferred:
                st.success(f"✓ {p}")

    # 탭 3: 면접 팁
    with tab3:
        st.subheader("💡 면접 준비 팁")

        tips = guide.get("interview_tips", [])
        if tips:
            for i, tip in enumerate(tips, 1):
                st.markdown(f"**{i}.** {tip}")

    # ----------------------------
    # 출처 정보
    # ----------------------------
    st.markdown("---")
    st.markdown("### 📚 정보 출처")

    source = guide.get("source", "")
    source_url = guide.get("source_url", "")

    st.markdown(f"""
    <div class="source-box">
        📌 <strong>출처:</strong> {source}<br>
        🔗 <strong>공식 사이트:</strong> <a href="{source_url}" target="_blank">{source_url}</a>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------
# 항공사 비교
# ----------------------------
st.markdown("---")
st.markdown("## 📊 항공사별 요약 비교")

# 유형별 필터
filter_type = st.radio("항공사 유형", ["전체", "FSC", "LCC", "HSC"], horizontal=True)

comparison_data = []
for airline, guide in AIRLINE_INTERVIEW_GUIDE.items():
    if filter_type != "전체" and guide.get("type") != filter_type:
        continue

    reqs = guide.get("requirements", {})
    process_count = len(guide.get("process", []))
    comparison_data.append({
        "항공사": airline,
        "유형": guide.get("type", ""),
        "슬로건": guide.get("slogan", ""),
        "전형 단계": f"{process_count}단계",
        "영어 기준": reqs.get("영어", "-"),
        "학력": reqs.get("학력", "-"),
    })

st.dataframe(comparison_data, use_container_width=True, hide_index=True)

# ----------------------------
# 하단 정보
# ----------------------------
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.caption("⚠️ 본 정보는 참고용이며, 정확한 정보는 각 항공사 공식 채용 페이지에서 확인하세요.")
with col2:
    st.caption("📅 최종 업데이트: 2026-01-16")

# 전체 출처 목록
with st.expander("📚 전체 정보 출처"):
    st.markdown("""
    **FSC (대형항공사)**
    - [대한항공 뉴스룸](https://news.koreanair.com/) - 2026년 공개 채용 관련 보도
    - [대한항공 채용](https://koreanair.recruiter.co.kr/)
    - [아시아나항공 채용](https://flyasiana.recruiter.co.kr/) - 2026년 신입 인턴 객실승무원 채용 공고

    **LCC (저비용항공사)**
    - [진에어 채용](https://jinair.recruiter.co.kr/) - 2026년 상반기 객실승무원 채용 공고
    - [헤럴드경제](https://biz.heraldcorp.com/article/10657008) - 진에어 채용 보도
    - [제주항공 채용](https://jejuair.recruiter.co.kr/) - 2025년 하반기 객실승무원 채용 공고
    - [티웨이항공 채용](https://twayair.recruiter.co.kr/)
    - [부산일보](https://www.busan.com/) - 티웨이항공 채용 보도
    - [에어부산 채용](https://airbusan.recruiter.co.kr/) - 2025년 7월 채용 공고
    - [에어서울 채용](https://flyairseoul.com/) - 2025년 12월 채용 공고
    - [airnews.co.kr](http://m.airnews.co.kr/) - 에어서울 채용 보도
    - [이스타항공](https://www.eastarjet.com/) - 2025년 채용 공고
    - [헤럴드경제](https://biz.heraldcorp.com/article/10443766) - 이스타항공 체력시험 도입 보도
    - [경향신문](https://www.khan.co.kr/article/202503182014005) - 이스타항공 채용 개편 보도
    - [에어로케이 채용](https://aerok-recruiter.career.greetinghr.com/) - 2025년 채용 공고
    - [전북일보](https://www.jbnews.com/) - 에어로케이 채용 보도
    - [파라타항공 채용](https://parataair.recruiter.co.kr/) - 2025년 12월 4기 채용 공고
    - [한국경제](https://www.hankyung.com/article/202512230877g) - 파라타항공 채용 보도
    - [뉴스1](https://www.news1.kr/industry/general-industry/6017836) - 파라타항공 채용 보도

    **HSC (하이브리드)**
    - [에어프레미아 채용](https://airpremia.career.greetinghr.com/) - 2026년 1차 신입 객실승무원 채용 공고
    - [한국경제](https://www.hankyung.com/article/202601088317g) - 에어프레미아 채용 보도
    - [헤럴드경제](https://biz.heraldcorp.com/article/10651145) - 에어프레미아 체력측정 도입 보도
    """)

# div 닫기
st.markdown('</div>', unsafe_allow_html=True)

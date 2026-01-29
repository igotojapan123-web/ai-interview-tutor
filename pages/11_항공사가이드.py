# pages/11_항공사가이드.py
# 항공사별 면접 가이드 - 사실 기반 정보 (국내 11개 항공사)
# 전면 개편: 기업 정체성, 최신 이슈, FSC vs LCC 질문 패턴 추가

import streamlit as st
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sidebar_common import init_page, end_page

init_page(
    title="항공사 가이드",
    current_page="항공사가이드",
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

from config import AIRLINES, AIRLINE_TYPE

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

.identity-card {
    background: white;
    border-radius: 16px;
    padding: 24px;
    margin: 12px 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

.value-badge {
    display: inline-block;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 8px 16px;
    border-radius: 20px;
    margin: 4px;
    font-size: 14px;
}

.issue-card {
    background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
    border-radius: 12px;
    padding: 20px;
    margin: 12px 0;
    border-left: 4px solid #f59e0b;
}

.issue-card.important {
    background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
    border-left-color: #ef4444;
}

.question-card {
    background: white;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 8px 0;
    border-left: 4px solid #3b82f6;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.question-card.fsc {
    border-left-color: #667eea;
    background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
}

.question-card.lcc {
    border-left-color: #f59e0b;
    background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
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

.airline-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 24px;
    border-radius: 16px;
    margin-bottom: 20px;
}

.talent-item {
    background: #f0fdf4;
    padding: 12px 16px;
    border-radius: 8px;
    margin: 6px 0;
    border-left: 3px solid #10b981;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# 채용 페이지 URL
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
# 기업 정체성 데이터 (미션/비전/핵심가치/인재상)
# ----------------------------
AIRLINE_IDENTITY = {
    "대한항공": {
        "mission": "Connecting for a better world.",
        "mission_kr": "더 나은 세상으로 사람과 문화를 연결한다",
        "vision": "To be the world's most loved airline.",
        "vision_kr": "전 세계에서 가장 사랑받는 항공사",
        "core_values": {
            "name": "KE Way",
            "values": [
                {"title": "Beyond Excellence", "desc": "최고 수준 안전과 서비스 실현"},
                {"title": "Journey Together", "desc": "직원·승객·공동체와 함께 성장"},
                {"title": "Better Tomorrow", "desc": "지속 가능한 미래 및 사회 기여"},
            ]
        },
        "talent": ["진취적 성향", "국제적 감각", "서비스 정신", "성실함", "팀워크"],
        "talent_summary": "고객 안전과 서비스 품질을 향상시키는 동시에 조직과 함께 성장할 수 있는 사람",
        "competencies": ["안전 중심 능력", "고객 서비스 품질", "커뮤니케이션·협업", "글로벌 마인드"],
    },
    "아시아나항공": {
        "mission": "최고 수준의 안전과 서비스를 통한 고객 만족 실현",
        "vision": "Better flight, Better tomorrow",
        "vision_kr": "안전하고 쾌적한 비행으로 더 나은 내일을",
        "core_values": {
            "name": "핵심 가치",
            "values": [
                {"title": "안전 최우선", "desc": "최신 설비와 안전 최우선 운영"},
                {"title": "최고 서비스", "desc": "정성 어린 서비스와 고객 중심"},
                {"title": "지속가능경영", "desc": "환경, 윤리, 상생 중심 운영"},
                {"title": "사회적 책임", "desc": "지역사회 및 사회공헌 활동"},
            ]
        },
        "talent": ["고객 감동 서비스", "안전 의식", "글로벌 역량", "팀워크"],
        "talent_summary": "따뜻한 서비스 마인드로 고객 감동을 실현하는 사람",
    },
    "제주항공": {
        "mission": "더 넓은 하늘을 향한 도전으로 더 많은 사람들과 행복한 여행의 경험을 나눈다",
        "vision": "대한민국 No.1 LCC",
        "core_values": {
            "name": "핵심가치 5",
            "values": [
                {"title": "안전", "desc": "타협 없는 안전 최우선"},
                {"title": "저비용", "desc": "효율적 운영으로 합리적 운임"},
                {"title": "신뢰", "desc": "고객과의 약속 준수"},
                {"title": "팀워크", "desc": "함께 협력하는 조직문화"},
                {"title": "도전", "desc": "끊임없는 혁신과 성장"},
            ]
        },
        "talent_framework": {
            "name": "7C 정신",
            "values": [
                {"title": "Confident", "desc": "위기를 이겨낼 자신감"},
                {"title": "Competent", "desc": "개인·조직의 기본 실력"},
                {"title": "Connected", "desc": "강한 유대감/공동체 의식"},
                {"title": "Cooperative", "desc": "존중·배려 기반 협동"},
                {"title": "Consistent", "desc": "일관성 있는 추진력"},
                {"title": "Creative", "desc": "유연성/창의력"},
                {"title": "Customer oriented", "desc": "고객 요구 선제 대응"},
            ]
        },
        "brand_tagline": "NEW STANDARD",
        "brand_statement": "고객이 바라는 제주항공이 되겠습니다",
    },
    "진에어": {
        "mission": "Fly, better fly - 더 나은 항공 여행",
        "vision": "핵심 서비스 강화, 불필요한 요소 제거, 합리적 운임 제공",
        "core_values": {
            "name": "4 Core Values",
            "values": [
                {"title": "SAFETY", "desc": "타협 없는 절대 안전"},
                {"title": "PRACTICALITY", "desc": "언제나 실용적인"},
                {"title": "CUSTOMER SERVICE", "desc": "칭송받는 고객서비스"},
                {"title": "DELIGHT", "desc": "친숙한 기쁨과 행복"},
            ]
        },
        "talent_framework": {
            "name": "5 JINISM",
            "values": [
                {"title": "JINIABLE", "desc": "최고의 안전과 실용성 보장"},
                {"title": "JINIFUL", "desc": "열린 사고로 미래 지향"},
                {"title": "JINIVELY", "desc": "고객에게 사랑받고 재방문"},
                {"title": "JINISH", "desc": "팀워크와 협업 지향"},
                {"title": "JINIQUE", "desc": "긍정적 에너지와 개성"},
            ]
        },
    },
    "티웨이항공": {
        "mission": "첫째도 안전, 둘째도 안전!",
        "vision": "Leading LCC - 여행에 즐거움을 더하는 행복 플러스 항공사",
        "vision_details": [
            "미래를 향해 함께 도전하는 진취적인 기업",
            "'같이'의 가치를 더하는 사람중심 기업",
            "공정한 경쟁과 정직함의 투명한 기업",
        ],
        "core_values": {
            "name": "5S",
            "values": [
                {"title": "Safety", "desc": "승객 안전은 최우선 가치"},
                {"title": "Smart", "desc": "합리적 운임과 실용적 서비스"},
                {"title": "Satisfaction", "desc": "고객 만족 경영"},
                {"title": "Sharing", "desc": "공유가치창출"},
                {"title": "Sustainability", "desc": "지속가능경영"},
            ]
        },
        "talent": [
            "도전의 가치를 아는 사람",
            "창의적 인재라고 말할 수 있는 사람",
            "열린 마음으로 소통하는 사람",
            "국제적 유머감각의 소유자",
        ],
        "certifications": ["IOSA 인증 (2014~)", "SMS 안전관리시스템"],
    },
    "이스타항공": {
        "mission": "항공여행의 대중화를 선도하고 사회공익에 기여하는 글로벌 국민항공사",
        "slogan": "기분 좋은 만남, 국민항공사 이스타항공",
        "slogan_en": "My Star, EASTAR JET",
        "core_values": {
            "name": "핵심 가치",
            "values": [
                {"title": "안전", "desc": "ESMS 통합안전관리시스템 운영"},
                {"title": "대중화", "desc": "가격 접근성 향상"},
                {"title": "사회공익", "desc": "공공성/윤리/준법 경영"},
                {"title": "글로벌", "desc": "국제선 확장/운항 역량"},
            ]
        },
        "compliance": "준법경영팀 신설 (2024.02) - 변호사, 개인정보보호담당자 등 전문 인력",
    },
    "에어부산": {
        "mission": "FLY SMART - 여행의 지혜",
        "vision": "부산/경남 지역 대표 항공사",
        "core_values": {
            "name": "2025 핵심가치",
            "values": [
                {"title": "안전운항", "desc": "안전한 운항 최우선"},
                {"title": "산업안전", "desc": "현장 안전관리 체계 확립"},
                {"title": "정보보안", "desc": "고객 정보 보호 및 보안 강화"},
            ]
        },
        "customer_values": "고객가치: 완벽한 안전, 편리한 서비스, 실용적인 가격",
        "esg_mission": "ESG 경영을 통한 지속 가능한 환경과 사회적 가치 창조",
        "parent": "아시아나항공 자회사",
    },
    "에어서울": {
        "mission": "Always Fresh - 프리미엄 LCC",
        "vision": "세련되고 신선한 항공 서비스",
        "core_values": {
            "name": "핵심 가치",
            "values": [
                {"title": "신선함", "desc": "Fresh한 서비스 경험"},
                {"title": "세련됨", "desc": "도시적이고 트렌디한 이미지"},
                {"title": "글로벌", "desc": "동남아 단거리 노선 특화"},
            ]
        },
        "parent": "아시아나항공 자회사",
    },
    "에어프레미아": {
        "mission": "New Way to Fly - 합리적인 프리미엄",
        "vision": "HSC(Hybrid Service Carrier) - 중장거리 노선 특화",
        "core_values": {
            "name": "핵심 가치",
            "values": [
                {"title": "안전", "desc": "안전 최우선 운항"},
                {"title": "합리", "desc": "가성비 높은 프리미엄"},
                {"title": "프리미엄", "desc": "풀서비스급 서비스 품질"},
                {"title": "혁신", "desc": "새로운 항공 모델 제시"},
            ]
        },
        "positioning": "FSC 수준의 서비스를 LCC 가격으로 제공하는 하이브리드 모델",
    },
    "에어로케이": {
        "mission": "K-Spirit Airline - 하늘 위의 새로운 가치",
        "vision": "청주 기반 신생 항공사로 성장",
        "core_values": {
            "name": "핵심 가치",
            "values": [
                {"title": "안전", "desc": "안전한 운항"},
                {"title": "한국", "desc": "K-Spirit 한국적 서비스"},
                {"title": "청춘", "desc": "젊고 도전적인 조직"},
                {"title": "도전", "desc": "신생 항공사의 성장"},
            ]
        },
        "base": "청주국제공항",
    },
    "파라타항공": {
        "mission": "Paradise in the Sky - 새로운 하늘, 새로운 가치",
        "vision": "양양 기반 휴양지 노선 특화 항공사",
        "core_values": {
            "name": "핵심 가치",
            "values": [
                {"title": "안전", "desc": "안전 최우선"},
                {"title": "휴양", "desc": "휴양지 여행 전문"},
                {"title": "프리미엄", "desc": "프리미엄 서비스 지향"},
                {"title": "새로움", "desc": "신생 항공사의 도전"},
            ]
        },
        "base": "양양국제공항 (서울 강서구 근무)",
    },
}

# ----------------------------
# 최신 이슈 데이터
# ----------------------------
LATEST_ISSUES = {
    "merger": {
        "title": "대한항공-아시아나 합병 (메가캐리어)",
        "importance": "critical",
        "timeline": [
            {"year": "2020.11", "event": "합병 공식 발표"},
            {"year": "2024.12", "event": "법적 인수 완료 (지분 63.88%)"},
            {"year": "2026-2027", "event": "브랜드/운영 통합 예정"},
        ],
        "key_points": [
            "아시아나항공은 대한항공의 자회사가 됨",
            "양대 FSC 체제 → 대한항공 단일 체제로 전환",
            "글로벌 10위권 메가캐리어 출현",
            "마일리지 통합 진행 중 (공정위 조건부 승인)",
        ],
        "impact_on_crew": [
            "서비스 기준 단일화 (대한항공 중심)",
            "단일 KPI 체계 적용 예정",
            "'개인 친절도'보다 '표준 준수 능력' 중시",
            "팀 기반 표준 수행 역량 강조",
        ],
        "interview_point": "\"표준과 팀 기반 환경에서 안정적으로 일한 경험\"을 강조",
    },
    "lcc_integration": {
        "title": "LCC 통합 가능성",
        "importance": "high",
        "content": [
            "대한항공 계열: 진에어",
            "아시아나 계열: 에어부산, 에어서울",
            "→ 통합 LCC 브랜드 운영 검토 중",
        ],
        "timeline": "2027년 통합 LCC 출범 논의",
        "interview_point": "통합 대비 유연성과 적응력 강조",
    },
    "tway_rebranding": {
        "title": "티웨이항공 → Trinity Airways 브랜드 전환",
        "importance": "high",
        "content": [
            "최대주주 변경: 소노인터내셔널",
            "새 브랜드명: Trinity Airways (트리니티 에어웨이즈)",
            "유럽 장거리 노선 확대 (바르셀로나, 로마, 파리 등)",
        ],
        "interview_point": "변화하는 조직에서의 적응력, 장거리 노선 서비스 역량",
    },
    "eastar_revival": {
        "title": "이스타항공 회생 및 재도약",
        "importance": "medium",
        "timeline": [
            {"year": "2022.03", "event": "기업회생절차 종결"},
            {"year": "2023.01", "event": "VIG파트너스 인수 (지분 100%)"},
            {"year": "2023.02", "event": "AOC 재취득"},
            {"year": "2023.03", "event": "국내선 운항 재개"},
        ],
        "key_points": [
            "B737-8 차세대 기종 도입",
            "준법경영팀 신설 (2024.02)",
            "ESMS 통합안전관리시스템 운영",
        ],
        "interview_point": "신뢰 회복, 안전/준법 의식, 함께 성장하겠다는 의지",
    },
    "physical_test": {
        "title": "체력측정 도입 확대",
        "importance": "medium",
        "airlines": ["이스타항공", "에어프레미아", "파라타항공"],
        "content": [
            "이스타: 오래달리기, 높이뛰기, 목소리 데시벨",
            "에어프레미아: 악력, 윗몸일으키기, 버피테스트",
            "파라타: 국민체력100 체력인증센터 결과서 제출 의무",
        ],
        "reason": "기내 비상상황 대응, 난동 승객 제압, 비상 탈출 지휘 능력 검증",
    },
}

# ----------------------------
# FSC vs LCC 면접 질문 패턴
# ----------------------------
FSC_QUESTIONS = {
    "category1": {
        "name": "판단 기준 · 안전 검증",
        "questions": [
            "그 상황에서 여러 선택지가 있었을 텐데, 왜 그 선택을 했나요?",
            "당시 판단할 때 가장 우선했던 기준은 무엇이었나요?",
            "그 선택이 틀렸을 가능성은 고려해봤나요?",
            "그 판단이 조직 전체에 미친 영향은 무엇이라고 생각하나요?",
            "판단 과정에서 가장 조심했던 부분은 무엇이었나요?",
            "그 선택이 위험하다고 느껴졌던 순간은 없었나요?",
            "안전이나 규정과 충돌할 가능성은 없었나요?",
        ]
    },
    "category2": {
        "name": "책임 · 역할 인식",
        "questions": [
            "그 상황에서 본인의 책임 범위는 어디까지였나요?",
            "문제가 생겼을 때 가장 먼저 본인이 한 행동은 무엇이었나요?",
            "결과가 좋지 않았다면 누구의 책임이었을까요?",
            "본인의 판단으로 인해 불편함을 느낀 사람이 있었나요?",
            "책임을 회피하고 싶었던 순간은 없었나요?",
            "본인의 판단이 규정과 다를 때 어떻게 행동했을 것 같나요?",
        ]
    },
    "category3": {
        "name": "재현 가능성 · 일관성",
        "questions": [
            "그 경험은 특별한 상황이었나요, 반복 가능한 상황이었나요?",
            "다른 환경에서도 같은 방식으로 대응할 수 있을까요?",
            "경험이 아니라 기준으로 설명할 수 있나요?",
            "상황이 더 악화됐다면 판단이 달라졌을까요?",
            "이 판단이 승무원 업무에서도 그대로 적용될 수 있을까요?",
        ]
    },
}

LCC_QUESTIONS = {
    "category1": {
        "name": "현장 대응 · 실무 판단",
        "questions": [
            "그 상황에서 빠르게 결정을 내려야 했던 이유는 무엇이었나요?",
            "판단을 미루면 어떤 문제가 생길 수 있었나요?",
            "당시 가장 현실적인 선택지는 무엇이었나요?",
            "감정적인 상대를 마주했을 때도 같은 판단을 할 수 있을까요?",
            "갈등 상황에서 우선적으로 고려한 것은 무엇이었나요?",
            "그 상황을 더 효율적으로 처리할 방법은 없었을까요?",
        ]
    },
    "category2": {
        "name": "돌발 · 압박 · 유연성",
        "questions": [
            "압박 상황에서 가장 흔들리기 쉬운 기준은 무엇이라고 생각하나요?",
            "예상하지 못한 요구가 나왔을 때 어떻게 판단했나요?",
            "상황을 빠르게 끝내기 위해 타협하고 싶었던 순간은 없었나요?",
            "기준을 지키는 것과 상황을 수습하는 것 중 무엇을 우선했나요?",
            "비슷한 돌발 상황이 반복된다면 판단 방식은 달라질까요?",
            "이 경험이 기내 돌발 상황 대응에 어떻게 연결될 수 있을까요?",
        ]
    },
}

# ----------------------------
# 기존 면접 가이드 데이터 (간소화)
# ----------------------------
AIRLINE_INTERVIEW_GUIDE = {
    "대한항공": {
        "type": "FSC",
        "slogan": "Excellence in Flight",
        "process": [
            {"name": "서류전형", "detail": "자기소개서 3개 항목 (600자 이내)"},
            {"name": "1차면접 (온라인)", "detail": "7~8인 1조, 면접관 2명, 20분, Standing"},
            {"name": "2차면접 / 영어구술", "detail": "영어 구술 능력 평가"},
            {"name": "3차면접 / 인성검사", "detail": "인성 평가"},
            {"name": "건강검진 / 수영", "detail": "수영 25m 완영 필수"},
            {"name": "최종합격", "detail": ""},
        ],
        "requirements": {
            "학력": "기졸업자 또는 졸업예정자",
            "영어": "TOEIC 550점 / TOEIC Speaking IM / OPIc IM 이상",
            "시력": "교정시력 1.0 이상",
            "수영": "25m 완영 필수",
        },
        "interview_tips": [
            "1차 면접은 Standing으로 진행",
            "자기소개서는 모든 면접에서 참고됨",
            "통합 항공사 출범 대비 글로벌 역량 강조",
        ],
    },
    "아시아나항공": {
        "type": "FSC",
        "slogan": "아름다운 사람들",
        "process": [
            {"name": "서류전형", "detail": ""},
            {"name": "1차면접", "detail": ""},
            {"name": "2차면접", "detail": ""},
            {"name": "3차면접", "detail": ""},
            {"name": "건강검진 / 수영", "detail": ""},
            {"name": "최종합격", "detail": "인턴 24개월 후 정규직"},
        ],
        "requirements": {
            "학력": "학력 무관",
            "영어": "TOEIC 550점 / TOEIC Speaking IM1 / OPIc IM 이상",
            "시력": "교정시력 1.0 이상",
        },
        "interview_tips": [
            "대한항공 채용 절차와 유사하게 개편",
            "인턴 24개월 후 정규직 전환 심사",
            "통합 항공사 출범 예정",
        ],
    },
    "제주항공": {
        "type": "LCC",
        "slogan": "Fly, Better Fly",
        "process": [
            {"name": "서류전형", "detail": ""},
            {"name": "온라인 역량검사", "detail": ""},
            {"name": "영상면접", "detail": ""},
            {"name": "1차면접", "detail": ""},
            {"name": "2차면접", "detail": ""},
            {"name": "채용검진", "detail": ""},
        ],
        "requirements": {
            "학력": "학력 제한 없음",
            "영어": "TOEIC 600점 / TOEIC Speaking IM1 / OPIc IM1 이상",
            "시력": "교정시력 1.0 이상",
        },
        "interview_tips": [
            "온라인 역량검사와 영상 면접 진행",
            "일본어/중국어 특기자 언어특기전형 가능",
            "학력 제한 없는 열린 채용",
        ],
    },
    "진에어": {
        "type": "LCC",
        "slogan": "Fly, better fly",
        "process": [
            {"name": "서류전형", "detail": ""},
            {"name": "영상전형", "detail": ""},
            {"name": "1차면접", "detail": ""},
            {"name": "2차면접", "detail": ""},
            {"name": "건강검진", "detail": ""},
            {"name": "최종합격", "detail": "약 9주 교육"},
        ],
        "requirements": {
            "학력": "기졸업자 또는 졸업예정자",
            "영어": "TOEIC 550점 / TOEIC Speaking IM1 / OPIc IM 이상",
            "시력": "교정시력 1.0 이상",
        },
        "interview_tips": [
            "서울/부산 지역별 채용",
            "2027년 통합 LCC 출범 대비",
            "약 9주간 교육 후 실무 투입",
        ],
    },
    "티웨이항공": {
        "type": "LCC",
        "slogan": "즐거운 여행의 시작",
        "process": [
            {"name": "서류전형", "detail": ""},
            {"name": "역량검사 / 영상", "detail": ""},
            {"name": "1차면접", "detail": ""},
            {"name": "2차면접", "detail": ""},
            {"name": "채용검진", "detail": ""},
            {"name": "최종합격", "detail": "인턴 1년"},
        ],
        "requirements": {
            "학력": "기졸업자 또는 졸업예정자",
            "영어": "TOEIC 600점 / TOEIC Speaking IM / OPIc IM 이상",
            "시력": "교정시력 1.0 이상",
        },
        "interview_tips": [
            "인턴 1년 후 정규직 전환 심사",
            "Trinity Airways 브랜드 전환 중",
            "유럽 장거리 노선 확대",
        ],
    },
    "에어부산": {
        "type": "LCC",
        "slogan": "부산의 자부심",
        "process": [
            {"name": "서류 / 영상", "detail": ""},
            {"name": "1차면접 (토론)", "detail": "그룹 토론"},
            {"name": "역량검사", "detail": ""},
            {"name": "2차면접", "detail": ""},
            {"name": "건강검진", "detail": ""},
        ],
        "requirements": {
            "학력": "학력 무관",
            "시력": "교정시력 1.0 이상",
        },
        "interview_tips": [
            "1차 면접은 그룹 토론",
            "부산/경남 거주자 우대",
            "아시아나항공 자회사",
        ],
    },
    "에어서울": {
        "type": "LCC",
        "slogan": "프리미엄 LCC",
        "process": [
            {"name": "서류전형", "detail": ""},
            {"name": "1차면접 (토론)", "detail": ""},
            {"name": "역량검사", "detail": ""},
            {"name": "2차면접 / 영어", "detail": ""},
            {"name": "건강검진", "detail": ""},
            {"name": "최종합격", "detail": "인턴 2년"},
        ],
        "requirements": {
            "학력": "기졸업자 또는 졸업예정자",
            "영어": "TOEIC 550점 / TOEIC Speaking IM1 / OPIc IM1 이상",
            "시력": "교정시력 1.0 이상",
        },
        "interview_tips": [
            "아시아나항공 자회사",
            "인턴 2년 후 정규직 전환",
            "아시아 노선 중심",
        ],
    },
    "이스타항공": {
        "type": "LCC",
        "slogan": "새로운 도약",
        "process": [
            {"name": "서류전형", "detail": "합격률 2배 확대"},
            {"name": "상황대처면접", "detail": "롤플레잉, 그룹미션"},
            {"name": "체력TEST", "detail": "오래달리기, 높이뛰기, 데시벨"},
            {"name": "임원면접", "detail": ""},
            {"name": "채용검진", "detail": ""},
        ],
        "requirements": {
            "학력": "기졸업자 또는 졸업예정자",
            "영어": "TOEIC 670점 / TOEIC Speaking IM3 / OPIc IM2 이상",
            "시력": "교정시력 1.0 이상",
        },
        "physical_test": ["오래달리기", "높이뛰기", "목소리 데시벨"],
        "interview_tips": [
            "2025년부터 체력시험 도입",
            "상황대처면접으로 협업/유연성 평가",
            "회생 후 재도약 중",
        ],
    },
    "에어프레미아": {
        "type": "HSC",
        "slogan": "New Way to Fly",
        "process": [
            {"name": "서류전형", "detail": ""},
            {"name": "실무면접 / 상황판단", "detail": "15분"},
            {"name": "컬처핏 / 체력측정", "detail": ""},
            {"name": "건강검진", "detail": ""},
        ],
        "requirements": {
            "학력": "졸업예정자 포함",
            "영어": "TOEIC 600점 / TOEIC Speaking IM / OPIc IM 이상",
            "시력": "교정시력 1.0 이상",
        },
        "physical_test": ["악력", "유연성", "윗몸일으키기", "버피테스트"],
        "interview_tips": [
            "2025년부터 체력측정 도입",
            "상황판단검사 약 15분",
            "중장거리 노선 특화",
        ],
    },
    "에어로케이": {
        "type": "LCC",
        "slogan": "새로운 하늘길",
        "process": [
            {"name": "서류전형", "detail": ""},
            {"name": "1차 토론/실무", "detail": ""},
            {"name": "2차 임원면접", "detail": ""},
            {"name": "신체검사", "detail": ""},
        ],
        "requirements": {
            "학력": "학력 제한 없음",
            "영어": "TOEIC Speaking IM1 / OPIc IM1 이상",
            "시력": "교정시력 1.0 이상",
            "기타": "나이/외모 제한 없음",
        },
        "interview_tips": [
            "학력, 나이, 외모 제한 없는 열린 채용",
            "청주국제공항 근무",
        ],
    },
    "파라타항공": {
        "type": "LCC",
        "slogan": "새로운 하늘, 새로운 가치",
        "process": [
            {"name": "서류전형", "detail": "체력평가 결과서 필수"},
            {"name": "1차면접", "detail": ""},
            {"name": "2차면접", "detail": ""},
            {"name": "건강검진", "detail": ""},
        ],
        "requirements": {
            "학력": "학력 무관",
            "영어": "TOEIC 650점 / TOEIC Speaking IM / OPIc IM 이상",
            "시력": "교정시력 1.0 이상",
            "체력": "국민체력100 결과서 제출 필수",
        },
        "interview_tips": [
            "국민체력100 체력평가 결과서 필수",
            "신생 항공사 성장 가능성",
        ],
    },
}

# ----------------------------
# 페이지 제목
# ----------------------------
st.title("️ 항공사별 면접 가이드")
st.caption("국내 11개 항공사 | 기업 정체성 · 최신 이슈 · 면접 전략")

st.markdown("---")

# ----------------------------
# 메인 탭 구성 (4개)
# ----------------------------
main_tab1, main_tab2, main_tab3, main_tab4, main_tab5 = st.tabs([
 " 기업 정체성",
 " 최신 이슈",
 " FSC vs LCC 질문",
 " 면접 가이드",
 " 나에게 맞는 항공사"
])

# ========================================
# 탭 1: 기업 정체성
# ========================================
with main_tab1:
    st.subheader(" 항공사별 기업 정체성")
    st.info("면접에서 '왜 이 항공사인가요?'에 답하려면 기업의 미션/비전/핵심가치를 알아야 합니다.")

    # 항공사 선택
    identity_airline = st.selectbox(
        "항공사 선택",
        list(AIRLINE_IDENTITY.keys()),
        key="identity_airline"
    )

    identity = AIRLINE_IDENTITY.get(identity_airline, {})
    guide = AIRLINE_INTERVIEW_GUIDE.get(identity_airline, {})

    if identity:
        # 헤더
        st.markdown(f"""
        <div class="airline-header">
            <h2 style="margin: 0;">️ {identity_airline}</h2>
            <p style="margin: 8px 0 0 0; opacity: 0.9;">{guide.get('type', '')} | {guide.get('slogan', '')}</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            # 미션
            st.markdown("### 미션 (Mission)")
            st.markdown(f"""
            <div class="identity-card">
                <p style="font-size: 18px; font-weight: 600; color: #667eea; margin: 0;">"{identity.get('mission', '')}"</p>
                {f'<p style="color: #666; margin: 8px 0 0 0;">{identity.get("mission_kr", "")}</p>' if identity.get('mission_kr') else ''}
            </div>
            """, unsafe_allow_html=True)

            # 비전
            st.markdown("### 비전 (Vision)")
            st.markdown(f"""
            <div class="identity-card">
                <p style="font-size: 16px; font-weight: 600; margin: 0;">{identity.get('vision', '')}</p>
                {f'<p style="color: #666; margin: 8px 0 0 0;">{identity.get("vision_kr", "")}</p>' if identity.get('vision_kr') else ''}
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # 핵심가치
            core_values = identity.get('core_values', {})
            if core_values:
                st.markdown(f"###  핵심가치 ({core_values.get('name', '')})")
                for val in core_values.get('values', []):
                    st.markdown(f"""
                    <div class="talent-item">
                        <strong>{val['title']}</strong>: {val['desc']}
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")

        # 인재상
        talent_framework = identity.get('talent_framework', {})
        talent = identity.get('talent', [])

        if talent_framework:
            st.markdown(f"###  인재상 ({talent_framework.get('name', '')})")
            cols = st.columns(min(len(talent_framework.get('values', [])), 4))
            for i, val in enumerate(talent_framework.get('values', [])):
                with cols[i % 4]:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px; border-radius: 12px; text-align: center; margin: 4px 0;">
                        <strong>{val['title']}</strong><br/>
                        <small style="opacity: 0.9;">{val['desc']}</small>
                    </div>
                    """, unsafe_allow_html=True)

        elif talent:
            st.markdown("### 인재상")
            talent_html = "".join([f'<span class="value-badge">{t}</span>' for t in talent])
            st.markdown(f"<div>{talent_html}</div>", unsafe_allow_html=True)

            if identity.get('talent_summary'):
                st.info(f" **요약:** {identity.get('talent_summary')}")

        # 추가 정보
        if identity.get('competencies'):
            st.markdown("### 객실승무원 핵심역량")
            for comp in identity.get('competencies', []):
                st.markdown(f"• {comp}")

        if identity.get('brand_tagline'):
            st.markdown(f"### ️ 브랜드")
            st.success(f"**Tagline:** {identity.get('brand_tagline')}")
            if identity.get('brand_statement'):
                st.caption(identity.get('brand_statement'))

# ========================================
# 탭 2: 최신 이슈
# ========================================
with main_tab2:
    st.subheader(" 항공 업계 최신 이슈")
    st.warning("️ 면접에서 자주 물어보는 업계 동향입니다. 반드시 숙지하세요!")

    # 합병 이슈
    merger = LATEST_ISSUES["merger"]
    st.markdown(f"""
    <div class="issue-card important">
        <h3 style="margin: 0 0 12px 0;"> {merger['title']}</h3>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("** 타임라인**")
        for item in merger['timeline']:
            st.markdown(f"• **{item['year']}**: {item['event']}")

        st.markdown("")
        st.markdown("** 핵심 포인트**")
        for point in merger['key_points']:
            st.markdown(f"• {point}")

    with col2:
        st.markdown("**‍️ 승무원에게 미치는 영향**")
        for impact in merger['impact_on_crew']:
            st.info(impact)

        st.markdown("")
        st.success(f" **면접 포인트:** {merger['interview_point']}")

    st.markdown("---")

    # LCC 통합
    lcc = LATEST_ISSUES["lcc_integration"]
    st.markdown(f"""
    <div class="issue-card">
        <h3 style="margin: 0 0 12px 0;">️ {lcc['title']}</h3>
    </div>
    """, unsafe_allow_html=True)

    for content in lcc['content']:
        st.markdown(f"• {content}")
    st.caption(f"예상 시점: {lcc['timeline']}")
    st.success(f" **면접 포인트:** {lcc['interview_point']}")

    st.markdown("---")

    # 티웨이 브랜드 전환
    tway = LATEST_ISSUES["tway_rebranding"]
    st.markdown(f"""
    <div class="issue-card">
        <h3 style="margin: 0 0 12px 0;"> {tway['title']}</h3>
    </div>
    """, unsafe_allow_html=True)

    for content in tway['content']:
        st.markdown(f"• {content}")
    st.success(f" **면접 포인트:** {tway['interview_point']}")

    st.markdown("---")

    # 이스타 회생
    eastar = LATEST_ISSUES["eastar_revival"]
    with st.expander(f" {eastar['title']}"):
        st.markdown("** 타임라인**")
        for item in eastar['timeline']:
            st.markdown(f"• **{item['year']}**: {item['event']}")

        st.markdown("")
        st.markdown("** 핵심 포인트**")
        for point in eastar['key_points']:
            st.markdown(f"• {point}")

        st.success(f" **면접 포인트:** {eastar['interview_point']}")

    # 체력측정 도입
    physical = LATEST_ISSUES["physical_test"]
    with st.expander(f"️ {physical['title']}"):
        st.markdown(f"**도입 항공사:** {', '.join(physical['airlines'])}")
        st.markdown("")
        for content in physical['content']:
            st.markdown(f"• {content}")
        st.caption(f"**도입 이유:** {physical['reason']}")

# ========================================
# 탭 3: FSC vs LCC 질문 패턴
# ========================================
with main_tab3:
    st.subheader(" FSC vs LCC 면접 질문 패턴")

    st.markdown("""
    <div class="identity-card">
        <h4 style="margin: 0 0 12px 0;">핵심 차이점</h4>
        <p style="margin: 0;"><strong>FSC 질문:</strong> "이 판단이 <span style="color: #667eea; font-weight: bold;">안전한가</span>"를 묻는다</p>
        <p style="margin: 8px 0 0 0;"><strong>LCC 질문:</strong> "이 판단이 <span style="color: #f59e0b; font-weight: bold;">현장에서 통하는가</span>"를 묻는다</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    question_tab1, question_tab2 = st.tabs(["️ FSC 질문 (대한항공/아시아나)", "️ LCC 질문 (제주/진에어/티웨이 등)"])

    with question_tab1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px; border-radius: 12px; margin-bottom: 16px;">
            <h4 style="margin: 0;">️ FSC 면접 특징</h4>
            <p style="margin: 8px 0 0 0; opacity: 0.9;">보수적, 검증 중심, 꼬리 질문 깊음 | "왜 그렇게 판단했는지"보다 "그 판단이 위험하지 않은지"를 먼저 봄</p>
        </div>
        """, unsafe_allow_html=True)

        for cat_key, cat_data in FSC_QUESTIONS.items():
            st.markdown(f"### {cat_data['name']}")
            for i, q in enumerate(cat_data['questions'], 1):
                st.markdown(f"""
                <div class="question-card fsc">
                    <strong>Q{i}.</strong> {q}
                </div>
                """, unsafe_allow_html=True)
            st.markdown("")

    with question_tab2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 16px; border-radius: 12px; margin-bottom: 16px;">
            <h4 style="margin: 0;">️ LCC 면접 특징</h4>
            <p style="margin: 8px 0 0 0; opacity: 0.9;">빠른 판단, 현실성, 말의 명확성 | 돌발/상황 질문 비중 높음</p>
        </div>
        """, unsafe_allow_html=True)

        for cat_key, cat_data in LCC_QUESTIONS.items():
            st.markdown(f"### {cat_data['name']}")
            for i, q in enumerate(cat_data['questions'], 1):
                st.markdown(f"""
                <div class="question-card lcc">
                    <strong>Q{i}.</strong> {q}
                </div>
                """, unsafe_allow_html=True)
            st.markdown("")

    st.markdown("---")
    st.info("**팁:** 같은 경험이라도 FSC와 LCC에서 강조하는 포인트가 다릅니다. 지원 항공사에 맞게 답변을 조정하세요!")

# ========================================
# 탭 4: 면접 가이드 (기존 기능)
# ========================================
with main_tab4:
    st.subheader(" 항공사별 면접 가이드")

    # 항공사 유형별 분류
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**️ FSC**")
        fsc = [a for a, g in AIRLINE_INTERVIEW_GUIDE.items() if g["type"] == "FSC"]
        st.caption(", ".join(fsc))

    with col2:
        st.markdown("**️ LCC**")
        lcc = [a for a, g in AIRLINE_INTERVIEW_GUIDE.items() if g["type"] == "LCC"]
        st.caption(", ".join(lcc))

    with col3:
        st.markdown("** HSC**")
        hsc = [a for a, g in AIRLINE_INTERVIEW_GUIDE.items() if g["type"] == "HSC"]
        st.caption(", ".join(hsc))

    st.markdown("---")

    # 항공사 선택
    selected_airline = st.selectbox(
        "항공사 선택",
        list(AIRLINE_INTERVIEW_GUIDE.keys()),
        format_func=lambda x: f"️ {x} ({AIRLINE_INTERVIEW_GUIDE[x]['type']})",
        key="guide_airline"
    )

    guide = AIRLINE_INTERVIEW_GUIDE.get(selected_airline, {})

    if guide:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"## ️ {selected_airline}")
            st.caption(f"{guide['type']} | {guide.get('slogan', '')}")
        with col2:
            url = AIRLINE_CAREER_URLS.get(selected_airline, "")
            if url:
                st.link_button(" 채용 페이지", url, use_container_width=True)

        # 서브탭
        sub_tab1, sub_tab2, sub_tab3 = st.tabs([" 전형 절차", " 지원 자격", " 면접 팁"])

        with sub_tab1:
            process = guide.get("process", [])
            if process:
                cols = st.columns(min(len(process), 6))
                for i, step in enumerate(process):
                    with cols[i % 6]:
                        st.markdown(f"""
                        <div class="process-step">
                            <div class="step-number">{i+1}</div>
                            <div class="step-name">{step['name']}</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("")
                for i, step in enumerate(process):
                    if step.get("detail"):
                        st.info(f"**{i+1}. {step['name']}**: {step['detail']}")

            if guide.get("physical_test"):
                st.markdown("### ️ 체력측정 항목")
                for item in guide.get("physical_test", []):
                    st.markdown(f"• {item}")

        with sub_tab2:
            requirements = guide.get("requirements", {})
            for key, val in requirements.items():
                st.info(f"**{key}**: {val}")

        with sub_tab3:
            tips = guide.get("interview_tips", [])
            for i, tip in enumerate(tips, 1):
                st.markdown(f"**{i}.** {tip}")

# ========================================
# 탭 5: 나에게 맞는 항공사
# ========================================
with main_tab5:
    st.subheader(" 나에게 맞는 항공사 찾기")
    st.info("간단한 질문에 답하면 나에게 가장 잘 맞는 항공사를 추천해드립니다!")

    st.markdown("### 나의 성향 체크")

    q1 = st.radio(
        "1. 선호하는 서비스 스타일은?",
        ["격식 있고 품격 있는 서비스", "친근하고 활기찬 서비스", "효율적이고 실용적인 서비스"],
        key="fit_q1"
    )

    q2 = st.radio(
        "2. 선호하는 노선은?",
        ["장거리 국제선 (미주/유럽)", "중단거리 국제선 (일본/동남아)", "국내선 + 단거리 국제선"],
        key="fit_q2"
    )

    q3 = st.radio(
        "3. 나의 외국어 능력은?",
        ["영어 고급 + 제2외국어 가능", "영어 중상급 (TOEIC 700+)", "영어 중급 (TOEIC 550~700)"],
        key="fit_q3"
    )

    q4 = st.radio(
        "4. 나의 성격에 가장 가까운 것은?",
        ["차분하고 세심한 성격", "밝고 에너지 넘치는 성격", "도전적이고 적응력 있는 성격"],
        key="fit_q4"
    )

    q5 = st.radio(
        "5. 근무 조건 중 가장 중요한 것은?",
        ["안정적인 대기업 + 높은 연봉", "자유로운 분위기 + 빠른 성장", "워라밸 + 합리적인 근무환경"],
        key="fit_q5"
    )

    st.markdown("---")

    if st.button("결과 보기", use_container_width=True, type="primary"):
        # 점수 계산
        scores = {
            "대한항공": 0, "아시아나항공": 0, "에어프레미아": 0,
            "진에어": 0, "제주항공": 0, "티웨이항공": 0,
            "에어부산": 0, "이스타항공": 0,
        }

        # Q1: 서비스 스타일
        if "격식" in q1:
            scores["대한항공"] += 3
            scores["아시아나항공"] += 3
        elif "친근" in q1:
            scores["진에어"] += 3
            scores["제주항공"] += 3
            scores["티웨이항공"] += 2
        else:
            scores["에어프레미아"] += 3
            scores["이스타항공"] += 2

        # Q2: 노선
        if "장거리" in q2:
            scores["대한항공"] += 3
            scores["아시아나항공"] += 3
            scores["에어프레미아"] += 2
        elif "중단거리" in q2:
            scores["에어프레미아"] += 3
            scores["진에어"] += 2
            scores["제주항공"] += 2
        else:
            scores["제주항공"] += 2
            scores["티웨이항공"] += 3
            scores["에어부산"] += 3

        # Q3: 외국어
        if "고급" in q3:
            scores["대한항공"] += 3
            scores["아시아나항공"] += 2
            scores["에어프레미아"] += 2
        elif "중상급" in q3:
            scores["에어프레미아"] += 2
            scores["진에어"] += 2
            scores["제주항공"] += 2
        else:
            scores["티웨이항공"] += 2
            scores["에어부산"] += 2
            scores["이스타항공"] += 2

        # Q4: 성격
        if "차분" in q4:
            scores["대한항공"] += 2
            scores["아시아나항공"] += 3
        elif "밝고" in q4:
            scores["진에어"] += 3
            scores["제주항공"] += 2
            scores["티웨이항공"] += 2
        else:
            scores["에어프레미아"] += 3
            scores["이스타항공"] += 2

        # Q5: 근무 조건
        if "안정" in q5:
            scores["대한항공"] += 3
            scores["아시아나항공"] += 3
        elif "자유" in q5:
            scores["에어프레미아"] += 3
            scores["진에어"] += 2
        else:
            scores["제주항공"] += 2
            scores["티웨이항공"] += 2
            scores["에어부산"] += 3

        # 상위 3개 추천
        sorted_airlines = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top3 = sorted_airlines[:3]
        max_score = top3[0][1] if top3 else 1

        st.markdown("### 나에게 맞는 항공사 TOP 3")

        medal_icons = ["", "", ""]
        medal_colors = ["#f59e0b", "#94a3b8", "#cd7f32"]

        for idx, (airline, score) in enumerate(top3):
            pct = int((score / max_score) * 100)
            airline_type = AIRLINE_TYPE.get(airline, "LCC")

            st.markdown(f"""
            <div style="background: white; border-radius: 14px; padding: 18px 22px; margin-bottom: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); border-left: 5px solid {medal_colors[idx]};">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="font-size: 2rem;">{medal_icons[idx]}</div>
                        <div>
                            <div style="font-weight: 700; font-size: 1.1rem;">️ {airline}</div>
                            <div style="font-size: 0.8rem; color: #64748b;">{airline_type}</div>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.3rem; font-weight: 800; color: {medal_colors[idx]};">{pct}%</div>
                        <div style="font-size: 0.75rem; color: #94a3b8;">적합도</div>
                    </div>
                </div>
                <div style="margin-top: 10px; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden;">
                    <div style="height: 100%; width: {pct}%; background: {medal_colors[idx]}; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 추천 이유")

        best_airline = top3[0][0]
        reasons = {
            "대한항공": "격식과 품격을 중시하는 성향에 적합합니다. 장거리 국제선이 많고, 안정적인 대기업 환경을 제공합니다.",
            "아시아나항공": "세심한 서비스와 따뜻한 분위기를 좋아하는 성향에 맞습니다. '아름다운 사람들'의 가치에 공감하실 거예요.",
            "에어프레미아": "도전적이고 효율을 중시하는 성향에 적합합니다. 빠르게 성장하는 HSC에서 다양한 경험을 쌓을 수 있습니다.",
            "진에어": "밝고 활기찬 성격에 딱! 자유롭고 젊은 분위기에서 즐겁게 일할 수 있습니다.",
            "제주항공": "친근하고 에너지 넘치는 성향에 적합합니다. 다양한 노선에서 활발하게 활동할 수 있어요.",
            "티웨이항공": "실용적이고 균형 잡힌 근무환경을 원하시는 분에게 추천합니다.",
            "에어부산": "워라밸을 중시하고 지역 밀착형 서비스에 관심 있는 분에게 적합합니다.",
            "이스타항공": "도전정신과 적응력이 강한 분에게 추천합니다. 재출범한 항공사에서 함께 성장할 수 있어요.",
        }

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #eff6ff, #dbeafe); border-radius: 12px; padding: 20px; border-left: 4px solid #3b82f6;">
            <div style="font-weight: 700; margin-bottom: 8px;">️ {best_airline}을(를) 추천하는 이유</div>
            <div style="font-size: 0.9rem; color: #334155;">{reasons.get(best_airline, "")}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        st.caption(" 이 결과는 참고용입니다. 여러 항공사에 동시 지원하는 것을 추천합니다!")

# ----------------------------
# 하단 정보
# ----------------------------
st.markdown("---")
st.caption("️ 본 정보는 참고용이며, 정확한 정보는 각 항공사 공식 채용 페이지에서 확인하세요.")
st.caption(" 최종 업데이트: 2026-01-23")

# div 닫기
st.markdown('</div>', unsafe_allow_html=True)

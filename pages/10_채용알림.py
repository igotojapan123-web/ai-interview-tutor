# pages/10_채용알림.py
# 항공사 채용 일정 알림 페이지 - 사실 기반 정보

import streamlit as st
from datetime import datetime, timedelta
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sidebar_common import init_page, end_page
from logging_config import get_logger
logger = get_logger(__name__)

init_page(
    title="채용 일정 알림",
    current_page="채용알림",
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
# 비밀번호 보호
# ----------------------------

# ----------------------------
# CSS 스타일링
# ----------------------------
st.markdown("""
<style>
/* 클릭 가능한 통계 카드 */
.stat-card-clickable {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    border: 2px solid #dee2e6;
    cursor: pointer;
    transition: all 0.3s ease;
}

.stat-card-clickable:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.stat-card-clickable.active {
    border-color: #667eea;
    background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
}

.stat-number {
    font-size: 36px;
    font-weight: 800;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.stat-label {
    color: #6c757d;
    font-size: 14px;
    margin-top: 4px;
}

/* 상태 배지 */
.status-badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 600;
    margin: 4px;
}

.status-ongoing {
    background: #10b981;
    color: white;
}

.status-upcoming {
    background: #f59e0b;
    color: white;
}

.status-closed {
    background: #6b7280;
    color: white;
}

/* 예정 카드 */
.hiring-card.upcoming {
    border-left-color: #f59e0b;
    background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
}

/* 알림 배너 */
.alert-banner {
    background: linear-gradient(90deg, #10b981 0%, #059669 100%);
    color: white;
    padding: 16px 24px;
    border-radius: 12px;
    margin: 16px 0;
    display: flex;
    align-items: center;
    animation: slideIn 0.5s ease-out;
}

.alert-banner-urgent {
    background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
}

@keyframes slideIn {
    from { transform: translateX(-20px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

/* 채용 카드 */
.hiring-card {
    background: white;
    border-radius: 16px;
    padding: 20px;
    margin: 12px 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    border-left: 5px solid #667eea;
}

.hiring-card.ongoing {
    border-left-color: #10b981;
    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
}

.hiring-card.closed {
    border-left-color: #6b7280;
    opacity: 0.7;
}

/* 프로세스 스텝 */
.process-step {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    margin: 4px;
    min-height: 80px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.step-number {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 4px;
}

.step-name {
    font-size: 13px;
}

/* 팁 카드 */
.tip-card {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    border-radius: 12px;
    padding: 16px;
    margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# 국내 항공사 채용 페이지 URL (11개 전체)
# ----------------------------
AIRLINE_CAREER_URLS = {
    # FSC (대형항공사)
    "대한항공": "https://koreanair.recruiter.co.kr/",
    "아시아나항공": "https://flyasiana.recruiter.co.kr/",
    # HSC (하이브리드)
    "에어프레미아": "https://airpremia.career.greetinghr.com/",
    # LCC (저비용항공사)
    "진에어": "https://jinair.recruiter.co.kr/",
    "제주항공": "https://jejuair.recruiter.co.kr/",
    "티웨이항공": "https://twayair.recruiter.co.kr/",
    "에어부산": "https://airbusan.recruiter.co.kr/",
    "에어서울": "https://flyairseoul.com/",
    "이스타항공": "https://www.eastarjet.com/",
    "에어로케이": "https://www.aerok.com/",
    "파라타항공": "https://parataair.recruiter.co.kr/",
}

# ----------------------------
# 국내 항공사 기본 정보 (11개 전체)
# ----------------------------
AIRLINE_INFO = {
    "대한항공": {
        "type": "FSC",
        "slogan": "Excellence in Flight",
        "base": "서울 (인천)",
        "process": "서류전형 → 1차면접 → 2차면접 → 체력검정 → 신체검사 → 최종합격",
        "requirements": {
            "education": "전문대 졸업 이상",
            "vision": "교정시력 1.0 이상",
            "english": "TOEIC 550점 이상",
            "swimming": "수영 25m 완영",
        },
        "preferred": ["제2외국어 능통자", "해외 거주 경험"],
    },
    "아시아나항공": {
        "type": "FSC",
        "slogan": "아름다운 사람들",
        "base": "서울 (인천)",
        "process": "서류전형 → 1차면접 → 2차면접 → 3차면접 → 건강검진/수영Test → 최종합격",
        "requirements": {
            "education": "학력 무관",
            "vision": "교정시력 1.0 이상",
            "english": "TOEIC 550점 / TOEIC Speaking IM1 / OPIc IM 이상",
        },
        "preferred": ["중국어/일본어 능통자"],
    },
    "에어프레미아": {
        "type": "HSC",
        "slogan": "New Way to Fly",
        "base": "서울 (인천)",
        "process": "서류전형 → 실무면접/상황판단검사 → 컬처핏면접/체력측정 → 건강검진 → 최종합격",
        "requirements": {
            "education": "학력 무관",
            "vision": "교정시력 1.0 이상",
            "english": "TOEIC 600점 / TOEIC Speaking IM / OPIc IM 이상",
        },
        "preferred": ["외국어 우수자", "안전/간호 관련 자격 보유자"],
    },
    "진에어": {
        "type": "LCC",
        "slogan": "Fun, Young, Dynamic",
        "base": "서울 (인천), 부산",
        "process": "서류전형 → 면접전형 → 신체검사 → 최종합격",
        "requirements": {
            "education": "기졸업자 또는 졸업예정자",
            "vision": "교정시력 1.0 이상",
            "english": "TOEIC 550점 / TOEIC Speaking IM1 / OPIc IM 이상",
        },
        "preferred": ["일본어 우수자", "중국어 우수자"],
    },
    "제주항공": {
        "type": "LCC",
        "slogan": "Fly, Better Fly",
        "base": "서울 (김포/인천), 부산",
        "process": "서류전형 → 역량검사 → 면접전형 → 최종합격",
        "requirements": {
            "education": "학력 제한 없음",
            "vision": "교정시력 1.0 이상",
            "english": "TOEIC 600점 / TOEIC Speaking IM1 / OPIc IM1 이상",
        },
        "preferred": ["밝은 성격", "체력 우수자"],
    },
    "티웨이항공": {
        "type": "LCC",
        "slogan": "즐거운 여행의 시작",
        "base": "서울 (김포/인천), 대구",
        "process": "서류전형 → 1차면접 → 2차면접 → 신체검사 → 최종합격",
        "requirements": {
            "education": "고졸 이상",
            "vision": "교정시력 1.0 이상",
            "english": "TOEIC 550점 이상 또는 이에 준하는 공인 성적",
        },
        "preferred": ["서비스 경험자", "외국어 능통자"],
    },
    "에어부산": {
        "type": "LCC",
        "slogan": "부산의 자부심",
        "base": "부산 (김해)",
        "process": "서류전형 → 그룹토론 → 개별면접 → 신체검사 → 최종합격",
        "requirements": {
            "education": "학력 무관",
            "vision": "교정시력 1.0 이상",
            "english": "TOEIC 550점 이상",
        },
        "preferred": ["부산/경남 거주자"],
    },
    "에어서울": {
        "type": "LCC",
        "slogan": "프리미엄 LCC",
        "base": "서울 (인천)",
        "process": "서류전형 → 1차면접 → 2차면접 → 신체검사 → 최종합격",
        "requirements": {
            "education": "전문대 졸업 이상",
            "vision": "교정시력 1.0 이상",
            "english": "TOEIC 550점 이상",
        },
        "preferred": ["일본어/중국어 가능자"],
    },
    "이스타항공": {
        "type": "LCC",
        "slogan": "새로운 도약",
        "base": "서울 (인천), 청주",
        "process": "서류전형 → 상황대처면접 → 체력TEST → 임원면접 → 채용검진 → 최종합격",
        "requirements": {
            "education": "기졸업자 또는 졸업예정자",
            "vision": "교정시력 1.0 이상",
            "english": "TOEIC 670점 / TOEIC Speaking IM3 / OPIc IM2 이상",
        },
        "preferred": ["열정적인 지원자"],
    },
    "에어로케이": {
        "type": "LCC",
        "slogan": "하늘 위의 새로운 가치",
        "base": "청주",
        "process": "서류전형 → 면접전형 → 신체검사 → 최종합격",
        "requirements": {
            "education": "고졸 이상",
            "vision": "교정시력 1.0 이상",
            "english": "TOEIC 550점 이상",
        },
        "preferred": ["청주/대전 거주자"],
    },
    "파라타항공": {
        "type": "LCC",
        "slogan": "행복한 여행 파트너",
        "base": "양양 (서울 강서구 근무)",
        "process": "서류전형 → AI역량검사 → 1차면접 → 2차면접 → 채용검진 → 최종합격",
        "requirements": {
            "education": "학력 무관 (졸업예정자 가능)",
            "vision": "교정시력 1.0 이상",
            "english": "TOEIC 650점 / TOEIC Speaking IM / OPIc IM 이상",
            "etc": "국민체력100 체력평가 결과서 제출 필수",
        },
        "preferred": ["외국어 능력 우수자"],
    },
}

# ----------------------------
# 채용 데이터 로드 (JSON 파일에서)
# ----------------------------
DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIRING_DATA_FILE = os.path.join(DATA_DIR, "hiring_data.json")


def load_hiring_data():
    """hiring_data.json에서 채용 데이터 로드"""
    if os.path.exists(HIRING_DATA_FILE):
        try:
            with open(HIRING_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                recruitments = data.get("recruitments", [])
                # JSON 데이터를 페이지에서 사용하는 형식으로 변환
                result = []
                for r in recruitments:
                    hire = {
                        "airline": r.get("airline", ""),
                        "position": r.get("position", ""),
                        "start_date": r.get("start_date", ""),
                        "end_date": r.get("end_date", ""),
                        "expected_count": r.get("expected_count", "미공개"),
                        "note": r.get("note", ""),
                        "source": r.get("source", ""),
                    }
                    # period 자동 생성
                    start = r.get("start_date", "").replace("-", ".")
                    end = r.get("end_date", "").replace("-", ".")
                    hire["period"] = f"{start} ~ {end}"

                    # 항공사별 기본 정보 추가
                    airline = r.get("airline", "")
                    if airline in AIRLINE_INFO:
                        info = AIRLINE_INFO[airline]
                        hire["requirements"] = info.get("requirements", {})
                        hire["preferred"] = info.get("preferred", [])
                        hire["process"] = info.get("process", "")

                    result.append(hire)
                return result
        except Exception as e:
            logger.warning(f"Failed to load hiring data: {e}")
    return []


# 채용 데이터 로드
HIRING_DATA = load_hiring_data()

# ----------------------------
# D-Day 계산 함수
# ----------------------------
def calculate_dday(date_str):
    """D-Day 계산"""
    if not date_str:
        return None
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        diff = (target - today).days
        return diff
    except Exception as e:
        logger.debug(f"Failed to parse date: {date_str}, error: {e}")
        return None


def get_hiring_status(hire):
    """채용 상태 자동 계산 (날짜 기반)"""
    today = datetime.now().date()

    start_date_str = hire.get("start_date", "")
    end_date_str = hire.get("end_date", "")

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
    except Exception as e:
        logger.debug(f"Failed to parse hiring status date: {e}")
        return "마감"  # 날짜 파싱 실패시 마감 처리

    if not end_date:
        return "마감"

    if start_date and today < start_date:
        return "예정"
    elif today <= end_date:
        return "진행중"
    else:
        return "마감"


def get_hiring_with_auto_status():
    """모든 채용 정보에 자동 상태 적용"""
    result = []
    for hire in HIRING_DATA:
        hire_copy = hire.copy()
        hire_copy["status"] = get_hiring_status(hire)  # 자동 계산된 상태로 덮어쓰기
        result.append(hire_copy)
    return result

# ----------------------------
# 세션 상태 초기화
# ----------------------------
if "selected_filter" not in st.session_state:
    st.session_state.selected_filter = "전체"

# ----------------------------
# 페이지 제목
# ----------------------------
st.title("항공사 채용 일정 알림")
st.caption("2026년 항공사 객실승무원 채용 정보 | 사실 기반 정보")

# ----------------------------
# 상단 요약 통계 (클릭 가능)
# ----------------------------
# 자동 계산된 상태 사용
ALL_HIRING = get_hiring_with_auto_status()

ongoing_list = [h for h in ALL_HIRING if h["status"] == "진행중"]
upcoming_list = [h for h in ALL_HIRING if h["status"] == "예정"]
closed_list = [h for h in ALL_HIRING if h["status"] == "마감"]

ongoing_count = len(ongoing_list)
upcoming_count = len(upcoming_list)
closed_count = len(closed_list)
total_count = len(ALL_HIRING)

st.markdown("### 채용 현황 (클릭하여 필터링)")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button(f" 진행중\n**{ongoing_count}건**",
                 use_container_width=True,
                 type="primary" if st.session_state.selected_filter == "진행중" else "secondary"):
        st.session_state.selected_filter = "진행중"
        st.rerun()

with col2:
    if st.button(f" 예정\n**{upcoming_count}건**",
                 use_container_width=True,
                 type="primary" if st.session_state.selected_filter == "예정" else "secondary"):
        st.session_state.selected_filter = "예정"
        st.rerun()

with col3:
    if st.button(f" 마감\n**{closed_count}건**",
                 use_container_width=True,
                 type="primary" if st.session_state.selected_filter == "마감" else "secondary"):
        st.session_state.selected_filter = "마감"
        st.rerun()

with col4:
    if st.button(f" 전체\n**{total_count}건**",
                 use_container_width=True,
                 type="primary" if st.session_state.selected_filter == "전체" else "secondary"):
        st.session_state.selected_filter = "전체"
        st.rerun()

st.caption(f" 현재 필터: **{st.session_state.selected_filter}** | 상태는 마감일 기준 자동 계산됩니다")

# ----------------------------
# 긴급 알림 배너 (진행중인 채용)
# ----------------------------
if ongoing_list:
    st.markdown("---")
    st.markdown("### 현재 진행중인 채용")

    for hire in ongoing_list:
        dday = calculate_dday(hire.get("end_date"))

        if dday is not None and dday <= 3:
            banner_class = "alert-banner-urgent"
            urgent_text = "️ 마감 임박!"
        else:
            banner_class = ""
            urgent_text = ""

        dday_text = f"D-{dday}" if dday and dday > 0 else "오늘 마감!" if dday == 0 else ""

        st.markdown(f"""
        <div class="alert-banner {banner_class}">
            <span style="font-size: 24px; margin-right: 12px;">️</span>
            <div style="flex: 1;">
                <strong>{hire['airline']}</strong> {hire['position']}
                <br><span style="font-size: 14px; opacity: 0.9;">{hire['period']} | {hire['expected_count']} 모집</span>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 24px; font-weight: bold;">{dday_text}</span>
                <br><span style="font-size: 12px;">{urgent_text}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 바로 지원 버튼
        url = AIRLINE_CAREER_URLS.get(hire['airline'], "")
        if url:
            st.link_button(f" {hire['airline']} 채용 페이지 바로가기", url, use_container_width=True)

        st.markdown("")

st.markdown("---")

# ----------------------------
# 구독자 데이터 관리
# ----------------------------
SUBSCRIBERS_FILE = os.path.join(DATA_DIR, "data", "subscribers.json")

def load_subscribers():
    """구독자 데이터 로드"""
    if os.path.exists(SUBSCRIBERS_FILE):
        try:
            with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load subscribers: {e}")
    return {"subscribers": [], "total_count": 0}

def save_subscribers(data):
    """구독자 데이터 저장"""
    os.makedirs(os.path.dirname(SUBSCRIBERS_FILE), exist_ok=True)
    with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_subscriber(name, email, phone="", airlines=None):
    """새 구독자 추가"""
    data = load_subscribers()

    # 이메일 중복 체크
    for sub in data["subscribers"]:
        if sub["email"] == email:
            return False, "이미 등록된 이메일입니다."

    new_sub = {
        "id": f"sub_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(data['subscribers'])}",
        "name": name,
        "email": email,
        "phone": phone,
        "airlines": airlines or [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "active": True
    }
    data["subscribers"].append(new_sub)
    data["total_count"] = len([s for s in data["subscribers"] if s.get("active", True)])
    save_subscribers(data)
    return True, "구독 신청이 완료되었습니다!"

def unsubscribe(email):
    """구독 해지"""
    data = load_subscribers()
    for sub in data["subscribers"]:
        if sub["email"] == email:
            sub["active"] = False
            data["total_count"] = len([s for s in data["subscribers"] if s.get("active", True)])
            save_subscribers(data)
            return True, "구독이 해지되었습니다."
    return False, "등록된 이메일을 찾을 수 없습니다."

def get_subscriber_count():
    """활성 구독자 수"""
    data = load_subscribers()
    return len([s for s in data["subscribers"] if s.get("active", True)])

# ----------------------------
# 내 지원 현황 데이터
# ----------------------------
APPLICATION_FILE = os.path.join(DATA_DIR, "data", "my_applications.json")

def load_applications():
    if os.path.exists(APPLICATION_FILE):
        try:
            with open(APPLICATION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load applications: {e}")
    return {"applications": []}

def save_applications(data):
    os.makedirs(os.path.dirname(APPLICATION_FILE), exist_ok=True)
    with open(APPLICATION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 채용 시즌 패턴 데이터 (과거 실적 기반)
HIRING_PATTERNS = {
    "대한항공": {
        "frequency": "연 1~2회",
        "typical_months": [3, 4, 9, 10],
        "pattern": "상반기(3~4월) + 하반기(9~10월) 정기 채용",
        "last_hiring": "2025년 10월",
        "next_expected": "2026년 3~4월 (예상)",
        "avg_applicants": "5,000~8,000명",
        "avg_selected": "100~200명",
        "tips": "영어면접 + 수영 25m 필수, 제2외국어 우대"
    },
    "아시아나항공": {
        "frequency": "연 1~2회",
        "typical_months": [5, 6, 10, 11],
        "pattern": "상반기(5~6월) + 하반기(10~11월) 채용",
        "last_hiring": "2025년 11월",
        "next_expected": "2026년 5~6월 (예상)",
        "avg_applicants": "4,000~6,000명",
        "avg_selected": "80~150명",
        "tips": "수영Test 포함, 중국어/일본어 우대"
    },
    "에어프레미아": {
        "frequency": "연 2~3회",
        "typical_months": [1, 2, 5, 6, 9, 10],
        "pattern": "분기별 수시 채용 (확장 중)",
        "last_hiring": "2026년 1월",
        "next_expected": "2026년 상시 채용 가능",
        "avg_applicants": "2,000~3,000명",
        "avg_selected": "50~80명",
        "tips": "영어+토론면접 특징, 체력측정 포함"
    },
    "진에어": {
        "frequency": "연 2~3회",
        "typical_months": [1, 2, 4, 5, 8, 9],
        "pattern": "분기별 수시 채용",
        "last_hiring": "2026년 1월",
        "next_expected": "2026년 4~5월 (예상)",
        "avg_applicants": "2,000~4,000명",
        "avg_selected": "60~100명",
        "tips": "일본어/중국어 우수자 우대, 밝은 이미지 중시"
    },
    "제주항공": {
        "frequency": "연 2~4회",
        "typical_months": [2, 3, 5, 6, 8, 9, 11],
        "pattern": "수시 채용 (가장 활발)",
        "last_hiring": "2025년 11월",
        "next_expected": "2026년 2~3월 (예상)",
        "avg_applicants": "3,000~5,000명",
        "avg_selected": "80~120명",
        "tips": "역량검사 포함, 밝은 에너지 중시"
    },
    "티웨이항공": {
        "frequency": "연 2~3회",
        "typical_months": [3, 4, 7, 8, 10, 11],
        "pattern": "상/하반기 정기 + 수시",
        "last_hiring": "2025년 10월",
        "next_expected": "2026년 3~4월 (예상)",
        "avg_applicants": "2,000~3,000명",
        "avg_selected": "50~80명",
        "tips": "서비스 경험자 우대, 대구 거주자 유리"
    },
    "에어부산": {
        "frequency": "연 1~2회",
        "typical_months": [4, 5, 9, 10],
        "pattern": "상/하반기 정기 채용",
        "last_hiring": "2025년 9월",
        "next_expected": "2026년 4~5월 (예상)",
        "avg_applicants": "1,500~2,500명",
        "avg_selected": "40~60명",
        "tips": "부산/경남 거주자 우대, 그룹토론 포함"
    },
    "에어서울": {
        "frequency": "연 1~2회",
        "typical_months": [3, 4, 8, 9],
        "pattern": "비정기 수시 채용",
        "last_hiring": "2025년 8월",
        "next_expected": "2026년 3~4월 (예상)",
        "avg_applicants": "1,000~2,000명",
        "avg_selected": "30~50명",
        "tips": "일본어/중국어 가능자 우대"
    },
    "이스타항공": {
        "frequency": "연 2~3회",
        "typical_months": [2, 3, 6, 7, 10, 11],
        "pattern": "수시 채용 (재출범 후 확대)",
        "last_hiring": "2025년 11월",
        "next_expected": "2026년 2~3월 (예상)",
        "avg_applicants": "1,500~2,500명",
        "avg_selected": "40~70명",
        "tips": "체력TEST 포함, 청주 근무 가능자"
    },
    "에어로케이": {
        "frequency": "연 1~2회",
        "typical_months": [3, 4, 9, 10],
        "pattern": "비정기 수시 채용",
        "last_hiring": "2025년 4월",
        "next_expected": "2026년 상반기 (예상)",
        "avg_applicants": "800~1,500명",
        "avg_selected": "20~40명",
        "tips": "외국어 능력 우수자 우대"
    },
    "파라타항공": {
        "frequency": "연 2~3회",
        "typical_months": [1, 2, 5, 6, 9, 10],
        "pattern": "수시 채용 (신생 항공사)",
        "last_hiring": "2026년 1월",
        "next_expected": "2026년 상시 채용 가능",
        "avg_applicants": "1,000~2,000명",
        "avg_selected": "30~50명",
        "tips": "국민체력100 제출 필수, 성장 가능성"
    },
}

APPLICATION_STAGES = ["서류 지원", "서류 합격", "1차 면접", "2차 면접", "3차 면접", "체력/수영", "건강검진", "최종 합격", "불합격"]

# ----------------------------
# 탭 구성 (6개 탭)
# ----------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
 " 채용 일정",
 " 채용 프로세스",
 " 채용 패턴",
 "️ 내 지원현황",
 " 알림 구독",
 " 채용 페이지"
])

# ----------------------------
# 탭 1: 채용 일정
# ----------------------------
with tab1:
    st.subheader(" 2026년 채용 일정")

    # 필터 적용 (자동 계산된 상태 기반)
    if st.session_state.selected_filter == "전체":
        filtered_schedule = ALL_HIRING
    else:
        filtered_schedule = [h for h in ALL_HIRING if h["status"] == st.session_state.selected_filter]

    if not filtered_schedule:
        st.info(f"'{st.session_state.selected_filter}' 상태의 채용 공고가 없습니다.")

    # 진행중 → 예정 → 마감 순서로 정렬
    status_order = {"진행중": 0, "예정": 1, "마감": 2}
    filtered_schedule = sorted(filtered_schedule, key=lambda x: (status_order.get(x["status"], 2), x.get("end_date") or "9999-99-99"))

    for hire in filtered_schedule:
        airline = hire["airline"]
        airline_t = AIRLINE_TYPE.get(airline, "LCC")

        # D-Day 계산
        dday = calculate_dday(hire.get("end_date"))

        # 상태별 스타일
        if hire["status"] == "진행중":
            status_emoji = ""
            card_style = "ongoing"
        elif hire["status"] == "예정":
            status_emoji = ""
            card_style = "upcoming"
        else:
            status_emoji = ""
            card_style = "closed"

        with st.container():
            # 헤더
            header_col1, header_col2 = st.columns([3, 1])
            with header_col1:
                st.markdown(f"### {status_emoji} {airline}")
                st.caption(f"{airline_t} | {hire['position']}")
            with header_col2:
                status_class = 'ongoing' if hire['status'] == '진행중' else ('upcoming' if hire['status'] == '예정' else 'closed')
                st.markdown(f"""
                <span class="status-badge status-{status_class}">{hire['status']}</span>
                """, unsafe_allow_html=True)

            # 상세 정보
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f" **{hire['period']}**")
                st.markdown(f" **모집인원:** {hire['expected_count']}")
                st.info(f" {hire['note']}")
                st.caption(f" 출처: {hire.get('source', '공식 채용사이트')}")

            with col2:
                # D-Day 표시
                if hire["status"] == "진행중":
                    if dday is not None:
                        if dday > 0:
                            st.metric("마감까지", f"D-{dday}")
                        elif dday == 0:
                            st.error("오늘 마감!")
                        else:
                            st.warning("마감됨")

                    # 지원 버튼
                    url = AIRLINE_CAREER_URLS.get(airline, "")
                    if url:
                        st.link_button(" 지원하기", url, use_container_width=True)
                elif hire["status"] == "예정":
                    start_dday = calculate_dday(hire.get("start_date"))
                    if start_dday is not None and start_dday > 0:
                        st.metric("시작까지", f"D-{start_dday}")
                    st.info("곧 시작됩니다!")
                    url = AIRLINE_CAREER_URLS.get(airline, "")
                    if url:
                        st.link_button(" 채용 페이지 확인", url, use_container_width=True)
                else:
                    st.caption("다음 채용 공고를 기다려주세요")
                    url = AIRLINE_CAREER_URLS.get(airline, "")
                    if url:
                        st.link_button(" 채용 페이지 확인", url, use_container_width=True)

            # 자격요건 (확장)
            with st.expander("자격요건 & 전형절차"):
                req_col1, req_col2 = st.columns(2)

                with req_col1:
                    st.markdown("**필수 자격**")
                    reqs = hire.get("requirements", {})
                    for key, val in reqs.items():
                        label = {
                            "education": " 학력",
                            "vision": "️ 시력",
                            "english": " 영어",
                            "swimming": " 수영",
                            "etc": " 기타"
                        }.get(key, key)
                        st.caption(f"{label}: {val}")

                with req_col2:
                    st.markdown("**우대사항**")
                    preferred = hire.get("preferred", [])
                    for p in preferred:
                        st.caption(f" {p}")

                    st.markdown("")
                    st.markdown("**전형절차**")
                    st.caption(hire.get("process", "미공개"))

            st.markdown("---")

# ----------------------------
# 탭 2: 채용 프로세스 (11개 전체 항공사)
# ----------------------------
with tab2:
    st.subheader(" 항공사별 채용 프로세스")
    st.caption("국내 11개 항공사 전체 정보")

    # 현재 진행중인 항공사 표시
    ongoing_airlines = [h["airline"] for h in ALL_HIRING if h["status"] == "진행중"]

    # 항공사 순서: FSC → HSC → LCC
    airline_order = ["대한항공", "아시아나항공", "에어프레미아", "진에어", "제주항공",
                     "티웨이항공", "에어부산", "에어서울", "이스타항공", "에어로케이", "파라타항공"]

    selected_airline = st.selectbox(
        "항공사 선택",
        airline_order,
        format_func=lambda x: f" {x} (채용 진행중)" if x in ongoing_airlines else x
    )

    # 선택한 항공사 정보 (AIRLINE_INFO에서 가져오기)
    airline_info = AIRLINE_INFO.get(selected_airline, {})

    if airline_info:
        airline_type = airline_info.get("type", "LCC")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### ️ {selected_airline}")
            st.caption(f"{airline_type} | {airline_info.get('slogan', '')} | 거점: {airline_info.get('base', '')}")
        with col2:
            url = AIRLINE_CAREER_URLS.get(selected_airline, "")
            if url:
                st.link_button("채용 페이지 →", url)

        # 진행중인 채용 알림
        if selected_airline in ongoing_airlines:
            st.success(f" **{selected_airline}** 현재 채용 진행중!")

        st.markdown("---")

        # 전형 절차 시각화
        st.markdown("### 전형 단계")

        process_str = airline_info.get("process", "")
        if process_str:
            steps = [s.strip() for s in process_str.replace("→", "|").split("|")]

            cols = st.columns(len(steps))
            for i, step in enumerate(steps):
                with cols[i]:
                    st.markdown(f"""
                    <div class="process-step">
                        <div class="step-number">{i+1}</div>
                        <div class="step-name">{step}</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")

        # 자격요건
        st.markdown("### 자격요건")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**필수 자격**")
            reqs = airline_info.get("requirements", {})
            for key, val in reqs.items():
                label = {
                    "education": " 학력",
                    "vision": "️ 시력",
                    "english": " 영어",
                    "swimming": " 수영",
                    "etc": " 기타"
                }.get(key, key)
                st.info(f"{label}: {val}")

        with col2:
            st.markdown("**우대사항**")
            preferred = airline_info.get("preferred", [])
            for p in preferred:
                st.success(f" {p}")

# ----------------------------
# 탭 3: 채용 패턴 분석
# ----------------------------
with tab3:
    st.subheader(" 항공사별 채용 패턴 분석")
    st.caption("과거 채용 실적 기반 예상 시기 | 참고용 정보")

    st.markdown("""
    <div style="background: linear-gradient(135deg, #fef3c7, #fde68a); border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; border-left: 4px solid #f59e0b;">
        <strong> 참고사항:</strong> 채용 시기는 과거 패턴 기반 예상이며, 실제 일정은 항공사 공식 발표를 확인하세요.
    </div>
    """, unsafe_allow_html=True)

    # 월별 채용 히트맵
    st.markdown("### 월별 채용 시즌 히트맵")
    st.markdown("각 항공사의 과거 채용 시기를 시각화합니다.")

    months = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"]
    current_month = datetime.now().month

    for airline_name, pattern in HIRING_PATTERNS.items():
        airline_type = AIRLINE_INFO.get(airline_name, {}).get("type", "LCC")
        typical = pattern["typical_months"]

        # 월별 활성화 표시
        month_cells = ""
        for m in range(1, 13):
            if m in typical:
                if m == current_month:
                    cell_style = "background: #10b981; color: white; font-weight: 700;"
                else:
                    cell_style = "background: #667eea; color: white;"
            else:
                if m == current_month:
                    cell_style = "background: #e2e8f0; font-weight: 700; border: 2px solid #667eea;"
                else:
                    cell_style = "background: #f1f5f9; color: #94a3b8;"
            month_cells += f'<div style="{cell_style} border-radius: 6px; padding: 4px 2px; text-align: center; font-size: 0.7rem;">{m}</div>'

        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 15px; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                <div style="font-weight: 700; font-size: 0.9rem; min-width: 90px;">{airline_name}</div>
                <div style="font-size: 0.7rem; color: #64748b; background: #f1f5f9; padding: 2px 8px; border-radius: 10px;">{airline_type}</div>
                <div style="font-size: 0.75rem; color: #64748b;">{pattern["frequency"]}</div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(12, 1fr); gap: 3px;">
                {month_cells}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display: flex; gap: 15px; margin: 15px 0; font-size: 0.8rem;">
        <div style="display: flex; align-items: center; gap: 5px;"><div style="width: 14px; height: 14px; background: #667eea; border-radius: 4px;"></div> 채용 예상 시기</div>
        <div style="display: flex; align-items: center; gap: 5px;"><div style="width: 14px; height: 14px; background: #10b981; border-radius: 4px;"></div> 현재 월 + 채용 시기</div>
        <div style="display: flex; align-items: center; gap: 5px;"><div style="width: 14px; height: 14px; background: #e2e8f0; border: 2px solid #667eea; border-radius: 4px;"></div> 현재 월</div>
    </div>
    """, unsafe_allow_html=True)

    # 상세 정보
    st.markdown("---")
    st.markdown("### 항공사별 상세 채용 정보")

    pattern_airline = st.selectbox("항공사 선택", list(HIRING_PATTERNS.keys()), key="pattern_airline")
    p_data = HIRING_PATTERNS[pattern_airline]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("채용 빈도", p_data["frequency"])
        st.caption(f"패턴: {p_data['pattern']}")
    with col2:
        st.metric("예상 지원자", p_data["avg_applicants"])
        st.caption(f"예상 선발: {p_data['avg_selected']}")
    with col3:
        st.metric("다음 채용 예상", p_data["next_expected"].split(" (")[0])
        st.caption(f"최근 채용: {p_data['last_hiring']}")

    st.info(f" **핵심 팁:** {p_data['tips']}")

    # 경쟁률 추정
    st.markdown("---")
    st.markdown("### 지원 전략 팁")

    st.markdown("""
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
        <div style="background: #f0fdf4; border-radius: 12px; padding: 15px; text-align: center;">
            <div style="font-size: 1.5rem;"></div>
            <div style="font-weight: 700; font-size: 0.85rem; margin: 5px 0;">동시 지원</div>
            <div style="font-size: 0.75rem; color: #64748b;">2~3개 항공사에<br>동시 지원 추천</div>
        </div>
        <div style="background: #eff6ff; border-radius: 12px; padding: 15px; text-align: center;">
            <div style="font-size: 1.5rem;"></div>
            <div style="font-weight: 700; font-size: 0.85rem; margin: 5px 0;">시즌 준비</div>
            <div style="font-size: 0.75rem; color: #64748b;">채용 시작 2개월 전부터<br>본격 준비 시작</div>
        </div>
        <div style="background: #fef2f2; border-radius: 12px; padding: 15px; text-align: center;">
            <div style="font-size: 1.5rem;"></div>
            <div style="font-weight: 700; font-size: 0.85rem; margin: 5px 0;">재지원</div>
            <div style="font-size: 0.75rem; color: #64748b;">불합격 후 다음 공채에<br>재지원 가능 (대부분)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------
# 탭 4: 내 지원 현황
# ----------------------------
with tab4:
    st.subheader("️ 내 지원 현황 관리")
    st.caption("지원한 항공사와 진행 상태를 관리하세요")

    app_data = load_applications()

    # 지원 추가
    with st.expander("새 지원 기록 추가", expanded=False):
        with st.form("add_application"):
            app_col1, app_col2 = st.columns(2)
            with app_col1:
                app_airline = st.selectbox("항공사", list(AIRLINE_INFO.keys()), key="app_airline")
                app_date = st.date_input("지원 날짜", key="app_date")
            with app_col2:
                app_stage = st.selectbox("현재 단계", APPLICATION_STAGES, key="app_stage")
                app_note = st.text_input("메모 (선택)", placeholder="예: 자소서 제출 완료", key="app_note")

            if st.form_submit_button(" 지원 기록 추가", use_container_width=True):
                new_app = {
                    "id": f"app_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "airline": app_airline,
                    "date": app_date.strftime("%Y-%m-%d"),
                    "stage": app_stage,
                    "note": app_note,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "history": [{"stage": app_stage, "date": datetime.now().strftime("%Y-%m-%d")}]
                }
                app_data["applications"].append(new_app)
                save_applications(app_data)
                st.success(f" {app_airline} 지원 기록이 추가되었습니다!")
                st.rerun()

    # 현재 지원 현황
    st.markdown("---")
    active_apps = [a for a in app_data["applications"] if a.get("stage") != "불합격"]
    finished_apps = [a for a in app_data["applications"] if a.get("stage") == "불합격" or a.get("stage") == "최종 합격"]

    if active_apps:
        st.markdown("### 진행 중인 지원")

        for app in active_apps:
            airline = app.get("airline", "")
            stage = app.get("stage", "")
            date = app.get("date", "")
            note = app.get("note", "")

            # 단계별 색상
            if stage == "최종 합격":
                stage_color = "#10b981"
                stage_bg = "#f0fdf4"
            elif "면접" in stage or "합격" in stage:
                stage_color = "#3b82f6"
                stage_bg = "#eff6ff"
            else:
                stage_color = "#f59e0b"
                stage_bg = "#fffbeb"

            # 진행률 계산
            stage_idx = APPLICATION_STAGES.index(stage) if stage in APPLICATION_STAGES else 0
            progress = int((stage_idx / (len(APPLICATION_STAGES) - 2)) * 100)  # 불합격 제외
            progress = min(progress, 100)

            st.markdown(f"""
            <div style="background: {stage_bg}; border-left: 4px solid {stage_color}; border-radius: 12px; padding: 15px 20px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: 700; font-size: 1rem;">️ {airline}</div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-top: 3px;">지원일: {date} {("| " + note) if note else ""}</div>
                    </div>
                    <div style="background: {stage_color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">{stage}</div>
                </div>
                <div style="margin-top: 10px; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden;">
                    <div style="height: 100%; width: {progress}%; background: {stage_color}; border-radius: 3px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 단계 업데이트 버튼
            col_update, col_delete = st.columns([3, 1])
            with col_update:
                new_stage = st.selectbox(
                    "단계 변경",
                    APPLICATION_STAGES,
                    index=stage_idx,
                    key=f"stage_{app['id']}"
                )
                if new_stage != stage:
                    if st.button("변경 적용", key=f"update_{app['id']}"):
                        app["stage"] = new_stage
                        app.setdefault("history", []).append({
                            "stage": new_stage,
                            "date": datetime.now().strftime("%Y-%m-%d")
                        })
                        save_applications(app_data)
                        st.rerun()
            with col_delete:
                if st.button("️ 삭제", key=f"del_{app['id']}"):
                    app_data["applications"] = [a for a in app_data["applications"] if a["id"] != app["id"]]
                    save_applications(app_data)
                    st.rerun()

            st.markdown("")
    else:
        st.info("아직 지원 기록이 없습니다. 위의 '새 지원 기록 추가'에서 추가해보세요!")

    # 완료/불합격 기록
    if finished_apps:
        with st.expander(f" 완료된 지원 ({len(finished_apps)}건)"):
            for app in finished_apps:
                result_icon = "" if app.get("stage") == "최종 합격" else ""
                st.markdown(f"{result_icon} **{app.get('airline', '')}** - {app.get('stage', '')} ({app.get('date', '')})")

    # 요약 통계
    if app_data["applications"]:
        st.markdown("---")
        st.markdown("### 지원 요약")
        total_apps = len(app_data["applications"])
        passed = len([a for a in app_data["applications"] if a.get("stage") == "최종 합격"])
        in_progress = len(active_apps)

        stat_col1, stat_col2, stat_col3 = st.columns(3)
        with stat_col1:
            st.metric("총 지원", f"{total_apps}곳")
        with stat_col2:
            st.metric("진행 중", f"{in_progress}곳")
        with stat_col3:
            st.metric("최종 합격", f"{passed}곳")

# ----------------------------
# 탭 6: 채용 페이지 바로가기 (11개 전체)
# ----------------------------
with tab6:
    st.subheader(" 항공사 채용 페이지 바로가기")
    st.caption("국내 11개 항공사 공식 채용 페이지")

    st.info("모든 링크는 실제 항공사 공식 채용 페이지로 연결됩니다.")

    # 현재 진행중인 항공사 확인
    ongoing_airlines = [h["airline"] for h in ALL_HIRING if h["status"] == "진행중"]

    # FSC (대형항공사)
    st.markdown("### ️ FSC (대형항공사)")

    fsc_col1, fsc_col2 = st.columns(2)

    with fsc_col1:
        badge = " 채용 진행중" if "대한항공" in ongoing_airlines else ""
        st.markdown(f"**대한항공** {badge}")
        st.caption("Excellence in Flight | 인천 거점")
        st.link_button(" koreanair.recruiter.co.kr",
                      AIRLINE_CAREER_URLS["대한항공"],
                      use_container_width=True)

    with fsc_col2:
        badge = " 채용 진행중" if "아시아나항공" in ongoing_airlines else ""
        st.markdown(f"**아시아나항공** {badge}")
        st.caption("아름다운 사람들 | 인천 거점")
        st.link_button(" flyasiana.recruiter.co.kr",
                      AIRLINE_CAREER_URLS["아시아나항공"],
                      use_container_width=True)

    st.markdown("---")

    # HSC (하이브리드)
    st.markdown("### HSC (하이브리드)")

    badge = " 채용 진행중" if "에어프레미아" in ongoing_airlines else ""
    st.markdown(f"**에어프레미아** {badge}")
    st.caption("New Way to Fly | 중장거리 노선 특화 | 인천 거점")
    st.link_button(" airpremia.career.greetinghr.com",
                  AIRLINE_CAREER_URLS["에어프레미아"],
                  use_container_width=True)

    st.markdown("---")

    # LCC (저비용항공사) - 8개
    st.markdown("### ️ LCC (저비용항공사)")

    lcc_airlines = [
        ("진에어", "Fun, Young, Dynamic", "인천/부산"),
        ("제주항공", "Fly, Better Fly", "김포/인천/부산"),
        ("티웨이항공", "즐거운 여행의 시작", "김포/인천/대구"),
        ("에어부산", "부산의 자부심", "김해"),
        ("에어서울", "프리미엄 LCC", "인천"),
        ("이스타항공", "새로운 도약", "인천/청주"),
        ("에어로케이", "하늘 위의 새로운 가치", "청주"),
        ("파라타항공", "행복한 여행 파트너", "양양"),
    ]

    # 3개씩 2줄 + 2개 1줄
    for i in range(0, len(lcc_airlines), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(lcc_airlines):
                airline, slogan, base = lcc_airlines[i + j]
                with col:
                    badge = "" if airline in ongoing_airlines else ""
                    st.markdown(f"**{airline}** {badge}")
                    st.caption(f"{slogan} | {base}")
                    url = AIRLINE_CAREER_URLS.get(airline, "")
                    if url:
                        st.link_button(f" 채용 페이지", url, use_container_width=True)

# ----------------------------
# 탭 5: 알림 구독
# ----------------------------
with tab5:
    st.subheader(" 채용 알림 구독")

    # 구독자 수 표시
    subscriber_count = get_subscriber_count()

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 24px; border-radius: 16px; color: white; text-align: center; margin-bottom: 20px;">
        <h2 style="margin: 0;"> {subscriber_count}명</h2>
        <p style="margin: 8px 0 0 0; opacity: 0.9;">이 채용 알림을 구독하고 있습니다</p>
    </div>
    """, unsafe_allow_html=True)

    st.info("**새로운 채용 공고가 등록되면 이메일로 알려드립니다!**")

    # 구독/구독해지 탭
    sub_tab1, sub_tab2 = st.tabs([" 구독 신청", " 구독 해지"])

    with sub_tab1:
        st.markdown("### 채용 알림 구독 신청")

        with st.form("subscribe_form"):
            col1, col2 = st.columns(2)

            with col1:
                sub_name = st.text_input("이름 *", placeholder="홍길동")
                sub_email = st.text_input("이메일 *", placeholder="example@email.com")

            with col2:
                sub_phone = st.text_input("연락처 (선택)", placeholder="010-1234-5678")
                st.caption("카카오톡 알림을 원하시면 연락처를 입력하세요")

            st.markdown("**관심 항공사 선택** (선택사항)")
            st.caption("선택하지 않으면 모든 항공사 채용 알림을 받습니다")

            airline_cols = st.columns(4)
            selected_airlines = []

            all_airlines = ["대한항공", "아시아나항공", "에어프레미아", "진에어", "제주항공",
                          "티웨이항공", "에어부산", "에어서울", "이스타항공", "에어로케이", "파라타항공"]

            for i, airline in enumerate(all_airlines):
                with airline_cols[i % 4]:
                    if st.checkbox(airline, key=f"airline_{airline}"):
                        selected_airlines.append(airline)

            st.markdown("---")

            agree = st.checkbox("개인정보 수집 및 이용에 동의합니다 (채용 알림 발송 목적)")

            submitted = st.form_submit_button(" 구독 신청", type="primary", use_container_width=True)

            if submitted:
                if not sub_name or not sub_email:
                    st.error("이름과 이메일은 필수 입력 항목입니다.")
                elif not agree:
                    st.error("개인정보 수집 및 이용에 동의해주세요.")
                elif "@" not in sub_email or "." not in sub_email:
                    st.error("올바른 이메일 형식을 입력해주세요.")
                else:
                    success, message = add_subscriber(sub_name, sub_email, sub_phone, selected_airlines)
                    if success:
                        st.success(f" {message}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.warning(message)

    with sub_tab2:
        st.markdown("### 구독 해지")
        st.caption("더 이상 알림을 받고 싶지 않으시면 이메일을 입력해주세요.")

        with st.form("unsubscribe_form"):
            unsub_email = st.text_input("등록된 이메일", placeholder="example@email.com")

            unsub_submitted = st.form_submit_button("구독 해지", use_container_width=True)

            if unsub_submitted:
                if not unsub_email:
                    st.error("이메일을 입력해주세요.")
                else:
                    success, message = unsubscribe(unsub_email)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.warning(message)

    st.markdown("---")

    # 알림 안내
    st.markdown("### 알림 안내")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: #f0fdf4; padding: 16px; border-radius: 12px; border-left: 4px solid #10b981;">
            <h4 style="margin: 0 0 8px 0;"> 이메일 알림</h4>
            <p style="font-size: 14px; margin: 0; color: #666;">
            새로운 채용 공고가 등록되면<br/>
            이메일로 알려드립니다.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: #fef3c7; padding: 16px; border-radius: 12px; border-left: 4px solid #f59e0b;">
            <h4 style="margin: 0 0 8px 0;"> 카카오톡 알림 (예정)</h4>
            <p style="font-size: 14px; margin: 0; color: #666;">
            연락처를 등록하시면<br/>
            카카오톡 알림도 받으실 수 있습니다.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.caption(" 알림은 관리자가 새 채용 공고를 등록할 때 발송됩니다.")
    st.caption(" 스팸 메일함도 확인해주세요!")

# ----------------------------
# 하단 정보
# ----------------------------
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.caption(" 채용 정보는 각 항공사 공식 채용 페이지에서 최종 확인하세요.")
    st.caption(" 본 페이지의 정보는 공식 발표 기준으로 작성되었습니다.")
with col2:
    # JSON 파일에서 마지막 업데이트 날짜 가져오기
    last_updated = ""
    if os.path.exists(HIRING_DATA_FILE):
        try:
            with open(HIRING_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                last_updated = data.get("last_updated", "")
        except Exception as e:
            logger.debug(f"Failed to read last_updated from hiring data: {e}")
    st.caption(f" 최종 업데이트: {last_updated if last_updated else '알 수 없음'}")
    st.caption(" 출처: 각 항공사 공식 채용사이트")

# 소스 링크
with st.expander("정보 출처"):
    st.markdown("""
    - [진에어 채용](https://jinair.recruiter.co.kr/) - 2026년 상반기 객실승무원 채용 공고
    - [파라타항공 채용](https://parataair.recruiter.co.kr/) - 2026년 상반기 4기 객실승무원 채용
    - [에어프레미아 채용](https://airpremia.career.greetinghr.com/) - 2026년 1차 신입 객실승무원 채용
    - [대한항공 채용](https://koreanair.recruiter.co.kr/) - 공식 채용사이트
    - [아시아나항공 채용](https://flyasiana.recruiter.co.kr/) - 공식 채용사이트
    - [제주항공 채용](https://jejuair.recruiter.co.kr/) - 공식 채용사이트
    - [티웨이항공 채용](https://twayair.recruiter.co.kr/) - 공식 채용사이트
    - [에어부산 채용](https://airbusan.recruiter.co.kr/) - 공식 채용사이트
    - [이스타항공](https://www.eastarjet.com/) - 공식 홈페이지
    - [에어로케이](https://www.aerok.com/) - 공식 홈페이지
    """)

# div 닫기
st.markdown('</div>', unsafe_allow_html=True)

# pages/10_채용알림.py
# 항공사 채용 일정 알림 페이지 - 사실 기반 정보

import streamlit as st
from datetime import datetime, timedelta
import json

# 구글 번역 방지
st.set_page_config(page_title="채용 일정 알림", page_icon="📅", layout="wide")

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="채용 알림")
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
        except:
            pass
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
    except:
        return None


def get_hiring_status(hire):
    """채용 상태 자동 계산 (날짜 기반)"""
    today = datetime.now().date()

    start_date_str = hire.get("start_date", "")
    end_date_str = hire.get("end_date", "")

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
    except:
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
st.title("📅 항공사 채용 일정 알림")
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

st.markdown("### 📊 채용 현황 (클릭하여 필터링)")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button(f"🟢 진행중\n**{ongoing_count}건**",
                 use_container_width=True,
                 type="primary" if st.session_state.selected_filter == "진행중" else "secondary"):
        st.session_state.selected_filter = "진행중"
        st.rerun()

with col2:
    if st.button(f"🟡 예정\n**{upcoming_count}건**",
                 use_container_width=True,
                 type="primary" if st.session_state.selected_filter == "예정" else "secondary"):
        st.session_state.selected_filter = "예정"
        st.rerun()

with col3:
    if st.button(f"⚫ 마감\n**{closed_count}건**",
                 use_container_width=True,
                 type="primary" if st.session_state.selected_filter == "마감" else "secondary"):
        st.session_state.selected_filter = "마감"
        st.rerun()

with col4:
    if st.button(f"📋 전체\n**{total_count}건**",
                 use_container_width=True,
                 type="primary" if st.session_state.selected_filter == "전체" else "secondary"):
        st.session_state.selected_filter = "전체"
        st.rerun()

st.caption(f"🔍 현재 필터: **{st.session_state.selected_filter}** | 상태는 마감일 기준 자동 계산됩니다")

# ----------------------------
# 긴급 알림 배너 (진행중인 채용)
# ----------------------------
if ongoing_list:
    st.markdown("---")
    st.markdown("### 🚨 현재 진행중인 채용")

    for hire in ongoing_list:
        dday = calculate_dday(hire.get("end_date"))

        if dday is not None and dday <= 3:
            banner_class = "alert-banner-urgent"
            urgent_text = "⚠️ 마감 임박!"
        else:
            banner_class = ""
            urgent_text = ""

        dday_text = f"D-{dday}" if dday and dday > 0 else "오늘 마감!" if dday == 0 else ""

        st.markdown(f"""
        <div class="alert-banner {banner_class}">
            <span style="font-size: 24px; margin-right: 12px;">✈️</span>
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
            st.link_button(f"🔗 {hire['airline']} 채용 페이지 바로가기", url, use_container_width=True)

        st.markdown("")

st.markdown("---")

# ----------------------------
# 탭 구성
# ----------------------------
tab1, tab2, tab3 = st.tabs([
    "📋 채용 일정",
    "📊 채용 프로세스",
    "🔗 채용 페이지 바로가기"
])

# ----------------------------
# 탭 1: 채용 일정
# ----------------------------
with tab1:
    st.subheader("📋 2026년 채용 일정")

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
            status_emoji = "🟢"
            card_style = "ongoing"
        elif hire["status"] == "예정":
            status_emoji = "🟡"
            card_style = "upcoming"
        else:
            status_emoji = "⚫"
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
                st.markdown(f"📆 **{hire['period']}**")
                st.markdown(f"👥 **모집인원:** {hire['expected_count']}")
                st.info(f"💡 {hire['note']}")
                st.caption(f"📌 출처: {hire.get('source', '공식 채용사이트')}")

            with col2:
                # D-Day 표시
                if hire["status"] == "진행중":
                    if dday is not None:
                        if dday > 0:
                            st.metric("마감까지", f"D-{dday}")
                        elif dday == 0:
                            st.error("🚨 오늘 마감!")
                        else:
                            st.warning("마감됨")

                    # 지원 버튼
                    url = AIRLINE_CAREER_URLS.get(airline, "")
                    if url:
                        st.link_button("🔗 지원하기", url, use_container_width=True)
                elif hire["status"] == "예정":
                    start_dday = calculate_dday(hire.get("start_date"))
                    if start_dday is not None and start_dday > 0:
                        st.metric("시작까지", f"D-{start_dday}")
                    st.info("곧 시작됩니다!")
                    url = AIRLINE_CAREER_URLS.get(airline, "")
                    if url:
                        st.link_button("📋 채용 페이지 확인", url, use_container_width=True)
                else:
                    st.caption("다음 채용 공고를 기다려주세요")
                    url = AIRLINE_CAREER_URLS.get(airline, "")
                    if url:
                        st.link_button("📋 채용 페이지 확인", url, use_container_width=True)

            # 자격요건 (확장)
            with st.expander("📋 자격요건 & 전형절차"):
                req_col1, req_col2 = st.columns(2)

                with req_col1:
                    st.markdown("**필수 자격**")
                    reqs = hire.get("requirements", {})
                    for key, val in reqs.items():
                        label = {
                            "education": "📚 학력",
                            "vision": "👁️ 시력",
                            "english": "🌏 영어",
                            "swimming": "🏊 수영",
                            "etc": "📌 기타"
                        }.get(key, key)
                        st.caption(f"{label}: {val}")

                with req_col2:
                    st.markdown("**우대사항**")
                    preferred = hire.get("preferred", [])
                    for p in preferred:
                        st.caption(f"✓ {p}")

                    st.markdown("")
                    st.markdown("**전형절차**")
                    st.caption(hire.get("process", "미공개"))

            st.markdown("---")

# ----------------------------
# 탭 2: 채용 프로세스 (11개 전체 항공사)
# ----------------------------
with tab2:
    st.subheader("📊 항공사별 채용 프로세스")
    st.caption("국내 11개 항공사 전체 정보")

    # 현재 진행중인 항공사 표시
    ongoing_airlines = [h["airline"] for h in ALL_HIRING if h["status"] == "진행중"]

    # 항공사 순서: FSC → HSC → LCC
    airline_order = ["대한항공", "아시아나항공", "에어프레미아", "진에어", "제주항공",
                     "티웨이항공", "에어부산", "에어서울", "이스타항공", "에어로케이", "파라타항공"]

    selected_airline = st.selectbox(
        "항공사 선택",
        airline_order,
        format_func=lambda x: f"🟢 {x} (채용 진행중)" if x in ongoing_airlines else x
    )

    # 선택한 항공사 정보 (AIRLINE_INFO에서 가져오기)
    airline_info = AIRLINE_INFO.get(selected_airline, {})

    if airline_info:
        airline_type = airline_info.get("type", "LCC")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### ✈️ {selected_airline}")
            st.caption(f"{airline_type} | {airline_info.get('slogan', '')} | 거점: {airline_info.get('base', '')}")
        with col2:
            url = AIRLINE_CAREER_URLS.get(selected_airline, "")
            if url:
                st.link_button("채용 페이지 →", url)

        # 진행중인 채용 알림
        if selected_airline in ongoing_airlines:
            st.success(f"🟢 **{selected_airline}** 현재 채용 진행중!")

        st.markdown("---")

        # 전형 절차 시각화
        st.markdown("### 📈 전형 단계")

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
        st.markdown("### 📋 자격요건")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**필수 자격**")
            reqs = airline_info.get("requirements", {})
            for key, val in reqs.items():
                label = {
                    "education": "📚 학력",
                    "vision": "👁️ 시력",
                    "english": "🌏 영어",
                    "swimming": "🏊 수영",
                    "etc": "📌 기타"
                }.get(key, key)
                st.info(f"{label}: {val}")

        with col2:
            st.markdown("**우대사항**")
            preferred = airline_info.get("preferred", [])
            for p in preferred:
                st.success(f"✓ {p}")

# ----------------------------
# 탭 3: 채용 페이지 바로가기 (11개 전체)
# ----------------------------
with tab3:
    st.subheader("🔗 항공사 채용 페이지 바로가기")
    st.caption("국내 11개 항공사 공식 채용 페이지")

    st.info("📢 모든 링크는 실제 항공사 공식 채용 페이지로 연결됩니다.")

    # 현재 진행중인 항공사 확인
    ongoing_airlines = [h["airline"] for h in ALL_HIRING if h["status"] == "진행중"]

    # FSC (대형항공사)
    st.markdown("### 🏛️ FSC (대형항공사)")

    fsc_col1, fsc_col2 = st.columns(2)

    with fsc_col1:
        badge = "🟢 채용 진행중" if "대한항공" in ongoing_airlines else ""
        st.markdown(f"**대한항공** {badge}")
        st.caption("Excellence in Flight | 인천 거점")
        st.link_button("🔗 koreanair.recruiter.co.kr",
                      AIRLINE_CAREER_URLS["대한항공"],
                      use_container_width=True)

    with fsc_col2:
        badge = "🟢 채용 진행중" if "아시아나항공" in ongoing_airlines else ""
        st.markdown(f"**아시아나항공** {badge}")
        st.caption("아름다운 사람들 | 인천 거점")
        st.link_button("🔗 flyasiana.recruiter.co.kr",
                      AIRLINE_CAREER_URLS["아시아나항공"],
                      use_container_width=True)

    st.markdown("---")

    # HSC (하이브리드)
    st.markdown("### 🌟 HSC (하이브리드)")

    badge = "🟢 채용 진행중" if "에어프레미아" in ongoing_airlines else ""
    st.markdown(f"**에어프레미아** {badge}")
    st.caption("New Way to Fly | 중장거리 노선 특화 | 인천 거점")
    st.link_button("🔗 airpremia.career.greetinghr.com",
                  AIRLINE_CAREER_URLS["에어프레미아"],
                  use_container_width=True)

    st.markdown("---")

    # LCC (저비용항공사) - 8개
    st.markdown("### ✈️ LCC (저비용항공사)")

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
                    badge = "🟢" if airline in ongoing_airlines else ""
                    st.markdown(f"**{airline}** {badge}")
                    st.caption(f"{slogan} | {base}")
                    url = AIRLINE_CAREER_URLS.get(airline, "")
                    if url:
                        st.link_button(f"🔗 채용 페이지", url, use_container_width=True)

# ----------------------------
# 하단 정보
# ----------------------------
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.caption("💡 채용 정보는 각 항공사 공식 채용 페이지에서 최종 확인하세요.")
    st.caption("📅 본 페이지의 정보는 공식 발표 기준으로 작성되었습니다.")
with col2:
    # JSON 파일에서 마지막 업데이트 날짜 가져오기
    last_updated = ""
    if os.path.exists(HIRING_DATA_FILE):
        try:
            with open(HIRING_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                last_updated = data.get("last_updated", "")
        except:
            pass
    st.caption(f"🔄 최종 업데이트: {last_updated if last_updated else '알 수 없음'}")
    st.caption("📌 출처: 각 항공사 공식 채용사이트")

# 소스 링크
with st.expander("📚 정보 출처"):
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

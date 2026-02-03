# pages/23_D-Day캘린더.py
# D-Day 캘린더 - 채용 일정 종합 관리
# 기능: 대시보드, 월간 캘린더, 일정관리(템플릿), 일일 체크리스트, 목표, D-Day 가이드

import streamlit as st
import os
import sys
import json
import calendar
from datetime import datetime, date, timedelta
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import AIRLINES

from sidebar_common import init_page, end_page

init_page(
    title="D-Day 캘린더",
    current_page="D-Day캘린더",
    wide_layout=True
)


# ========================================
# 데이터 관리
# ========================================
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CALENDAR_FILE = os.path.join(DATA_DIR, "my_calendar.json")


@st.cache_data(ttl=60)
def load_calendar():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(CALENDAR_FILE):
            with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"events": [], "goals": [], "daily_todos": {}, "processes": []}


def save_calendar(data):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        load_calendar.clear()  # 캐시 무효화
    except Exception:
        pass


def get_dday(target_date_str):
    try:
        target = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        diff = (target - date.today()).days
        if diff > 0:
            return f"D-{diff}", diff
        elif diff == 0:
            return "D-Day", 0
        else:
            return f"D+{abs(diff)}", diff
    except Exception:
        return "-", None


# ========================================
# 상수 데이터
# ========================================
EVENT_CATEGORIES = {
    "서류 접수": {"icon": "", "color": "#3b82f6"},
    "서류 마감": {"icon": "⏰", "color": "#ef4444"},
    "서류 발표": {"icon": "", "color": "#f59e0b"},
    "1차 면접": {"icon": "", "color": "#8b5cf6"},
    "2차 면접": {"icon": "", "color": "#6366f1"},
    "영어 면접": {"icon": "", "color": "#0891b2"},
    "체력 테스트": {"icon": "", "color": "#10b981"},
    "수영 테스트": {"icon": "", "color": "#06b6d4"},
    "최종 발표": {"icon": "", "color": "#ec4899"},
    "건강검진": {"icon": "", "color": "#14b8a6"},
    "입사": {"icon": "️", "color": "#f43f5e"},
    "기타": {"icon": "", "color": "#6b7280"},
}

# 항공사별 채용 전형 템플릿
AIRLINE_TEMPLATES = {
    "대한항공": {
        "stages": [
            {"name": "서류 접수", "category": "서류 접수", "offset": 0},
            {"name": "서류 마감", "category": "서류 마감", "offset": 14},
            {"name": "서류 발표", "category": "서류 발표", "offset": 28},
            {"name": "1차 면접 (영어+실무)", "category": "1차 면접", "offset": 35},
            {"name": "2차 면접 (임원)", "category": "2차 면접", "offset": 49},
            {"name": "체력검정 (수영 25m)", "category": "수영 테스트", "offset": 56},
            {"name": "건강검진", "category": "건강검진", "offset": 63},
            {"name": "최종 발표", "category": "최종 발표", "offset": 70},
        ],
        "note": "영어면접 포함, 수영 25m 필수"
    },
    "아시아나항공": {
        "stages": [
            {"name": "서류 접수", "category": "서류 접수", "offset": 0},
            {"name": "서류 마감", "category": "서류 마감", "offset": 14},
            {"name": "서류 발표", "category": "서류 발표", "offset": 28},
            {"name": "1차 면접", "category": "1차 면접", "offset": 35},
            {"name": "2차 면접 (임원)", "category": "2차 면접", "offset": 49},
            {"name": "건강검진/수영Test", "category": "수영 테스트", "offset": 56},
            {"name": "최종 발표", "category": "최종 발표", "offset": 63},
        ],
        "note": "수영 25m 포함 (건강검진 단계)"
    },
    "제주항공": {
        "stages": [
            {"name": "서류 접수", "category": "서류 접수", "offset": 0},
            {"name": "서류 마감", "category": "서류 마감", "offset": 10},
            {"name": "서류 발표", "category": "서류 발표", "offset": 21},
            {"name": "1차 면접 (그룹토론)", "category": "1차 면접", "offset": 28},
            {"name": "2차 면접 (임원)", "category": "2차 면접", "offset": 42},
            {"name": "최종 발표", "category": "최종 발표", "offset": 49},
        ],
        "note": "그룹토론 면접 특징"
    },
    "진에어": {
        "stages": [
            {"name": "서류 접수", "category": "서류 접수", "offset": 0},
            {"name": "서류 마감", "category": "서류 마감", "offset": 10},
            {"name": "서류 발표", "category": "서류 발표", "offset": 21},
            {"name": "1차 면접", "category": "1차 면접", "offset": 28},
            {"name": "2차 면접 (영어 포함)", "category": "영어 면접", "offset": 42},
            {"name": "최종 발표", "category": "최종 발표", "offset": 49},
        ],
        "note": "영어면접 포함"
    },
    "티웨이항공": {
        "stages": [
            {"name": "서류 접수", "category": "서류 접수", "offset": 0},
            {"name": "서류 마감", "category": "서류 마감", "offset": 10},
            {"name": "서류 발표", "category": "서류 발표", "offset": 21},
            {"name": "1차 면접", "category": "1차 면접", "offset": 28},
            {"name": "2차 면접", "category": "2차 면접", "offset": 42},
            {"name": "최종 발표", "category": "최종 발표", "offset": 49},
        ],
        "note": "표준 전형 절차"
    },
    "에어부산": {
        "stages": [
            {"name": "서류 접수", "category": "서류 접수", "offset": 0},
            {"name": "서류 마감", "category": "서류 마감", "offset": 10},
            {"name": "서류 발표", "category": "서류 발표", "offset": 21},
            {"name": "1차 면접", "category": "1차 면접", "offset": 28},
            {"name": "2차 면접", "category": "2차 면접", "offset": 42},
            {"name": "최종 발표", "category": "최종 발표", "offset": 49},
        ],
        "note": "표준 전형 절차"
    },
    "에어서울": {
        "stages": [
            {"name": "서류 접수", "category": "서류 접수", "offset": 0},
            {"name": "서류 마감", "category": "서류 마감", "offset": 10},
            {"name": "서류 발표", "category": "서류 발표", "offset": 21},
            {"name": "1차 면접", "category": "1차 면접", "offset": 28},
            {"name": "2차 면접", "category": "2차 면접", "offset": 42},
            {"name": "최종 발표", "category": "최종 발표", "offset": 49},
        ],
        "note": "표준 전형 절차"
    },
    "이스타항공": {
        "stages": [
            {"name": "서류 접수", "category": "서류 접수", "offset": 0},
            {"name": "서류 마감", "category": "서류 마감", "offset": 10},
            {"name": "서류 발표", "category": "서류 발표", "offset": 21},
            {"name": "1차 면접", "category": "1차 면접", "offset": 28},
            {"name": "체력TEST", "category": "체력 테스트", "offset": 35},
            {"name": "2차 면접", "category": "2차 면접", "offset": 42},
            {"name": "최종 발표", "category": "최종 발표", "offset": 49},
        ],
        "note": "체력TEST 단계 포함"
    },
    "에어로케이": {
        "stages": [
            {"name": "서류 접수", "category": "서류 접수", "offset": 0},
            {"name": "서류 마감", "category": "서류 마감", "offset": 10},
            {"name": "서류 발표", "category": "서류 발표", "offset": 21},
            {"name": "1차 면접", "category": "1차 면접", "offset": 28},
            {"name": "2차 면접", "category": "2차 면접", "offset": 42},
            {"name": "최종 발표", "category": "최종 발표", "offset": 49},
        ],
        "note": "표준 전형 절차"
    },
    "에어프레미아": {
        "stages": [
            {"name": "서류 접수", "category": "서류 접수", "offset": 0},
            {"name": "서류 마감", "category": "서류 마감", "offset": 14},
            {"name": "서류 발표", "category": "서류 발표", "offset": 28},
            {"name": "1차 면접 (영어+토론)", "category": "영어 면접", "offset": 35},
            {"name": "컬처핏 면접 + 체력측정", "category": "체력 테스트", "offset": 49},
            {"name": "최종 발표", "category": "최종 발표", "offset": 56},
        ],
        "note": "영어면접 + 자체 체력측정"
    },
    "파라타항공": {
        "stages": [
            {"name": "서류 접수 (국민체력100 제출)", "category": "서류 접수", "offset": 0},
            {"name": "서류 마감", "category": "서류 마감", "offset": 14},
            {"name": "서류 발표", "category": "서류 발표", "offset": 28},
            {"name": "1차 면접", "category": "1차 면접", "offset": 35},
            {"name": "2차 면접", "category": "2차 면접", "offset": 49},
            {"name": "최종 발표", "category": "최종 발표", "offset": 56},
        ],
        "note": "국민체력100 결과서 제출 필수"
    },
}

# D-Day 가이드 (남은 기간별)
DDAY_GUIDES = {
    "면접": {
        30: {
            "title": "D-30: 본격 면접 준비 시작",
            "tasks": [
                "자소서 최종 점검 및 예상 질문 추출",
                "모의면접 주 2회 이상 연습",
                "항공사 최신 뉴스 스크랩 시작",
                "면접 복장 준비 (정장, 구두, 악세서리)",
                "이미지메이킹 연습 (미소, 자세, 시선)",
            ]
        },
        14: {
            "title": "D-14: 집중 준비 기간",
            "tasks": [
                "1분 자기소개 완벽 암기 + 자연스럽게",
                "모의면접 매일 1회 (녹화 분석)",
                "영어 면접 준비 (해당 시)",
                "지원 항공사 인재상/핵심가치 암기",
                "면접장 위치 확인 + 교통편 계획",
            ]
        },
        7: {
            "title": "D-7: 마무리 점검",
            "tasks": [
                "면접 복장 리허설 (전신 거울 확인)",
                "헤어/메이크업 최종 스타일 결정",
                "면접 서류 준비 (이력서, 자격증 사본 등)",
                "체력 관리 (무리한 운동 금지)",
                "수면 패턴 조절 (일찍 자고 일찍 일어나기)",
            ]
        },
        3: {
            "title": "D-3: 컨디션 관리",
            "tasks": [
                "면접 준비물 최종 체크리스트 작성",
                "면접장까지 이동 시간 재확인",
                "가벼운 복습만 (새로운 내용 X)",
                "충분한 수면 + 피부 관리",
                "긍정적 마인드 + 심호흡 연습",
            ]
        },
        1: {
            "title": "D-1: 전날 준비",
            "tasks": [
                "면접 복장 + 가방 미리 세팅",
                "준비물 가방에 넣기 (필기구, 서류, 보조배터리)",
                "면접장 교통편 최종 확인",
                "일찍 취침 (최소 7시간 수면)",
                "알람 2개 이상 설정",
            ]
        },
        0: {
            "title": "D-Day: 면접 당일",
            "tasks": [
                "3시간 전 기상 + 스킨케어",
                "2시간 전 메이크업 + 헤어",
                "1시간 전 복장 착용 + 최종 확인",
                "30분 전 면접장 도착",
                "심호흡 3회 + 미소 연습 + 자신감!",
            ]
        },
    },
    "서류": {
        7: {
            "title": "서류 마감 D-7",
            "tasks": [
                "자소서 초안 완성",
                "맞춤법/문법 검수",
                "첨삭 받기 (AI 또는 주변인)",
                "지원서 양식 확인 + 사진 준비",
                "제출 서류 리스트 확인",
            ]
        },
        3: {
            "title": "서류 마감 D-3",
            "tasks": [
                "자소서 최종 수정",
                "증명사진 확인 (사이즈, 배경색)",
                "자격증/성적증명서 발급",
                "지원서 미리보기 확인",
                "비상 연락처 + 이메일 확인",
            ]
        },
        1: {
            "title": "서류 마감 D-1",
            "tasks": [
                "자소서 최최종 검토 (오타 없는지)",
                "첨부파일 정상 업로드 확인",
                "지원서 제출 (마감 당일 피하기)",
                "제출 확인 메일/문자 확인",
                "제출 완료 캡쳐 저장",
            ]
        },
    },
    "체력": {
        14: {
            "title": "체력시험 D-14",
            "tasks": [
                "수영 25m 완영 최종 확인 (해당 시)",
                "체력 항목별 모의 테스트",
                "부족한 항목 집중 훈련",
                "규칙적인 식사 + 수면",
                "과도한 운동 삼가 (부상 방지)",
            ]
        },
        3: {
            "title": "체력시험 D-3",
            "tasks": [
                "가벼운 스트레칭만 (근육통 방지)",
                "수영복/운동복 준비",
                "수영장/체육관 위치 확인",
                "탄수화물 위주 식사",
                "충분한 수면",
            ]
        },
        1: {
            "title": "체력시험 D-1",
            "tasks": [
                "운동 금지 (완전 휴식)",
                "준비물 챙기기 (수영복, 물안경, 수건 등)",
                "가벼운 스트레칭만",
                "일찍 취침",
                "아침 식사 계획 (바나나 + 물)",
            ]
        },
    },
}

# 반복 할 일 템플릿
DAILY_TEMPLATES = {
    "면접 준비": [
        "1분 자기소개 연습",
        "예상 질문 3개 답변 연습",
        "뉴스 스크랩 (항공/시사)",
        "미소 + 자세 연습 (거울 1분)",
    ],
    "체력 준비": [
        "스트레칭 10분",
        "근력 운동 30분",
        "유산소 운동 20분",
    ],
    "영어 준비": [
        "영어 자기소개 연습",
        "영어 예상질문 2개 답변",
        "영어 뉴스 1개 읽기",
    ],
    "이미지 준비": [
        "메이크업 연습",
        "헤어 스타일 연습",
        "면접 복장 착용 연습",
    ],
}


# ========================================
# CSS
# ========================================
st.markdown("""
<style>
.dday-hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white; border-radius: 20px; padding: 30px; text-align: center; margin: 10px 0;
}
.dday-card {
    border-radius: 14px; padding: 20px; text-align: center; margin: 5px 0;
    border: 2px solid; transition: transform 0.2s;
}
.dday-card:hover { transform: translateY(-2px); }
.cal-cell {
    border: 1px solid #e5e7eb; border-radius: 8px; padding: 6px;
    min-height: 80px; margin: 2px; text-align: center;
}
.cal-today { background: #667eea15; border-color: #667eea; }
.cal-has-event { font-weight: bold; }
.cal-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin: 1px; }
.process-bar { border-radius: 12px; padding: 16px; margin: 8px 0; border-left: 4px solid; }
.guide-card { background: #f8f9fa; border-radius: 12px; padding: 16px; margin: 10px 0; border-left: 4px solid #667eea; }
.stat-box { background: white; border-radius: 12px; padding: 16px; text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08); margin: 5px; }
.todo-done { text-decoration: line-through; opacity: 0.5; }
</style>
""", unsafe_allow_html=True)


# ========================================
# 메인
# ========================================
st.title("D-Day 캘린더")
st.markdown("면접 일정, 목표, 체크리스트를 한 곳에서 관리하세요!")

cal_data = load_calendar()
events = cal_data.get("events", [])
goals = cal_data.get("goals", [])
daily_todos = cal_data.get("daily_todos", {})
processes = cal_data.get("processes", [])

# 탭 구성
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
 " 대시보드",
 " 월간 캘린더",
 " 일정 관리",
 " 일일 체크리스트",
 " 목표 설정",
 " D-Day 가이드",
])


# ========================================
# 탭1: 대시보드
# ========================================
with tab1:
    st.markdown("### 준비 현황 대시보드")

    # 상단 메트릭
    today_str = date.today().strftime("%Y-%m-%d")
    upcoming_events = [e for e in events if e.get("date", "") >= today_str]
    past_events = [e for e in events if e.get("date", "") < today_str]
    completed_goals = [g for g in goals if g.get("completed")]
    today_todos = daily_todos.get(today_str, [])
    today_done = len([t for t in today_todos if t.get("done")])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <div style="font-size: 28px;"></div>
            <div style="font-size: 24px; font-weight: bold; color: #3b82f6;">{len(upcoming_events)}</div>
            <div style="font-size: 13px; color: #666;">예정된 일정</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        interview_count = len([e for e in upcoming_events if "면접" in e.get("category", "")])
        st.markdown(f"""
        <div class="stat-box">
            <div style="font-size: 28px;"></div>
            <div style="font-size: 24px; font-weight: bold; color: #8b5cf6;">{interview_count}</div>
            <div style="font-size: 13px; color: #666;">면접 예정</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        goal_pct = int(len(completed_goals) / max(len(goals), 1) * 100)
        st.markdown(f"""
        <div class="stat-box">
            <div style="font-size: 28px;"></div>
            <div style="font-size: 24px; font-weight: bold; color: #10b981;">{goal_pct}%</div>
            <div style="font-size: 13px; color: #666;">목표 달성률</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        todo_pct = int(today_done / max(len(today_todos), 1) * 100) if today_todos else 0
        st.markdown(f"""
        <div class="stat-box">
            <div style="font-size: 28px;"></div>
            <div style="font-size: 24px; font-weight: bold; color: #f59e0b;">{todo_pct}%</div>
            <div style="font-size: 13px; color: #666;">오늘 할 일</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 가장 가까운 D-Day 표시
    st.markdown("#### 다가오는 일정 TOP 3")

    upcoming_sorted = sorted(upcoming_events, key=lambda x: x.get("date", ""))[:3]

    if upcoming_sorted:
        cols = st.columns(min(len(upcoming_sorted), 3))
        for i, event in enumerate(upcoming_sorted):
            dday_str, diff = get_dday(event.get("date", ""))
            cat = EVENT_CATEGORIES.get(event.get("category", "기타"), EVENT_CATEGORIES["기타"])
            with cols[i]:
                urgency_bg = "#fff5f5" if diff is not None and diff <= 7 else f"{cat['color']}10"
                st.markdown(f"""
                <div style="background: {urgency_bg}; border: 2px solid {cat['color']};
                            border-radius: 14px; padding: 20px; text-align: center;">
                    <div style="font-size: 30px;">{cat['icon']}</div>
                    <div style="font-size: 28px; font-weight: 800; color: {cat['color']};">{dday_str}</div>
                    <div style="font-weight: 600; margin-top: 5px; font-size: 14px;">{event.get('title', '')}</div>
                    <div style="font-size: 12px; color: #666; margin-top: 3px;">
                        {event.get('airline', '')} {'| ' if event.get('airline') else ''}{event.get('date', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("예정된 일정이 없습니다. '일정 관리' 탭에서 일정을 추가해보세요!")

    st.markdown("---")

    # 항공사별 진행 현황
    st.markdown("#### ️ 항공사별 진행 현황")

    # 이벤트에서 항공사별 그룹핑
    airline_events = defaultdict(list)
    for e in events:
        if e.get("airline"):
            airline_events[e["airline"]].append(e)

    if airline_events:
        for airline, a_events in airline_events.items():
            a_events_sorted = sorted(a_events, key=lambda x: x.get("date", ""))
            total_stages = len(a_events_sorted)
            done_stages = len([e for e in a_events_sorted if e.get("date", "") < today_str])
            progress = done_stages / max(total_stages, 1)

            # 현재 단계
            current_stage = "대기 중"
            for e in a_events_sorted:
                if e.get("date", "") >= today_str:
                    current_stage = e.get("title", "")
                    break

            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**️ {airline}** - 다음: {current_stage}")
                st.progress(progress, text=f"{done_stages}/{total_stages} 단계 완료")
            with col2:
                next_event = next((e for e in a_events_sorted if e.get("date", "") >= today_str), None)
                if next_event:
                    dday_str, _ = get_dday(next_event.get("date", ""))
                    st.markdown(f"<div style='text-align:center; font-size: 20px; font-weight: bold; color: #667eea;'>{dday_str}</div>", unsafe_allow_html=True)
    else:
        st.caption("일정에 항공사를 지정하면 진행 현황이 여기에 표시됩니다.")

    # 이번 주 일정
    st.markdown("---")
    st.markdown("#### 이번 주 일정")

    week_start = date.today()
    week_end = week_start + timedelta(days=7)
    week_events = [e for e in events if week_start.strftime("%Y-%m-%d") <= e.get("date", "") <= week_end.strftime("%Y-%m-%d")]

    if week_events:
        for event in sorted(week_events, key=lambda x: x.get("date", "")):
            cat = EVENT_CATEGORIES.get(event.get("category", "기타"), EVENT_CATEGORIES["기타"])
            dday_str, _ = get_dday(event.get("date", ""))
            day_name = ["월", "화", "수", "목", "금", "토", "일"][datetime.strptime(event["date"], "%Y-%m-%d").weekday()]
            st.markdown(f"{cat['icon']} **{event['date'][-5:]}({day_name})** - {event.get('title', '')} `{dday_str}`")
    else:
        st.caption("이번 주 예정된 일정이 없습니다.")


# ========================================
# 탭2: 월간 캘린더 뷰
# ========================================
with tab2:
    st.markdown("### 월간 캘린더")

    # 월 선택
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        cal_year = st.selectbox("연도", [2025, 2026, 2027], index=1 if date.today().year == 2026 else 0, key="cal_year")
    with col2:
        cal_month = st.selectbox("월", list(range(1, 13)), index=date.today().month - 1, key="cal_month")

    # 해당 월의 이벤트 가져오기
    month_str = f"{cal_year}-{cal_month:02d}"
    month_events = [e for e in events if e.get("date", "").startswith(month_str)]

    # 날짜별 이벤트 매핑
    date_events = defaultdict(list)
    for e in month_events:
        day = int(e.get("date", "")[-2:])
        date_events[day].append(e)

    # 캘린더 렌더링
    cal = calendar.Calendar(firstweekday=6)  # 일요일 시작
    month_days = cal.monthdays2calendar(cal_year, cal_month)

    # 요일 헤더
    day_headers = ["일", "월", "화", "수", "목", "금", "토"]
    header_cols = st.columns(7)
    for i, dh in enumerate(day_headers):
        with header_cols[i]:
            color = "#dc3545" if i == 0 else "#3b82f6" if i == 6 else "#333"
            st.markdown(f"<div style='text-align: center; font-weight: bold; color: {color}; padding: 5px;'>{dh}</div>", unsafe_allow_html=True)

    # 주별 렌더링
    for week in month_days:
        cols = st.columns(7)
        for i, (day, weekday) in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown("<div style='min-height: 80px;'></div>", unsafe_allow_html=True)
                else:
                    is_today = (cal_year == date.today().year and cal_month == date.today().month and day == date.today().day)
                    has_events = day in date_events
                    day_events_list = date_events.get(day, [])

                    # 셀 스타일
                    bg = "#667eea15" if is_today else "white"
                    border = "2px solid #667eea" if is_today else "1px solid #e5e7eb"
                    day_color = "#dc3545" if i == 0 else "#3b82f6" if i == 6 else "#333"
                    font_weight = "bold" if has_events or is_today else "normal"

                    # 이벤트 도트 생성
                    dots_html = ""
                    if day_events_list:
                        dots = []
                        for de in day_events_list[:3]:
                            cat = EVENT_CATEGORIES.get(de.get("category", "기타"), EVENT_CATEGORIES["기타"])
                            dots.append(f"<span class='cal-dot' style='background: {cat['color']};'></span>")
                        dots_html = " ".join(dots)

                    # 이벤트 제목 (첫 번째만)
                    title_html = ""
                    if day_events_list:
                        first_title = day_events_list[0].get("title", "")[:6]
                        if len(day_events_list) > 1:
                            first_title += f" +{len(day_events_list)-1}"
                        title_html = f"<div style='font-size: 10px; color: #555; margin-top: 2px; overflow: hidden; white-space: nowrap;'>{first_title}</div>"

                    st.markdown(f"""
                    <div style="background: {bg}; border: {border}; border-radius: 8px;
                                padding: 6px; min-height: 75px; margin: 1px;">
                        <div style="color: {day_color}; font-weight: {font_weight}; font-size: 13px;">{day}</div>
                        <div style="margin-top: 3px;">{dots_html}</div>
                        {title_html}
                    </div>
                    """, unsafe_allow_html=True)

    # 범례
    st.markdown("---")
    st.markdown("**범례:**")
    legend_cols = st.columns(6)
    for i, (cat_name, cat_info) in enumerate(list(EVENT_CATEGORIES.items())[:6]):
        with legend_cols[i]:
            st.markdown(f"<span class='cal-dot' style='background: {cat_info['color']};'></span> {cat_name}", unsafe_allow_html=True)

    # 해당 월 일정 목록
    if month_events:
        st.markdown("---")
        st.markdown(f"####  {cal_month}월 일정 목록")
        for event in sorted(month_events, key=lambda x: x.get("date", "")):
            cat = EVENT_CATEGORIES.get(event.get("category", "기타"), EVENT_CATEGORIES["기타"])
            dday_str, _ = get_dday(event.get("date", ""))
            st.markdown(f"{cat['icon']} **{event['date'][-5:]}** {event.get('title', '')} {'| ' + event.get('airline', '') if event.get('airline') else ''} `{dday_str}`")


# ========================================
# 탭3: 일정 관리 (템플릿 포함)
# ========================================
with tab3:
    st.markdown("### 일정 관리")

    sub_tab1, sub_tab2, sub_tab3 = st.tabs([" 일정 추가", " 전형 템플릿", " 전체 일정"])

    # ----- 일정 추가 -----
    with sub_tab1:
        st.markdown("#### 새 일정 추가")

        with st.form("add_event_form"):
            col1, col2 = st.columns(2)
            with col1:
                event_title = st.text_input("일정명 *", placeholder="예: 대한항공 1차 면접")
                event_airline = st.selectbox("항공사", ["선택 안함"] + AIRLINES, key="add_airline")
                event_category = st.selectbox("카테고리", list(EVENT_CATEGORIES.keys()), key="add_cat")
            with col2:
                event_date = st.date_input("날짜 *", value=date.today(), key="add_date")
                event_time = st.time_input("시간 (선택)", value=None, key="add_time")
                event_location = st.text_input("장소", placeholder="면접장 주소", key="add_loc")

            event_note = st.text_input("메모", placeholder="준비물, 주의사항 등", key="add_note")

            if st.form_submit_button("일정 추가", type="primary", use_container_width=True):
                if not event_title:
                    st.error("일정명을 입력하세요!")
                else:
                    new_event = {
                        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                        "title": event_title,
                        "airline": event_airline if event_airline != "선택 안함" else "",
                        "category": event_category,
                        "date": event_date.strftime("%Y-%m-%d"),
                        "time": event_time.strftime("%H:%M") if event_time else "",
                        "location": event_location,
                        "note": event_note,
                        "created_at": datetime.now().isoformat()
                    }
                    cal_data["events"].append(new_event)
                    save_calendar(cal_data)
                    st.success(f"'{event_title}' 일정이 추가되었습니다!")
                    st.rerun()

    # ----- 전형 템플릿 -----
    with sub_tab2:
        st.markdown("#### 채용 전형 템플릿")
        st.info("항공사를 선택하고 서류 접수일만 입력하면, 전형 전체 일정이 자동 생성됩니다!")

        col1, col2 = st.columns(2)
        with col1:
            tmpl_airline = st.selectbox("항공사 선택", AIRLINES, key="tmpl_airline")
            tmpl_start = st.date_input("서류 접수 시작일", value=date.today(), key="tmpl_start")

        with col2:
            if tmpl_airline in AIRLINE_TEMPLATES:
                tmpl = AIRLINE_TEMPLATES[tmpl_airline]
                st.caption(f" {tmpl['note']}")
                st.markdown("**전형 단계 미리보기:**")
                for stage in tmpl["stages"]:
                    stage_date = tmpl_start + timedelta(days=stage["offset"])
                    cat = EVENT_CATEGORIES.get(stage["category"], EVENT_CATEGORIES["기타"])
                    st.markdown(f"{cat['icon']} {stage_date.strftime('%m/%d')} - {stage['name']}")

        if tmpl_airline in AIRLINE_TEMPLATES:
            if st.button("전체 일정 자동 생성", type="primary", use_container_width=True, key="gen_tmpl"):
                tmpl = AIRLINE_TEMPLATES[tmpl_airline]
                generated = 0
                for stage in tmpl["stages"]:
                    stage_date = tmpl_start + timedelta(days=stage["offset"])
                    new_event = {
                        "id": datetime.now().strftime("%Y%m%d%H%M%S%f") + str(generated),
                        "title": f"[{tmpl_airline}] {stage['name']}",
                        "airline": tmpl_airline,
                        "category": stage["category"],
                        "date": stage_date.strftime("%Y-%m-%d"),
                        "time": "",
                        "location": "",
                        "note": f"자동 생성 (템플릿 기반, 예상 일정)",
                        "created_at": datetime.now().isoformat()
                    }
                    cal_data["events"].append(new_event)
                    generated += 1
                save_calendar(cal_data)
                st.success(f" {tmpl_airline} 전형 일정 {generated}개가 생성되었습니다!")
                st.rerun()
        else:
            st.warning("해당 항공사의 템플릿이 없습니다.")

    # ----- 전체 일정 -----
    with sub_tab3:
        st.markdown("#### 전체 일정 목록")

        # 필터
        col1, col2 = st.columns(2)
        with col1:
            filter_status = st.selectbox("상태", ["전체", "예정", "지난 일정"], key="filter_status")
        with col2:
            filter_airline = st.selectbox("항공사", ["전체"] + AIRLINES, key="filter_airline2")

        filtered_events = events.copy()
        if filter_status == "예정":
            filtered_events = [e for e in filtered_events if e.get("date", "") >= today_str]
        elif filter_status == "지난 일정":
            filtered_events = [e for e in filtered_events if e.get("date", "") < today_str]
        if filter_airline != "전체":
            filtered_events = [e for e in filtered_events if e.get("airline") == filter_airline]

        filtered_events = sorted(filtered_events, key=lambda x: x.get("date", ""))

        if not filtered_events:
            st.info("해당 조건의 일정이 없습니다.")
        else:
            for event in filtered_events:
                dday_str, diff = get_dday(event.get("date", ""))
                cat = EVENT_CATEGORIES.get(event.get("category", "기타"), EVENT_CATEGORIES["기타"])
                is_past = diff is not None and diff < 0
                opacity = "0.5" if is_past else "1"

                col_a, col_b, col_c = st.columns([4, 1, 0.5])
                with col_a:
                    airline_str = f"[{event.get('airline')}] " if event.get("airline") else ""
                    time_str = f" {event.get('time')}" if event.get("time") else ""
                    loc_str = f" | {event.get('location')}" if event.get("location") else ""
                    st.markdown(f"{cat['icon']} **{event.get('title', '')}**")
                    st.caption(f"{airline_str}{event.get('date', '')}{time_str}{loc_str}")
                with col_b:
                    color = "#dc3545" if diff is not None and 0 <= diff <= 3 else cat["color"]
                    st.markdown(f"<span style='color: {color}; font-weight: 700; font-size: 16px;'>{dday_str}</span>", unsafe_allow_html=True)
                with col_c:
                    if st.button("️", key=f"del_ev_{event.get('id', '')}", help="삭제"):
                        cal_data["events"] = [e for e in cal_data["events"] if e.get("id") != event.get("id")]
                        save_calendar(cal_data)
                        st.rerun()
                st.markdown("<hr style='margin: 5px 0; opacity: 0.2;'>", unsafe_allow_html=True)

        # 일정 초기화
        if events:
            st.markdown("---")
            with st.expander("️ 일정 전체 삭제"):
                st.warning("모든 일정이 삭제됩니다. 되돌릴 수 없습니다.")
                if st.button("모든 일정 삭제", type="primary", key="clear_events"):
                    cal_data["events"] = []
                    save_calendar(cal_data)
                    st.success("모든 일정이 삭제되었습니다.")
                    st.rerun()


# ========================================
# 탭4: 일일 체크리스트
# ========================================
with tab4:
    st.markdown("### 일일 체크리스트")

    # 날짜 선택
    selected_date = st.date_input("날짜 선택", value=date.today(), key="todo_date")
    sel_date_str = selected_date.strftime("%Y-%m-%d")

    # 해당 날짜 할 일 로드
    if sel_date_str not in cal_data["daily_todos"]:
        cal_data["daily_todos"][sel_date_str] = []
    day_todos = cal_data["daily_todos"][sel_date_str]

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"####  {selected_date.strftime('%m월 %d일')} 할 일")

        # 할 일 표시 및 체크
        if day_todos:
            done_count = 0
            for idx, todo in enumerate(day_todos):
                col_a, col_b, col_c = st.columns([0.3, 3, 0.3])
                with col_a:
                    checked = st.checkbox("", value=todo.get("done", False), key=f"todo_chk_{sel_date_str}_{idx}")
                    if checked != todo.get("done", False):
                        cal_data["daily_todos"][sel_date_str][idx]["done"] = checked
                        save_calendar(cal_data)
                        st.rerun()
                with col_b:
                    style = "text-decoration: line-through; opacity: 0.5;" if todo.get("done") else ""
                    st.markdown(f"<span style='{style}'>{todo.get('text', '')}</span>", unsafe_allow_html=True)
                with col_c:
                    if st.button("", key=f"del_todo_{sel_date_str}_{idx}", help="삭제"):
                        cal_data["daily_todos"][sel_date_str].pop(idx)
                        save_calendar(cal_data)
                        st.rerun()
                if todo.get("done"):
                    done_count += 1

            # 진행률
            progress = done_count / max(len(day_todos), 1)
            st.progress(progress, text=f"달성률: {done_count}/{len(day_todos)} ({int(progress * 100)}%)")
        else:
            st.info("오늘 할 일을 추가해보세요! 오른쪽에서 템플릿을 사용하거나 직접 입력하세요.")

        # 할 일 직접 추가
        st.markdown("---")
        with st.form(f"add_todo_form_{sel_date_str}"):
            new_todo_text = st.text_input("할 일 추가", placeholder="예: 모의면접 연습 30분", key=f"new_todo_{sel_date_str}")
            if st.form_submit_button("추가", use_container_width=True):
                if new_todo_text:
                    cal_data["daily_todos"][sel_date_str].append({"text": new_todo_text, "done": False})
                    save_calendar(cal_data)
                    st.success("할 일이 추가되었습니다!")
                    st.rerun()

    with col2:
        st.markdown("#### 빠른 추가 (템플릿)")

        for tmpl_name, tmpl_items in DAILY_TEMPLATES.items():
            with st.expander(f" {tmpl_name}"):
                if st.button(f"전체 추가", key=f"tmpl_add_{tmpl_name}_{sel_date_str}", use_container_width=True):
                    existing_texts = [t.get("text", "") for t in cal_data["daily_todos"][sel_date_str]]
                    added = 0
                    for item in tmpl_items:
                        if item not in existing_texts:
                            cal_data["daily_todos"][sel_date_str].append({"text": item, "done": False})
                            added += 1
                    if added > 0:
                        save_calendar(cal_data)
                        st.success(f"{added}개 항목 추가!")
                        st.rerun()
                    else:
                        st.info("이미 모두 추가됨")
                for item in tmpl_items:
                    st.caption(f"• {item}")

        # 반복 할 일 (어제 미완료 가져오기)
        st.markdown("---")
        yesterday_str = (selected_date - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_todos = cal_data["daily_todos"].get(yesterday_str, [])
        undone_yesterday = [t for t in yesterday_todos if not t.get("done")]

        if undone_yesterday:
            st.markdown("#### ️ 어제 미완료")
            if st.button("미완료 항목 가져오기", key="bring_yesterday", use_container_width=True):
                existing_texts = [t.get("text", "") for t in cal_data["daily_todos"][sel_date_str]]
                added = 0
                for t in undone_yesterday:
                    if t.get("text", "") not in existing_texts:
                        cal_data["daily_todos"][sel_date_str].append({"text": t["text"], "done": False})
                        added += 1
                if added > 0:
                    save_calendar(cal_data)
                    st.success(f"{added}개 항목을 오늘로 가져왔습니다!")
                    st.rerun()
            for t in undone_yesterday:
                st.caption(f"• {t.get('text', '')}")

    # 주간 달성률 그래프
    st.markdown("---")
    st.markdown("#### 최근 7일 달성률")

    week_stats = []
    for i in range(6, -1, -1):
        d = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
        d_todos = cal_data["daily_todos"].get(d, [])
        if d_todos:
            done = len([t for t in d_todos if t.get("done")])
            pct = int(done / len(d_todos) * 100)
        else:
            pct = 0
        week_stats.append({"날짜": d[-5:], "달성률": pct})

    if any(s["달성률"] > 0 for s in week_stats):
        import pandas as pd
        df = pd.DataFrame(week_stats)
        df = df.set_index("날짜")
        st.bar_chart(df, height=200)
    else:
        st.caption("할 일을 완료하면 여기에 달성률 그래프가 표시됩니다.")


# ========================================
# 탭5: 목표 설정
# ========================================
with tab5:
    st.markdown("### 목표 관리")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### 새 목표 추가")

        with st.form("add_goal_form"):
            goal_title = st.text_input("목표 *", placeholder="예: 이번 달 모의면접 10회")
            goal_deadline = st.date_input("목표 기한", value=date.today() + timedelta(days=30), key="goal_deadline")
            goal_type = st.selectbox("유형", ["면접 준비", "체력", "자소서", "영어", "자격증", "학습", "기타"], key="goal_type")

            if st.form_submit_button("목표 추가", type="primary", use_container_width=True):
                if goal_title:
                    new_goal = {
                        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                        "title": goal_title,
                        "deadline": goal_deadline.strftime("%Y-%m-%d"),
                        "type": goal_type,
                        "completed": False,
                        "created_at": datetime.now().isoformat()
                    }
                    cal_data["goals"].append(new_goal)
                    save_calendar(cal_data)
                    st.success("목표가 추가되었습니다!")
                    st.rerun()

    with col2:
        st.markdown("#### 진행 중인 목표")

        active_goals = [g for g in goals if not g.get("completed")]
        done_goals = [g for g in goals if g.get("completed")]

        if active_goals:
            for goal in active_goals:
                dday_str, diff = get_dday(goal.get("deadline", ""))
                is_overdue = diff is not None and diff < 0

                col_a, col_b, col_c = st.columns([0.3, 3, 0.5])
                with col_a:
                    if st.checkbox("", value=False, key=f"goal_chk_{goal.get('id')}"):
                        for g in cal_data["goals"]:
                            if g.get("id") == goal.get("id"):
                                g["completed"] = True
                                g["completed_at"] = datetime.now().isoformat()
                        save_calendar(cal_data)
                        st.balloons()
                        st.rerun()
                with col_b:
                    overdue_style = "color: #dc3545;" if is_overdue else ""
                    st.markdown(f"<span style='{overdue_style}'>{goal.get('title', '')}</span>", unsafe_allow_html=True)
                    st.caption(f"{goal.get('type', '')} | 기한: {goal.get('deadline', '')} ({dday_str})")
                with col_c:
                    if st.button("️", key=f"del_goal_{goal.get('id')}"):
                        cal_data["goals"] = [g for g in cal_data["goals"] if g.get("id") != goal.get("id")]
                        save_calendar(cal_data)
                        st.rerun()
        else:
            st.info("진행 중인 목표가 없습니다. 새 목표를 추가해보세요!")

        # 달성 통계
        st.markdown("---")
        total = len(goals)
        completed = len(done_goals)
        if total > 0:
            progress = completed / total
            st.progress(progress, text=f"전체 달성률: {completed}/{total} ({int(progress*100)}%)")

        # 완료된 목표
        if done_goals:
            with st.expander(f" 달성 완료 ({len(done_goals)}개)"):
                for g in done_goals:
                    st.markdown(f"~~{g.get('title', '')}~~ ({g.get('type', '')})")


# ========================================
# 탭6: D-Day 맞춤 가이드
# ========================================
with tab6:
    st.markdown("### D-Day 맞춤 가이드")
    st.info("다가오는 일정에 맞춰 지금 해야 할 일을 자동으로 안내합니다!")

    # 다가오는 이벤트 중 가이드 대상 찾기
    guide_events = []
    for event in events:
        dday_str, diff = get_dday(event.get("date", ""))
        if diff is not None and 0 <= diff <= 30:
            event["_dday"] = dday_str
            event["_diff"] = diff
            guide_events.append(event)

    guide_events = sorted(guide_events, key=lambda x: x.get("_diff", 999))

    if guide_events:
        for event in guide_events[:5]:
            cat = EVENT_CATEGORIES.get(event.get("category", "기타"), EVENT_CATEGORIES["기타"])
            diff = event["_diff"]

            # 가이드 유형 결정
            if "면접" in event.get("category", ""):
                guide_type = "면접"
            elif "서류" in event.get("category", ""):
                guide_type = "서류"
            elif "체력" in event.get("category", "") or "수영" in event.get("category", ""):
                guide_type = "체력"
            else:
                guide_type = None

            # 해당 가이드 찾기
            matched_guide = None
            if guide_type and guide_type in DDAY_GUIDES:
                guides = DDAY_GUIDES[guide_type]
                # 가장 적합한 가이드 선택 (diff 이하 중 가장 큰 값)
                applicable = [d for d in sorted(guides.keys(), reverse=True) if d >= diff]
                if applicable:
                    matched_guide = guides[applicable[-1]]

            # 이벤트 헤더
            urgency_color = "#dc3545" if diff <= 3 else "#f59e0b" if diff <= 7 else "#3b82f6"
            st.markdown(f"""
            <div style="background: {urgency_color}10; border: 2px solid {urgency_color}; border-radius: 14px; padding: 16px; margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 20px;">{cat['icon']}</span>
                        <strong style="font-size: 16px; margin-left: 8px;">{event.get('title', '')}</strong>
                        <span style="color: #666; margin-left: 10px;">{event.get('date', '')}</span>
                    </div>
                    <div style="font-size: 24px; font-weight: 800; color: {urgency_color};">{event['_dday']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if matched_guide:
                st.markdown(f"**{matched_guide['title']}**")
                for task in matched_guide["tasks"]:
                    st.checkbox(task, key=f"guide_{event.get('id', '')}_{task[:10]}")
            else:
                # 일반 가이드
                st.markdown("**지금 해야 할 일:**")
                if diff <= 1:
                    general_tasks = ["준비물 최종 확인", "충분한 수면", "일정 재확인", "교통편 확인"]
                elif diff <= 7:
                    general_tasks = ["세부 일정 확인", "필요 서류 준비", "리허설/연습", "컨디션 관리"]
                else:
                    general_tasks = ["일정 인지하기", "준비 계획 수립", "필요사항 미리 확인"]

                for task in general_tasks:
                    st.checkbox(task, key=f"gen_guide_{event.get('id', '')}_{task[:8]}")

            st.markdown("")
    else:
        st.markdown("#### 30일 내 예정된 일정이 없습니다")
        st.markdown("일정을 등록하면 남은 기간에 맞는 맞춤 가이드를 제공합니다.")

        # 일반 가이드 참고용 표시
        st.markdown("---")
        st.markdown("#### 가이드 참고 (면접 기준)")

        for days, guide in sorted(DDAY_GUIDES["면접"].items(), reverse=True):
            with st.expander(f"{'' if days > 7 else '️' if days > 1 else ''} {guide['title']}"):
                for task in guide["tasks"]:
                    st.markdown(f"- {task}")

    # 꿀팁
    st.markdown("---")
    st.markdown("#### 면접 준비 핵심 팁")

    tips_cols = st.columns(3)
    with tips_cols[0]:
        st.markdown("""
        ** D-30~D-14**
        - 자소서 기반 예상질문 준비
        - 모의면접 주 2회 이상
        - 항공사 뉴스 매일 체크
        - 체력/수영 훈련 병행
        """)
    with tips_cols[1]:
        st.markdown("""
        ** D-7~D-3**
        - 면접 복장 리허설
        - 면접장 위치/교통 확인
        - 1분 자기소개 자연스럽게
        - 수면 패턴 규칙적으로
        """)
    with tips_cols[2]:
        st.markdown("""
        ** D-1~당일**
        - 준비물 전날 세팅
        - 알람 2개 이상 설정
        - 30분 전 도착 목표
        - 심호흡 + 미소 + 자신감!
        """)

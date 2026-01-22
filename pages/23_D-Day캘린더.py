# pages/23_D데이캘린더.py
# D-Day 캘린더 및 목표 관리

import streamlit as st
import os
import json
from datetime import datetime, date, timedelta

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AIRLINES
from auth_utils import check_tester_password

st.set_page_config(
    page_title="D-Day 캘린더",
    page_icon="📅",
    layout="wide"
)

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="D-Day 캘린더")
except ImportError:
    pass


check_tester_password()

# ----------------------------
# 데이터
# ----------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CALENDAR_FILE = os.path.join(DATA_DIR, "my_calendar.json")


def load_calendar():
    if os.path.exists(CALENDAR_FILE):
        try:
            with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"events": [], "goals": []}


def save_calendar(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_dday(target_date_str):
    """D-Day 계산"""
    try:
        target = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        diff = (target - date.today()).days
        if diff > 0:
            return f"D-{diff}", diff
        elif diff == 0:
            return "D-Day", 0
        else:
            return f"D+{abs(diff)}", diff
    except:
        return "-", None


# 이벤트 카테고리
EVENT_CATEGORIES = {
    "서류 접수": {"icon": "📝", "color": "#3b82f6"},
    "서류 마감": {"icon": "⏰", "color": "#ef4444"},
    "면접": {"icon": "🎤", "color": "#8b5cf6"},
    "체력 테스트": {"icon": "💪", "color": "#10b981"},
    "결과 발표": {"icon": "📢", "color": "#f59e0b"},
    "입사": {"icon": "✈️", "color": "#ec4899"},
    "기타": {"icon": "📌", "color": "#6b7280"},
}


# ----------------------------
# UI
# ----------------------------
st.title("📅 D-Day 캘린더")
st.caption("면접 일정과 목표를 관리하세요")

calendar_data = load_calendar()
events = calendar_data.get("events", [])
goals = calendar_data.get("goals", [])

# ========== 상단: D-Day 위젯 ==========
st.markdown("### 🎯 주요 D-Day")

# 가장 가까운 이벤트 3개
upcoming = []
for e in events:
    dday_str, diff = get_dday(e.get("date", ""))
    if diff is not None and diff >= 0:
        e["_dday"] = dday_str
        e["_diff"] = diff
        upcoming.append(e)

upcoming = sorted(upcoming, key=lambda x: x.get("_diff", 999))[:3]

if upcoming:
    cols = st.columns(len(upcoming))
    for i, event in enumerate(upcoming):
        cat = EVENT_CATEGORIES.get(event.get("category", "기타"), EVENT_CATEGORIES["기타"])
        with cols[i]:
            st.markdown(f"""
            <div style="background: {cat['color']}15; border: 2px solid {cat['color']}; border-radius: 12px; padding: 20px; text-align: center;">
                <div style="font-size: 32px;">{cat['icon']}</div>
                <div style="font-size: 28px; font-weight: 800; color: {cat['color']};">{event.get('_dday', '')}</div>
                <div style="font-weight: 600; margin-top: 5px;">{event.get('title', '')}</div>
                <div style="font-size: 12px; color: #666;">{event.get('airline', '')} | {event.get('date', '')}</div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("등록된 일정이 없습니다. 아래에서 일정을 추가해보세요!")

st.markdown("---")

# 탭 구성
tab1, tab2, tab3 = st.tabs(["📋 일정 관리", "🎯 목표 설정", "📊 타임라인"])

# ========== 탭1: 일정 관리 ==========
with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("➕ 일정 추가")

        with st.form("add_event"):
            event_title = st.text_input("일정명 *", placeholder="예: 대한항공 1차 면접")
            event_airline = st.selectbox("항공사", ["선택 안함"] + AIRLINES)
            event_category = st.selectbox("카테고리", list(EVENT_CATEGORIES.keys()))
            event_date = st.date_input("날짜 *", value=date.today())
            event_time = st.time_input("시간 (선택)", value=None)
            event_location = st.text_input("장소", placeholder="예: 공항 근처 면접장")
            event_note = st.text_input("메모", placeholder="준비물, 주의사항 등")

            if st.form_submit_button("추가", type="primary", use_container_width=True):
                if not event_title:
                    st.error("일정명을 입력하세요!")
                else:
                    new_event = {
                        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                        "title": event_title,
                        "airline": event_airline if event_airline != "선택 안함" else "",
                        "category": event_category,
                        "date": event_date.strftime("%Y-%m-%d"),
                        "time": event_time.strftime("%H:%M") if event_time else "",
                        "location": event_location,
                        "note": event_note,
                        "created_at": datetime.now().isoformat()
                    }
                    calendar_data["events"].append(new_event)
                    save_calendar(calendar_data)
                    st.success("일정이 추가되었습니다!")
                    st.rerun()

    with col2:
        st.subheader("📋 등록된 일정")

        if not events:
            st.info("등록된 일정이 없습니다.")
        else:
            # 날짜순 정렬
            sorted_events = sorted(events, key=lambda x: x.get("date", ""))

            for event in sorted_events:
                dday_str, diff = get_dday(event.get("date", ""))
                cat = EVENT_CATEGORIES.get(event.get("category", "기타"), EVENT_CATEGORIES["기타"])

                # 지난 일정은 흐리게
                opacity = "0.5" if diff is not None and diff < 0 else "1"

                with st.container():
                    col_a, col_b, col_c = st.columns([0.5, 3, 0.5])

                    with col_a:
                        st.markdown(f"<span style='font-size: 24px;'>{cat['icon']}</span>", unsafe_allow_html=True)

                    with col_b:
                        st.markdown(f"**{event.get('title', '')}**")
                        info_text = f"{event.get('date', '')} {event.get('time', '')}"
                        if event.get("airline"):
                            info_text = f"{event.get('airline')} | " + info_text
                        if event.get("location"):
                            info_text += f" | {event.get('location')}"
                        st.caption(info_text)

                    with col_c:
                        st.markdown(f"<span style='color: {cat['color']}; font-weight: 700;'>{dday_str}</span>", unsafe_allow_html=True)
                        if st.button("🗑️", key=f"del_event_{event.get('id')}", help="삭제"):
                            calendar_data["events"] = [e for e in events if e.get("id") != event.get("id")]
                            save_calendar(calendar_data)
                            st.rerun()

                    st.markdown("---")


# ========== 탭2: 목표 설정 ==========
with tab2:
    st.subheader("🎯 나의 목표")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**새 목표 추가**")

        with st.form("add_goal"):
            goal_title = st.text_input("목표 *", placeholder="예: 이번 달 모의면접 10회")
            goal_deadline = st.date_input("목표 기한", value=date.today() + timedelta(days=30))
            goal_type = st.selectbox("유형", ["학습", "체력", "자격증", "기타"])

            if st.form_submit_button("추가", use_container_width=True):
                if goal_title:
                    new_goal = {
                        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                        "title": goal_title,
                        "deadline": goal_deadline.strftime("%Y-%m-%d"),
                        "type": goal_type,
                        "completed": False,
                        "created_at": datetime.now().isoformat()
                    }
                    calendar_data["goals"].append(new_goal)
                    save_calendar(calendar_data)
                    st.success("목표가 추가되었습니다!")
                    st.rerun()

    with col2:
        st.markdown("**진행 중인 목표**")

        if not goals:
            st.info("등록된 목표가 없습니다.")
        else:
            for goal in goals:
                dday_str, diff = get_dday(goal.get("deadline", ""))
                completed = goal.get("completed", False)

                col_a, col_b, col_c = st.columns([0.3, 2.5, 0.5])

                with col_a:
                    if st.checkbox("", value=completed, key=f"goal_check_{goal.get('id')}"):
                        if not completed:
                            for g in calendar_data["goals"]:
                                if g.get("id") == goal.get("id"):
                                    g["completed"] = True
                            save_calendar(calendar_data)
                            st.balloons()
                            st.rerun()

                with col_b:
                    style = "text-decoration: line-through; opacity: 0.5;" if completed else ""
                    st.markdown(f"<span style='{style}'>{goal.get('title', '')}</span>", unsafe_allow_html=True)
                    st.caption(f"{goal.get('type', '')} | 기한: {goal.get('deadline', '')} ({dday_str})")

                with col_c:
                    if st.button("🗑️", key=f"del_goal_{goal.get('id')}"):
                        calendar_data["goals"] = [g for g in goals if g.get("id") != goal.get("id")]
                        save_calendar(calendar_data)
                        st.rerun()

    # 통계
    st.markdown("---")
    completed_count = len([g for g in goals if g.get("completed")])
    total_count = len(goals)

    if total_count > 0:
        progress = completed_count / total_count
        st.progress(progress, text=f"목표 달성률: {completed_count}/{total_count} ({progress*100:.0f}%)")


# ========== 탭3: 타임라인 ==========
with tab3:
    st.subheader("📊 일정 타임라인")

    # 월별 보기
    all_events = sorted(events, key=lambda x: x.get("date", ""))

    if not all_events:
        st.info("등록된 일정이 없습니다.")
    else:
        # 월별로 그룹핑
        from collections import defaultdict
        monthly = defaultdict(list)

        for event in all_events:
            month = event.get("date", "")[:7]  # YYYY-MM
            monthly[month].append(event)

        for month, month_events in sorted(monthly.items()):
            year, mon = month.split("-")
            st.markdown(f"### 📅 {year}년 {int(mon)}월")

            for event in month_events:
                dday_str, diff = get_dday(event.get("date", ""))
                cat = EVENT_CATEGORIES.get(event.get("category", "기타"), EVENT_CATEGORIES["기타"])

                # 지난 일정/오늘/미래 구분
                if diff is not None:
                    if diff < 0:
                        bg_color = "#f3f4f6"
                    elif diff == 0:
                        bg_color = "#fef3c7"
                    else:
                        bg_color = "#ffffff"
                else:
                    bg_color = "#ffffff"

                st.markdown(f"""
                <div style="background: {bg_color}; border-left: 4px solid {cat['color']}; padding: 10px 15px; margin: 5px 0; border-radius: 0 8px 8px 0;">
                    <span style="font-size: 18px; margin-right: 8px;">{cat['icon']}</span>
                    <strong>{event.get('date', '')[-5:]}</strong>
                    <span style="margin: 0 10px;">|</span>
                    {event.get('title', '')}
                    <span style="color: {cat['color']}; font-weight: 600; float: right;">{dday_str}</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("")

# pages/3_진도관리.py
# 학습 진도 관리 - 쉽고 직관적인 UI

import os
import json
from datetime import datetime, timedelta
import streamlit as st

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 롤플레잉 시나리오 (ID -> 한국어 제목 변환용)
try:
    from roleplay_scenarios import SCENARIOS as RP_SCENARIOS
except ImportError:
    RP_SCENARIOS = {}


def get_scenario_title(scenario_id: str) -> str:
    """시나리오 ID를 한국어 제목으로 변환"""
    if scenario_id in RP_SCENARIOS:
        return RP_SCENARIOS[scenario_id].get("title", scenario_id)
    return scenario_id


st.set_page_config(
    page_title="진도 관리",
    page_icon="📅",
    layout="wide"
)

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="진도 관리")
except ImportError:
    pass


# =====================
# 데이터 저장/로드
# =====================

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "user_progress.json")


def load_progress_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "target_date": None,
        "target_airline": "",
        "daily_goals": [],
        "checklist_completed": {},
        "practice_history": [],
        "study_streak": 0,
        "last_study_date": None,
    }


def save_progress_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass


if "progress_data" not in st.session_state:
    st.session_state.progress_data = load_progress_data()


def get_data():
    return st.session_state.progress_data


def update_data(key, value):
    st.session_state.progress_data[key] = value
    save_progress_data(st.session_state.progress_data)


def toggle_check(item_id):
    data = get_data()
    if "checklist_completed" not in data:
        data["checklist_completed"] = {}
    current = data["checklist_completed"].get(item_id, False)
    data["checklist_completed"][item_id] = not current
    save_progress_data(data)


# =====================
# 체크리스트 데이터
# =====================

CHECKLIST = {
    "자소서": {
        "icon": "📝",
        "color": "#3b82f6",
        "items": [
            ("resume_intro", "인사/이름 작성"),
            ("resume_edu", "학력/전공"),
            ("resume_exp", "경력/경험"),
            ("resume_motive", "지원동기"),
            ("resume_strength", "강점/장점"),
            ("resume_closing", "마무리 멘트"),
            ("analysis_done", "자소서 분석 완료"),
            ("answer_q1", "Q1 답변 준비"),
            ("answer_q2", "Q2 답변 준비"),
            ("answer_q3", "Q3 답변 준비"),
        ]
    },
    "영어면접": {
        "icon": "🌍",
        "color": "#10b981",
        "items": [
            ("eng_intro", "영어 자기소개"),
            ("eng_intro_why", "지원동기 (영어)"),
            ("eng_intro_strength", "강점 (영어)"),
            ("eng_cat_service", "Service 질문 연습"),
            ("eng_cat_team", "Teamwork 질문 연습"),
            ("eng_cat_safety", "Safety 질문 연습"),
            ("eng_mock_1", "모의면접 1회"),
            ("eng_mock_2", "모의면접 2회"),
            ("eng_mock_3", "모의면접 3회"),
        ]
    },
    "롤플레잉": {
        "icon": "🎭",
        "color": "#f59e0b",
        "items": [
            ("rp_seat", "좌석 변경 요청"),
            ("rp_meal", "기내식 문제"),
            ("rp_delay", "지연/결항 안내"),
            ("rp_baggage", "수하물 문제"),
            ("rp_angry", "화난 승객 응대"),
            ("rp_drunk", "음주 승객 응대"),
            ("rp_medical", "응급환자 대응"),
            ("rp_turbulence", "난기류 대응"),
        ]
    },
    "면접준비": {
        "icon": "✨",
        "color": "#8b5cf6",
        "items": [
            ("prep_history", "회사 연혁 공부"),
            ("prep_value", "핵심가치/인재상"),
            ("prep_news", "최근 뉴스 확인"),
            ("prep_suit", "면접 복장 준비"),
            ("prep_hair", "헤어/메이크업"),
            ("prep_posture", "자세/표정 연습"),
            ("prep_documents", "서류 준비"),
            ("prep_location", "면접장 위치 확인"),
        ]
    },
}


def get_category_progress(cat_name):
    data = get_data()
    completed = data.get("checklist_completed", {})
    items = CHECKLIST.get(cat_name, {}).get("items", [])
    if not items:
        return 0
    done = sum(1 for item_id, _ in items if completed.get(item_id, False))
    return int((done / len(items)) * 100)


def get_total_progress():
    data = get_data()
    completed = data.get("checklist_completed", {})
    total = 0
    done = 0
    for cat_data in CHECKLIST.values():
        for item_id, _ in cat_data["items"]:
            total += 1
            if completed.get(item_id, False):
                done += 1
    return int((done / total) * 100) if total > 0 else 0


def calculate_dday(target_date_str):
    if not target_date_str:
        return None
    try:
        target = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        return (target - today).days
    except:
        return None


# =====================
# CSS 스타일
# =====================

st.markdown("""
<style>
/* 전체 레이아웃 */
.block-container { padding-top: 1rem !important; }

/* 대시보드 헤더 */
.dashboard-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 20px;
    padding: 25px 30px;
    color: white;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 15px;
}
.dday-box {
    text-align: center;
}
.dday-number {
    font-size: 3rem;
    font-weight: 800;
    line-height: 1;
}
.dday-label {
    font-size: 0.9rem;
    opacity: 0.9;
    margin-top: 5px;
}
.stats-row {
    display: flex;
    gap: 30px;
}
.stat-item {
    text-align: center;
}
.stat-value {
    font-size: 1.8rem;
    font-weight: 700;
}
.stat-label {
    font-size: 0.8rem;
    opacity: 0.8;
}

/* 진도율 원형 카드 */
.progress-cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
    margin-bottom: 25px;
}
.progress-card {
    background: white;
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    cursor: pointer;
    transition: all 0.2s;
    border: 2px solid transparent;
}
.progress-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.12);
}
.progress-card.active {
    border-color: #667eea;
}
.progress-ring {
    width: 80px;
    height: 80px;
    margin: 0 auto 10px;
    position: relative;
}
.progress-ring svg {
    transform: rotate(-90deg);
}
.progress-ring-bg {
    fill: none;
    stroke: #e5e7eb;
    stroke-width: 8;
}
.progress-ring-fill {
    fill: none;
    stroke-width: 8;
    stroke-linecap: round;
    transition: stroke-dashoffset 0.5s ease;
}
.progress-percent {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 1.2rem;
    font-weight: 700;
}
.progress-card-title {
    font-size: 1rem;
    font-weight: 600;
    color: #333;
}
.progress-card-icon {
    font-size: 1.5rem;
    margin-bottom: 5px;
}

/* 체크리스트 그리드 */
.checklist-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 12px;
    margin-top: 15px;
}
.check-item {
    background: white;
    border-radius: 12px;
    padding: 15px 18px;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    cursor: pointer;
    transition: all 0.15s;
    border: 2px solid #f0f0f0;
}
.check-item:hover {
    background: #f8fafc;
    border-color: #ddd;
}
.check-item.done {
    background: #f0fdf4;
    border-color: #86efac;
}
.check-item.done .check-text {
    text-decoration: line-through;
    color: #888;
}
.check-box {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    border: 2px solid #d1d5db;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
    transition: all 0.15s;
}
.check-item.done .check-box {
    background: #22c55e;
    border-color: #22c55e;
    color: white;
}
.check-text {
    font-size: 0.95rem;
    color: #333;
}

/* 할일 섹션 */
.todo-section {
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    margin-top: 20px;
}
.todo-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}
.todo-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #333;
}
.todo-item {
    background: #f8fafc;
    border-radius: 10px;
    padding: 12px 15px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.todo-item.done {
    background: #f0fdf4;
}

/* 퀵 액션 버튼 */
.quick-actions {
    display: flex;
    gap: 10px;
    margin-top: 20px;
    flex-wrap: wrap;
}
.quick-btn {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    padding: 12px 24px;
    border-radius: 25px;
    font-weight: 600;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    transition: all 0.2s;
}
.quick-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
}

/* 모바일 대응 */
@media (max-width: 768px) {
    .progress-cards { grid-template-columns: repeat(2, 1fr); }
    .dashboard-header { flex-direction: column; text-align: center; }
    .stats-row { justify-content: center; }
    .checklist-grid { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)


# =====================
# UI 시작
# =====================

data = get_data()

# ========== 대시보드 헤더 ==========
dday = calculate_dday(data.get("target_date"))
streak = data.get("study_streak", 0)
today_count = len([p for p in data.get("practice_history", []) if p.get("date") == datetime.now().strftime("%Y-%m-%d")])
total_progress = get_total_progress()

if dday is not None:
    if dday > 0:
        dday_text = f"D-{dday}"
    elif dday == 0:
        dday_text = "D-Day!"
    else:
        dday_text = f"D+{abs(dday)}"
else:
    dday_text = "미설정"

airline = data.get("target_airline", "")

st.markdown(f'''
<div class="dashboard-header">
    <div class="dday-box">
        <div class="dday-number">{dday_text}</div>
        <div class="dday-label">{airline if airline else "목표를 설정하세요"}</div>
    </div>
    <div class="stats-row">
        <div class="stat-item">
            <div class="stat-value">🔥 {streak}</div>
            <div class="stat-label">연속 학습일</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">📊 {total_progress}%</div>
            <div class="stat-label">전체 진도</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">✅ {today_count}</div>
            <div class="stat-label">오늘 연습</div>
        </div>
    </div>
</div>
''', unsafe_allow_html=True)

# ========== 목표 설정 (간단히) ==========
with st.expander("🎯 목표 설정 변경", expanded=not data.get("target_date")):
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        new_date = st.date_input(
            "면접일",
            value=datetime.strptime(data["target_date"], "%Y-%m-%d") if data.get("target_date") else datetime.now() + timedelta(days=30),
            label_visibility="collapsed"
        )
    with col2:
        from config import AIRLINES
        current_idx = AIRLINES.index(data["target_airline"]) if data.get("target_airline") in AIRLINES else 0
        new_airline = st.selectbox("항공사", AIRLINES, index=current_idx, label_visibility="collapsed")
    with col3:
        if st.button("저장", type="primary", use_container_width=True):
            update_data("target_date", new_date.strftime("%Y-%m-%d"))
            update_data("target_airline", new_airline)
            st.rerun()


# ========== 카테고리 선택 ==========
if "selected_category" not in st.session_state:
    st.session_state.selected_category = "자소서"


def render_progress_ring(percent, color):
    """원형 진도율 SVG 생성"""
    circumference = 2 * 3.14159 * 35  # radius = 35
    offset = circumference - (percent / 100) * circumference
    return f'''
    <div class="progress-ring">
        <svg width="80" height="80" viewBox="0 0 80 80">
            <circle class="progress-ring-bg" cx="40" cy="40" r="35"/>
            <circle class="progress-ring-fill" cx="40" cy="40" r="35"
                stroke="{color}"
                stroke-dasharray="{circumference}"
                stroke-dashoffset="{offset}"/>
        </svg>
        <div class="progress-percent" style="color: {color}">{percent}%</div>
    </div>
    '''


# 카테고리 카드 (클릭 가능)
st.markdown("### 📊 카테고리별 진도")

cols = st.columns(4)
for idx, (cat_name, cat_data) in enumerate(CHECKLIST.items()):
    progress = get_category_progress(cat_name)
    is_active = st.session_state.selected_category == cat_name

    with cols[idx]:
        # 카드 클릭 버튼
        if st.button(
            f"{cat_data['icon']} {cat_name}\n{progress}%",
            key=f"cat_btn_{cat_name}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state.selected_category = cat_name
            st.rerun()


# ========== 선택된 카테고리 체크리스트 ==========
st.markdown("---")
selected = st.session_state.selected_category
cat_data = CHECKLIST[selected]

st.markdown(f"### {cat_data['icon']} {selected} 체크리스트")
st.caption("클릭하면 완료/미완료가 토글됩니다")

# 체크리스트 항목들
completed = data.get("checklist_completed", {})

# 그리드로 표시
col_count = 2
items = cat_data["items"]
rows = [items[i:i+col_count] for i in range(0, len(items), col_count)]

for row in rows:
    cols = st.columns(col_count)
    for col_idx, (item_id, item_text) in enumerate(row):
        with cols[col_idx]:
            is_done = completed.get(item_id, False)

            # 체크 버튼
            btn_label = f"{'✅' if is_done else '⬜'} {item_text}"
            if st.button(
                btn_label,
                key=f"check_{item_id}",
                use_container_width=True,
                type="primary" if is_done else "secondary"
            ):
                toggle_check(item_id)
                st.rerun()


# ========== 오늘 할 일 (간단 버전) ==========
st.markdown("---")
st.markdown("### 📋 오늘 할 일")

# 할 일 추가
col1, col2 = st.columns([4, 1])
with col1:
    new_task = st.text_input("할 일 추가", placeholder="예: 영어 자기소개 연습", label_visibility="collapsed")
with col2:
    if st.button("➕ 추가", use_container_width=True):
        if new_task.strip():
            goals = data.get("daily_goals", [])
            goals.append({"task": new_task.strip(), "completed": False})
            update_data("daily_goals", goals)
            st.rerun()

# 할 일 목록
goals = data.get("daily_goals", [])
if goals:
    for i, goal in enumerate(goals):
        col1, col2, col3 = st.columns([0.5, 5, 0.5])

        with col1:
            is_done = goal.get("completed", False)
            if st.button("✅" if is_done else "⬜", key=f"todo_check_{i}"):
                goals[i]["completed"] = not is_done
                update_data("daily_goals", goals)
                st.rerun()

        with col2:
            if goal.get("completed"):
                st.markdown(f"~~{goal['task']}~~")
            else:
                st.write(goal["task"])

        with col3:
            if st.button("🗑️", key=f"todo_del_{i}"):
                goals.pop(i)
                update_data("daily_goals", goals)
                st.rerun()

    # 완료된 항목 정리
    done_count = sum(1 for g in goals if g.get("completed"))
    if done_count > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"완료: {done_count}/{len(goals)}")
        with col2:
            if st.button("정리", key="clear_done"):
                goals = [g for g in goals if not g.get("completed")]
                update_data("daily_goals", goals)
                st.rerun()
else:
    st.info("할 일을 추가하거나, 아래 퀵 추가 버튼을 사용하세요!")


# ========== 퀵 액션 ==========
st.markdown("---")
st.markdown("### ⚡ 바로가기")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.page_link("pages/4_모의면접.py", label="🎤 모의면접", use_container_width=True)
with col2:
    st.page_link("pages/1_롤플레잉.py", label="🎭 롤플레잉", use_container_width=True)
with col3:
    st.page_link("pages/2_영어면접.py", label="🌍 영어면접", use_container_width=True)
with col4:
    # 추천 할일 추가
    if st.button("📚 추천 할일", use_container_width=True):
        recommended = [
            "영어 자기소개 연습",
            "롤플레잉 1개 시나리오",
            "자소서 질문 답변 준비",
            "표정/자세 연습 10분"
        ]
        goals = data.get("daily_goals", [])
        for task in recommended:
            if not any(g["task"] == task for g in goals):
                goals.append({"task": task, "completed": False})
        update_data("daily_goals", goals)
        st.success("추천 할일이 추가되었습니다!")
        st.rerun()


# ========== 최근 기록 (롤플레잉 진도 포함) ==========
st.markdown("---")
with st.expander("📊 최근 학습 기록", expanded=False):
    # 롤플레잉 진도 파일에서 실제 기록 가져오기
    RP_PROGRESS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "roleplay_progress.json")

    all_records = []

    # 롤플레잉 실제 기록
    if os.path.exists(RP_PROGRESS_FILE):
        try:
            with open(RP_PROGRESS_FILE, "r", encoding="utf-8") as f:
                rp_data = json.load(f)
                for h in rp_data.get("history", []):
                    timestamp = h.get("timestamp", "")
                    date_str = timestamp[:10] if timestamp else ""
                    scenario_id = h.get("scenario_id", "")
                    all_records.append({
                        "date": date_str,
                        "type": "🎭 롤플레잉",
                        "detail": get_scenario_title(scenario_id),  # 한국어 제목으로 변환
                        "score": h.get("score", 0)
                    })
        except:
            pass

    # 정렬 (최신순)
    all_records.sort(key=lambda x: x.get("date", ""), reverse=True)

    if all_records:
        for i, record in enumerate(all_records[:15]):
            col1, col2 = st.columns([6, 1])
            with col1:
                score_text = f" ({record.get('score', '')}점)" if record.get('score') else ""
                st.write(f"• {record.get('date', '')} - {record.get('type', '')} : {record.get('detail', '')}{score_text}")
    else:
        st.info("아직 학습 기록이 없습니다. 롤플레잉이나 면접 연습을 시작해보세요!")

    # 기존 수동 기록 정리 버튼
    old_history = data.get("practice_history", [])
    if old_history:
        st.divider()
        st.caption("수동 입력 기록:")
        for record in old_history:
            st.caption(f"  • {record.get('date', '')} - {record.get('detail', '')}")
        if st.button("🗑️ 수동 기록 전체 삭제", key="clear_manual"):
            update_data("practice_history", [])
            st.rerun()

# 홈.py
# flyready_lab - 종합 대시보드 메인 페이지
# 기능: 학습 현황, D-Day, 맞춤 추천, 연속 학습일, 빠른 접근

import streamlit as st
import base64
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

from logging_config import get_logger

# 로거 설정
logger = get_logger(__name__)

# 로고 이미지 로드 (캐싱 적용)
@st.cache_resource
def get_logo_base64():
    """로고 이미지를 Base64로 인코딩 (영구 캐시)"""
    logo_path = Path(__file__).parent / "logo.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

LOGO_BASE64 = get_logo_base64()

st.set_page_config(
    page_title="flyready_lab",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 세션 시간 초기화
try:
    from motivation import init_session_time, check_and_show_motivation
    init_session_time()
    if check_and_show_motivation():
        st.rerun()
    if st.session_state.get("show_motivation_popup", False):
        from motivation import show_motivation_popup
        show_motivation_popup()
except ImportError:
    logger.debug("motivation 모듈 없음 - 동기부여 기능 비활성화")
except Exception as e:
    logger.warning(f"동기부여 모듈 초기화 실패: {e}")

# =====================
# 데이터 로드 함수
# =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

def load_json(filepath, default=None):
    """JSON 파일을 안전하게 로드"""
    if default is None:
        default = {}
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패 ({filepath}): {e}")
        except Exception as e:
            logger.error(f"파일 읽기 실패 ({filepath}): {e}")
    return default

@st.cache_data(ttl=60)  # 60초 캐시
def get_dashboard_data():
    """대시보드에 필요한 모든 데이터 수집 (60초 캐시)"""
    data = {}

    # D-Day 캘린더 데이터
    cal_data = load_json(os.path.join(DATA_DIR, "my_calendar.json"), {"events": [], "goals": [], "daily_todos": {}})
    data["events"] = cal_data.get("events", [])
    data["goals"] = cal_data.get("goals", [])
    data["daily_todos"] = cal_data.get("daily_todos", {})

    # 연습 점수 데이터
    data["scores"] = load_json(os.path.join(BASE_DIR, "user_scores.json"), {"scores": [], "detailed_scores": []})

    # 학습 진도 데이터
    data["progress"] = load_json(os.path.join(BASE_DIR, "user_progress.json"), {})

    # 기내방송 연습 데이터
    data["broadcast"] = load_json(os.path.join(DATA_DIR, "broadcast_practice.json"), {"records": []})

    # 롤플레잉 진도
    data["roleplay"] = load_json(os.path.join(BASE_DIR, "roleplay_progress.json"), {})

    return data

def get_upcoming_events(events, limit=3):
    """다가오는 일정 (D-Day 기준 정렬)"""
    today = datetime.now().date()
    upcoming = []
    for ev in events:
        try:
            date_str = ev.get("date", "")
            if not date_str:
                continue
            ev_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            days_left = (ev_date - today).days
            if days_left >= 0:
                upcoming.append({**ev, "days_left": days_left})
        except ValueError as e:
            logger.debug(f"날짜 파싱 실패: {ev.get('date', '')}")
            continue
    upcoming.sort(key=lambda x: x["days_left"])
    return upcoming[:limit]

def get_study_streak(daily_todos):
    """연속 학습일 계산"""
    today = datetime.now().date()
    streak = 0
    check_date = today

    while True:
        date_str = check_date.strftime("%Y-%m-%d")
        todos = daily_todos.get(date_str, [])
        if todos and any(t.get("done", False) for t in todos):
            streak += 1
            check_date -= timedelta(days=1)
        else:
            # 오늘은 아직 안 했어도 어제까지 연속이면 OK
            if check_date == today:
                check_date -= timedelta(days=1)
                continue
            break
    return streak

def get_weekly_practice_count(scores_data, broadcast_data):
    """이번 주 연습 횟수"""
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    count = 0

    # 점수 기록에서
    for score in scores_data.get("scores", []):
        try:
            score_date = datetime.strptime(score.get("date", "")[:10], "%Y-%m-%d").date()
            if score_date >= week_start:
                count += 1
        except (ValueError, TypeError, AttributeError) as e:
            logger.debug(f"점수 기록 날짜 파싱 실패: {e}")
            continue

    # 기내방송 기록에서
    for rec in broadcast_data.get("records", []):
        try:
            rec_date = datetime.strptime(rec.get("date", "")[:10], "%Y-%m-%d").date()
            if rec_date >= week_start:
                count += 1
        except (ValueError, TypeError, AttributeError) as e:
            logger.debug(f"기내방송 기록 날짜 파싱 실패: {e}")
            continue

    return count

def get_overall_progress(progress_data, roleplay_data):
    """전체 진도율 계산"""
    total_items = 0
    completed_items = 0

    # 학습 진도
    if isinstance(progress_data, dict):
        for key, val in progress_data.items():
            if isinstance(val, dict) and "total" in val and "completed" in val:
                total_items += val["total"]
                completed_items += val["completed"]
            elif isinstance(val, bool):
                total_items += 1
                if val:
                    completed_items += 1

    # 롤플레잉 진도
    if isinstance(roleplay_data, dict):
        for key, val in roleplay_data.items():
            if isinstance(val, dict) and val.get("completed", False):
                completed_items += 1
                total_items += 1
            elif isinstance(val, dict):
                total_items += 1

    if total_items == 0:
        return 0
    return int((completed_items / total_items) * 100)

def get_recent_avg_score(scores_data):
    """최근 5회 평균 점수"""
    all_scores = []
    for s in scores_data.get("scores", []):
        try:
            score_val = s.get("score", 0)
            if isinstance(score_val, (int, float)) and score_val > 0:
                all_scores.append(score_val)
        except (TypeError, KeyError) as e:
            logger.debug(f"점수 값 추출 실패: {e}")
            continue
    if not all_scores:
        return 0
    recent = all_scores[-5:]
    return int(sum(recent) / len(recent))

def get_recommendations(data):
    """맞춤 학습 추천 생성"""
    recommendations = []

    # 1. D-Day 임박 일정 기반 추천
    upcoming = get_upcoming_events(data["events"], 1)
    if upcoming:
        ev = upcoming[0]
        days = ev["days_left"]
        category = ev.get("category", "")
        if days <= 7:
            if "면접" in category:
                recommendations.append({
                    "icon": "🎤",
                    "text": f"D-{days} 면접 임박! 모의면접으로 최종 점검하세요",
                    "link": "/모의면접",
                    "urgency": "high"
                })
            elif "서류" in category:
                recommendations.append({
                    "icon": "📝",
                    "text": f"D-{days} 서류 마감! 자소서 최종 첨삭 받으세요",
                    "link": "/자소서첨삭",
                    "urgency": "high"
                })
            elif "체력" in category or "수영" in category:
                recommendations.append({
                    "icon": "🏋️",
                    "text": f"D-{days} 체력시험! 국민체력 가이드를 확인하세요",
                    "link": "/국민체력",
                    "urgency": "high"
                })

    # 2. 점수 기반 추천
    scores = data["scores"].get("scores", [])
    if scores:
        recent_scores = scores[-10:]
        low_categories = []
        for s in recent_scores:
            if s.get("score", 100) < 60:
                cat = s.get("category", "")
                if cat and cat not in low_categories:
                    low_categories.append(cat)
        if low_categories:
            recommendations.append({
                "icon": "📊",
                "text": f"약한 분야 재연습 추천: 최근 점수가 낮아요",
                "link": "/실전연습",
                "urgency": "medium"
            })

    # 3. 기내방송 연습 추천
    broadcast = data["broadcast"].get("records", [])
    if len(broadcast) == 0:
        recommendations.append({
            "icon": "🎙️",
            "text": "기내방송 연습을 시작해보세요! 15개 스크립트 준비됨",
            "link": "/기내방송연습",
            "urgency": "low"
        })
    elif len(broadcast) < 5:
        recommendations.append({
            "icon": "🎙️",
            "text": "기내방송 연습을 더 해보세요. 다양한 스크립트가 있어요",
            "link": "/기내방송연습",
            "urgency": "low"
        })

    # 4. 이미지메이킹 추천 (항상 유용)
    if not recommendations:
        recommendations.append({
            "icon": "👗",
            "text": "이미지메이킹 셀프체크로 면접 복장을 점검하세요",
            "link": "/이미지메이킹",
            "urgency": "low"
        })

    # 5. 퀴즈 추천
    if len(recommendations) < 3:
        recommendations.append({
            "icon": "✈️",
            "text": "항공 상식 퀴즈로 기본기를 다져보세요 (187문항)",
            "link": "/항공사퀴즈",
            "urgency": "low"
        })

    return recommendations[:3]

# =====================
# 데이터 로드
# =====================
dashboard_data = get_dashboard_data()
upcoming_events = get_upcoming_events(dashboard_data["events"])
study_streak = get_study_streak(dashboard_data["daily_todos"])
weekly_count = get_weekly_practice_count(dashboard_data["scores"], dashboard_data["broadcast"])
progress_pct = get_overall_progress(dashboard_data["progress"], dashboard_data["roleplay"])
recent_avg = get_recent_avg_score(dashboard_data["scores"])
recommendations = get_recommendations(dashboard_data)

# 오늘 할 일 달성률
today_str = datetime.now().strftime("%Y-%m-%d")
today_todos = dashboard_data["daily_todos"].get(today_str, [])
today_done = sum(1 for t in today_todos if t.get("done", False)) if today_todos else 0
today_total = len(today_todos) if today_todos else 0
today_pct = int((today_done / today_total) * 100) if today_total > 0 else 0

# 인사 메시지
hour = datetime.now().hour
if hour < 6:
    greeting = "새벽에도 열심히!"
elif hour < 12:
    greeting = "좋은 아침이에요!"
elif hour < 18:
    greeting = "오후도 힘내세요!"
else:
    greeting = "오늘도 수고했어요!"

# =====================
# CSS 스타일
# =====================
st.markdown("""
<style>
/* 기본 레이아웃 */
[data-testid="stSidebar"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
.block-container { padding: 0 !important; max-width: 100% !important; }
header[data-testid="stHeader"] { display: none; }
.stApp { background: #f8fafc; }

/* 헤더 */
.header {
    background: white;
    padding: 18px 60px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 15px rgba(0,0,0,0.04);
    position: sticky;
    top: 0;
    z-index: 100;
}
.logo {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 1.5rem;
    font-weight: 800;
    color: #1e3a5f;
    text-decoration: none;
}
.logo img { height: 40px; }
.header-greeting {
    font-size: 0.95rem;
    color: #64748b;
    font-weight: 500;
}

/* 히어로 - 콤팩트 */
.hero-compact {
    background: linear-gradient(135deg, #1e3a5f 0%, #3b82f6 100%);
    padding: 35px 60px;
    color: white;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 20px;
}
.hero-text h1 {
    font-size: 1.8rem;
    margin: 0 0 8px 0;
    font-weight: 800;
}
.hero-text p {
    font-size: 0.95rem;
    opacity: 0.85;
    margin: 0;
}
.hero-actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}
.hero-btn {
    display: inline-block;
    padding: 12px 28px;
    border-radius: 50px;
    font-weight: 700;
    text-decoration: none;
    transition: all 0.3s;
    font-size: 0.9rem;
}
.hero-btn.primary {
    background: white;
    color: #1e3a5f;
}
.hero-btn.primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}
.hero-btn.secondary {
    background: rgba(255,255,255,0.15);
    color: white;
    border: 2px solid rgba(255,255,255,0.3);
}

/* 메인 컨텐츠 */
.main-content {
    max-width: 1200px;
    margin: 30px auto;
    padding: 0 20px;
}

/* 대시보드 그리드 */
.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 18px;
    margin-bottom: 25px;
}
.stat-card {
    background: white;
    border-radius: 16px;
    padding: 22px;
    box-shadow: 0 2px 15px rgba(0,0,0,0.04);
    text-align: center;
    transition: all 0.3s;
    border: 2px solid transparent;
}
.stat-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.08);
}
.stat-card .stat-icon {
    font-size: 1.8rem;
    margin-bottom: 8px;
}
.stat-card .stat-value {
    font-size: 1.8rem;
    font-weight: 800;
    color: #1e3a5f;
    margin-bottom: 4px;
}
.stat-card .stat-label {
    font-size: 0.8rem;
    color: #64748b;
    font-weight: 500;
}
.stat-card.streak { border-left: 4px solid #f59e0b; }
.stat-card.weekly { border-left: 4px solid #3b82f6; }
.stat-card.progress { border-left: 4px solid #10b981; }
.stat-card.score { border-left: 4px solid #8b5cf6; }

/* D-Day + 추천 영역 */
.info-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 25px;
}

/* D-Day 카드 */
.dday-section {
    background: white;
    border-radius: 16px;
    padding: 25px;
    box-shadow: 0 2px 15px rgba(0,0,0,0.04);
}
.dday-title {
    font-size: 1rem;
    font-weight: 700;
    color: #1e3a5f;
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.dday-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 15px;
    background: #f8fafc;
    border-radius: 10px;
    margin-bottom: 8px;
    border-left: 4px solid #3b82f6;
}
.dday-item.urgent { border-left-color: #ef4444; background: #fef2f2; }
.dday-item.warning { border-left-color: #f59e0b; background: #fffbeb; }
.dday-item .event-name {
    font-size: 0.9rem;
    font-weight: 600;
    color: #334155;
}
.dday-item .event-date {
    font-size: 0.75rem;
    color: #64748b;
}
.dday-badge {
    font-size: 0.85rem;
    font-weight: 800;
    padding: 4px 12px;
    border-radius: 20px;
    color: white;
}
.dday-badge.red { background: #ef4444; }
.dday-badge.orange { background: #f59e0b; }
.dday-badge.blue { background: #3b82f6; }

/* 추천 카드 */
.recommend-section {
    background: white;
    border-radius: 16px;
    padding: 25px;
    box-shadow: 0 2px 15px rgba(0,0,0,0.04);
}
.recommend-title {
    font-size: 1rem;
    font-weight: 700;
    color: #1e3a5f;
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.recommend-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 15px;
    background: #f8fafc;
    border-radius: 10px;
    margin-bottom: 8px;
    border: 1px solid #e2e8f0;
}
.recommend-item.high { border-left: 4px solid #ef4444; }
.recommend-item.medium { border-left: 4px solid #f59e0b; }
.recommend-item.low { border-left: 4px solid #10b981; }
.recommend-icon { font-size: 1.5rem; }
.recommend-text {
    font-size: 0.85rem;
    font-weight: 500;
    color: #334155;
}

/* 오늘 할 일 프로그레스 */
.today-progress {
    background: white;
    border-radius: 16px;
    padding: 20px 25px;
    box-shadow: 0 2px 15px rgba(0,0,0,0.04);
    margin-bottom: 25px;
    display: flex;
    align-items: center;
    gap: 20px;
}
.today-label {
    font-size: 0.9rem;
    font-weight: 600;
    color: #334155;
    white-space: nowrap;
}
.progress-bar-container {
    flex: 1;
    height: 12px;
    background: #e2e8f0;
    border-radius: 6px;
    overflow: hidden;
}
.progress-bar-fill {
    height: 100%;
    border-radius: 6px;
    transition: width 0.5s ease;
}
.progress-pct {
    font-size: 0.9rem;
    font-weight: 700;
    color: #1e3a5f;
    white-space: nowrap;
}

/* 섹션 */
.section {
    background: white;
    border-radius: 20px;
    box-shadow: 0 4px 25px rgba(0,0,0,0.05);
    padding: 30px;
    margin-bottom: 25px;
}
.section-title {
    font-size: 1.1rem;
    color: #1e3a5f;
    margin-bottom: 20px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 10px;
}

/* 카드 그리드 */
.card-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
}
.card {
    background: linear-gradient(145deg, #f8fafc, #f1f5f9);
    border-radius: 14px;
    padding: 24px 18px;
    text-align: center;
    text-decoration: none;
    color: inherit;
    transition: all 0.3s;
    border: 2px solid transparent;
}
.card:hover {
    background: linear-gradient(145deg, #eff6ff, #dbeafe);
    border-color: #3b82f6;
    transform: translateY(-4px);
    box-shadow: 0 12px 30px rgba(59, 130, 246, 0.15);
}
.card .icon { font-size: 2.2rem; margin-bottom: 12px; }
.card .title { font-size: 0.9rem; font-weight: 700; color: #1e3a5f; margin-bottom: 6px; }
.card .desc { font-size: 0.78rem; color: #64748b; line-height: 1.4; }

/* 미니 카드 그리드 */
.mini-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
}
.mini-card {
    background: #f8fafc;
    border-radius: 12px;
    padding: 18px 12px;
    text-align: center;
    text-decoration: none;
    color: inherit;
    transition: all 0.25s;
    border: 1px solid #e2e8f0;
}
.mini-card:hover {
    background: #eff6ff;
    border-color: #93c5fd;
    transform: translateY(-3px);
}
.mini-card .icon { font-size: 1.6rem; margin-bottom: 8px; }
.mini-card .title { font-size: 0.82rem; font-weight: 600; color: #334155; }

/* 푸터 */
.footer {
    background: #1e3a5f;
    padding: 35px;
    text-align: center;
    color: rgba(255,255,255,0.7);
}
.footer p { margin: 5px 0; font-size: 0.85rem; }
.footer .brand {
    font-size: 1.1rem;
    font-weight: 700;
    color: white;
    margin-bottom: 8px;
}

/* 반응형 */
@media (max-width: 900px) {
    .dashboard-grid { grid-template-columns: repeat(2, 1fr); }
    .info-row { grid-template-columns: 1fr; }
    .card-grid { grid-template-columns: repeat(2, 1fr); }
    .mini-grid { grid-template-columns: repeat(3, 1fr); }
    .header { padding: 15px 20px; }
    .hero-compact { padding: 25px 20px; flex-direction: column; text-align: center; }
    .hero-text h1 { font-size: 1.4rem; }
    .today-progress { flex-wrap: wrap; }
}
@media (max-width: 500px) {
    .dashboard-grid { grid-template-columns: 1fr 1fr; }
    .card-grid { grid-template-columns: 1fr; }
    .mini-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
""", unsafe_allow_html=True)

# =====================
# 헤더
# =====================
if LOGO_BASE64:
    logo_html = f'<img src="data:image/png;base64,{LOGO_BASE64}" alt="flyready_lab">'
else:
    logo_html = '<span style="color: #3b82f6;">flyready</span><span style="color: #1e3a5f;">_lab</span>'

st.markdown(f'''
<div class="header">
    <a href="/" class="logo">{logo_html}</a>
    <div class="header-greeting">{greeting} 오늘도 한 걸음 더 가까이 ✈️</div>
</div>
''', unsafe_allow_html=True)

# =====================
# 히어로 (콤팩트)
# =====================
st.markdown('''
<div class="hero-compact">
    <div class="hero-text">
        <h1>✈️ AI와 함께하는 승무원 면접 준비</h1>
        <p>실전 모의면접 · 자소서 첨삭 · 기내 롤플레잉 · 체력/이미지 관리까지</p>
    </div>
    <div class="hero-actions">
        <a href="/모의면접" class="hero-btn primary">🎤 모의면접</a>
        <a href="/롤플레잉" class="hero-btn secondary">🎭 롤플레잉</a>
    </div>
</div>
''', unsafe_allow_html=True)

# =====================
# 메인 컨텐츠 시작
# =====================
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# =====================
# 대시보드 통계 카드
# =====================
streak_emoji = "🔥" if study_streak >= 3 else "📅"
score_color = "#10b981" if recent_avg >= 80 else ("#f59e0b" if recent_avg >= 60 else "#ef4444")

st.markdown(f'''
<div class="dashboard-grid">
    <div class="stat-card streak">
        <div class="stat-icon">{streak_emoji}</div>
        <div class="stat-value">{study_streak}일</div>
        <div class="stat-label">연속 학습일</div>
    </div>
    <div class="stat-card weekly">
        <div class="stat-icon">💪</div>
        <div class="stat-value">{weekly_count}회</div>
        <div class="stat-label">이번 주 연습</div>
    </div>
    <div class="stat-card progress">
        <div class="stat-icon">📈</div>
        <div class="stat-value">{progress_pct}%</div>
        <div class="stat-label">전체 진도율</div>
    </div>
    <div class="stat-card score">
        <div class="stat-icon">⭐</div>
        <div class="stat-value">{recent_avg if recent_avg > 0 else "-"}점</div>
        <div class="stat-label">최근 평균 점수</div>
    </div>
</div>
''', unsafe_allow_html=True)

# =====================
# 오늘 할 일 프로그레스
# =====================
if today_total > 0:
    bar_color = "#10b981" if today_pct >= 80 else ("#3b82f6" if today_pct >= 50 else "#f59e0b")
    st.markdown(f'''
    <div class="today-progress">
        <div class="today-label">📋 오늘 할 일</div>
        <div class="progress-bar-container">
            <div class="progress-bar-fill" style="width: {today_pct}%; background: {bar_color};"></div>
        </div>
        <div class="progress-pct">{today_done}/{today_total} ({today_pct}%)</div>
    </div>
    ''', unsafe_allow_html=True)

# =====================
# D-Day + 추천 영역
# =====================
# D-Day 카드 HTML
dday_items_html = ""
if upcoming_events:
    for ev in upcoming_events:
        days = ev["days_left"]
        if days <= 3:
            urgency_class = "urgent"
            badge_class = "red"
        elif days <= 7:
            urgency_class = "warning"
            badge_class = "orange"
        else:
            urgency_class = ""
            badge_class = "blue"

        dday_text = "D-Day" if days == 0 else f"D-{days}"
        title = ev.get("title", "일정")
        date_str = ev.get("date", "")

        dday_items_html += f'<div class="dday-item {urgency_class}"><div><div class="event-name">{title}</div><div class="event-date">{date_str}</div></div><div class="dday-badge {badge_class}">{dday_text}</div></div>'
else:
    dday_items_html = '<div style="text-align:center;padding:20px;color:#94a3b8;font-size:0.85rem;">등록된 일정이 없습니다<br><span style="color:#3b82f6;">D-Day캘린더에서 추가하세요</span></div>'

# 추천 카드 HTML
recommend_items_html = ""
for rec in recommendations:
    recommend_items_html += f'<div class="recommend-item {rec["urgency"]}"><span class="recommend-icon">{rec["icon"]}</span><span class="recommend-text">{rec["text"]}</span></div>'

col_dday, col_rec = st.columns(2)

with col_dday:
    st.markdown(f'<div class="dday-section"><div class="dday-title">📅 다가오는 일정</div>{dday_items_html}</div>', unsafe_allow_html=True)

with col_rec:
    st.markdown(f'<div class="recommend-section"><div class="recommend-title">💡 오늘의 추천</div>{recommend_items_html}</div>', unsafe_allow_html=True)

# =====================
# 섹션 1: 면접 연습
# =====================
st.markdown('''
<div class="section">
    <div class="section-title"><span class="icon">🎤</span> 면접 연습</div>
    <div class="card-grid">
        <a href="/모의면접" class="card">
            <div class="icon">🎤</div>
            <div class="title">AI 모의면접</div>
            <div class="desc">실전처럼 연습하고<br>즉시 피드백 받기</div>
        </a>
        <a href="/롤플레잉" class="card">
            <div class="icon">🎭</div>
            <div class="title">기내 롤플레잉</div>
            <div class="desc">실제 기내 상황<br>시뮬레이션</div>
        </a>
        <a href="/영어면접" class="card">
            <div class="icon">🌐</div>
            <div class="title">영어면접</div>
            <div class="desc">영어 질문<br>답변 연습</div>
        </a>
        <a href="/토론면접" class="card">
            <div class="icon">💬</div>
            <div class="title">토론면접</div>
            <div class="desc">그룹 토론<br>시뮬레이션</div>
        </a>
    </div>
</div>
''', unsafe_allow_html=True)

# =====================
# 섹션 2: 준비 도구
# =====================
st.markdown('''
<div class="section">
    <div class="section-title"><span class="icon">📚</span> 준비 도구</div>
    <div class="card-grid">
        <a href="/자소서첨삭" class="card">
            <div class="icon">📝</div>
            <div class="title">자소서 AI 첨삭</div>
            <div class="desc">AI가 자소서<br>피드백 제공</div>
        </a>
        <a href="/실전연습" class="card">
            <div class="icon">🎯</div>
            <div class="title">실전 연습</div>
            <div class="desc">영상/음성 종합<br>분석 연습</div>
        </a>
        <a href="/이미지메이킹" class="card">
            <div class="icon">👗</div>
            <div class="title">이미지메이킹</div>
            <div class="desc">메이크업/복장<br>가이드</div>
        </a>
        <a href="/기내방송연습" class="card">
            <div class="icon">🎙️</div>
            <div class="title">기내방송 연습</div>
            <div class="desc">한국어/영어<br>15개 스크립트</div>
        </a>
    </div>
</div>
''', unsafe_allow_html=True)

# =====================
# 섹션 3: 학습/정보
# =====================
st.markdown('''
<div class="section">
    <div class="section-title"><span class="icon">🎯</span> 학습 · 정보</div>
    <div class="mini-grid">
        <a href="/항공사퀴즈" class="mini-card">
            <div class="icon">✈️</div>
            <div class="title">항공 상식 퀴즈</div>
        </a>
        <a href="/면접꿀팁" class="mini-card">
            <div class="icon">💡</div>
            <div class="title">면접 꿀팁</div>
        </a>
        <a href="/항공사가이드" class="mini-card">
            <div class="icon">🏢</div>
            <div class="title">항공사 가이드</div>
        </a>
        <a href="/국민체력" class="mini-card">
            <div class="icon">🏋️</div>
            <div class="title">국민체력/수영</div>
        </a>
        <a href="/기업분석" class="mini-card">
            <div class="icon">📊</div>
            <div class="title">기업 분석</div>
        </a>
    </div>
</div>
''', unsafe_allow_html=True)

# =====================
# 섹션 4: 학습 관리
# =====================
st.markdown('''
<div class="section">
    <div class="section-title"><span class="icon">📋</span> 학습 관리</div>
    <div class="mini-grid">
        <a href="/진도관리" class="mini-card">
            <div class="icon">📈</div>
            <div class="title">진도 관리</div>
        </a>
        <a href="/성장그래프" class="mini-card">
            <div class="icon">📉</div>
            <div class="title">성장 그래프</div>
        </a>
        <a href="/채용알림" class="mini-card">
            <div class="icon">📢</div>
            <div class="title">채용 알림</div>
        </a>
        <a href="/합격자DB" class="mini-card">
            <div class="icon">🏆</div>
            <div class="title">합격자 DB</div>
        </a>
        <a href="/D-Day캘린더" class="mini-card">
            <div class="icon">📅</div>
            <div class="title">D-Day 캘린더</div>
        </a>
    </div>
</div>
''', unsafe_allow_html=True)

# 메인 컨텐츠 종료
st.markdown('</div>', unsafe_allow_html=True)

# =====================
# 푸터
# =====================
st.markdown('''
<div class="footer">
    <div class="brand">✈️ flyready_lab</div>
    <p>당신의 꿈을 응원합니다</p>
    <p style="margin-top: 12px; font-size: 0.75rem; opacity: 0.5;">© 2026 flyready_lab. All rights reserved.</p>
</div>
''', unsafe_allow_html=True)

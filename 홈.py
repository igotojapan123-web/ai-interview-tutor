# 홈.py
# FlyReady Lab - 종합 대시보드 메인 페이지
# 전문적인 디자인 (이모지 없는 버전)
# A-G 개선사항 통합 버전

import streamlit as st
import base64
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Sentry 에러 모니터링 초기화
try:
    import sentry_sdk
    from dotenv import load_dotenv
    load_dotenv()

    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=0.1,
            send_default_pii=False,
        )
except ImportError:
    pass

from logging_config import get_logger

# A-G 개선사항 통합 모듈 - 안정성 문제로 비활성화
ENHANCEMENT_AVAILABLE = False
MODULES_AVAILABLE = {}

# 로거 설정
logger = get_logger(__name__)

# 공통 유틸리티 import
try:
    from safe_utils import safe_divide, safe_percentage, safe_average
except ImportError:
    pass

try:
    from sidebar_common import render_sidebar
except ImportError:
    pass

try:
    from auth_utils import is_authenticated, require_auth
except ImportError:
    pass

# 디자인 시스템 import
try:
    from ui_config import COLORS, get_base_css, MAIN_PAGE_CARDS
    UI_CONFIG_AVAILABLE = True
except ImportError:
    UI_CONFIG_AVAILABLE = False

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
    page_title="FlyReady Lab",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 비밀번호 인증 (Beta 웹)
from auth_utils import require_auth
require_auth("FlyReady Lab - Beta")

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

@st.cache_data(ttl=60)
def get_dashboard_data():
    """대시보드에 필요한 모든 데이터 수집 (60초 캐시)"""
    data = {}
    cal_data = load_json(os.path.join(DATA_DIR, "my_calendar.json"), {"events": [], "goals": [], "daily_todos": {}})
    data["events"] = cal_data.get("events", [])
    data["goals"] = cal_data.get("goals", [])
    data["daily_todos"] = cal_data.get("daily_todos", {})
    data["scores"] = load_json(os.path.join(BASE_DIR, "user_scores.json"), {"scores": [], "detailed_scores": []})
    data["progress"] = load_json(os.path.join(BASE_DIR, "user_progress.json"), {})
    data["broadcast"] = load_json(os.path.join(DATA_DIR, "broadcast_practice.json"), {"records": []})
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
        except ValueError:
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
    for score in scores_data.get("scores", []):
        try:
            score_date = datetime.strptime(score.get("date", "")[:10], "%Y-%m-%d").date()
            if score_date >= week_start:
                count += 1
        except (ValueError, TypeError, AttributeError):
            continue
    for rec in broadcast_data.get("records", []):
        try:
            rec_date = datetime.strptime(rec.get("date", "")[:10], "%Y-%m-%d").date()
            if rec_date >= week_start:
                count += 1
        except (ValueError, TypeError, AttributeError):
            continue
    return count

def get_overall_progress(progress_data, roleplay_data):
    """전체 진도율 계산"""
    total_items = 0
    completed_items = 0
    if isinstance(progress_data, dict):
        for key, val in progress_data.items():
            if isinstance(val, dict) and "total" in val and "completed" in val:
                total_items += val["total"]
                completed_items += val["completed"]
            elif isinstance(val, bool):
                total_items += 1
                if val:
                    completed_items += 1
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
        except (TypeError, KeyError):
            continue
    if not all_scores:
        return 0
    recent = all_scores[-5:]
    return int(sum(recent) / len(recent))

def get_recommendations(data):
    """맞춤 학습 추천 생성"""
    recommendations = []
    upcoming = get_upcoming_events(data["events"], 1)
    if upcoming:
        ev = upcoming[0]
        days = ev["days_left"]
        category = ev.get("category", "")
        if days <= 7:
            if "면접" in category:
                recommendations.append({
                    "text": f"D-{days} 면접 임박! 모의면접으로 최종 점검하세요",
                    "link": "/모의면접",
                    "urgency": "high"
                })
            elif "서류" in category:
                recommendations.append({
                    "text": f"D-{days} 서류 마감! 자소서 최종 첨삭 받으세요",
                    "link": "/자소서첨삭",
                    "urgency": "high"
                })
            elif "체력" in category or "수영" in category:
                recommendations.append({
                    "text": f"D-{days} 체력시험! 국민체력 가이드를 확인하세요",
                    "link": "/국민체력",
                    "urgency": "high"
                })
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
                "text": "약한 분야 재연습 추천: 최근 점수가 낮아요",
                "link": "/모의면접",
                "urgency": "medium"
            })
    broadcast = data["broadcast"].get("records", [])
    if len(broadcast) == 0:
        recommendations.append({
            "text": "기내방송 연습을 시작해보세요! 15개 스크립트 준비됨",
            "link": "/기내방송연습",
            "urgency": "low"
        })
    elif len(broadcast) < 5:
        recommendations.append({
            "text": "기내방송 연습을 더 해보세요. 다양한 스크립트가 있어요",
            "link": "/기내방송연습",
            "urgency": "low"
        })
    if not recommendations:
        recommendations.append({
            "text": "이미지메이킹 셀프체크로 면접 복장을 점검하세요",
            "link": "/이미지메이킹",
            "urgency": "low"
        })
    if len(recommendations) < 3:
        recommendations.append({
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

today_str = datetime.now().strftime("%Y-%m-%d")
today_todos = dashboard_data["daily_todos"].get(today_str, [])
today_done = sum(1 for t in today_todos if t.get("done", False)) if today_todos else 0
today_total = len(today_todos) if today_todos else 0
today_pct = int((today_done / today_total) * 100) if today_total > 0 else 0

hour = datetime.now().hour
if hour < 6:
    greeting = "새벽에도 열심히!"
elif hour < 12:
    greeting = "좋은 아침이에요"
elif hour < 18:
    greeting = "오후도 힘내세요"
else:
    greeting = "오늘도 수고했어요"

# =====================
# CSS 스타일
# =====================
if UI_CONFIG_AVAILABLE:
    st.markdown(get_base_css(), unsafe_allow_html=True)
else:
    # 폴백 CSS
    st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { display: none; }
    .stApp { background: #f8fafc; }
    </style>
    """, unsafe_allow_html=True)

# 추가 스타일 + 링크 동작 수정
st.markdown("""
<base target="_self">
<script>
document.addEventListener('click', function(e) {
    var target = e.target;
    while (target && target.tagName !== 'A') {
        target = target.parentNode;
    }
    if (target && target.tagName === 'A') {
        var href = target.getAttribute('href');
        if (href && href.startsWith('/') && !href.startsWith('//')) {
            e.preventDefault();
            window.location.href = href;
        }
    }
});
</script>

<style>
/* 커스텀 스타일 추가 */
.fr-header {
    background: white;
    padding: 16px 48px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    position: sticky;
    top: 0;
    z-index: 100;
}
.fr-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 1.25rem;
    font-weight: 800;
    color: #1e3a5f;
    text-decoration: none;
}
.fr-logo img { height: 36px; }
.fr-header-text {
    font-size: 0.9rem;
    color: #64748b;
    font-weight: 500;
}
.fr-hero {
    background: linear-gradient(135deg, #1e3a5f 0%, #3b82f6 100%);
    padding: 40px 48px;
    color: white;
}
.fr-hero h1 {
    font-size: 1.75rem;
    font-weight: 800;
    margin: 0 0 8px 0;
}
.fr-hero p {
    font-size: 0.95rem;
    opacity: 0.85;
    margin: 0;
}
.fr-hero-actions {
    display: flex;
    gap: 12px;
    margin-top: 20px;
}
.fr-btn {
    display: inline-block;
    padding: 12px 28px;
    border-radius: 8px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s;
    font-size: 0.9rem;
}
.fr-btn-primary {
    background: white;
    color: #1e3a5f;
}
.fr-btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.fr-btn-secondary {
    background: rgba(255,255,255,0.95);
    color: #1e3a5f;
    border: 2px solid white;
    font-weight: 700;
}
.fr-btn-secondary:hover {
    background: white;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.fr-main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 32px 24px;
}
.fr-stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}
.fr-stat-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    border-left: 4px solid #3b82f6;
    transition: all 0.2s;
}
.fr-stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
.fr-stat-card.streak { border-left-color: #f59e0b; }
.fr-stat-card.weekly { border-left-color: #3b82f6; }
.fr-stat-card.progress { border-left-color: #10b981; }
.fr-stat-card.score { border-left-color: #8b5cf6; }
.fr-stat-value {
    font-size: 1.75rem;
    font-weight: 800;
    color: #1e3a5f;
    margin-bottom: 4px;
}
.fr-stat-label {
    font-size: 0.8rem;
    color: #64748b;
    font-weight: 500;
}
.fr-section {
    background: white;
    border-radius: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    padding: 28px;
    margin-bottom: 24px;
}
.fr-section-title {
    font-size: 1.1rem;
    color: #1e3a5f;
    margin-bottom: 20px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 8px;
}
.fr-section-title::before {
    content: '';
    width: 4px;
    height: 20px;
    background: #3b82f6;
    border-radius: 2px;
}
.fr-card-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
}
.fr-card {
    background: #f8fafc;
    border-radius: 12px;
    padding: 24px 20px;
    text-align: center;
    text-decoration: none;
    color: inherit;
    transition: all 0.2s;
    border: 1px solid transparent;
}
.fr-card:hover {
    background: #eff6ff;
    border-color: #3b82f6;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}
.fr-card-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #1e3a5f;
    margin-bottom: 6px;
}
.fr-card-desc {
    font-size: 0.8rem;
    color: #64748b;
    line-height: 1.4;
}
.fr-mini-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
}
.fr-mini-card {
    background: #f8fafc;
    border-radius: 10px;
    padding: 16px 12px;
    text-align: center;
    text-decoration: none;
    color: inherit;
    transition: all 0.2s;
    border: 1px solid #e2e8f0;
}
.fr-mini-card:hover {
    background: #eff6ff;
    border-color: #93c5fd;
    transform: translateY(-2px);
}
.fr-mini-card-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: #334155;
}
.fr-info-box {
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.fr-info-title {
    font-size: 1rem;
    font-weight: 700;
    color: #1e3a5f;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e2e8f0;
}
.fr-dday-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: #f8fafc;
    border-radius: 8px;
    margin-bottom: 8px;
    border-left: 3px solid #3b82f6;
}
.fr-dday-item.urgent { border-left-color: #ef4444; background: #fef2f2; }
.fr-dday-item.warning { border-left-color: #f59e0b; background: #fffbeb; }
.fr-dday-name {
    font-size: 0.9rem;
    font-weight: 600;
    color: #334155;
}
.fr-dday-date {
    font-size: 0.75rem;
    color: #64748b;
}
.fr-dday-badge {
    font-size: 0.8rem;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 16px;
    color: white;
}
.fr-dday-badge.red { background: #ef4444; }
.fr-dday-badge.orange { background: #f59e0b; }
.fr-dday-badge.blue { background: #3b82f6; }
.fr-recommend-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: #f8fafc;
    border-radius: 8px;
    margin-bottom: 8px;
    border-left: 3px solid #10b981;
}
.fr-recommend-item.high { border-left-color: #ef4444; }
.fr-recommend-item.medium { border-left-color: #f59e0b; }
.fr-recommend-text {
    font-size: 0.85rem;
    font-weight: 500;
    color: #334155;
}
.fr-today-progress {
    background: white;
    border-radius: 12px;
    padding: 16px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 20px;
}
.fr-today-label {
    font-size: 0.9rem;
    font-weight: 600;
    color: #334155;
    white-space: nowrap;
}
.fr-progress-bar-container {
    flex: 1;
    height: 10px;
    background: #e2e8f0;
    border-radius: 5px;
    overflow: hidden;
}
.fr-progress-bar-fill {
    height: 100%;
    border-radius: 5px;
    transition: width 0.5s ease;
}
.fr-progress-pct {
    font-size: 0.9rem;
    font-weight: 700;
    color: #1e3a5f;
    white-space: nowrap;
}
.fr-footer {
    background: #1e3a5f;
    padding: 32px;
    text-align: center;
    color: rgba(255,255,255,0.7);
    margin-top: 48px;
}
.fr-footer-brand {
    font-size: 1.1rem;
    font-weight: 700;
    color: white;
    margin-bottom: 8px;
}
.fr-footer p { margin: 4px 0; font-size: 0.85rem; }
@media (max-width: 900px) {
    .fr-stats-grid { grid-template-columns: repeat(2, 1fr); }
    .fr-card-grid { grid-template-columns: repeat(2, 1fr); }
    .fr-mini-grid { grid-template-columns: repeat(3, 1fr); }
    .fr-header { padding: 12px 20px; }
    .fr-hero { padding: 28px 20px; }
    .fr-hero h1 { font-size: 1.4rem; }
    .fr-today-progress { flex-wrap: wrap; }
}
@media (max-width: 500px) {
    .fr-stats-grid { grid-template-columns: 1fr 1fr; }
    .fr-card-grid { grid-template-columns: 1fr; }
    .fr-mini-grid { grid-template-columns: repeat(2, 1fr); }
}

/* 헤더 네비게이션 */
.fr-header-nav {
    display: flex;
    align-items: center;
    gap: 20px;
}
.fr-nav-link {
    color: #475569;
    text-decoration: none;
    font-weight: 600;
    font-size: 0.9rem;
    padding: 8px 16px;
    border-radius: 6px;
    transition: all 0.2s;
}
.fr-nav-link:hover {
    color: #3b82f6;
    background: #eff6ff;
}
.fr-nav-btn {
    background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
    color: white !important;
    font-weight: 700;
    font-size: 0.9rem;
    padding: 10px 20px;
    border-radius: 8px;
    text-decoration: none;
    box-shadow: 0 4px 12px rgba(59,130,246,0.3);
    transition: all 0.2s;
}
.fr-nav-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(59,130,246,0.4);
}

/* 요금제 섹션 */
.fr-pricing-section {
    background: white;
    padding: 60px 24px;
    margin-top: 48px;
}
.fr-pricing-inner {
    max-width: 1100px;
    margin: 0 auto;
}
.fr-pricing-title {
    font-size: 2rem;
    font-weight: 800;
    color: #1e3a5f;
    text-align: center;
    margin-bottom: 48px;
}
.fr-pricing-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
}
@media (max-width: 800px) {
    .fr-pricing-grid { grid-template-columns: 1fr; }
}
.fr-pricing-card {
    background: white;
    border-radius: 16px;
    padding: 32px 24px;
    border: 2px solid #e2e8f0;
    text-align: center;
    transition: all 0.3s;
}
.fr-pricing-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0,0,0,0.08);
}
.fr-pricing-card.popular {
    border-color: #3b82f6;
    position: relative;
}
.fr-pricing-card.premium {
    border-color: #8b5cf6;
}
.fr-popular-badge {
    position: absolute;
    top: -14px;
    left: 50%;
    transform: translateX(-50%);
    background: #3b82f6;
    color: white;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 6px 16px;
    border-radius: 20px;
}
.fr-plan-name {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1e3a5f;
    margin-bottom: 8px;
}
.fr-plan-price {
    font-size: 2rem;
    font-weight: 800;
    margin-bottom: 4px;
}
.fr-plan-price.free { color: #1e3a5f; }
.fr-plan-price.standard { color: #3b82f6; }
.fr-plan-price.premium { color: #8b5cf6; }
.fr-plan-period {
    font-size: 0.9rem;
    color: #64748b;
    margin-bottom: 24px;
}
.fr-plan-features {
    list-style: none;
    padding: 0;
    margin: 0 0 24px 0;
    text-align: left;
}
.fr-plan-features li {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 0;
    font-size: 0.9rem;
    color: #334155;
    border-bottom: 1px solid #f1f5f9;
}
.fr-plan-features li:last-child { border-bottom: none; }
.fr-check { color: #22c55e; font-weight: bold; }
.fr-cross { color: #cbd5e1; }
.fr-plan-btn {
    display: block;
    width: 100%;
    padding: 14px;
    border-radius: 10px;
    font-size: 1rem;
    font-weight: 700;
    text-decoration: none;
    text-align: center;
    transition: all 0.2s;
    box-sizing: border-box;
}
.fr-plan-btn-secondary {
    background: #e2e8f0;
    color: #475569;
}
.fr-plan-btn-secondary:hover {
    background: #cbd5e1;
}
.fr-plan-btn-primary {
    background: #3b82f6;
    color: white;
}
.fr-plan-btn-primary:hover {
    background: #2563eb;
}
.fr-plan-btn-premium {
    background: #8b5cf6;
    color: white;
}
.fr-plan-btn-premium:hover {
    background: #7c3aed;
}

/* ========================================
   FlyReady Lab - Enterprise UI/UX Enhancement
   ======================================== */

/* 페이지 로드 애니메이션 */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideInLeft {
    from {
        opacity: 0;
        transform: translateX(-30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-5px); }
}

/* 스크롤 기반 애니메이션 */
.fr-animate-on-scroll {
    opacity: 0;
    transform: translateY(20px);
    transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.fr-animate-on-scroll.visible {
    opacity: 1;
    transform: translateY(0);
}

/* 향상된 버튼 효과 */
.fr-btn {
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fr-btn::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    border-radius: 50%;
    background: rgba(255,255,255,0.3);
    transform: translate(-50%, -50%);
    transition: width 0.6s, height 0.6s;
}

.fr-btn:active::before {
    width: 300px;
    height: 300px;
}

/* 카드 호버 효과 강화 */
.fr-card {
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    animation: fadeInUp 0.6s ease forwards;
}

.fr-card:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 20px 40px rgba(0,0,0,0.12), 0 8px 16px rgba(0,0,0,0.08);
}

/* 미니 카드 효과 */
.fr-mini-card {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fr-mini-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0,0,0,0.1);
    border-color: #3b82f6;
}

/* 로딩 스켈레톤 */
.skeleton {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 8px;
}

/* 로딩 스피너 */
.fr-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #e2e8f0;
    border-top-color: #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* 프로그레스 바 애니메이션 */
.fr-progress-bar-fill {
    animation: progressGrow 1s ease-out forwards;
}

@keyframes progressGrow {
    from { width: 0; }
}

/* 툴팁 */
.fr-tooltip {
    position: relative;
}

.fr-tooltip::after {
    content: attr(data-tooltip);
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%) translateY(-8px);
    background: #1e3a5f;
    color: white;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 0.8rem;
    white-space: nowrap;
    opacity: 0;
    visibility: hidden;
    transition: all 0.2s;
    z-index: 1000;
}

.fr-tooltip:hover::after {
    opacity: 1;
    visibility: visible;
    transform: translateX(-50%) translateY(-4px);
}

/* 알림 뱃지 */
.fr-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 20px;
    height: 20px;
    padding: 0 6px;
    border-radius: 10px;
    font-size: 0.7rem;
    font-weight: 700;
    background: #ef4444;
    color: white;
    animation: pulse 2s infinite;
}

/* 성공/에러 토스트 */
.fr-toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    padding: 16px 24px;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    animation: slideInLeft 0.3s ease;
    z-index: 9999;
}

.fr-toast-success {
    background: #10b981;
    color: white;
}

.fr-toast-error {
    background: #ef4444;
    color: white;
}

/* 향상된 입력 필드 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    transition: all 0.2s ease;
    border: 2px solid #e2e8f0 !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

/* 그라데이션 텍스트 */
.fr-gradient-text {
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* 글로우 효과 */
.fr-glow {
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
}

.fr-glow:hover {
    box-shadow: 0 0 30px rgba(59, 130, 246, 0.5);
}

/* 물결 효과 버튼 */
.fr-ripple {
    position: relative;
    overflow: hidden;
}

/* 페이드 인 시퀀스 (각 요소마다 딜레이) */
.fr-card:nth-child(1) { animation-delay: 0.1s; }
.fr-card:nth-child(2) { animation-delay: 0.2s; }
.fr-card:nth-child(3) { animation-delay: 0.3s; }
.fr-card:nth-child(4) { animation-delay: 0.4s; }

/* 히어로 섹션 강화 */
.fr-hero {
    position: relative;
    overflow: hidden;
}

.fr-hero::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 100%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
    animation: float 6s ease-in-out infinite;
}

.fr-hero h1 {
    animation: fadeInUp 0.8s ease;
}

.fr-hero p {
    animation: fadeInUp 0.8s ease 0.2s both;
}

.fr-hero-actions {
    animation: fadeInUp 0.8s ease 0.4s both;
}

/* 섹션 타이틀 효과 */
.fr-section-title {
    position: relative;
    display: inline-block;
}

.fr-section-title::after {
    content: '';
    position: absolute;
    bottom: -4px;
    left: 0;
    width: 40px;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    border-radius: 2px;
    transition: width 0.3s ease;
}

.fr-section-title:hover::after {
    width: 100%;
}

/* 스크롤바 스타일 */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #3b82f6, #1e3a5f);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(180deg, #2563eb, #1e3a5f);
}

/* 부드러운 스크롤 */
html {
    scroll-behavior: smooth;
}

/* 선택 텍스트 스타일 */
::selection {
    background: rgba(59, 130, 246, 0.3);
    color: #1e3a5f;
}

/* 포커스 스타일 개선 (접근성) */
*:focus {
    outline: none;
}

*:focus-visible {
    outline: 2px solid #3b82f6;
    outline-offset: 2px;
}

/* 모바일 반응형 개선 */
@media (max-width: 768px) {
    .fr-hero {
        padding: 32px 20px;
    }
    
    .fr-hero h1 {
        font-size: 1.5rem;
    }
    
    .fr-hero-actions {
        flex-direction: column;
    }
    
    .fr-btn {
        width: 100%;
        text-align: center;
    }
    
    .fr-card {
        margin-bottom: 12px;
    }
    
    .fr-header {
        padding: 12px 16px;
    }
}

/* 태블릿 */
@media (min-width: 769px) and (max-width: 1024px) {
    .fr-card-grid {
        grid-template-columns: repeat(2, 1fr) !important;
    }
}

/* 인쇄 스타일 */
@media print {
    .fr-header, .fr-hero-actions, .fr-nav-link, .fr-nav-btn {
        display: none !important;
    }
    
    .fr-card {
        break-inside: avoid;
        box-shadow: none;
        border: 1px solid #ddd;
    }
}

</style>
""", unsafe_allow_html=True)

# =====================
# 헤더
# =====================
if LOGO_BASE64:
    logo_html = f'<img src="data:image/png;base64,{LOGO_BASE64}" alt="FlyReady Lab">'
else:
    logo_html = '<span style="color: #3b82f6;">FlyReady</span><span style="color: #1e3a5f;">Lab</span>'

st.markdown(f'''
<div class="fr-header">
    <a target="_self" href="/" class="fr-logo">{logo_html}</a>
    <div class="fr-header-nav">
        <a target="_self" href="/요금제" class="fr-nav-link">요금제</a>
        <a target="_self" href="/로그인" class="fr-nav-link">로그인</a>
        <a target="_self" href="/자소서첨삭" class="fr-nav-btn">무료로 시작하기</a>
    </div>
</div>
''', unsafe_allow_html=True)

# =====================
# 히어로 섹션
# =====================
st.markdown(f'''
<div class="fr-hero">
    <p style="font-size: 0.95rem; opacity: 0.9; margin-bottom: 8px;">{greeting}</p>
    <h1>AI와 함께하는 승무원 면접 준비</h1>
    <p>실전 모의면접 | 자소서 첨삭 | 기내 롤플레잉 | 체력/이미지 관리</p>
    <div class="fr-hero-actions">
        <a target="_self" href="/모의면접" class="fr-btn fr-btn-primary">모의면접 시작</a>
        <a target="_self" href="/롤플레잉" class="fr-btn fr-btn-secondary">롤플레잉 연습</a>
    </div>
</div>
''', unsafe_allow_html=True)

# =====================
# 메인 컨텐츠 시작
# =====================
st.markdown('<div class="fr-main">', unsafe_allow_html=True)

# =====================
# 대시보드 통계 카드
# =====================
st.markdown(f'''
<div class="fr-stats-grid">
    <div class="fr-stat-card streak">
        <div class="fr-stat-value">{study_streak}일</div>
        <div class="fr-stat-label">연속 학습일</div>
    </div>
    <div class="fr-stat-card weekly">
        <div class="fr-stat-value">{weekly_count}회</div>
        <div class="fr-stat-label">이번 주 연습</div>
    </div>
    <div class="fr-stat-card progress">
        <div class="fr-stat-value">{progress_pct}%</div>
        <div class="fr-stat-label">전체 진도율</div>
    </div>
    <div class="fr-stat-card score">
        <div class="fr-stat-value">{recent_avg if recent_avg > 0 else "-"}점</div>
        <div class="fr-stat-label">최근 평균 점수</div>
    </div>
</div>
''', unsafe_allow_html=True)

# =====================
# 오늘 할 일 프로그레스
# =====================
if today_total > 0:
    bar_color = "#10b981" if today_pct >= 80 else ("#3b82f6" if today_pct >= 50 else "#f59e0b")
    st.markdown(f'''
    <div class="fr-today-progress">
        <div class="fr-today-label">오늘 할 일</div>
        <div class="fr-progress-bar-container">
            <div class="fr-progress-bar-fill" style="width: {today_pct}%; background: {bar_color};"></div>
        </div>
        <div class="fr-progress-pct">{today_done}/{today_total} ({today_pct}%)</div>
    </div>
    ''', unsafe_allow_html=True)

# =====================
# 스트릭 & 일일 미션 (A-G 개선사항)
# =====================
streak_html = ""
missions_html = ""
if ENHANCEMENT_AVAILABLE:
    # 연습 날짜 기록 (scores에서 추출)
    practice_dates = []
    for score in dashboard_data["scores"].get("scores", []):
        try:
            date_str = score.get("date", "")[:10]
            if date_str:
                practice_dates.append(datetime.strptime(date_str, "%Y-%m-%d"))
        except (ValueError, TypeError):
            pass

    # 스트릭 HTML
    streak_html = get_streak_display_html(practice_dates)

    # 일일 미션 HTML
    missions_html = get_daily_missions_html()

# 스트릭 배지 표시 (히어로 섹션 아래)
if streak_html:
    st.markdown(f'''
    <div style="display: flex; justify-content: center; margin-top: -16px; margin-bottom: 16px;">
        {streak_html}
    </div>
    ''', unsafe_allow_html=True)

# =====================
# D-Day + 추천 영역
# =====================
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
        dday_items_html += f'<div class="fr-dday-item {urgency_class}"><div><div class="fr-dday-name">{title}</div><div class="fr-dday-date">{date_str}</div></div><div class="fr-dday-badge {badge_class}">{dday_text}</div></div>'
else:
    dday_items_html = '<div style="text-align:center;padding:20px;color:#64748b;font-size:0.85rem;">첫 일정을 등록하고<br><a href="/D-Day캘린더" style="color:#3b82f6;font-weight:600;">D-Day 관리 시작하기</a></div>'

recommend_items_html = ""
for rec in recommendations:
    urgency_class = rec.get("urgency", "low")
    recommend_items_html += f'<div class="fr-recommend-item {urgency_class}"><span class="fr-recommend-text">{rec["text"]}</span></div>'

# 일일 미션이 있으면 3컬럼, 없으면 2컬럼
if missions_html:
    col_dday, col_mission, col_rec = st.columns(3)

    with col_dday:
        st.markdown(f'<div class="fr-info-box"><div class="fr-info-title">다가오는 일정</div>{dday_items_html}</div>', unsafe_allow_html=True)

    with col_mission:
        st.markdown(missions_html, unsafe_allow_html=True)

    with col_rec:
        st.markdown(f'<div class="fr-info-box"><div class="fr-info-title">오늘의 추천</div>{recommend_items_html}</div>', unsafe_allow_html=True)
else:
    col_dday, col_rec = st.columns(2)

    with col_dday:
        st.markdown(f'<div class="fr-info-box"><div class="fr-info-title">다가오는 일정</div>{dday_items_html}</div>', unsafe_allow_html=True)

    with col_rec:
        st.markdown(f'<div class="fr-info-box"><div class="fr-info-title">오늘의 추천</div>{recommend_items_html}</div>', unsafe_allow_html=True)

# =====================
# 섹션 1: 면접 연습 (핵심)
# =====================
st.markdown('''
<div class="fr-section">
    <div class="fr-section-title">면접 연습</div>
    <div class="fr-card-grid">
        <a target="_self" href="/모의면접" class="fr-card">
            <div class="fr-card-title">AI 모의면접</div>
            <div class="fr-card-desc">실전처럼 연습하고<br>즉시 피드백 받기</div>
        </a>
        <a target="_self" href="/롤플레잉" class="fr-card">
            <div class="fr-card-title">기내 롤플레잉</div>
            <div class="fr-card-desc">실제 기내 상황<br>시뮬레이션</div>
        </a>
        <a target="_self" href="/영어면접" class="fr-card">
            <div class="fr-card-title">영어면접</div>
            <div class="fr-card-desc">영어 질문<br>답변 연습</div>
        </a>
        <a target="_self" href="/토론면접" class="fr-card">
            <div class="fr-card-title">토론면접</div>
            <div class="fr-card-desc">그룹 토론<br>시뮬레이션</div>
        </a>
    </div>
</div>
''', unsafe_allow_html=True)

# =====================
# 섹션 2: 서류 준비
# =====================
st.markdown('''
<div class="fr-section">
    <div class="fr-section-title">서류 준비</div>
    <div class="fr-card-grid" style="grid-template-columns: repeat(2, 1fr);">
        <a target="_self" href="/자소서작성" class="fr-card" style="border: 2px solid #2563eb;">
            <div class="fr-card-title">자소서 작성 도우미</div>
            <div class="fr-card-desc">문항 의도 분석 +<br>AI 챗봇 컨설팅</div>
        </a>
        <a target="_self" href="/자소서첨삭" class="fr-card">
            <div class="fr-card-title">자소서 AI 첨삭</div>
            <div class="fr-card-desc">AI가 자소서 분석 및<br>피드백 제공</div>
        </a>
        <a target="_self" href="/자소서기반질문" class="fr-card">
            <div class="fr-card-title">자소서 기반 질문</div>
            <div class="fr-card-desc">내 자소서에서<br>예상 질문 생성</div>
        </a>
        <a target="_self" href="/에어로케이" class="fr-card" style="border: 2px solid #10b981; background: linear-gradient(135deg, #ecfdf5, #d1fae5);">
            <div class="fr-card-title">에어로케이 가이드</div>
            <div class="fr-card-desc">경험 포트폴리오<br>컨설팅 (자소서 폐지)</div>
        </a>
    </div>
</div>
''', unsafe_allow_html=True)

# =====================
# 섹션 3: 실전 훈련
# =====================
st.markdown('''
<div class="fr-section">
    <div class="fr-section-title">실전 훈련</div>
    <div class="fr-card-grid" style="grid-template-columns: repeat(2, 1fr);">
        <a target="_self" href="/표정연습" class="fr-card">
            <div class="fr-card-title">표정 연습</div>
            <div class="fr-card-desc">면접 표정<br>훈련하기</div>
        </a>
        <a target="_self" href="/기내방송연습" class="fr-card">
            <div class="fr-card-title">기내방송 연습</div>
            <div class="fr-card-desc">한국어/영어<br>15개 스크립트</div>
        </a>
    </div>
</div>
''', unsafe_allow_html=True)

# =====================
# 섹션 4: 이미지 / 체력
# =====================
st.markdown('''
<div class="fr-section">
    <div class="fr-section-title">이미지 / 체력</div>
    <div class="fr-card-grid" style="grid-template-columns: repeat(2, 1fr);">
        <a target="_self" href="/이미지메이킹" class="fr-card">
            <div class="fr-card-title">이미지메이킹</div>
            <div class="fr-card-desc">메이크업/복장<br>셀프체크 가이드</div>
        </a>
        <a target="_self" href="/국민체력" class="fr-card">
            <div class="fr-card-title">국민체력 / 수영</div>
            <div class="fr-card-desc">체력시험 준비<br>가이드</div>
        </a>
    </div>
</div>
''', unsafe_allow_html=True)

# =====================
# 섹션 5: 정보 / 가이드
# =====================
st.markdown('''
<div class="fr-section">
    <div class="fr-section-title">정보 / 가이드</div>
    <div class="fr-mini-grid">
        <a target="_self" href="/항공사퀴즈" class="fr-mini-card">
            <div class="fr-mini-card-title">항공 상식 퀴즈</div>
        </a>
        <a target="_self" href="/면접꿀팁" class="fr-mini-card">
            <div class="fr-mini-card-title">면접 꿀팁</div>
        </a>
        <a target="_self" href="/항공사가이드" class="fr-mini-card">
            <div class="fr-mini-card-title">항공사 가이드</div>
        </a>
        <a target="_self" href="/기업분석" class="fr-mini-card">
            <div class="fr-mini-card-title">기업 분석</div>
        </a>
        <a target="_self" href="/합격자DB" class="fr-mini-card">
            <div class="fr-mini-card-title">합격자 DB</div>
        </a>
    </div>
</div>
''', unsafe_allow_html=True)

# =====================
# 섹션 6: 학습 관리
# =====================
st.markdown('''
<div class="fr-section">
    <div class="fr-section-title">학습 관리</div>
    <div class="fr-mini-grid">
        <a target="_self" href="/진도관리" class="fr-mini-card">
            <div class="fr-mini-card-title">진도 관리</div>
        </a>
        <a target="_self" href="/성장그래프" class="fr-mini-card">
            <div class="fr-mini-card-title">성장 그래프</div>
        </a>
        <a target="_self" href="/D-Day캘린더" class="fr-mini-card">
            <div class="fr-mini-card-title">D-Day 캘린더</div>
        </a>
        <a target="_self" href="/스킬분석" class="fr-mini-card">
            <div class="fr-mini-card-title">스킬 분석</div>
        </a>
        <a target="_self" href="/AI코칭" class="fr-mini-card">
            <div class="fr-mini-card-title">AI 코칭</div>
        </a>
    </div>
</div>
''', unsafe_allow_html=True)

# =====================
# 섹션 7: 채용 / 커뮤니티
# =====================
st.markdown('''
<div class="fr-section">
    <div class="fr-section-title">채용 / 커뮤니티</div>
    <div class="fr-card-grid" style="grid-template-columns: repeat(3, 1fr);">
        <a target="_self" href="/채용알림" class="fr-card">
            <div class="fr-card-title">채용 알림</div>
            <div class="fr-card-desc">11개 국내 항공사<br>채용 일정 확인</div>
        </a>
        <a target="_self" href="/QnA게시판" class="fr-card">
            <div class="fr-card-title">Q&A 게시판</div>
            <div class="fr-card-desc">궁금한 점<br>질문하기</div>
        </a>
        <a target="_self" href="/멘토찾기" class="fr-card">
            <div class="fr-card-title">멘토 찾기</div>
            <div class="fr-card-desc">현직자/합격자<br>멘토 연결</div>
        </a>
    </div>
</div>
''', unsafe_allow_html=True)

# 메인 컨텐츠 종료
st.markdown('</div>', unsafe_allow_html=True)

# =====================
# 격려 메시지 토스트 (A-G 개선사항)
# =====================
if ENHANCEMENT_AVAILABLE and recent_avg > 0:
    encouragement_html = show_encouragement_toast(
        score=recent_avg,
        streak=study_streak,
        previous_score=recent_avg - 5 if recent_avg > 5 else 0
    )
    if encouragement_html:
        st.markdown(encouragement_html, unsafe_allow_html=True)

# =====================
# 푸터
# =====================
st.markdown('''
<div class="fr-footer">
    <div class="fr-footer-brand">FlyReady Lab</div>
    <p>당신의 꿈을 응원합니다</p>
    <p style="margin-top: 12px; font-size: 0.75rem; opacity: 0.5;">2026 FlyReady Lab. All rights reserved.</p>
</div>
''', unsafe_allow_html=True)

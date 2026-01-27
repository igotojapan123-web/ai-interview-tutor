# pages/3_진도관리.py
# 학습 진도 관리 - 자동 연동, AI 추천, 시각적 성취감

import os
import json
from datetime import datetime, timedelta
from collections import defaultdict
import streamlit as st

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging_config import get_logger
logger = get_logger(__name__)

# 롤플레잉 시나리오
try:
    from roleplay_scenarios import SCENARIOS as RP_SCENARIOS, get_all_scenarios
except ImportError:
    RP_SCENARIOS = {}
    def get_all_scenarios():
        return []

# 영어면접 질문
try:
    from english_interview_data import ENGLISH_QUESTIONS, get_all_categories as get_eng_categories
except ImportError:
    ENGLISH_QUESTIONS = {}
    def get_eng_categories():
        return []

# 점수 유틸리티
try:
    from score_utils import load_scores, get_category_averages, get_weekly_report, EVALUATION_CATEGORIES
    SCORE_UTILS_AVAILABLE = True
except ImportError:
    SCORE_UTILS_AVAILABLE = False
    def load_scores():
        return {"scores": [], "detailed_scores": []}

# 약점 기반 추천
try:
    from roleplay_report import get_weakness_recommendations, WEAKNESS_SCENARIO_MAP
    from english_interview_report import get_weakness_recommendations_english
    RECOMMENDATIONS_AVAILABLE = True
except ImportError:
    RECOMMENDATIONS_AVAILABLE = False


from sidebar_common import render_sidebar

st.set_page_config(
    page_title="진도 관리",
    page_icon="📅",
    layout="wide"
)
render_sidebar("진도관리")



# =====================
# 데이터 파일 경로
# =====================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "user_progress.json")
RP_PROGRESS_FILE = os.path.join(BASE_DIR, "roleplay_progress.json")
SCORES_FILE = os.path.join(BASE_DIR, "user_scores.json")


# =====================
# 데이터 저장/로드
# =====================

def load_progress_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"진도 데이터 로드 실패: {e}")
    return {
        "checklist_completed": {},
    }


def save_progress_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"진도 데이터 저장 실패: {e}")


def load_roleplay_progress():
    if os.path.exists(RP_PROGRESS_FILE):
        try:
            with open(RP_PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"롤플레이 진도 로드 실패: {e}")
    return {"history": [], "completed_scenarios": []}


if "progress_data" not in st.session_state:
    st.session_state.progress_data = load_progress_data()


def get_data():
    return st.session_state.progress_data


def update_data(key, value):
    st.session_state.progress_data[key] = value
    save_progress_data(st.session_state.progress_data)


# =====================
# 자동 진도 계산 (실제 연습 기록 기반)
# =====================

def get_actual_progress():
    """실제 연습 기록을 기반으로 진도 계산"""
    progress = {
        "롤플레잉": {"completed": 0, "total": 0, "items": []},
        "영어면접": {"completed": 0, "total": 0, "items": []},
        "모의면접": {"completed": 0, "total": 0, "items": []},
        "자소서": {"completed": 0, "total": 0, "items": []},
    }

    # 1. 롤플레잉 진도
    rp_data = load_roleplay_progress()
    completed_scenarios = set(rp_data.get("completed_scenarios", []))
    all_scenarios = get_all_scenarios()

    for scenario in all_scenarios:
        sid = scenario.get("id", "")
        title = scenario.get("title", sid)
        is_done = sid in completed_scenarios
        progress["롤플레잉"]["items"].append({
            "id": sid,
            "title": title,
            "completed": is_done,
            "category": scenario.get("category", ""),
            "difficulty": scenario.get("difficulty", 1),
        })
        progress["롤플레잉"]["total"] += 1
        if is_done:
            progress["롤플레잉"]["completed"] += 1

    # 2. 영어면접 진도 (점수 기록 기반)
    scores_data = load_scores()
    eng_scores = [s for s in scores_data.get("scores", []) if s.get("type") == "영어면접"]

    # 카테고리별 완료 여부
    eng_categories = get_eng_categories()
    practiced_categories = set()
    for s in eng_scores:
        scenario = s.get("scenario", "")
        for cat in eng_categories:
            if cat.get("name", "") in scenario or cat.get("name_en", "") in scenario:
                practiced_categories.add(cat.get("key", ""))

    for cat in eng_categories:
        is_done = cat.get("key", "") in practiced_categories
        progress["영어면접"]["items"].append({
            "id": cat.get("key", ""),
            "title": f"{cat.get('name', '')} ({cat.get('name_en', '')})",
            "completed": is_done,
        })
        progress["영어면접"]["total"] += 1
        if is_done:
            progress["영어면접"]["completed"] += 1

    # 모의면접 5회 이상 완료 체크
    mock_count = len([s for s in eng_scores if "모의면접" in s.get("scenario", "")])
    progress["영어면접"]["items"].append({
        "id": "eng_mock_5",
        "title": f"모의면접 5회 완료 ({mock_count}/5)",
        "completed": mock_count >= 5,
    })
    progress["영어면접"]["total"] += 1
    if mock_count >= 5:
        progress["영어면접"]["completed"] += 1

    # 3. 모의면접 (한국어) 진도
    mock_scores = [s for s in scores_data.get("scores", []) if s.get("type") == "모의면접"]
    mock_interviews_done = len(mock_scores)

    milestones = [1, 3, 5, 10, 20]
    for m in milestones:
        is_done = mock_interviews_done >= m
        progress["모의면접"]["items"].append({
            "id": f"mock_{m}",
            "title": f"모의면접 {m}회 완료",
            "completed": is_done,
        })
        progress["모의면접"]["total"] += 1
        if is_done:
            progress["모의면접"]["completed"] += 1

    # 4. 자소서 진도 (수동 체크리스트 유지)
    manual_checklist = get_data().get("checklist_completed", {})
    resume_items = [
        ("resume_written", "자소서 작성 완료"),
        ("resume_analyzed", "자소서 분석 완료"),
        ("resume_q1", "예상 질문 1 준비"),
        ("resume_q2", "예상 질문 2 준비"),
        ("resume_q3", "예상 질문 3 준비"),
    ]
    for item_id, title in resume_items:
        is_done = manual_checklist.get(item_id, False)
        progress["자소서"]["items"].append({
            "id": item_id,
            "title": title,
            "completed": is_done,
        })
        progress["자소서"]["total"] += 1
        if is_done:
            progress["자소서"]["completed"] += 1

    return progress


def get_category_percent(progress, category):
    """카테고리별 진도율 계산"""
    cat_data = progress.get(category, {})
    total = cat_data.get("total", 0)
    completed = cat_data.get("completed", 0)
    if total == 0:
        return 0
    return int((completed / total) * 100)


def get_total_percent(progress):
    """전체 진도율 계산"""
    total = 0
    completed = 0
    for cat_data in progress.values():
        total += cat_data.get("total", 0)
        completed += cat_data.get("completed", 0)
    if total == 0:
        return 0
    return int((completed / total) * 100)


# =====================
# 학습 기록 히트맵 데이터
# =====================

def get_heatmap_data(days=90):
    """최근 N일간 학습 기록 (히트맵용)"""
    scores_data = load_scores()
    rp_data = load_roleplay_progress()

    # 날짜별 학습 횟수 집계
    daily_counts = defaultdict(int)

    # 점수 기록
    for s in scores_data.get("scores", []):
        date_str = s.get("date", "")
        if date_str:
            daily_counts[date_str] += 1

    # 롤플레잉 기록
    for h in rp_data.get("history", []):
        timestamp = h.get("timestamp", "")
        if timestamp:
            date_str = timestamp[:10]
            daily_counts[date_str] += 1

    # 최근 N일 데이터로 변환
    today = datetime.now().date()
    heatmap = []
    for i in range(days - 1, -1, -1):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        count = daily_counts.get(date_str, 0)
        heatmap.append({
            "date": date_str,
            "weekday": date.weekday(),
            "count": count,
        })

    return heatmap


def get_streak_count():
    """연속 학습일 계산"""
    scores_data = load_scores()
    rp_data = load_roleplay_progress()

    # 모든 학습 날짜 수집
    study_dates = set()

    for s in scores_data.get("scores", []):
        if s.get("date"):
            study_dates.add(s["date"])

    for h in rp_data.get("history", []):
        if h.get("timestamp"):
            study_dates.add(h["timestamp"][:10])

    if not study_dates:
        return 0

    # 오늘부터 거꾸로 연속일 계산
    today = datetime.now().date()
    streak = 0

    for i in range(365):
        check_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        if check_date in study_dates:
            streak += 1
        else:
            if i == 0:
                continue
            break

    return streak


# =====================
# AI 맞춤 추천
# =====================

def get_ai_recommendations():
    """약점 기반 AI 맞춤 추천"""
    recommendations = []

    if not SCORE_UTILS_AVAILABLE:
        return recommendations

    scores_data = load_scores()
    detailed_scores = scores_data.get("detailed_scores", [])

    if not detailed_scores:
        # 기록이 없으면 기본 추천
        return [
            {"type": "시작", "title": "롤플레잉 연습 시작하기", "reason": "아직 연습 기록이 없습니다", "link": "pages/1_롤플레잉.py"},
            {"type": "시작", "title": "영어면접 연습 시작하기", "reason": "아직 연습 기록이 없습니다", "link": "pages/2_영어면접.py"},
        ]

    # 최근 세부 점수 분석
    recent_detailed = detailed_scores[-10:]

    # 카테고리별 평균 계산
    category_scores = defaultdict(list)
    for entry in recent_detailed:
        for key, score in entry.get("scores", {}).items():
            category_scores[key].append(score)

    # 가장 낮은 점수 항목 찾기
    weak_areas = []
    for key, scores in category_scores.items():
        avg = sum(scores) / len(scores)
        weak_areas.append((key, avg))

    weak_areas.sort(key=lambda x: x[1])

    # 약점 기반 추천 생성
    for key, avg in weak_areas[:3]:
        if avg >= 80:
            continue

        # 약점에 맞는 추천 찾기
        if key in ["empathy", "solution", "professionalism", "attitude"]:
            # 롤플레잉 관련
            all_scenarios = get_all_scenarios()
            if all_scenarios:
                # 난이도 낮은 시나리오 추천
                easy_scenarios = [s for s in all_scenarios if s.get("difficulty", 1) <= 2]
                if easy_scenarios:
                    scenario = easy_scenarios[0]
                    recommendations.append({
                        "type": "롤플레잉",
                        "title": scenario.get("title", ""),
                        "reason": f"{get_item_name(key)} 점수 개선 필요 (평균 {avg:.0f}점)",
                        "link": "pages/1_롤플레잉.py",
                        "scenario_id": scenario.get("id"),
                    })

        elif key in ["pronunciation", "fluency", "grammar", "content", "vocabulary"]:
            # 영어면접 관련
            recommendations.append({
                "type": "영어면접",
                "title": f"{get_item_name(key)} 집중 연습",
                "reason": f"{get_item_name(key)} 점수 개선 필요 (평균 {avg:.0f}점)",
                "link": "pages/2_영어면접.py",
            })

    # 연습량 부족 체크
    today = datetime.now().date()
    week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    this_week_count = len([s for s in scores_data.get("scores", []) if s.get("date", "") >= week_start])

    if this_week_count < 5:
        recommendations.append({
            "type": "연습량",
            "title": "이번 주 연습량 부족",
            "reason": f"이번 주 {this_week_count}회 연습 (권장: 10회 이상)",
            "link": None,
        })

    return recommendations[:5]


def get_item_name(key):
    """세부 항목 키를 한글 이름으로 변환"""
    names = {
        "empathy": "공감 표현",
        "solution": "해결책 제시",
        "professionalism": "전문성",
        "attitude": "태도/말투",
        "pronunciation": "발음",
        "fluency": "유창성",
        "grammar": "문법",
        "content": "내용",
        "vocabulary": "어휘력",
        "first_impression": "첫인상",
        "answer_quality": "답변 내용",
        "communication": "의사소통",
        "adaptability": "순발력",
    }
    return names.get(key, key)


# =====================
# 주간 통계
# =====================

def get_weekly_stats():
    """주간 통계 데이터"""
    scores_data = load_scores()
    rp_data = load_roleplay_progress()

    today = datetime.now().date()
    stats = []

    for i in range(7):
        date = today - timedelta(days=6-i)
        date_str = date.strftime("%Y-%m-%d")

        count = 0
        total_score = 0

        for s in scores_data.get("scores", []):
            if s.get("date") == date_str:
                count += 1
                total_score += s.get("score", 0)

        for h in rp_data.get("history", []):
            if h.get("timestamp", "").startswith(date_str):
                count += 1
                total_score += h.get("score", 0)

        avg_score = total_score / count if count > 0 else 0

        stats.append({
            "date": date.strftime("%m/%d"),
            "weekday": ["월", "화", "수", "목", "금", "토", "일"][date.weekday()],
            "count": count,
            "avg_score": round(avg_score, 1),
        })

    return stats


# =====================
# CSS 스타일
# =====================

st.markdown("""
<style>
.block-container { padding-top: 1rem !important; }

/* 히트맵 */
.heatmap-container {
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    margin-bottom: 20px;
    overflow-x: auto;
}
.heatmap-grid {
    display: grid;
    grid-template-columns: repeat(13, 1fr);
    gap: 3px;
    min-width: 600px;
}
.heatmap-cell {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    background: #ebedf0;
}
.heatmap-cell.level-1 { background: #9be9a8; }
.heatmap-cell.level-2 { background: #40c463; }
.heatmap-cell.level-3 { background: #30a14e; }
.heatmap-cell.level-4 { background: #216e39; }

/* 추천 카드 */
.recommendation-card {
    background: linear-gradient(135deg, #fff 0%, #f8f9ff 100%);
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 10px;
    border-left: 4px solid #667eea;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.rec-type {
    font-size: 0.75rem;
    color: #667eea;
    font-weight: 600;
    margin-bottom: 5px;
}
.rec-title {
    font-size: 1rem;
    font-weight: 600;
    color: #333;
    margin-bottom: 5px;
}
.rec-reason {
    font-size: 0.85rem;
    color: #666;
}

/* 진도 바 */
.progress-section {
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    margin-bottom: 15px;
}
.progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}
.progress-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #333;
}
.progress-percent {
    font-size: 1.2rem;
    font-weight: 700;
}
.progress-bar-bg {
    background: #e5e7eb;
    border-radius: 10px;
    height: 12px;
    overflow: hidden;
}
.progress-bar-fill {
    height: 100%;
    border-radius: 10px;
    transition: width 0.5s ease;
}

@media (max-width: 768px) {
    .heatmap-grid { grid-template-columns: repeat(7, 1fr); }
}
</style>
""", unsafe_allow_html=True)


# =====================
# UI 시작
# =====================

st.title("📅 진도 관리")

data = get_data()
progress = get_actual_progress()

# 기본 통계
streak = get_streak_count()
total_progress = get_total_percent(progress)
scores_data = load_scores()
today_str = datetime.now().strftime("%Y-%m-%d")
today_count = len([s for s in scores_data.get("scores", []) if s.get("date") == today_str])

# 간단한 상단 요약
col_stat1, col_stat2, col_stat3 = st.columns(3)
with col_stat1:
    st.metric("🔥 연속 학습일", f"{streak}일")
with col_stat2:
    st.metric("📊 전체 진도", f"{total_progress}%")
with col_stat3:
    st.metric("✅ 오늘 연습", f"{today_count}회")

st.markdown("---")

# ========== 메인 컨텐츠: 2열 레이아웃 ==========
col_left, col_right = st.columns([2, 1])

with col_left:
    # ===== 학습 캘린더 히트맵 =====
    st.markdown("### 📅 학습 캘린더")

    heatmap_data = get_heatmap_data(91)  # 13주

    # 히트맵 HTML 생성
    heatmap_html = '<div class="heatmap-container"><div class="heatmap-grid">'

    # 요일 라벨
    for day in ["", "월", "", "수", "", "금", ""]:
        heatmap_html += f'<div style="font-size:10px;color:#666;text-align:center;">{day}</div>'

    # 주별로 그룹화
    weeks = []
    current_week = []
    for item in heatmap_data:
        current_week.append(item)
        if item["weekday"] == 6:
            weeks.append(current_week)
            current_week = []
    if current_week:
        weeks.append(current_week)

    # 마지막 13주만
    weeks = weeks[-13:]

    for week in weeks:
        # 빈 셀로 시작 (첫 주 처리)
        if week[0]["weekday"] > 0:
            for _ in range(week[0]["weekday"]):
                heatmap_html += '<div></div>'

        for item in week:
            count = item["count"]
            if count == 0:
                level = ""
            elif count == 1:
                level = "level-1"
            elif count <= 3:
                level = "level-2"
            elif count <= 5:
                level = "level-3"
            else:
                level = "level-4"

            heatmap_html += f'<div class="heatmap-cell {level}" title="{item["date"]}: {count}회"></div>'

        # 주 마무리 (빈 셀)
        remaining = 6 - week[-1]["weekday"]
        for _ in range(remaining):
            heatmap_html += '<div></div>'

    heatmap_html += '</div>'

    # 범례
    heatmap_html += '''
    <div style="display:flex;align-items:center;gap:5px;margin-top:10px;justify-content:flex-end;">
        <span style="font-size:11px;color:#666;">적음</span>
        <div class="heatmap-cell"></div>
        <div class="heatmap-cell level-1"></div>
        <div class="heatmap-cell level-2"></div>
        <div class="heatmap-cell level-3"></div>
        <div class="heatmap-cell level-4"></div>
        <span style="font-size:11px;color:#666;">많음</span>
    </div>
    '''
    heatmap_html += '</div>'

    st.markdown(heatmap_html, unsafe_allow_html=True)

    # ===== 주간 통계 (텍스트) =====
    weekly_stats = get_weekly_stats()
    week_total = sum(s["count"] for s in weekly_stats)
    week_avg_score = 0
    score_count = 0
    for s in weekly_stats:
        if s["avg_score"] > 0:
            week_avg_score += s["avg_score"]
            score_count += 1
    week_avg_score = round(week_avg_score / score_count, 1) if score_count > 0 else 0

    st.caption(f"📊 이번 주: {week_total}회 연습 | 평균 {week_avg_score}점")

    # ===== 카테고리별 진도 =====
    st.markdown("### 📈 카테고리별 진도")

    category_icons = {"롤플레잉": "🎭", "영어면접": "🌍", "모의면접": "👔", "자소서": "📝"}
    category_colors = {"롤플레잉": "#f59e0b", "영어면접": "#10b981", "모의면접": "#3b82f6", "자소서": "#8b5cf6"}

    for cat_name, cat_data in progress.items():
        percent = get_category_percent(progress, cat_name)
        icon = category_icons.get(cat_name, "📋")
        color = category_colors.get(cat_name, "#667eea")

        st.markdown(f'''
        <div class="progress-section">
            <div class="progress-header">
                <div class="progress-title">{icon} {cat_name}</div>
                <div class="progress-percent" style="color:{color}">{percent}%</div>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width:{percent}%;background:{color};"></div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        # 세부 항목 (접힌 상태)
        with st.expander(f"{cat_name} 세부 항목 보기", expanded=False):
            items = cat_data.get("items", [])
            for item in items:
                status = "✅" if item.get("completed") else "⬜"
                st.write(f"{status} {item.get('title', '')}")


with col_right:
    # ===== AI 맞춤 추천 =====
    st.markdown("### 🤖 오늘의 추천")

    recommendations = get_ai_recommendations()

    if recommendations:
        for rec in recommendations:
            rec_type = rec.get("type", "")
            rec_title = rec.get("title", "")
            rec_reason = rec.get("reason", "")
            rec_link = rec.get("link")

            st.markdown(f'''
            <div class="recommendation-card">
                <div class="rec-type">{rec_type}</div>
                <div class="rec-title">{rec_title}</div>
                <div class="rec-reason">{rec_reason}</div>
            </div>
            ''', unsafe_allow_html=True)

            if rec_link:
                st.page_link(rec_link, label=f"▶ {rec_type} 연습하기", use_container_width=True)
    else:
        st.info("연습 기록이 쌓이면 AI가 맞춤 추천을 해드립니다!")

    st.markdown("---")

    # ===== 바로가기 =====
    st.markdown("### ⚡ 바로가기")

    st.page_link("pages/1_롤플레잉.py", label="🎭 롤플레잉", use_container_width=True)
    st.page_link("pages/2_영어면접.py", label="🌍 영어면접", use_container_width=True)
    st.page_link("pages/4_모의면접.py", label="👔 모의면접", use_container_width=True)
    st.page_link("pages/6_성장그래프.py", label="📈 성장그래프", use_container_width=True)

    st.markdown("---")

    # ===== 자소서 체크리스트 (수동) =====
    st.markdown("### 📝 자소서 체크리스트")

    resume_items = [
        ("resume_written", "자소서 작성 완료"),
        ("resume_analyzed", "자소서 분석 완료"),
        ("resume_q1", "예상 질문 1 준비"),
        ("resume_q2", "예상 질문 2 준비"),
        ("resume_q3", "예상 질문 3 준비"),
    ]

    completed = data.get("checklist_completed", {})

    for item_id, title in resume_items:
        is_done = completed.get(item_id, False)
        if st.checkbox(title, value=is_done, key=f"chk_{item_id}"):
            if not is_done:
                completed[item_id] = True
                update_data("checklist_completed", completed)
        else:
            if is_done:
                completed[item_id] = False
                update_data("checklist_completed", completed)


# ========== 최근 학습 기록 ==========
st.markdown("---")
with st.expander("📜 최근 학습 기록", expanded=False):
    all_records = []

    # 롤플레잉 기록
    rp_data = load_roleplay_progress()
    for h in rp_data.get("history", []):
        timestamp = h.get("timestamp", "")
        if timestamp:
            scenario_id = h.get("scenario_id", "")
            scenario_title = RP_SCENARIOS.get(scenario_id, {}).get("title", scenario_id)
            all_records.append({
                "timestamp": timestamp,
                "type": "🎭 롤플레잉",
                "detail": scenario_title,
                "score": h.get("score", 0),
            })

    # 점수 기록
    for s in scores_data.get("scores", []):
        date_str = s.get("date", "")
        time_str = s.get("time", "00:00")
        if date_str:
            all_records.append({
                "timestamp": f"{date_str} {time_str}",
                "type": s.get("type", "기타"),
                "detail": s.get("scenario", "")[:30],
                "score": s.get("score", 0),
            })

    # 정렬
    all_records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    if all_records:
        for rec in all_records[:20]:
            score_text = f" ({rec['score']}점)" if rec.get("score") else ""
            st.write(f"• {rec['timestamp'][:16]} - {rec['type']}: {rec['detail']}{score_text}")
    else:
        st.info("아직 학습 기록이 없습니다. 롤플레잉이나 면접 연습을 시작해보세요!")

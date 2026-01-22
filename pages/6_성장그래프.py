# pages/6_성장그래프.py
# 성장 그래프 - 간단하고 직관적인 대시보드

import os
import json
from datetime import datetime, timedelta
from collections import defaultdict
import streamlit as st

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 롤플레잉 시나리오 (ID -> 한국어 제목 변환용)
try:
    from roleplay_scenarios import SCENARIOS as RP_SCENARIOS
    SCENARIOS_AVAILABLE = True
except ImportError:
    RP_SCENARIOS = {}
    SCENARIOS_AVAILABLE = False

st.set_page_config(
    page_title="성장 그래프",
    page_icon="📈",
    layout="wide"
)

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="성장 그래프")
except ImportError:
    pass


# =====================
# 데이터 로드
# =====================

DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRESS_FILE = os.path.join(DATA_DIR, "user_progress.json")
SCORES_FILE = os.path.join(DATA_DIR, "user_scores.json")
RP_FILE = os.path.join(DATA_DIR, "roleplay_progress.json")


def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return default


def get_scenario_title(scenario_id: str) -> str:
    """시나리오 ID를 한국어 제목으로 변환"""
    if SCENARIOS_AVAILABLE and scenario_id in RP_SCENARIOS:
        return RP_SCENARIOS[scenario_id].get("title", scenario_id)
    return scenario_id


def get_all_scores():
    """모든 점수 데이터 수집"""
    all_scores = []

    # user_scores.json
    scores_data = load_json(SCORES_FILE, {"scores": []})
    for s in scores_data.get("scores", []):
        all_scores.append({
            "date": s.get("date", ""),
            "type": s.get("type", "기타"),
            "score": s.get("score", 0),
            "detail": s.get("scenario", "")[:30]
        })

    # roleplay_progress.json
    rp_data = load_json(RP_FILE, {"history": []})
    for h in rp_data.get("history", []):
        timestamp = h.get("timestamp", "")
        date_str = timestamp[:10] if timestamp else ""
        scenario_id = h.get("scenario_id", "")
        all_scores.append({
            "date": date_str,
            "type": "롤플레잉",
            "score": h.get("score", 0),
            "detail": get_scenario_title(scenario_id)  # 한국어 제목으로 변환
        })

    # 날짜 순 정렬
    all_scores.sort(key=lambda x: x.get("date", ""))
    return all_scores


def get_practice_counts():
    """연습 횟수 통계"""
    progress = load_json(PROGRESS_FILE, {"practice_history": []})
    rp = load_json(RP_FILE, {"history": []})

    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    counts = {
        "total": len(rp.get("history", [])) + len(progress.get("practice_history", [])),
        "week": 0,
        "month": 0,
        "by_type": defaultdict(int),
        "by_date": defaultdict(int)
    }

    # 롤플레잉 기록
    for h in rp.get("history", []):
        timestamp = h.get("timestamp", "")
        if timestamp:
            date_str = timestamp[:10]
            counts["by_date"][date_str] += 1
            counts["by_type"]["롤플레잉"] += 1
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
                if d >= week_ago:
                    counts["week"] += 1
                if d >= month_ago:
                    counts["month"] += 1
            except:
                pass

    return counts


# =====================
# CSS
# =====================

st.markdown("""
<style>
.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 20px;
    color: white;
    text-align: center;
}
.stat-value {
    font-size: 2.5rem;
    font-weight: 800;
    line-height: 1.2;
}
.stat-label {
    font-size: 0.9rem;
    opacity: 0.9;
    margin-top: 5px;
}
.score-card {
    background: white;
    border-radius: 12px;
    padding: 15px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 10px;
}
.trend-up { color: #22c55e; }
.trend-down { color: #ef4444; }
</style>
""", unsafe_allow_html=True)


# =====================
# UI
# =====================

st.title("📈 성장 그래프")

# 데이터 로드
all_scores = get_all_scores()
counts = get_practice_counts()
progress = load_json(PROGRESS_FILE, {})

# ========== 핵심 지표 (상단) ==========
st.markdown("### 📊 나의 학습 현황")

col1, col2, col3, col4 = st.columns(4)

# 총 연습
with col1:
    total = len(all_scores) if all_scores else 0
    st.metric("총 연습", f"{total}회")

# 이번 주
with col2:
    week_count = counts.get("week", 0)
    st.metric("이번 주", f"{week_count}회")

# 연속 학습
with col3:
    streak = progress.get("study_streak", 0)
    st.metric("연속 학습", f"{streak}일", delta="🔥" if streak >= 3 else None)

# 평균 점수
with col4:
    if all_scores:
        recent_scores = [s["score"] for s in all_scores[-10:] if s["score"] > 0]
        avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        st.metric("최근 평균", f"{avg:.0f}점")
    else:
        st.metric("최근 평균", "-")

st.markdown("---")

# ========== 점수 추이 그래프 ==========
if all_scores and any(s["score"] > 0 for s in all_scores):
    st.markdown("### 📈 점수 추이")

    # 최근 20개 점수
    recent = [s for s in all_scores if s["score"] > 0][-20:]

    if recent:
        # 간단한 라인 차트
        chart_data = {
            "점수": [s["score"] for s in recent]
        }
        st.line_chart(chart_data, height=250)

        # 성장 분석
        if len(recent) >= 5:
            first_avg = sum(s["score"] for s in recent[:5]) / 5
            last_avg = sum(s["score"] for s in recent[-5:]) / 5
            growth = last_avg - first_avg

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("처음 평균", f"{first_avg:.0f}점")
            with col2:
                st.metric("최근 평균", f"{last_avg:.0f}점")
            with col3:
                if growth > 0:
                    st.metric("성장", f"+{growth:.0f}점", delta="상승")
                elif growth < 0:
                    st.metric("성장", f"{growth:.0f}점", delta="하락", delta_color="inverse")
                else:
                    st.metric("성장", "0점")

            # 성장 메시지
            if growth >= 10:
                st.success("🎉 대단해요! 크게 성장했습니다!")
            elif growth >= 5:
                st.success("📈 꾸준히 성장하고 있어요!")
            elif growth >= 0:
                st.info("💪 꾸준히 연습하면 점수가 오를 거예요!")
            else:
                st.warning("📚 복습이 필요해 보여요. 힘내세요!")

    st.markdown("---")

# ========== 유형별 점수 ==========
st.markdown("### 🎯 유형별 현황")

# 유형별 집계
type_stats = defaultdict(lambda: {"count": 0, "scores": []})
for s in all_scores:
    t = s.get("type", "기타")
    type_stats[t]["count"] += 1
    if s["score"] > 0:
        type_stats[t]["scores"].append(s["score"])

if type_stats:
    cols = st.columns(min(len(type_stats), 4))

    for idx, (type_name, data) in enumerate(type_stats.items()):
        with cols[idx % len(cols)]:
            count = data["count"]
            scores = data["scores"]
            avg = sum(scores) / len(scores) if scores else 0

            # 색상 결정
            if avg >= 80:
                color = "🟢"
            elif avg >= 60:
                color = "🟡"
            elif avg > 0:
                color = "🔴"
            else:
                color = "⚪"

            st.markdown(f"**{type_name}**")
            st.write(f"{color} {count}회 연습")
            if avg > 0:
                st.write(f"평균 **{avg:.0f}점**")
            else:
                st.write("점수 없음")
else:
    st.info("아직 연습 기록이 없습니다.")

st.markdown("---")

# ========== 최근 기록 ==========
st.markdown("### 📋 최근 기록")

if all_scores:
    # 최근 10개
    recent_10 = list(reversed(all_scores[-10:]))

    for record in recent_10:
        score = record.get("score", 0)
        date = record.get("date", "")[-5:]  # MM-DD
        type_name = record.get("type", "기타")
        detail = record.get("detail", "")

        col1, col2, col3, col4 = st.columns([1.5, 2, 1.5, 3])

        with col1:
            st.write(date)
        with col2:
            st.write(type_name)
        with col3:
            if score >= 80:
                st.success(f"{score}점")
            elif score >= 60:
                st.warning(f"{score}점")
            elif score > 0:
                st.error(f"{score}점")
            else:
                st.write("-")
        with col4:
            st.caption(detail if detail else "-")
else:
    st.info("연습을 시작하면 여기에 기록이 표시됩니다!")

st.markdown("---")

# ========== 빠른 시작 ==========
st.markdown("### ⚡ 바로 연습하기")

col1, col2, col3 = st.columns(3)

with col1:
    st.page_link("pages/4_모의면접.py", label="🎤 모의면접", use_container_width=True)
with col2:
    st.page_link("pages/1_롤플레잉.py", label="🎭 롤플레잉", use_container_width=True)
with col3:
    st.page_link("pages/2_영어면접.py", label="🌍 영어면접", use_container_width=True)

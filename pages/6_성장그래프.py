# pages/6_성장그래프.py
# 성장 그래프 - 종합 대시보드 (Premium 기능 포함)

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
    from roleplay_scenarios import SCENARIOS as RP_SCENARIOS
    SCENARIOS_AVAILABLE = True
except ImportError:
    RP_SCENARIOS = {}
    SCENARIOS_AVAILABLE = False

# PDF 리포트
try:
    from growth_report import generate_growth_report, get_growth_report_filename
    GROWTH_REPORT_AVAILABLE = True
except ImportError:
    GROWTH_REPORT_AVAILABLE = False

from sidebar_common import init_page, end_page

# 공용 유틸리티 (Stage 2)
try:
    from shared_utils import get_api_key, load_json, save_json
except ImportError:
    pass

# Initialize page with new layout
init_page(
    title="성장 그래프",
    current_page="성장그래프",
    wide_layout=True
)



# =====================
# 데이터 로드
# =====================

DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRESS_FILE = os.path.join(DATA_DIR, "user_progress.json")
SCORES_FILE = os.path.join(DATA_DIR, "user_scores.json")
RP_FILE = os.path.join(DATA_DIR, "roleplay_progress.json")
GOALS_FILE = os.path.join(DATA_DIR, "user_goals.json")


def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"JSON 로드 실패 ({filepath}): {e}")
    return default


def save_json(filepath, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.warning(f"JSON 저장 실패 ({filepath}): {e}")
        return False


def get_scenario_title(scenario_id: str) -> str:
    if SCENARIOS_AVAILABLE and scenario_id in RP_SCENARIOS:
        return RP_SCENARIOS[scenario_id].get("title", scenario_id)
    return scenario_id


def get_all_scores():
    """모든 점수 데이터 수집"""
    all_scores = []

    # user_scores.json
    scores_data = load_json(SCORES_FILE, {"scores": [], "detailed_scores": []})
    for s in scores_data.get("scores", []):
        all_scores.append({
            "date": s.get("date", ""),
            "time": s.get("time", ""),
            "type": s.get("type", "기타"),
            "score": s.get("score", 0),
            "detail": s.get("scenario", "")[:50]
        })

    # roleplay_progress.json
    rp_data = load_json(RP_FILE, {"history": []})
    for h in rp_data.get("history", []):
        timestamp = h.get("timestamp", "")
        date_str = timestamp[:10] if timestamp else ""
        time_str = timestamp[11:16] if len(timestamp) > 11 else ""
        scenario_id = h.get("scenario_id", "")
        all_scores.append({
            "date": date_str,
            "time": time_str,
            "type": "롤플레잉",
            "score": h.get("score", 0),
            "detail": get_scenario_title(scenario_id)
        })

    all_scores.sort(key=lambda x: (x.get("date", ""), x.get("time", "")))
    return all_scores


def get_detailed_scores():
    """세부 점수 데이터"""
    scores_data = load_json(SCORES_FILE, {"detailed_scores": []})
    return scores_data.get("detailed_scores", [])


def calculate_skill_scores(detailed_scores):
    """스킬별 평균 점수 계산"""
    skill_totals = defaultdict(lambda: {"sum": 0, "count": 0})

    # 스킬 매핑 (쉬운 한국어)
    skill_map = {
        # 롤플레잉/모의면접
        "empathy": "승객 공감하기",
        "solution": "문제 해결력",
        "professionalism": "프로다운 응대",
        "attitude": "서비스 태도",
        "communication": "말하기 능력",
        # 영어면접
        "grammar": "영어 문법",
        "fluency": "영어 유창성",
        "pronunciation": "영어 발음",
        "vocabulary": "영어 어휘",
        "content": "답변 내용",
        # 토론면접
        "logic": "논리적 말하기",
        "listening": "상대방 경청",
        "expression": "생각 표현력",
        "leadership": "토론 리드",
        # 추가 항목
        "service_tone": "서비스 말투",
        "clarity": "발음 명확성",
        "confidence": "자신감",
        "structure": "답변 구성력",
    }

    for ds in detailed_scores:
        scores = ds.get("scores", {})
        for key, value in scores.items():
            if isinstance(value, (int, float)) and value > 0:
                skill_name = skill_map.get(key, key)
                skill_totals[skill_name]["sum"] += value
                skill_totals[skill_name]["count"] += 1

    result = {}
    for skill, data in skill_totals.items():
        if data["count"] > 0:
            result[skill] = round(data["sum"] / data["count"], 1)

    return result


def get_streak_count():
    """연속 학습일 계산"""
    all_scores = get_all_scores()
    if not all_scores:
        return 0

    dates = set()
    for s in all_scores:
        if s.get("date"):
            dates.add(s["date"])

    if not dates:
        return 0

    today = datetime.now().date()
    streak = 0
    check_date = today

    while True:
        date_str = check_date.strftime("%Y-%m-%d")
        if date_str in dates:
            streak += 1
            check_date -= timedelta(days=1)
        elif check_date == today:
            check_date -= timedelta(days=1)
        else:
            break

    return streak


def get_weekly_comparison():
    """이번주 vs 저번주 비교"""
    all_scores = get_all_scores()
    today = datetime.now().date()

    this_week_start = today - timedelta(days=today.weekday())
    last_week_start = this_week_start - timedelta(days=7)
    last_week_end = this_week_start - timedelta(days=1)

    this_week = {"count": 0, "scores": []}
    last_week = {"count": 0, "scores": []}

    for s in all_scores:
        try:
            d = datetime.strptime(s["date"], "%Y-%m-%d").date()
            if d >= this_week_start:
                this_week["count"] += 1
                if s["score"] > 0:
                    this_week["scores"].append(s["score"])
            elif last_week_start <= d <= last_week_end:
                last_week["count"] += 1
                if s["score"] > 0:
                    last_week["scores"].append(s["score"])
        except (ValueError, KeyError, TypeError) as e:
            logger.warning(f"주간 통계 처리 중 데이터 오류: {e}")
            continue

    this_avg = sum(this_week["scores"]) / len(this_week["scores"]) if this_week["scores"] else 0
    last_avg = sum(last_week["scores"]) / len(last_week["scores"]) if last_week["scores"] else 0

    return {
        "this_week": {"count": this_week["count"], "avg": this_avg},
        "last_week": {"count": last_week["count"], "avg": last_avg},
    }


def get_heatmap_data():
    """히트맵 데이터 (최근 12주)"""
    all_scores = get_all_scores()
    date_counts = defaultdict(int)

    for s in all_scores:
        if s.get("date"):
            date_counts[s["date"]] += 1

    today = datetime.now().date()
    data = []

    for i in range(84):  # 12주 = 84일
        d = today - timedelta(days=83 - i)
        date_str = d.strftime("%Y-%m-%d")
        data.append({
            "date": date_str,
            "weekday": d.weekday(),
            "week": i // 7,
            "count": date_counts.get(date_str, 0)
        })

    return data


def generate_ai_insights(all_scores, skill_scores, weekly_comp):
    """AI 인사이트 생성 - 친근한 한국어"""
    insights = []

    # 1. 연습량 분석
    this_count = weekly_comp["this_week"]["count"]
    last_count = weekly_comp["last_week"]["count"]

    if this_count > last_count:
        diff = this_count - last_count
        insights.append({
            "type": "positive",
            "title": "연습량 UP!",
            "message": f"이번 주에 지난주보다 {diff}번 더 연습했어요. 이 페이스 유지해요!"
        })
    elif this_count < last_count and last_count > 0:
        insights.append({
            "type": "warning",
            "title": "조금 쉬었나요?",
            "message": "이번 주 연습이 줄었어요. 하루 1번이라도 꾸준히 해봐요!"
        })
    elif this_count == 0:
        insights.append({
            "type": "warning",
            "title": "이번 주 시작해볼까요?",
            "message": "아직 이번 주 연습을 안 했어요. 지금 바로 시작해보세요!"
        })

    # 2. 점수 추이 분석
    if weekly_comp["this_week"]["avg"] > 0 and weekly_comp["last_week"]["avg"] > 0:
        diff = weekly_comp["this_week"]["avg"] - weekly_comp["last_week"]["avg"]
        if diff >= 5:
            insights.append({
                "type": "positive",
                "title": "실력이 늘었어요!",
                "message": f"평균 점수가 {diff:.0f}점이나 올랐어요. 열심히 한 보람이 있네요!"
            })
        elif diff <= -5:
            insights.append({
                "type": "warning",
                "title": "점수가 조금 떨어졌어요",
                "message": "걱정 마세요! 어려운 문제에 도전한 거예요. 복습하면 금방 올라요."
            })

    # 3. 약점 분석
    if skill_scores:
        weak_skills = [k for k, v in skill_scores.items() if v < 70]
        if weak_skills:
            weak_text = weak_skills[0] if len(weak_skills) == 1 else f"{weak_skills[0]}, {weak_skills[1]}"
            insights.append({
                "type": "info",
                "title": "여기 집중하면 좋겠어요",
                "message": f"'{weak_text}' 부분을 더 연습하면 점수가 확 오를 거예요!"
            })

        strong_skills = [k for k, v in skill_scores.items() if v >= 85]
        if strong_skills:
            strong_text = strong_skills[0]
            insights.append({
                "type": "positive",
                "title": "이건 진짜 잘해요!",
                "message": f"'{strong_text}' 점수가 높아요! 면접에서 이 강점을 어필하세요."
            })

    # 4. 유형별 분석
    type_counts = defaultdict(int)
    for s in all_scores:
        type_counts[s.get("type", "기타")] += 1

    if type_counts:
        practiced_types = set(type_counts.keys())
        all_types = {"롤플레잉", "영어면접", "모의면접", "토론면접"}
        missing = all_types - practiced_types
        if missing:
            missing_text = list(missing)[0]
            insights.append({
                "type": "info",
                "title": "이것도 해보세요",
                "message": f"'{missing_text}'은 아직 안 해봤죠? 실제 면접은 다양하니까 한번 도전해봐요!"
            })

    # 5. 연속 학습 격려
    streak = get_streak_count() if 'get_streak_count' in dir() else 0
    if streak >= 7:
        insights.append({
            "type": "positive",
            "title": "일주일 연속 학습!",
            "message": f"{streak}일 연속으로 공부하고 있어요. 대단해요! 이 습관이 합격을 만들어요."
        })
    elif streak >= 3:
        insights.append({
            "type": "positive",
            "title": "꾸준함이 보여요",
            "message": f"{streak}일 연속 학습 중! 조금만 더 하면 일주일이에요. 파이팅!"
        })

    # 기본 인사이트
    if not insights:
        insights.append({
            "type": "info",
            "title": "시작이 반이에요!",
            "message": "연습을 더 하면 나만의 분석 리포트를 보여드릴게요. 화이팅!"
        })

    return insights


# =====================
# CSS
# =====================

st.markdown("""
<style>
/* 메인 스탯 카드 */
.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 20px;
    padding: 25px;
    color: white;
    text-align: center;
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    transition: transform 0.3s ease;
}
.stat-card:hover {
    transform: translateY(-5px);
}
.stat-card.green {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    box-shadow: 0 10px 30px rgba(17, 153, 142, 0.3);
}
.stat-card.orange {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    box-shadow: 0 10px 30px rgba(245, 87, 108, 0.3);
}
.stat-card.blue {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    box-shadow: 0 10px 30px rgba(79, 172, 254, 0.3);
}
.stat-value {
    font-size: 3rem;
    font-weight: 800;
    line-height: 1.2;
    text-shadow: 0 2px 10px rgba(0,0,0,0.2);
}
.stat-label {
    font-size: 1rem;
    opacity: 0.95;
    margin-top: 8px;
    font-weight: 500;
}
.stat-delta {
    font-size: 0.85rem;
    margin-top: 5px;
    opacity: 0.9;
}

/* 히트맵 */
.heatmap-container {
    display: flex;
    gap: 3px;
    flex-wrap: wrap;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 12px;
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

/* 인사이트 카드 */
.insight-card {
    padding: 16px 20px;
    border-radius: 12px;
    margin-bottom: 12px;
    border-left: 4px solid;
}
.insight-positive {
    background: #ecfdf5;
    border-color: #10b981;
}
.insight-warning {
    background: #fffbeb;
    border-color: #f59e0b;
}
.insight-info {
    background: #eff6ff;
    border-color: #3b82f6;
}
.insight-title {
    font-weight: 700;
    font-size: 1rem;
    margin-bottom: 4px;
}
.insight-message {
    color: #4b5563;
    font-size: 0.9rem;
}

/* 프리미엄 배지 */
.premium-badge {
    background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
    color: #000;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 700;
    margin-left: 8px;
}

/* 레이더 차트 컨테이너 */
.radar-container {
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
}

/* 기록 테이블 */
.record-row {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    background: white;
    border-radius: 10px;
    margin-bottom: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    transition: all 0.2s ease;
}
.record-row:hover {
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    transform: translateX(5px);
}

/* 목표 프로그레스 */
.goal-progress {
    height: 12px;
    background: #e5e7eb;
    border-radius: 6px;
    overflow: hidden;
}
.goal-progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    border-radius: 6px;
    transition: width 0.5s ease;
}
</style>
""", unsafe_allow_html=True)


# =====================
# UI
# =====================

st.title("성장 그래프")
st.caption("나의 면접 준비 현황을 한눈에 확인하세요")

# 데이터 로드
all_scores = get_all_scores()
detailed_scores = get_detailed_scores()
skill_scores = calculate_skill_scores(detailed_scores)
streak = get_streak_count()
weekly_comp = get_weekly_comparison()
heatmap_data = get_heatmap_data()
goals_data = load_json(GOALS_FILE, {"weekly_goal": 10, "score_goal": 80})

# ========== 핵심 지표 카드 ==========
st.markdown("### 나의 학습 현황")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total = len(all_scores)
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value">{total}</div>
        <div class="stat-label">총 연습 횟수</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    week_count = weekly_comp["this_week"]["count"]
    last_week = weekly_comp["last_week"]["count"]
    delta = week_count - last_week
    delta_text = f"+{delta}" if delta > 0 else str(delta)
    st.markdown(f"""
    <div class="stat-card green">
        <div class="stat-value">{week_count}</div>
        <div class="stat-label">이번 주 연습</div>
        <div class="stat-delta">{delta_text} vs 지난주</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    fire = "" if streak >= 3 else ""
    st.markdown(f"""
    <div class="stat-card orange">
        <div class="stat-value">{streak}{fire}</div>
        <div class="stat-label">연속 학습일</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    recent_scores = [s["score"] for s in all_scores[-20:] if s["score"] > 0]
    avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
    st.markdown(f"""
    <div class="stat-card blue">
        <div class="stat-value">{avg:.0f}</div>
        <div class="stat-label">최근 평균 점수</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ========== 메인 콘텐츠 (2열) ==========
left_col, right_col = st.columns([2, 1])

with left_col:
    # 점수 추이 그래프
    st.markdown("### 점수 추이")

    # 필터
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        date_range = st.selectbox(
            "기간",
            ["최근 2주", "최근 1개월", "최근 3개월", "전체"],
            index=1,
            label_visibility="collapsed"
        )
    with filter_col2:
        type_filter = st.selectbox(
            "유형",
            ["전체"] + list(set(s["type"] for s in all_scores)),
            label_visibility="collapsed"
        )

    # 필터링
    filtered_scores = all_scores.copy()

    if type_filter != "전체":
        filtered_scores = [s for s in filtered_scores if s["type"] == type_filter]

    today = datetime.now().date()
    if date_range == "최근 2주":
        cutoff = today - timedelta(days=14)
    elif date_range == "최근 1개월":
        cutoff = today - timedelta(days=30)
    elif date_range == "최근 3개월":
        cutoff = today - timedelta(days=90)
    else:
        cutoff = None

    if cutoff:
        filtered_scores = [
            s for s in filtered_scores
            if s["date"] and datetime.strptime(s["date"], "%Y-%m-%d").date() >= cutoff
        ]

    # 그래프
    if filtered_scores and any(s["score"] > 0 for s in filtered_scores):
        scored = [s for s in filtered_scores if s["score"] > 0]

        # Plotly 사용 시도
        try:
            import plotly.express as px
            import plotly.graph_objects as go

            dates = [s["date"] for s in scored]
            scores = [s["score"] for s in scored]
            types = [s["type"] for s in scored]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(len(scores))),
                y=scores,
                mode='lines+markers',
                name='점수',
                line=dict(color='#667eea', width=3),
                marker=dict(size=8, color='#667eea'),
                hovertemplate='%{y}점<br>%{text}<extra></extra>',
                text=[f"{d}<br>{t}" for d, t in zip(dates, types)]
            ))

            # 평균선
            avg_score = sum(scores) / len(scores)
            fig.add_hline(y=avg_score, line_dash="dash", line_color="#f59e0b",
                         annotation_text=f"평균 {avg_score:.0f}점")

            fig.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis=dict(showticklabels=False, showgrid=False),
                yaxis=dict(range=[0, 105], gridcolor='#f0f0f0'),
                plot_bgcolor='white',
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

        except ImportError:
            # Fallback to st.line_chart
            chart_data = {"점수": [s["score"] for s in scored]}
            st.line_chart(chart_data, height=250)

        # 성장 분석
        if len(scored) >= 6:
            first_half = scored[:len(scored)//2]
            second_half = scored[len(scored)//2:]

            first_avg = sum(s["score"] for s in first_half) / len(first_half)
            second_avg = sum(s["score"] for s in second_half) / len(second_half)
            growth = second_avg - first_avg

            growth_col1, growth_col2, growth_col3 = st.columns(3)
            with growth_col1:
                st.metric("처음 평균", f"{first_avg:.0f}점")
            with growth_col2:
                st.metric("최근 평균", f"{second_avg:.0f}점")
            with growth_col3:
                delta_text = "상승" if growth > 0 else "하락" if growth < 0 else ""
                st.metric("성장", f"{growth:+.0f}점", delta=delta_text)
    else:
        st.info("선택한 기간/유형에 점수 기록이 없습니다.")

    st.markdown("---")

    # 학습 캘린더 히트맵
    st.markdown("### 학습 캘린더")

    # 히트맵 그리기
    heatmap_html = '<div class="heatmap-container">'
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]

    # 요일 헤더
    for wd in weekdays:
        heatmap_html += f'<div style="width:14px;height:14px;text-align:center;font-size:10px;color:#666;">{wd}</div>'

    for cell in heatmap_data:
        count = cell["count"]
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

        date_str = cell["date"]
        heatmap_html += f'<div class="heatmap-cell {level}" title="{date_str}: {count}회"></div>'

    heatmap_html += '</div>'

    # 범례
    heatmap_html += '''
    <div style="display:flex;align-items:center;gap:5px;margin-top:10px;font-size:12px;color:#666;">
        <span>적음</span>
        <div style="width:14px;height:14px;background:#ebedf0;border-radius:3px;"></div>
        <div style="width:14px;height:14px;background:#9be9a8;border-radius:3px;"></div>
        <div style="width:14px;height:14px;background:#40c463;border-radius:3px;"></div>
        <div style="width:14px;height:14px;background:#30a14e;border-radius:3px;"></div>
        <div style="width:14px;height:14px;background:#216e39;border-radius:3px;"></div>
        <span>많음</span>
    </div>
    '''

    st.markdown(heatmap_html, unsafe_allow_html=True)


with right_col:
    # AI 인사이트
    st.markdown("### 오늘의 조언")

    insights = generate_ai_insights(all_scores, skill_scores, weekly_comp)

    for insight in insights[:4]:
        insight_type = insight["type"]
        st.markdown(f"""
        <div class="insight-card insight-{insight_type}">
            <div class="insight-title">{insight["title"]}</div>
            <div class="insight-message">{insight["message"]}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 주간 목표
    st.markdown("### 주간 목표")

    weekly_goal = goals_data.get("weekly_goal", 10)
    current_week = weekly_comp["this_week"]["count"]
    progress_pct = min(100, (current_week / weekly_goal) * 100) if weekly_goal > 0 else 0

    st.markdown(f"**{current_week} / {weekly_goal}회** 달성")
    st.markdown(f"""
    <div class="goal-progress">
        <div class="goal-progress-bar" style="width: {progress_pct}%;"></div>
    </div>
    """, unsafe_allow_html=True)

    if progress_pct >= 100:
        st.success("목표 달성!")
    elif progress_pct >= 70:
        st.info(f" {weekly_goal - current_week}회 더!")
    else:
        st.warning(f" {weekly_goal - current_week}회 남음")

    # 목표 설정
    with st.expander("목표 수정"):
        new_goal = st.number_input("주간 연습 목표", min_value=1, max_value=50, value=weekly_goal)
        if st.button("저장", use_container_width=True):
            goals_data["weekly_goal"] = new_goal
            save_json(GOALS_FILE, goals_data)
            st.success("저장됨!")
            st.rerun()

st.markdown("---")

# ========== 스킬 분석 ==========
st.markdown("### 내가 잘하는 것 / 더 연습할 것")

if skill_scores:
    skill_col1, skill_col2 = st.columns([1, 1])

    with skill_col1:
        # 레이더 차트 시도
        try:
            import plotly.graph_objects as go

            skills = list(skill_scores.keys())[:8]
            values = [skill_scores[s] for s in skills]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],
                theta=skills + [skills[0]],
                fill='toself',
                fillcolor='rgba(102, 126, 234, 0.3)',
                line=dict(color='#667eea', width=2),
                name='내 점수'
            ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100]),
                    bgcolor='white'
                ),
                showlegend=False,
                height=350,
                margin=dict(l=60, r=60, t=30, b=30)
            )

            st.plotly_chart(fig, use_container_width=True)

        except ImportError:
            # Fallback: 바 형식으로 표시
            for skill, score in skill_scores.items():
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.progress(score / 100)
                with col_b:
                    st.write(f"{skill}: {score:.0f}")

    with skill_col2:
        st.markdown("**항목별 점수**")

        sorted_skills = sorted(skill_scores.items(), key=lambda x: x[1], reverse=True)

        for skill, score in sorted_skills:
            if score >= 85:
                icon = ""
                status = "아주 잘하고 있어요!"
            elif score >= 70:
                icon = ""
                status = "괜찮아요, 조금만 더!"
            else:
                icon = ""
                status = "집중 연습 필요"

            st.markdown(f"{icon} **{skill}**: {score:.0f}점 _{status}_")

        # 강점/약점 요약
        if sorted_skills:
            st.markdown("---")
            strongest = sorted_skills[0]
            weakest = sorted_skills[-1]
            st.success(f" 가장 잘하는 것: **{strongest[0]}** ({strongest[1]:.0f}점)")
            if weakest[1] < 70:
                st.warning(f" 더 연습하면 좋을 것: **{weakest[0]}** ({weakest[1]:.0f}점)")
else:
    st.info("연습을 더 하면 내가 뭘 잘하고, 뭘 더 연습해야 하는지 분석해드려요!")

st.markdown("---")

# ========== 유형별 현황 ==========
st.markdown("### 유형별 현황")

type_stats = defaultdict(lambda: {"count": 0, "scores": [], "recent": None})
for s in all_scores:
    t = s.get("type", "기타")
    type_stats[t]["count"] += 1
    if s["score"] > 0:
        type_stats[t]["scores"].append(s["score"])
    type_stats[t]["recent"] = s["date"]

if type_stats:
    type_cols = st.columns(min(len(type_stats), 4))

    type_icons = {
        "롤플레잉": "",
        "영어면접": "",
        "모의면접": "",
        "토론면접": "",
        "기타": ""
    }

    for idx, (type_name, data) in enumerate(type_stats.items()):
        with type_cols[idx % len(type_cols)]:
            count = data["count"]
            scores = data["scores"]
            avg = sum(scores) / len(scores) if scores else 0
            icon = type_icons.get(type_name, "")

            # 상태 색상
            if avg >= 80:
                status_color = "#10b981"
            elif avg >= 60:
                status_color = "#f59e0b"
            elif avg > 0:
                status_color = "#ef4444"
            else:
                status_color = "#6b7280"

            st.markdown(f"""
            <div style="
                background: white;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                border-top: 4px solid {status_color};
            ">
                <div style="font-size: 2rem;">{icon}</div>
                <div style="font-weight: 700; margin: 8px 0;">{type_name}</div>
                <div style="font-size: 1.5rem; color: {status_color};">{count}회</div>
                <div style="color: #666; font-size: 0.9rem;">평균 {avg:.0f}점</div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("연습 기록이 없습니다.")

st.markdown("---")

# ========== 최근 기록 ==========
st.markdown("### 최근 기록")

if all_scores:
    recent_records = list(reversed(all_scores[-15:]))

    for record in recent_records:
        score = record.get("score", 0)
        date = record.get("date", "")
        time_str = record.get("time", "")
        type_name = record.get("type", "기타")
        detail = record.get("detail", "")

        # 점수 색상
        if score >= 80:
            score_color = "#10b981"
            score_bg = "#ecfdf5"
        elif score >= 60:
            score_color = "#f59e0b"
            score_bg = "#fffbeb"
        elif score > 0:
            score_color = "#ef4444"
            score_bg = "#fef2f2"
        else:
            score_color = "#6b7280"
            score_bg = "#f9fafb"

        type_icon = {"롤플레잉": "", "영어면접": "", "모의면접": "", "토론면접": ""}.get(type_name, "")

        st.markdown(f"""
        <div class="record-row">
            <div style="width: 80px; color: #666; font-size: 0.85rem;">{date[5:] if date else "-"}</div>
            <div style="width: 100px;">{type_icon} {type_name}</div>
            <div style="
                width: 60px;
                background: {score_bg};
                color: {score_color};
                padding: 4px 10px;
                border-radius: 8px;
                font-weight: 700;
                text-align: center;
            ">{score if score > 0 else "-"}점</div>
            <div style="flex: 1; color: #666; margin-left: 15px; font-size: 0.9rem;">{detail if detail else "-"}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("연습을 시작하면 여기에 기록이 표시됩니다!")

st.markdown("---")

# ========== 프리미엄 기능 ==========
st.markdown("### ⭐ 리포트 다운로드")

report_col1, report_col2 = st.columns(2)

with report_col1:
    # PDF 리포트
    if GROWTH_REPORT_AVAILABLE and all_scores:
        try:
            pdf_bytes = generate_growth_report(
                all_scores=all_scores,
                skill_scores=skill_scores,
                weekly_comp=weekly_comp,
                insights=insights,
                streak=streak
            )
            filename = get_growth_report_filename()

            st.download_button(
                label= " 성장 리포트 (PDF)",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        except Exception as e:
            st.error(f"PDF 생성 오류: {e}")
    else:
        st.button("성장 리포트 (PDF)", disabled=True, use_container_width=True)
        st.caption("연습 기록이 있어야 다운로드 가능합니다")

with report_col2:
    # CSV 내보내기
    if all_scores:
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["날짜", "시간", "유형", "점수", "상세"])
        for s in all_scores:
            writer.writerow([s["date"], s["time"], s["type"], s["score"], s["detail"]])

        csv_data = output.getvalue()

        st.download_button(
            label= " 데이터 내보내기 (CSV)",
            data=csv_data,
            file_name=f"학습기록_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.button("데이터 내보내기 (CSV)", disabled=True, use_container_width=True)

st.markdown("---")

# ========== 빠른 시작 ==========
st.markdown("### 바로 연습하기")

quick_cols = st.columns(4)

with quick_cols[0]:
    st.page_link("pages/1_롤플레잉.py", label= " 롤플레잉", use_container_width=True)
with quick_cols[1]:
    st.page_link("pages/2_영어면접.py", label= " 영어면접", use_container_width=True)
with quick_cols[2]:
    st.page_link("pages/4_모의면접.py", label= " 모의면접", use_container_width=True)
with quick_cols[3]:
    st.page_link("pages/5_토론면접.py", label= " 토론면접", use_container_width=True)

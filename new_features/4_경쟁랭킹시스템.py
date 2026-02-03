# new_features/4_경쟁랭킹시스템.py
# FlyReady Lab - 경쟁 랭킹 시스템
# 다른 지원자들과 점수 비교, 동기부여

import os
import sys
import json
import random
from datetime import datetime, timedelta
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sidebar_common import init_page, end_page
from logging_config import get_logger

logger = get_logger(__name__)

# =====================
# 데이터 경로
# =====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RANKING_FILE = os.path.join(DATA_DIR, "rankings.json")
ACHIEVEMENTS_FILE = os.path.join(DATA_DIR, "achievements.json")


def load_rankings():
    """랭킹 데이터 로드"""
    try:
        if os.path.exists(RANKING_FILE):
            with open(RANKING_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"랭킹 로드 실패: {e}")
    return {"weekly": [], "monthly": [], "all_time": []}


def save_rankings(data):
    """랭킹 데이터 저장"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(RANKING_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"랭킹 저장 실패: {e}")


def load_achievements():
    """업적 데이터 로드"""
    try:
        if os.path.exists(ACHIEVEMENTS_FILE):
            with open(ACHIEVEMENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"업적 로드 실패: {e}")
    return {}


def save_achievements(data):
    """업적 데이터 저장"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(ACHIEVEMENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"업적 저장 실패: {e}")


# =====================
# 랭킹 시스템
# =====================

TIERS = {
    "bronze": {"name": "브론즈", "color": "#cd7f32", "min_score": 0, "icon": "🥉"},
    "silver": {"name": "실버", "color": "#c0c0c0", "min_score": 500, "icon": "🥈"},
    "gold": {"name": "골드", "color": "#ffd700", "min_score": 1500, "icon": "🥇"},
    "platinum": {"name": "플래티넘", "color": "#e5e4e2", "min_score": 3000, "icon": "💎"},
    "diamond": {"name": "다이아", "color": "#b9f2ff", "min_score": 5000, "icon": "💠"},
    "master": {"name": "마스터", "color": "#ff6b6b", "min_score": 10000, "icon": "👑"},
}

ACHIEVEMENTS = {
    "first_interview": {
        "name": "첫 발걸음",
        "description": "첫 모의면접 완료",
        "icon": "🎯",
        "points": 10,
    },
    "perfect_score": {
        "name": "완벽주의자",
        "description": "모의면접 100점 달성",
        "icon": "💯",
        "points": 100,
    },
    "streak_7": {
        "name": "일주일 연속",
        "description": "7일 연속 학습",
        "icon": "🔥",
        "points": 50,
    },
    "streak_30": {
        "name": "한 달 습관",
        "description": "30일 연속 학습",
        "icon": "🌟",
        "points": 200,
    },
    "quiz_master": {
        "name": "퀴즈왕",
        "description": "퀴즈 100문제 정답",
        "icon": "🧠",
        "points": 80,
    },
    "early_bird": {
        "name": "얼리버드",
        "description": "오전 6시 이전 학습",
        "icon": "🌅",
        "points": 30,
    },
    "night_owl": {
        "name": "올빼미",
        "description": "자정 이후 학습",
        "icon": "🦉",
        "points": 30,
    },
    "pressure_survivor": {
        "name": "압박 생존자",
        "description": "압박 면접 80점 이상",
        "icon": "💪",
        "points": 100,
    },
    "speed_demon": {
        "name": "스피드 마스터",
        "description": "타임어택 S랭크 달성",
        "icon": "⚡",
        "points": 80,
    },
    "all_airlines": {
        "name": "만능 지원자",
        "description": "모든 항공사 면접 경험",
        "icon": "✈️",
        "points": 150,
    },
}


def get_tier(total_points: int) -> dict:
    """포인트에 따른 티어 반환"""
    current_tier = TIERS["bronze"]
    for tier_key, tier_info in TIERS.items():
        if total_points >= tier_info["min_score"]:
            current_tier = {**tier_info, "key": tier_key}
    return current_tier


def calculate_percentile(user_score: int, all_scores: list) -> int:
    """상위 몇 %인지 계산"""
    if not all_scores:
        return 100
    scores_below = sum(1 for s in all_scores if s < user_score)
    percentile = 100 - int((scores_below / len(all_scores)) * 100)
    return max(1, min(100, percentile))


def generate_sample_rankings(count: int = 50) -> list:
    """샘플 랭킹 데이터 생성 (테스트용)"""
    names = [
        "하늘꿈", "승무원지망", "파랑새", "구름위에", "날개달기",
        "비행소녀", "에어라인", "캐빈크루", "스카이워커", "플라이투",
        "항공열정", "서비스왕", "미소천사", "글로벌인재", "예비승무원",
    ]

    rankings = []
    for i in range(count):
        score = random.randint(100, 5000)
        rankings.append({
            "rank": i + 1,
            "nickname": random.choice(names) + str(random.randint(1, 99)),
            "score": score,
            "tier": get_tier(score)["key"],
            "practice_count": random.randint(10, 200),
            "streak": random.randint(0, 30),
        })

    rankings.sort(key=lambda x: x["score"], reverse=True)
    for i, r in enumerate(rankings):
        r["rank"] = i + 1

    return rankings


# =====================
# UI
# =====================

def render_ranking_system():
    """랭킹 시스템 UI"""

    st.markdown("""
    <style>
    .ranking-header {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 24px;
        text-align: center;
    }
    .my-rank-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 24px;
    }
    .tier-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 1.1rem;
    }
    .rank-table {
        width: 100%;
        border-collapse: collapse;
    }
    .rank-table th, .rank-table td {
        padding: 12px 16px;
        text-align: left;
        border-bottom: 1px solid #e2e8f0;
    }
    .rank-table tr:hover {
        background: #f8fafc;
    }
    .rank-1 { color: #ffd700; font-weight: 800; }
    .rank-2 { color: #c0c0c0; font-weight: 700; }
    .rank-3 { color: #cd7f32; font-weight: 700; }
    .achievement-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        border: 2px solid #e2e8f0;
        transition: all 0.2s;
    }
    .achievement-card.unlocked {
        border-color: #10b981;
        background: #ecfdf5;
    }
    .achievement-card.locked {
        opacity: 0.5;
        filter: grayscale(1);
    }
    .achievement-icon {
        font-size: 2rem;
        margin-bottom: 8px;
    }
    .progress-ring {
        width: 120px;
        height: 120px;
        margin: 0 auto;
    }
    .leaderboard-row {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 12px 16px;
        background: white;
        border-radius: 8px;
        margin: 8px 0;
        border: 1px solid #e2e8f0;
    }
    .leaderboard-row.me {
        background: #eff6ff;
        border-color: #3b82f6;
    }
    </style>
    """, unsafe_allow_html=True)

    # 헤더
    st.markdown("""
    <div class="ranking-header">
        <h2 style="margin:0 0 8px 0;">🏆 경쟁 랭킹</h2>
        <p style="margin:0;opacity:0.9;">다른 지원자들과 실력을 비교해보세요</p>
    </div>
    """, unsafe_allow_html=True)

    # 내 정보 (세션에서 가져오기)
    user_id = st.session_state.get("user_id", "guest")
    my_nickname = st.session_state.get("nickname", "나")
    my_points = st.session_state.get("total_points", random.randint(500, 3000))  # 테스트용
    my_tier = get_tier(my_points)
    my_achievements = st.session_state.get("achievements", ["first_interview", "streak_7"])

    # 샘플 랭킹 데이터
    if "sample_rankings" not in st.session_state:
        st.session_state.sample_rankings = generate_sample_rankings(50)

    rankings = st.session_state.sample_rankings
    all_scores = [r["score"] for r in rankings]
    my_percentile = calculate_percentile(my_points, all_scores)

    # 탭
    tab1, tab2, tab3 = st.tabs(["내 순위", "전체 랭킹", "업적"])

    with tab1:
        # 내 순위 카드
        st.markdown(f"""
        <div class="my-rank-card">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;">
                <div>
                    <div style="font-size:0.9rem;color:#64748b;">내 티어</div>
                    <div class="tier-badge" style="background:{my_tier['color']}20;color:{my_tier['color']};">
                        {my_tier['icon']} {my_tier['name']}
                    </div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.9rem;color:#64748b;">총 포인트</div>
                    <div style="font-size:2rem;font-weight:800;color:#1e3a5f;">{my_points:,}</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.9rem;color:#64748b;">상위</div>
                    <div style="font-size:2rem;font-weight:800;color:#3b82f6;">{my_percentile}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 다음 티어까지
        next_tier = None
        for tier_key, tier_info in TIERS.items():
            if tier_info["min_score"] > my_points:
                next_tier = tier_info
                break

        if next_tier:
            points_needed = next_tier["min_score"] - my_points
            progress = (my_points - my_tier["min_score"]) / (next_tier["min_score"] - my_tier["min_score"])

            st.markdown(f"### 다음 티어: {next_tier['icon']} {next_tier['name']}")
            st.progress(progress)
            st.caption(f"{points_needed:,}포인트 더 필요")
        else:
            st.success("🎉 최고 티어 달성!")

        # 최근 활동
        st.markdown("### 최근 활동으로 얻은 포인트")

        recent_activities = [
            {"activity": "모의면접 완료", "points": 50, "date": "오늘"},
            {"activity": "퀴즈 10문제 정답", "points": 20, "date": "오늘"},
            {"activity": "연속 학습 보너스", "points": 30, "date": "어제"},
            {"activity": "자소서 첨삭 완료", "points": 40, "date": "2일 전"},
        ]

        for activity in recent_activities:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{activity['activity']}** ({activity['date']})")
            with col2:
                st.markdown(f"<span style='color:#10b981;font-weight:700;'>+{activity['points']}</span>",
                           unsafe_allow_html=True)

    with tab2:
        # 기간 선택
        period = st.radio(
            "기간",
            ["이번 주", "이번 달", "전체"],
            horizontal=True
        )

        # 랭킹 테이블
        st.markdown("### 🏅 리더보드")

        for i, entry in enumerate(rankings[:20]):
            is_me = entry["nickname"] == my_nickname
            tier = TIERS.get(entry["tier"], TIERS["bronze"])

            rank_class = ""
            if entry["rank"] == 1:
                rank_class = "rank-1"
            elif entry["rank"] == 2:
                rank_class = "rank-2"
            elif entry["rank"] == 3:
                rank_class = "rank-3"

            row_class = "me" if is_me else ""

            st.markdown(f"""
            <div class="leaderboard-row {row_class}">
                <div style="width:40px;text-align:center;" class="{rank_class}">
                    {"🥇" if entry["rank"] == 1 else "🥈" if entry["rank"] == 2 else "🥉" if entry["rank"] == 3 else entry["rank"]}
                </div>
                <div style="flex:1;">
                    <span style="font-weight:600;">{entry['nickname']}</span>
                    <span style="margin-left:8px;">{tier['icon']}</span>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:700;color:#1e3a5f;">{entry['score']:,}</div>
                    <div style="font-size:0.75rem;color:#64748b;">연습 {entry['practice_count']}회</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 내 순위 (20위 밖이면)
        my_rank = len([r for r in rankings if r["score"] > my_points]) + 1
        if my_rank > 20:
            st.markdown("---")
            st.markdown(f"""
            <div class="leaderboard-row me">
                <div style="width:40px;text-align:center;font-weight:700;">{my_rank}</div>
                <div style="flex:1;">
                    <span style="font-weight:600;">{my_nickname}</span>
                    <span style="margin-left:8px;">{my_tier['icon']}</span>
                    <span style="margin-left:4px;color:#3b82f6;">(나)</span>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:700;color:#1e3a5f;">{my_points:,}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.markdown("### 🏅 업적")
        st.caption("업적을 달성하고 포인트를 획득하세요!")

        # 업적 그리드
        cols = st.columns(3)

        for i, (ach_key, ach_info) in enumerate(ACHIEVEMENTS.items()):
            unlocked = ach_key in my_achievements

            with cols[i % 3]:
                status_class = "unlocked" if unlocked else "locked"
                st.markdown(f"""
                <div class="achievement-card {status_class}">
                    <div class="achievement-icon">{ach_info['icon']}</div>
                    <div style="font-weight:700;color:#1e3a5f;">{ach_info['name']}</div>
                    <div style="font-size:0.8rem;color:#64748b;margin:8px 0;">{ach_info['description']}</div>
                    <div style="font-size:0.9rem;color:#10b981;font-weight:600;">+{ach_info['points']} 포인트</div>
                </div>
                """, unsafe_allow_html=True)
                st.write("")

        # 업적 통계
        st.markdown("---")
        unlocked_count = len(my_achievements)
        total_count = len(ACHIEVEMENTS)
        unlocked_points = sum(ACHIEVEMENTS[a]["points"] for a in my_achievements if a in ACHIEVEMENTS)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("달성 업적", f"{unlocked_count}/{total_count}")
        with col2:
            st.metric("업적 포인트", f"{unlocked_points}")
        with col3:
            completion = int((unlocked_count / total_count) * 100)
            st.metric("완료율", f"{completion}%")


# 메인 실행
if __name__ == "__main__":
    render_ranking_system()

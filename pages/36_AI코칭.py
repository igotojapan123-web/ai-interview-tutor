# pages/36_AI코칭.py
# FlyReady Lab - AI 1:1 코칭 대시보드
# Phase 4 모듈 통합: ai_coach, learning_path, progress_tracker

import streamlit as st
import os
import sys
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# 상위 디렉토리 import 설정
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 페이지 설정
st.set_page_config(
    page_title="AI 1:1 코칭 - FlyReady Lab",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 로깅 설정
try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Phase 4 모듈 import
try:
    from ai_coach import (
        analyze_weaknesses,
        generate_coaching_feedback,
        get_focus_areas_for_today,
        get_daily_coaching_summary,
        get_weekly_coaching_report,
        generate_practice_tips,
        get_pre_interview_tips,
        SKILL_NAMES_KR,
    )
    AI_COACH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ai_coach 모듈 로드 실패: {e}")
    AI_COACH_AVAILABLE = False

try:
    from learning_path import (
        get_user_stage,
        get_recommended_modules,
        create_daily_plan,
        create_weekly_plan,
        get_review_items,
        get_wrong_answers,
        add_wrong_answer,
        mark_mastered,
        check_milestone_completion,
        get_next_milestone,
        get_learning_summary,
        get_stage_requirements,
        LEARNING_STAGES,
        LEARNING_MODULES,
    )
    LEARNING_PATH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"learning_path 모듈 로드 실패: {e}")
    LEARNING_PATH_AVAILABLE = False

try:
    from progress_tracker import (
        get_skill_radar_chart_data,
        get_practice_statistics,
        get_improvement_rate,
        check_daily_goal,
        set_daily_goal,
        get_goal_streak,
        get_weekly_goal_completion,
        get_score_trend,
        compare_with_previous_week,
    )
    PROGRESS_TRACKER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"progress_tracker 모듈 로드 실패: {e}")
    PROGRESS_TRACKER_AVAILABLE = False

try:
    from benchmark_service import get_achievement_badges, get_streak_info
    BENCHMARK_AVAILABLE = True
except ImportError as e:
    logger.warning(f"benchmark_service 모듈 로드 실패: {e}")
    BENCHMARK_AVAILABLE = False

try:
    from score_aggregator import compare_to_passing, PASSING_AVERAGES, SCORE_CATEGORIES
    SCORE_AGGREGATOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"score_aggregator 모듈 로드 실패: {e}")
    SCORE_AGGREGATOR_AVAILABLE = False

# CSS 스타일 정의
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

* {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

[data-testid="stSidebar"] { display: none !important; }
[data-testid="stSidebarNav"] { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

.block-container {
    max-width: 1200px;
    padding-top: 32px;
    padding-bottom: 48px;
}

/* 헤더 영역 */
.page-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #3b82f6 100%);
    border-radius: 20px;
    padding: 40px;
    color: white;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
}

.page-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 300px;
    height: 300px;
    background: rgba(255,255,255,0.1);
    border-radius: 50%;
}

.page-header h1 {
    font-size: 2rem;
    font-weight: 800;
    margin: 0 0 8px 0;
}

.page-header .subtitle {
    font-size: 1.1rem;
    opacity: 0.9;
    margin-bottom: 24px;
}

.greeting-box {
    background: rgba(255,255,255,0.15);
    border-radius: 12px;
    padding: 16px 20px;
    display: inline-block;
}

.greeting-box .name {
    font-weight: 700;
    font-size: 1.1rem;
}

.greeting-box .focus {
    font-size: 0.9rem;
    opacity: 0.9;
    margin-top: 4px;
}

/* 카드 스타일 */
.coaching-card {
    background: white;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    margin-bottom: 20px;
    border: 1px solid #e2e8f0;
    transition: all 0.2s ease;
}

.coaching-card:hover {
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    transform: translateY(-2px);
}

.coaching-card h3 {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1e3a5f;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e2e8f0;
}

.coaching-card.gradient {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
}

.coaching-card.gradient h3 {
    color: white;
    border-bottom-color: rgba(255,255,255,0.2);
}

/* 단계 진행률 바 */
.stage-progress {
    background: #e2e8f0;
    border-radius: 10px;
    height: 12px;
    overflow: hidden;
    margin: 16px 0;
}

.stage-progress-fill {
    height: 100%;
    border-radius: 10px;
    background: linear-gradient(90deg, #3b82f6, #10b981);
    transition: width 0.5s ease;
}

/* 단계 배지 */
.stage-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(135deg, #3b82f6, #10b981);
    color: white;
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.95rem;
}

.stage-badge.inactive {
    background: #e2e8f0;
    color: #94a3b8;
}

/* 팁 카드 */
.tip-card {
    background: #eff6ff;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    border-left: 4px solid #3b82f6;
}

.tip-card.warning {
    background: #fef3c7;
    border-left-color: #f59e0b;
}

.tip-card.success {
    background: #d1fae5;
    border-left-color: #10b981;
}

.tip-card .tip-title {
    font-weight: 700;
    color: #1e3a5f;
    font-size: 0.95rem;
    margin-bottom: 4px;
}

.tip-card .tip-content {
    font-size: 0.85rem;
    color: #475569;
}

/* 오답 노트 아이템 */
.wrong-answer-item {
    background: #f8fafc;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    border: 1px solid #e2e8f0;
}

.wrong-answer-item .category {
    display: inline-block;
    background: #dbeafe;
    color: #1d4ed8;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 8px;
}

.wrong-answer-item .question {
    font-weight: 600;
    color: #1e3a5f;
    margin-bottom: 8px;
}

.wrong-answer-item .answer {
    font-size: 0.85rem;
    color: #64748b;
    padding: 8px;
    background: white;
    border-radius: 8px;
    margin-bottom: 8px;
}

.wrong-answer-item .guidance {
    font-size: 0.85rem;
    color: #059669;
    padding: 8px;
    background: #d1fae5;
    border-radius: 8px;
}

/* 마일스톤 */
.milestone-card {
    background: linear-gradient(135deg, #fef3c7, #fde68a);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}

.milestone-card .icon {
    font-size: 2rem;
    margin-bottom: 8px;
}

.milestone-card .title {
    font-weight: 700;
    color: #92400e;
    margin-bottom: 4px;
}

.milestone-card .progress {
    font-size: 0.85rem;
    color: #b45309;
}

/* 통계 메트릭 */
.stat-metric {
    text-align: center;
    padding: 20px;
    background: #f8fafc;
    border-radius: 12px;
}

.stat-metric .value {
    font-size: 2rem;
    font-weight: 800;
    color: #1e3a5f;
}

.stat-metric .label {
    font-size: 0.85rem;
    color: #64748b;
    margin-top: 4px;
}

.stat-metric.highlight {
    background: linear-gradient(135deg, #dbeafe, #e0e7ff);
}

.stat-metric.highlight .value {
    color: #1d4ed8;
}

/* 모듈 카드 */
.module-card {
    background: white;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    border: 1px solid #e2e8f0;
    display: flex;
    align-items: center;
    gap: 16px;
}

.module-card .difficulty {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    color: white;
    flex-shrink: 0;
}

.module-card .difficulty.easy { background: #10b981; }
.module-card .difficulty.medium { background: #3b82f6; }
.module-card .difficulty.hard { background: #f59e0b; }
.module-card .difficulty.expert { background: #ef4444; }

.module-card .info h4 {
    font-size: 0.95rem;
    font-weight: 600;
    color: #1e3a5f;
    margin: 0 0 4px 0;
}

.module-card .info p {
    font-size: 0.8rem;
    color: #64748b;
    margin: 0;
}

/* 목표 스트릭 */
.streak-display {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 16px;
    background: linear-gradient(135deg, #fed7aa, #fdba74);
    border-radius: 12px;
}

.streak-display .fire {
    font-size: 2rem;
}

.streak-display .count {
    font-size: 1.5rem;
    font-weight: 800;
    color: #c2410c;
}

.streak-display .label {
    font-size: 0.85rem;
    color: #ea580c;
}

/* 동기부여 메시지 */
.motivation-box {
    background: linear-gradient(135deg, #a855f7, #6366f1);
    border-radius: 16px;
    padding: 24px;
    color: white;
    text-align: center;
}

.motivation-box .quote {
    font-size: 1.1rem;
    font-style: italic;
    margin-bottom: 8px;
}

.motivation-box .author {
    font-size: 0.85rem;
    opacity: 0.8;
}

/* 탭 스타일 */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: #f1f5f9;
    padding: 4px;
    border-radius: 12px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    background: white !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* 반응형 */
@media (max-width: 768px) {
    .page-header {
        padding: 24px;
    }
    .page-header h1 {
        font-size: 1.5rem;
    }
    .coaching-card {
        padding: 16px;
    }
}
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "user_id" not in st.session_state:
    st.session_state.user_id = "guest"

user_id = st.session_state.user_id

# 오늘의 집중 영역 가져오기
focus_areas = {}
if AI_COACH_AVAILABLE:
    try:
        focus_areas = get_focus_areas_for_today(user_id)
    except Exception as e:
        logger.error(f"집중 영역 로드 실패: {e}")

# 헤더 섹션
today_date = datetime.now().strftime("%Y년 %m월 %d일")
focus_text = focus_areas.get("focus_areas", [])
focus_display = ", ".join([f["area"] for f in focus_text[:2]]) if focus_text else "자유 연습"

st.markdown(f"""
<div class="page-header">
    <h1>AI 1:1 코칭</h1>
    <p class="subtitle">당신만을 위한 맞춤형 코칭 서비스</p>
    <div class="greeting-box">
        <div class="name">{today_date}</div>
        <div class="focus">오늘의 집중 영역: {focus_display}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "오늘의 코칭",
    "학습 경로",
    "실력 분석",
    "오답 노트",
    "목표 관리"
])

# =============================================================================
# 탭 1: 오늘의 코칭
# =============================================================================
with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        # 일일 코칭 요약
        st.markdown("""
        <div class="coaching-card">
            <h3>오늘의 코칭 요약</h3>
        """, unsafe_allow_html=True)

        if AI_COACH_AVAILABLE:
            try:
                daily_summary = get_daily_coaching_summary(user_id)

                practice_count = daily_summary.get("practice_count", 0)
                avg_score = daily_summary.get("average_score", 0)
                message = daily_summary.get("message", "오늘의 연습을 시작해보세요!")
                recommendation = daily_summary.get("recommendation", "")

                st.markdown(f"""
                <div style="margin-bottom: 20px;">
                    <p style="font-size: 1rem; color: #475569; margin-bottom: 16px;">{message}</p>
                </div>
                """, unsafe_allow_html=True)

                # 오늘의 통계
                stat_col1, stat_col2, stat_col3 = st.columns(3)
                with stat_col1:
                    st.metric("오늘 연습", f"{practice_count}회")
                with stat_col2:
                    st.metric("평균 점수", f"{avg_score:.0f}점" if avg_score > 0 else "-")
                with stat_col3:
                    improvement = daily_summary.get("improvement")
                    if improvement is not None:
                        delta = f"+{improvement}점" if improvement > 0 else f"{improvement}점"
                        st.metric("어제 대비", delta)
                    else:
                        st.metric("어제 대비", "-")

                if recommendation:
                    st.markdown(f"""
                    <div class="tip-card success">
                        <div class="tip-title">AI 추천</div>
                        <div class="tip-content">{recommendation}</div>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                logger.error(f"일일 요약 로드 실패: {e}")
                st.info("연습 기록이 없습니다. 첫 연습을 시작해보세요!")
        else:
            st.info("AI 코칭 모듈을 불러올 수 없습니다.")

        st.markdown("</div>", unsafe_allow_html=True)

        # 오늘의 집중 영역
        st.markdown("""
        <div class="coaching-card">
            <h3>오늘의 집중 영역</h3>
        """, unsafe_allow_html=True)

        if focus_areas and focus_areas.get("focus_areas"):
            for i, area in enumerate(focus_areas["focus_areas"][:3], 1):
                priority_class = "success" if area.get("priority", 0) == 1 else ""
                st.markdown(f"""
                <div class="tip-card {priority_class}">
                    <div class="tip-title">{i}순위: {area.get('area', '')}</div>
                    <div class="tip-content">{area.get('reason', '')}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="tip-card">
                <div class="tip-title">자유 연습 모드</div>
                <div class="tip-content">아직 분석할 데이터가 부족합니다. 다양한 연습을 시도해보세요!</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # 연습 제안
        if focus_areas.get("practice_suggestions"):
            st.markdown("""
            <div class="coaching-card">
                <h3>오늘의 연습 제안</h3>
            """, unsafe_allow_html=True)

            for suggestion in focus_areas["practice_suggestions"][:3]:
                st.markdown(f"- {suggestion}")

            st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        # 동기부여 메시지
        motivation = focus_areas.get("motivation", "작은 노력이 쌓여 큰 결과를 만듭니다. 오늘도 최선을 다해봐요!")
        st.markdown(f"""
        <div class="motivation-box">
            <div class="quote">"{motivation}"</div>
            <div class="author">- AI 코치</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 퀵 팁
        st.markdown("""
        <div class="coaching-card">
            <h3>오늘의 퀵 팁</h3>
        """, unsafe_allow_html=True)

        quick_tips = [
            "답변은 1-2분 내로 간결하게",
            "STAR 기법으로 구조화하기",
            "밝은 표정과 자신감 있는 목소리",
            "질문의 의도를 파악하고 답변하기",
        ]

        for tip in quick_tips:
            st.markdown(f"- {tip}")

        st.markdown("</div>", unsafe_allow_html=True)

        # 바로가기 버튼
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("모의면접 시작하기", type="primary", use_container_width=True):
            st.switch_page("pages/4_모의면접.py")

        if st.button("롤플레잉 연습", use_container_width=True):
            st.switch_page("pages/1_롤플레잉.py")

# =============================================================================
# 탭 2: 학습 경로
# =============================================================================
with tab2:
    if not LEARNING_PATH_AVAILABLE:
        st.warning("학습 경로 모듈을 불러올 수 없습니다.")
    else:
        try:
            # 현재 단계 정보
            current_stage = get_user_stage(user_id)
            stage_info = LEARNING_STAGES.get(current_stage, {})

            col1, col2 = st.columns([2, 1])

            with col1:
                # 현재 단계 표시
                st.markdown(f"""
                <div class="coaching-card gradient">
                    <h3>현재 학습 단계</h3>
                    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
                        <div class="stage-badge">
                            {current_stage}단계
                        </div>
                        <div>
                            <div style="font-size: 1.2rem; font-weight: 700;">{stage_info.get('name', '학습 중')}</div>
                            <div style="font-size: 0.9rem; opacity: 0.9;">{stage_info.get('description', '')}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # 단계 진행률
                learning_summary = get_learning_summary(user_id)
                progress = learning_summary.get("progress", {})
                completion_rate = progress.get("completion_rate", 0) * 100

                st.markdown(f"""
                    <div style="margin-top: 16px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span>진행률</span>
                            <span>{completion_rate:.0f}%</span>
                        </div>
                        <div class="stage-progress">
                            <div class="stage-progress-fill" style="width: {completion_rate}%"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 추천 모듈
                st.markdown("""
                <div class="coaching-card">
                    <h3>추천 학습 모듈</h3>
                """, unsafe_allow_html=True)

                recommended = get_recommended_modules(user_id)[:5]

                for module in recommended:
                    difficulty = module.get("difficulty", 1)
                    if difficulty == 1:
                        diff_class = "easy"
                        diff_label = "기초"
                    elif difficulty == 2:
                        diff_class = "medium"
                        diff_label = "중급"
                    elif difficulty == 3:
                        diff_class = "hard"
                        diff_label = "심화"
                    else:
                        diff_class = "expert"
                        diff_label = "전문"

                    st.markdown(f"""
                    <div class="module-card">
                        <div class="difficulty {diff_class}">{diff_label}</div>
                        <div class="info">
                            <h4>{module.get('name', '')}</h4>
                            <p>{module.get('description', '')[:50]}...</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                # 다음 마일스톤
                next_milestone = get_next_milestone(user_id)

                if next_milestone:
                    milestone_progress = next_milestone.get("progress", {})
                    st.markdown(f"""
                    <div class="milestone-card">
                        <div class="icon">🎯</div>
                        <div class="title">{next_milestone.get('name', '다음 목표')}</div>
                        <div class="progress">
                            {milestone_progress.get('current', 0)} / {milestone_progress.get('target', 1)}
                            ({milestone_progress.get('percentage', 0)}%)
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # 단계별 요구사항
                st.markdown("""
                <div class="coaching-card">
                    <h3>단계별 목표</h3>
                """, unsafe_allow_html=True)

                for stage_num in range(1, 5):
                    stage = LEARNING_STAGES.get(stage_num, {})
                    is_current = stage_num == current_stage
                    is_completed = stage_num < current_stage

                    if is_completed:
                        status_icon = "✅"
                    elif is_current:
                        status_icon = "▶️"
                    else:
                        status_icon = "⬜"

                    st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 8px; padding: 8px 0;
                                {'font-weight: 700;' if is_current else 'opacity: 0.7;'}">
                        <span>{status_icon}</span>
                        <span>{stage_num}단계: {stage.get('name', '')}</span>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

                # 일일/주간 계획
                st.markdown("<br>", unsafe_allow_html=True)

                with st.expander("일일 학습 계획 보기"):
                    available_hours = st.slider("오늘 학습 가능 시간 (시간)", 0.5, 4.0, 2.0, 0.5)

                    if st.button("계획 생성"):
                        daily_plan = create_daily_plan(user_id, available_hours)

                        for task in daily_plan.get("tasks", []):
                            task_type = task.get("type", "")
                            if task_type == "review":
                                st.info(f"📝 {task.get('title', '')} ({task.get('duration_hours', 0)*60:.0f}분)")
                            elif task_type == "main_study":
                                st.success(f"📚 {task.get('title', '')} ({task.get('duration_hours', 0)*60:.0f}분)")
                            else:
                                st.warning(f"🎯 {task.get('title', '')} ({task.get('duration_hours', 0)*60:.0f}분)")

        except Exception as e:
            logger.error(f"학습 경로 로드 실패: {e}")
            st.error("학습 경로를 불러오는 중 오류가 발생했습니다.")

# =============================================================================
# 탭 3: 실력 분석
# =============================================================================
with tab3:
    col1, col2 = st.columns([3, 2])

    with col1:
        # 스킬 레이더 차트
        st.markdown("""
        <div class="coaching-card">
            <h3>스킬 레이더 차트</h3>
        """, unsafe_allow_html=True)

        if PROGRESS_TRACKER_AVAILABLE:
            try:
                radar_data = get_skill_radar_chart_data(user_id)
                categories = radar_data.get("categories", [])
                values = radar_data.get("scores", [])

                if categories and values:
                    # Plotly 레이더 차트
                    fig = go.Figure()

                    fig.add_trace(go.Scatterpolar(
                        r=values + [values[0]] if values else [],
                        theta=categories + [categories[0]] if categories else [],
                        fill='toself',
                        fillcolor='rgba(59, 130, 246, 0.3)',
                        line=dict(color='#3b82f6', width=2),
                        name='내 점수'
                    ))

                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 100],
                                tickfont=dict(size=10),
                            ),
                            angularaxis=dict(
                                tickfont=dict(size=11, color='#334155')
                            )
                        ),
                        showlegend=False,
                        margin=dict(l=60, r=60, t=40, b=40),
                        height=350,
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("아직 스킬 데이터가 충분하지 않습니다. 연습을 시작해보세요!")

            except Exception as e:
                logger.error(f"레이더 차트 로드 실패: {e}")
                st.error("차트를 불러오는 중 오류가 발생했습니다.")
        else:
            st.warning("진도 추적 모듈을 불러올 수 없습니다.")

        st.markdown("</div>", unsafe_allow_html=True)

        # 약점/강점 분석
        if AI_COACH_AVAILABLE:
            try:
                weaknesses = analyze_weaknesses(user_id)

                st.markdown("""
                <div class="coaching-card">
                    <h3>강점/약점 분석</h3>
                """, unsafe_allow_html=True)

                summary = weaknesses.get("summary", "")
                if summary:
                    st.markdown(f"<p style='color: #475569; margin-bottom: 16px;'>{summary}</p>", unsafe_allow_html=True)

                # 개선 우선순위
                priorities = weaknesses.get("improvement_priorities", [])
                if priorities:
                    st.markdown("<h4 style='font-size: 0.95rem; color: #1e3a5f; margin-bottom: 12px;'>개선 우선순위</h4>", unsafe_allow_html=True)

                    for p in priorities:
                        gap = p.get('target_score', 0) - p.get('current_score', 0)
                        st.markdown(f"""
                        <div class="tip-card warning">
                            <div class="tip-title">{p.get('priority', '')}순위: {p.get('skill', '')}</div>
                            <div class="tip-content">현재 {p.get('current_score', 0)}점 → 목표 {p.get('target_score', 0)}점 (차이: {gap}점)</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

            except Exception as e:
                logger.error(f"약점 분석 로드 실패: {e}")

    with col2:
        # 카테고리별 개선율
        st.markdown("""
        <div class="coaching-card">
            <h3>카테고리별 개선율</h3>
        """, unsafe_allow_html=True)

        if PROGRESS_TRACKER_AVAILABLE and SCORE_AGGREGATOR_AVAILABLE:
            try:
                for category in SCORE_CATEGORIES:
                    improvement = get_improvement_rate(user_id, category)

                    if improvement > 0:
                        color = "#10b981"
                        arrow = "↑"
                    elif improvement < 0:
                        color = "#ef4444"
                        arrow = "↓"
                    else:
                        color = "#64748b"
                        arrow = "→"

                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #e2e8f0;">
                        <span style="color: #475569;">{category}</span>
                        <span style="color: {color}; font-weight: 700;">{arrow} {abs(improvement):.1f}점/주</span>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                logger.error(f"개선율 로드 실패: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

        # 합격선 비교
        if SCORE_AGGREGATOR_AVAILABLE:
            st.markdown("""
            <div class="coaching-card">
                <h3>합격선 비교</h3>
            """, unsafe_allow_html=True)

            target_airline = st.selectbox(
                "목표 항공사",
                list(PASSING_AVERAGES.keys()),
                key="passing_airline"
            )

            try:
                # 사용자 점수 가져오기 (최근 평균)
                user_scores = {}
                for cat in SCORE_CATEGORIES:
                    trend = get_score_trend(user_id, cat, days=30) if PROGRESS_TRACKER_AVAILABLE else []
                    if trend:
                        scores = [t.get("score", 0) for t in trend]
                        user_scores[cat] = sum(scores) / len(scores) if scores else 0

                if user_scores:
                    comparison = compare_to_passing(user_scores, target_airline)

                    for cat, data in comparison.items():
                        status = data.get("status", "below")
                        diff = data.get("diff", 0)

                        if status == "excellent":
                            color = "#10b981"
                            status_kr = "우수"
                        elif status == "passing":
                            color = "#3b82f6"
                            status_kr = "합격"
                        elif status == "close":
                            color = "#f59e0b"
                            status_kr = "근접"
                        else:
                            color = "#ef4444"
                            status_kr = "미달"

                        st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0;">
                            <span style="color: #475569; font-size: 0.9rem;">{cat}</span>
                            <span style="background: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">{status_kr} ({diff:+.0f})</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("비교할 점수 데이터가 없습니다.")

            except Exception as e:
                logger.error(f"합격선 비교 실패: {e}")

            st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# 탭 4: 오답 노트
# =============================================================================
with tab4:
    if not LEARNING_PATH_AVAILABLE:
        st.warning("학습 경로 모듈을 불러올 수 없습니다.")
    else:
        col1, col2 = st.columns([2, 1])

        with col1:
            # 오답 목록
            st.markdown("""
            <div class="coaching-card">
                <h3>오답 노트</h3>
            """, unsafe_allow_html=True)

            # 필터
            category_filter = st.selectbox(
                "카테고리 필터",
                ["전체", "자기소개", "지원동기", "인성 면접", "직무 면접", "상황 대처", "영어 면접"],
                key="wrong_category"
            )

            try:
                filter_cat = None if category_filter == "전체" else category_filter
                wrong_answers = get_wrong_answers(user_id, category=filter_cat)

                if wrong_answers:
                    for item in wrong_answers[:10]:
                        st.markdown(f"""
                        <div class="wrong-answer-item">
                            <span class="category">{item.get('category', '기타')}</span>
                            <div class="question">{item.get('question', '')[:100]}...</div>
                            <div class="answer">
                                <strong>내 답변:</strong> {item.get('user_answer', '')[:150]}...
                            </div>
                            <div class="guidance">
                                <strong>가이드:</strong> {item.get('correct_guidance', '')[:150]}...
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # 마스터 버튼
                        item_id = item.get("item_id", "")
                        if st.button(f"마스터 완료", key=f"master_{item_id}"):
                            result = mark_mastered(user_id, item_id)
                            if result.get("mastered"):
                                st.success(result.get("message", "마스터 완료!"))
                                st.rerun()
                            else:
                                st.error(result.get("error", "오류가 발생했습니다."))

                        st.markdown("---")
                else:
                    st.info("오답 기록이 없습니다. 연습 중 틀린 문제가 여기에 저장됩니다.")

            except Exception as e:
                logger.error(f"오답 노트 로드 실패: {e}")
                st.error("오답 노트를 불러오는 중 오류가 발생했습니다.")

            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            # 복습 필요 항목
            st.markdown("""
            <div class="coaching-card">
                <h3>복습 필요 항목</h3>
            """, unsafe_allow_html=True)

            try:
                review_items = get_review_items(user_id)

                if review_items:
                    st.markdown(f"""
                    <div class="tip-card warning">
                        <div class="tip-title">복습 대기</div>
                        <div class="tip-content">{len(review_items)}개 항목이 복습을 기다리고 있습니다.</div>
                    </div>
                    """, unsafe_allow_html=True)

                    for item in review_items[:5]:
                        st.markdown(f"- {item.get('item_id', '')[:8]}...")
                else:
                    st.markdown("""
                    <div class="tip-card success">
                        <div class="tip-title">복습 완료</div>
                        <div class="tip-content">현재 복습이 필요한 항목이 없습니다!</div>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                logger.error(f"복습 항목 로드 실패: {e}")

            st.markdown("</div>", unsafe_allow_html=True)

            # 오답 추가 폼
            st.markdown("<br>", unsafe_allow_html=True)

            with st.expander("새 오답 추가"):
                new_question = st.text_area("질문", key="new_wrong_q")
                new_answer = st.text_area("내 답변", key="new_wrong_a")
                new_guidance = st.text_area("올바른 답변 가이드", key="new_wrong_g")
                new_category = st.selectbox(
                    "카테고리",
                    ["자기소개", "지원동기", "인성 면접", "직무 면접", "상황 대처", "영어 면접"],
                    key="new_wrong_cat"
                )

                if st.button("오답 추가", type="primary"):
                    if new_question and new_answer:
                        try:
                            result = add_wrong_answer(
                                user_id,
                                new_question,
                                new_answer,
                                new_guidance,
                                new_category
                            )
                            st.success("오답이 추가되었습니다!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"추가 실패: {e}")
                    else:
                        st.warning("질문과 답변을 입력해주세요.")

# =============================================================================
# 탭 5: 목표 관리
# =============================================================================
with tab5:
    col1, col2 = st.columns([2, 1])

    with col1:
        # 목표 설정
        st.markdown("""
        <div class="coaching-card">
            <h3>목표 설정</h3>
        """, unsafe_allow_html=True)

        if SCORE_AGGREGATOR_AVAILABLE:
            target_airline = st.selectbox(
                "목표 항공사",
                list(PASSING_AVERAGES.keys()),
                key="goal_airline"
            )

            deadline_days = st.slider("면접까지 남은 일수", 7, 90, 30)

            passing_score = PASSING_AVERAGES.get(target_airline, {}).get("종합점수", 75)
            st.info(f"{target_airline} 합격 평균 점수: {passing_score}점")

            deadline_date = datetime.now() + timedelta(days=deadline_days)
            st.markdown(f"**목표 면접일:** {deadline_date.strftime('%Y년 %m월 %d일')}")

        st.markdown("</div>", unsafe_allow_html=True)

        # 일일 목표 설정
        st.markdown("""
        <div class="coaching-card">
            <h3>일일 목표 설정</h3>
        """, unsafe_allow_html=True)

        if PROGRESS_TRACKER_AVAILABLE:
            daily_practice = st.number_input("일일 연습 횟수 목표", 1, 10, 3, key="daily_practice")
            daily_score = st.number_input("일일 목표 점수", 50, 100, 75, key="daily_score")

            if st.button("일일 목표 저장", type="primary"):
                try:
                    set_daily_goal(user_id, daily_practice, daily_score)
                    st.success("일일 목표가 설정되었습니다!")
                except Exception as e:
                    st.error(f"설정 실패: {e}")

            # 오늘의 목표 달성 현황
            st.markdown("<br>", unsafe_allow_html=True)

            try:
                goal_status = check_daily_goal(user_id)

                if goal_status.get("has_goal"):
                    st.markdown("**오늘의 목표 달성 현황**")

                    count_progress = goal_status.get("count_progress", 0)
                    score_progress = goal_status.get("score_progress", 0)

                    st.progress(count_progress / 100)
                    st.caption(f"연습 횟수: {goal_status.get('completed_count', 0)} / {goal_status.get('practice_count', 0)}")

                    st.progress(score_progress / 100)
                    st.caption(f"점수: {goal_status.get('achieved_score', 0):.0f} / {goal_status.get('target_score', 0)}")

                    if goal_status.get("is_met"):
                        st.success("오늘의 목표를 달성했습니다!")
                else:
                    st.info("오늘의 목표가 설정되지 않았습니다.")

            except Exception as e:
                logger.error(f"목표 상태 로드 실패: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        # 목표 달성 스트릭
        st.markdown("""
        <div class="coaching-card">
            <h3>연속 달성</h3>
        """, unsafe_allow_html=True)

        if PROGRESS_TRACKER_AVAILABLE:
            try:
                streak = get_goal_streak(user_id)

                st.markdown(f"""
                <div class="streak-display">
                    <span class="fire">🔥</span>
                    <div>
                        <div class="count">{streak}일</div>
                        <div class="label">연속 목표 달성</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 주간 달성률
                weekly_completion = get_weekly_goal_completion(user_id)

                st.markdown(f"""
                <div style="margin-top: 16px; text-align: center;">
                    <div style="font-size: 0.9rem; color: #64748b;">이번 주 달성률</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #1e3a5f;">
                        {weekly_completion.get('completion_rate', 0):.0f}%
                    </div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">
                        {weekly_completion.get('met_count', 0)}/{weekly_completion.get('total_days_with_goal', 0)}일 달성
                    </div>
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                logger.error(f"스트릭 로드 실패: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

        # 배지/업적
        if BENCHMARK_AVAILABLE:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div class="coaching-card">
                <h3>획득한 배지</h3>
            """, unsafe_allow_html=True)

            try:
                badges = get_achievement_badges(user_id)
                earned = badges.get("earned", [])

                if earned:
                    for badge in earned[:5]:
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; gap: 12px; padding: 8px 0;">
                            <span style="font-size: 1.5rem;">🏆</span>
                            <div>
                                <div style="font-weight: 600; color: #1e3a5f;">{badge.get('name', '')}</div>
                                <div style="font-size: 0.8rem; color: #64748b;">{badge.get('description', '')[:30]}...</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("아직 획득한 배지가 없습니다.")

                st.markdown(f"""
                <div style="text-align: center; margin-top: 12px; color: #64748b; font-size: 0.85rem;">
                    {badges.get('total_earned', 0)} / {badges.get('total_available', 0)} 배지 획득
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                logger.error(f"배지 로드 실패: {e}")

            st.markdown("</div>", unsafe_allow_html=True)

# 푸터
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94a3b8; font-size: 0.85rem; padding: 24px 0;">
    FlyReady Lab - AI 1:1 코칭 서비스
</div>
""", unsafe_allow_html=True)

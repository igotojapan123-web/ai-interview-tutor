# pages/25_면접히스토리.py
# 면접 히스토리 & 복습 페이지

# 정식 웹사이트 이전 안내
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from redirect_to_web import show_redirect_and_stop
show_redirect_and_stop()

import streamlit as st
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# 상위 디렉토리 import 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 페이지 초기화
try:
    from sidebar_common import init_page, end_page
    init_page(
        title="면접 히스토리",
        current_page="면접히스토리",
        wide_layout=True
    )
except ImportError:
    st.set_page_config(page_title="면접 히스토리", layout="wide")

# 히스토리 유틸리티 import
try:
    from interview_history_utils import (
        get_all_sessions,
        get_session_by_id,
        get_sessions_by_airline,
        get_sessions_by_date,
        get_weak_questions,
        get_category_stats,
        get_airline_stats,
        get_total_stats,
        get_recent_scores,
        delete_session,
    )
    HISTORY_AVAILABLE = True
except ImportError:
    HISTORY_AVAILABLE = False

# AI 추천 서비스 import
try:
    from interview_review_service import (
        get_weekly_recommendation,
        get_improvement_trend,
        get_practice_again_list,
    )
    REVIEW_SERVICE_AVAILABLE = True
except ImportError:
    REVIEW_SERVICE_AVAILABLE = False

# ============================================
# 스타일 정의
# ============================================

st.markdown("""
<style>
/* 세션 카드 */
.session-card {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    border: 1px solid #e2e8f0;
    transition: all 0.2s ease;
}
.session-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* AI 추천 카드 */
.ai-recommendation {
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    border: 1px solid #93c5fd;
}
.ai-recommendation h3 {
    color: #1e40af;
    margin: 0 0 12px 0;
}

/* 약점 카드 */
.weak-card {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    border: 1px solid #fbbf24;
}

/* 점수 배지 */
.score-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 14px;
}
.score-high { background: #dcfce7; color: #166534; }
.score-mid { background: #fef9c3; color: #854d0e; }
.score-low { background: #fee2e2; color: #991b1b; }

/* 상세 모달 */
.detail-section {
    background: #f8fafc;
    border-radius: 12px;
    padding: 16px;
    margin: 12px 0;
}

/* 빈 상태 */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #64748b;
}
.empty-state h3 {
    color: #334155;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)


# ============================================
# 유틸리티 함수
# ============================================

def get_score_badge_class(score: int) -> str:
    """점수에 따른 배지 클래스"""
    if score >= 80:
        return "score-high"
    elif score >= 60:
        return "score-mid"
    else:
        return "score-low"


def get_star_rating(score: int) -> str:
    """점수를 별점으로 변환"""
    stars = score / 20  # 100점 -> 5점
    full_stars = int(stars)
    half_star = 1 if stars - full_stars >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star
    return "★" * full_stars + ("☆" if half_star else "") + "☆" * empty_stars


def format_duration(seconds: int) -> str:
    """초를 분:초 형식으로 변환"""
    if seconds <= 0:
        return "0분"
    minutes = seconds // 60
    secs = seconds % 60
    if minutes > 0:
        return f"{minutes}분 {secs}초" if secs > 0 else f"{minutes}분"
    return f"{secs}초"


# ============================================
# 메인 페이지
# ============================================

st.title("면접 히스토리")
st.caption("지난 면접 연습을 돌아보고, 약점을 집중 연습하세요")

if not HISTORY_AVAILABLE:
    st.error("히스토리 기능을 사용할 수 없습니다. 관리자에게 문의하세요.")
    st.stop()

# 전체 통계 로드
total_stats = get_total_stats()

# ============================================
# 상단 통계 카드
# ============================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="총 연습 횟수",
        value=f"{total_stats['total_sessions']}회",
        delta=None
    )

with col2:
    st.metric(
        label="평균 점수",
        value=f"{total_stats['avg_score']}점",
        delta=f"최고 {total_stats['best_score']}점" if total_stats['best_score'] > 0 else None
    )

with col3:
    trend_icon = {"up": "📈", "down": "📉", "stable": "➡️", "none": ""}
    st.metric(
        label="최근 추세",
        value=trend_icon.get(total_stats['recent_trend'], "") + " " + {
            "up": "상승",
            "down": "하락",
            "stable": "유지",
            "none": "데이터 부족"
        }.get(total_stats['recent_trend'], "")
    )

with col4:
    st.metric(
        label="총 질문 수",
        value=f"{total_stats['total_questions']}개"
    )

st.divider()

# ============================================
# AI 추천 섹션
# ============================================

if REVIEW_SERVICE_AVAILABLE:
    try:
        recommendation = get_weekly_recommendation()
        if recommendation and recommendation.get("message"):
            st.markdown(f"""
            <div class="ai-recommendation">
                <h3>🎯 AI 추천</h3>
                <p style="font-size: 16px; margin: 0;">{recommendation.get("message", "")}</p>
            </div>
            """, unsafe_allow_html=True)

            if recommendation.get("weak_areas"):
                weak_cols = st.columns(len(recommendation["weak_areas"]))
                for i, area in enumerate(recommendation["weak_areas"][:3]):
                    with weak_cols[i]:
                        if st.button(f"'{area}' 집중 연습", key=f"weak_practice_{i}", use_container_width=True):
                            st.info(f"'{area}' 관련 질문으로 연습을 시작합니다.")
                            # TODO: 모의면접 페이지로 이동 with 필터
    except Exception as e:
        pass  # AI 추천 실패해도 페이지는 정상 표시

# ============================================
# 탭 구성
# ============================================

tab1, tab2, tab3 = st.tabs(["📚 전체 기록", "⚠️ 약점 분석", "📈 성장 추이"])

# ============================================
# Tab 1: 전체 기록
# ============================================

with tab1:
    # 필터 옵션
    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])

    with filter_col1:
        # 항공사 필터
        airline_stats = get_airline_stats()
        airline_options = ["전체"] + list(airline_stats.keys())
        selected_airline = st.selectbox("항공사", airline_options, key="filter_airline")

    with filter_col2:
        # 날짜 범위
        date_range = st.date_input(
            "날짜 범위",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            key="filter_date"
        )

    with filter_col3:
        st.write("")  # 여백
        st.write("")
        refresh = st.button("🔄 새로고침", use_container_width=True)

    st.divider()

    # 세션 목록 로드
    if selected_airline == "전체":
        if isinstance(date_range, tuple) and len(date_range) == 2:
            sessions = get_sessions_by_date(
                date_range[0].strftime("%Y-%m-%d"),
                date_range[1].strftime("%Y-%m-%d")
            )
        else:
            sessions = get_all_sessions(limit=50)
    else:
        sessions = get_sessions_by_airline(selected_airline)

    # 세션 표시
    if not sessions:
        st.markdown("""
        <div class="empty-state">
            <h3>아직 기록이 없어요</h3>
            <p>모의면접을 연습하면 여기에 기록이 쌓여요!</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🎤 모의면접 시작하기", type="primary"):
            st.switch_page("pages/4_모의면접.py")
    else:
        for session in sessions:
            session_id = session.get("session_id", "")
            score = session.get("scores", {}).get("total", 0)
            score_class = get_score_badge_class(score)

            with st.expander(
                f"📅 {session.get('created_date', '')} {session.get('created_time', '')} | "
                f"{session.get('airline', '')} {session.get('type', '')} | "
                f"{get_star_rating(score)} ({score}점)",
                expanded=False
            ):
                # 세션 요약
                info_col1, info_col2, info_col3 = st.columns(3)
                with info_col1:
                    st.write(f"**질문 수:** {session.get('question_count', 0)}문항")
                with info_col2:
                    voice_avg = session.get('scores', {}).get('voice_avg', 0)
                    content_avg = session.get('scores', {}).get('content_avg', 0)
                    st.write(f"**음성/내용:** {voice_avg}/{content_avg}")
                with info_col3:
                    duration = session.get('total_duration_sec', 0)
                    st.write(f"**소요 시간:** {format_duration(duration)}")

                st.divider()

                # 질문별 상세
                questions = session.get("questions", [])
                if questions:
                    st.write("**질문별 결과:**")
                    for q in questions:
                        q_score = q.get("content_analysis", {}).get("total_score", 0)
                        voice_score = q.get("voice_analysis", {}).get("total_score", 0)
                        avg_q_score = (q_score + voice_score) / 2 if voice_score else q_score

                        # 점수 아이콘
                        score_icon = "✅" if avg_q_score >= 70 else ("⚠️" if avg_q_score >= 50 else "❌")

                        with st.container():
                            st.markdown(f"""
                            <div class="detail-section">
                                <strong>{score_icon} Q{q.get('index', 0) + 1}. {q.get('question_text', '')[:50]}...</strong>
                                <br>
                                <span class="score-badge {get_score_badge_class(int(avg_q_score))}">{int(avg_q_score)}점</span>
                            </div>
                            """, unsafe_allow_html=True)

                            # 답변 보기
                            answer = q.get("answer_text", "")
                            if answer:
                                with st.expander("💬 내 답변 보기"):
                                    st.write(answer)

                                    # 피드백
                                    feedback = q.get("feedback", {})
                                    if feedback.get("ai_comment"):
                                        st.info(f"**AI 피드백:** {feedback['ai_comment']}")

                st.divider()

                # 액션 버튼
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                with btn_col1:
                    if st.button("🔄 다시 연습", key=f"retry_{session_id}", use_container_width=True):
                        st.session_state["retry_airline"] = session.get("airline", "")
                        st.switch_page("pages/4_모의면접.py")
                with btn_col2:
                    if st.button("📊 상세 분석", key=f"detail_{session_id}", use_container_width=True):
                        st.session_state["detail_session_id"] = session_id
                        st.info("상세 분석 페이지로 이동합니다.")
                with btn_col3:
                    if st.button("🗑️ 삭제", key=f"delete_{session_id}", use_container_width=True):
                        if delete_session(session_id):
                            st.success("삭제되었습니다.")
                            st.rerun()
                        else:
                            st.error("삭제 실패")

# ============================================
# Tab 2: 약점 분석
# ============================================

with tab2:
    st.subheader("⚠️ 약점 질문 모아보기")
    st.caption("60점 미만으로 답변한 질문들을 모아봤어요. 집중 연습이 필요해요!")

    weak_questions = get_weak_questions(score_threshold=60, limit=20)

    if not weak_questions:
        st.markdown("""
        <div class="empty-state">
            <h3>약점이 없어요! 🎉</h3>
            <p>모든 질문에 잘 답변하셨네요. 계속 연습해서 실력을 유지하세요!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 카테고리별 그룹화
        category_groups = {}
        for wq in weak_questions:
            cat = wq.get("category", "기타")
            if cat not in category_groups:
                category_groups[cat] = []
            category_groups[cat].append(wq)

        # 카테고리별 표시
        for category, questions in category_groups.items():
            st.markdown(f"### {category} ({len(questions)}개)")

            for wq in questions:
                st.markdown(f"""
                <div class="weak-card">
                    <strong>Q. {wq.get('question_text', '')}</strong>
                    <br>
                    <small>
                        {wq.get('session_date', '')} | {wq.get('airline', '')} |
                        점수: <span style="color: #dc2626; font-weight: bold;">{wq.get('score', 0)}점</span>
                    </small>
                </div>
                """, unsafe_allow_html=True)

                # 피드백
                feedback = wq.get("feedback", {})
                improvements = feedback.get("improvements", [])
                if improvements:
                    with st.expander("💡 개선 포인트"):
                        for imp in improvements:
                            st.write(f"- {imp}")

            st.divider()

        # 약점 집중 연습 버튼
        if st.button("🎯 약점 집중 연습 시작", type="primary", use_container_width=True):
            st.info("약점 질문 위주로 모의면접을 시작합니다.")
            st.switch_page("pages/4_모의면접.py")

# ============================================
# Tab 3: 성장 추이
# ============================================

with tab3:
    st.subheader("📈 점수 변화 추이")

    # 최근 점수 데이터 가져오기
    recent_scores = get_recent_scores(days=30, limit=30)

    if not recent_scores:
        st.markdown("""
        <div class="empty-state">
            <h3>아직 데이터가 부족해요</h3>
            <p>면접 연습을 더 하면 성장 추이를 볼 수 있어요!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 점수 추이 차트
        import pandas as pd

        df = pd.DataFrame(recent_scores)
        df = df.sort_values("date")

        # 라인 차트
        st.line_chart(df.set_index("date")["score"], use_container_width=True)

        # 통계 요약
        st.divider()

        stat_col1, stat_col2, stat_col3 = st.columns(3)
        with stat_col1:
            avg_score = df["score"].mean()
            st.metric("평균 점수", f"{avg_score:.1f}점")
        with stat_col2:
            max_score = df["score"].max()
            st.metric("최고 점수", f"{max_score}점")
        with stat_col3:
            # 최근 5개 vs 이전 5개
            if len(df) >= 10:
                recent_5 = df.tail(5)["score"].mean()
                prev_5 = df.iloc[-10:-5]["score"].mean()
                change = recent_5 - prev_5
                st.metric("최근 변화", f"{change:+.1f}점")
            else:
                st.metric("최근 변화", "데이터 부족")

    # 카테고리별 점수
    st.divider()
    st.subheader("📊 카테고리별 평균 점수")

    category_stats = get_category_stats()
    if category_stats:
        cat_df = pd.DataFrame([
            {"카테고리": k, "평균점수": v["avg_score"], "연습횟수": v["count"]}
            for k, v in category_stats.items()
        ])
        st.bar_chart(cat_df.set_index("카테고리")["평균점수"])
    else:
        st.info("아직 카테고리별 데이터가 없습니다.")

    # 항공사별 점수
    st.divider()
    st.subheader("✈️ 항공사별 평균 점수")

    airline_stats = get_airline_stats()
    if airline_stats:
        airline_df = pd.DataFrame([
            {"항공사": k, "평균점수": v["avg_score"], "연습횟수": v["count"]}
            for k, v in airline_stats.items()
        ])
        st.bar_chart(airline_df.set_index("항공사")["평균점수"])
    else:
        st.info("아직 항공사별 데이터가 없습니다.")


# ============================================
# 페이지 종료
# ============================================

try:
    end_page()
except:
    pass

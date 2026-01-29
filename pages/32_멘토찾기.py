# pages/32_멘토찾기.py
# FlyReady Lab - 멘토 매칭 페이지

import streamlit as st
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="멘토 찾기 - FlyReady Lab",
    page_icon="✈️",
    layout="wide"
)

# 시스템 import
try:
    from mentor_system import MentorMatchingEngine, MentorBookingService, SessionType
    MENTOR_AVAILABLE = True
    mentor_engine = MentorMatchingEngine()
    booking_service = MentorBookingService()
except ImportError:
    MENTOR_AVAILABLE = False
    mentor_engine = None

# CSS
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
* { font-family: 'Pretendard', -apple-system, sans-serif; }
[data-testid="stSidebar"] { display: none; }
.block-container { max-width: 1200px; padding-top: 32px; }

.page-header {
    margin-bottom: 32px;
}
.page-header h1 {
    font-size: 1.75rem;
    font-weight: 800;
    color: #1e3a5f;
    margin-bottom: 8px;
}
.page-header p {
    color: #64748b;
}

.mentor-card {
    background: white;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    margin-bottom: 20px;
    transition: all 0.2s;
    border: 1px solid #e2e8f0;
}
.mentor-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    border-color: #3b82f6;
}

.mentor-header {
    display: flex;
    gap: 20px;
    margin-bottom: 16px;
}
.mentor-avatar {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: linear-gradient(135deg, #3b82f6, #1e3a5f);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 2rem;
    font-weight: 700;
    flex-shrink: 0;
}
.mentor-info h3 {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1e3a5f;
    margin: 0 0 4px 0;
}
.mentor-type {
    font-size: 0.85rem;
    color: #3b82f6;
    font-weight: 600;
    margin-bottom: 4px;
}
.mentor-meta {
    font-size: 0.85rem;
    color: #64748b;
}

.mentor-stats {
    display: flex;
    gap: 24px;
    margin: 16px 0;
    padding: 16px;
    background: #f8fafc;
    border-radius: 10px;
}
.mentor-stat {
    text-align: center;
}
.mentor-stat-value {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1e3a5f;
}
.mentor-stat-label {
    font-size: 0.75rem;
    color: #64748b;
}

.mentor-specialties {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 12px 0;
}
.specialty-tag {
    background: #eff6ff;
    color: #3b82f6;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 0.8rem;
    font-weight: 500;
}

.mentor-bio {
    font-size: 0.9rem;
    color: #475569;
    line-height: 1.6;
    margin: 12px 0;
}

.mentor-actions {
    display: flex;
    gap: 12px;
    margin-top: 16px;
}
</style>
""", unsafe_allow_html=True)

# 헤더
st.markdown("""
<div class="page-header">
    <h1>멘토 찾기</h1>
    <p>현직 승무원, 합격자 멘토와 함께 면접을 준비하세요</p>
</div>
""", unsafe_allow_html=True)

if not MENTOR_AVAILABLE:
    st.warning("멘토 시스템을 불러올 수 없습니다.")
    st.stop()

# 필터
col1, col2, col3, col4 = st.columns(4)

with col1:
    airline_filter = st.selectbox(
        "항공사",
        ["전체", "KE", "OZ", "7C", "LJ", "TW", "EK", "SQ", "CX", "QR"],
        format_func=lambda x: mentor_engine.AIRLINE_NAMES.get(x, x) if x != "전체" else "전체"
    )

with col2:
    type_filter = st.selectbox(
        "멘토 유형",
        ["전체", "current_crew", "recent_pass", "instructor"],
        format_func=lambda x: mentor_engine.MENTOR_TYPE_NAMES.get(x, x) if x != "전체" else "전체"
    )

with col3:
    session_filter = st.selectbox(
        "상담 유형",
        ["전체", "video_call", "mock_interview", "document_review", "chat"],
        format_func=lambda x: mentor_engine.SESSION_TYPE_NAMES.get(x, x) if x != "전체" else "전체"
    )

with col4:
    sort_by = st.selectbox(
        "정렬",
        ["rating", "reviews", "price_low", "price_high"],
        format_func=lambda x: {
            "rating": "평점 높은순",
            "reviews": "리뷰 많은순",
            "price_low": "가격 낮은순",
            "price_high": "가격 높은순"
        }.get(x, x)
    )

st.markdown("---")

# 멘토 목록 조회
mentors = mentor_engine.repo.search_mentors(
    airline=None if airline_filter == "전체" else airline_filter,
    mentor_type=None if type_filter == "전체" else type_filter,
    session_type=None if session_filter == "전체" else session_filter
)

# 정렬
if sort_by == "reviews":
    mentors.sort(key=lambda x: x.total_reviews, reverse=True)
elif sort_by == "price_low":
    mentors.sort(key=lambda x: x.hourly_rate)
elif sort_by == "price_high":
    mentors.sort(key=lambda x: x.hourly_rate, reverse=True)
# rating은 기본값

if not mentors:
    st.info("조건에 맞는 멘토가 없습니다. 필터를 조정해보세요.")
else:
    st.caption(f"총 {len(mentors)}명의 멘토")

    for mentor in mentors:
        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                # 멘토 정보
                type_name = mentor_engine.MENTOR_TYPE_NAMES.get(mentor.mentor_type, mentor.mentor_type)
                airlines = [mentor_engine.AIRLINE_NAMES.get(a, a) for a in mentor.airlines]

                st.markdown(f"""
                <div class="mentor-card">
                    <div class="mentor-header">
                        <div class="mentor-avatar">{mentor.name[0]}</div>
                        <div class="mentor-info">
                            <h3>{mentor.name} {'✓' if mentor.verified else ''}</h3>
                            <div class="mentor-type">{type_name}</div>
                            <div class="mentor-meta">{', '.join(airlines)} | 경력 {mentor.years_experience}년</div>
                        </div>
                    </div>
                    <div class="mentor-stats">
                        <div class="mentor-stat">
                            <div class="mentor-stat-value">{'★' * int(mentor.rating)} {mentor.rating}</div>
                            <div class="mentor-stat-label">평점</div>
                        </div>
                        <div class="mentor-stat">
                            <div class="mentor-stat-value">{mentor.total_reviews}</div>
                            <div class="mentor-stat-label">리뷰</div>
                        </div>
                        <div class="mentor-stat">
                            <div class="mentor-stat-value">{mentor.total_sessions}</div>
                            <div class="mentor-stat-label">상담</div>
                        </div>
                        <div class="mentor-stat">
                            <div class="mentor-stat-value">₩{mentor.hourly_rate:,}</div>
                            <div class="mentor-stat-label">/시간</div>
                        </div>
                    </div>
                    <div class="mentor-specialties">
                        {''.join([f'<span class="specialty-tag">{s}</span>' for s in mentor.specialties[:4]])}
                    </div>
                    <div class="mentor-bio">{mentor.bio[:150]}...</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.write("")
                st.write("")

                # 예약 버튼
                if st.button("상담 신청", key=f"book_{mentor.id}", type="primary", use_container_width=True):
                    st.session_state['booking_mentor_id'] = mentor.id
                    st.session_state['show_booking_modal'] = True

                st.caption(f"가능: {', '.join(mentor.available_days)}")

# 예약 모달
if st.session_state.get('show_booking_modal') and st.session_state.get('booking_mentor_id'):
    mentor_id = st.session_state['booking_mentor_id']
    mentor = mentor_engine.repo.get_mentor_by_id(mentor_id)

    if mentor:
        st.markdown("---")
        st.subheader(f"{mentor.name} 멘토 상담 예약")

        col1, col2 = st.columns(2)

        with col1:
            session_type = st.selectbox(
                "상담 유형",
                mentor.session_types,
                format_func=lambda x: mentor_engine.SESSION_TYPE_NAMES.get(x, x),
                key="booking_session_type"
            )

            min_date = datetime.now().date() + timedelta(days=1)
            max_date = datetime.now().date() + timedelta(days=30)
            selected_date = st.date_input("날짜", min_value=min_date, max_value=max_date, key="booking_date")

            date_str = selected_date.strftime("%Y-%m-%d")
            available_times = booking_service.get_available_slots(mentor_id, date_str)

            if available_times:
                selected_time = st.selectbox("시간", available_times, key="booking_time")
            else:
                st.warning("해당 날짜에 예약 가능한 시간이 없습니다.")
                selected_time = None

        with col2:
            topic = st.text_input("상담 주제", placeholder="예: 대한항공 면접 준비", key="booking_topic")
            questions = st.text_area("사전 질문 (선택)", placeholder="멘토에게 미리 전달할 질문을 작성해주세요", key="booking_questions")

            st.markdown(f"### 결제 금액: ₩{mentor.hourly_rate:,}")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("예약하기", type="primary", use_container_width=True, disabled=not selected_time):
                    user_id = st.session_state.get("user_id", "guest")

                    session = booking_service.create_booking(
                        mentor_id=mentor_id,
                        mentee_id=user_id,
                        session_type=session_type,
                        date=date_str,
                        time=selected_time,
                        topic=topic,
                        questions=[q.strip() for q in questions.split('\n') if q.strip()]
                    )

                    if session:
                        st.success(f"예약이 완료되었습니다! (예약번호: {session.id})")
                        st.session_state['show_booking_modal'] = False
                        st.balloons()
                    else:
                        st.error("예약에 실패했습니다. 다시 시도해주세요.")

            with col_b:
                if st.button("취소", use_container_width=True):
                    st.session_state['show_booking_modal'] = False
                    st.rerun()

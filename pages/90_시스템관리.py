"""
FlyReady Lab Admin Dashboard.

Comprehensive admin panel for system management.
"""

import streamlit as st
from datetime import datetime, timedelta
import json

st.set_page_config(
    page_title="관리자 대시보드 | FlyReady Lab",
    page_icon="⚙️",
    layout="wide"
)

# Admin authentication check
def check_admin_auth():
    """Check if user is authenticated as admin."""
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    return st.session_state.admin_authenticated

def admin_login():
    """Admin login form."""
    st.title("🔐 관리자 로그인")

    with st.form("admin_login"):
        password = st.text_input("관리자 비밀번호", type="password")
        submit = st.form_submit_button("로그인")

        if submit:
            import os
            admin_pw = os.getenv("ADMIN_PASSWORD", "admin123")
            if password == admin_pw:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")

# Check authentication
if not check_admin_auth():
    admin_login()
    st.stop()

# Admin Dashboard
st.title("⚙️ FlyReady Lab 관리자 대시보드")

# Sidebar navigation
st.sidebar.title("관리 메뉴")
menu = st.sidebar.radio(
    "메뉴 선택",
    ["📊 대시보드", "👥 사용자 관리", "💳 결제 관리", "👨‍🏫 멘토 관리",
     "📋 채용공고 관리", "📚 콘텐츠 관리", "🔔 알림 관리", "⚙️ 시스템 설정"]
)

# Logout button
if st.sidebar.button("🚪 로그아웃"):
    st.session_state.admin_authenticated = False
    st.rerun()

# =============================================================================
# Dashboard Overview
# =============================================================================

if menu == "📊 대시보드":
    st.header("시스템 현황")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("총 사용자", "1,234", "+56")
    with col2:
        st.metric("유료 구독자", "456", "+23")
    with col3:
        st.metric("오늘 면접 연습", "89회", "+12")
    with col4:
        st.metric("이번 달 매출", "₩4,560,000", "+15%")

    st.divider()

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 일일 사용자 추이")
        # Placeholder chart data
        import random
        chart_data = {
            "date": [f"1/{i}" for i in range(1, 15)],
            "users": [random.randint(50, 150) for _ in range(14)]
        }
        st.line_chart(chart_data, x="date", y="users")

    with col2:
        st.subheader("💰 구독 분포")
        sub_data = {
            "tier": ["Free", "Standard", "Premium"],
            "count": [800, 300, 134]
        }
        st.bar_chart(sub_data, x="tier", y="count")

    st.divider()

    # Recent activity
    st.subheader("🕐 최근 활동")
    activities = [
        {"time": "5분 전", "user": "user123", "action": "면접 연습 완료", "detail": "자기소개 (85점)"},
        {"time": "12분 전", "user": "premium_user", "action": "멘토 세션 예약", "detail": "김멘토 - 1/30 14:00"},
        {"time": "23분 전", "user": "new_user", "action": "회원가입", "detail": "카카오 로그인"},
        {"time": "45분 전", "user": "user456", "action": "결제 완료", "detail": "Premium 월간 - ₩39,900"},
    ]

    for activity in activities:
        with st.container():
            cols = st.columns([1, 2, 3, 3])
            cols[0].write(activity["time"])
            cols[1].write(f"**{activity['user']}**")
            cols[2].write(activity["action"])
            cols[3].write(activity["detail"])

# =============================================================================
# User Management
# =============================================================================

elif menu == "👥 사용자 관리":
    st.header("사용자 관리")

    # Search and filters
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search = st.text_input("🔍 사용자 검색", placeholder="이메일 또는 이름")
    with col2:
        tier_filter = st.selectbox("구독 등급", ["전체", "Free", "Standard", "Premium"])
    with col3:
        status_filter = st.selectbox("상태", ["전체", "활성", "비활성"])

    # User table
    st.dataframe(
        {
            "ID": ["u001", "u002", "u003", "u004", "u005"],
            "이메일": ["user1@test.com", "user2@test.com", "user3@test.com", "user4@test.com", "user5@test.com"],
            "이름": ["홍길동", "김철수", "이영희", "박지민", "최민수"],
            "구독": ["Premium", "Standard", "Free", "Premium", "Standard"],
            "가입일": ["2024-01-15", "2024-01-10", "2024-01-08", "2024-01-05", "2024-01-03"],
            "마지막 접속": ["오늘", "어제", "3일 전", "오늘", "1주 전"],
            "면접 횟수": [45, 23, 5, 67, 12]
        },
        use_container_width=True
    )

    # User detail modal
    with st.expander("👤 사용자 상세 정보"):
        st.write("사용자를 선택하면 상세 정보가 표시됩니다.")

        col1, col2 = st.columns(2)
        with col1:
            st.text_input("이름", value="홍길동")
            st.text_input("이메일", value="user1@test.com")
            st.selectbox("구독 등급", ["Free", "Standard", "Premium"], index=2)
        with col2:
            st.date_input("구독 만료일")
            st.number_input("면접 제한 (일일)", value=999)
            st.checkbox("관리자 권한")

        if st.button("저장"):
            st.success("저장되었습니다.")

# =============================================================================
# Payment Management
# =============================================================================

elif menu == "💳 결제 관리":
    st.header("결제 관리")

    tab1, tab2, tab3 = st.tabs(["💰 결제 내역", "📊 매출 통계", "🔄 환불 처리"])

    with tab1:
        st.subheader("최근 결제 내역")
        st.dataframe(
            {
                "주문번호": ["ORD-20240128-001", "ORD-20240127-005", "ORD-20240127-003"],
                "사용자": ["user1@test.com", "user2@test.com", "user3@test.com"],
                "상품": ["Premium 월간", "Standard 연간", "Premium 월간"],
                "금액": ["₩39,900", "₩149,000", "₩39,900"],
                "결제수단": ["카카오페이", "토스", "카카오페이"],
                "상태": ["✅ 완료", "✅ 완료", "✅ 완료"],
                "일시": ["2024-01-28 14:30", "2024-01-27 09:15", "2024-01-27 08:45"]
            },
            use_container_width=True
        )

    with tab2:
        st.subheader("매출 통계")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("이번 달 매출", "₩4,560,000")
        with col2:
            st.metric("지난 달 대비", "+15%")
        with col3:
            st.metric("평균 객단가", "₩32,500")

    with tab3:
        st.subheader("환불 처리")
        with st.form("refund_form"):
            order_id = st.text_input("주문번호")
            reason = st.text_area("환불 사유")
            amount = st.number_input("환불 금액", min_value=0)

            if st.form_submit_button("환불 처리"):
                st.success(f"주문 {order_id}의 환불이 처리되었습니다.")

# =============================================================================
# Mentor Management
# =============================================================================

elif menu == "👨‍🏫 멘토 관리":
    st.header("멘토 관리")

    tab1, tab2, tab3 = st.tabs(["👥 멘토 목록", "✅ 승인 대기", "📊 세션 통계"])

    with tab1:
        st.dataframe(
            {
                "멘토명": ["김멘토", "이코치", "박선배"],
                "유형": ["현직 승무원", "현직 승무원", "전직 승무원"],
                "항공사": ["대한항공", "아시아나", "에미레이트"],
                "평점": ["4.9 ⭐", "4.7 ⭐", "4.8 ⭐"],
                "총 세션": [120, 85, 95],
                "시급": ["₩50,000", "₩45,000", "₩55,000"],
                "상태": ["✅ 활성", "✅ 활성", "⏸️ 휴무"]
            },
            use_container_width=True
        )

    with tab2:
        st.subheader("승인 대기 멘토")
        st.info("새로운 멘토 신청이 2건 있습니다.")

        with st.expander("신청자: 최멘토"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**이름:** 최영희")
                st.write("**유형:** 현직 승무원")
                st.write("**항공사:** 제주항공")
                st.write("**경력:** 3년")
            with col2:
                st.write("**자기소개:**")
                st.write("제주항공에서 3년간 근무 중인 현직 승무원입니다...")

            col1, col2 = st.columns(2)
            if col1.button("✅ 승인", key="approve1"):
                st.success("멘토가 승인되었습니다.")
            if col2.button("❌ 거절", key="reject1"):
                st.warning("멘토 신청이 거절되었습니다.")

    with tab3:
        st.subheader("세션 통계")
        st.metric("이번 달 총 세션", "234회")
        st.metric("평균 만족도", "4.8 / 5.0")

# =============================================================================
# Job Posting Management
# =============================================================================

elif menu == "📋 채용공고 관리":
    st.header("채용공고 관리")

    tab1, tab2 = st.tabs(["📋 공고 목록", "➕ 공고 등록"])

    with tab1:
        st.dataframe(
            {
                "항공사": ["대한항공", "아시아나", "제주항공"],
                "제목": ["2024 상반기 객실승무원", "경력 승무원 채용", "신입 승무원 모집"],
                "마감일": ["2024-02-28", "2024-02-15", "2024-03-10"],
                "상태": ["🟢 진행중", "🟡 마감임박", "🟢 진행중"],
                "조회수": [1234, 567, 890]
            },
            use_container_width=True
        )

    with tab2:
        st.subheader("새 채용공고 등록")
        with st.form("job_form"):
            col1, col2 = st.columns(2)
            with col1:
                airline = st.selectbox("항공사", ["대한항공", "아시아나", "제주항공", "기타"])
                title = st.text_input("공고 제목")
                job_type = st.selectbox("유형", ["객실승무원", "지상직", "기타"])
            with col2:
                start_date = st.date_input("시작일")
                end_date = st.date_input("마감일")
                source_url = st.text_input("원본 URL")

            description = st.text_area("상세 내용")
            requirements = st.text_area("지원 자격 (줄바꿈으로 구분)")

            if st.form_submit_button("등록"):
                st.success("채용공고가 등록되었습니다.")

# =============================================================================
# Content Management
# =============================================================================

elif menu == "📚 콘텐츠 관리":
    st.header("학습 콘텐츠 관리")

    tab1, tab2, tab3 = st.tabs(["📹 콘텐츠 목록", "➕ 콘텐츠 등록", "📊 인기 콘텐츠"])

    with tab1:
        st.dataframe(
            {
                "제목": ["영어 자기소개 완벽 가이드", "상황대처 질문 공략법", "면접 메이크업 튜토리얼"],
                "유형": ["📹 영상", "📄 문서", "📹 영상"],
                "스킬": ["영어 스피킹", "상황대처", "메이크업"],
                "난이도": ["초급", "중급", "초급"],
                "조회수": [5678, 3456, 2345],
                "평점": ["4.8 ⭐", "4.6 ⭐", "4.9 ⭐"],
                "프리미엄": ["❌", "✅", "❌"]
            },
            use_container_width=True
        )

    with tab2:
        with st.form("content_form"):
            title = st.text_input("콘텐츠 제목")
            col1, col2 = st.columns(2)
            with col1:
                content_type = st.selectbox("유형", ["영상", "문서", "퀴즈", "연습문제"])
                skill = st.selectbox("스킬 카테고리", ["자기소개", "지원동기", "상황대처", "영어", "메이크업"])
            with col2:
                difficulty = st.selectbox("난이도", ["초급", "중급", "고급"])
                is_premium = st.checkbox("프리미엄 콘텐츠")

            description = st.text_area("설명")
            content_url = st.text_input("콘텐츠 URL")

            if st.form_submit_button("등록"):
                st.success("콘텐츠가 등록되었습니다.")

    with tab3:
        st.subheader("인기 콘텐츠 TOP 5")
        for i, content in enumerate([
            ("영어 자기소개 완벽 가이드", 5678),
            ("면접 실전 꿀팁 10가지", 4567),
            ("상황대처 질문 공략법", 3456),
            ("대한항공 면접 후기", 3234),
            ("아시아나 채용 트렌드", 2890)
        ], 1):
            st.write(f"**{i}. {content[0]}** - {content[1]:,}회 조회")

# =============================================================================
# Notification Management
# =============================================================================

elif menu == "🔔 알림 관리":
    st.header("알림 관리")

    tab1, tab2 = st.tabs(["📤 알림 발송", "📋 발송 내역"])

    with tab1:
        st.subheader("시스템 알림 발송")
        with st.form("notification_form"):
            target = st.multiselect(
                "대상",
                ["전체 사용자", "Premium 구독자", "Standard 구독자", "Free 사용자"]
            )
            title = st.text_input("알림 제목")
            message = st.text_area("알림 내용")

            col1, col2 = st.columns(2)
            with col1:
                send_push = st.checkbox("푸시 알림", value=True)
                send_email = st.checkbox("이메일")
            with col2:
                schedule = st.checkbox("예약 발송")
                if schedule:
                    scheduled_time = st.datetime_input("발송 시간")

            if st.form_submit_button("발송"):
                st.success("알림이 발송되었습니다.")

    with tab2:
        st.dataframe(
            {
                "제목": ["시스템 점검 안내", "새로운 기능 출시", "연말 이벤트 안내"],
                "대상": ["전체", "Premium", "전체"],
                "발송일": ["2024-01-28", "2024-01-25", "2024-01-20"],
                "수신": ["1,234명", "456명", "1,100명"],
                "열람률": ["78%", "92%", "65%"]
            },
            use_container_width=True
        )

# =============================================================================
# System Settings
# =============================================================================

elif menu == "⚙️ 시스템 설정":
    st.header("시스템 설정")

    tab1, tab2, tab3 = st.tabs(["🔧 일반 설정", "🔐 보안", "📊 시스템 상태"])

    with tab1:
        st.subheader("일반 설정")

        with st.form("general_settings"):
            st.write("**면접 제한 설정**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.number_input("Free 일일 제한", value=3)
            with col2:
                st.number_input("Standard 일일 제한", value=50)
            with col3:
                st.number_input("Premium 일일 제한", value=999)

            st.write("**AI 설정**")
            st.selectbox("기본 AI 모델", ["gpt-4o-mini", "gpt-4o", "gpt-4"])
            st.slider("응답 창의성 (Temperature)", 0.0, 1.0, 0.7)

            if st.form_submit_button("설정 저장"):
                st.success("설정이 저장되었습니다.")

    with tab2:
        st.subheader("보안 설정")

        col1, col2 = st.columns(2)
        with col1:
            st.write("**비밀번호 정책**")
            st.checkbox("최소 8자 이상", value=True)
            st.checkbox("특수문자 포함", value=True)
            st.checkbox("숫자 포함", value=True)

        with col2:
            st.write("**세션 설정**")
            st.number_input("세션 타임아웃 (분)", value=60)
            st.number_input("최대 동시 접속", value=3)

        if st.button("보안 설정 저장"):
            st.success("보안 설정이 저장되었습니다.")

    with tab3:
        st.subheader("시스템 상태")

        # System health
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("API 서버", "🟢 정상")
        with col2:
            st.metric("데이터베이스", "🟢 정상")
        with col3:
            st.metric("AI 서비스", "🟢 정상")
        with col4:
            st.metric("결제 연동", "🟢 정상")

        st.divider()

        # Server info
        col1, col2 = st.columns(2)
        with col1:
            st.write("**서버 정보**")
            st.write("- CPU 사용률: 35%")
            st.write("- 메모리 사용률: 62%")
            st.write("- 디스크 사용률: 48%")

        with col2:
            st.write("**데이터베이스**")
            st.write("- 총 사용자: 1,234명")
            st.write("- 총 면접 기록: 15,678건")
            st.write("- 총 결제: 2,345건")

        if st.button("🔄 데이터베이스 백업"):
            st.info("백업이 시작되었습니다...")
            st.success("백업이 완료되었습니다.")

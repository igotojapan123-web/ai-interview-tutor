# pages/90_시스템관리.py
# FlyReady Lab - 관리자 대시보드
# 사용자/구독/수익 관리, 에러 모니터링, 시스템 상태

import streamlit as st
import os
import sys
from datetime import datetime, timedelta
import json

# 상위 디렉토리 import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="관리자 대시보드 | FlyReady Lab",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 로깅
try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# 관리자 모듈 import
ADMIN_AVAILABLE = False
ERROR_MONITOR_AVAILABLE = False
ALERTS_AVAILABLE = False
REPORTS_AVAILABLE = False

try:
    from admin_dashboard import (
        UserManager, SubscriptionManager, RevenueManager,
        UsageStatsManager, AuditLogger, get_dashboard_summary
    )
    ADMIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"admin_dashboard 로드 실패: {e}")

try:
    from error_monitor import (
        ErrorLogger, ErrorAnalyzer, APIUsageMonitor,
        run_health_check, get_error_stats
    )
    ERROR_MONITOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"error_monitor 로드 실패: {e}")

try:
    from admin_alerts import AlertManager, AlertType
    ALERTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"admin_alerts 로드 실패: {e}")

try:
    from weekly_report import (
        ReportGenerator, run_full_check, generate_quick_report
    )
    REPORTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"weekly_report 로드 실패: {e}")

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
* { font-family: 'Pretendard', sans-serif; }

.admin-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
    color: white;
    padding: 20px 30px;
    border-radius: 12px;
    margin-bottom: 24px;
}
.admin-header h1 { margin: 0; font-size: 1.5rem; }
.admin-header p { margin: 8px 0 0 0; opacity: 0.8; font-size: 0.9rem; }

.metric-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border-left: 4px solid #3b82f6;
}
.metric-card.success { border-left-color: #10b981; }
.metric-card.warning { border-left-color: #f59e0b; }
.metric-card.danger { border-left-color: #ef4444; }
.metric-card .label { font-size: 0.85rem; color: #64748b; margin-bottom: 4px; }
.metric-card .value { font-size: 1.75rem; font-weight: 700; color: #1e3a5f; }
.metric-card .change { font-size: 0.85rem; margin-top: 4px; }
.metric-card .change.up { color: #10b981; }
.metric-card .change.down { color: #ef4444; }

.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}
.status-badge.healthy { background: #d1fae5; color: #065f46; }
.status-badge.warning { background: #fef3c7; color: #92400e; }
.status-badge.error { background: #fee2e2; color: #991b1b; }

.section-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1e3a5f;
    margin: 24px 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid #e2e8f0;
}

.alert-item {
    background: #f8fafc;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    border-left: 3px solid #3b82f6;
}
.alert-item.error { border-left-color: #ef4444; background: #fef2f2; }
.alert-item.warning { border-left-color: #f59e0b; background: #fffbeb; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 인증 체크
# ============================================================

def check_admin_auth():
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    return st.session_state.admin_authenticated

def admin_login():
    st.markdown("""
    <div class="admin-header">
        <h1>FlyReady Lab 관리자</h1>
        <p>관리자 인증이 필요합니다</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("admin_login"):
            password = st.text_input("관리자 비밀번호", type="password")
            submit = st.form_submit_button("로그인", use_container_width=True)

            if submit:
                admin_pw = os.getenv("ADMIN_PASSWORD", "admin123")
                if password == admin_pw:
                    st.session_state.admin_authenticated = True
                    if ADMIN_AVAILABLE:
                        audit = AuditLogger()
                        audit.log("admin_login", "admin", level="info")
                    st.rerun()
                else:
                    st.error("비밀번호가 올바르지 않습니다.")

if not check_admin_auth():
    admin_login()
    st.stop()

# ============================================================
# 사이드바
# ============================================================

st.sidebar.markdown("### 관리 메뉴")

menu = st.sidebar.radio(
    "메뉴",
    ["대시보드", "사용자 관리", "구독/수익", "에러 모니터링", "시스템 상태", "알림 설정", "리포트"],
    label_visibility="collapsed"
)

st.sidebar.divider()

if st.sidebar.button("로그아웃", use_container_width=True):
    st.session_state.admin_authenticated = False
    st.rerun()

# 모듈 상태
st.sidebar.markdown("### 모듈 상태")
st.sidebar.write(f"- Admin: {'OK' if ADMIN_AVAILABLE else 'X'}")
st.sidebar.write(f"- Error Monitor: {'OK' if ERROR_MONITOR_AVAILABLE else 'X'}")
st.sidebar.write(f"- Alerts: {'OK' if ALERTS_AVAILABLE else 'X'}")
st.sidebar.write(f"- Reports: {'OK' if REPORTS_AVAILABLE else 'X'}")

# ============================================================
# 대시보드
# ============================================================

if menu == "대시보드":
    st.markdown("""
    <div class="admin-header">
        <h1>FlyReady Lab 관리자 대시보드</h1>
        <p>실시간 서비스 현황 및 지표</p>
    </div>
    """, unsafe_allow_html=True)

    # 핵심 지표
    if ADMIN_AVAILABLE:
        summary = get_dashboard_summary()
        users = summary.get("users", {})
        revenue = summary.get("revenue", {})
        usage = summary.get("usage", {})
    else:
        users = {"total_users": 0, "active_users_7d": 0, "new_users_7d": 0}
        revenue = {"mrr": 0, "revenue_7d": 0}
        usage = {"dau_today": 0}

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">총 사용자</div>
            <div class="value">{users.get('total_users', 0):,}</div>
            <div class="change up">+{users.get('new_users_7d', 0)} 이번 주</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card success">
            <div class="label">월간 반복 수익 (MRR)</div>
            <div class="value">{revenue.get('mrr', 0):,}원</div>
            <div class="change">활성 구독 기준</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">오늘 활성 사용자</div>
            <div class="value">{usage.get('dau_today', 0):,}</div>
            <div class="change">DAU</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        if ERROR_MONITOR_AVAILABLE:
            error_stats = get_error_stats()
            errors_24h = error_stats.get("errors_24h", 0)
        else:
            errors_24h = 0

        card_class = "danger" if errors_24h > 10 else ("warning" if errors_24h > 0 else "success")
        st.markdown(f"""
        <div class="metric-card {card_class}">
            <div class="label">24시간 에러</div>
            <div class="value">{errors_24h}</div>
            <div class="change">{'주의 필요' if errors_24h > 5 else '정상'}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">시스템 상태</div>', unsafe_allow_html=True)

    if ERROR_MONITOR_AVAILABLE:
        health = run_health_check()
        status = health.get("status", "unknown")
        status_class = "healthy" if status == "healthy" else ("warning" if status == "degraded" else "error")

        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f'<span class="status-badge {status_class}">{status.upper()}</span>', unsafe_allow_html=True)
        with col2:
            checks = health.get("checks", [])
            passed = sum(1 for c in checks if c.get("status") == "pass")
            st.write(f"헬스 체크: {passed}/{len(checks)} 통과")
    else:
        st.info("에러 모니터링 모듈이 로드되지 않았습니다.")

    # 빠른 작업
    st.markdown('<div class="section-title">빠른 작업</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("전체 점검 실행", use_container_width=True):
            if REPORTS_AVAILABLE:
                with st.spinner("점검 중..."):
                    result = run_full_check()
                st.success(f"점검 완료: {result.get('overall_status', 'unknown')}")
            else:
                st.warning("리포트 모듈 필요")

    with col2:
        if st.button("주간 리포트 생성", use_container_width=True):
            if REPORTS_AVAILABLE:
                with st.spinner("생성 중..."):
                    generator = ReportGenerator()
                    report = generator.generate_weekly_report()
                st.success(f"리포트 생성: {report.get('period', '')}")
            else:
                st.warning("리포트 모듈 필요")

    with col3:
        if st.button("테스트 알림 전송", use_container_width=True):
            if ALERTS_AVAILABLE:
                alert_mgr = AlertManager()
                result = alert_mgr.send("테스트 알림", "관리자 대시보드에서 전송된 테스트입니다.", AlertType.INFO)
                if result.get("success"):
                    st.success("알림 전송 완료")
                else:
                    st.warning("알림 채널 미설정")
            else:
                st.warning("알림 모듈 필요")

    with col4:
        if st.button("에러 로그 보기", use_container_width=True):
            st.session_state.show_errors = True

    if st.session_state.get("show_errors"):
        if ERROR_MONITOR_AVAILABLE:
            error_logger = ErrorLogger()
            recent_errors = error_logger.get_errors(days=1, level="error")[:5]

            st.markdown('<div class="section-title">최근 에러 (24시간)</div>', unsafe_allow_html=True)

            if recent_errors:
                for error in recent_errors:
                    st.markdown(f"""
                    <div class="alert-item error">
                        <strong>{error.get('type', 'Unknown')}</strong>
                        <br><small>{error.get('message', '')[:100]}</small>
                        <br><small style="color:#64748b">{error.get('timestamp', '')}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("최근 24시간 에러 없음")

# ============================================================
# 사용자 관리
# ============================================================

elif menu == "사용자 관리":
    st.markdown('<div class="section-title">사용자 관리</div>', unsafe_allow_html=True)

    if ADMIN_AVAILABLE:
        user_mgr = UserManager()
        stats = user_mgr.get_user_statistics()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 사용자", f"{stats.get('total_users', 0):,}")
        with col2:
            st.metric("7일 활성", f"{stats.get('active_users_7d', 0):,}")
        with col3:
            st.metric("신규 (7일)", f"{stats.get('new_users_7d', 0):,}")
        with col4:
            by_plan = stats.get("by_plan", {})
            premium = by_plan.get("premium_monthly", 0) + by_plan.get("premium_yearly", 0)
            st.metric("프리미엄", f"{premium:,}")

        st.divider()

        # 플랜별 분포
        st.subheader("플랜별 분포")
        by_plan = stats.get("by_plan", {})
        if by_plan:
            import pandas as pd
            df = pd.DataFrame([
                {"플랜": k, "사용자 수": v}
                for k, v in by_plan.items()
            ])
            st.bar_chart(df.set_index("플랜"))
        else:
            st.info("데이터 없음")

        st.divider()

        # 사용자 목록
        st.subheader("최근 가입 사용자")
        new_users = user_mgr.get_new_users(30)[:10]

        if new_users:
            for user in new_users:
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                with col1:
                    st.write(f"**{user.get('email', 'N/A')}**")
                with col2:
                    st.write(user.get('plan', 'free'))
                with col3:
                    st.write(user.get('created_at', '')[:10])
                with col4:
                    st.write(user.get('status', 'active'))
        else:
            st.info("최근 가입자 없음")
    else:
        st.warning("관리자 모듈이 로드되지 않았습니다.")

# ============================================================
# 구독/수익
# ============================================================

elif menu == "구독/수익":
    st.markdown('<div class="section-title">구독 및 수익 관리</div>', unsafe_allow_html=True)

    if ADMIN_AVAILABLE:
        sub_mgr = SubscriptionManager()
        rev_mgr = RevenueManager()

        sub_stats = sub_mgr.get_subscription_statistics()
        rev_stats = rev_mgr.get_revenue_statistics()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("활성 구독", f"{sub_stats.get('active_subscriptions', 0):,}")
        with col2:
            st.metric("MRR", f"{rev_stats.get('mrr', 0):,}원")
        with col3:
            st.metric("7일 매출", f"{rev_stats.get('revenue_7d', 0):,}원")
        with col4:
            churn = sub_mgr.get_churn_rate(30)
            st.metric("이탈률 (30일)", f"{churn:.1f}%")

        st.divider()

        tab1, tab2, tab3 = st.tabs(["구독 현황", "수익 추이", "만료 예정"])

        with tab1:
            st.subheader("플랜별 구독")
            by_plan = sub_stats.get("by_plan", {})
            if by_plan:
                for plan, count in by_plan.items():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{plan}**")
                    with col2:
                        st.write(f"{count}명")
            else:
                st.info("구독 데이터 없음")

        with tab2:
            st.subheader("일별 수익")
            daily = rev_stats.get("daily_revenue", [])
            if daily:
                import pandas as pd
                df = pd.DataFrame(daily)
                st.line_chart(df.set_index("date"))
            else:
                st.info("수익 데이터 없음")

        with tab3:
            st.subheader("7일 내 만료 예정")
            expiring = sub_mgr.get_expiring_subscriptions(7)
            if expiring:
                for sub in expiring[:10]:
                    st.write(f"- {sub.get('user_id', 'N/A')} | {sub.get('plan', '')} | 만료: {sub.get('expires_at', '')[:10]}")
            else:
                st.success("7일 내 만료 예정 없음")
    else:
        st.warning("관리자 모듈이 로드되지 않았습니다.")

# ============================================================
# 에러 모니터링
# ============================================================

elif menu == "에러 모니터링":
    st.markdown('<div class="section-title">에러 모니터링</div>', unsafe_allow_html=True)

    if ERROR_MONITOR_AVAILABLE:
        error_logger = ErrorLogger()
        analyzer = ErrorAnalyzer()
        api_monitor = APIUsageMonitor()

        stats = error_logger.get_statistics()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 에러", f"{stats.get('total', 0):,}")
        with col2:
            st.metric("24시간", f"{stats.get('errors_24h', 0)}")
        with col3:
            st.metric("7일", f"{stats.get('errors_7d', 0)}")
        with col4:
            st.metric("미해결", f"{stats.get('unresolved', 0)}")

        st.divider()

        tab1, tab2, tab3 = st.tabs(["최근 에러", "에러 분석", "API 사용량"])

        with tab1:
            errors = error_logger.get_errors(days=7)[:20]
            if errors:
                for error in errors:
                    level = error.get('level', 'error')
                    item_class = 'error' if level in ['error', 'critical'] else 'warning'
                    st.markdown(f"""
                    <div class="alert-item {item_class}">
                        <strong>[{level.upper()}] {error.get('type', 'Unknown')}</strong>
                        <br>{error.get('message', '')[:150]}
                        <br><small>페이지: {error.get('page', 'N/A')} | {error.get('timestamp', '')}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("최근 에러 없음")

        with tab2:
            st.subheader("자주 발생하는 에러")
            top_errors = analyzer.get_top_errors(days=7, limit=5)
            if top_errors:
                for err in top_errors:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{err.get('type', 'Unknown')}**")
                    with col2:
                        st.write(f"{err.get('count', 0)}회")
            else:
                st.info("데이터 없음")

            st.subheader("에러 핫스팟 (페이지)")
            hotspots = analyzer.get_error_hotspots(days=7)
            if hotspots:
                for spot in hotspots[:5]:
                    st.write(f"- {spot.get('page', 'N/A')}: {spot.get('count', 0)}건")
            else:
                st.info("데이터 없음")

        with tab3:
            st.subheader("API 사용량 (오늘)")
            usage = api_monitor.get_usage_summary()
            for api_name, data in usage.items():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**{api_name}**")
                with col2:
                    st.progress(min(data.get('percentage', 0) / 100, 1.0))
                with col3:
                    st.write(f"{data.get('current', 0):,} / {data.get('limit', 0):,}")
    else:
        st.warning("에러 모니터링 모듈이 로드되지 않았습니다.")

# ============================================================
# 시스템 상태
# ============================================================

elif menu == "시스템 상태":
    st.markdown('<div class="section-title">시스템 상태</div>', unsafe_allow_html=True)

    if ERROR_MONITOR_AVAILABLE:
        health = run_health_check()

        status = health.get("status", "unknown")
        status_class = "healthy" if status == "healthy" else ("warning" if status == "degraded" else "error")

        st.markdown(f"""
        <div style="text-align:center; padding:20px;">
            <span class="status-badge {status_class}" style="font-size:1.2rem; padding:8px 24px;">
                시스템 상태: {status.upper()}
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        st.subheader("헬스 체크 결과")
        checks = health.get("checks", [])

        for check in checks:
            check_status = check.get("status", "unknown")
            icon = "✅" if check_status == "pass" else ("⚠️" if check_status == "warning" else "❌")

            col1, col2, col3 = st.columns([1, 3, 2])
            with col1:
                st.write(icon)
            with col2:
                st.write(f"**{check.get('name', 'Unknown')}**")
            with col3:
                st.write(check_status)

        st.divider()

        if st.button("새로고침", use_container_width=True):
            st.rerun()
    else:
        st.warning("에러 모니터링 모듈이 로드되지 않았습니다.")

    # 환경 변수 상태
    st.subheader("환경 변수 상태")

    env_vars = [
        ("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", "")),
        ("DID_API_KEY", os.getenv("DID_API_KEY", "")),
        ("TELEGRAM_BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN", "")),
        ("SLACK_WEBHOOK_URL", os.getenv("SLACK_WEBHOOK_URL", "")),
        ("SENTRY_DSN", os.getenv("SENTRY_DSN", "")),
    ]

    for name, value in env_vars:
        status = "설정됨" if value and len(value) > 5 else "미설정"
        icon = "✅" if status == "설정됨" else "❌"
        st.write(f"{icon} **{name}**: {status}")

# ============================================================
# 알림 설정
# ============================================================

elif menu == "알림 설정":
    st.markdown('<div class="section-title">알림 설정</div>', unsafe_allow_html=True)

    if ALERTS_AVAILABLE:
        alert_mgr = AlertManager()

        # 현재 설정
        st.subheader("알림 채널 상태")

        channels = [
            ("텔레그램", alert_mgr.telegram.enabled),
            ("슬랙", alert_mgr.slack.enabled),
            ("이메일", alert_mgr.email.enabled),
        ]

        for name, enabled in channels:
            icon = "✅" if enabled else "❌"
            status = "활성" if enabled else "미설정"
            st.write(f"{icon} **{name}**: {status}")

        st.divider()

        # 테스트 전송
        st.subheader("테스트 알림 전송")

        col1, col2 = st.columns(2)
        with col1:
            test_title = st.text_input("제목", value="테스트 알림")
        with col2:
            test_type = st.selectbox("유형", ["INFO", "WARNING", "ERROR"])

        test_content = st.text_area("내용", value="관리자 대시보드에서 전송된 테스트 알림입니다.")

        if st.button("알림 전송", type="primary"):
            alert_type = getattr(AlertType, test_type)
            result = alert_mgr.send(test_title, test_content, alert_type)

            if result.get("success"):
                st.success(f"전송 완료: {result.get('channels_sent', [])}")
            else:
                st.warning(f"전송 실패: {result.get('reason', 'unknown')}")

        st.divider()

        # 알림 히스토리
        st.subheader("최근 알림 히스토리")
        history = alert_mgr.history.get("alerts", [])[-10:]

        if history:
            for alert in reversed(history):
                st.write(f"- [{alert.get('type', '')}] {alert.get('title', '')} | {alert.get('sent_at', '')[:16]}")
        else:
            st.info("히스토리 없음")
    else:
        st.warning("알림 모듈이 로드되지 않았습니다.")

        st.info("""
        알림을 활성화하려면 환경 변수를 설정하세요:

        **텔레그램:**
        - TELEGRAM_BOT_TOKEN
        - TELEGRAM_CHAT_ID

        **슬랙:**
        - SLACK_WEBHOOK_URL

        **이메일:**
        - SMTP_USER
        - SMTP_PASSWORD
        - ADMIN_EMAIL
        """)

# ============================================================
# 리포트
# ============================================================

elif menu == "리포트":
    st.markdown('<div class="section-title">리포트</div>', unsafe_allow_html=True)

    if REPORTS_AVAILABLE:
        generator = ReportGenerator()

        tab1, tab2, tab3 = st.tabs(["빠른 점검", "리포트 생성", "히스토리"])

        with tab1:
            st.subheader("시스템 빠른 점검")

            if st.button("점검 실행", type="primary"):
                with st.spinner("점검 중..."):
                    report = generate_quick_report()
                st.code(report)

        with tab2:
            st.subheader("리포트 생성")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("일일 리포트", use_container_width=True):
                    with st.spinner("생성 중..."):
                        report = generator.generate_daily_report()
                    st.success(f"생성 완료: {report.get('date', '')}")
                    st.json(report.get("sections", {}))

            with col2:
                if st.button("주간 리포트", use_container_width=True):
                    with st.spinner("생성 중..."):
                        report = generator.generate_weekly_report()
                    st.success(f"생성 완료: {report.get('period', '')}")
                    st.json(report.get("summary", {}))

            with col3:
                if st.button("월간 리포트", use_container_width=True):
                    with st.spinner("생성 중..."):
                        report = generator.generate_monthly_report()
                    st.success(f"생성 완료: {report.get('period', '')}")
                    st.json(report.get("summary", {}))

        with tab3:
            st.subheader("생성된 리포트")
            recent = generator.get_recent_reports(limit=10)

            if recent:
                for r in reversed(recent):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.write(f"**{r.get('type', '')}**")
                    with col2:
                        st.write(r.get('period', r.get('generated_at', '')[:10]))
                    with col3:
                        st.write("📄")
            else:
                st.info("생성된 리포트 없음")
    else:
        st.warning("리포트 모듈이 로드되지 않았습니다.")

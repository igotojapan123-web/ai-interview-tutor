# pages/33_채용정보.py
# FlyReady Lab - 채용 정보 페이지

import streamlit as st
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="채용 정보 - FlyReady Lab",
    page_icon="✈️",
    layout="wide"
)

# 시스템 import
try:
    from job_crawler import JobCrawlerManager, AirlineCode, JobType
    JOB_AVAILABLE = True
    job_manager = JobCrawlerManager()
except ImportError:
    JOB_AVAILABLE = False
    job_manager = None

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

.job-card {
    background: white;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border-left: 4px solid #3b82f6;
    transition: all 0.2s;
}
.job-card:hover {
    transform: translateX(4px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}
.job-card.urgent {
    border-left-color: #ef4444;
    background: #fef2f2;
}
.job-card.upcoming {
    border-left-color: #f59e0b;
}

.job-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
}
.job-airline {
    font-size: 0.8rem;
    color: #3b82f6;
    font-weight: 600;
    margin-bottom: 4px;
}
.job-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1e3a5f;
}
.job-deadline {
    font-size: 0.9rem;
    font-weight: 700;
    padding: 6px 14px;
    border-radius: 20px;
    background: #eff6ff;
    color: #3b82f6;
}
.job-deadline.urgent {
    background: #fee2e2;
    color: #ef4444;
}

.job-info {
    display: flex;
    gap: 20px;
    margin: 16px 0;
    flex-wrap: wrap;
}
.job-info-item {
    font-size: 0.85rem;
    color: #64748b;
}
.job-info-item strong {
    color: #334155;
}

.job-requirements {
    background: #f8fafc;
    border-radius: 8px;
    padding: 16px;
    margin: 16px 0;
}
.job-requirements h4 {
    font-size: 0.9rem;
    font-weight: 600;
    color: #334155;
    margin: 0 0 12px 0;
}
.job-requirements ul {
    margin: 0;
    padding-left: 20px;
}
.job-requirements li {
    font-size: 0.85rem;
    color: #475569;
    margin-bottom: 6px;
}

.job-actions {
    display: flex;
    gap: 12px;
    margin-top: 16px;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 32px;
}
.stat-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.stat-value {
    font-size: 2rem;
    font-weight: 800;
    color: #1e3a5f;
}
.stat-label {
    font-size: 0.85rem;
    color: #64748b;
}

@media (max-width: 768px) {
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
}

/* Material Icon 텍스트 폴백 숨김 */
[data-testid="stIconMaterial"] {
    font-size: 0 !important;
    line-height: 0 !important;
    overflow: hidden !important;
}
</style>
""", unsafe_allow_html=True)

# 헤더
st.markdown("""
<div class="page-header">
    <h1>항공사 채용 정보</h1>
    <p>국내외 항공사 최신 채용 공고를 한눈에 확인하세요</p>
</div>
""", unsafe_allow_html=True)

if not JOB_AVAILABLE:
    st.warning("채용 정보 시스템을 불러올 수 없습니다.")
    st.stop()

# 새로고침 버튼
col1, col2, col3 = st.columns([2, 1, 1])
with col3:
    if st.button("새로고침", use_container_width=True):
        with st.spinner("채용 정보 업데이트 중..."):
            job_manager.crawl_all()
        st.success("업데이트 완료!")
        st.rerun()

# 통계
all_jobs = job_manager.load_jobs()
open_jobs = [j for j in all_jobs if j.get('status') in ['open', 'upcoming']]
upcoming_deadlines = job_manager.get_upcoming_deadlines(7)

st.markdown(f"""
<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-value">{len(all_jobs)}</div>
        <div class="stat-label">전체 공고</div>
    </div>
    <div class="stat-card">
        <div class="stat-value" style="color:#10b981">{len(open_jobs)}</div>
        <div class="stat-label">진행중</div>
    </div>
    <div class="stat-card">
        <div class="stat-value" style="color:#ef4444">{len(upcoming_deadlines)}</div>
        <div class="stat-label">7일 내 마감</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{len(set(j.get('airline_code') for j in all_jobs))}</div>
        <div class="stat-label">항공사</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 필터
col1, col2, col3 = st.columns(3)

AIRLINE_NAMES = {
    "KE": "대한항공", "OZ": "아시아나항공", "7C": "제주항공",
    "LJ": "진에어", "TW": "티웨이항공", "BX": "에어부산",
    "RS": "에어서울", "EK": "에미레이트", "SQ": "싱가포르항공",
    "CX": "캐세이퍼시픽", "QR": "카타르항공", "EY": "에티하드"
}

with col1:
    airline_filter = st.selectbox(
        "항공사",
        ["전체"] + list(AIRLINE_NAMES.keys()),
        format_func=lambda x: AIRLINE_NAMES.get(x, x) if x != "전체" else "전체"
    )

with col2:
    status_filter = st.selectbox(
        "상태",
        ["전체", "open", "upcoming", "closed"],
        format_func=lambda x: {"전체": "전체", "open": "진행중", "upcoming": "예정", "closed": "마감"}.get(x, x)
    )

with col3:
    region_filter = st.selectbox(
        "지역",
        ["전체", "국내", "외항사"],
        format_func=lambda x: x
    )

st.markdown("---")

# 채용 공고 목록
jobs = job_manager.get_open_jobs(
    airline_code=None if airline_filter == "전체" else airline_filter
)

# 상태 필터
if status_filter != "전체":
    jobs = [j for j in jobs if j.status == status_filter]

# 지역 필터
domestic_codes = ["KE", "OZ", "7C", "LJ", "TW", "BX", "RS", "ZE"]
if region_filter == "국내":
    jobs = [j for j in jobs if j.airline_code in domestic_codes]
elif region_filter == "외항사":
    jobs = [j for j in jobs if j.airline_code not in domestic_codes]

if not jobs:
    st.info("조건에 맞는 채용 공고가 없습니다.")
else:
    st.caption(f"총 {len(jobs)}건의 채용 공고")

    for job in jobs:
        # 마감일 계산
        days_left = None
        deadline_text = ""
        urgent = False

        if job.end_date:
            try:
                end = datetime.strptime(job.end_date, "%Y-%m-%d").date()
                days_left = (end - datetime.now().date()).days

                if days_left < 0:
                    deadline_text = "마감"
                elif days_left == 0:
                    deadline_text = "D-Day"
                    urgent = True
                else:
                    deadline_text = f"D-{days_left}"
                    urgent = days_left <= 3
            except Exception:
                deadline_text = job.end_date

        card_class = "urgent" if urgent else ("upcoming" if job.status == "upcoming" else "")
        deadline_class = "urgent" if urgent else ""

        # 지원 자격 HTML
        requirements_html = ""
        if job.requirements:
            req_items = "".join([f"<li><strong>{k}:</strong> {v}</li>" for k, v in job.requirements.items()])
            requirements_html = f"""
            <div class="job-requirements">
                <h4>지원 자격</h4>
                <ul>{req_items}</ul>
            </div>
            """

        st.markdown(f"""
        <div class="job-card {card_class}">
            <div class="job-header">
                <div>
                    <div class="job-airline">{job.airline_name}</div>
                    <div class="job-title">{job.title}</div>
                </div>
                <div class="job-deadline {deadline_class}">{deadline_text}</div>
            </div>
            <div class="job-info">
                <div class="job-info-item"><strong>접수기간:</strong> {job.start_date or '미정'} ~ {job.end_date or '미정'}</div>
                <div class="job-info-item"><strong>근무지:</strong> {job.location or '미정'}</div>
                {f'<div class="job-info-item"><strong>어학:</strong> {", ".join([f"{k} {v}" for k, v in (job.language or {}).items()])}</div>' if job.language else ''}
            </div>
            {requirements_html}
        </div>
        """, unsafe_allow_html=True)

        # 지원 버튼
        col1, col2 = st.columns([3, 1])
        with col2:
            if job.application_url:
                st.link_button("지원하기", job.application_url, use_container_width=True)

        st.write("")

# 알림 설정 섹션
st.markdown("---")
st.subheader("채용 알림 설정")

user_id = st.session_state.get("user_id", "guest")

with st.expander("관심 항공사 설정"):
    selected_airlines = st.multiselect(
        "알림 받을 항공사 선택",
        list(AIRLINE_NAMES.keys()),
        default=["KE", "OZ"],
        format_func=lambda x: AIRLINE_NAMES.get(x, x)
    )

    col1, col2 = st.columns(2)
    with col1:
        notify_new = st.checkbox("새 공고 알림", value=True)
        notify_d7 = st.checkbox("마감 7일 전 알림", value=True)
    with col2:
        notify_d3 = st.checkbox("마감 3일 전 알림", value=True)
        notify_d1 = st.checkbox("마감 1일 전 알림", value=True)

    if st.button("설정 저장"):
        # 설정 저장 로직
        st.success("알림 설정이 저장되었습니다!")

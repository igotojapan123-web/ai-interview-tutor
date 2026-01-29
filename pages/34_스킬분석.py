# pages/34_스킬분석.py
# FlyReady Lab - 스킬 분석 대시보드

import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="스킬 분석 - FlyReady Lab",
    page_icon="✈️",
    layout="wide"
)

# 시스템 import
try:
    from recommendation_system import RecommendationEngine, SkillAnalyzer, SkillCategory
    REC_AVAILABLE = True
    rec_engine = RecommendationEngine()
    skill_analyzer = SkillAnalyzer()
except ImportError:
    REC_AVAILABLE = False
    rec_engine = None

# CSS
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
* { font-family: 'Pretendard', -apple-system, sans-serif; }
[data-testid="stSidebar"] { display: none; }
.block-container { max-width: 1100px; padding-top: 32px; }

.page-header h1 {
    font-size: 1.75rem;
    font-weight: 800;
    color: #1e3a5f;
    margin-bottom: 8px;
}

.readiness-card {
    background: linear-gradient(135deg, #1e3a5f 0%, #3b82f6 100%);
    border-radius: 20px;
    padding: 32px;
    color: white;
    text-align: center;
    margin-bottom: 32px;
}
.readiness-score {
    font-size: 4rem;
    font-weight: 800;
    margin: 16px 0;
}
.readiness-label {
    font-size: 1.1rem;
    opacity: 0.9;
}
.readiness-desc {
    font-size: 0.9rem;
    opacity: 0.7;
    margin-top: 8px;
}

.skill-section {
    background: white;
    border-radius: 16px;
    padding: 28px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    margin-bottom: 24px;
}
.skill-section h3 {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1e3a5f;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e2e8f0;
}

.skill-bar-container {
    margin-bottom: 16px;
}
.skill-bar-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
}
.skill-bar-name {
    font-size: 0.9rem;
    font-weight: 600;
    color: #334155;
}
.skill-bar-score {
    font-size: 0.9rem;
    font-weight: 700;
    color: #1e3a5f;
}
.skill-bar {
    height: 10px;
    background: #e2e8f0;
    border-radius: 5px;
    overflow: hidden;
}
.skill-bar-fill {
    height: 100%;
    border-radius: 5px;
    transition: width 0.5s ease;
}
.skill-bar-fill.high { background: #10b981; }
.skill-bar-fill.medium { background: #3b82f6; }
.skill-bar-fill.low { background: #f59e0b; }
.skill-bar-fill.critical { background: #ef4444; }

.insight-card {
    background: #f8fafc;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 12px;
    border-left: 4px solid #3b82f6;
}
.insight-card.warning { border-left-color: #f59e0b; }
.insight-card.danger { border-left-color: #ef4444; }
.insight-card.success { border-left-color: #10b981; }
.insight-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #1e3a5f;
    margin-bottom: 6px;
}
.insight-desc {
    font-size: 0.85rem;
    color: #64748b;
}

.recommendation-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    background: #f8fafc;
    border-radius: 10px;
    margin-bottom: 12px;
    transition: all 0.2s;
}
.recommendation-item:hover {
    background: #eff6ff;
    transform: translateX(4px);
}
.rec-priority {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    color: white;
    flex-shrink: 0;
}
.rec-priority.high { background: #ef4444; }
.rec-priority.medium { background: #f59e0b; }
.rec-priority.low { background: #3b82f6; }
.rec-content h4 {
    font-size: 0.95rem;
    font-weight: 600;
    color: #1e3a5f;
    margin: 0 0 4px 0;
}
.rec-content p {
    font-size: 0.8rem;
    color: #64748b;
    margin: 0;
}
</style>
""", unsafe_allow_html=True)

# 헤더
st.markdown("""
<div class="page-header">
    <h1>나의 스킬 분석</h1>
    <p>AI가 분석한 면접 준비 현황과 맞춤 학습 가이드</p>
</div>
""", unsafe_allow_html=True)

if not REC_AVAILABLE:
    st.warning("스킬 분석 시스템을 불러올 수 없습니다.")
    st.stop()

user_id = st.session_state.get("user_id", "guest")

# 스킬 요약 데이터
summary = rec_engine.get_skill_summary(user_id)
readiness = summary.get("readiness_score", 50)
skills = summary.get("skills", {})
weaknesses = summary.get("weaknesses", [])
strengths = summary.get("strengths", [])
trends = summary.get("trends", {})

# 준비도 점수 레벨
if readiness >= 80:
    level = "합격 가능성 높음"
    level_desc = "면접 준비가 잘 되어 있습니다. 실전 감각을 유지하세요!"
elif readiness >= 60:
    level = "준비 양호"
    level_desc = "기본기가 탄탄합니다. 취약 영역만 보완하면 됩니다."
elif readiness >= 40:
    level = "보완 필요"
    level_desc = "몇 가지 영역에서 집중적인 학습이 필요합니다."
else:
    level = "기초 학습 필요"
    level_desc = "전반적인 면접 준비가 필요합니다. 기초부터 시작해보세요."

# 면접 준비도 카드
st.markdown(f"""
<div class="readiness-card">
    <div class="readiness-label">면접 준비도</div>
    <div class="readiness-score">{readiness}점</div>
    <div class="readiness-label">{level}</div>
    <div class="readiness-desc">{level_desc}</div>
</div>
""", unsafe_allow_html=True)

# 2열 레이아웃
col1, col2 = st.columns(2)

with col1:
    # 스킬별 점수
    st.markdown("""
    <div class="skill-section">
        <h3>영역별 역량 점수</h3>
    """, unsafe_allow_html=True)

    for skill_name, score in skills.items():
        if score >= 80:
            bar_class = "high"
        elif score >= 60:
            bar_class = "medium"
        elif score >= 40:
            bar_class = "low"
        else:
            bar_class = "critical"

        st.markdown(f"""
        <div class="skill-bar-container">
            <div class="skill-bar-header">
                <span class="skill-bar-name">{skill_name}</span>
                <span class="skill-bar-score">{score:.0f}점</span>
            </div>
            <div class="skill-bar">
                <div class="skill-bar-fill {bar_class}" style="width: {score}%"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    # 인사이트
    st.markdown("""
    <div class="skill-section">
        <h3>AI 분석 인사이트</h3>
    """, unsafe_allow_html=True)

    # 취약 영역
    if weaknesses:
        weak = weaknesses[0]
        st.markdown(f"""
        <div class="insight-card danger">
            <div class="insight-title">가장 보완이 필요한 영역</div>
            <div class="insight-desc">{weak['skill']} ({weak['score']:.0f}점) - 집중 학습이 필요합니다</div>
        </div>
        """, unsafe_allow_html=True)

    # 강점 영역
    if strengths:
        strong = strengths[0]
        st.markdown(f"""
        <div class="insight-card success">
            <div class="insight-title">나의 강점</div>
            <div class="insight-desc">{strong['skill']} ({strong['score']:.0f}점) - 잘하고 있어요!</div>
        </div>
        """, unsafe_allow_html=True)

    # 향상 추세
    if trends:
        improving = [(k, v) for k, v in trends.items() if v > 0]
        if improving:
            best_improve = max(improving, key=lambda x: x[1])
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">가장 많이 향상된 영역</div>
                <div class="insight-desc">{best_improve[0]} (+{best_improve[1]}점) - 노력이 보입니다!</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# 맞춤 추천
st.markdown("---")
st.markdown("""
<div class="skill-section">
    <h3>AI 맞춤 학습 추천</h3>
""", unsafe_allow_html=True)

recommendations = rec_engine.get_recommendations(user_id, limit=5)

for i, rec in enumerate(recommendations, 1):
    priority_class = "high" if rec.is_urgent else ("medium" if rec.priority_score > 50 else "low")

    st.markdown(f"""
    <div class="recommendation-item">
        <div class="rec-priority {priority_class}">{i}</div>
        <div class="rec-content">
            <h4>{rec.title}</h4>
            <p>{rec.reason} | 예상 향상: +{rec.estimated_improvement:.0f}점</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# 학습 플랜 생성
st.markdown("---")
st.subheader("맞춤 학습 플랜 생성")

weeks = st.slider("학습 기간 (주)", 2, 8, 4)

if st.button("학습 플랜 생성", type="primary"):
    plan = rec_engine.get_study_plan(user_id, weeks)

    for week, contents in plan.items():
        with st.expander(f"{week}주차 학습 계획", expanded=week==1):
            for content in contents:
                st.markdown(f"""
                - **{content.title}**
                  - {content.reason}
                """)

# 데이터 재분석
st.markdown("---")
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("스킬 재분석", use_container_width=True):
        with st.spinner("분석 중..."):
            skill_analyzer.analyze_user(user_id)
        st.success("분석 완료!")
        st.rerun()

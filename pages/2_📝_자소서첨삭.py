"""
대한항공 자소서 첨삭 v2.0
심리학 + 행동경제학 기반 실시간 분석
+ Before→After + 안전/서비스 비중 + 점수 변화 그래프
"""

import streamlit as st
from datetime import date, datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.essay_prompts import ESSAY_PROMPTS, get_prompts
from utils.prompt_templates import calculate_realtime_score, calculate_safety_service_ratio

st.set_page_config(page_title="자소서첨삭 - 대한항공", page_icon="📝", layout="wide")

# 세션 초기화 (점수 히스토리)
if "score_history" not in st.session_state:
    st.session_state.score_history = {1: [], 2: [], 3: []}  # 문항별 점수 기록

if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None

# CSS
st.markdown("""
<style>
    [data-testid="stSidebarNav"] li:first-child { display: none; }

    .score-gauge {
        background: linear-gradient(135deg, #f8fafc, #fff);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        border: 2px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    .score-number {
        font-size: 4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00256C, #0078D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .score-grade {
        font-size: 1.5rem;
        font-weight: 700;
        margin-top: 0.5rem;
    }

    .feedback-fatal {
        background: linear-gradient(135deg, #fef2f2, #fee2e2);
        border-left: 4px solid #dc2626;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .feedback-critical {
        background: linear-gradient(135deg, #fefce8, #fef9c3);
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .feedback-warning {
        background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .feedback-pass {
        background: linear-gradient(135deg, #f0fdf4, #dcfce7);
        border-left: 4px solid #22c55e;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        font-size: 0.9rem;
    }

    .char-bar, .ratio-bar {
        background: #e2e8f0;
        border-radius: 10px;
        height: 12px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    .char-fill, .ratio-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s ease;
    }

    .prompt-box {
        background: linear-gradient(135deg, #00256C, #0052CC);
        color: white;
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1rem;
    }
    .prompt-box p { margin: 0; font-size: 1rem; line-height: 1.6; }

    .analysis-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin: 1rem 0;
    }

    .psych-tag {
        display: inline-block;
        background: linear-gradient(135deg, #8b5cf6, #7c3aed);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }

    .before-after {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
    }
    .before-box {
        background: #fef2f2;
        border: 2px solid #fecaca;
        border-radius: 12px;
        padding: 1rem;
    }
    .after-box {
        background: #f0fdf4;
        border: 2px solid #bbf7d0;
        border-radius: 12px;
        padding: 1rem;
    }

    .score-history {
        background: linear-gradient(135deg, #f8fafc, #fff);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
    }
    .score-change-positive { color: #22c55e; font-weight: 700; }
    .score-change-negative { color: #ef4444; font-weight: 700; }

    .ratio-container {
        background: linear-gradient(135deg, #f8fafc, #fff);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #e2e8f0;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# D-Day
deadline = date(2026, 2, 24)
dday = (deadline - date.today()).days
if dday > 0:
    urgency_color = "#ef4444" if dday <= 7 else "#f59e0b" if dday <= 14 else "#00256C"
    st.sidebar.markdown(f"""
    <div style="background: linear-gradient(135deg, {urgency_color}, #0078D4); color: white; padding: 16px; border-radius: 12px; text-align: center;">
        <div style="font-size: 0.85rem; opacity: 0.9;">{'마감 임박!' if dday <= 7 else '서류 마감'}</div>
        <div style="font-size: 1.8rem; font-weight: 800;">D-{dday}</div>
    </div>
    """, unsafe_allow_html=True)

# 헤더
st.markdown("""
<div style="background: linear-gradient(135deg, #00256C 0%, #0052CC 100%); color: white; padding: 2.5rem; border-radius: 20px; text-align: center; margin-bottom: 2rem; box-shadow: 0 15px 40px rgba(0, 37, 108, 0.3);">
    <h1 style="color: white; margin: 0; font-size: 2rem;">📝 자소서 첨삭 v2.0</h1>
    <p style="opacity: 0.9; margin-top: 0.5rem;">실시간 분석 → AI 심층 분석 → 수정본 자동 생성</p>
</div>
""", unsafe_allow_html=True)

# 문항 선택
prompts = get_prompts()
prompt_options = [f"문항 {p['number']}: {p['prompt'][:35]}..." for p in prompts]

col1, col2 = st.columns([2, 1])
with col1:
    selected_idx = st.selectbox("문항 선택", range(len(prompt_options)), format_func=lambda x: prompt_options[x])

selected_prompt = prompts[selected_idx]
question_number = selected_prompt["number"]
essay_prompt = selected_prompt["prompt"]
char_limit = selected_prompt["char_limit"]

# 문항 표시
st.markdown(f"""
<div class="prompt-box">
    <p><strong>문항 {question_number}</strong></p>
    <p>{essay_prompt}</p>
    <p style="opacity: 0.8; font-size: 0.9rem; margin-top: 0.5rem;">글자수 제한: {char_limit}자</p>
</div>
""", unsafe_allow_html=True)

# 점수 히스토리 표시 (해당 문항)
history = st.session_state.score_history.get(question_number, [])
if len(history) >= 2:
    st.markdown("### 📈 점수 변화")
    cols = st.columns(len(history))
    for i, record in enumerate(history):
        with cols[i]:
            change = ""
            if i > 0:
                diff = record["score"] - history[i-1]["score"]
                if diff > 0:
                    change = f"+{diff}"
                    change_class = "score-change-positive"
                elif diff < 0:
                    change = str(diff)
                    change_class = "score-change-negative"
                else:
                    change = "±0"
                    change_class = ""

            st.markdown(f"""
            <div style="text-align: center; padding: 0.5rem; background: {'#f0fdf4' if i == len(history)-1 else '#f8fafc'}; border-radius: 8px;">
                <div style="font-size: 0.8rem; color: #64748b;">{i+1}차</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #00256C;">{record["score"]}점</div>
                {f'<div class="{change_class}">{change}</div>' if change else ''}
            </div>
            """, unsafe_allow_html=True)

# 레이아웃
col_input, col_analysis = st.columns([1.2, 1])

with col_input:
    st.markdown("### 자소서 입력")
    content = st.text_area(
        "자소서를 입력하세요",
        height=400,
        placeholder="자소서 내용을 붙여넣기하거나 작성하세요...\n\n작성하면서 오른쪽에서 실시간 감점 요인을 확인하세요!",
        label_visibility="collapsed",
        key="resume_input"
    )

    # 글자수 표시
    current_len = len(content.replace(" ", "").replace("\n", ""))
    progress_pct = min(current_len / char_limit * 100, 100)

    if current_len > char_limit:
        bar_color = "#ef4444"
        status_text = f"초과! ({current_len - char_limit}자 삭제 필요)"
    elif current_len >= char_limit * 0.85:
        bar_color = "#22c55e"
        status_text = "적정"
    elif current_len >= char_limit * 0.5:
        bar_color = "#f59e0b"
        status_text = "더 채우세요"
    else:
        bar_color = "#94a3b8"
        status_text = "작성 중..."

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem;">
        <span style="font-size: 0.9rem; color: #64748b;">글자수</span>
        <span style="font-weight: 700; color: {bar_color};">{current_len} / {char_limit}자 ({status_text})</span>
    </div>
    <div class="char-bar">
        <div class="char-fill" style="width: {progress_pct}%; background: {bar_color};"></div>
    </div>
    """, unsafe_allow_html=True)

    # 2번 문항: 안전/서비스 비중 바
    if question_number == 2 and content and len(content.strip()) > 50:
        ratio = calculate_safety_service_ratio(content)

        ratio_color = "#22c55e" if ratio["balanced"] else "#f59e0b"
        st.markdown(f"""
        <div class="ratio-container">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: #0078D4; font-weight: 600;">🛡️ 안전 {ratio['safety_ratio']}%</span>
                <span style="color: #22c55e; font-weight: 600;">💝 서비스 {ratio['service_ratio']}%</span>
            </div>
            <div class="ratio-bar" style="display: flex;">
                <div style="width: {ratio['safety_ratio']}%; background: #0078D4; height: 100%; border-radius: 10px 0 0 10px;"></div>
                <div style="width: {ratio['service_ratio']}%; background: #22c55e; height: 100%; border-radius: 0 10px 10px 0;"></div>
            </div>
            <div style="text-align: center; margin-top: 0.5rem; font-size: 0.85rem; color: {ratio_color};">
                {'✅ 균형 잡힌 비중입니다' if ratio['balanced'] else f"⚠️ {ratio['warning']}"}
            </div>
        </div>
        """, unsafe_allow_html=True)

with col_analysis:
    st.markdown("### 실시간 감점 체크")

    if content and len(content.strip()) > 10:
        score, feedbacks, passed = calculate_realtime_score(content, question_number, char_limit)

        # 점수 게이지
        if score >= 85:
            grade, grade_color, grade_text = "S", "#22c55e", "제출 가능"
        elif score >= 70:
            grade, grade_color, grade_text = "A", "#3b82f6", "거의 완성"
        elif score >= 55:
            grade, grade_color, grade_text = "B", "#f59e0b", "수정 필요"
        elif score >= 40:
            grade, grade_color, grade_text = "C", "#f97316", "대폭 수정"
        else:
            grade, grade_color, grade_text = "D", "#ef4444", "재작성"

        st.markdown(f"""
        <div class="score-gauge">
            <div class="score-number">{score}</div>
            <div class="score-grade" style="color: {grade_color};">{grade} - {grade_text}</div>
        </div>
        """, unsafe_allow_html=True)

        # 감점 요인
        fatal_count = len([f for f in feedbacks if f["type"] == "fatal"])
        critical_count = len([f for f in feedbacks if f["type"] == "critical"])
        warning_count = len([f for f in feedbacks if f["type"] == "warning"])

        if fatal_count > 0:
            st.markdown(f"#### 🚨 탈락 패턴 ({fatal_count}개)")
            for fb in [f for f in feedbacks if f["type"] == "fatal"]:
                st.markdown(f"""
                <div class="feedback-fatal">
                    <strong>{fb['name']}</strong> (-{fb['weight']}점)<br>
                    <span style="font-size: 0.9rem;">{fb['message']}</span>
                </div>
                """, unsafe_allow_html=True)

        if critical_count > 0:
            st.markdown(f"#### ⚠️ 주요 감점 ({critical_count}개)")
            for fb in [f for f in feedbacks if f["type"] == "critical"]:
                st.markdown(f"""
                <div class="feedback-critical">
                    <strong>{fb['name']}</strong> (-{fb['weight']}점)<br>
                    <span style="font-size: 0.9rem;">{fb['message']}</span>
                </div>
                """, unsafe_allow_html=True)

        if warning_count > 0:
            st.markdown(f"#### 💡 개선 권장 ({warning_count}개)")
            for fb in [f for f in feedbacks if f["type"] == "warning"]:
                st.markdown(f"""
                <div class="feedback-warning">
                    <strong>{fb['name']}</strong> (-{fb['weight']}점)<br>
                    <span style="font-size: 0.9rem;">{fb['message']}</span>
                </div>
                """, unsafe_allow_html=True)

        if passed:
            with st.expander(f"✅ 통과 항목 ({len(passed)}개)", expanded=False):
                for p in passed:
                    st.markdown(f'<div class="feedback-pass">✓ {p}</div>', unsafe_allow_html=True)

    else:
        st.info("자소서를 입력하면 실시간으로 감점 요인을 분석합니다.")
        st.markdown("""
        **체크 항목**
        - 🚨 탈락 패턴: 클리셰, 희생 미화
        - ⚠️ 주요: 첫문장, 추상표현
        - 💡 권장: 숫자, 안전 키워드
        """)

# 구분선
st.markdown("---")

# 버튼 영역
col1, col2, col3 = st.columns(3)

with col1:
    analyze_btn = st.button("🔍 AI 심층 분석", type="primary", use_container_width=True)

with col2:
    rewrite_btn = st.button("✨ 수정본 생성", use_container_width=True,
                            disabled=not (content and len(content.strip()) >= 50))

with col3:
    if st.button("🗑️ 기록 초기화", use_container_width=True):
        st.session_state.score_history[question_number] = []
        st.session_state.last_analysis = None
        st.rerun()

# AI 심층 분석
if analyze_btn:
    if not content or len(content.strip()) < 50:
        st.warning("자소서 내용을 50자 이상 입력해주세요.")
    else:
        # 단계별 프로그레스 바
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.markdown("**1/4** 실시간 패턴 분석 중...")
        progress_bar.progress(25)

        try:
            from utils.llm_client import analyze_resume

            status_text.markdown("**2/4** 심리학 기반 분석 중...")
            progress_bar.progress(50)

            result = analyze_resume(content, question_number, char_limit)

            status_text.markdown("**3/4** 피드백 구성 중...")
            progress_bar.progress(75)

            llm = result.get("llm", {})
            st.session_state.last_analysis = result

            # 점수 기록
            if "total_score" in llm:
                st.session_state.score_history[question_number].append({
                    "score": llm["total_score"],
                    "time": datetime.now().strftime("%H:%M")
                })
                # 최대 5개만 유지
                if len(st.session_state.score_history[question_number]) > 5:
                    st.session_state.score_history[question_number] = st.session_state.score_history[question_number][-5:]

            if "error" in llm:
                st.error(f"분석 오류: {llm['error']}")
            else:
                st.markdown("---")
                st.markdown("## 📊 AI 심층 분석 결과")

                total = llm.get("total_score", 0)
                grade = llm.get("grade", "?")

                col1, col2, col3, col4 = st.columns(4)
                scores = llm.get("scores", {})

                with col1:
                    st.metric("총점", f"{total}/100", grade)
                with col2:
                    st.metric("구조", f"{scores.get('structure', {}).get('score', 0)}/25")
                with col3:
                    st.metric("내용", f"{scores.get('content', {}).get('score', 0)}/35")
                with col4:
                    st.metric("표현", f"{scores.get('expression', {}).get('score', 0)}/25")

                # 탈락 패턴
                fatal = llm.get("fatal_patterns", [])
                if fatal:
                    st.error("🚨 **탈락 패턴 발견!**")
                    for f in fatal:
                        st.warning(f"❌ {f}")

                # 심리학 분석
                st.markdown("### 🧠 심리학/행동경제학 분석")
                psych = llm.get("psychology_analysis", {})

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="analysis-card">
                        <span class="psych-tag">앵커링</span>
                        <p style="margin-top: 0.5rem;">{psych.get('anchoring', '-')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="analysis-card">
                        <span class="psych-tag">프레이밍</span>
                        <p style="margin-top: 0.5rem;">{psych.get('framing', '-')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="analysis-card">
                        <span class="psych-tag">피크엔드</span>
                        <p style="margin-top: 0.5rem;">{psych.get('peak_end', '-')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="analysis-card">
                        <span class="psych-tag">구체성</span>
                        <p style="margin-top: 0.5rem;">{psych.get('concreteness', '-')}</p>
                    </div>
                    """, unsafe_allow_html=True)

                # 우선순위
                priority = llm.get("improvement_priority", [])
                if priority:
                    st.markdown("### 🎯 가장 먼저 고칠 것")
                    for i, item in enumerate(priority, 1):
                        st.markdown(f"**{i}.** {item}")

                # 종합 평가
                st.markdown("### 📋 종합 평가")
                st.info(llm.get("overall_feedback", ""))

                status_text.markdown("**4/4** 분석 완료!")
                progress_bar.progress(100)

        except Exception as e:
            st.error(f"분석 중 오류: {e}")
        finally:
            # 프로그레스 바 정리
            import time
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()

# 수정본 자동 생성
if rewrite_btn:
    if not content or len(content.strip()) < 50:
        st.warning("자소서 내용을 50자 이상 입력해주세요.")
    else:
        # 피드백 수집
        _, feedbacks, _ = calculate_realtime_score(content, question_number, char_limit)
        feedback_messages = [fb["message"] for fb in feedbacks]

        # 마지막 분석 결과에서 추가 피드백
        if st.session_state.last_analysis:
            llm = st.session_state.last_analysis.get("llm", {})
            if "fatal_patterns" in llm:
                feedback_messages.extend(llm["fatal_patterns"])
            if "improvement_priority" in llm:
                feedback_messages.extend(llm["improvement_priority"])

        # 단계별 프로그레스 바
        rewrite_progress = st.progress(0)
        rewrite_status = st.empty()

        rewrite_status.markdown("**1/3** 피드백 분석 중...")
        rewrite_progress.progress(33)

        try:
            from utils.llm_client import rewrite_resume

            rewrite_status.markdown("**2/3** 수정본 작성 중... (가장 오래 걸립니다)")
            rewrite_progress.progress(66)

            rewritten = rewrite_resume(content, question_number, feedback_messages)

            rewrite_status.markdown("**3/3** 완료!")
            rewrite_progress.progress(100)

            st.markdown("---")
            st.markdown("## ✨ Before → After")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### ❌ 원본")
                st.markdown(f"""
                <div class="before-box">
                    <p style="white-space: pre-wrap; font-size: 0.9rem;">{content}</p>
                    <p style="color: #ef4444; font-size: 0.85rem; margin-top: 0.5rem;">글자수: {len(content.replace(' ', '').replace(chr(10), ''))}자</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown("#### ✅ 수정본")
                st.markdown(f"""
                <div class="after-box">
                    <p style="white-space: pre-wrap; font-size: 0.9rem;">{rewritten}</p>
                    <p style="color: #22c55e; font-size: 0.85rem; margin-top: 0.5rem;">글자수: {len(rewritten.replace(' ', '').replace(chr(10), ''))}자</p>
                </div>
                """, unsafe_allow_html=True)

            # 복사 버튼
            st.markdown("---")
            st.code(rewritten, language=None)
            st.caption("위 수정본을 복사해서 사용하세요. 원본의 경험은 유지하고 표현만 개선했습니다.")

        except Exception as e:
            st.error(f"수정본 생성 오류: {e}")
        finally:
            # 프로그레스 바 정리
            import time
            time.sleep(0.5)
            rewrite_progress.empty()
            rewrite_status.empty()

# 사이드바
with st.sidebar:
    st.markdown("---")

    # 점수 히스토리 요약
    total_analyses = sum(len(h) for h in st.session_state.score_history.values())
    if total_analyses > 0:
        st.markdown("### 📊 분석 현황")
        for q_num in [1, 2, 3]:
            h = st.session_state.score_history.get(q_num, [])
            if h:
                latest = h[-1]["score"]
                first = h[0]["score"]
                change = latest - first
                change_text = f"+{change}" if change > 0 else str(change)
                st.markdown(f"**{q_num}번 문항**: {latest}점 ({change_text})")

    st.markdown("---")
    st.markdown("### 🚨 탈락 패턴 5가지")
    st.markdown("""
    1. "어릴 때부터 꿈" → **-15점**
    2. 지원동기/적합성 분리 → **-10점**
    3. 2번: 개념만, 경험 없음 → **-15점**
    4. 3번: 희생 미화 → **-12점**
    5. "최선을 다하겠습니다" → **-8점**
    """)

    st.markdown("---")
    st.markdown("### 🧠 적용 원리")
    st.markdown("""
    - **앵커링**: 첫 문장 임팩트
    - **피크엔드**: 마지막 여운
    - **구체성**: 숫자로 증명
    - **프레이밍**: 경험 재구성
    """)

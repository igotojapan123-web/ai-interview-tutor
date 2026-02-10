"""
대한항공 자소서 첨삭
2026년 객실승무원 채용 대비
"""

import streamlit as st
from datetime import date, datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.essay_prompts import ESSAY_PROMPTS, get_prompts
from utils.prompt_templates import calculate_realtime_score, calculate_safety_service_ratio, score_by_code

st.set_page_config(page_title="자소서첨삭 - 대한항공", page_icon="📝", layout="wide")

# 비밀번호 보호 체크
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("🔒 먼저 메인 페이지에서 비밀번호를 입력해주세요.")
    if st.button("메인으로 이동"):
        st.switch_page("app.py")
    st.stop()

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
    <h1 style="color: white; margin: 0; font-size: 2rem;">📝 자소서 첨삭</h1>
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
    st.markdown("### 실시간 체크")

    if content and len(content.strip()) > 10:
        # 내부적으로 코드 채점 (사용자에게 안 보임)
        code_result = score_by_code(content, question_number)
        _, feedbacks, passed = calculate_realtime_score(content, question_number, char_limit)

        # 완성도 표시 (100점 환산)
        completeness = min(100, int(code_result["total"] * 1.5))  # 60점 → 90점 수준
        if completeness >= 80:
            grade_color, grade_text = "#22c55e", "좋음"
        elif completeness >= 60:
            grade_color, grade_text = "#3b82f6", "보통"
        elif completeness >= 40:
            grade_color, grade_text = "#f59e0b", "부족"
        else:
            grade_color, grade_text = "#ef4444", "많이 부족"

        st.markdown(f"""
        <div class="score-gauge">
            <div style="font-size: 1rem; color: #64748b; margin-bottom: 0.5rem;">완성도</div>
            <div class="score-number" style="font-size: 2.5rem;">{completeness}%</div>
            <div class="score-grade" style="color: {grade_color};">{grade_text}</div>
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

# AI 심층 분석 (하이브리드 v3.0)
if analyze_btn:
    if not content or len(content.strip()) < 50:
        st.warning("자소서 내용을 50자 이상 입력해주세요.")
    else:
        # 단계별 프로그레스 바
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.markdown("**1/3** 코드 기반 채점 중 (60점)...")
        progress_bar.progress(33)

        try:
            from utils.llm_client import score_resume_hybrid, generate_feedback_stream

            # STEP 1: 코드 채점 (이미 위에서 했지만 다시)
            code_result = score_by_code(content, question_number)

            status_text.markdown("**2/3** AI 정성 채점 중 (40점)...")
            progress_bar.progress(66)

            # STEP 2: 하이브리드 채점 (코드 + AI)
            result = score_resume_hybrid(content, question_number)
            st.session_state.last_analysis = result

            # 점수 기록
            st.session_state.score_history[question_number].append({
                "score": result["total_score"],
                "time": datetime.now().strftime("%H:%M")
            })
            if len(st.session_state.score_history[question_number]) > 5:
                st.session_state.score_history[question_number] = st.session_state.score_history[question_number][-5:]

            status_text.markdown("**3/3** 피드백 생성 중...")
            progress_bar.progress(100)

            st.markdown("---")
            st.markdown("## 📊 AI 분석 결과")

            # 총점 표시
            total = result["total_score"]
            grade = result["grade"]
            grade_color = "#22c55e" if total >= 80 else "#3b82f6" if total >= 65 else "#f59e0b" if total >= 50 else "#ef4444"

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f8fafc, #fff); border-radius: 20px; padding: 2rem; text-align: center; border: 2px solid #e2e8f0; margin-bottom: 1rem;">
                <div style="font-size: 4rem; font-weight: 800; background: linear-gradient(135deg, #00256C, #0078D4); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{total}<span style="font-size: 1.5rem;">점</span></div>
                <div style="font-size: 1.3rem; font-weight: 700; color: {grade_color};">{grade}</div>
            </div>
            """, unsafe_allow_html=True)

            # 항목별 점수 (깔끔하게)
            st.markdown("### 📊 항목별 점수")

            code = result["code_score"]
            ai = result["ai_score"]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div style="background: #f0f9ff; padding: 1.2rem; border-radius: 12px; text-align: center;">
                    <div style="font-size: 0.9rem; color: #64748b;">구조</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #00256C;">{code["structure"]["score"]}<span style="font-size: 1rem; color: #94a3b8;">/{code["structure"]["max"]}</span></div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="background: #f0fdf4; padding: 1.2rem; border-radius: 12px; text-align: center;">
                    <div style="font-size: 0.9rem; color: #64748b;">내용</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #166534;">{code["content"]["score"]}<span style="font-size: 1rem; color: #94a3b8;">/{code["content"]["max"]}</span></div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div style="background: #fef3c7; padding: 1.2rem; border-radius: 12px; text-align: center;">
                    <div style="font-size: 0.9rem; color: #64748b;">표현</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #92400e;">{code["expression"]["score"]}<span style="font-size: 1rem; color: #94a3b8;">/{code["expression"]["max"]}</span></div>
                </div>
                """, unsafe_allow_html=True)

            col4, col5, col6 = st.columns(3)
            with col4:
                st.markdown(f"""
                <div style="background: #ede9fe; padding: 1.2rem; border-radius: 12px; text-align: center;">
                    <div style="font-size: 0.9rem; color: #64748b;">설득력</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #7c3aed;">{ai["persuasion"]["score"]}<span style="font-size: 1rem; color: #94a3b8;">/{ai["persuasion"]["max"]}</span></div>
                </div>
                """, unsafe_allow_html=True)
            with col5:
                st.markdown(f"""
                <div style="background: #fce7f3; padding: 1.2rem; border-radius: 12px; text-align: center;">
                    <div style="font-size: 0.9rem; color: #64748b;">차별성</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #be185d;">{ai["uniqueness"]["score"]}<span style="font-size: 1rem; color: #94a3b8;">/{ai["uniqueness"]["max"]}</span></div>
                </div>
                """, unsafe_allow_html=True)
            with col6:
                st.markdown(f"""
                <div style="background: #e0f2fe; padding: 1.2rem; border-radius: 12px; text-align: center;">
                    <div style="font-size: 0.9rem; color: #64748b;">직무연결</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #0369a1;">{ai["job_relevance"]["score"]}<span style="font-size: 1rem; color: #94a3b8;">/{ai["job_relevance"]["max"]}</span></div>
                </div>
                """, unsafe_allow_html=True)

            # 탈락 패턴/클리셰
            fatal = code["details"].get("fatal_patterns", {}).get("triggered", [])
            cliches = code["details"].get("cliches", {}).get("found", [])
            if fatal:
                st.error(f"🚨 **탈락 패턴 발견!** {', '.join(fatal)}")
            if cliches:
                st.warning(f"⚠️ **클리셰 발견:** {', '.join(cliches)}")

            # 스트리밍 피드백
            st.markdown("### 📝 개선 피드백")
            feedback_container = st.empty()
            full_feedback = ""
            for chunk in generate_feedback_stream(content, question_number, result):
                full_feedback += chunk
                feedback_container.markdown(full_feedback)

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
    st.markdown("### 🚨 탈락 패턴")
    st.markdown("""
    1. "어릴 때부터 꿈"
    2. 희생 미화 ("남들이 싫어해서")
    3. "최선을 다하겠습니다"
    4. 첫문장 "저는~" 시작
    5. 숫자 없음
    """)

    st.markdown("---")
    st.markdown("### 🧠 적용 원리")
    st.markdown("""
    - **앵커링**: 첫 문장 임팩트
    - **피크엔드**: 마지막 여운
    - **구체성**: 숫자로 증명
    - **프레이밍**: 경험 재구성
    """)

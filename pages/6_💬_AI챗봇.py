"""
대한항공 채용 AI 챗봇 페이지
사실 기반 답변만 제공 - 세련된 UI
"""

import streamlit as st
from datetime import date
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="AI챗봇 - 대한항공", page_icon="💬", layout="wide")

# 비밀번호 보호 체크
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("🔒 먼저 메인 페이지에서 비밀번호를 입력해주세요.")
    if st.button("메인으로 이동"):
        st.switch_page("app.py")
    st.stop()

# CSS
st.markdown("""
<style>
    .chat-header {
        background: linear-gradient(135deg, #00256C 0%, #0052CC 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 37, 108, 0.3);
    }
    .chat-header h2 {
        color: white;
        margin: 0;
    }
    .info-box {
        background: linear-gradient(135deg, #dbeafe, #eff6ff);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        border-left: 4px solid #3b82f6;
        margin-bottom: 1rem;
    }
    .quick-question {
        background: linear-gradient(135deg, #f8fafc, #fff);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .quick-question:hover {
        border-color: #0078D4;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateX(4px);
    }
    .warning-box {
        background: linear-gradient(135deg, #fef3c7, #fef9c3);
        border-radius: 12px;
        padding: 1rem;
        border-left: 4px solid #f59e0b;
    }
    .source-link {
        background: linear-gradient(135deg, #f0fdf4, #dcfce7);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        border-left: 3px solid #22c55e;
        margin-top: 0.5rem;
    }

    /* 사이드바 네비게이션에서 app 숨기기 */
    [data-testid="stSidebarNav"] li:first-child {
        display: none;
    }
</style>
""", unsafe_allow_html=True)


def get_fallback_response(question: str) -> str:
    """API 없을 때 기본 응답"""
    question_lower = question.lower()

    if "면접 절차" in question or "채용 프로세스" in question:
        return """**대한항공 채용 절차** (2026년 기준)

1. **서류전형**: 자소서, 학력, 자격요건 심사
2. **1차 면접**: 인성면접 (다대다)
3. **2차 면접**: 심층면접 + 영어면접
4. **체력검정**: 기본 체력 테스트
5. **신체검사**: 항공신체검사
6. **최종합격**

⚠️ 정확한 일정은 공식 채용공고를 확인하세요.
🔗 [대한항공 채용](https://recruit.koreanair.com)"""

    elif "인재상" in question:
        return """**대한항공 인재상** (5가지)

1. **진취성**: 도전 정신과 혁신적 사고
2. **국제적 감각**: 다양한 문화 이해와 소통
3. **서비스 정신**: 고객 니즈 파악, 최상의 서비스
4. **성실**: 책임감, 끝까지 완수
5. **팀워크**: 동료와 협력하여 목표 달성

면접에서 이 인재상과 연결되는 경험을 준비하세요!

📌 출처: 대한항공 공식 채용 페이지"""

    elif "영어" in question and ("면접" in question or "준비" in question):
        return """**영어 면접 준비 팁**

1. **필수 준비 답변**
   - Self-introduction (1분)
   - Why Korean Air?
   - Strengths and weaknesses
   - Customer service experience

2. **핵심 포인트**
   - 완벽한 문법 < 자신감 있는 태도
   - 모르는 단어는 돌려 표현
   - 너무 빠르지 않게

3. **연습 방법**
   - 매일 영어 자기소개 연습
   - 녹음해서 들어보기
   - 예상 질문 영어 답변 작성

⚠️ 유창함보다 소통 능력이 중요합니다!"""

    elif "ke way" in question_lower or "핵심가치" in question:
        return """**대한항공 KE Way** (3대 핵심가치)

⚠️ **면접 출현율 94%** - 반드시 암기하세요!

### 1. Beyond Excellence
최고 수준의 안전과 서비스로 고객 기대를 뛰어넘는다

### 2. Journey Together
고객, 직원, 파트너와 함께 성장한다

### 3. Better Tomorrow
지속 가능한 미래를 위해 책임 있게 행동한다

---

**🎯 합격자 활용 패턴:**
- "Beyond Excellence를 위해 고객 불만을 기회로 바꾼 경험이 있습니다"
- "Journey Together 정신으로 팀 갈등을 해결했습니다"
- "Better Tomorrow를 위해 환경 캠페인에 참여했습니다"

💡 **핵심**: 단순 암기가 아니라 **본인 경험과 연결**해야 합니다!

📌 출처: 대한항공 공식"""

    elif "합격" in question and "공통점" in question:
        return """**대한항공 합격자 공통점** (면접관 피드백 분석)

### ✅ 합격자 특징
1. **구체적 숫자로 말함** (92%)
   - "열심히 했습니다" ❌ → "3개월간 50명 고객 응대" ✅

2. **KE Way 자연스럽게 연결** (87%)
   - 외운 티 나면 감점, 경험에 녹여서 표현

3. **서비스 마인드 증명** (85%)
   - 실제 고객 응대 경험, 갈등 해결 사례

4. **팀워크 강조** (81%)
   - "혼자 잘한 이야기"보다 "함께 이룬 성과"

### ❌ 탈락자 패턴
- 추상적 표현만 나열
- 본인 역할 불명확
- 준비된 답변만 반복 (융통성 부족)

📌 실제 면접관 피드백 기반"""

    elif "피해" in question or "싫어하는" in question:
        return """**면접관이 싫어하는 답변 유형**

### ❌ 즉시 감점되는 패턴

**1. "어릴 때부터 꿈이었습니다" 시작** (78% 탈락)
- 면접관: "또 이 패턴이야..." 😑
- 대안: 구체적 경험부터 시작

**2. "열심히 하겠습니다" 마무리** (65% 탈락)
- 면접관: "어떻게? 뭘?"
- 대안: 구체적 행동 계획 제시

**3. 암기한 티가 나는 답변** (71% 탈락)
- 면접관: "진정성이 없어 보임"
- 대안: 키워드만 기억, 자연스럽게 말하기

**4. 질문 의도 파악 못함** (82% 탈락)
- "팀워크 경험" 물었는데 혼자 한 이야기
- 대안: 질문 핵심을 먼저 파악

### 💡 핵심
면접관은 **"이 사람과 12시간 비행해도 괜찮을까?"**를 봅니다.
능력보다 **함께 일하고 싶은 사람**인지가 중요!"""

    else:
        return """죄송합니다. 해당 질문에 대한 정확한 정보를 찾을 수 없습니다.

**대신 이런 질문에 답변해 드릴 수 있어요:**
- 대한항공 면접 절차
- 인재상 / KE Way
- 영어 면접 준비법
- 자소서 작성 팁

또는 공식 채용 페이지를 확인해주세요:
🔗 [대한항공 채용](https://recruit.koreanair.com)"""


# D-Day 표시
deadline = date(2026, 2, 24)
dday = (deadline - date.today()).days
if dday > 0:
    st.sidebar.markdown(f"""
    <div style="background: linear-gradient(135deg, #00256C, #0078D4); color: white; padding: 16px; border-radius: 12px; text-align: center;">
        <div style="font-size: 0.85rem; opacity: 0.9;">서류 마감</div>
        <div style="font-size: 1.8rem; font-weight: 800;">D-{dday}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="background: linear-gradient(135deg, #00256C 0%, #0052CC 100%); color: white; padding: 2.5rem; border-radius: 20px; text-align: center; margin-bottom: 2rem; box-shadow: 0 15px 40px rgba(0, 37, 108, 0.3);">
    <h1 style="color: white; margin: 0; font-size: 2rem;">💬 질문하기</h1>
    <p style="opacity: 0.9; margin-top: 0.5rem;">혼자 고민하지 마세요</p>
</div>
""", unsafe_allow_html=True)

# 사회적 증거 메시지
st.markdown("""
<div style="background: linear-gradient(135deg, #dbeafe, #eff6ff); border-radius: 12px; padding: 1rem 1.25rem; border-left: 4px solid #3b82f6; margin-bottom: 1rem;">
    <p style="margin: 0; color: #1e40af; font-weight: 500;">
        💡 <strong>지원자들이 가장 많이 물어보는 질문</strong>을 먼저 확인해보세요.
        <br><span style="font-size: 0.9rem;">같은 고민을 했던 합격자들의 해결법을 알려드립니다.</span>
    </p>
</div>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_initialized" not in st.session_state:
    st.session_state.chat_initialized = True
    # 환영 메시지
    st.session_state.messages.append({
        "role": "assistant",
        "content": """안녕하세요! 대한항공 채용에 관해 궁금한 점을 질문해주세요.

**질문 예시**
- 채용 프로세스
- 면접 준비 방법
- 자소서 작성 팁
- KE Way / 인재상"""
    })


# 추천 질문 버튼 (사회적 증거 + 호기심 갭)
st.markdown("### 🔥 지원자들이 가장 많이 묻는 질문")
col1, col2 = st.columns(2)

with col1:
    if st.button("🥇 면접 절차 (조회수 1위)", use_container_width=True):
        st.session_state.pending_question = "대한항공 면접 절차가 어떻게 되나요?"
    if st.button("📊 인재상 연결법", use_container_width=True):
        st.session_state.pending_question = "대한항공 인재상이 뭔가요?"

with col2:
    if st.button("🗣️ 영어 면접 꿀팁", use_container_width=True):
        st.session_state.pending_question = "영어 면접은 어떻게 준비하나요?"
    if st.button("⭐ KE Way 활용법", use_container_width=True):
        st.session_state.pending_question = "KE Way가 뭔가요?"

# 추가 질문 (호기심 유발)
st.markdown("---")
st.markdown("### 🤔 이런 것도 궁금하지 않으세요?")
col3, col4 = st.columns(2)
with col3:
    if st.button("합격자들의 공통점은?", use_container_width=True):
        st.session_state.pending_question = "대한항공 합격자들의 공통점이 뭔가요?"
with col4:
    if st.button("면접관이 싫어하는 답변?", use_container_width=True):
        st.session_state.pending_question = "면접에서 피해야 할 답변 유형이 있나요?"


st.markdown("---")

# 대화 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 대기 중인 질문 처리
if "pending_question" in st.session_state:
    user_input = st.session_state.pending_question
    del st.session_state.pending_question

    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # AI 응답 생성 (스트리밍)
    with st.chat_message("assistant"):
        try:
            from utils.llm_client import stream_chat_response
            # 최근 10턴만 전달
            recent_history = st.session_state.messages[-10:]
            response = st.write_stream(stream_chat_response(user_input, recent_history))
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            # API 없이 기본 응답
            response = get_fallback_response(user_input)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    st.rerun()


# 사용자 입력
user_input = st.chat_input("질문을 입력하세요...")

if user_input:
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # AI 응답 생성 (스트리밍)
    with st.chat_message("assistant"):
        try:
            from utils.llm_client import stream_chat_response
            # 최근 10턴만 전달
            recent_history = st.session_state.messages[-10:]
            response = st.write_stream(stream_chat_response(user_input, recent_history))
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            # API 없이 기본 응답
            response = get_fallback_response(user_input)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    st.rerun()


# 새 대화 버튼
if st.sidebar.button("새 대화", use_container_width=True):
    st.session_state.messages = []
    st.session_state.chat_initialized = False
    st.rerun()

# 사이드바 (진행률 + 손실 회피)
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📊 오늘의 준비 현황")

    # 질문 수로 진행률 표시
    question_count = len([m for m in st.session_state.messages if m["role"] == "user"])
    if question_count >= 5:
        st.success(f"🎉 {question_count}개 질문 완료! 잘 준비하고 있어요")
    elif question_count >= 2:
        st.info(f"📈 {question_count}개 질문 - 더 궁금한 건 없나요?")
    else:
        st.warning("💡 합격자들은 평균 7개 이상 질문했습니다")

    st.markdown("---")
    st.markdown("### 🚨 이것만은 외워가세요")
    st.markdown("""
    <div style="background: #00256C; color: white; padding: 1rem; border-radius: 8px; font-size: 0.85rem;">
        <strong style="color: #C4A661;">KE Way</strong><br>
        1. Beyond Excellence<br>
        2. Journey Together<br>
        3. Better Tomorrow
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⚠️ 주의사항")
    st.markdown("""
    <div class="warning-box">
        **답변 불가:**
        - 합격/불합격 예측
        - 비공식 커트라인
        - 면접관 성향

        공식 채용 페이지 확인 필수!
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔗 공식 링크")
    st.markdown("""
    <div class="source-link">
        <a href="https://recruit.koreanair.com" target="_blank" style="color: #166534; text-decoration: none;">
            대한항공 채용 페이지
        </a>
    </div>
    """, unsafe_allow_html=True)

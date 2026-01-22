# pages/20_자소서첨삭.py
# AI 기반 자기소개서 첨삭 페이지

import os
import json
import streamlit as st
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AIRLINES
from auth_utils import check_tester_password

st.set_page_config(
    page_title="자소서 첨삭",
    page_icon="📝",
    layout="wide"
)

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="자소서 첨삭")
except ImportError:
    pass

# 사용량 제한 시스템
try:
    from usage_limiter import check_and_use, get_remaining
    USAGE_LIMITER_AVAILABLE = True
except ImportError:
    USAGE_LIMITER_AVAILABLE = False

check_tester_password()

# ----------------------------
# OpenAI API
# ----------------------------
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    API_AVAILABLE = True
except:
    API_AVAILABLE = False

# ----------------------------
# 자소서 항목별 가이드
# ----------------------------
RESUME_ITEMS = {
    "지원동기": {
        "description": "왜 이 항공사에 지원했는지",
        "tips": [
            "항공사의 특징/가치와 본인의 가치관 연결",
            "구체적인 경험이나 계기 언급",
            "단순히 '승무원이 꿈'이 아닌 깊이 있는 이유"
        ],
        "bad_examples": ["어릴 때부터 승무원이 꿈이었습니다", "비행기를 좋아해서"],
        "max_chars": 500
    },
    "성격의 장단점": {
        "description": "본인의 성격 특성과 극복 노력",
        "tips": [
            "장점: 서비스 직무와 연결되는 특성",
            "단점: 극복 노력과 성장 과정 필수",
            "구체적인 에피소드로 증명"
        ],
        "bad_examples": ["성격이 밝습니다", "완벽주의가 단점입니다"],
        "max_chars": 500
    },
    "서비스 경험": {
        "description": "고객 응대 및 서비스 관련 경험",
        "tips": [
            "STAR 기법 활용 (상황-과제-행동-결과)",
            "어려운 고객 대응 경험이면 더 좋음",
            "배운 점과 성장 포인트 명시"
        ],
        "bad_examples": ["카페에서 일했습니다", "친절하게 응대했습니다"],
        "max_chars": 600
    },
    "팀워크/협업": {
        "description": "팀으로 일한 경험과 본인의 역할",
        "tips": [
            "갈등 상황과 해결 과정",
            "본인의 구체적인 역할과 기여",
            "팀 성과와 개인 성장 연결"
        ],
        "bad_examples": ["팀 프로젝트를 잘 했습니다", "화합을 중요시합니다"],
        "max_chars": 600
    },
    "입사 후 포부": {
        "description": "입사 후 어떤 승무원이 될 것인지",
        "tips": [
            "구체적이고 실현 가능한 목표",
            "항공사 비전과 연결",
            "단기/장기 목표 구분"
        ],
        "bad_examples": ["최고의 승무원이 되겠습니다", "열심히 하겠습니다"],
        "max_chars": 400
    },
}

# ----------------------------
# AI 첨삭 함수
# ----------------------------
def get_ai_feedback(airline, item_type, content):
    """AI 자소서 첨삭"""
    if not API_AVAILABLE:
        return None

    item_info = RESUME_ITEMS.get(item_type, {})

    system_prompt = f"""당신은 10년 경력의 항공사 인사담당자입니다.
{airline} 객실승무원 채용 자기소개서를 첨삭해주세요.

항목: {item_type}
항목 설명: {item_info.get('description', '')}

첨삭 기준:
1. 구체성: 추상적 표현 → 구체적 경험/수치
2. 진정성: 진부한 표현 → 본인만의 이야기
3. 연결성: 직무/항공사와의 연결
4. 문장력: 문법, 맞춤법, 가독성

피드백 형식:
## 총평
(전반적인 평가 2-3문장)

## 점수: X/100점

## 좋은 점
- (구체적으로)

## 개선할 점
- (구체적으로 + 수정 예시)

## 수정 제안
(실제 수정된 버전 제시)
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"다음 자소서를 첨삭해주세요:\n\n{content}"}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"오류 발생: {str(e)}"


# ----------------------------
# 데이터 저장
# ----------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
RESUME_FILE = os.path.join(DATA_DIR, "my_resumes.json")


def load_my_resumes():
    if os.path.exists(RESUME_FILE):
        try:
            with open(RESUME_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []


def save_my_resumes(resumes):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(RESUME_FILE, "w", encoding="utf-8") as f:
        json.dump(resumes, f, ensure_ascii=False, indent=2)


# ----------------------------
# UI
# ----------------------------
st.title("📝 자소서 AI 첨삭")
st.caption("항공사 객실승무원 자기소개서를 AI가 첨삭해드립니다")

if not API_AVAILABLE:
    st.error("OpenAI API를 사용할 수 없습니다.")
    st.stop()

# 탭 구성
tab1, tab2, tab3 = st.tabs(["✍️ 첨삭받기", "📚 작성 가이드", "💾 내 자소서"])

# ========== 탭1: 첨삭받기 ==========
with tab1:
    st.subheader("✍️ 자소서 첨삭받기")

    col1, col2 = st.columns(2)

    with col1:
        selected_airline = st.selectbox("지원 항공사", AIRLINES)

    with col2:
        selected_item = st.selectbox(
            "자소서 항목",
            list(RESUME_ITEMS.keys()),
            format_func=lambda x: f"{x} ({RESUME_ITEMS[x]['description']})"
        )

    item_info = RESUME_ITEMS[selected_item]

    # 팁 표시
    with st.expander("💡 작성 팁 보기"):
        st.markdown("**작성 팁:**")
        for tip in item_info["tips"]:
            st.markdown(f"- {tip}")

        st.markdown("**피해야 할 표현:**")
        for bad in item_info["bad_examples"]:
            st.markdown(f"- ❌ {bad}")

    # 자소서 입력
    content = st.text_area(
        f"{selected_item} 내용 입력",
        height=250,
        max_chars=item_info["max_chars"],
        placeholder=f"{item_info['description']}에 대해 작성해주세요...",
        help=f"최대 {item_info['max_chars']}자"
    )

    char_count = len(content)
    st.caption(f"📏 {char_count} / {item_info['max_chars']}자")

    # 남은 사용량 표시
    if USAGE_LIMITER_AVAILABLE:
        remaining = get_remaining("자소서첨삭")
        st.markdown(f"오늘 남은 첨삭 횟수: **{remaining}회**")

    col1, col2 = st.columns([3, 1])

    with col1:
        submit = st.button("🔍 AI 첨삭받기", type="primary", use_container_width=True, disabled=len(content) < 50)

    with col2:
        if st.button("💾 저장", use_container_width=True, disabled=len(content) < 50):
            resumes = load_my_resumes()
            resumes.append({
                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "airline": selected_airline,
                "item": selected_item,
                "content": content,
                "created_at": datetime.now().isoformat()
            })
            save_my_resumes(resumes)
            st.success("저장되었습니다!")

    if submit and len(content) >= 50:
        # 사용량 체크
        if USAGE_LIMITER_AVAILABLE and not check_and_use("자소서첨삭"):
            st.stop()
        with st.spinner("AI가 첨삭 중입니다..."):
            feedback = get_ai_feedback(selected_airline, selected_item, content)

        if feedback:
            st.markdown("---")
            st.subheader("📋 AI 첨삭 결과")
            st.markdown(feedback)

            # 피드백 저장 버튼
            if st.button("💾 첨삭 결과 저장"):
                resumes = load_my_resumes()
                resumes.append({
                    "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "airline": selected_airline,
                    "item": selected_item,
                    "content": content,
                    "feedback": feedback,
                    "created_at": datetime.now().isoformat()
                })
                save_my_resumes(resumes)
                st.success("첨삭 결과가 저장되었습니다!")

    elif submit:
        st.warning("최소 50자 이상 작성해주세요.")


# ========== 탭2: 작성 가이드 ==========
with tab2:
    st.subheader("📚 항목별 작성 가이드")

    for item_name, info in RESUME_ITEMS.items():
        with st.expander(f"📌 {item_name}"):
            st.markdown(f"**{info['description']}**")

            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**✅ 작성 팁**")
                for tip in info["tips"]:
                    st.markdown(f"- {tip}")

            with col2:
                st.markdown("**❌ 피해야 할 표현**")
                for bad in info["bad_examples"]:
                    st.error(bad)

            st.caption(f"권장 글자수: {info['max_chars']}자 이내")

    st.markdown("---")

    st.info("""
    **STAR 기법이란?**
    - **S**ituation (상황): 어떤 상황이었는지
    - **T**ask (과제): 무엇을 해야 했는지
    - **A**ction (행동): 어떻게 행동했는지
    - **R**esult (결과): 어떤 결과를 얻었는지
    """)


# ========== 탭3: 내 자소서 ==========
with tab3:
    st.subheader("💾 저장된 자소서")

    resumes = load_my_resumes()

    if not resumes:
        st.info("저장된 자소서가 없습니다. '첨삭받기' 탭에서 저장해보세요!")
    else:
        # 최신순 정렬
        resumes = sorted(resumes, key=lambda x: x.get("created_at", ""), reverse=True)

        for resume in resumes:
            date_str = resume.get("created_at", "")[:10]
            has_feedback = "feedback" in resume

            with st.expander(f"📄 {resume.get('airline', '')} - {resume.get('item', '')} ({date_str}) {'✅' if has_feedback else ''}"):
                st.markdown("**원본:**")
                st.write(resume.get("content", ""))

                if has_feedback:
                    st.markdown("---")
                    st.markdown("**AI 첨삭:**")
                    st.markdown(resume.get("feedback", ""))

                if st.button("🗑️ 삭제", key=f"del_{resume.get('id')}"):
                    resumes = [r for r in resumes if r.get("id") != resume.get("id")]
                    save_my_resumes(resumes)
                    st.rerun()

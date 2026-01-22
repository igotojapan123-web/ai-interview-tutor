# pages/12_표정연습.py
# 동영상으로 표정/자세 연습

import streamlit as st
import streamlit.components.v1 as components
import os
import sys
import json
import base64
import requests
from typing import Optional, Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_utils import check_tester_password
from env_config import OPENAI_API_KEY

# 페이지 설정
st.set_page_config(page_title="표정 연습", page_icon="🎬", layout="wide")

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="표정 연습")
except ImportError:
    pass


st.markdown('<meta name="google" content="notranslate"><style>html{translate:no;}</style>', unsafe_allow_html=True)
st.markdown('<div translate="no" class="notranslate">', unsafe_allow_html=True)

# 비밀번호 보호
check_tester_password()

# 동영상 녹화 컴포넌트
try:
    from video_recorder import get_video_recorder_html, extract_frames_from_video, check_ffmpeg_available
    VIDEO_RECORDER_AVAILABLE = True
except ImportError:
    VIDEO_RECORDER_AVAILABLE = False


def analyze_video_frames(frames_base64: List[str], context: str = "면접") -> Optional[Dict[str, Any]]:
    """GPT-4 Vision으로 프레임 분석"""
    if not OPENAI_API_KEY or not frames_base64:
        return None

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    system_prompt = """항공사 면접 코칭 전문가입니다. 동영상에서 추출한 프레임들을 분석합니다.

JSON 형식으로만 응답:
{
    "expression": {
        "score": 1-10,
        "smile": "좋음/보통/부족",
        "smile_consistency": "일관됨/변동있음/부족",
        "eye_contact": "좋음/보통/부족",
        "naturalness": "자연스러움/어색함/긴장됨",
        "feedback": "표정 피드백"
    },
    "posture": {
        "score": 1-10,
        "consistency": "일관됨/흔들림",
        "shoulders": "바름/처짐/비대칭",
        "feedback": "자세 피드백"
    },
    "impression": {
        "score": 1-10,
        "confidence": "높음/보통/낮음",
        "friendliness": "높음/보통/낮음",
        "professionalism": "높음/보통/낮음",
        "feedback": "인상 피드백"
    },
    "time_analysis": {
        "start": "초반 상태",
        "mid": "중반 상태",
        "end": "후반 상태",
        "consistency_score": 1-10,
        "feedback": "시간별 변화 피드백"
    },
    "overall_score": 1-100,
    "strengths": ["강점1", "강점2"],
    "improvements": ["개선점1", "개선점2"],
    "tip": "핵심 팁"
}"""

    content_list = [{"type": "text", "text": f"{context} 동영상에서 추출한 {len(frames_base64)}개 프레임입니다. 시간 순서대로 표정과 자세를 분석해주세요."}]

    for frame in frames_base64[:5]:
        content_list.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{frame}", "detail": "low"}
        })

    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content_list}
        ],
        "temperature": 0.3,
        "max_tokens": 1500,
    }

    try:
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=90)
        r.raise_for_status()
        content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        return json.loads(content.strip())
    except Exception as e:
        st.error(f"분석 오류: {e}")
        return None


def display_result(result: Dict[str, Any]):
    """분석 결과 표시"""
    score = result.get("overall_score", 0)

    if score >= 80:
        color, emoji, grade = "#28a745", "🌟", "우수"
    elif score >= 60:
        color, emoji, grade = "#ffc107", "👍", "양호"
    else:
        color, emoji, grade = "#dc3545", "💪", "개선필요"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {color}20, {color}10); border: 2px solid {color}; border-radius: 20px; padding: 30px; text-align: center; margin-bottom: 20px;">
        <div style="font-size: 50px;">{emoji}</div>
        <div style="font-size: 42px; font-weight: bold; color: {color};">{score}점</div>
        <div style="font-size: 18px; color: #666;">{grade}</div>
    </div>
    """, unsafe_allow_html=True)

    # 시간별 변화
    time_a = result.get("time_analysis", {})
    if time_a:
        st.markdown("### ⏱️ 시간별 표정 변화")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**초반**: {time_a.get('start', '-')}")
        with col2:
            st.info(f"**중반**: {time_a.get('mid', '-')}")
        with col3:
            st.info(f"**후반**: {time_a.get('end', '-')}")

        if time_a.get('feedback'):
            st.caption(f"📊 일관성 점수: {time_a.get('consistency_score', 0)}/10 - {time_a.get('feedback')}")

    # 세부 분석
    st.markdown("### 📊 세부 분석")
    col1, col2, col3 = st.columns(3)

    expr = result.get("expression", {})
    with col1:
        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h4 style="color: #667eea;">😊 표정 {expr.get('score', 0)}/10</h4>
            <p>미소: {expr.get('smile', '-')}</p>
            <p>유지력: {expr.get('smile_consistency', '-')}</p>
            <p>눈맞춤: {expr.get('eye_contact', '-')}</p>
            <small style="color: #666;">{expr.get('feedback', '')}</small>
        </div>
        """, unsafe_allow_html=True)

    posture = result.get("posture", {})
    with col2:
        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h4 style="color: #764ba2;">🧍 자세 {posture.get('score', 0)}/10</h4>
            <p>어깨: {posture.get('shoulders', '-')}</p>
            <p>일관성: {posture.get('consistency', '-')}</p>
            <small style="color: #666;">{posture.get('feedback', '')}</small>
        </div>
        """, unsafe_allow_html=True)

    imp = result.get("impression", {})
    with col3:
        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h4 style="color: #f093fb;">✨ 인상 {imp.get('score', 0)}/10</h4>
            <p>자신감: {imp.get('confidence', '-')}</p>
            <p>친근함: {imp.get('friendliness', '-')}</p>
            <small style="color: #666;">{imp.get('feedback', '')}</small>
        </div>
        """, unsafe_allow_html=True)

    # 강점/개선점
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 💪 강점")
        for s in result.get("strengths", []):
            st.success(f"✓ {s}")
    with col2:
        st.markdown("### 📈 개선점")
        for i in result.get("improvements", []):
            st.warning(f"△ {i}")

    # 핵심 팁
    if result.get("tip"):
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb20, #f5576c10); border-radius: 12px; padding: 20px; margin-top: 20px; text-align: center;">
            <strong style="color: #f5576c;">💡 핵심 팁:</strong> {result.get('tip')}
        </div>
        """, unsafe_allow_html=True)


# ========================================
# 메인
# ========================================

st.title("🎬 표정 연습")
st.markdown("동영상을 녹화하고 AI가 표정과 자세를 분석합니다!")

if not OPENAI_API_KEY:
    st.error("OpenAI API 키가 필요합니다.")
    st.stop()

# 세션 상태
if "expr_result" not in st.session_state:
    st.session_state.expr_result = None
if "expr_history" not in st.session_state:
    st.session_state.expr_history = []

# 탭
tab1, tab2, tab3 = st.tabs(["🎬 연습하기", "📊 기록", "📚 가이드"])

with tab1:
    # 설정
    col1, col2 = st.columns(2)
    with col1:
        context = st.selectbox("연습 상황", ["1차 면접", "2차 면접", "최종 면접", "일반 연습"])
    with col2:
        airline_type = st.selectbox("항공사 유형", ["FSC (대한항공, 아시아나)", "LCC (제주, 진에어 등)"])

    st.markdown("---")

    # 동영상 녹화
    st.markdown("### 📹 동영상 녹화")

    if VIDEO_RECORDER_AVAILABLE:
        components.html(get_video_recorder_html(duration=15), height=700)

    st.markdown("---")

    # 동영상 업로드
    st.markdown("### 📤 녹화한 영상 업로드")
    video_file = st.file_uploader(
        "위에서 저장한 영상 파일을 업로드하세요",
        type=["webm", "mp4", "mov"],
        key="video_upload"
    )

    if video_file:
        st.video(video_file)
        st.success(f"✅ 영상 업로드됨: {video_file.name}")

        if st.button("🔍 분석하기", type="primary", use_container_width=True):
            with st.spinner("🤖 동영상 분석 중... (프레임 추출 → AI 분석)"):
                video_bytes = video_file.getvalue()

                # 프레임 추출
                st.info("📽️ 동영상에서 프레임 추출 중...")

                if VIDEO_RECORDER_AVAILABLE and check_ffmpeg_available():
                    frames = extract_frames_from_video(video_bytes, num_frames=5)
                else:
                    st.warning("ffmpeg가 설치되지 않아 프레임 추출이 제한됩니다. 이미지를 직접 업로드해주세요.")
                    frames = []

                if frames:
                    st.success(f"✅ {len(frames)}개 프레임 추출 완료")

                    # AI 분석
                    st.info("🧠 AI 표정 분석 중...")
                    result = analyze_video_frames(frames, f"{context}, {airline_type}")

                    if result:
                        st.session_state.expr_result = result
                        st.session_state.expr_history.append({"context": context, "result": result})
                        st.rerun()
                    else:
                        st.error("분석에 실패했습니다.")
                else:
                    st.error("프레임 추출에 실패했습니다.")

    # 대체: 이미지 업로드
    with st.expander("📷 또는 이미지 직접 업로드"):
        images = st.file_uploader("이미지 여러 장 선택", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="img_upload")

        if images:
            cols = st.columns(min(len(images), 5))
            for i, img in enumerate(images[:5]):
                with cols[i]:
                    st.image(img, use_container_width=True)

            if st.button("🔍 이미지 분석", use_container_width=True):
                with st.spinner("분석 중..."):
                    frames = [base64.b64encode(img.getvalue()).decode('utf-8') for img in images[:5]]
                    result = analyze_video_frames(frames, f"{context}, {airline_type}")

                    if result:
                        st.session_state.expr_result = result
                        st.session_state.expr_history.append({"context": context, "result": result})
                        st.rerun()

    # 결과 표시
    if st.session_state.expr_result:
        st.markdown("---")
        st.markdown("### 📊 분석 결과")
        display_result(st.session_state.expr_result)

        if st.button("🔄 새로 연습하기", use_container_width=True):
            st.session_state.expr_result = None
            st.rerun()

with tab2:
    st.markdown("### 📊 연습 기록")

    if not st.session_state.expr_history:
        st.info("아직 기록이 없습니다.")
    else:
        scores = [h["result"].get("overall_score", 0) for h in st.session_state.expr_history]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("평균", f"{sum(scores)/len(scores):.0f}점")
        with col2:
            st.metric("최고", f"{max(scores)}점")
        with col3:
            st.metric("횟수", f"{len(scores)}회")

        for i, h in enumerate(reversed(st.session_state.expr_history[-5:]), 1):
            with st.expander(f"#{len(st.session_state.expr_history) - i + 1} - {h['result'].get('overall_score', 0)}점"):
                display_result(h["result"])

with tab3:
    st.markdown("""
    ### 📚 표정 연습 가이드

    #### 😊 자연스러운 미소
    - **듀센 스마일**: 눈과 입이 함께 웃어야 자연스럽습니다
    - **입꼬리**: 살짝 올리되 과하지 않게
    - **눈웃음**: 눈가에 주름이 살짝 지는 정도

    #### 🧍 바른 자세
    - **어깨**: 양쪽이 수평으로
    - **목**: 턱을 살짝 당기고 목을 길게
    - **등**: 허리를 세우고 앉기

    #### ✨ FSC vs LCC
    - **FSC**: 품위 있고 절제된 미소
    - **LCC**: 밝고 에너지 넘치는 미소
    """)

st.markdown('</div>', unsafe_allow_html=True)

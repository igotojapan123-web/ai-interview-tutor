# new_features/7_AR복장체크.py
# FlyReady Lab - AR 복장 체크
# 카메라로 면접 복장 실시간 분석

import os
import sys
import base64
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sidebar_common import init_page, end_page
from logging_config import get_logger

logger = get_logger(__name__)

# OpenAI Vision API
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False


# =====================
# 항공사별 드레스코드
# =====================

AIRLINE_DRESS_CODES = {
    "대한항공": {
        "colors": ["네이비", "흰색"],
        "suit": "네이비 또는 차콜 그레이 정장",
        "blouse": "흰색 또는 아이보리 블라우스",
        "scarf": "하늘색 또는 네이비 스카프 (선택)",
        "shoes": "검정 또는 네이비 펌프스 (굽 5-7cm)",
        "stockings": "살색 스타킹",
        "hair": "단정한 올림머리 또는 단발 (어깨 위)",
        "makeup": "자연스럽고 깔끔한 메이크업",
        "accessories": "작은 귀걸이, 심플한 시계",
        "nails": "자연색 또는 연한 핑크",
        "tips": [
            "KE 블루 컬러를 포인트로 활용",
            "고급스럽고 세련된 이미지 강조",
            "글로벌 항공사다운 품격 표현",
        ],
    },
    "아시아나항공": {
        "colors": ["회색", "흰색", "레드포인트"],
        "suit": "그레이 또는 네이비 정장",
        "blouse": "흰색 블라우스",
        "scarf": "빨간색 또는 회색 스카프 (선택)",
        "shoes": "검정 펌프스 (굽 5-7cm)",
        "stockings": "살색 스타킹",
        "hair": "단정한 헤어스타일",
        "makeup": "밝고 화사한 메이크업",
        "accessories": "미니멀한 액세서리",
        "nails": "자연색 또는 레드",
        "tips": [
            "아시아나 레드를 포인트로",
            "'아름다운 사람들' 이미지 표현",
            "따뜻하고 친근한 인상",
        ],
    },
    "제주항공": {
        "colors": ["오렌지", "흰색", "네이비"],
        "suit": "네이비 또는 검정 정장",
        "blouse": "흰색 또는 오렌지 포인트",
        "scarf": "오렌지 스카프 (선택)",
        "shoes": "검정 펌프스",
        "stockings": "살색 스타킹",
        "hair": "밝고 활기찬 헤어스타일",
        "makeup": "생기있는 메이크업",
        "accessories": "간단한 귀걸이",
        "nails": "자연색",
        "tips": [
            "7C 오렌지를 포인트로",
            "젊고 활기찬 이미지",
            "친근하고 밝은 인상",
        ],
    },
    "공통": {
        "colors": ["네이비", "흰색", "검정"],
        "suit": "네이비 또는 검정 정장",
        "blouse": "흰색 블라우스",
        "scarf": "항공사 컬러 스카프 (선택)",
        "shoes": "검정 펌프스 (굽 5-7cm)",
        "stockings": "살색 스타킹",
        "hair": "단정한 올림머리 또는 단발",
        "makeup": "자연스럽고 깔끔한 메이크업",
        "accessories": "최소한의 액세서리",
        "nails": "자연색 또는 연한 색",
        "tips": [
            "청결하고 단정한 이미지가 가장 중요",
            "과한 화장이나 액세서리 피하기",
            "자신감 있는 자세와 미소",
        ],
    },
}

# 체크 항목
CHECK_ITEMS = [
    {"id": "overall", "name": "전체 인상", "description": "전반적으로 단정하고 전문적인가"},
    {"id": "suit_fit", "name": "정장 핏", "description": "정장이 몸에 잘 맞고 구김이 없는가"},
    {"id": "suit_color", "name": "정장 색상", "description": "적절한 색상인가 (네이비, 검정, 차콜)"},
    {"id": "blouse", "name": "블라우스", "description": "깔끔하고 목선이 단정한가"},
    {"id": "hair", "name": "헤어스타일", "description": "얼굴이 드러나고 단정한가"},
    {"id": "makeup", "name": "메이크업", "description": "자연스럽고 깔끔한가"},
    {"id": "accessories", "name": "액세서리", "description": "과하지 않고 적절한가"},
    {"id": "posture", "name": "자세", "description": "바르고 자신감 있는 자세인가"},
]


def analyze_outfit_image(image_data: bytes, airline: str = "공통") -> dict:
    """이미지에서 복장 분석 (Vision API)"""
    if not API_AVAILABLE:
        return {
            "overall_score": 75,
            "feedback": "API를 사용할 수 없어 기본 분석을 제공합니다.",
            "items": {item["id"]: {"score": 75, "feedback": "확인 필요"} for item in CHECK_ITEMS},
            "improvements": ["API 연결 후 상세 분석 가능"],
            "strengths": ["이미지 업로드 완료"],
        }

    dress_code = AIRLINE_DRESS_CODES.get(airline, AIRLINE_DRESS_CODES["공통"])

    # 이미지를 base64로 인코딩
    base64_image = base64.b64encode(image_data).decode("utf-8")

    system_prompt = f"""당신은 항공사 면접 복장 전문 컨설턴트입니다.
지원자의 면접 복장 사진을 분석하여 피드백을 제공해주세요.

분석 기준 ({airline}):
- 정장: {dress_code['suit']}
- 블라우스: {dress_code['blouse']}
- 구두: {dress_code['shoes']}
- 헤어: {dress_code['hair']}
- 메이크업: {dress_code['makeup']}
- 액세서리: {dress_code['accessories']}

JSON 형식으로 응답:
{{
    "overall_score": 0-100,
    "items": {{
        "overall": {{"score": 점수, "feedback": "피드백"}},
        "suit_fit": {{"score": 점수, "feedback": "피드백"}},
        "suit_color": {{"score": 점수, "feedback": "피드백"}},
        "blouse": {{"score": 점수, "feedback": "피드백"}},
        "hair": {{"score": 점수, "feedback": "피드백"}},
        "makeup": {{"score": 점수, "feedback": "피드백"}},
        "accessories": {{"score": 점수, "feedback": "피드백"}},
        "posture": {{"score": 점수, "feedback": "피드백"}}
    }},
    "strengths": ["강점1", "강점2"],
    "improvements": ["개선점1", "개선점2"],
    "feedback": "종합 피드백 2-3문장"
}}

사진이 불분명하거나 복장이 보이지 않으면 해당 항목은 "확인 불가"로 표시하세요.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "이 면접 복장을 분석해주세요."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )

        import json
        result_text = response.choices[0].message.content

        # JSON 추출
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]

        return json.loads(result_text)
    except Exception as e:
        logger.error(f"복장 분석 실패: {e}")
        return {
            "overall_score": 0,
            "feedback": f"분석 중 오류가 발생했습니다: {str(e)}",
            "items": {},
            "improvements": [],
            "strengths": [],
        }


def get_camera_component():
    """실시간 카메라 컴포넌트"""
    return """
    <div id="camera-container" style="text-align:center;">
        <video id="video" width="400" height="300" autoplay style="
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: scaleX(-1);
        "></video>

        <div style="margin-top:16px;">
            <button id="capture-btn" onclick="capturePhoto()" style="
                padding: 12px 32px;
                font-size: 1rem;
                font-weight: 700;
                border: none;
                border-radius: 8px;
                background: #3b82f6;
                color: white;
                cursor: pointer;
                margin: 8px;
            ">📸 사진 촬영</button>
        </div>

        <canvas id="canvas" style="display:none;"></canvas>
        <img id="captured" style="display:none;max-width:400px;border-radius:12px;margin-top:16px;">
    </div>

    <script>
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const captured = document.getElementById('captured');

        // 카메라 시작
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                video.srcObject = stream;
            })
            .catch(err => {
                console.error('카메라 접근 오류:', err);
                document.getElementById('camera-container').innerHTML =
                    '<p style="color:#ef4444;">카메라에 접근할 수 없습니다. 권한을 확인해주세요.</p>';
            });

        function capturePhoto() {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;

            const ctx = canvas.getContext('2d');
            ctx.translate(canvas.width, 0);
            ctx.scale(-1, 1);
            ctx.drawImage(video, 0, 0);

            const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
            captured.src = dataUrl;
            captured.style.display = 'block';

            // Streamlit에 데이터 전송
            window.parent.postMessage({
                type: 'captured_image',
                data: dataUrl
            }, '*');
        }
    </script>
    """


# =====================
# UI
# =====================

def render_ar_outfit():
    """AR 복장 체크 UI"""

    st.markdown("""
    <style>
    .ar-header {
        background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    .dress-code-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .check-item-result {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        background: #f8fafc;
        border-radius: 8px;
        margin: 8px 0;
    }
    .score-circle {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: white;
    }
    .score-high { background: #10b981; }
    .score-medium { background: #f59e0b; }
    .score-low { background: #ef4444; }
    .overall-score {
        font-size: 4rem;
        font-weight: 800;
        text-align: center;
    }
    .tip-card {
        background: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 16px;
        border-radius: 0 8px 8px 0;
        margin: 12px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # 헤더
    st.markdown("""
    <div class="ar-header">
        <h2 style="margin:0 0 8px 0;">👔 AR 복장 체크</h2>
        <p style="margin:0;opacity:0.9;">카메라로 면접 복장을 실시간 분석합니다</p>
    </div>
    """, unsafe_allow_html=True)

    # 항공사 선택
    airline = st.selectbox(
        "지원 항공사",
        ["공통", "대한항공", "아시아나항공", "제주항공"],
        key="ar_airline"
    )

    # 드레스코드 표시
    dress_code = AIRLINE_DRESS_CODES.get(airline, AIRLINE_DRESS_CODES["공통"])

    with st.expander(f"📋 {airline} 드레스코드 가이드", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**정장:** {dress_code['suit']}")
            st.markdown(f"**블라우스:** {dress_code['blouse']}")
            st.markdown(f"**구두:** {dress_code['shoes']}")
            st.markdown(f"**스타킹:** {dress_code['stockings']}")

        with col2:
            st.markdown(f"**헤어:** {dress_code['hair']}")
            st.markdown(f"**메이크업:** {dress_code['makeup']}")
            st.markdown(f"**네일:** {dress_code['nails']}")
            st.markdown(f"**액세서리:** {dress_code['accessories']}")

        st.markdown("**💡 팁:**")
        for tip in dress_code['tips']:
            st.markdown(f"- {tip}")

    st.markdown("---")

    # 이미지 업로드 또는 카메라
    tab1, tab2 = st.tabs(["📷 사진 업로드", "📹 실시간 카메라"])

    with tab1:
        uploaded_file = st.file_uploader(
            "면접 복장 사진을 업로드하세요",
            type=["jpg", "jpeg", "png"],
            key="outfit_upload"
        )

        if uploaded_file:
            st.image(uploaded_file, caption="업로드된 사진", width=400)

            if st.button("복장 분석하기", type="primary", key="analyze_upload"):
                with st.spinner("AI가 복장을 분석 중입니다..."):
                    image_data = uploaded_file.read()
                    result = analyze_outfit_image(image_data, airline)
                    st.session_state.ar_result = result
                st.rerun()

    with tab2:
        st.info("실시간 카메라로 복장을 확인하고 사진을 촬영하세요.")

        # 카메라 컴포넌트
        components.html(get_camera_component(), height=450)

        st.caption("촬영된 사진은 자동으로 분석됩니다.")

        # 파일 업로드로 카메라 캡처 대체
        camera_file = st.camera_input("또는 여기서 직접 촬영", key="camera_capture")

        if camera_file:
            if st.button("촬영한 사진 분석", type="primary"):
                with st.spinner("AI가 복장을 분석 중입니다..."):
                    image_data = camera_file.read()
                    result = analyze_outfit_image(image_data, airline)
                    st.session_state.ar_result = result
                st.rerun()

    # 분석 결과
    if st.session_state.get("ar_result"):
        result = st.session_state.ar_result

        st.markdown("---")
        st.markdown("## 분석 결과")

        # 전체 점수
        overall = result.get("overall_score", 0)
        if overall >= 80:
            score_class = "score-high"
            score_text = "훌륭해요!"
        elif overall >= 60:
            score_class = "score-medium"
            score_text = "조금만 더!"
        else:
            score_class = "score-low"
            score_text = "개선 필요"

        st.markdown(f"""
        <div style="text-align:center;margin:24px 0;">
            <div class="overall-score" style="color:{'#10b981' if overall >= 80 else '#f59e0b' if overall >= 60 else '#ef4444'};">
                {overall}점
            </div>
            <div style="font-size:1.2rem;color:#64748b;">{score_text}</div>
        </div>
        """, unsafe_allow_html=True)

        # 항목별 결과
        st.markdown("### 항목별 분석")

        items = result.get("items", {})
        for check_item in CHECK_ITEMS:
            item_result = items.get(check_item["id"], {})
            item_score = item_result.get("score", 0)
            item_feedback = item_result.get("feedback", "분석 불가")

            if item_score >= 80:
                score_class = "score-high"
            elif item_score >= 60:
                score_class = "score-medium"
            else:
                score_class = "score-low"

            st.markdown(f"""
            <div class="check-item-result">
                <div class="score-circle {score_class}">{item_score}</div>
                <div style="flex:1;">
                    <div style="font-weight:700;color:#1e3a5f;">{check_item['name']}</div>
                    <div style="font-size:0.85rem;color:#64748b;">{item_feedback}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 강점 & 개선점
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### ✅ 강점")
            for s in result.get("strengths", []):
                st.markdown(f"- {s}")

        with col2:
            st.markdown("### 💡 개선점")
            for i in result.get("improvements", []):
                st.markdown(f"- {i}")

        # 종합 피드백
        st.markdown("### 종합 피드백")
        st.info(result.get("feedback", ""))

        # 다시 분석
        if st.button("다시 분석하기"):
            st.session_state.ar_result = None
            st.rerun()


# 메인 실행
if __name__ == "__main__":
    render_ar_outfit()

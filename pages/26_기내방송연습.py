# pages/26_기내방송연습.py
# 기내방송 연습 페이지 - 음성 녹음 및 피드백

import streamlit as st
import os
import json
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_utils import check_tester_password

st.set_page_config(
    page_title="기내방송 연습",
    page_icon="🎙️",
    layout="wide"
)

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="기내방송 연습")
except ImportError:
    pass


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
# 기내방송 스크립트 (예시 값 포함)
# ----------------------------
ANNOUNCEMENTS = {
    "탑승 환영": {
        "korean": """안녕하십니까, 고객 여러분.
대한항공 KE001편에 탑승해 주셔서 감사합니다.
본 항공편은 인천에서 뉴욕까지 운항하며,
예정 비행시간은 약 14시간입니다.

좌석 상단의 선반에 짐을 넣으실 때는
다른 승객분들을 배려하여 한 칸씩만 사용해 주시기 바랍니다.
잠시 후 안전에 관한 안내방송이 있겠습니다.
편안한 여행 되시기 바랍니다. 감사합니다.""",

        "english": """Good morning, ladies and gentlemen.
Welcome aboard Korean Air flight KE001,
with service from Incheon to New York.
Our flight time will be approximately 14 hours.

Please store your carry-on items in the overhead bin
or under the seat in front of you.
Shortly, we will be showing our safety demonstration.
Thank you for flying with us today.""",

        "tips": [
            "밝고 따뜻한 톤으로",
            "적절한 속도 (너무 빠르지 않게)",
            "숫자는 또박또박",
            "미소 띤 목소리"
        ],
        "key_points": ["환영 인사", "편명/목적지", "비행시간", "짐 정리 안내"]
    },

    "안전 안내": {
        "korean": """고객 여러분, 잠시 안전에 관한 안내 말씀 드리겠습니다.

좌석벨트는 비행 중 항상 착용해 주시고,
벨트 사인이 켜지면 좌석에 앉아 주시기 바랍니다.

비상구는 기내 앞쪽과 뒤쪽, 그리고 날개 위에 있으며,
좌석 앞 주머니에 있는 안전 카드를 참고해 주시기 바랍니다.

화장실 내 흡연은 법으로 금지되어 있습니다.
안전한 여행을 위해 협조해 주셔서 감사합니다.""",

        "english": """Ladies and gentlemen, may I have your attention please.

Please keep your seatbelt fastened at all times while seated.
When the seatbelt sign is on, please return to your seat.

Emergency exits are located at the front and rear of the cabin,
as well as over the wings.
Please take a moment to review the safety card
in the seat pocket in front of you.

Smoking is prohibited in the lavatories.
Thank you for your attention.""",

        "tips": [
            "명확하고 차분하게",
            "중요한 부분 강조",
            "적절한 포즈 (쉼)",
            "안전 관련은 진지하게"
        ],
        "key_points": ["좌석벨트", "비상구 위치", "안전 카드", "흡연 금지"]
    },

    "이륙 전": {
        "korean": """고객 여러분, 곧 이륙하겠습니다.

좌석 테이블과 등받이를 원위치해 주시고,
좌석벨트를 착용해 주시기 바랍니다.
휴대전화를 포함한 모든 전자기기는
비행기 모드로 전환하거나 전원을 꺼 주시기 바랍니다.

창문 덮개는 열어 주시기 바랍니다.
협조해 주셔서 감사합니다.""",

        "english": """Ladies and gentlemen, we will be taking off shortly.

Please make sure your seat back is upright,
your tray table is stowed,
and your seatbelt is securely fastened.

All electronic devices, including mobile phones,
must be switched to airplane mode or turned off.

Please open your window shades.
Thank you for your cooperation.""",

        "tips": [
            "단호하지만 친절하게",
            "각 항목 끊어 읽기",
            "적절한 속도 유지"
        ],
        "key_points": ["테이블/등받이", "좌석벨트", "전자기기", "창문 덮개"]
    },

    "식음료 서비스": {
        "korean": """고객 여러분, 잠시 후 식음료 서비스를 시작하겠습니다.

오늘 준비된 음료는 커피, 차, 주스, 그리고 생수가 있습니다.
식사로는 불고기 덮밥과 해산물 파스타를 준비했습니다.

서비스 중에는 좌석벨트를 착용한 상태로
좌석에 앉아 계시기 바랍니다.
서비스 카트가 지나갈 때 통로 쪽으로
몸이나 손을 내밀지 않도록 주의해 주십시오.

감사합니다.""",

        "english": """Ladies and gentlemen,
we will now begin our in-flight service.

Today we have coffee, tea, juice, and water available.
For your meal, we are serving Bulgogi rice bowl and Seafood pasta.

Please remain seated with your seatbelt fastened
during the service.
Please be careful not to extend your arms or legs
into the aisle as the cart passes.

Thank you.""",

        "tips": [
            "메뉴 설명은 천천히",
            "서비스 안내 시 미소",
            "감사 인사 진심으로"
        ],
        "key_points": ["음료 종류", "기내식 메뉴", "안전 안내", "통로 주의"]
    },

    "착륙 전": {
        "korean": """고객 여러분, 곧 뉴욕 JFK 공항에 착륙하겠습니다.
현재 뉴욕의 기온은 섭씨 15도이며,
현지 시각은 오후 3시입니다.

좌석벨트를 착용하시고,
좌석 테이블과 등받이를 원위치해 주시기 바랍니다.
휴대전화와 전자기기는 비행기 모드를 유지해 주시고,
착륙 후 벨트 사인이 꺼질 때까지
좌석에 앉아 계시기 바랍니다.

대한항공을 이용해 주셔서 감사합니다.""",

        "english": """Ladies and gentlemen,
we will be landing at New York JFK Airport shortly.
The current temperature is 15 degrees Celsius,
and the local time is 3 PM.

Please fasten your seatbelt,
stow your tray table, and return your seat to the upright position.

Please keep your electronic devices in airplane mode.
For your safety, please remain seated
until the seatbelt sign has been turned off.

Thank you for flying with Korean Air.""",

        "tips": [
            "도착지 정보 정확히",
            "숫자 또박또박",
            "감사 인사 따뜻하게"
        ],
        "key_points": ["도착지/기온/시간", "좌석벨트/테이블", "전자기기", "착석 유지"]
    },

    "착륙 후": {
        "korean": """고객 여러분, 뉴욕 JFK 공항에 도착했습니다.

좌석벨트 사인이 꺼질 때까지 좌석에 앉아 계시기 바랍니다.
선반을 여실 때는 짐이 떨어질 수 있으니 주의해 주시고,
내리실 때 휴대품을 다시 한 번 확인해 주시기 바랍니다.

오늘 대한항공을 이용해 주셔서 진심으로 감사드립니다.
즐거운 하루 되시기 바랍니다.
다음에도 대한항공을 이용해 주시기 바랍니다.
감사합니다.""",

        "english": """Ladies and gentlemen,
welcome to New York JFK Airport.

Please remain seated until the seatbelt sign has been turned off.
Please use caution when opening the overhead bins,
as items may have shifted during the flight.
Please make sure to take all your personal belongings with you.

Thank you for choosing Korean Air today.
We hope you have a pleasant day,
and we look forward to seeing you again soon.
Thank you.""",

        "tips": [
            "환영하는 느낌으로",
            "감사 인사 진심을 담아",
            "다음 이용 권유는 밝게"
        ],
        "key_points": ["도착 환영", "안전 주의", "소지품 확인", "감사 인사"]
    },
}

# 데이터 저장
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PRACTICE_FILE = os.path.join(DATA_DIR, "announcement_practice.json")


def load_practice():
    if os.path.exists(PRACTICE_FILE):
        try:
            with open(PRACTICE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []


def save_practice(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PRACTICE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def transcribe_audio(audio_bytes):
    """음성을 텍스트로 변환"""
    if not API_AVAILABLE:
        return None

    try:
        # 임시 파일로 저장
        temp_path = os.path.join(DATA_DIR, "temp_audio.wav")
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)

        # Whisper로 변환
        with open(temp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ko"
            )

        # 임시 파일 삭제
        os.remove(temp_path)

        return transcript.text
    except Exception as e:
        return f"오류: {str(e)}"


def analyze_announcement(original_script, user_transcript, language):
    """방송 분석 및 피드백"""
    if not API_AVAILABLE:
        return None

    system_prompt = f"""당신은 10년 경력의 항공사 객실승무원 트레이너입니다.
기내방송 연습을 분석하고 피드백을 제공해주세요.

원본 스크립트와 사용자가 낭독한 내용을 비교 분석합니다.

평가 기준:
1. 정확성: 스크립트와 얼마나 일치하는지
2. 발음: 명확하게 전달되었는지 (인식된 텍스트 기준)
3. 누락: 빠뜨린 중요 내용이 있는지

피드백 형식:
## 📊 종합 점수: X/100점

## ✅ 잘한 점
- (구체적으로)

## 📝 개선할 점
- (구체적으로)

## 💡 팁
- (방송 톤, 속도, 발음 관련 조언)

언어: {language}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"원본 스크립트:\n{original_script}\n\n사용자 낭독 (음성인식 결과):\n{user_transcript}"}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"분석 오류: {str(e)}"


# ----------------------------
# UI
# ----------------------------
st.title("🎙️ 기내방송 연습")
st.caption("실제 기내방송 스크립트로 연습하고, 음성 녹음 후 AI 피드백을 받아보세요")

# 탭 구성
tab1, tab2, tab3 = st.tabs(["📜 스크립트 보기", "🎤 녹음 연습", "📝 연습 기록"])

# ========== 탭1: 스크립트 보기 ==========
with tab1:
    st.subheader("📜 기내방송 스크립트")

    # 방송 종류 선택
    selected_type = st.selectbox(
        "방송 종류 선택",
        list(ANNOUNCEMENTS.keys()),
        key="script_type"
    )

    announcement = ANNOUNCEMENTS[selected_type]

    st.markdown("---")

    # 스크립트 표시
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🇰🇷 한국어")
        st.markdown(f"""
        <div style="background: #f8fafc; padding: 20px; border-radius: 12px; border-left: 4px solid #3b82f6; line-height: 1.8; white-space: pre-wrap;">
{announcement["korean"]}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 🇺🇸 English")
        st.markdown(f"""
        <div style="background: #f8fafc; padding: 20px; border-radius: 12px; border-left: 4px solid #10b981; line-height: 1.8; white-space: pre-wrap;">
{announcement["english"]}
        </div>
        """, unsafe_allow_html=True)

    # 핵심 포인트
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎯 핵심 포인트")
        for point in announcement.get("key_points", []):
            st.markdown(f"- {point}")

    with col2:
        st.markdown("### 💡 방송 팁")
        for tip in announcement["tips"]:
            st.info(tip)


# ========== 탭2: 녹음 연습 ==========
with tab2:
    st.subheader("🎤 음성 녹음 연습")

    if not API_AVAILABLE:
        st.warning("⚠️ OpenAI API가 설정되지 않아 음성 분석 기능을 사용할 수 없습니다.")

    # 방송 선택
    practice_type = st.selectbox(
        "연습할 방송",
        list(ANNOUNCEMENTS.keys()),
        key="practice_type"
    )

    practice_lang = st.radio("언어", ["한국어", "English"], horizontal=True)

    announcement = ANNOUNCEMENTS[practice_type]
    script_text = announcement["korean"] if practice_lang == "한국어" else announcement["english"]

    st.markdown("---")

    # 스크립트 표시 옵션
    show_script = st.checkbox("스크립트 보면서 연습", value=True)

    if show_script:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea15, #764ba215); padding: 25px; border-radius: 16px; font-size: 16px; line-height: 2; white-space: pre-wrap;">
{script_text}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 음성 녹음
    st.markdown("### 🎙️ 음성 녹음")
    st.info("아래 버튼을 눌러 방송을 녹음하세요. 녹음 후 AI가 분석해드립니다.")

    audio_value = st.audio_input("녹음하기", key="audio_recorder")

    if audio_value:
        st.audio(audio_value)

        if st.button("🔍 AI 분석 받기", type="primary", use_container_width=True):
            if API_AVAILABLE:
                with st.spinner("음성 분석 중..."):
                    # 1. 음성을 텍스트로 변환
                    audio_bytes = audio_value.getvalue()
                    transcript = transcribe_audio(audio_bytes)

                    if transcript and not transcript.startswith("오류"):
                        st.markdown("---")
                        st.markdown("### 📝 음성 인식 결과")
                        st.write(transcript)

                        # 2. AI 분석
                        st.markdown("---")
                        st.markdown("### 📊 AI 피드백")

                        feedback = analyze_announcement(script_text, transcript, practice_lang)

                        if feedback:
                            st.markdown(feedback)

                            # 기록 저장
                            practices = load_practice()
                            practices.append({
                                "type": practice_type,
                                "language": practice_lang,
                                "transcript": transcript,
                                "feedback": feedback,
                                "date": datetime.now().isoformat()
                            })
                            save_practice(practices)
                            st.success("연습 기록이 저장되었습니다!")
                        else:
                            st.error("분석 중 오류가 발생했습니다.")
                    else:
                        st.error(f"음성 인식 실패: {transcript}")
            else:
                st.error("OpenAI API가 필요합니다.")

    st.markdown("---")

    # 수동 자가 평가
    st.markdown("### ✍️ 자가 평가 (녹음 없이)")

    with st.form("self_evaluation"):
        eval_accuracy = st.slider("정확성 (스크립트 일치)", 1, 5, 3)
        eval_tone = st.slider("목소리 톤/밝기", 1, 5, 3)
        eval_speed = st.slider("속도 적절성", 1, 5, 3)
        eval_clarity = st.slider("발음 명확성", 1, 5, 3)
        eval_note = st.text_area("메모", placeholder="개선할 점, 느낀 점 등")

        if st.form_submit_button("기록 저장", use_container_width=True):
            practices = load_practice()
            practices.append({
                "type": practice_type,
                "language": practice_lang,
                "accuracy": eval_accuracy,
                "tone": eval_tone,
                "speed": eval_speed,
                "clarity": eval_clarity,
                "note": eval_note,
                "date": datetime.now().isoformat()
            })
            save_practice(practices)
            st.success("기록되었습니다!")


# ========== 탭3: 연습 기록 ==========
with tab3:
    st.subheader("📝 나의 연습 기록")

    practices = load_practice()

    if not practices:
        st.info("아직 연습 기록이 없습니다. '녹음 연습' 탭에서 연습해보세요!")
    else:
        # 최신순
        practices = sorted(practices, key=lambda x: x.get("date", ""), reverse=True)

        # 통계
        total = len(practices)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("총 연습 횟수", f"{total}회")
        with col2:
            korean_count = len([p for p in practices if p.get("language") == "한국어"])
            st.metric("한국어/영어", f"{korean_count}/{total - korean_count}")

        st.markdown("---")

        # 기록 목록
        for p in practices[:15]:
            has_ai_feedback = "feedback" in p and "transcript" in p

            with st.expander(f"🎙️ {p.get('type', '')} ({p.get('language', '')}) - {p.get('date', '')[:10]} {'🤖' if has_ai_feedback else ''}"):
                if has_ai_feedback:
                    st.markdown("**🎯 음성 인식 결과:**")
                    st.write(p.get("transcript", ""))
                    st.markdown("---")
                    st.markdown("**📊 AI 피드백:**")
                    st.markdown(p.get("feedback", ""))
                else:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("정확성", f"{p.get('accuracy', '-')}/5")
                    with col2:
                        st.metric("톤", f"{p.get('tone', '-')}/5")
                    with col3:
                        st.metric("속도", f"{p.get('speed', '-')}/5")
                    with col4:
                        st.metric("발음", f"{p.get('clarity', '-')}/5")

                    if p.get("note"):
                        st.caption(f"메모: {p.get('note')}")

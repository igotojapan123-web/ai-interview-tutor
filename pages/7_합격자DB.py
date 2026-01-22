# pages/7_합격자DB.py
# 합격자 후기 게시판 - 단계별 분류 + 증빙 시스템 + 보상 시스템

import os
import json
import streamlit as st
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AIRLINES
from auth_utils import check_tester_password

st.set_page_config(
    page_title="합격자 후기",
    page_icon="🏆",
    layout="wide"
)

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="합격자 DB")
except ImportError:
    pass


# 구글 번역 방지
st.markdown(
    """
    <meta name="google" content="notranslate">
    <style>html { translate: no; }</style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# 비밀번호 보호
# ----------------------------
check_tester_password()

# ----------------------------
# 상수
# ----------------------------
# 항공사별 면접 단계 수 (몇 차가 최종인지)
# 3차까지 있는 항공사: 대한항공, 제주항공
# 나머지는 2차가 최종
AIRLINE_FINAL_ROUND = {
    "대한항공": 3,      # 1차(영어) → 2차(실무) → 3차(임원) → 최종
    "제주항공": 3,      # AI → 실무 → 임원 → 최종
    # 나머지는 기본값 2
}

def get_final_round(airline):
    """해당 항공사의 최종 면접 차수 반환"""
    return AIRLINE_FINAL_ROUND.get(airline, 2)

# 합격 단계 정의
PASS_STAGES = {
    "final": {"name": "최종 합격", "icon": "🏆", "order": 1},
    "3rd": {"name": "3차 면접 합격", "icon": "🥉", "order": 2},
    "2nd": {"name": "2차 면접 합격", "icon": "🥈", "order": 3},
    "1st": {"name": "1차 면접 합격", "icon": "🥇", "order": 4},
    "document": {"name": "서류 합격", "icon": "📄", "order": 5},
}

# 보상 정의
def get_reward(stage, airline):
    """합격 단계와 항공사에 따른 보상 반환"""
    final_round = get_final_round(airline)

    if stage == "document":
        return None  # 서류합격: 없음

    elif stage == "1st":
        if final_round == 2:
            # 2차가 최종인 항공사: 1차합격 → 스타벅스
            return {
                "type": "gifticon",
                "name": "스타벅스 아메리카노",
                "icon": "☕",
                "description": "스타벅스 아메리카노 기프티콘"
            }
        else:
            # 3차까지 있는 항공사: 1차합격 → 스탠다드 1주일
            return {
                "type": "standard",
                "name": "스탠다드 1주일",
                "icon": "⭐",
                "description": "스탠다드 멤버십 1주일 추가"
            }

    elif stage == "2nd":
        if final_round == 2:
            # 2차가 최종인 항공사: 2차=최종이므로 final로 처리해야 함
            # 이 케이스는 사용자가 "2nd" 대신 "final"을 선택해야 함
            return None
        else:
            # 3차까지 있는 항공사: 2차합격 → 스타벅스
            return {
                "type": "gifticon",
                "name": "스타벅스 아메리카노",
                "icon": "☕",
                "description": "스타벅스 아메리카노 기프티콘"
            }

    elif stage == "3rd":
        # 3차합격 (대한항공, 제주항공만 해당)
        # 3차가 최종 직전이므로 특별 보상 없음 or 스타벅스?
        # 일단 없음으로 처리
        return None

    elif stage == "final":
        return {
            "type": "premium",
            "name": "명예의전당 + 프리미엄 1주일",
            "icon": "👑",
            "description": "명예의전당 등록 + 프리미엄 멤버십 1주일 추가"
        }

    return None

# ----------------------------
# 데이터 저장/로드
# ----------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SUCCESS_STORIES_FILE = os.path.join(DATA_DIR, "success_stories.json")
PROOF_DIR = os.path.join(DATA_DIR, "proofs")
HALL_OF_FAME_FILE = os.path.join(DATA_DIR, "hall_of_fame.json")

def load_stories():
    if os.path.exists(SUCCESS_STORIES_FILE):
        try:
            with open(SUCCESS_STORIES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_stories(stories):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SUCCESS_STORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)

def load_hall_of_fame():
    if os.path.exists(HALL_OF_FAME_FILE):
        try:
            with open(HALL_OF_FAME_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_hall_of_fame(hof):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(HALL_OF_FAME_FILE, "w", encoding="utf-8") as f:
        json.dump(hof, f, ensure_ascii=False, indent=2)

def save_proof_image(image_data, story_id):
    os.makedirs(PROOF_DIR, exist_ok=True)
    filepath = os.path.join(PROOF_DIR, f"{story_id}.jpg")
    with open(filepath, "wb") as f:
        f.write(image_data)
    return filepath

def get_proof_image(story_id):
    filepath = os.path.join(PROOF_DIR, f"{story_id}.jpg")
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            return f.read()
    return None

# ----------------------------
# UI
# ----------------------------
st.title("🏆 합격자 후기 게시판")
st.caption("실제 합격자들의 소중한 경험담을 공유하는 공간입니다.")

# ----------------------------
# 명예의 전당 배너
# ----------------------------
hall_of_fame = load_hall_of_fame()
if hall_of_fame:
    st.markdown("### 👑 명예의 전당")
    cols = st.columns(min(len(hall_of_fame), 5))
    for i, member in enumerate(hall_of_fame[:5]):
        with cols[i]:
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; background: linear-gradient(135deg, #ffd70020, #ffed4a20); border-radius: 10px; border: 2px solid #ffd700;">
                <div style="font-size: 24px;">✈️</div>
                <div style="font-weight: bold; color: #b8860b;">{member.get('nickname', '익명')}</div>
                <div style="font-size: 12px; color: #666;">{member.get('airline', '')}</div>
                <div style="font-size: 11px; color: #888;">{member.get('year', '')}년 합격</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("---")

# 탭 구성
tab1, tab2, tab3 = st.tabs(["📖 후기 보기", "✍️ 후기 작성", "🎁 보상 안내"])

# ----------------------------
# 탭 1: 합격 후기 보기
# ----------------------------
with tab1:
    stories = load_stories()
    # 승인된 후기만 표시 (관리는 관리자 페이지에서)
    visible_stories = [s for s in stories if s.get("approved", False)]

    if not visible_stories:
        st.info("""
        ### 아직 등록된 합격 후기가 없습니다.

        **합격하셨다면 후기를 작성해주세요!**

        ✨ 후기 작성 시 단계별 보상이 있습니다! (🎁 보상 안내 탭 확인)
        """)
    else:
        # 필터
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_airline = st.selectbox("항공사", ["전체"] + AIRLINES, key="filter_airline")
        with col2:
            filter_stage = st.selectbox("합격 단계", ["전체"] + [v["name"] for v in PASS_STAGES.values()], key="filter_stage")
        with col3:
            approved_count = len([s for s in visible_stories if s.get("approved")])
            st.metric("총 후기", f"{approved_count}건")

        # 필터링
        filtered = visible_stories
        if filter_airline != "전체":
            filtered = [s for s in filtered if s.get("airline") == filter_airline]
        if filter_stage != "전체":
            stage_key = [k for k, v in PASS_STAGES.items() if v["name"] == filter_stage]
            if stage_key:
                filtered = [s for s in filtered if s.get("stage") == stage_key[0]]

        st.markdown("---")

        # 정렬 (최종합격 먼저)
        def get_stage_order(story):
            stage = story.get("stage", "final")
            return PASS_STAGES.get(stage, {}).get("order", 99)

        filtered = sorted(filtered, key=lambda x: (get_stage_order(x), x.get("created_at", "")))

        # 단계별 표시
        current_stage = None
        for story in filtered:
            stage = story.get("stage", "final")
            stage_info = PASS_STAGES.get(stage, PASS_STAGES["final"])

            if current_stage != stage:
                current_stage = stage
                st.markdown(f"### {stage_info['icon']} {stage_info['name']}")

            approved = story.get("approved", False)
            reward = get_reward(stage, story.get("airline", ""))
            reward_badge = f" {reward['icon']}" if reward else ""
            status_badge = "✅" if approved else "⏳"

            with st.expander(f"✈️ {story.get('airline', '미정')} | {story.get('nickname', '익명')} ({story.get('year', '?')}년) {reward_badge}"):
                # 보상 표시
                if approved and reward:
                    reward_color = {"gifticon": "#4a5568", "standard": "#3182ce", "premium": "#d69e2e"}
                    st.markdown(f"""
                    <div style="background: {reward_color.get(reward['type'], '#888')}15; padding: 8px 12px; border-radius: 8px; border-left: 4px solid {reward_color.get(reward['type'], '#888')}; margin-bottom: 10px;">
                        {reward['icon']} <strong>보상:</strong> {reward['description']}
                    </div>
                    """, unsafe_allow_html=True)

                # 기본 정보
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**전공:** {story.get('major', '-') or '-'}")
                    st.markdown(f"**경력:** {story.get('experience', '-') or '-'}")
                with col2:
                    st.markdown(f"**도전:** {story.get('attempts', 1)}번째")
                    st.markdown(f"**면접:** {story.get('interview_type', '-') or '-'}")

                st.divider()
                st.markdown("#### 📝 합격 수기")
                st.write(story.get('story', ''))

                questions = story.get('questions', [])
                tips = story.get('tips', [])
                if questions or tips:
                    st.divider()
                    col1, col2 = st.columns(2)
                    with col1:
                        if questions:
                            st.markdown("#### ❓ 받은 질문")
                            for q in questions:
                                if q: st.markdown(f"• {q}")
                    with col2:
                        if tips:
                            st.markdown("#### 💡 팁")
                            for t in tips:
                                if t: st.markdown(f"• {t}")

# ----------------------------
# 탭 2: 후기 작성
# ----------------------------
with tab2:
    st.subheader("✍️ 합격 후기 작성")

    st.warning("""
    ⚠️ **증빙 필수** - 합격 문자/이메일 스크린샷이 필요합니다.
    ⚠️ **개인정보 모자이크** 후 업로드해주세요.
    ✨ **보상 안내** - 🎁 보상 안내 탭을 확인하세요!
    """)

    with st.form("story_form"):
        st.markdown("### 📋 합격 정보")
        col1, col2, col3 = st.columns(3)

        with col1:
            airline = st.selectbox("항공사 *", ["선택"] + AIRLINES)

        # 항공사 선택에 따라 단계 옵션 동적 생성
        with col2:
            if airline and airline != "선택":
                final_round = get_final_round(airline)
                if final_round == 3:
                    stage_options = ["final", "3rd", "2nd", "1st", "document"]
                else:
                    # 2차가 최종인 경우: 2nd 옵션 제외 (최종으로 선택해야 함)
                    stage_options = ["final", "1st", "document"]

                stage = st.selectbox(
                    "합격 단계 *",
                    options=stage_options,
                    format_func=lambda x: f"{PASS_STAGES[x]['icon']} {PASS_STAGES[x]['name']}"
                )
            else:
                stage = st.selectbox("합격 단계 *", ["항공사를 먼저 선택하세요"], disabled=True)
                stage = "final"

        with col3:
            year = st.selectbox("연도 *", [2026, 2025, 2024, 2023])

        # 보상 미리보기
        if airline and airline != "선택":
            reward = get_reward(stage, airline)
            if reward:
                st.success(f"🎁 **예상 보상:** {reward['icon']} {reward['description']}")
            elif stage == "document":
                st.info("📄 서류합격은 보상이 없습니다.")

        st.markdown("---")

        # 증빙
        st.markdown("### 📎 증빙 자료 *")
        proof_file = st.file_uploader("합격 문자/이메일 스크린샷", type=["png", "jpg", "jpeg"])
        if proof_file:
            st.image(proof_file, width=250)

        # 기프티콘 수령 연락처 (해당되는 경우)
        if airline and airline != "선택":
            reward = get_reward(stage, airline)
            if reward and reward["type"] == "gifticon":
                st.markdown("### 📱 기프티콘 수령 연락처 *")
                phone = st.text_input("휴대폰 번호", placeholder="010-0000-0000", help="승인 후 기프티콘 발송에 사용됩니다.")
            else:
                phone = ""
        else:
            phone = ""

        st.markdown("---")

        # 기본 정보
        st.markdown("### 👤 기본 정보")
        col1, col2 = st.columns(2)
        with col1:
            nickname = st.text_input("닉네임 *", placeholder="예: 꿈꾸는승무원")
            major = st.text_input("전공", placeholder="예: 항공서비스학과")
            attempts = st.number_input("도전 횟수", 1, 20, 1)
        with col2:
            experience = st.text_input("경력", placeholder="예: 카페 1년")
            interview_type = st.text_input("면접 유형", placeholder="예: 1차 영어, 2차 임원")

        st.markdown("---")

        # 수기
        st.markdown("### 📝 합격 수기 *")
        story = st.text_area("합격 경험을 자유롭게 작성해주세요", height=180)

        # 질문 & 팁
        st.markdown("### ❓ 받은 질문 / 💡 팁 (선택)")
        col1, col2 = st.columns(2)
        questions = []
        tips = []
        for i in range(3):
            with col1:
                questions.append(st.text_input(f"질문 {i+1}", key=f"q{i}"))
            with col2:
                tips.append(st.text_input(f"팁 {i+1}", key=f"t{i}"))

        st.markdown("---")
        submitted = st.form_submit_button("📤 등록 신청", type="primary", use_container_width=True)

        if submitted:
            if airline == "선택":
                st.error("항공사를 선택하세요.")
            elif not nickname.strip():
                st.error("닉네임을 입력하세요.")
            elif not proof_file:
                st.error("증빙 자료를 업로드하세요.")
            elif not story.strip() or len(story.strip()) < 30:
                st.error("합격 수기를 30자 이상 작성하세요.")
            elif get_reward(stage, airline) and get_reward(stage, airline)["type"] == "gifticon" and not phone.strip():
                st.error("기프티콘 수령을 위한 연락처를 입력하세요.")
            else:
                story_id = f"{airline}_{nickname}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                save_proof_image(proof_file.getvalue(), story_id)

                new_story = {
                    "id": story_id,
                    "nickname": nickname.strip(),
                    "airline": airline,
                    "year": year,
                    "stage": stage,
                    "major": major.strip(),
                    "experience": experience.strip(),
                    "attempts": attempts,
                    "interview_type": interview_type.strip(),
                    "story": story.strip(),
                    "questions": [q for q in questions if q.strip()],
                    "tips": [t for t in tips if t.strip()],
                    "phone": phone.strip() if phone else "",
                    "approved": False,
                    "created_at": datetime.now().isoformat(),
                }

                stories = load_stories()
                stories.append(new_story)
                save_stories(stories)

                st.success("🎉 등록 신청 완료! 증빙 확인 후 1-2일 내 승인됩니다.")
                st.balloons()

# ----------------------------
# 탭 3: 보상 안내
# ----------------------------
with tab3:
    st.subheader("🎁 후기 작성 보상 안내")
    st.markdown("합격 후기를 작성해주시면 단계별로 보상을 드립니다!")

    st.markdown("---")

    # 보상 테이블
    st.markdown("### 📋 단계별 보상")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        #### 🏛️ 3차 면접이 있는 항공사
        <small>(대한항공, 제주항공)</small>

        | 단계 | 보상 |
        |------|------|
        | 📄 서류합격 | - |
        | 🥇 1차 합격 | ⭐ 스탠다드 1주일 |
        | 🥈 2차 합격 | ☕ 스타벅스 아메리카노 |
        | 🏆 최종 합격 | 👑 명예의전당 + 프리미엄 1주일 |
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        #### ✈️ 2차가 최종인 항공사
        <small>(아시아나, 진에어, 티웨이, 에어부산 등)</small>

        | 단계 | 보상 |
        |------|------|
        | 📄 서류합격 | - |
        | 🥇 1차 합격 | ☕ 스타벅스 아메리카노 |
        | 🏆 최종 합격 | 👑 명예의전당 + 프리미엄 1주일 |
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 보상 상세
    st.markdown("### 🎁 보상 상세")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="padding: 20px; background: #ebf8ff; border-radius: 10px; text-align: center;">
            <div style="font-size: 40px;">⭐</div>
            <h4>스탠다드 1주일</h4>
            <p style="font-size: 13px; color: #666;">스탠다드 멤버십<br/>1주일 무료 이용</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="padding: 20px; background: #f0fff4; border-radius: 10px; text-align: center;">
            <div style="font-size: 40px;">☕</div>
            <h4>스타벅스 기프티콘</h4>
            <p style="font-size: 13px; color: #666;">아메리카노 Tall<br/>기프티콘 발송</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="padding: 20px; background: #fffff0; border-radius: 10px; text-align: center;">
            <div style="font-size: 40px;">👑</div>
            <h4>명예의전당 + 프리미엄</h4>
            <p style="font-size: 13px; color: #666;">명예의전당 등록<br/>+ 프리미엄 1주일</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.info("""
    **안내사항**
    - 보상은 후기 승인 후 지급됩니다.
    - 기프티콘은 등록하신 연락처로 발송됩니다.
    - 멤버십 혜택은 계정에 자동 적용됩니다.
    - 허위 후기 작성 시 보상이 취소될 수 있습니다.
    """)

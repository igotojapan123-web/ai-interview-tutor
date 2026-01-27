# pages/99_관리자.py
# 관리자 전용 페이지 - 채용 관리 + 합격자 DB 관리

import os
import json
from datetime import datetime, date
import streamlit as st

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AIRLINES
from env_config import ADMIN_PASSWORD
from sidebar_common import render_sidebar
from logging_config import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title="관리자 모드",
    page_icon="🔐",
    layout="wide"
)
render_sidebar("관리자")

# 관리자 인증 체크
if not st.session_state.get("admin_authenticated", False):
    st.warning("🔐 관리자 전용 페이지입니다.")
    pw = st.text_input("관리자 비밀번호를 입력하세요", type="password")
    if pw == ADMIN_PASSWORD:
        st.session_state["admin_authenticated"] = True
        st.rerun()
    elif pw:
        st.error("비밀번호가 틀렸습니다.")
    st.stop()

# ----------------------------
# 파일 경로
# ----------------------------
DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIRING_DATA_FILE = os.path.join(DATA_DIR, "hiring_data.json")
SUCCESS_STORIES_FILE = os.path.join(DATA_DIR, "data", "success_stories.json")
PROOF_DIR = os.path.join(DATA_DIR, "data", "proofs")
SUBSCRIBERS_FILE = os.path.join(DATA_DIR, "data", "subscribers.json")

# 공식 채용사이트
CAREER_SITES = {
    "대한항공": "koreanair.recruiter.co.kr",
    "아시아나항공": "flyasiana.recruiter.co.kr",
    "에어프레미아": "airpremia.career.greetinghr.com",
    "진에어": "jinair.recruiter.co.kr",
    "제주항공": "jejuair.recruiter.co.kr",
    "티웨이항공": "twayair.recruiter.co.kr",
    "에어부산": "airbusan.recruiter.co.kr",
    "에어서울": "flyairseoul.com",
    "이스타항공": "eastarjet.com",
    "에어로케이": "aerok.com",
    "파라타항공": "parataair.recruiter.co.kr",
}

# 합격 단계
PASS_STAGES = {
    "final": {"name": "최종 합격", "icon": "🏆", "order": 1},
    "3rd": {"name": "3차 면접 합격", "icon": "🥉", "order": 2},
    "2nd": {"name": "2차 면접 합격", "icon": "🥈", "order": 3},
    "1st": {"name": "1차 면접 합격", "icon": "🥇", "order": 4},
    "document": {"name": "서류 합격", "icon": "📄", "order": 5},
}

# ----------------------------
# 채용 데이터 함수
# ----------------------------
def load_hiring_data():
    if os.path.exists(HIRING_DATA_FILE):
        try:
            with open(HIRING_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"채용 데이터 로드 실패: {e}")
    return {"last_updated": "", "recruitments": []}


def save_hiring_data(data):
    data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    with open(HIRING_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_status(start_date_str, end_date_str):
    today = date.today()
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError) as e:
        logger.debug(f"날짜 파싱 실패: {e}")
        return "마감", "⚫"

    if today < start_date:
        return "예정", "🟡"
    elif today <= end_date:
        return "진행중", "🟢"
    else:
        return "마감", "⚫"


def get_dday(end_date_str):
    today = date.today()
    try:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        diff = (end_date - today).days
        if diff > 0:
            return f"D-{diff}"
        elif diff == 0:
            return "D-Day"
        else:
            return f"D+{abs(diff)}"
    except (ValueError, TypeError) as e:
        logger.debug(f"D-Day 계산 실패: {e}")
        return "-"


# ----------------------------
# 구독자 데이터 함수
# ----------------------------
def load_subscribers():
    """구독자 데이터 로드"""
    if os.path.exists(SUBSCRIBERS_FILE):
        try:
            with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"구독자 데이터 로드 실패: {e}")
    return {"subscribers": [], "total_count": 0}


def save_subscribers(data):
    """구독자 데이터 저장"""
    os.makedirs(os.path.dirname(SUBSCRIBERS_FILE), exist_ok=True)
    with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_active_subscribers(airline=None):
    """활성 구독자 목록 (특정 항공사 필터 가능)"""
    data = load_subscribers()
    active = [s for s in data["subscribers"] if s.get("active", True)]

    if airline:
        # 해당 항공사 선택했거나, 전체 선택한 구독자
        active = [s for s in active if not s.get("airlines") or airline in s.get("airlines", [])]

    return active


# ----------------------------
# 합격자 데이터 함수
# ----------------------------
def load_stories():
    if os.path.exists(SUCCESS_STORIES_FILE):
        try:
            with open(SUCCESS_STORIES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"합격 스토리 로드 실패: {e}")
    return []


def save_stories(stories):
    os.makedirs(os.path.dirname(SUCCESS_STORIES_FILE), exist_ok=True)
    with open(SUCCESS_STORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)


def get_proof_image(story_id):
    filepath = os.path.join(PROOF_DIR, f"{story_id}.jpg")
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            return f.read()
    return None


def get_reward(stage, airline):
    """합격 단계와 항공사에 따른 보상"""
    AIRLINE_FINAL_ROUND = {"대한항공": 3, "제주항공": 3}
    final_round = AIRLINE_FINAL_ROUND.get(airline, 2)

    if stage == "document":
        return None
    elif stage == "1st":
        if final_round == 2:
            return {"type": "gifticon", "name": "스타벅스", "icon": "☕", "description": "스타벅스 아메리카노"}
        else:
            return {"type": "standard", "name": "스탠다드 1주일", "icon": "⭐", "description": "스탠다드 멤버십 1주일"}
    elif stage == "2nd":
        if final_round == 3:
            return {"type": "gifticon", "name": "스타벅스", "icon": "☕", "description": "스타벅스 아메리카노"}
        return None
    elif stage == "final":
        return {"type": "premium", "name": "프리미엄", "icon": "👑", "description": "프리미엄 멤버십 1주일"}
    return None


# =====================
# UI
# =====================

st.title("🔐 관리자 모드")
st.caption("채용 정보 및 합격자 DB 관리")

# =====================
# 탭 구성
# =====================
tab1, tab2, tab3, tab4 = st.tabs(["📅 채용 관리", "🏆 합격자 관리", "📬 구독자 관리", "🔗 채용사이트"])

# ========== 탭1: 채용 관리 ==========
with tab1:
    st.subheader("📅 채용 정보 관리")

    hiring_data = load_hiring_data()
    recruitments = hiring_data.get("recruitments", [])

    st.info(f"📅 마지막 업데이트: **{hiring_data.get('last_updated', '없음')}** | 총 **{len(recruitments)}**건")

    # 서브탭
    sub_tab1, sub_tab2 = st.tabs(["📋 목록 관리", "➕ 새 채용 추가"])

    with sub_tab1:
        if not recruitments:
            st.warning("등록된 채용 공고가 없습니다.")
        else:
            filter_status = st.radio("필터", ["전체", "진행중", "예정", "마감"], horizontal=True, key="hire_filter")

            status_order = {"진행중": 0, "예정": 1, "마감": 2}
            sorted_list = []
            for r in recruitments:
                status, emoji = get_status(r.get("start_date", ""), r.get("end_date", ""))
                r["_status"] = status
                r["_emoji"] = emoji
                r["_dday"] = get_dday(r.get("end_date", ""))
                sorted_list.append(r)

            sorted_list.sort(key=lambda x: (status_order.get(x["_status"], 2), x.get("end_date", "")))

            if filter_status != "전체":
                sorted_list = [r for r in sorted_list if r["_status"] == filter_status]

            for r in sorted_list:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

                    with col1:
                        st.markdown(f"### {r['_emoji']} {r['airline']}")
                        st.caption(r.get("position", ""))

                    with col2:
                        st.write(f"📅 {r.get('start_date', '')} ~ {r.get('end_date', '')}")
                        st.write(f"👥 {r.get('expected_count', '미공개')}")

                    with col3:
                        st.metric("상태", r["_status"])
                        st.caption(r["_dday"])

                    with col4:
                        if st.button("✏️", key=f"edit_{r['id']}", help="수정"):
                            st.session_state.edit_hire_id = r["id"]
                            st.rerun()

                        if st.button("🗑️", key=f"del_{r['id']}", help="삭제"):
                            hiring_data["recruitments"] = [x for x in recruitments if x.get("id") != r["id"]]
                            save_hiring_data(hiring_data)
                            st.success("삭제됨!")
                            st.rerun()

                    st.markdown("---")

            # 수정 폼
            if "edit_hire_id" in st.session_state:
                edit_id = st.session_state.edit_hire_id
                edit_item = next((r for r in recruitments if r.get("id") == edit_id), None)

                if edit_item:
                    st.subheader(f"✏️ 수정: {edit_item['airline']}")

                    with st.form("edit_hire_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            edit_airline = st.selectbox("항공사", AIRLINES, index=AIRLINES.index(edit_item["airline"]) if edit_item["airline"] in AIRLINES else 0)
                            edit_position = st.text_input("포지션", value=edit_item.get("position", ""))
                            edit_count = st.text_input("모집인원", value=edit_item.get("expected_count", ""))
                        with col2:
                            edit_start = st.date_input("시작일", value=datetime.strptime(edit_item["start_date"], "%Y-%m-%d").date())
                            edit_end = st.date_input("마감일", value=datetime.strptime(edit_item["end_date"], "%Y-%m-%d").date())
                            edit_note = st.text_input("비고", value=edit_item.get("note", ""))

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("저장", type="primary", use_container_width=True):
                                for r in hiring_data["recruitments"]:
                                    if r["id"] == edit_id:
                                        r["airline"] = edit_airline
                                        r["position"] = edit_position
                                        r["start_date"] = edit_start.strftime("%Y-%m-%d")
                                        r["end_date"] = edit_end.strftime("%Y-%m-%d")
                                        r["expected_count"] = edit_count
                                        r["note"] = edit_note
                                        r["source"] = CAREER_SITES.get(edit_airline, "")
                                save_hiring_data(hiring_data)
                                del st.session_state.edit_hire_id
                                st.success("수정 완료!")
                                st.rerun()
                        with col2:
                            if st.form_submit_button("취소", use_container_width=True):
                                del st.session_state.edit_hire_id
                                st.rerun()

    with sub_tab2:
        st.markdown("공식 채용사이트에서 확인한 정보만 입력하세요")

        with st.form("add_hire_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_airline = st.selectbox("항공사 *", AIRLINES)
                new_position = st.text_input("포지션 *", placeholder="예: 2026년 상반기 신입 객실승무원")
                new_count = st.text_input("모집인원", placeholder="예: 두 자릿수")
            with col2:
                new_start = st.date_input("시작일 *", value=date.today())
                new_end = st.date_input("마감일 *", value=date.today())
                new_note = st.text_input("비고", placeholder="예: 4월 입사 예정")

            st.caption(f"📌 출처: {CAREER_SITES.get(new_airline, '')}")

            if st.form_submit_button("추가", type="primary", use_container_width=True):
                if not new_position:
                    st.error("포지션을 입력하세요!")
                elif new_end < new_start:
                    st.error("마감일이 시작일보다 빠를 수 없습니다!")
                else:
                    max_id = max([r.get("id", 0) for r in recruitments], default=0)
                    new_item = {
                        "id": max_id + 1,
                        "airline": new_airline,
                        "position": new_position,
                        "start_date": new_start.strftime("%Y-%m-%d"),
                        "end_date": new_end.strftime("%Y-%m-%d"),
                        "expected_count": new_count if new_count else "미공개",
                        "note": new_note,
                        "source": CAREER_SITES.get(new_airline, "")
                    }
                    hiring_data["recruitments"].append(new_item)
                    save_hiring_data(hiring_data)
                    st.success(f"✅ {new_airline} 채용 공고 추가됨!")
                    st.rerun()


# ========== 탭2: 합격자 관리 ==========
with tab2:
    st.subheader("🏆 합격자 후기 관리")

    stories = load_stories()

    # 통계
    total = len(stories)
    approved = len([s for s in stories if s.get("approved")])
    pending = total - approved

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("전체", f"{total}건")
    with col2:
        st.metric("승인됨", f"{approved}건")
    with col3:
        st.metric("대기중", f"{pending}건", delta="검토 필요" if pending > 0 else None)

    st.markdown("---")

    # 필터
    filter_approved = st.radio("필터", ["전체", "승인 대기", "승인됨"], horizontal=True, key="story_filter")

    if filter_approved == "승인 대기":
        filtered = [s for s in stories if not s.get("approved")]
    elif filter_approved == "승인됨":
        filtered = [s for s in stories if s.get("approved")]
    else:
        filtered = stories

    if not filtered:
        st.info("해당 조건의 후기가 없습니다.")
    else:
        # 정렬 (최신순)
        filtered = sorted(filtered, key=lambda x: x.get("created_at", ""), reverse=True)

        for story in filtered:
            approved_flag = story.get("approved", False)
            stage = story.get("stage", "final")
            stage_info = PASS_STAGES.get(stage, PASS_STAGES["final"])
            reward = get_reward(stage, story.get("airline", ""))

            status_badge = "✅ 승인됨" if approved_flag else "⏳ 대기중"

            with st.expander(f"{stage_info['icon']} {story.get('airline', '')} | {story.get('nickname', '익명')} | {status_badge}"):
                # 증빙 이미지
                proof_data = get_proof_image(story.get("id"))
                if proof_data:
                    st.image(proof_data, caption="증빙 자료", width=300)
                else:
                    st.warning("증빙 이미지 없음")

                # 기본 정보
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**항공사:** {story.get('airline', '-')}")
                    st.write(f"**단계:** {stage_info['name']}")
                    st.write(f"**연도:** {story.get('year', '-')}년")
                with col2:
                    st.write(f"**닉네임:** {story.get('nickname', '-')}")
                    st.write(f"**연락처:** {story.get('phone', '-')}")
                    st.write(f"**등록일:** {story.get('created_at', '-')[:10]}")

                if reward:
                    st.info(f"🎁 보상: {reward['icon']} {reward['description']}")

                st.markdown("**수기 내용:**")
                st.write(story.get("story", "")[:200] + "..." if len(story.get("story", "")) > 200 else story.get("story", ""))

                st.markdown("---")

                # 액션 버튼
                col1, col2, col3 = st.columns(3)
                with col1:
                    if not approved_flag:
                        if st.button("✅ 승인", key=f"approve_{story.get('id')}", use_container_width=True):
                            for s in stories:
                                if s.get("id") == story.get("id"):
                                    s["approved"] = True
                                    s["reward"] = reward
                            save_stories(stories)
                            st.success("승인 완료!")
                            st.rerun()
                    else:
                        st.write("✅ 이미 승인됨")

                with col2:
                    if approved_flag:
                        if st.button("↩️ 승인 취소", key=f"unapprove_{story.get('id')}", use_container_width=True):
                            for s in stories:
                                if s.get("id") == story.get("id"):
                                    s["approved"] = False
                            save_stories(stories)
                            st.warning("승인 취소됨")
                            st.rerun()

                with col3:
                    if st.button("🗑️ 삭제", key=f"del_story_{story.get('id')}", use_container_width=True):
                        stories = [s for s in stories if s.get("id") != story.get("id")]
                        save_stories(stories)
                        st.success("삭제됨!")
                        st.rerun()


# ========== 탭4: 채용사이트 ==========
with tab4:
    st.subheader("🔗 공식 채용사이트 바로가기")
    st.caption("채용 공고 확인 후 '채용 관리' 탭에서 등록하세요")

    st.markdown("### 🏛️ FSC (대형항공사)")
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("대한항공", "https://koreanair.recruiter.co.kr/", use_container_width=True)
    with col2:
        st.link_button("아시아나항공", "https://flyasiana.recruiter.co.kr/", use_container_width=True)

    st.markdown("### 🌟 HSC (하이브리드)")
    st.link_button("에어프레미아", "https://airpremia.career.greetinghr.com/", use_container_width=True)

    st.markdown("### ✈️ LCC (저비용항공사)")

    lcc_list = [
        ("진에어", "https://jinair.recruiter.co.kr/"),
        ("제주항공", "https://jejuair.recruiter.co.kr/"),
        ("티웨이항공", "https://twayair.recruiter.co.kr/"),
        ("에어부산", "https://airbusan.recruiter.co.kr/"),
        ("에어서울", "https://flyairseoul.com/"),
        ("이스타항공", "https://www.eastarjet.com/"),
        ("에어로케이", "https://www.aerok.com/"),
        ("파라타항공", "https://parataair.recruiter.co.kr/"),
    ]

    for i in range(0, len(lcc_list), 4):
        cols = st.columns(4)
        for j, col in enumerate(cols):
            if i + j < len(lcc_list):
                name, url = lcc_list[i + j]
                with col:
                    st.link_button(name, url, use_container_width=True)

# ========== 탭3: 구독자 관리 ==========
with tab3:
    st.subheader("📬 채용 알림 구독자 관리")

    subscribers_data = load_subscribers()
    all_subscribers = subscribers_data.get("subscribers", [])
    active_subscribers = [s for s in all_subscribers if s.get("active", True)]
    inactive_subscribers = [s for s in all_subscribers if not s.get("active", True)]

    # 통계
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("전체 구독자", f"{len(all_subscribers)}명")
    with col2:
        st.metric("활성 구독자", f"{len(active_subscribers)}명", delta=f"+{len(active_subscribers)}")
    with col3:
        st.metric("해지 구독자", f"{len(inactive_subscribers)}명")

    st.markdown("---")

    # 서브탭
    sub_tab1, sub_tab2 = st.tabs(["📋 구독자 목록", "📊 항공사별 현황"])

    with sub_tab1:
        if not all_subscribers:
            st.info("등록된 구독자가 없습니다.")
        else:
            # 필터
            status_filter = st.radio("필터", ["활성", "해지", "전체"], horizontal=True, key="sub_filter")

            if status_filter == "활성":
                filtered = active_subscribers
            elif status_filter == "해지":
                filtered = inactive_subscribers
            else:
                filtered = all_subscribers

            st.caption(f"총 {len(filtered)}명")

            # 목록
            for sub in filtered:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        status_emoji = "🟢" if sub.get("active", True) else "⚫"
                        st.markdown(f"**{status_emoji} {sub.get('name', '이름없음')}**")
                        st.caption(f"📧 {sub.get('email', '')}")
                        if sub.get("phone"):
                            st.caption(f"📱 {sub.get('phone')}")

                    with col2:
                        airlines = sub.get("airlines", [])
                        if airlines:
                            st.caption(f"관심: {', '.join(airlines[:3])}{'...' if len(airlines) > 3 else ''}")
                        else:
                            st.caption("관심: 전체 항공사")
                        st.caption(f"등록일: {sub.get('created_at', '-')}")

                    with col3:
                        if sub.get("active", True):
                            if st.button("해지", key=f"unsub_{sub.get('id')}"):
                                for s in subscribers_data["subscribers"]:
                                    if s.get("id") == sub.get("id"):
                                        s["active"] = False
                                save_subscribers(subscribers_data)
                                st.rerun()
                        else:
                            if st.button("복원", key=f"restore_{sub.get('id')}"):
                                for s in subscribers_data["subscribers"]:
                                    if s.get("id") == sub.get("id"):
                                        s["active"] = True
                                save_subscribers(subscribers_data)
                                st.rerun()

                    st.markdown("---")

    with sub_tab2:
        st.markdown("### 📊 항공사별 관심 구독자")

        airline_counts = {}
        no_preference = 0

        for sub in active_subscribers:
            airlines = sub.get("airlines", [])
            if not airlines:
                no_preference += 1
            else:
                for airline in airlines:
                    airline_counts[airline] = airline_counts.get(airline, 0) + 1

        # 전체 선택
        st.info(f"📢 **전체 항공사 알림 수신:** {no_preference}명")

        # 항공사별
        if airline_counts:
            sorted_airlines = sorted(airline_counts.items(), key=lambda x: x[1], reverse=True)
            for airline, count in sorted_airlines:
                st.markdown(f"✈️ **{airline}:** {count}명")
        else:
            st.caption("특정 항공사 선택 구독자가 없습니다.")

        st.markdown("---")

        # 알림 발송 안내
        st.markdown("### 📧 알림 발송")
        st.warning("""
        **알림 발송 방법:**
        1. 새 채용 공고 등록 시 자동으로 구독자 목록 확인
        2. 해당 항공사 관심 구독자 + 전체 구독자에게 발송
        3. 이메일 발송은 외부 서비스 연동 필요 (Mailchimp, SendGrid 등)
        """)

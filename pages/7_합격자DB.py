# pages/7_합격자DB.py
# 합격자 후기 게시판 - 전면 개편: 통계 대시보드 + 질문 DB + 좋아요/댓글

import os
import json
import streamlit as st
from datetime import datetime
from collections import defaultdict, Counter

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AIRLINES
from sidebar_common import render_sidebar
from logging_config import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title="합격자 DB",
    page_icon="🏆",
    layout="wide"
)
render_sidebar("합격자DB")


# 구글 번역 방지
st.markdown(
    """
    <meta name="google" content="notranslate">
    <style>html { translate: no; }</style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# 상수
# ----------------------------
AIRLINE_FINAL_ROUND = {
    "대한항공": 3,
    "제주항공": 3,
}

def get_final_round(airline):
    return AIRLINE_FINAL_ROUND.get(airline, 2)

PASS_STAGES = {
    "final": {"name": "최종 합격", "icon": "🏆", "order": 1},
    "3rd": {"name": "3차 면접 합격", "icon": "🥉", "order": 2},
    "2nd": {"name": "2차 면접 합격", "icon": "🥈", "order": 3},
    "1st": {"name": "1차 면접 합격", "icon": "🥇", "order": 4},
    "document": {"name": "서류 합격", "icon": "📄", "order": 5},
}

# 보상 정의
def get_reward(stage, airline):
    final_round = get_final_round(airline)

    if stage == "document":
        return None
    elif stage == "1st":
        if final_round == 2:
            return {"type": "gifticon", "name": "스타벅스 아메리카노", "icon": "☕", "description": "스타벅스 아메리카노 기프티콘"}
        else:
            return {"type": "standard", "name": "스탠다드 1주일", "icon": "⭐", "description": "스탠다드 멤버십 1주일 추가"}
    elif stage == "2nd":
        if final_round == 2:
            return None
        else:
            return {"type": "gifticon", "name": "스타벅스 아메리카노", "icon": "☕", "description": "스타벅스 아메리카노 기프티콘"}
    elif stage == "3rd":
        return None
    elif stage == "final":
        return {"type": "premium", "name": "프리미엄 1주일", "icon": "👑", "description": "프리미엄 멤버십 1주일 추가"}
    return None

# ----------------------------
# 데이터 저장/로드
# ----------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SUCCESS_STORIES_FILE = os.path.join(DATA_DIR, "success_stories.json")
PROOF_DIR = os.path.join(DATA_DIR, "proofs")
LIKES_FILE = os.path.join(DATA_DIR, "story_likes.json")
COMMENTS_FILE = os.path.join(DATA_DIR, "story_comments.json")

def load_stories():
    if os.path.exists(SUCCESS_STORIES_FILE):
        try:
            with open(SUCCESS_STORIES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, OSError) as e:
            logger.error(f"합격자 스토리 로드 실패: {e}")
            return []
    return []

def save_stories(stories):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SUCCESS_STORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)

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

# 좋아요 데이터
def load_likes():
    if os.path.exists(LIKES_FILE):
        try:
            with open(LIKES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, OSError) as e:
            logger.error(f"좋아요 데이터 로드 실패: {e}")
            return {}
    return {}

def save_likes(likes):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LIKES_FILE, "w", encoding="utf-8") as f:
        json.dump(likes, f, ensure_ascii=False, indent=2)

def get_like_count(story_id, likes_data):
    return likes_data.get(story_id, {}).get("count", 0)

def toggle_like(story_id, user_id):
    likes = load_likes()
    if story_id not in likes:
        likes[story_id] = {"count": 0, "users": []}

    if user_id in likes[story_id]["users"]:
        likes[story_id]["users"].remove(user_id)
        likes[story_id]["count"] = max(0, likes[story_id]["count"] - 1)
        liked = False
    else:
        likes[story_id]["users"].append(user_id)
        likes[story_id]["count"] += 1
        liked = True

    save_likes(likes)
    return liked

def has_liked(story_id, user_id, likes_data):
    return user_id in likes_data.get(story_id, {}).get("users", [])

# 댓글 데이터
def load_comments():
    if os.path.exists(COMMENTS_FILE):
        try:
            with open(COMMENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, OSError) as e:
            logger.error(f"댓글 데이터 로드 실패: {e}")
            return {}
    return {}

def save_comments(comments):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(COMMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)

def add_comment(story_id, nickname, content):
    comments = load_comments()
    if story_id not in comments:
        comments[story_id] = []

    comment = {
        "id": f"{story_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "nickname": nickname,
        "content": content,
        "created_at": datetime.now().isoformat(),
    }
    comments[story_id].append(comment)
    save_comments(comments)
    return comment

def get_comments(story_id, comments_data):
    return comments_data.get(story_id, [])

# ----------------------------
# 통계 계산 함수
# ----------------------------
def calculate_statistics(stories):
    """승인된 후기 기반 통계 계산"""
    approved = [s for s in stories if s.get("approved", False)]

    if not approved:
        return None

    stats = {
        "total_count": len(approved),
        "final_count": len([s for s in approved if s.get("stage") == "final"]),
        "by_airline": defaultdict(lambda: {"total": 0, "final": 0}),
        "by_major": Counter(),
        "by_year": Counter(),
        "attempts_data": [],
        "questions_count": 0,
    }

    for s in approved:
        airline = s.get("airline", "기타")
        stats["by_airline"][airline]["total"] += 1
        if s.get("stage") == "final":
            stats["by_airline"][airline]["final"] += 1

        major = s.get("major", "").strip()
        if major:
            # 전공 간소화
            if "항공" in major:
                stats["by_major"]["항공서비스"] += 1
            elif "관광" in major or "호텔" in major:
                stats["by_major"]["관광/호텔"] += 1
            elif "영어" in major or "영문" in major:
                stats["by_major"]["영어/영문"] += 1
            elif "간호" in major:
                stats["by_major"]["간호"] += 1
            else:
                stats["by_major"]["기타 전공"] += 1

        year = s.get("year", 2024)
        stats["by_year"][year] += 1

        attempts = s.get("attempts", 1)
        stats["attempts_data"].append(attempts)

        questions = s.get("questions", [])
        stats["questions_count"] += len([q for q in questions if q.strip()])

    # 평균 도전 횟수
    if stats["attempts_data"]:
        stats["avg_attempts"] = sum(stats["attempts_data"]) / len(stats["attempts_data"])
    else:
        stats["avg_attempts"] = 0

    return stats

def get_all_questions(stories):
    """모든 면접 질문 수집"""
    questions = []
    approved = [s for s in stories if s.get("approved", False)]

    for s in approved:
        airline = s.get("airline", "기타")
        stage = s.get("stage", "final")
        year = s.get("year", 2024)
        story_questions = s.get("questions", [])

        for q in story_questions:
            if q.strip():
                questions.append({
                    "question": q.strip(),
                    "airline": airline,
                    "stage": stage,
                    "year": year,
                    "nickname": s.get("nickname", "익명"),
                })

    return questions

# ----------------------------
# 기출질문 기본 데이터 (항상 표시)
# ----------------------------
CURATED_QUESTIONS = {
    "대한항공": [
        "자기소개를 1분 내로 해주세요.",
        "대한항공에 지원한 이유는 무엇인가요?",
        "승무원이 되기 위해 어떤 준비를 했나요?",
        "영어로 자기소개를 해주세요. (영어면접)",
        "해외에서 문화 차이로 어려웠던 경험은?",
        "팀워크를 발휘했던 경험을 말씀해주세요.",
        "체력 관리는 어떻게 하고 계신가요?",
        "수영은 어느 정도 할 수 있나요?",
        "10년 후 자신의 모습은 어떨까요?",
        "기내에서 외국인 승객이 한국어를 못할 때 어떻게 하시겠습니까?",
    ],
    "아시아나항공": [
        "아시아나항공의 슬로건 '아름다운 사람들'은 어떤 의미라고 생각하나요?",
        "서비스업에서 가장 중요한 것은 무엇이라고 생각하나요?",
        "갈등 상황에서 어떻게 해결하시나요?",
        "왜 다른 항공사가 아닌 아시아나를 선택했나요?",
        "불만 고객을 응대한 경험이 있나요?",
        "자신의 장단점을 말해주세요.",
        "스트레스 해소 방법은 무엇인가요?",
        "중국어/일본어 가능 여부는?",
        "비행 중 안전이 위협받는 상황에서 어떻게 하시겠습니까?",
        "승무원의 가장 중요한 덕목은 무엇이라고 생각하나요?",
    ],
    "에어프레미아": [
        "에어프레미아에 대해 아는 것을 말씀해주세요.",
        "HSC(하이브리드 항공사)란 무엇이라고 생각하나요?",
        "장거리 비행에서 승무원에게 필요한 자질은?",
        "본인의 서비스 철학은 무엇인가요?",
        "토론 주제: '승객 만족 vs 안전 규정' 중 어느 것이 우선인가요?",
        "체력 관리 루틴이 있나요?",
        "영어 외 다른 외국어를 할 수 있나요?",
        "에어프레미아의 성장 가능성에 대해 어떻게 생각하나요?",
    ],
    "진에어": [
        "진에어의 'Fun, Young, Dynamic' 이미지에 대해 어떻게 생각하나요?",
        "본인이 '펀(Fun)'한 사람인 이유는?",
        "고객에게 즐거운 경험을 준 사례가 있나요?",
        "왜 FSC가 아닌 LCC를 선택했나요?",
        "불규칙한 근무 스케줄에 대해 어떻게 생각하나요?",
        "일본어/중국어 능력은 어느 정도인가요?",
        "동료와 의견이 다를 때 어떻게 하시나요?",
    ],
    "제주항공": [
        "제주항공에 지원한 이유를 말씀해주세요.",
        "'Fly, Better Fly'의 의미는 무엇이라고 생각하나요?",
        "승객에게 감동을 준 서비스 경험이 있나요?",
        "안전규정을 거부하는 승객에게 어떻게 대응하시겠습니까?",
        "체력 관리는 어떻게 하고 계신가요?",
        "LCC 승무원과 FSC 승무원의 차이점은 무엇이라고 생각하나요?",
        "본인만의 강점은 무엇인가요?",
    ],
    "티웨이항공": [
        "티웨이항공에 대해 아는 것을 말해주세요.",
        "서비스업 경험이 있다면 말해주세요.",
        "어려운 고객을 대한 경험을 말해주세요.",
        "왜 승무원이 되고 싶은가요?",
        "팀에서 갈등이 생기면 어떻게 해결하나요?",
        "체력이 좋은 편인가요? 어떻게 관리하나요?",
    ],
    "에어부산": [
        "에어부산에 지원한 이유는?",
        "부산에 대해 아는 것을 말해주세요.",
        "그룹 토론: '공항 야간운항 확대'에 대한 의견은?",
        "동료가 실수했을 때 어떻게 하시겠습니까?",
        "서비스에서 가장 중요한 것은 무엇이라고 생각하나요?",
        "불규칙한 생활 패턴에 적응할 수 있나요?",
    ],
    "이스타항공": [
        "이스타항공의 재출범에 대해 어떻게 생각하나요?",
        "상황대처: 기내에서 승객이 갑자기 쓰러지면?",
        "체력 관리는 어떻게 하고 계신가요?",
        "청주 근무가 가능한가요?",
        "승무원으로서 가장 중요한 역할은 무엇이라고 생각하나요?",
        "위기 상황에서 침착하게 대응한 경험이 있나요?",
    ],
    "파라타항공": [
        "파라타항공에 대해 아는 것을 말씀해주세요.",
        "신생 항공사에서 일하는 것에 대해 어떻게 생각하나요?",
        "국민체력100 결과는 어떻게 나왔나요?",
        "본인이 이 팀에 기여할 수 있는 점은?",
        "안전에 대한 본인의 생각을 말해주세요.",
    ],
}

# ----------------------------
# 세션 상태 초기화
# ----------------------------
if "user_id" not in st.session_state:
    # 간단한 익명 사용자 ID 생성
    st.session_state.user_id = f"user_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

# ----------------------------
# CSS 스타일
# ----------------------------
st.markdown("""
<style>
/* 통계 카드 */
.stat-card {
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.stat-value {
    font-size: 32px;
    font-weight: bold;
    margin-bottom: 5px;
}
.stat-label {
    font-size: 14px;
    color: #666;
}

/* 질문 카드 */
.question-card {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
    border-left: 4px solid #667eea;
}
.question-text {
    font-size: 15px;
    font-weight: 500;
    margin-bottom: 8px;
}
.question-meta {
    font-size: 12px;
    color: #888;
}

/* 좋아요 버튼 */
.like-btn {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 12px;
    border-radius: 20px;
    background: #f0f0f0;
    cursor: pointer;
    transition: all 0.2s;
}
.like-btn:hover {
    background: #ffe0e6;
}
.like-btn.liked {
    background: #ffe0e6;
    color: #e91e63;
}

/* 댓글 */
.comment-item {
    background: #f5f5f5;
    padding: 10px 15px;
    border-radius: 8px;
    margin-bottom: 8px;
}
.comment-author {
    font-weight: bold;
    font-size: 13px;
    color: #333;
}
.comment-time {
    font-size: 11px;
    color: #999;
}
.comment-content {
    margin-top: 5px;
    font-size: 14px;
}

/* 인기 후기 배지 */
.popular-badge {
    display: inline-block;
    background: linear-gradient(135deg, #ff6b6b, #ffa500);
    color: white;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# UI
# ----------------------------
st.title("🏆 합격자 DB")
st.caption("합격자들의 실제 경험, 면접 질문, 통계를 한눈에 확인하세요!")

# 데이터 로드
stories = load_stories()
likes_data = load_likes()
comments_data = load_comments()

# 탭 구성 (5개 탭)
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 통계 대시보드", "❓ 면접 질문 DB", "📖 후기 보기", "✍️ 후기 작성", "🎁 보상 안내"])

# ----------------------------
# 탭 1: 통계 대시보드
# ----------------------------
with tab1:
    stats = calculate_statistics(stories)

    if not stats:
        st.info("아직 승인된 후기가 없어 통계를 표시할 수 없습니다.")
    else:
        st.markdown("### 📈 합격 현황 한눈에 보기")

        # 핵심 지표 카드
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="stat-card" style="background: linear-gradient(135deg, #667eea20, #764ba220);">
                <div class="stat-value" style="color: #667eea;">{stats['total_count']}</div>
                <div class="stat-label">전체 합격 후기</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="stat-card" style="background: linear-gradient(135deg, #f5576c20, #f093fb20);">
                <div class="stat-value" style="color: #f5576c;">{stats['final_count']}</div>
                <div class="stat-label">최종 합격자</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="stat-card" style="background: linear-gradient(135deg, #4facfe20, #00f2fe20);">
                <div class="stat-value" style="color: #4facfe;">{stats['avg_attempts']:.1f}회</div>
                <div class="stat-label">평균 도전 횟수</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="stat-card" style="background: linear-gradient(135deg, #11998e20, #38ef7d20);">
                <div class="stat-value" style="color: #11998e;">{stats['questions_count']}</div>
                <div class="stat-label">수집된 질문</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # 2열 레이아웃
        col_left, col_right = st.columns([3, 2])

        with col_left:
            # 항공사별 현황
            st.markdown("#### ✈️ 항공사별 합격 현황")

            airline_data = dict(stats["by_airline"])
            if airline_data:
                # 항공사별 카드
                sorted_airlines = sorted(airline_data.items(), key=lambda x: x[1]["final"], reverse=True)

                for airline, data in sorted_airlines[:8]:
                    total = data["total"]
                    final = data["final"]
                    pass_rate = (final / total * 100) if total > 0 else 0

                    # 색상 결정
                    if pass_rate >= 80:
                        color = "#11998e"
                    elif pass_rate >= 50:
                        color = "#f5a623"
                    else:
                        color = "#667eea"

                    st.markdown(f"""
                    <div style="display: flex; align-items: center; padding: 10px; background: #f8f9fa; border-radius: 8px; margin-bottom: 8px;">
                        <div style="flex: 1;">
                            <span style="font-weight: bold;">{airline}</span>
                            <span style="color: #888; font-size: 12px; margin-left: 10px;">후기 {total}건</span>
                        </div>
                        <div style="text-align: right;">
                            <span style="background: {color}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 13px;">
                                최종 {final}명
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")

            # 연도별 추이
            st.markdown("#### 📅 연도별 합격 현황")
            year_data = dict(stats["by_year"])
            if year_data:
                sorted_years = sorted(year_data.items(), reverse=True)
                for year, count in sorted_years[:5]:
                    progress = min(count / max(year_data.values()) * 100, 100)
                    st.markdown(f"**{year}년** - {count}건")
                    st.progress(progress / 100)

        with col_right:
            # 전공 분포
            st.markdown("#### 🎓 합격자 전공 분포")
            major_data = dict(stats["by_major"])
            if major_data:
                sorted_majors = sorted(major_data.items(), key=lambda x: x[1], reverse=True)
                total_majors = sum(major_data.values())

                for major, count in sorted_majors:
                    pct = (count / total_majors * 100) if total_majors > 0 else 0
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                        <span>{major}</span>
                        <span style="font-weight: bold;">{pct:.0f}%</span>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("")
                st.caption("* 비전공자도 많이 합격하고 있어요!")

            st.markdown("---")

            # 도전 횟수 분포
            st.markdown("#### 🔄 도전 횟수 분포")
            attempts = stats["attempts_data"]
            if attempts:
                attempts_counter = Counter(attempts)

                first_try = attempts_counter.get(1, 0)
                second_try = attempts_counter.get(2, 0)
                third_plus = sum(v for k, v in attempts_counter.items() if k >= 3)

                total_attempts = len(attempts)

                st.markdown(f"""
                <div style="background: #e8f5e9; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <div style="font-size: 24px; font-weight: bold; color: #2e7d32;">첫 도전 합격</div>
                    <div style="font-size: 14px; color: #666;">{first_try}명 ({first_try/total_attempts*100:.0f}%)</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div style="background: #fff3e0; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <div style="font-size: 24px; font-weight: bold; color: #ef6c00;">2번째 도전</div>
                    <div style="font-size: 14px; color: #666;">{second_try}명 ({second_try/total_attempts*100:.0f}%)</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div style="background: #fce4ec; padding: 15px; border-radius: 10px;">
                    <div style="font-size: 24px; font-weight: bold; color: #c2185b;">3번 이상</div>
                    <div style="font-size: 14px; color: #666;">{third_plus}명 ({third_plus/total_attempts*100:.0f}%)</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("")
                st.info("포기하지 마세요! 여러 번 도전해서 합격한 분들도 많아요.")

# ----------------------------
# 탭 2: 면접 질문 DB
# ----------------------------
with tab2:
    st.markdown("### ❓ 면접 기출질문 모음")
    st.caption("항공사별 실제 기출질문 + 합격자 제보 질문을 모았습니다. 면접 준비에 활용하세요!")

    all_questions = get_all_questions(stories)

    # 기출질문 기본 데이터 항상 표시
    st.markdown("#### 📚 항공사별 기출질문")
    curated_airline = st.selectbox("항공사 선택", list(CURATED_QUESTIONS.keys()), key="curated_airline")
    curated_qs = CURATED_QUESTIONS.get(curated_airline, [])

    for i, q in enumerate(curated_qs, 1):
        st.markdown(f"""
        <div style="background: white; border-radius: 10px; padding: 12px 16px; margin: 6px 0; border-left: 4px solid #667eea; box-shadow: 0 1px 4px rgba(0,0,0,0.05);">
            <span style="color: #667eea; font-weight: 700;">Q{i}.</span> {q}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.info(f"💡 **{curated_airline}** 면접 준비 팁: 위 질문들에 대한 답변을 STAR 기법으로 준비하세요!")

    st.markdown("---")
    st.markdown("#### 💬 사용자 제보 질문")

    if not all_questions:
        st.caption("아직 사용자 제보 질문이 없습니다. 합격 후기를 작성하면서 질문을 공유해주세요!")
    else:
        # 필터
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            q_airline = st.selectbox("항공사 필터", ["전체"] + AIRLINES, key="q_airline")

        with col2:
            q_search = st.text_input("질문 검색", placeholder="키워드로 검색...", key="q_search")

        with col3:
            st.metric("총 질문 수", f"{len(all_questions)}개")

        # 필터링
        filtered_questions = all_questions
        if q_airline != "전체":
            filtered_questions = [q for q in filtered_questions if q["airline"] == q_airline]
        if q_search:
            filtered_questions = [q for q in filtered_questions if q_search.lower() in q["question"].lower()]

        st.markdown("---")

        # 질문 카테고리
        if q_airline == "전체":
            # 항공사별로 그룹핑
            questions_by_airline = defaultdict(list)
            for q in filtered_questions:
                questions_by_airline[q["airline"]].append(q)

            for airline, qs in sorted(questions_by_airline.items(), key=lambda x: len(x[1]), reverse=True):
                with st.expander(f"✈️ {airline} ({len(qs)}개 질문)", expanded=False):
                    for q in qs:
                        stage_info = PASS_STAGES.get(q["stage"], PASS_STAGES["final"])
                        st.markdown(f"""
                        <div class="question-card">
                            <div class="question-text">"{q['question']}"</div>
                            <div class="question-meta">
                                {stage_info['icon']} {stage_info['name']} | {q['year']}년 | 작성자: {q['nickname']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            # 선택한 항공사 질문만
            st.markdown(f"#### ✈️ {q_airline} 면접 질문 ({len(filtered_questions)}개)")

            for q in filtered_questions:
                stage_info = PASS_STAGES.get(q["stage"], PASS_STAGES["final"])
                st.markdown(f"""
                <div class="question-card">
                    <div class="question-text">"{q['question']}"</div>
                    <div class="question-meta">
                        {stage_info['icon']} {stage_info['name']} | {q['year']}년 | 작성자: {q['nickname']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # 인기 질문 유형
        st.markdown("---")
        st.markdown("#### 🔥 자주 나오는 질문 유형")

        question_types = {
            "자기소개": 0,
            "지원동기": 0,
            "장단점": 0,
            "갈등/스트레스": 0,
            "서비스 경험": 0,
            "영어": 0,
        }

        for q in all_questions:
            text = q["question"].lower()
            if "자기소개" in text or "소개" in text:
                question_types["자기소개"] += 1
            if "지원" in text or "동기" in text or "왜" in text:
                question_types["지원동기"] += 1
            if "장점" in text or "단점" in text:
                question_types["장단점"] += 1
            if "갈등" in text or "스트레스" in text or "힘들" in text or "어려" in text:
                question_types["갈등/스트레스"] += 1
            if "서비스" in text or "고객" in text:
                question_types["서비스 경험"] += 1
            if "영어" in text or "english" in text:
                question_types["영어"] += 1

        cols = st.columns(3)
        sorted_types = sorted(question_types.items(), key=lambda x: x[1], reverse=True)
        for i, (qtype, count) in enumerate(sorted_types):
            with cols[i % 3]:
                if count > 0:
                    st.markdown(f"""
                    <div style="background: #f0f4ff; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
                        <div style="font-weight: bold; color: #667eea;">{qtype}</div>
                        <div style="font-size: 20px; font-weight: bold;">{count}회</div>
                    </div>
                    """, unsafe_allow_html=True)

# ----------------------------
# 탭 3: 합격 후기 보기
# ----------------------------
with tab3:
    visible_stories = [s for s in stories if s.get("approved", False)]

    if not visible_stories:
        st.info("""
        ### 아직 등록된 합격 후기가 없습니다.

        **합격하셨다면 후기를 작성해주세요!**

        ✨ 후기 작성 시 단계별 보상이 있습니다! (🎁 보상 안내 탭 확인)
        """)
    else:
        # 필터 및 정렬
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            filter_airline = st.selectbox("항공사", ["전체"] + AIRLINES, key="filter_airline")
        with col2:
            filter_stage = st.selectbox("합격 단계", ["전체"] + [v["name"] for v in PASS_STAGES.values()], key="filter_stage")
        with col3:
            sort_option = st.selectbox("정렬", ["최신순", "좋아요순", "댓글많은순"], key="sort_option")
        with col4:
            st.metric("총 후기", f"{len(visible_stories)}건")

        # 필터링
        filtered = visible_stories
        if filter_airline != "전체":
            filtered = [s for s in filtered if s.get("airline") == filter_airline]
        if filter_stage != "전체":
            stage_key = [k for k, v in PASS_STAGES.items() if v["name"] == filter_stage]
            if stage_key:
                filtered = [s for s in filtered if s.get("stage") == stage_key[0]]

        # 정렬
        if sort_option == "최신순":
            filtered = sorted(filtered, key=lambda x: x.get("created_at", ""), reverse=True)
        elif sort_option == "좋아요순":
            filtered = sorted(filtered, key=lambda x: get_like_count(x.get("id", ""), likes_data), reverse=True)
        elif sort_option == "댓글많은순":
            filtered = sorted(filtered, key=lambda x: len(get_comments(x.get("id", ""), comments_data)), reverse=True)

        st.markdown("---")

        # 인기 후기 표시
        for story in filtered:
            story_id = story.get("id", "")
            stage = story.get("stage", "final")
            stage_info = PASS_STAGES.get(stage, PASS_STAGES["final"])
            approved = story.get("approved", False)
            reward = get_reward(stage, story.get("airline", ""))
            reward_badge = f" {reward['icon']}" if reward else ""

            like_count = get_like_count(story_id, likes_data)
            comment_count = len(get_comments(story_id, comments_data))
            user_liked = has_liked(story_id, st.session_state.user_id, likes_data)

            # 인기 배지
            popular_badge = ""
            if like_count >= 5:
                popular_badge = '<span class="popular-badge">인기 후기</span> '

            with st.expander(f"{popular_badge}{stage_info['icon']} {story.get('airline', '미정')} | {story.get('nickname', '익명')} ({story.get('year', '?')}년) {reward_badge} | ❤️ {like_count} 💬 {comment_count}"):
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

                st.divider()

                # 좋아요 & 댓글 섹션
                col_like, col_comment = st.columns([1, 3])

                with col_like:
                    like_text = "❤️ 좋아요" if not user_liked else "💖 좋아요 취소"
                    if st.button(f"{like_text} ({like_count})", key=f"like_{story_id}"):
                        toggle_like(story_id, st.session_state.user_id)
                        st.rerun()

                # 댓글 표시
                st.markdown("#### 💬 댓글 / 질문")
                story_comments = get_comments(story_id, comments_data)

                if story_comments:
                    for comment in story_comments[-5:]:  # 최근 5개만
                        created = comment.get("created_at", "")
                        try:
                            created_dt = datetime.fromisoformat(created)
                            created_str = created_dt.strftime("%m/%d %H:%M")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"댓글 시간 파싱 실패: {e}")
                            created_str = ""

                        st.markdown(f"""
                        <div class="comment-item">
                            <span class="comment-author">{comment.get('nickname', '익명')}</span>
                            <span class="comment-time">{created_str}</span>
                            <div class="comment-content">{comment.get('content', '')}</div>
                        </div>
                        """, unsafe_allow_html=True)

                # 댓글 작성
                with st.form(key=f"comment_form_{story_id}"):
                    comment_cols = st.columns([1, 3, 1])
                    with comment_cols[0]:
                        comment_nickname = st.text_input("닉네임", key=f"cn_{story_id}", placeholder="익명")
                    with comment_cols[1]:
                        comment_content = st.text_input("댓글/질문 작성", key=f"cc_{story_id}", placeholder="합격자에게 궁금한 점을 물어보세요!")
                    with comment_cols[2]:
                        st.markdown("<br>", unsafe_allow_html=True)
                        submit_comment = st.form_submit_button("등록")

                    if submit_comment and comment_content.strip():
                        add_comment(story_id, comment_nickname or "익명", comment_content.strip())
                        st.success("댓글이 등록되었습니다!")
                        st.rerun()

# ----------------------------
# 탭 4: 후기 작성
# ----------------------------
with tab4:
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

        with col2:
            if airline and airline != "선택":
                final_round = get_final_round(airline)
                if final_round == 3:
                    stage_options = ["final", "3rd", "2nd", "1st", "document"]
                else:
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

        # 기프티콘 수령 연락처
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
        story_content = st.text_area("합격 경험을 자유롭게 작성해주세요", height=180)

        # 질문 & 팁
        st.markdown("### ❓ 받은 질문 / 💡 팁 (선택)")
        st.caption("실제로 받은 면접 질문을 공유해주시면 다른 지원자들에게 큰 도움이 됩니다!")
        col1, col2 = st.columns(2)
        questions = []
        tips = []
        for i in range(5):  # 5개로 확장
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
            elif not story_content.strip() or len(story_content.strip()) < 30:
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
                    "story": story_content.strip(),
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
# 탭 5: 보상 안내
# ----------------------------
with tab5:
    st.subheader("🎁 후기 작성 보상 안내")
    st.markdown("합격 후기를 작성해주시면 단계별로 보상을 드립니다!")

    st.markdown("---")

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
        | 🏆 최종 합격 | 👑 프리미엄 1주일 |
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        #### ✈️ 2차가 최종인 항공사
        <small>(아시아나, 진에어, 티웨이, 에어부산 등)</small>

        | 단계 | 보상 |
        |------|------|
        | 📄 서류합격 | - |
        | 🥇 1차 합격 | ☕ 스타벅스 아메리카노 |
        | 🏆 최종 합격 | 👑 프리미엄 1주일 |
        """, unsafe_allow_html=True)

    st.markdown("---")

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
            <h4>프리미엄 1주일</h4>
            <p style="font-size: 13px; color: #666;">프리미엄 멤버십<br/>1주일 무료 이용</p>
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

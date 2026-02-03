# personalized_interview_prototype.py
# 개인화 AI 면접 시스템 - 독립형 프로토타입
# FlyReady Lab 메인 웹과 완전히 분리된 별도 페이지
# 실행: streamlit run personalized_interview_prototype.py

import os
import time
import random
import json
import streamlit as st
import requests

# =====================
# 설정
# =====================
st.set_page_config(
    page_title="개인화 AI 면접 코치",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# API 설정 (기존 config에서 가져오거나 기본값 사용)
try:
    from config import LLM_MODEL_NAME, LLM_API_URL, LLM_TIMEOUT_SEC
except ImportError:
    LLM_MODEL_NAME = "gpt-4o-mini"
    LLM_API_URL = "https://api.openai.com/v1/chat/completions"
    LLM_TIMEOUT_SEC = 60

try:
    from env_config import OPENAI_API_KEY
except ImportError:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# =====================
# 커스텀 CSS (독립형)
# =====================
st.markdown("""
<style>
/* 기본 Streamlit UI 숨김 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stSidebarNav"] {display: none !important;}
[data-testid="stSidebar"] {display: none !important;}

/* 폰트 */
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
html, body, [class*="st-"] {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* 헤더 스타일 */
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 30px;
    border-radius: 16px;
    color: white;
    text-align: center;
    margin-bottom: 30px;
}
.main-header h1 {
    margin: 0;
    font-size: 32px;
    font-weight: 700;
}
.main-header p {
    margin: 10px 0 0 0;
    opacity: 0.9;
    font-size: 16px;
}

/* 카드 스타일 */
.info-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
}

/* 진행 단계 */
.step-indicator {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin: 20px 0;
}
.step-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #e2e8f0;
}
.step-dot.active {
    background: #667eea;
}
.step-dot.completed {
    background: #10b981;
}

/* 약점 태그 */
.weakness-tag {
    display: inline-block;
    background: #fee2e2;
    color: #dc2626;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 13px;
    margin: 4px;
}
.strength-tag {
    display: inline-block;
    background: #d1fae5;
    color: #059669;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 13px;
    margin: 4px;
}

/* 질문 박스 */
.question-box {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border-left: 4px solid #f59e0b;
    padding: 20px;
    border-radius: 8px;
    margin: 20px 0;
    font-size: 18px;
    font-weight: 500;
}
.question-label {
    font-size: 12px;
    color: #92400e;
    margin-bottom: 8px;
}

/* 개인화 이유 */
.personalization-reason {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 13px;
    color: #1e40af;
    margin-top: 10px;
}

/* 버튼 스타일 */
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    border: none !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# =====================
# 세션 상태 초기화
# =====================
defaults = {
    # 온보딩 상태
    "onboarding_step": 0,  # 0=시작, 1-8=각 단계, 9=완료
    "onboarding_completed": False,

    # 사용자 프로필
    "user_profile": {
        "name": "",
        "age": 25,
        "height": 165,
        "weight": None,  # 선택

        "university": "",
        "major": "",
        "major_type": "기타",  # 항공과/관광/호텔/기타
        "graduation_year": 2024,

        "toeic": 800,
        "toeic_speaking": None,
        "opic": None,
        "other_lang": "",

        "work_experiences": [],  # [{type, period, role}, ...]

        "exchange": None,  # 국가
        "study_abroad": None,  # 국가
        "language_training": None,  # {country, months}
        "volunteer_hours": 0,
        "awards": "",
        "certificates": "",

        "application_history": {},  # {항공사: {count, result}}
    },

    # 약점 분석 결과
    "detected_weaknesses": [],
    "detected_strengths": [],

    # 개인화 질문
    "personalized_questions": [],

    # 면접 세션
    "interview_started": False,
    "interview_current_idx": 0,
    "interview_answers": [],
    "interview_evaluations": [],
    "interview_completed": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =====================
# 약점 탐지 로직
# =====================
def detect_weaknesses(profile: dict) -> tuple:
    """사용자 프로필 기반 약점/강점 탐지"""
    weaknesses = []
    strengths = []

    # 1. 토익 점수 분석
    toeic = profile.get("toeic", 0)
    if toeic < 750:
        weaknesses.append({
            "type": "toeic_low",
            "label": "토익 점수 부족",
            "detail": f"토익 {toeic}점 (평균 이하)",
            "severity": "high"
        })
    elif toeic < 850:
        weaknesses.append({
            "type": "toeic_mid",
            "label": "토익 점수 보통",
            "detail": f"토익 {toeic}점 (900점 미만)",
            "severity": "medium"
        })
    else:
        strengths.append({
            "type": "toeic_high",
            "label": "우수한 토익 점수",
            "detail": f"토익 {toeic}점"
        })

    # 2. 전공 분석
    major_type = profile.get("major_type", "기타")
    if major_type == "기타":
        weaknesses.append({
            "type": "major_mismatch",
            "label": "비항공 전공",
            "detail": f"전공: {profile.get('major', '미입력')}",
            "severity": "medium"
        })
    elif major_type == "항공서비스학과":
        strengths.append({
            "type": "major_match",
            "label": "항공 전공",
            "detail": "항공서비스학과 출신"
        })

    # 3. 키 분석
    height = profile.get("height", 165)
    if height <= 162:
        weaknesses.append({
            "type": "height_limit",
            "label": "신장 제한 우려",
            "detail": f"키 {height}cm (아시아나 163cm 기준 미달)",
            "severity": "high"
        })
    elif height < 165:
        weaknesses.append({
            "type": "height_borderline",
            "label": "신장 아슬아슬",
            "detail": f"키 {height}cm",
            "severity": "low"
        })

    # 4. 서비스 경력 분석
    experiences = profile.get("work_experiences", [])
    service_exp = [e for e in experiences if e.get("type") in ["카페", "레스토랑", "호텔", "면세점"]]
    if not service_exp:
        weaknesses.append({
            "type": "no_service_exp",
            "label": "서비스직 경험 부족",
            "detail": "서비스업 경력 없음",
            "severity": "medium"
        })
    else:
        total_months = sum(e.get("period", 0) for e in service_exp)
        if total_months >= 12:
            strengths.append({
                "type": "service_exp",
                "label": "풍부한 서비스 경험",
                "detail": f"서비스직 {total_months}개월"
            })

    # 5. 해외 경험 분석
    has_overseas = (
        profile.get("exchange") or
        profile.get("study_abroad") or
        profile.get("language_training")
    )
    if not has_overseas:
        weaknesses.append({
            "type": "no_overseas",
            "label": "해외 경험 부족",
            "detail": "교환학생/유학/어학연수 경험 없음",
            "severity": "medium"
        })
    else:
        if profile.get("study_abroad"):
            strengths.append({
                "type": "study_abroad",
                "label": "유학 경험",
                "detail": f"{profile.get('study_abroad')} 유학"
            })
        elif profile.get("exchange"):
            strengths.append({
                "type": "exchange",
                "label": "교환학생 경험",
                "detail": f"{profile.get('exchange')} 교환학생"
            })

    # 6. 지원 이력 분석 (가장 날카로운)
    history = profile.get("application_history", {})
    for airline, info in history.items():
        if info.get("count", 0) >= 2 and info.get("result") == "불합격":
            weaknesses.append({
                "type": "multiple_fail",
                "label": f"{airline} 다회 탈락",
                "detail": f"{airline} {info['count']}회 불합격",
                "severity": "critical"
            })

    # 7. 봉사활동 분석
    volunteer = profile.get("volunteer_hours", 0)
    if volunteer < 50:
        weaknesses.append({
            "type": "low_volunteer",
            "label": "봉사활동 부족",
            "detail": f"봉사활동 {volunteer}시간",
            "severity": "low"
        })
    elif volunteer >= 100:
        strengths.append({
            "type": "high_volunteer",
            "label": "적극적 봉사활동",
            "detail": f"봉사활동 {volunteer}시간"
        })

    return weaknesses, strengths


# =====================
# 개인화 질문 생성
# =====================
def generate_personalized_questions(profile: dict, weaknesses: list) -> list:
    """약점 기반 개인화 질문 생성"""
    questions = []

    # 기본 질문 (누구에게나)
    questions.append({
        "question": "간단하게 자기소개 해주세요.",
        "reason": "기본 질문",
        "category": "기본",
        "weakness_target": None
    })

    # 약점 기반 질문 생성
    for weakness in weaknesses:
        w_type = weakness.get("type")

        if w_type == "toeic_low":
            questions.append({
                "question": f"토익 점수가 {profile.get('toeic')}점인데, 영어 실력은 어떻게 증명하시겠어요?",
                "reason": f"당신의 토익 {profile.get('toeic')}점이 평균(800점) 이하입니다",
                "category": "어학",
                "weakness_target": "toeic_low"
            })

        elif w_type == "toeic_mid":
            questions.append({
                "question": f"토익 {profile.get('toeic')}점인데, 왜 900점까지 안 올렸나요?",
                "reason": f"경쟁자 대부분이 850점 이상입니다",
                "category": "어학",
                "weakness_target": "toeic_mid"
            })

        elif w_type == "major_mismatch":
            major = profile.get("major", "전공")
            questions.extend([
                {
                    "question": f"{major} 전공인데 왜 승무원을 선택했나요?",
                    "reason": f"비항공 전공({major})에 대한 의문",
                    "category": "전공",
                    "weakness_target": "major_mismatch"
                },
                {
                    "question": "항공과 학생들과 경쟁해서 이길 자신 있나요?",
                    "reason": "항공과 출신과의 경쟁력 확인",
                    "category": "전공",
                    "weakness_target": "major_mismatch"
                }
            ])

        elif w_type == "height_limit":
            height = profile.get("height")
            questions.append({
                "question": f"키가 {height}cm면 아시아나는 163cm 제한에 걸리는데, 대한항공만 지원하실 건가요?",
                "reason": f"신장 {height}cm - 아시아나 기준 미달",
                "category": "신체",
                "weakness_target": "height_limit"
            })

        elif w_type == "height_borderline":
            questions.append({
                "question": f"키가 {profile.get('height')}cm로 아슬아슬한데, 불안하지 않으세요?",
                "reason": "신장 경계선에 대한 압박",
                "category": "신체",
                "weakness_target": "height_borderline"
            })

        elif w_type == "no_service_exp":
            questions.append({
                "question": "서비스 경험이 없는데, 고객 응대 자신 있나요?",
                "reason": "서비스직 경험 부재",
                "category": "경험",
                "weakness_target": "no_service_exp"
            })

        elif w_type == "no_overseas":
            questions.append({
                "question": "해외 경험이 없는데, 다양한 문화를 이해할 자신 있나요?",
                "reason": "해외 경험(교환학생/유학/어학연수) 없음",
                "category": "경험",
                "weakness_target": "no_overseas"
            })

        elif w_type == "multiple_fail":
            # 가장 날카로운 질문
            detail = weakness.get("detail", "")
            if "대한항공" in detail:
                airline = "대한항공"
            elif "아시아나" in detail:
                airline = "아시아나"
            else:
                airline = detail.split()[0] if detail else "해당 항공사"

            count = 2
            for h_airline, info in profile.get("application_history", {}).items():
                if h_airline in detail:
                    count = info.get("count", 2)
                    break

            questions.extend([
                {
                    "question": f"{airline}에 {count}번 떨어졌는데, 이번엔 뭐가 다른가요?",
                    "reason": f"{airline} {count}회 불합격 이력",
                    "category": "지원이력",
                    "weakness_target": "multiple_fail"
                },
                {
                    "question": "왜 계속 같은 항공사에 지원하시나요?",
                    "reason": "반복 지원에 대한 질문",
                    "category": "지원이력",
                    "weakness_target": "multiple_fail"
                }
            ])

        elif w_type == "low_volunteer":
            questions.append({
                "question": "봉사활동 경험이 적은데, 서비스 정신을 어떻게 보여주시겠어요?",
                "reason": f"봉사활동 {profile.get('volunteer_hours', 0)}시간으로 부족",
                "category": "경험",
                "weakness_target": "low_volunteer"
            })

    # 경력 기반 질문 (있는 경우)
    experiences = profile.get("work_experiences", [])
    if experiences:
        exp = experiences[0]
        exp_type = exp.get("type", "직장")
        questions.append({
            "question": f"{exp_type} 경험이 승무원 서비스와 어떻게 연결되나요? 구체적인 사례 하나 말씀해주세요.",
            "reason": f"입력하신 {exp_type} 경험에서 서비스 역량 확인",
            "category": "경험",
            "weakness_target": None
        })

    # 어학연수 질문
    lang_training = profile.get("language_training")
    if lang_training:
        country = lang_training.get("country", "해외")
        months = lang_training.get("months", 3)
        questions.append({
            "question": f"{country} 어학연수 {months}개월인데, 영어 회화 실력은 어느 정도인가요?",
            "reason": f"입력하신 {country} 어학연수 경험 확인",
            "category": "어학",
            "weakness_target": None
        })

    # 공통 질문 추가
    common_questions = [
        {
            "question": "왜 승무원이 되고 싶으신가요?",
            "reason": "기본 질문",
            "category": "동기",
            "weakness_target": None
        },
        {
            "question": "본인의 강점과 약점을 말씀해주세요.",
            "reason": "자기 인식 확인",
            "category": "인성",
            "weakness_target": None
        },
        {
            "question": "스트레스를 어떻게 관리하시나요?",
            "reason": "자기 관리 능력 확인",
            "category": "인성",
            "weakness_target": None
        }
    ]
    questions.extend(common_questions)

    # 중복 제거 및 랜덤 정렬
    seen = set()
    unique_questions = []
    for q in questions:
        if q["question"] not in seen:
            seen.add(q["question"])
            unique_questions.append(q)

    # 약점 타겟 질문을 앞으로, 나머지는 랜덤
    targeted = [q for q in unique_questions if q["weakness_target"]]
    general = [q for q in unique_questions if not q["weakness_target"]]
    random.shuffle(targeted)
    random.shuffle(general)

    # 자기소개는 항상 첫번째
    intro = [q for q in unique_questions if "자기소개" in q["question"]]
    rest = [q for q in targeted + general if "자기소개" not in q["question"]]

    return intro + rest[:9]  # 최대 10개 질문


# =====================
# AI 답변 평가
# =====================
def evaluate_answer(question: str, answer: str, weakness_target: str, profile: dict) -> dict:
    """AI로 답변 평가"""
    api_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "score": 0,
            "feedback": "API 키가 설정되지 않았습니다.",
            "improvement": "환경변수에 OPENAI_API_KEY를 설정해주세요."
        }

    # 약점 정보 추가
    weakness_context = ""
    if weakness_target:
        weakness_context = f"\n\n참고: 이 질문은 지원자의 약점('{weakness_target}')을 공략하기 위한 질문입니다. 이 약점을 얼마나 잘 커버했는지도 평가해주세요."

    system_prompt = f"""당신은 엄격한 항공사 면접관입니다.
지원자의 답변을 평가하고 점수와 피드백을 제공하세요.

평가 기준:
1. 구체성 (숫자, 사례 포함 여부)
2. STAR 구조 (상황-과제-행동-결과)
3. 논리성과 일관성
4. 진정성
5. 약점 커버 능력 (해당되는 경우){weakness_context}

반드시 아래 JSON 형식으로만 응답하세요:
{{"score": 0-100, "feedback": "피드백 내용", "improvement": "개선 포인트", "good_points": "잘한 점"}}"""

    user_prompt = f"""질문: {question}

지원자 답변:
{answer}

평가해주세요."""

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": LLM_MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 500,
        }

        r = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        resp = r.json()

        content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")

        # JSON 파싱 시도
        try:
            # JSON 부분만 추출
            if "{" in content and "}" in content:
                json_str = content[content.find("{"):content.rfind("}")+1]
                result = json.loads(json_str)
                return result
        except:
            pass

        return {
            "score": 50,
            "feedback": content,
            "improvement": "더 구체적인 사례와 숫자를 포함해보세요.",
            "good_points": ""
        }

    except Exception as e:
        return {
            "score": 0,
            "feedback": f"평가 중 오류: {str(e)}",
            "improvement": "",
            "good_points": ""
        }


# =====================
# UI: 온보딩 플로우
# =====================
def render_onboarding():
    """온보딩 단계별 UI 렌더링"""
    step = st.session_state.onboarding_step
    profile = st.session_state.user_profile

    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>개인화 AI 면접 코치</h1>
        <p>실제 면접처럼 준비하려면, 당신에 대해 알아야 합니다</p>
    </div>
    """, unsafe_allow_html=True)

    # 진행률 표시
    total_steps = 8
    progress_html = '<div class="step-indicator">'
    for i in range(1, total_steps + 1):
        if i < step:
            progress_html += '<div class="step-dot completed"></div>'
        elif i == step:
            progress_html += '<div class="step-dot active"></div>'
        else:
            progress_html += '<div class="step-dot"></div>'
    progress_html += '</div>'
    st.markdown(progress_html, unsafe_allow_html=True)

    st.divider()

    # =====================
    # Step 0: 시작
    # =====================
    if step == 0:
        st.markdown("### FlyReady Lab에 오신 걸 환영합니다!")
        st.markdown("""
        <div class="info-card">
        <h4>이 시스템의 특별한 점</h4>
        <p>일반 면접 앱: "승무원 지원 동기는?" (누구에게나 같은 질문)</p>
        <p><strong>개인화 AI 면접</strong>: "토익 750점인데, 왜 900점까지 안 올렸나요?" (당신만을 위한 질문)</p>
        <br>
        <p>당신의 약점을 미리 파악하고, 실제 면접에서 받을 법한 날카로운 질문으로 대비하세요.</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("시작하기", type="primary", use_container_width=True):
            st.session_state.onboarding_step = 1
            st.rerun()

    # =====================
    # Step 1: 기본 정보
    # =====================
    elif step == 1:
        st.markdown("### Step 1. 기본 정보")

        col1, col2 = st.columns(2)
        with col1:
            profile["name"] = st.text_input("이름", value=profile.get("name", ""))
            profile["age"] = st.number_input("나이", min_value=18, max_value=40, value=profile.get("age", 25))
        with col2:
            profile["height"] = st.number_input("키 (cm)", min_value=150, max_value=190, value=profile.get("height", 165))
            profile["weight"] = st.number_input("체중 (kg) - 선택사항", min_value=0, max_value=100, value=profile.get("weight") or 0)
            if profile["weight"] == 0:
                profile["weight"] = None

        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("이전"):
                st.session_state.onboarding_step = 0
                st.rerun()
        with col_next:
            if st.button("다음", type="primary"):
                st.session_state.user_profile = profile
                st.session_state.onboarding_step = 2
                st.rerun()

    # =====================
    # Step 2: 학력
    # =====================
    elif step == 2:
        st.markdown("### Step 2. 학력")

        profile["university"] = st.text_input("대학교", value=profile.get("university", ""))

        major_options = ["항공서비스학과", "관광학과", "호텔경영학과", "기타"]
        major_type_idx = major_options.index(profile.get("major_type", "기타")) if profile.get("major_type") in major_options else 3
        profile["major_type"] = st.selectbox("전공 계열", major_options, index=major_type_idx)

        if profile["major_type"] == "기타":
            profile["major"] = st.text_input("전공명 (직접 입력)", value=profile.get("major", ""))
        else:
            profile["major"] = profile["major_type"]

        profile["graduation_year"] = st.number_input(
            "졸업 연도 (예정 포함)",
            min_value=2015, max_value=2030,
            value=profile.get("graduation_year", 2024)
        )

        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("이전"):
                st.session_state.onboarding_step = 1
                st.rerun()
        with col_next:
            if st.button("다음", type="primary"):
                st.session_state.user_profile = profile
                st.session_state.onboarding_step = 3
                st.rerun()

    # =====================
    # Step 3: 어학 점수
    # =====================
    elif step == 3:
        st.markdown("### Step 3. 어학 점수")

        profile["toeic"] = st.number_input(
            "토익 점수",
            min_value=0, max_value=990,
            value=profile.get("toeic", 800),
            help="없으면 0 입력"
        )

        col1, col2 = st.columns(2)
        with col1:
            toeic_sp = st.number_input(
                "토익 스피킹 (선택)",
                min_value=0, max_value=200,
                value=profile.get("toeic_speaking") or 0
            )
            profile["toeic_speaking"] = toeic_sp if toeic_sp > 0 else None

        with col2:
            opic_options = ["없음", "IL", "IM1", "IM2", "IM3", "IH", "AL", "AH"]
            opic_val = profile.get("opic") or "없음"
            opic_idx = opic_options.index(opic_val) if opic_val in opic_options else 0
            opic = st.selectbox("오픽 (선택)", opic_options, index=opic_idx)
            profile["opic"] = opic if opic != "없음" else None

        profile["other_lang"] = st.text_input(
            "기타 어학 (선택)",
            value=profile.get("other_lang", ""),
            placeholder="예: JLPT N2, HSK 5급"
        )

        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("이전"):
                st.session_state.onboarding_step = 2
                st.rerun()
        with col_next:
            if st.button("다음", type="primary"):
                st.session_state.user_profile = profile
                st.session_state.onboarding_step = 4
                st.rerun()

    # =====================
    # Step 4: 경력
    # =====================
    elif step == 4:
        st.markdown("### Step 4. 경력")
        st.caption("아르바이트, 인턴 등 모든 경험을 입력해주세요")

        experiences = profile.get("work_experiences", [])

        # 기존 경력 표시
        for i, exp in enumerate(experiences):
            col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
            with col1:
                st.text(f"{exp.get('type', '')}")
            with col2:
                st.text(f"{exp.get('period', 0)}개월")
            with col3:
                st.text(f"{exp.get('role', '')}")
            with col4:
                if st.button("삭제", key=f"del_exp_{i}"):
                    experiences.pop(i)
                    profile["work_experiences"] = experiences
                    st.session_state.user_profile = profile
                    st.rerun()

        # 새 경력 추가
        st.markdown("---")
        st.markdown("**경력 추가**")
        exp_col1, exp_col2, exp_col3 = st.columns(3)
        with exp_col1:
            new_type = st.selectbox(
                "종류",
                ["카페", "레스토랑", "면세점", "호텔", "항공사 인턴", "기타"],
                key="new_exp_type"
            )
        with exp_col2:
            new_period = st.number_input("기간 (개월)", min_value=1, max_value=60, value=6, key="new_exp_period")
        with exp_col3:
            new_role = st.text_input("역할", placeholder="예: 바리스타, 홀서빙", key="new_exp_role")

        if st.button("+ 경력 추가"):
            experiences.append({
                "type": new_type,
                "period": new_period,
                "role": new_role
            })
            profile["work_experiences"] = experiences
            st.session_state.user_profile = profile
            st.rerun()

        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("이전"):
                st.session_state.onboarding_step = 3
                st.rerun()
        with col_next:
            if st.button("다음", type="primary"):
                st.session_state.user_profile = profile
                st.session_state.onboarding_step = 5
                st.rerun()

    # =====================
    # Step 5: 특이사항
    # =====================
    elif step == 5:
        st.markdown("### Step 5. 특이사항")

        # 교환학생
        has_exchange = st.checkbox("교환학생 경험 있음", value=bool(profile.get("exchange")))
        if has_exchange:
            profile["exchange"] = st.text_input("교환학생 국가", value=profile.get("exchange", ""))
        else:
            profile["exchange"] = None

        # 유학
        has_abroad = st.checkbox("유학 경험 있음", value=bool(profile.get("study_abroad")))
        if has_abroad:
            profile["study_abroad"] = st.text_input("유학 국가", value=profile.get("study_abroad", ""))
        else:
            profile["study_abroad"] = None

        # 어학연수
        lang_training = profile.get("language_training") or {}
        has_lang = st.checkbox("어학연수 경험 있음", value=bool(lang_training))
        if has_lang:
            lt_col1, lt_col2 = st.columns(2)
            with lt_col1:
                lt_country = st.text_input("어학연수 국가", value=lang_training.get("country", ""))
            with lt_col2:
                lt_months = st.number_input("기간 (개월)", min_value=1, max_value=24, value=lang_training.get("months", 3))
            profile["language_training"] = {"country": lt_country, "months": lt_months}
        else:
            profile["language_training"] = None

        # 봉사활동
        profile["volunteer_hours"] = st.number_input(
            "봉사활동 시간 (총)",
            min_value=0, max_value=1000,
            value=profile.get("volunteer_hours", 0)
        )

        # 수상/자격증
        profile["awards"] = st.text_input("수상 경력 (선택)", value=profile.get("awards", ""))
        profile["certificates"] = st.text_input("자격증 (선택)", value=profile.get("certificates", ""))

        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("이전"):
                st.session_state.onboarding_step = 4
                st.rerun()
        with col_next:
            if st.button("다음", type="primary"):
                st.session_state.user_profile = profile
                st.session_state.onboarding_step = 6
                st.rerun()

    # =====================
    # Step 6: 지원 이력
    # =====================
    elif step == 6:
        st.markdown("### Step 6. 지원 이력")
        st.caption("지금까지 지원한 항공사와 결과를 입력해주세요 (가장 중요한 정보입니다!)")

        history = profile.get("application_history", {})

        airlines = ["대한항공", "아시아나", "진에어", "제주항공", "티웨이", "에어부산", "에어서울"]

        for airline in airlines:
            col1, col2, col3 = st.columns([2, 1, 1])
            airline_data = history.get(airline, {"count": 0, "result": "미지원"})

            with col1:
                st.markdown(f"**{airline}**")
            with col2:
                count = st.number_input(
                    f"{airline} 지원 횟수",
                    min_value=0, max_value=10,
                    value=airline_data.get("count", 0),
                    key=f"hist_{airline}_count",
                    label_visibility="collapsed"
                )
            with col3:
                if count > 0:
                    result = st.selectbox(
                        f"{airline} 결과",
                        ["불합격", "1차 합격", "2차 합격", "최종 합격"],
                        index=0 if airline_data.get("result", "불합격") == "불합격" else
                              ["불합격", "1차 합격", "2차 합격", "최종 합격"].index(airline_data.get("result", "불합격")),
                        key=f"hist_{airline}_result",
                        label_visibility="collapsed"
                    )
                    history[airline] = {"count": count, "result": result}
                else:
                    if airline in history:
                        del history[airline]

        profile["application_history"] = history

        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("이전"):
                st.session_state.onboarding_step = 5
                st.rerun()
        with col_next:
            if st.button("다음", type="primary"):
                st.session_state.user_profile = profile
                st.session_state.onboarding_step = 7
                st.rerun()

    # =====================
    # Step 7: 확인 및 분석
    # =====================
    elif step == 7:
        st.markdown("### Step 7. 입력 정보 확인")

        # 프로필 요약 표시
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**기본 정보**")
            st.write(f"- 이름: {profile.get('name', '미입력')}")
            st.write(f"- 나이: {profile.get('age')}세")
            st.write(f"- 키: {profile.get('height')}cm")

            st.markdown("**학력**")
            st.write(f"- 대학: {profile.get('university', '미입력')}")
            st.write(f"- 전공: {profile.get('major', '미입력')}")

        with col2:
            st.markdown("**어학**")
            st.write(f"- 토익: {profile.get('toeic')}점")
            if profile.get("toeic_speaking"):
                st.write(f"- 토스: {profile.get('toeic_speaking')}점")
            if profile.get("opic"):
                st.write(f"- 오픽: {profile.get('opic')}")

            st.markdown("**지원 이력**")
            history = profile.get("application_history", {})
            if history:
                for airline, info in history.items():
                    st.write(f"- {airline}: {info['count']}회 ({info['result']})")
            else:
                st.write("- 없음")

        st.divider()

        # 약점 분석 미리보기
        weaknesses, strengths = detect_weaknesses(profile)

        st.markdown("**탐지된 약점**")
        if weaknesses:
            weakness_html = ""
            for w in weaknesses:
                weakness_html += f'<span class="weakness-tag">{w["label"]}</span>'
            st.markdown(weakness_html, unsafe_allow_html=True)
        else:
            st.success("큰 약점이 발견되지 않았습니다!")

        st.markdown("**탐지된 강점**")
        if strengths:
            strength_html = ""
            for s in strengths:
                strength_html += f'<span class="strength-tag">{s["label"]}</span>'
            st.markdown(strength_html, unsafe_allow_html=True)

        st.divider()

        st.warning("""
        **주의**: 입력하신 정보를 바탕으로 **당신의 약점을 파고드는** 질문이 생성됩니다.

        정보가 정확할수록 실전에 가까운 질문이 나옵니다!
        """)

        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("이전 (수정하기)"):
                st.session_state.onboarding_step = 1
                st.rerun()
        with col_next:
            if st.button("면접 시작하기", type="primary"):
                # 약점/강점 저장
                st.session_state.detected_weaknesses = weaknesses
                st.session_state.detected_strengths = strengths

                # 개인화 질문 생성
                questions = generate_personalized_questions(profile, weaknesses)
                st.session_state.personalized_questions = questions

                # 온보딩 완료
                st.session_state.onboarding_completed = True
                st.session_state.onboarding_step = 8
                st.rerun()


# =====================
# UI: 개인화 면접 세션
# =====================
def render_interview():
    """개인화 면접 세션 UI"""
    questions = st.session_state.personalized_questions
    current_idx = st.session_state.interview_current_idx
    profile = st.session_state.user_profile

    if not questions:
        st.error("질문이 생성되지 않았습니다. 다시 시작해주세요.")
        if st.button("처음으로"):
            for key in defaults:
                st.session_state[key] = defaults[key]
            st.rerun()
        return

    # 면접 완료 체크
    if st.session_state.interview_completed:
        render_interview_result()
        return

    # 헤더
    st.markdown(f"""
    <div class="main-header">
        <h1>개인화 AI 면접</h1>
        <p>{profile.get('name', '지원자')}님을 위한 맞춤 면접</p>
    </div>
    """, unsafe_allow_html=True)

    # 진행률
    progress = current_idx / len(questions)
    st.progress(progress)
    st.markdown(f"**질문 {current_idx + 1} / {len(questions)}**")

    # 현재 질문
    q_data = questions[current_idx]
    question = q_data["question"]
    reason = q_data["reason"]
    category = q_data["category"]

    # 질문 표시
    st.markdown(f"""
    <div class="question-box">
        <div class="question-label">[{category}] 개인화 질문</div>
        {question}
    </div>
    """, unsafe_allow_html=True)

    # 개인화 이유 표시
    if reason and reason != "기본 질문":
        st.markdown(f"""
        <div class="personalization-reason">
            💡 <strong>왜 이 질문이?</strong> {reason}
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # 답변 입력
    answer = st.text_area(
        "답변을 입력하세요",
        height=200,
        placeholder="실제 면접처럼 1분 내외로 답변해보세요...",
        key=f"answer_{current_idx}"
    )

    # 버튼
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if current_idx > 0:
            if st.button("이전 질문"):
                st.session_state.interview_current_idx -= 1
                st.rerun()

    with col2:
        if st.button("면접 종료"):
            st.session_state.interview_completed = True
            st.rerun()

    with col3:
        if st.button("답변 제출", type="primary"):
            if not answer.strip():
                st.warning("답변을 입력해주세요!")
            else:
                # 답변 저장
                while len(st.session_state.interview_answers) <= current_idx:
                    st.session_state.interview_answers.append("")
                st.session_state.interview_answers[current_idx] = answer

                # AI 평가
                with st.spinner("답변 평가 중..."):
                    evaluation = evaluate_answer(
                        question,
                        answer,
                        q_data.get("weakness_target"),
                        profile
                    )

                    while len(st.session_state.interview_evaluations) <= current_idx:
                        st.session_state.interview_evaluations.append({})
                    st.session_state.interview_evaluations[current_idx] = evaluation

                # 다음 질문 또는 완료
                if current_idx + 1 < len(questions):
                    st.session_state.interview_current_idx += 1
                else:
                    st.session_state.interview_completed = True

                st.rerun()


# =====================
# UI: 면접 결과
# =====================
def render_interview_result():
    """면접 결과 및 분석 UI"""
    questions = st.session_state.personalized_questions
    answers = st.session_state.interview_answers
    evaluations = st.session_state.interview_evaluations
    weaknesses = st.session_state.detected_weaknesses
    profile = st.session_state.user_profile

    st.markdown("""
    <div class="main-header">
        <h1>면접 결과 분석</h1>
        <p>당신만을 위한 맞춤 피드백</p>
    </div>
    """, unsafe_allow_html=True)

    # 종합 점수
    scores = [e.get("score", 0) for e in evaluations if e]
    avg_score = sum(scores) / len(scores) if scores else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("종합 점수", f"{avg_score:.0f}점", delta=None)
    with col2:
        st.metric("답변 완료", f"{len(answers)}개", delta=None)
    with col3:
        weakness_covered = len([e for e in evaluations if e.get("score", 0) >= 60])
        st.metric("약점 커버", f"{weakness_covered}/{len(weaknesses) if weaknesses else 0}")

    st.divider()

    # 질문별 상세 결과
    st.markdown("### 질문별 상세 분석")

    for i, (q_data, answer, evaluation) in enumerate(zip(questions, answers, evaluations)):
        if not answer:
            continue

        with st.expander(f"Q{i+1}. {q_data['question'][:50]}... ({evaluation.get('score', 0)}점)", expanded=False):
            st.markdown(f"**질문**: {q_data['question']}")
            if q_data.get("reason") and q_data["reason"] != "기본 질문":
                st.caption(f"개인화 이유: {q_data['reason']}")

            st.markdown("**내 답변**")
            st.info(answer)

            st.markdown("**평가**")
            st.write(f"점수: **{evaluation.get('score', 0)}점** / 100점")
            st.write(f"피드백: {evaluation.get('feedback', '')}")

            if evaluation.get("good_points"):
                st.success(f"잘한 점: {evaluation.get('good_points')}")

            if evaluation.get("improvement"):
                st.warning(f"개선 포인트: {evaluation.get('improvement')}")

    st.divider()

    # 약점 분석 요약
    st.markdown("### 약점 커버 분석")

    for weakness in weaknesses:
        # 해당 약점을 타겟으로 한 질문 찾기
        target_questions = [
            (i, q, evaluations[i] if i < len(evaluations) else {})
            for i, q in enumerate(questions)
            if q.get("weakness_target") == weakness.get("type")
        ]

        if target_questions:
            avg_weakness_score = sum(e.get("score", 0) for _, _, e in target_questions) / len(target_questions)
            status = "개선 필요" if avg_weakness_score < 60 else "양호" if avg_weakness_score < 80 else "우수"

            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{weakness.get('label')}** - {weakness.get('detail')}")
            with col2:
                if status == "개선 필요":
                    st.error(f"{avg_weakness_score:.0f}점 ({status})")
                elif status == "양호":
                    st.warning(f"{avg_weakness_score:.0f}점 ({status})")
                else:
                    st.success(f"{avg_weakness_score:.0f}점 ({status})")

    st.divider()

    # 다시 시작
    col1, col2 = st.columns(2)
    with col1:
        if st.button("같은 프로필로 다시 연습"):
            # 면접 세션만 초기화
            st.session_state.interview_started = False
            st.session_state.interview_current_idx = 0
            st.session_state.interview_answers = []
            st.session_state.interview_evaluations = []
            st.session_state.interview_completed = False
            # 질문 재생성
            questions = generate_personalized_questions(
                st.session_state.user_profile,
                st.session_state.detected_weaknesses
            )
            st.session_state.personalized_questions = questions
            st.rerun()

    with col2:
        if st.button("프로필 수정 (처음부터)"):
            # 전체 초기화
            for key in defaults:
                st.session_state[key] = defaults[key]
            st.rerun()


# =====================
# 메인 실행
# =====================
def main():
    """메인 실행 함수"""

    # 온보딩 완료 여부에 따라 화면 분기
    if not st.session_state.onboarding_completed:
        render_onboarding()
    else:
        render_interview()


if __name__ == "__main__":
    main()

# pages/22_체력준비.py
# 체력 테스트 및 수영 준비 가이드

import streamlit as st
import os
import json
from datetime import datetime, date

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_utils import check_tester_password

st.set_page_config(
    page_title="체력 준비",
    page_icon="🏊",
    layout="wide"
)

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="체력 준비")
except ImportError:
    pass


check_tester_password()

# ----------------------------
# 데이터
# ----------------------------

# 항공사별 체력 테스트 (11개 국내 항공사 - 사실 기반)
AIRLINE_FITNESS = {
    "대한항공": {
        "type": "FSC",
        "swimming": {
            "required": True,
            "distance": "25m",
            "style": "자유형",
            "time_limit": "제한 없음 (완영 필수)",
            "note": "물안경, 수영모 착용 가능. 체력검정 단계에서 실시"
        },
        "fitness": {
            "items": ["근력", "유연성", "심폐지구력"],
            "note": "체력검정 단계에서 실시"
        }
    },
    "아시아나항공": {
        "type": "FSC",
        "swimming": {
            "required": True,
            "distance": "25m",
            "style": "자유형",
            "time_limit": "제한 없음",
            "note": "최종 면접 단계 (건강검진/수영Test)에서 실시"
        },
        "fitness": {
            "items": [],
            "note": "별도 체력 테스트 없음 (수영만 실시)"
        }
    },
    "에어프레미아": {
        "type": "HSC",
        "swimming": {
            "required": False,
            "note": "수영 테스트 없음"
        },
        "fitness": {
            "items": ["체력 측정"],
            "note": "컬처핏면접/체력측정 단계에서 실시"
        }
    },
    "진에어": {
        "type": "LCC",
        "swimming": {
            "required": False,
            "note": "수영 테스트 없음"
        },
        "fitness": {
            "items": [],
            "note": "별도 체력 테스트 없음"
        }
    },
    "제주항공": {
        "type": "LCC",
        "swimming": {
            "required": False,
            "note": "수영 테스트 없음"
        },
        "fitness": {
            "items": [],
            "note": "별도 체력 테스트 없음"
        }
    },
    "티웨이항공": {
        "type": "LCC",
        "swimming": {
            "required": False,
            "note": "수영 테스트 없음"
        },
        "fitness": {
            "items": [],
            "note": "별도 체력 테스트 없음"
        }
    },
    "에어부산": {
        "type": "LCC",
        "swimming": {
            "required": False,
            "note": "수영 테스트 없음"
        },
        "fitness": {
            "items": [],
            "note": "별도 체력 테스트 없음"
        }
    },
    "에어서울": {
        "type": "LCC",
        "swimming": {
            "required": False,
            "note": "수영 테스트 없음"
        },
        "fitness": {
            "items": [],
            "note": "별도 체력 테스트 없음"
        }
    },
    "이스타항공": {
        "type": "LCC",
        "swimming": {
            "required": False,
            "note": "수영 테스트 없음"
        },
        "fitness": {
            "items": ["체력 TEST"],
            "note": "면접 과정에서 체력TEST 실시"
        }
    },
    "에어로케이": {
        "type": "LCC",
        "swimming": {
            "required": False,
            "note": "수영 테스트 없음"
        },
        "fitness": {
            "items": [],
            "note": "별도 체력 테스트 없음"
        }
    },
    "파라타항공": {
        "type": "LCC",
        "swimming": {
            "required": False,
            "note": "수영 테스트 없음"
        },
        "fitness": {
            "items": ["국민체력100"],
            "note": "국민체력100 체력평가 결과서 제출 필수"
        }
    },
}

# 수영 가이드
SWIMMING_GUIDE = {
    "준비물": [
        "수영복 (원피스형 추천)",
        "수영모 (실리콘 추천)",
        "물안경",
        "수건",
        "여분 속옷",
        "드라이기 (탈의실에 없을 수 있음)"
    ],
    "자유형 기본": [
        "1. 스트림라인 자세로 벽 차고 출발",
        "2. 팔 돌리기: 물 밖으로 손 빼서 앞으로 던지기",
        "3. 발차기: 허벅지부터 작게 빠르게",
        "4. 호흡: 3스트로크마다 옆으로 고개 돌려 호흡",
        "5. 25m 완영이 목표 (속도보다 완주)"
    ],
    "초보자 팁": [
        "처음엔 킥판 잡고 발차기 연습",
        "호흡이 어려우면 2스트로크마다 해도 OK",
        "긴장하면 몸이 가라앉으니 릴렉스",
        "중간에 쉬어도 되니 포기하지 말 것",
        "실제 테스트는 수영장 얕은 곳에서 진행"
    ],
    "연습 계획": {
        "1주차": "물 적응, 발차기 연습 (킥판)",
        "2주차": "팔 동작 추가, 호흡 연습",
        "3주차": "전체 동작 연결, 10m 완영",
        "4주차": "25m 완영 도전, 속도 조절"
    }
}

# 체력 테스트 가이드
FITNESS_GUIDE = {
    "윗몸일으키기": {
        "description": "1분간 실시, 복근 근력 측정",
        "standard": {
            "20대 여성": "30회 이상 (우수)",
            "기준": "20회 이상 권장"
        },
        "tips": [
            "목에 힘 빼고 복근으로 올라오기",
            "내려갈 때 천천히 (이완 동작도 중요)",
            "호흡: 올라갈 때 내쉬고, 내려갈 때 들이쉬기"
        ],
        "training": [
            "플랭크 30초~1분 x 3세트",
            "크런치 20개 x 3세트",
            "레그레이즈 15개 x 3세트"
        ]
    },
    "팔굽혀펴기": {
        "description": "무릎 대고 실시 (여성), 상체 근력 측정",
        "standard": {
            "20대 여성": "20회 이상 (우수)",
            "기준": "10회 이상 권장"
        },
        "tips": [
            "손 위치는 어깨너비보다 살짝 넓게",
            "팔꿈치 각도 45도 유지",
            "몸통 일직선 유지 (허리 꺾이지 않게)"
        ],
        "training": [
            "벽 푸쉬업 → 무릎 푸쉬업 → 풀 푸쉬업",
            "하루 10개씩 3세트로 시작",
            "매주 2개씩 증가"
        ]
    },
    "왕복오래달리기 (셔틀런)": {
        "description": "20m 왕복, 비프음에 맞춰 달리기",
        "standard": {
            "20대 여성": "40회 이상 (우수)",
            "기준": "30회 이상 권장"
        },
        "tips": [
            "처음엔 천천히, 페이스 조절이 핵심",
            "턴할 때 급정거 후 출발",
            "호흡 일정하게 유지"
        ],
        "training": [
            "조깅 20분 x 주 3회",
            "인터벌: 100m 달리기 + 100m 걷기 반복",
            "계단 오르기"
        ]
    },
    "국민체력100": {
        "description": "국민체육진흥공단 체력 인증 프로그램",
        "how_to": [
            "1. 국민체력100 홈페이지 접속",
            "2. 가까운 체력인증센터 예약",
            "3. 방문하여 체력 측정",
            "4. 결과서 발급 (당일 가능)"
        ],
        "items": ["악력", "윗몸일으키기", "왕복오래달리기", "앉아윗몸앞으로굽히기", "BMI"],
        "url": "https://nfa.kspo.or.kr"
    }
}

# 데이터 저장
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
FITNESS_LOG_FILE = os.path.join(DATA_DIR, "fitness_log.json")


def load_fitness_log():
    if os.path.exists(FITNESS_LOG_FILE):
        try:
            with open(FITNESS_LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []


def save_fitness_log(logs):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FITNESS_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


# ----------------------------
# UI
# ----------------------------
st.title("🏊 체력 준비 가이드")
st.caption("항공사 면접 체력 테스트 및 수영 준비")

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["✈️ 항공사별 기준", "🏊 수영 가이드", "💪 체력 테스트", "📝 운동 기록"])

# ========== 탭1: 항공사별 기준 ==========
with tab1:
    st.subheader("✈️ 항공사별 체력 테스트 기준")

    for airline, info in AIRLINE_FITNESS.items():
        with st.expander(f"✈️ {airline}"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🏊 수영 테스트**")
                swim = info["swimming"]
                if swim.get("required"):
                    st.success(f"필수 - {swim.get('distance', '')} {swim.get('style', '')}")
                    if swim.get("time_limit"):
                        st.caption(f"시간: {swim['time_limit']}")
                    if swim.get("note"):
                        st.caption(swim["note"])
                else:
                    st.info(swim.get("note", "수영 테스트 없음"))

            with col2:
                st.markdown("**💪 체력 테스트**")
                fit = info["fitness"]
                if fit.get("items"):
                    for item in fit["items"]:
                        st.write(f"- {item}")
                if fit.get("note"):
                    st.caption(fit["note"])

    st.markdown("---")
    st.warning("""
    **주의사항**
    - 채용 공고마다 기준이 달라질 수 있으니 반드시 확인하세요
    - 수영 테스트는 보통 최종 면접 단계에서 실시됩니다
    - 수영을 못하면 지금부터라도 배우세요! (1-2개월이면 25m 가능)
    """)


# ========== 탭2: 수영 가이드 ==========
with tab2:
    st.subheader("🏊 수영 준비 가이드")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📦 준비물")
        for item in SWIMMING_GUIDE["준비물"]:
            st.checkbox(item, key=f"swim_prep_{item}")

    with col2:
        st.markdown("### 📅 4주 연습 계획")
        for week, plan in SWIMMING_GUIDE["연습 계획"].items():
            st.info(f"**{week}**: {plan}")

    st.markdown("---")

    st.markdown("### 🏊 자유형 기본 동작")
    for i, step in enumerate(SWIMMING_GUIDE["자유형 기본"]):
        st.markdown(step)

    st.markdown("---")

    st.markdown("### 💡 초보자 팁")
    for tip in SWIMMING_GUIDE["초보자 팁"]:
        st.success(tip)

    st.markdown("---")

    st.info("""
    **수영 못하는 분들께**

    걱정 마세요! 25m 완영은 1-2개월이면 충분합니다.

    1. 가까운 수영장 등록 (주 2-3회)
    2. 성인 초보반 수강 추천
    3. 유튜브 '성인 수영 기초' 검색
    4. 꾸준히 하면 반드시 됩니다!
    """)


# ========== 탭3: 체력 테스트 ==========
with tab3:
    st.subheader("💪 체력 테스트 가이드")

    for test_name, info in FITNESS_GUIDE.items():
        with st.expander(f"💪 {test_name}", expanded=(test_name == "국민체력100")):
            st.markdown(f"**{info['description']}**")

            if "standard" in info:
                st.markdown("---")
                st.markdown("**기준:**")
                for k, v in info["standard"].items():
                    st.write(f"- {k}: {v}")

            if "tips" in info:
                st.markdown("---")
                st.markdown("**팁:**")
                for tip in info["tips"]:
                    st.info(tip)

            if "training" in info:
                st.markdown("---")
                st.markdown("**훈련 방법:**")
                for t in info["training"]:
                    st.write(f"- {t}")

            if "how_to" in info:
                st.markdown("---")
                st.markdown("**신청 방법:**")
                for step in info["how_to"]:
                    st.markdown(step)

            if "url" in info:
                st.link_button("🔗 국민체력100 바로가기", info["url"])


# ========== 탭4: 운동 기록 ==========
with tab4:
    st.subheader("📝 나의 운동 기록")

    logs = load_fitness_log()

    # 기록 추가
    with st.form("add_log"):
        st.markdown("**오늘의 운동 기록**")

        col1, col2 = st.columns(2)

        with col1:
            log_date = st.date_input("날짜", value=date.today())
            log_type = st.selectbox("운동 종류", ["수영", "윗몸일으키기", "팔굽혀펴기", "달리기", "기타"])

        with col2:
            log_amount = st.text_input("운동량", placeholder="예: 25m x 4회, 30개 x 3세트")
            log_note = st.text_input("메모", placeholder="오늘의 컨디션, 느낀점 등")

        if st.form_submit_button("기록 추가", type="primary", use_container_width=True):
            logs.append({
                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "date": log_date.strftime("%Y-%m-%d"),
                "type": log_type,
                "amount": log_amount,
                "note": log_note
            })
            save_fitness_log(logs)
            st.success("기록되었습니다!")
            st.rerun()

    st.markdown("---")

    # 기록 보기
    if logs:
        st.markdown("**최근 기록**")

        # 최신순 정렬
        logs = sorted(logs, key=lambda x: x.get("date", ""), reverse=True)

        for log in logs[:20]:
            col1, col2, col3, col4 = st.columns([1.5, 1.5, 2, 2])

            with col1:
                st.write(log.get("date", "")[-5:])
            with col2:
                st.write(log.get("type", ""))
            with col3:
                st.write(log.get("amount", ""))
            with col4:
                st.caption(log.get("note", ""))

        # 통계
        st.markdown("---")
        st.markdown("**이번 주 운동 횟수**")

        from datetime import timedelta
        week_ago = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
        week_logs = [l for l in logs if l.get("date", "") >= week_ago]

        col1, col2, col3 = st.columns(3)
        with col1:
            swim_count = len([l for l in week_logs if l.get("type") == "수영"])
            st.metric("🏊 수영", f"{swim_count}회")
        with col2:
            strength_count = len([l for l in week_logs if l.get("type") in ["윗몸일으키기", "팔굽혀펴기"]])
            st.metric("💪 근력운동", f"{strength_count}회")
        with col3:
            cardio_count = len([l for l in week_logs if l.get("type") == "달리기"])
            st.metric("🏃 유산소", f"{cardio_count}회")

    else:
        st.info("아직 기록이 없습니다. 오늘부터 운동을 기록해보세요!")

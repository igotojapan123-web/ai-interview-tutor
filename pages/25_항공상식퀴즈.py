# pages/25_항공상식퀴즈.py
# 항공 상식 퀴즈 게임

import streamlit as st
import os
import json
import random
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_utils import check_tester_password

st.set_page_config(
    page_title="항공 상식 퀴즈",
    page_icon="✈️",
    layout="wide"
)

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="항공상식 퀴즈")
except ImportError:
    pass


check_tester_password()

# ----------------------------
# 퀴즈 데이터
# ----------------------------
QUIZ_DATA = {
    "항공 기초": [
        {
            "question": "항공기의 날개 끝에 있는 작은 수직 날개를 무엇이라고 할까요?",
            "options": ["윙렛(Winglet)", "플랩(Flap)", "스포일러(Spoiler)", "에일러론(Aileron)"],
            "answer": 0,
            "explanation": "윙렛(Winglet)은 연료 효율을 높이고 항력을 줄이기 위해 날개 끝에 부착된 작은 수직 날개입니다."
        },
        {
            "question": "비행기가 이륙할 때 속도를 나타내는 V1은 무엇을 의미할까요?",
            "options": ["이륙 결심 속도", "최대 이륙 속도", "순항 속도", "착륙 속도"],
            "answer": 0,
            "explanation": "V1은 이륙 결심 속도로, 이 속도를 넘으면 이륙을 중단할 수 없습니다."
        },
        {
            "question": "국제선 항공기에서 사용하는 표준 언어는?",
            "options": ["영어", "프랑스어", "스페인어", "중국어"],
            "answer": 0,
            "explanation": "ICAO(국제민간항공기구)에 의해 영어가 국제 항공 표준 언어로 지정되어 있습니다."
        },
        {
            "question": "항공기 동체의 압력을 유지하는 것을 무엇이라고 할까요?",
            "options": ["여압(Pressurization)", "가압(Compression)", "감압(Decompression)", "기압(Barometry)"],
            "answer": 0,
            "explanation": "여압(Pressurization)은 고고도에서 승객이 편안하게 호흡할 수 있도록 객실 압력을 유지하는 것입니다."
        },
        {
            "question": "항공기 블랙박스의 실제 색상은?",
            "options": ["주황색", "검정색", "빨간색", "노란색"],
            "answer": 0,
            "explanation": "블랙박스는 사고 현장에서 쉽게 발견할 수 있도록 밝은 주황색으로 되어 있습니다."
        },
    ],
    "항공사 상식": [
        {
            "question": "대한민국 최초의 민간 항공사는?",
            "options": ["대한항공", "대한국민항공사", "아시아나항공", "조선항공"],
            "answer": 1,
            "explanation": "1948년 설립된 대한국민항공사(KNA)가 한국 최초의 민간 항공사입니다."
        },
        {
            "question": "스타얼라이언스(Star Alliance)의 창립 멤버가 아닌 항공사는?",
            "options": ["아시아나항공", "루프트한자", "유나이티드항공", "에어캐나다"],
            "answer": 0,
            "explanation": "아시아나항공은 2003년에 스타얼라이언스에 가입했으며, 창립 멤버가 아닙니다."
        },
        {
            "question": "세계에서 가장 큰 항공 동맹체는?",
            "options": ["스타얼라이언스", "스카이팀", "원월드", "밸류얼라이언스"],
            "answer": 0,
            "explanation": "스타얼라이언스는 26개 회원 항공사로 세계 최대 항공 동맹체입니다."
        },
        {
            "question": "대한항공이 속해 있는 항공 동맹체는?",
            "options": ["스카이팀", "스타얼라이언스", "원월드", "없음"],
            "answer": 0,
            "explanation": "대한항공은 스카이팀(SkyTeam)의 창립 멤버입니다."
        },
        {
            "question": "FSC, LCC에서 'C'가 의미하는 것은?",
            "options": ["Carrier", "Company", "Corporation", "Center"],
            "answer": 0,
            "explanation": "FSC(Full Service Carrier), LCC(Low Cost Carrier)에서 C는 Carrier(항공사)를 의미합니다."
        },
    ],
    "객실 서비스": [
        {
            "question": "비상구 좌석에 앉을 수 없는 승객은?",
            "options": ["15세 미만 승객", "비즈니스맨", "외국인", "첫 비행 승객"],
            "answer": 0,
            "explanation": "비상구 좌석은 비상시 문을 열 수 있어야 하므로, 어린이, 노약자, 임산부 등은 앉을 수 없습니다."
        },
        {
            "question": "항공기 내에서 전자기기 사용을 제한하는 이유는?",
            "options": ["항공기 통신 장비 간섭 가능성", "배터리 폭발 위험", "승객 집중력 저하", "객실 온도 상승"],
            "answer": 0,
            "explanation": "전자기기가 항공기의 통신 및 항법 장비에 간섭을 일으킬 수 있기 때문입니다."
        },
        {
            "question": "기내식이 지상에서 먹을 때보다 맛없게 느껴지는 이유는?",
            "options": ["낮은 습도와 기압", "음식 온도", "좌석 불편함", "조명"],
            "answer": 0,
            "explanation": "기내의 낮은 습도와 기압으로 인해 미각과 후각이 둔해져 음식 맛이 다르게 느껴집니다."
        },
        {
            "question": "객실승무원이 이착륙 시 앉는 좌석을 무엇이라고 할까요?",
            "options": ["점프시트(Jump Seat)", "크루시트(Crew Seat)", "서비스시트(Service Seat)", "에어시트(Air Seat)"],
            "answer": 0,
            "explanation": "점프시트(Jump Seat)는 승무원 전용 접이식 좌석입니다."
        },
        {
            "question": "기내에서 승객이 쓰러졌을 때 찾는 의료 장비는?",
            "options": ["AED", "CPR", "EMS", "ICU"],
            "answer": 0,
            "explanation": "AED(자동제세동기)는 심정지 환자에게 전기 충격을 주는 응급 의료 장비입니다."
        },
    ],
    "공항/항로": [
        {
            "question": "인천국제공항의 IATA 코드는?",
            "options": ["ICN", "INC", "SEL", "GMP"],
            "answer": 0,
            "explanation": "인천국제공항의 IATA 코드는 ICN입니다. 참고로 김포공항은 GMP입니다."
        },
        {
            "question": "세계에서 가장 붐비는 공항(2023년 기준)은?",
            "options": ["하츠필드-잭슨 애틀랜타", "두바이", "히스로", "인천"],
            "answer": 0,
            "explanation": "미국 애틀랜타 공항이 승객 수 기준 세계 1위입니다."
        },
        {
            "question": "항공기가 대서양을 횡단할 때 사용하는 항로를 무엇이라고 할까요?",
            "options": ["NAT Track", "PAC Route", "ATL Path", "SEA Lane"],
            "answer": 0,
            "explanation": "NAT(North Atlantic Track)는 대서양 횡단 항공로입니다."
        },
        {
            "question": "면세점에서 'Duty Free'의 Duty는 무엇을 의미할까요?",
            "options": ["관세", "의무", "근무", "세금"],
            "answer": 0,
            "explanation": "Duty는 관세를 의미하며, Duty Free는 관세가 없다는 뜻입니다."
        },
        {
            "question": "CIQ는 무엇의 약자일까요?",
            "options": ["세관/출입국/검역", "체크인/입국/대기", "수하물/입국/조회", "출국/입국/대기"],
            "answer": 0,
            "explanation": "CIQ는 Customs(세관), Immigration(출입국), Quarantine(검역)의 약자입니다."
        },
    ],
    "안전/비상": [
        {
            "question": "항공기 비상탈출 슬라이드가 펼쳐지는 데 걸리는 시간은?",
            "options": ["약 6초", "약 30초", "약 1분", "약 3분"],
            "answer": 0,
            "explanation": "비상 슬라이드는 약 6초 만에 완전히 펼쳐지도록 설계되어 있습니다."
        },
        {
            "question": "산소마스크가 내려왔을 때 먼저 해야 하는 것은?",
            "options": ["본인 먼저 착용", "아이 먼저 착용", "안전벨트 확인", "짐 챙기기"],
            "answer": 0,
            "explanation": "본인이 먼저 착용해야 의식을 잃지 않고 옆 사람을 도울 수 있습니다."
        },
        {
            "question": "비상착수 시 구명조끼는 언제 부풀려야 할까요?",
            "options": ["항공기 밖으로 나간 후", "착석 즉시", "착수 직전", "산소마스크 착용 후"],
            "answer": 0,
            "explanation": "기내에서 부풀리면 이동이 어려우므로, 반드시 항공기 밖으로 나간 후 부풀려야 합니다."
        },
        {
            "question": "Brace Position(충격 방지 자세)에서 머리를 어디에 두어야 할까요?",
            "options": ["앞좌석 등받이", "무릎 위", "창문 쪽", "통로 쪽"],
            "answer": 0,
            "explanation": "앞좌석 등받이에 머리를 대고 손으로 머리를 감싸 보호합니다."
        },
        {
            "question": "항공기 화재 시 승무원이 사용하는 소화기 종류가 아닌 것은?",
            "options": ["물 소화기", "할론 소화기", "이산화탄소 소화기", "건조 분말 소화기"],
            "answer": 0,
            "explanation": "항공기에서는 주로 할론, 이산화탄소, 하론 대체 소화기를 사용합니다."
        },
    ],
}

# 데이터 저장
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
QUIZ_SCORE_FILE = os.path.join(DATA_DIR, "quiz_scores.json")


def load_scores():
    if os.path.exists(QUIZ_SCORE_FILE):
        try:
            with open(QUIZ_SCORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []


def save_scores(scores):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(QUIZ_SCORE_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)


# ----------------------------
# UI
# ----------------------------
st.title("✈️ 항공 상식 퀴즈")
st.caption("게임처럼 즐기며 항공 상식을 익혀보세요!")

# 세션 상태 초기화
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "current_quiz" not in st.session_state:
    st.session_state.current_quiz = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "answered" not in st.session_state:
    st.session_state.answered = False
if "selected_category" not in st.session_state:
    st.session_state.selected_category = None

# 탭 구성
tab1, tab2 = st.tabs(["🎮 퀴즈 풀기", "🏆 기록"])

# ========== 탭1: 퀴즈 풀기 ==========
with tab1:
    if not st.session_state.quiz_started:
        # 카테고리 선택
        st.subheader("🎯 카테고리 선택")

        categories = list(QUIZ_DATA.keys())

        cols = st.columns(3)
        for i, cat in enumerate(categories):
            with cols[i % 3]:
                if st.button(f"📚 {cat}\n({len(QUIZ_DATA[cat])}문제)", key=f"cat_{cat}", use_container_width=True):
                    st.session_state.selected_category = cat
                    st.session_state.current_quiz = random.sample(QUIZ_DATA[cat], min(5, len(QUIZ_DATA[cat])))
                    st.session_state.current_index = 0
                    st.session_state.score = 0
                    st.session_state.quiz_started = True
                    st.session_state.answered = False
                    st.rerun()

        st.markdown("---")

        # 전체 랜덤
        if st.button("🎲 전체 랜덤 퀴즈 (10문제)", type="primary", use_container_width=True):
            all_questions = []
            for cat_questions in QUIZ_DATA.values():
                all_questions.extend(cat_questions)
            st.session_state.selected_category = "전체 랜덤"
            st.session_state.current_quiz = random.sample(all_questions, min(10, len(all_questions)))
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.quiz_started = True
            st.session_state.answered = False
            st.rerun()

    else:
        # 퀴즈 진행 중
        quiz_list = st.session_state.current_quiz
        idx = st.session_state.current_index
        total = len(quiz_list)

        if idx < total:
            current_q = quiz_list[idx]

            # 진행 상황
            progress = (idx) / total
            st.progress(progress, text=f"문제 {idx + 1} / {total}")

            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"📚 {st.session_state.selected_category}")
            with col2:
                st.metric("현재 점수", f"{st.session_state.score}점")

            st.markdown("---")

            # 문제
            st.markdown(f"### Q{idx + 1}. {current_q['question']}")

            st.markdown("")

            # 선택지
            if not st.session_state.answered:
                for i, option in enumerate(current_q["options"]):
                    if st.button(f"{chr(65+i)}. {option}", key=f"opt_{i}", use_container_width=True):
                        st.session_state.answered = True
                        st.session_state.user_answer = i
                        st.rerun()
            else:
                # 정답 표시
                correct = current_q["answer"]
                user_ans = st.session_state.user_answer

                for i, option in enumerate(current_q["options"]):
                    if i == correct:
                        st.success(f"✅ {chr(65+i)}. {option}")
                    elif i == user_ans and user_ans != correct:
                        st.error(f"❌ {chr(65+i)}. {option}")
                    else:
                        st.write(f"{chr(65+i)}. {option}")

                # 결과 표시
                st.markdown("---")
                if user_ans == correct:
                    st.success("🎉 정답입니다!")
                    if not hasattr(st.session_state, 'score_added') or not st.session_state.score_added:
                        st.session_state.score += 10
                        st.session_state.score_added = True
                else:
                    st.error(f"😅 오답입니다. 정답은 {chr(65+correct)}번입니다.")

                st.info(f"💡 **해설:** {current_q['explanation']}")

                # 다음 문제 버튼
                if st.button("다음 문제 →", type="primary", use_container_width=True):
                    st.session_state.current_index += 1
                    st.session_state.answered = False
                    st.session_state.score_added = False
                    st.rerun()

        else:
            # 퀴즈 종료
            final_score = st.session_state.score
            total_possible = total * 10

            st.markdown("---")
            st.markdown("## 🎉 퀴즈 완료!")

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 16px; text-align: center; color: white;">
                <div style="font-size: 48px; font-weight: 800;">{final_score} / {total_possible}</div>
                <div style="font-size: 18px; margin-top: 10px;">점</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("")

            # 등급
            percentage = (final_score / total_possible) * 100
            if percentage >= 90:
                grade = "🏆 항공 전문가!"
            elif percentage >= 70:
                grade = "✈️ 우수 준비생!"
            elif percentage >= 50:
                grade = "📚 조금 더 공부해요!"
            else:
                grade = "💪 다시 도전해봐요!"

            st.markdown(f"### {grade}")

            # 기록 저장
            scores = load_scores()
            scores.append({
                "category": st.session_state.selected_category,
                "score": final_score,
                "total": total_possible,
                "date": datetime.now().isoformat()
            })
            save_scores(scores)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 다시 도전", use_container_width=True):
                    st.session_state.quiz_started = False
                    st.rerun()
            with col2:
                if st.button("🏠 처음으로", use_container_width=True):
                    st.session_state.quiz_started = False
                    st.session_state.selected_category = None
                    st.rerun()


# ========== 탭2: 기록 ==========
with tab2:
    st.subheader("🏆 나의 퀴즈 기록")

    scores = load_scores()

    if not scores:
        st.info("아직 기록이 없습니다. 퀴즈를 풀어보세요!")
    else:
        # 최신순 정렬
        scores = sorted(scores, key=lambda x: x.get("date", ""), reverse=True)

        # 통계
        total_attempts = len(scores)
        total_score = sum(s.get("score", 0) for s in scores)
        total_possible = sum(s.get("total", 0) for s in scores)
        avg_percentage = (total_score / total_possible * 100) if total_possible > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 도전", f"{total_attempts}회")
        with col2:
            st.metric("총 점수", f"{total_score}점")
        with col3:
            st.metric("평균 정답률", f"{avg_percentage:.0f}%")

        st.markdown("---")

        st.markdown("**최근 기록**")
        for score in scores[:10]:
            percentage = (score.get("score", 0) / score.get("total", 1)) * 100

            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(score.get("category", ""))
            with col2:
                st.write(f"{score.get('score', 0)} / {score.get('total', 0)}점")
            with col3:
                if percentage >= 70:
                    st.success(f"{percentage:.0f}%")
                elif percentage >= 50:
                    st.warning(f"{percentage:.0f}%")
                else:
                    st.error(f"{percentage:.0f}%")
